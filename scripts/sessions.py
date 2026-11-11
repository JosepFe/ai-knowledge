#!/usr/bin/env python3
"""Compact digest of past Claude Code sessions for config-review.

  sessions.py [YYYY-MM-DD]   (default: 30 days ago)
Sections: user requests, slash commands, likely corrections, repeated Bash descriptions, skills and agents used.
Reads ~/.claude/history.jsonl and ~/.claude/projects/*/*.jsonl; prints to stdout, writes nothing.
"""
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
since = dt.datetime.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now() - dt.timedelta(days=30)
TRIVIAL = {"si", "sí", "no", "ok", "vale", "yes", "exit", "sigue", "continua", "continúa", "go on", "dale", "perfecto", "gracias", "thanks"}
CORRECTION = re.compile(r"^(no[,. ]|wrong|don't|do not|stop|i said|te he dicho|ya te dije|eso no|mal\b|otra vez|again|not what)", re.I)

print(f"# Requests since {since:%Y-%m-%d}\n")
slash, corrections, n = collections.Counter(), [], 0
hist = f"{HOME}/.claude/history.jsonl"
for line in open(hist, encoding="utf-8", errors="ignore") if os.path.exists(hist) else []:
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("timestamp", 0) < since.timestamp() * 1000:
        continue
    t = " ".join((d.get("display") or "").split())
    if t.startswith("/"):
        slash[t.split()[0]] += 1
        continue
    if len(t) < 12 or t.lower().strip(" .!") in TRIVIAL:
        continue
    when = dt.datetime.fromtimestamp(d["timestamp"] / 1000)
    proj = (d.get("project") or "").replace(HOME, "~")
    print(f"{when:%m-%d} | {proj} | {t[:280]}")
    n += 1
    if CORRECTION.search(t):
        corrections.append(f"{when:%m-%d} | {t[:200]}")
print(f"\n({n} requests)\n\n# Slash commands\n")
for k, v in slash.most_common():
    print(f"{v:4} {k}")
print("\n# Likely corrections (each one is a rule that failed or is missing)\n")
print("\n".join(corrections) or "(none)")

bash, skills, agents = collections.Counter(), collections.Counter(), collections.Counter()
for f in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
    if os.path.getmtime(f) < since.timestamp():
        continue
    for line in open(f, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            inp = c.get("input") or {}
            if c.get("name") == "Bash" and inp.get("description"):
                bash[inp["description"].strip().lower()] += 1
            elif c.get("name") == "Skill":
                skills[inp.get("skill", "?")] += 1
            elif c.get("name") in ("Agent", "Task"):
                agents[inp.get("subagent_type") or "general-purpose"] += 1
print("\n# Repeated Bash descriptions (what Claude keeps doing by hand)\n")
for k, v in bash.most_common():
    if v < 2:
        break
    print(f"{v:4} {k}")
print("\n# Skills used\n")
for k, v in skills.most_common():
    print(f"{v:4} {k}")
print("\n# Subagents used\n")
for k, v in agents.most_common():
    print(f"{v:4} {k}")
