---
name: usage-report
description: Token, time and process report from past Claude Code sessions (by model, skill, subagent, branch, plugin version, leak signals), with an optional interactive HTML. Use when asked about tokens, cost, time spent, which process or skill uses the most, comparing periods or plugin versions, or where tokens leak.
---

# Usage report

The script is `../../scripts/usage.py` relative to this skill's folder. It reads the local session transcripts only and prints numbers, never prompts or answers. Run it from the plugin root.

## Choose the period

Dates are local days. The end date is excluded. Default: the last 30 days.

| Ask | Command |
|---|---|
| Summary for a period | `python3 scripts/usage.py 2026-11-01 2026-11-20` |
| Markdown tables to paste | `python3 scripts/usage.py 2026-11-01 --md` |
| Compare periods side by side | `python3 scripts/usage.py --periods 2026-10-01:2026-10-31 2026-11-01:2026-11-30` |
| Skills and subagents by plugin version | `python3 scripts/usage.py 2026-11-01 --by-version` |
| Interactive report | `python3 scripts/usage.py 2026-11-01 --html` |

The HTML goes to `internal_docs/usage-report.html` (git-ignored, personal data). Tell the user the path and that it opens in a browser. Do not paste the HTML in the chat.

## What to return

Give the same shape each time, in the user's language:

1. **Totals:** sessions, tokens, output tokens, cache writes, active and waiting hours.
2. **By model** and **by process** (skill or subagent), top 5 each.
3. **By branch** when the user works on kickstart stories or epics.
4. **Versions** when asked, from `--by-version`.
5. **Leak signals:** top sessions by cache writes, peak context and repeated reads.

Then say what to check first. Keep the explanation short.

## Limits to state

- Attribution is approximate: each message counts for the last skill invoked in its session, and subagents by their type.
- Waiting time includes breaks and approvals. It is not work.
- A plugin version only counts when the skill name is known to the script. Unknown skills are not assigned to a version.
- Do not claim a saving or a regression from one run. Compare two runs, or two periods, before concluding anything.
