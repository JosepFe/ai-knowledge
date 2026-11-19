#!/usr/bin/env python3
"""Token, time and leak report from past Claude Code sessions. Numbers only: no prompts, answers or file names.

  usage.py [FROM [TO]] [--md]           text or Markdown summary (default: last 30 days; TO excluded)
  usage.py [FROM [TO]] --html [PATH]    HTML report with charts (default: internal_docs/usage-report.html)
  usage.py --periods FROM:TO FROM:TO ... one comparison table, one row per period

Reads ~/.claude/projects/*/*.jsonl. Each API message is counted once (streamed events repeat its id).
Context per turn = input + cache read + cache write. Leak signals: cache writes, peak context, repeated
file reads and subagent (sidechain) tokens. Time: gaps up to IDLE_SECONDS count as active, longer as waiting.
Approximate, by design.
"""
import collections
import datetime as dt
import glob
import html
import json
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDLE_SECONDS = 300
TOP = 10


def parse_args(argv):
    """Returns (since, until, md, html_path, periods). Dates are local days; until is excluded."""
    now = dt.datetime.now()
    since, until, html_path, md, periods, dates, i = now - dt.timedelta(days=30), now + dt.timedelta(days=1), None, False, [], [], 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--md", "--by-version"):
            md = md or arg == "--md"
        elif arg == "--periods":
            for p in argv[i + 1:]:
                if p.startswith("--"):
                    break
                start, _, end = p.partition(":")
                periods.append((dt.datetime.fromisoformat(start), dt.datetime.fromisoformat(end)))
                i += 1
        elif arg == "--html":
            nxt = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else None
            html_path = nxt or os.path.join(ROOT, "internal_docs", "usage-report.html")
            i += 1 if nxt else 0
        else:
            dates.append(dt.datetime.fromisoformat(arg))
        i += 1
    if dates:
        since = dates[0]
    if len(dates) > 1:
        until = dates[1]
    return since, until, md, html_path, periods


def ctx_of(u):
    return (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)


def clean_model(model):
    for prefix in ("eu.", "us.", "global.", "anthropic."):
        model = model.removeprefix(prefix)
    return model


