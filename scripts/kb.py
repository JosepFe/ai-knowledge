#!/usr/bin/env python3
"""Keyword (BM25) search over the user's markdown knowledge, plus health signals.

  kb.py <keywords...> [--top N]   search; prints "score  file:line  heading" and matching lines
  kb.py --misses [DAYS]           weak searches (questions the notes could not answer)
  kb.py --stale [DAYS]            notes whose "Last reviewed"/"Última revisión" is older than DAYS (default 180), and re-check/BROKEN facts
  kb.py --stats                   size and always-on budget signals
Config: ~/.config/ai-knowledge/config.json (knowledge_dirs, exclude, weak_score).
"""
import datetime as dt
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HOME, load_config, state_file  # noqa: E402

CFG = load_config()
WORD = re.compile(r"[a-z0-9][a-z0-9_.+#-]*")
STOP = set("the a an of to in and or for is are on with how what which de la el los las un una y o en para por con que como del al es se su".split())
DATE = r"(\d{4}-\d{2}-\d{2})"
REVIEWED = re.compile(r"(?:last reviewed|última revisión|ultima revision)\s*:?\s*" + DATE, re.I)


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def tokens(text):
    return [t.strip(".-") for t in WORD.findall(norm(text)) if t not in STOP and len(t) > 1]


def files():
    for d in CFG["knowledge_dirs"]:
        for p in sorted(Path(d).rglob("*.md")):
            if not any(part in CFG["exclude"] for part in p.parts):
                yield p


def chunks():
    """One chunk per heading section: (path, start_line, heading, lines)."""
    for p in files():
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        start, head, buf = 1, p.stem, []
        for i, line in enumerate(lines, 1):
            if line.startswith("#") and buf:
                yield p, start, head, buf
                start, head, buf = i, line.lstrip("# ").strip(), []
            elif line.startswith("#"):
                head = line.lstrip("# ").strip()
            buf.append(line)
        if buf:
            yield p, start, head, buf


def short(p):
    return str(p).replace(str(HOME), "~")


def search(query, top):
    q = tokens(query)
    if not q or not CFG["knowledge_dirs"]:
        sys.exit("No keywords, or no knowledge_dirs in the config.")
    docs = []
    for p, start, head, lines in chunks():
        toks = tokens(head + " " + p.stem.replace("-", " ") + " " + "\n".join(lines))
        docs.append((p, start, head, lines, Counter(toks), len(toks)))
    n = len(docs)
    avg = sum(d[5] for d in docs) / max(n, 1)
    df = Counter(t for d in docs for t in set(d[4]) if t in q)
    k1, b = 1.4, 0.75
    scored = []
    for p, start, head, lines, tf, length in docs:
        s = 0.0
        for t in q:
            if tf[t]:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * length / avg))
        if s > 0:
            scored.append((s, p, start, head, lines, sum(1 for t in set(q) if tf[t]) / len(set(q))))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0] if scored else 0.0
    # A high score from one common word is not an answer: with 2+ keywords, some top result must hold half of them.
    cover = max((x[5] for x in scored[:5]), default=0.0)
    weak = best < CFG["weak_score"] or (len(set(q)) > 1 and cover < CFG.get("min_coverage", 0.5))
    with open(state_file("searches.log"), "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')}\t{best:.2f}\t{'WEAK' if weak else 'ok'}\t{query}\n")
    for s, p, start, head, lines, _ in scored[:top]:
        print(f"{s:6.2f}  {short(p)}:{start}  {head}")
        hits = [(i, l) for i, l in enumerate(lines) if set(tokens(l)) & set(q)][:3]
        for i, l in hits:
            print(f"        {start + i}: {l.strip()[:160]}")
    if weak:
        why = f"best score {best:.2f} < {CFG['weak_score']}" if best < CFG["weak_score"] else f"no top result holds half of the keywords (best {cover:.0%})"
        print(f"\nWEAK: {why}. Try the words the notes would use, or research it and save the result.")


def misses(days):
    since = dt.datetime.now() - dt.timedelta(days=days)
    log = state_file("searches.log")
    rows = [l.rstrip("\n").split("\t") for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    rows = [r for r in rows if len(r) == 4 and dt.datetime.fromisoformat(r[0]) >= since]
    weak = [r for r in rows if r[2] == "WEAK"]
    print(f"{len(weak)} weak of {len(rows)} searches in the last {days} days")
    for q, c in Counter(r[3] for r in weak).most_common():
        print(f"{c:3}  {q}")


def stale(days):
    limit = dt.date.today() - dt.timedelta(days=days)
    old, flagged, none = [], [], 0
    for p in files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = REVIEWED.search(text)
        if m and dt.date.fromisoformat(m.group(1)) < limit:
            old.append((m.group(1), p))
        elif not m:
            none += 1
        for i, l in enumerate(text.splitlines(), 1):
            if re.search(r"\bre-check\b|\bBROKEN\b", l):
                flagged.append(f"{short(p)}:{i}  {l.strip()[:140]}")
    print(f"# Reviewed before {limit} ({len(old)})")
    for d, p in sorted(old):
        print(f"{d}  {short(p)}")
    print(f"\n# Facts marked re-check / BROKEN ({len(flagged)})")
    print("\n".join(flagged))
    print(f"\n({none} notes have no review date; only notes that go stale need one)")


def stats():
    lim = CFG["max_note_kb"]
    print(f"# Knowledge files over {lim} KB (split by topic)")
    total = 0
    for p in files():
        size = p.stat().st_size
        total += 1
        if size > lim * 1024:
            print(f"OVER  {size // 1024:4} KB  {short(p)}")
    print(f"({total} notes)\n\n# Skills over 80 lines (move detail into reference files)")
    for sk in sorted((HOME / ".claude" / "skills").glob("*/SKILL.md")):
        n = len(sk.read_text(encoding="utf-8", errors="ignore").splitlines())
        if n > 80:
            print(f"OVER  {n:4} lines  {short(sk)}")
    print("\n# Always-on text (loaded every session)")
    always = [HOME / ".claude" / "CLAUDE.md", Path.cwd() / "CLAUDE.md"]
    always += list((HOME / ".claude" / "projects").glob("*/memory/MEMORY.md"))
    for p in always:
        if p.exists():
            c = len(p.read_text(encoding="utf-8", errors="ignore"))
            print(f"{'OVER' if c > 13000 else 'ok  '}  {c:6} chars  {short(p)}")
    log = state_file("searches.log")
    if log.exists():
        rows = log.read_text(encoding="utf-8").splitlines()[-200:]
        w = sum("\tWEAK\t" in r for r in rows)
        flag = "OVER" if rows and len(rows) >= 20 and w / len(rows) > 0.2 else "ok  "
        print(f"\n# Searches\n{flag}  {w}/{len(rows)} weak in the last {len(rows)} searches")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--misses":
        misses(int(a[1]) if len(a) > 1 else 30)
    elif a[0] == "--stale":
        stale(int(a[1]) if len(a) > 1 else 180)
    elif a[0] == "--stats":
        stats()
    else:
        top = 8
        if "--top" in a:
            i = a.index("--top")
            top = int(a[i + 1])
            a = a[:i] + a[i + 2:]
        search(" ".join(a), top)
