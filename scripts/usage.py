#!/usr/bin/env python3
"""Token and time report from past Claude Code sessions. Numbers only: no prompts, no answers.

  usage.py [YYYY-MM-DD] [--md]   (default: 30 days ago; --md writes a Markdown table)
Reads ~/.claude/projects/*/*.jsonl. Tokens are counted once per API message id (streamed events repeat it).
Active time: gaps between consecutive events of a session up to IDLE_SECONDS; longer gaps count as waiting
(approvals, breaks) and are reported apart. Approximate, by design.
"""
import collections
import datetime as dt
import glob
import json
import os
import sys

HOME = os.path.expanduser("~")
IDLE_SECONDS = 300
FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def parse_args(argv):
    md = "--md" in argv
    dates = [a for a in argv if not a.startswith("--")]
    since = dt.datetime.fromisoformat(dates[0]) if dates else dt.datetime.now() - dt.timedelta(days=30)
    return since, md


def read_session(path, since):
    usage, stamps = {}, []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("timestamp")
        if ts:
            stamps.append(dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None))
        msg = d.get("message") or {}
        if d.get("type") == "assistant" and msg.get("usage") and msg.get("id"):
            usage[msg["id"]] = (msg.get("model", "unknown"), msg["usage"])
    return usage, stamps


def report(since):
    by_model = collections.defaultdict(lambda: collections.Counter())
    by_project = collections.defaultdict(lambda: collections.Counter())
    active, waiting, sessions = 0.0, 0.0, 0
    for path in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl"):
        if os.path.getmtime(path) < since.timestamp():
            continue
        usage, stamps = read_session(path, since)
        stamps = sorted(s for s in stamps if s >= since)
        if not usage and not stamps:
            continue
        sessions += 1
        project = os.path.basename(os.path.dirname(path))
        for model, u in usage.values():
            model = model.removeprefix("eu.").removeprefix("us.").removeprefix("global.").removeprefix("anthropic.")
            if model.startswith("<"):
                continue
            for target in (by_model[model], by_project[project]):
                target["messages"] += 1
                for f in FIELDS:
                    target[f] += u.get(f, 0) or 0
        for a, b in zip(stamps, stamps[1:]):
            gap = (b - a).total_seconds()
            if gap <= IDLE_SECONDS:
                active += gap
            else:
                waiting += gap
    return by_model, by_project, sessions, active, waiting


def table(title, rows, md):
    head = "| name | messages | input | cache write | cache read | output |" if md else f"{title}"
    lines = [f"## {title}", "", head, "|---|---:|---:|---:|---:|---:|"] if md else [title]
    for name, c in sorted(rows.items(), key=lambda kv: -kv[1]["output_tokens"]):
        cells = [c["messages"], c["input_tokens"], c["cache_creation_input_tokens"], c["cache_read_input_tokens"], c["output_tokens"]]
        if md:
            lines.append(f"| {name} | " + " | ".join(f"{x:,}" for x in cells) + " |")
        else:
            lines.append(f"  {name}: " + ", ".join(f"{k}={v:,}" for k, v in zip(
                ["messages", "input", "cache_write", "cache_read", "output"], cells)))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    since, md = parse_args(sys.argv[1:])
    by_model, by_project, sessions, active, waiting = report(since)
    out = [f"# Usage since {since:%Y-%m-%d} ({sessions} sessions)", ""]
    out.append(table("By model", by_model, md))
    out.append(table("By project folder", by_project, md))
    out.append(f"Active time ~{active / 3600:.1f} h; waiting (gaps over {IDLE_SECONDS // 60} min) ~{waiting / 3600:.1f} h. Approximate.")
    print("\n".join(out))