def read_session(path):
    """Returns per-message usage, active times, repeated reads and tool output sizes.

    usage maps message id -> (model, usage, is_subagent, skill, subagent_type, branch). The skill and the
    subagent type are the last ones the session invoked before the message: an approximation, since a
    skill's tokens run until the next skill call.
    """
    usage, stamps, read_ids, reads, tool_chars, max_tool = {}, [], set(), collections.Counter(), 0, 0
    skill, agent = "", ""
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("timestamp"):
            stamps.append(dt.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None))
        msg = d.get("message") or {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        for block in content:
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                skill = (block.get("input") or {}).get("skill", "") or skill
            if block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                agent = (block.get("input") or {}).get("subagent_type") or "general-purpose"
        if d.get("type") == "assistant" and msg.get("usage") and msg.get("id") and stamps:
            usage[msg["id"]] = (clean_model(msg.get("model", "unknown")), msg["usage"], bool(d.get("isSidechain")),
                                skill or "(sin skill)", agent or "general-purpose", d.get("gitBranch") or "(sin rama)",
                                stamps[-1])
        for block in content:
            if block.get("type") == "tool_use" and block.get("name") == "Read" and block.get("id") not in read_ids:
                read_ids.add(block.get("id"))
                reads[(block.get("input") or {}).get("file_path", "")] += 1
            if block.get("type") == "tool_result":
                body = block.get("content")
                size = sum(len(b.get("text", "")) for b in body) if isinstance(body, list) else len(body or "")
                tool_chars += size
                max_tool = max(max_tool, size)
    return usage, stamps, reads, tool_chars, max_tool


def session_row(path, since, until):
    usage, stamps, reads, tool_chars, max_tool = read_session(path)
    stamps = sorted(s for s in stamps if since <= s < until)
    usage = {k: v for k, v in usage.items() if since <= v[6] < until}
    if not usage and not stamps:
        return None
    row = {
        "project": os.path.basename(os.path.dirname(path)), "session": os.path.basename(path)[:8],
        "messages": 0, "input": 0, "cache_write": 0, "cache_read": 0, "output": 0,
        "peak_ctx": 0, "series": [], "sidechain_tokens": 0, "tokens": 0,
        "reads": sum(reads.values()), "reads_repeated": sum(c - 1 for c in reads.values() if c > 1),
        "tool_chars": tool_chars, "max_tool": max_tool, "active": 0.0, "waiting": 0.0,
        "models": collections.Counter(), "procs": collections.defaultdict(collections.Counter),
        "branches": collections.defaultdict(collections.Counter),
    }
    for model, u, side, skill, agent, branch, _ in usage.values():
        ctx = ctx_of(u)
        tokens = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("output_tokens") or 0)
        proc = f"subagente: {agent}" if side else (skill if skill == "(sin skill)" else f"skill: {skill}")
        for key, bucket in ((proc, row["procs"]), (branch, row["branches"])):
            bucket[key]["messages"] += 1
            bucket[key]["tokens"] += tokens
            bucket[key]["output"] += u.get("output_tokens") or 0
        row["messages"] += 1
        row["models"][model] += 1
        row["input"] += u.get("input_tokens") or 0
        row["cache_write"] += u.get("cache_creation_input_tokens") or 0
        row["cache_read"] += u.get("cache_read_input_tokens") or 0
        row["output"] += u.get("output_tokens") or 0
        row["peak_ctx"] = max(row["peak_ctx"], ctx)
        row["series"].append(ctx)
        if side:
            row["sidechain_tokens"] += (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
    row["tokens"] = row["input"] + row["cache_write"] + row["cache_read"] + row["output"]
    for a, b in zip(stamps, stamps[1:]):
        gap = (b - a).total_seconds()
        row["active" if gap <= IDLE_SECONDS else "waiting"] += gap / 3600
    return row


def collect(since, until):
    rows = []
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < since.timestamp():
            continue
        row = session_row(path, since, until)
        if row:
            rows.append(row)
    return rows


def totals(rows):
    keys = ("messages", "input", "cache_write", "cache_read", "output", "tokens", "sidechain_tokens",
            "reads", "reads_repeated", "tool_chars", "active", "waiting")
    t = {k: sum(r[k] for r in rows) for k in keys}
    t["sessions"] = len(rows)
    t["peak_ctx"] = max((r["peak_ctx"] for r in rows), default=0)
    return t


def group_by_project(rows):
    out = collections.defaultdict(collections.Counter)
    for r in rows:
        for k in ("messages", "input", "cache_write", "cache_read", "output", "tokens", "active", "waiting"):
            out[r["project"]][k] += r[k]
    return out


def merge(rows, key):
    out = collections.defaultdict(collections.Counter)
    for r in rows:
        for label, c in r[key].items():
            out[label].update(c)
    return out


def top_by_tokens(agg, n=TOP):
    return sorted(agg.items(), key=lambda kv: -kv[1]["tokens"])[:n]


def model_totals(since, until):
    out = collections.defaultdict(collections.Counter)
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < since.timestamp():
            continue
        usage, _, _, _, _ = read_session(path)
        for model, u, _, _, _, _, ts in usage.values():
            if model.startswith("<") or not since <= ts < until:
                continue
            out[model]["messages"] += 1
            out[model]["input"] += u.get("input_tokens") or 0
            out[model]["cache_write"] += u.get("cache_creation_input_tokens") or 0
            out[model]["cache_read"] += u.get("cache_read_input_tokens") or 0
            out[model]["output"] += u.get("output_tokens") or 0
    return out


def fmt(n):
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


PLUGINS = {
    "ai-knowledge": {
        "repo": ROOT,
        "skills": {"knowledge-search", "research", "save-knowledge", "setup", "duel", "config-review", "knowledge-refresh"},
    },
    "ai-kickstart": {
        "repo": os.path.join(os.path.dirname(ROOT), "ai-kickstart"),
        "skills": {"run-story", "run-epic", "review-app", "new-project", "check-sensitive"},
    },
}


def plugin_history(repo):
    """(UTC time, version) for each commit that changed .claude-plugin/plugin.json, oldest first. Read-only git."""
    log = subprocess.run(["git", "-C", repo, "log", "--format=%cI %H", "--", ".claude-plugin/plugin.json"],
                         capture_output=True, text=True, check=False).stdout.split("\n")
    history = []
    for line in log:
        if not line.strip():
            continue
        when, sha = line.split()
        shown = subprocess.run(["git", "-C", repo, "show", f"{sha}:.claude-plugin/plugin.json"],
                               capture_output=True, text=True, check=False).stdout
        version = json.loads(shown).get("version") if shown.strip() else None
        if version:
            utc = dt.datetime.fromisoformat(when).astimezone(dt.timezone.utc).replace(tzinfo=None)
            history.append((utc, version))
    return sorted(history)


def version_at(history, ts):
    current = history[0][1] if history else "sin versión"
    for when, version in history:
        if when <= ts:
            current = version
    return current


def by_version(since, until):
    """Tokens of the messages whose skill belongs to each plugin, grouped by that plugin's version at the time."""
    histories = {name: plugin_history(cfg["repo"]) for name, cfg in PLUGINS.items()}
    buckets = collections.defaultdict(collections.Counter)
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < since.timestamp():
            continue
        usage, _, _, _, _ = read_session(path)
        for model, u, _, skill, _, _, ts in usage.values():
            if not since <= ts < until or model.startswith("<"):
                continue
            name = skill.removeprefix("ai-kickstart:").removeprefix("ai-knowledge:")
            for plugin, cfg in PLUGINS.items():
                if name in cfg["skills"] or skill.startswith(f"{plugin}:"):
                    key = (plugin, version_at(histories[plugin], ts))
                    buckets[key]["messages"] += 1
                    buckets[key]["tokens"] += ctx_of(u) + (u.get("output_tokens") or 0)
                    buckets[key]["output"] += u.get("output_tokens") or 0
    return buckets


def version_report(since, until):
    lines = [f"# Skills by plugin version {since:%Y-%m-%d}..{until:%Y-%m-%d}", "",
             "Each message counts for the plugin version active on its date. Approximate.", ""]
    for (plugin, version), c in sorted(by_version(since, until).items()):
        lines.append(f"  {plugin} {version}: messages={fmt(c['messages'])}, tokens={fmt(c['tokens'])}, output={fmt(c['output'])}")
    return "\n".join(lines)


def period_line(label, rows):
    t = totals(rows)
    return (f"{label:24} sessions={t['sessions']:>4}  tokens={fmt(t['tokens']):>16}  output={fmt(t['output']):>12}  "
            f"cache_write={fmt(t['cache_write']):>14}  active={t['active']:.1f} h  waiting={t['waiting']:.1f} h")


def periods_report(periods):
    lines = ["# Periods"]
    for since, until in periods:
        lines.append(period_line(f"{since:%Y-%m-%d}..{until:%Y-%m-%d}", collect(since, until)))
    return "\n".join(lines)


def text_report(since, until, rows, md):
    t = totals(rows)
    by_model = model_totals(since, until)
    by_project = group_by_project(rows)
    out = [f"# Usage {since:%Y-%m-%d}..{until:%Y-%m-%d} ({t['sessions']} sessions)", ""]
    if md:
        out += ["## By model", "", "| model | messages | input | cache write | cache read | output |", "|---|---:|---:|---:|---:|---:|"]
        out += [f"| {m} | " + " | ".join(fmt(c[k]) for k in ("messages", "input", "cache_write", "cache_read", "output")) + " |"
                for m, c in sorted(by_model.items(), key=lambda kv: -kv[1]["output"])]
        out += ["", "## By project folder", "", "| project | messages | tokens | output | active h | waiting h |", "|---|---:|---:|---:|---:|---:|"]
        out += [f"| {p} | {fmt(c['messages'])} | {fmt(c['tokens'])} | {fmt(c['output'])} | {c['active']:.1f} | {c['waiting']:.1f} |"
                for p, c in sorted(by_project.items(), key=lambda kv: -kv[1]["tokens"])]
    else:
        for m, c in sorted(by_model.items(), key=lambda kv: -kv[1]["output"]):
            out.append(f"  {m}: messages={fmt(c['messages'])}, output={fmt(c['output'])}, cache_write={fmt(c['cache_write'])}")
        for p, c in sorted(by_project.items(), key=lambda kv: -kv[1]["tokens"]):
            out.append(f"  {p}: tokens={fmt(c['tokens'])}, active={c['active']:.1f} h, waiting={c['waiting']:.1f} h")
    procs, branches = merge(rows, "procs"), merge(rows, "branches")
    if md:
        out += ["", "## By process (skill or subagent)", "", "| process | messages | tokens | output |", "|---|---:|---:|---:|"]
        out += [f"| {p} | {fmt(c['messages'])} | {fmt(c['tokens'])} | {fmt(c['output'])} |" for p, c in top_by_tokens(procs, 20)]
        out += ["", "## By branch (kickstart story or epic)", "", "| branch | messages | tokens | output |", "|---|---:|---:|---:|"]
        out += [f"| {b} | {fmt(c['messages'])} | {fmt(c['tokens'])} | {fmt(c['output'])} |" for b, c in top_by_tokens(branches, 20)]
    else:
        out.append("Por proceso:")
        out += [f"  {p}: tokens={fmt(c['tokens'])}, messages={fmt(c['messages'])}" for p, c in top_by_tokens(procs, 20)]
        out.append("Por rama:")
        out += [f"  {b}: tokens={fmt(c['tokens'])}, messages={fmt(c['messages'])}" for b, c in top_by_tokens(branches, 20)]
    out += ["", "## Leak signals (top sessions)" if md else "Leak signals:"]
    for label, key in (("cache writes", "cache_write"), ("peak context", "peak_ctx"), ("repeated file reads", "reads_repeated")):
        top = sorted(rows, key=lambda r: -r[key])[:3]
        out.append(f"  {label}: " + ", ".join(f"{r['project']}/{r['session']} {fmt(r[key])}" for r in top))
    out.append(f"  subagent tokens: {fmt(t['sidechain_tokens'])} of {fmt(t['tokens'])} total")
    out.append(f"\nActive ~{t['active']:.1f} h; waiting (gaps over {IDLE_SECONDS // 60} min) ~{t['waiting']:.1f} h. Approximate.")
    return "\n".join(out)


def leak_table(rows, key, label):
    top = sorted(rows, key=lambda r: -r[key])[:TOP]
    body = "".join(
        f"<tr><td>{html.escape(r['project'])}</td><td>{html.escape(r['session'])}</td>"
        f"<td class='num'>{fmt(r[key])}</td><td class='num'>{fmt(r['tokens'])}</td></tr>" for r in top)
    return (f"<h3>{label}</h3><table><thead><tr><th>proyecto</th><th>sesión</th><th>{label}</th><th>tokens</th></tr></thead>"
            f"<tbody>{body or '<tr><td colspan=4>Sin datos</td></tr>'}</tbody></table>")


def build_dataset(since, until):
    """Aggregated numbers for the interactive report: one record per day, project, model, process, branch and plugin version."""
    histories = {name: plugin_history(cfg["repo"]) for name, cfg in PLUGINS.items()}
    recs = collections.defaultdict(collections.Counter)
    times = collections.defaultdict(lambda: [0.0, 0.0])
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < since.timestamp():
            continue
        usage, stamps, _, _, _ = read_session(path)
        project = os.path.basename(os.path.dirname(path))
        stamps = sorted(s for s in stamps if since <= s < until)
        for a, b in zip(stamps, stamps[1:]):
            gap = (b - a).total_seconds()
            times[(a.date().isoformat(), project)][0 if gap <= IDLE_SECONDS else 1] += gap / 3600
        for model, u, side, skill, agent, branch, ts in usage.values():
            if not since <= ts < until or model.startswith("<"):
                continue
            proc = f"subagente: {agent}" if side else (skill if skill == "(sin skill)" else f"skill: {skill}")
            name = skill.removeprefix("ai-kickstart:").removeprefix("ai-knowledge:")
            owner = next((p for p, cfg in PLUGINS.items() if name in cfg["skills"] or skill.startswith(f"{p}:")), "")
            key = (ts.date().isoformat(), project, model, proc, branch,
                   version_at(histories["ai-knowledge"], ts), version_at(histories["ai-kickstart"], ts), owner)
            c = recs[key]
            c["messages"] += 1
            c["input"] += u.get("input_tokens") or 0
            c["cache_write"] += u.get("cache_creation_input_tokens") or 0
            c["cache_read"] += u.get("cache_read_input_tokens") or 0
            c["output"] += u.get("output_tokens") or 0
    fields = ("messages", "input", "cache_write", "cache_read", "output")
    return {
        "records": [[*k, *(c[f] for f in fields)] for k, c in recs.items()],
        "time": [[d, p, round(a, 3), round(w, 3)] for (d, p), (a, w) in times.items()],
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Informe de tokens</title>
<style>
body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:1040px;color:#1f2937;background:#fafafa}
h1{margin-bottom:.2rem} h2{margin-top:2rem;border-bottom:1px solid #e5e7eb;padding-bottom:.3rem}
.note{color:#6b7280;font-size:.9rem}
.controls{display:flex;flex-wrap:wrap;gap:.75rem;align-items:end;margin:1rem 0;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:.75rem}
.controls label{display:flex;flex-direction:column;font-size:.8rem;color:#6b7280}
.controls select,.controls input{font-size:.9rem;padding:.2rem .3rem}
.cards{display:flex;flex-wrap:wrap;gap:.75rem}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:.75rem 1rem;min-width:150px}
.card .k{font-size:.8rem;color:#6b7280} .card .v{font-size:1.4rem;font-weight:600}
.bar{display:grid;grid-template-columns:300px 1fr 170px;gap:.5rem;align-items:center;margin:.3rem 0;cursor:default}
.track{background:#e5e7eb;border-radius:4px;height:14px;overflow:hidden}
.fill{display:block;background:#2563eb;height:100%}
.val{font-variant-numeric:tabular-nums;font-size:.85rem;color:#374151}
.name{font-size:.85rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.days{display:flex;align-items:flex-end;gap:3px;height:160px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px;overflow-x:auto}
.day{flex:1 0 14px;background:#60a5fa;border-radius:3px 3px 0 0;min-height:1px}
.daylabels{display:flex;gap:3px;font-size:.6rem;color:#6b7280;overflow:hidden}
.daylabels span{flex:1 0 14px;text-align:center}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.85rem}
th,td{border-bottom:1px solid #e5e7eb;padding:.35rem .5rem;text-align:left}
th{cursor:pointer;user-select:none;white-space:nowrap} th.sorted::after{content:" \25BC"} th.asc::after{content:" \25B2"}
td.num{text-align:right;font-variant-numeric:tabular-nums} td.name{max-width:380px}
</style></head><body>
<h1>Informe de tokens y tiempo</h1>
<p class="note">Periodo <span id="period"></span>. Generado __GENERATED__. Solo números: sin prompts, respuestas ni nombres de ficheros. Aproximado.</p>

<div class="controls">
  <label>Desde <input type="date" id="from"></label>
  <label>Hasta <input type="date" id="to"></label>
  <label>Proyecto <select id="project"></select></label>
  <label>Medir <select id="metric">
    <option value="tokens">tokens totales</option>
    <option value="output">tokens de salida</option>
    <option value="cache_write">escritura de caché</option>
    <option value="messages">mensajes</option>
  </select></label>
  <label>Agrupar por <select id="group">
    <option value="proc">proceso (skill o subagente)</option>
    <option value="model">modelo</option>
    <option value="branch">rama</option>
    <option value="project">proyecto</option>
  </select></label>
</div>

<div class="cards" id="cards"></div>
<h2>Consumo por día</h2>
<div class="days" id="days"></div>
<div class="daylabels" id="daylabels"></div>
<h2>Top por grupo</h2>
<div id="bars"></div>
<h2>Comparar versiones</h2>
<p class="note">Solo cuentan los mensajes cuya skill pertenece al plugin elegido, agrupados por la versión vigente en su fecha. Las horas activas no se pueden separar por versión.</p>
<div class="controls"><label>Plugin <select id="plugin">
  <option value="ai-knowledge">ai-knowledge</option>
  <option value="ai-kickstart">ai-kickstart</option>
</select></label></div>
<table><thead id="vhead"></thead><tbody id="vbody"></tbody></table>
<h2>Tabla completa</h2>
<p class="note">Pulsa una cabecera para ordenar.</p>
<table><thead id="thead"></thead><tbody id="tbody"></tbody></table>

<h2>Señales de fuga (sesiones)</h2>
__LEAKS__

<script>
const DATA = __DATA__;
const COLS = ["day", "project", "model", "proc", "branch", "kb", "ks", "owner", "messages", "input", "cache_write", "cache_read", "output"];
const RECS = DATA.records.map(r => Object.fromEntries(COLS.map((c, i) => [c, r[i]])));
const TIME = DATA.time.map(([day, project, active, waiting]) => ({day, project, active, waiting}));
const GROUP_LABEL = {proc: "proceso", model: "modelo", branch: "rama", project: "proyecto", kb: "versión ai-knowledge", ks: "versión ai-kickstart"};
const METRIC_LABEL = {tokens: "tokens", output: "salida", cache_write: "escritura de caché", messages: "mensajes"};
const $ = id => document.getElementById(id);
const fmt = n => Math.round(n).toLocaleString("es-ES");

const el = (tag, text, cls) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; };
const value = (r, metric) => metric === "tokens" ? r.input + r.cache_write + r.cache_read + r.output : r[metric];

let sortKey = null, sortDir = -1;

const projects = [...new Set(RECS.map(r => r.project))].sort();
const days = [...new Set(RECS.map(r => r.day))].sort();
for (const p of ["", ...projects]) {
  const o = el("option", p === "" ? "todos" : p); o.value = p; $("project").appendChild(o);
}
$("from").value = days[0] || "";
$("to").value = days[days.length - 1] || "";

function current() {
  const from = $("from").value, to = $("to").value, project = $("project").value;
  const metric = $("metric").value, group = $("group").value;
  const rows = RECS.filter(r => r.day >= from && r.day <= to && (project === "" || r.project === project));
  const time = TIME.filter(t => t.day >= from && t.day <= to && (project === "" || t.project === project));
  return {from, to, project, metric, group, rows, time};
}

function aggregate(rows, key, metric) {
  const m = new Map();
  for (const r of rows) {
    const k = r[key];
    const a = m.get(k) || {key: k, messages: 0, input: 0, cache_write: 0, cache_read: 0, output: 0};
    for (const f of ["messages", "input", "cache_write", "cache_read", "output"]) a[f] += r[f];
    m.set(k, a);
  }
  return [...m.values()].map(a => ({...a, tokens: a.input + a.cache_write + a.cache_read + a.output, score: value(a, metric)}));
}

function renderCards(s) {
  const sum = f => s.rows.reduce((t, r) => t + r[f], 0);
  const tokens = s.rows.reduce((t, r) => t + value(r, "tokens"), 0);
  const active = s.time.reduce((t, x) => t + x.active, 0), waiting = s.time.reduce((t, x) => t + x.waiting, 0);
  const cards = [["Mensajes", fmt(sum("messages"))], ["Tokens", fmt(tokens)], ["Salida", fmt(sum("output"))],
    ["Escritura de caché", fmt(sum("cache_write"))], ["Tiempo activo (h)", active.toFixed(1)], ["Espera (h)", waiting.toFixed(1)]];
  $("cards").replaceChildren(...cards.map(([k, v]) => {
    const c = el("div", undefined, "card"); c.append(el("div", k, "k"), el("div", v, "v")); return c;
  }));
}

function renderDays(s) {
  const perDay = new Map(s.rows.length ? [...new Set(s.rows.map(r => r.day))].sort().map(d => [d, 0]) : []);
  for (const r of s.rows) perDay.set(r.day, perDay.get(r.day) + value(r, s.metric));
  const max = Math.max(1, ...perDay.values());
  const bars = [...perDay].map(([d, v]) => {
    const b = el("div", undefined, "day");
    b.style.height = (v / max * 100).toFixed(1) + "%";
    b.title = `${d}: ${fmt(v)} ${METRIC_LABEL[s.metric]}`;
    return b;
  });
  $("days").replaceChildren(...(bars.length ? bars : [el("p", "Sin datos en este periodo.", "note")]));
  $("daylabels").replaceChildren(...[...perDay.keys()].map(d => el("span", d.slice(5))));
}

function renderBars(groups, s) {
  const top = [...groups].sort((a, b) => b.score - a.score).slice(0, 20);
  const max = Math.max(1, ...top.map(g => g.score));
  $("bars").replaceChildren(...(top.length ? top : [null]).map(g => {
    if (!g) return el("p", "Sin datos en este periodo.", "note");
    const row = el("div", undefined, "bar");
    row.title = `${g.key}\nmensajes ${fmt(g.messages)}, tokens ${fmt(g.tokens)}, salida ${fmt(g.output)}, escritura de caché ${fmt(g.cache_write)}`;
    const track = el("span", undefined, "track");
    const fill = el("span", undefined, "fill"); fill.style.width = (g.score / max * 100).toFixed(1) + "%";
    track.append(fill);
    row.append(el("span", g.key, "name"), track, el("span", `${fmt(g.score)} ${METRIC_LABEL[s.metric]}`, "val"));
    return row;
  }));
}

const COLUMNS = [["key", "grupo"], ["messages", "mensajes"], ["input", "entrada"], ["cache_write", "escritura caché"],
  ["cache_read", "lectura caché"], ["output", "salida"], ["tokens", "tokens"]];

function renderTable(groups, s) {
  const sorted = [...groups].sort((a, b) => {
    if (!sortKey) return b.score - a.score;
    const x = a[sortKey], y = b[sortKey];
    return (typeof x === "string" ? x.localeCompare(y) : x - y) * sortDir;
  });
  $("thead").replaceChildren(el("tr", undefined, undefined));
  const tr = $("thead").firstChild;
  for (const [key, label] of COLUMNS) {
    const th = el("th", GROUP_LABEL[s.group] && key === "key" ? `${GROUP_LABEL[s.group]}` : label);
    if (sortKey === key) th.className = sortDir < 0 ? "sorted" : "sorted asc";
    th.onclick = () => { sortDir = sortKey === key ? -sortDir : -1; sortKey = key; render(); };
    tr.append(th);
  }
  $("tbody").replaceChildren(...sorted.map(g => {
    const row = el("tr");
    for (const [key] of COLUMNS) row.append(key === "key" ? el("td", g.key, "name") : el("td", fmt(g[key]), "num"));
    return row;
  }));
}

function renderVersions(s) {
  const plugin = $("plugin").value;
  const verKey = plugin === "ai-knowledge" ? "kb" : "ks";
  const rows = s.rows.filter(r => r.owner === plugin);
  const byVer = new Map();
  for (const r of rows) {
    const v = r[verKey];
    const a = byVer.get(v) || {version: v, days: new Set(), messages: 0, input: 0, cache_write: 0, cache_read: 0, output: 0, first: r.day};
    a.days.add(r.day); a.first = r.day < a.first ? r.day : a.first;
    for (const f of ["messages", "input", "cache_write", "cache_read", "output"]) a[f] += r[f];
    byVer.set(v, a);
  }
  const list = [...byVer.values()].sort((a, b) => a.first.localeCompare(b.first));
  const head = ["versión", "primer día", "días", "mensajes", "tokens", "salida", "tokens por mensaje", "escritura caché"];
  $("vhead").replaceChildren(el("tr", undefined), ...[]);
  const tr = $("vhead").firstChild;
  for (const h of head) tr.append(el("th", h));
  $("vbody").replaceChildren(...(list.length ? list.map(a => {
    const tokens = a.input + a.cache_write + a.cache_read + a.output;
    const row = el("tr");
    row.append(el("td", a.version, "name"), el("td", a.first), el("td", String(a.days.size), "num"), el("td", fmt(a.messages), "num"),
      el("td", fmt(tokens), "num"), el("td", fmt(a.output), "num"), el("td", fmt(a.messages ? tokens / a.messages : 0), "num"),
      el("td", fmt(a.cache_write), "num"));
    return row;
  }) : [el("tr", undefined)]));
  if (!list.length) $("vbody").firstChild.append(el("td", "Sin mensajes de este plugin en el periodo.", "note"));
}

function render() {
  const s = current();
  $("period").textContent = `${s.from} a ${s.to}`;
  renderCards(s);
  renderDays(s);
  const groups = aggregate(s.rows, s.group, s.metric);
  renderBars(groups, s);
  renderTable(groups, s);
  renderVersions(s);
}

for (const id of ["from", "to", "project", "metric", "group", "plugin"]) $(id).addEventListener("change", () => { sortKey = null; render(); });
render();
</script>
</body></html>
"""


def leaks_html(rows):
    return (leak_table(rows, "cache_write", "escritura de caché") + leak_table(rows, "peak_ctx", "contexto máximo")
            + leak_table(rows, "reads_repeated", "lecturas repetidas"))


def html_report(since, until, rows):
    payload = json.dumps(build_dataset(since, until), ensure_ascii=False).replace("</", "<\\/")
    return (HTML_TEMPLATE.replace("__DATA__", payload).replace("__LEAKS__", leaks_html(rows))
            .replace("__GENERATED__", dt.datetime.now().strftime("%Y-%m-%d %H:%M")))


if __name__ == "__main__":
    since, until, md, html_path, periods = parse_args(sys.argv[1:])
    if "--by-version" in sys.argv:
        print(version_report(since, until))
    elif periods:
        print(periods_report(periods))
    elif html_path:
        rows = collect(since, until)
        os.makedirs(os.path.dirname(os.path.abspath(html_path)), exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_report(since, until, rows))
        print(f"Wrote {html_path}")
    else:
        print(text_report(since, until, collect(since, until), md))
