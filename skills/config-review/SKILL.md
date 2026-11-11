---
name: config-review
description: Learn from past Claude Code sessions - repeated workflows, user corrections, knowledge gaps, stale or unused skills, token waste - and propose ranked improvements (skill, agent, hook, rule, note). Use when the user says "review my AI setup", "what do we keep repeating", "what can we automate", "learn from past chats", "detecta repeticiones", "qué podemos automatizar".
---

# Config review

`<plugin>` is two folders up from this skill\'s folder (the `ai-knowledge` plugin root).

## 1. Gather (cheap, filtered)

- `python3 <plugin>/scripts/sessions.py [YYYY-MM-DD]` (default 30 days): requests, slash commands, likely corrections, repeated Bash descriptions, skills and subagents used. Write it to a scratch file and read it; for a long digest, a cheap subagent returns only the findings.
- `python3 <plugin>/scripts/kb.py --misses <days>` and `--stats`.
- What already exists: `~/.claude/CLAUDE.md`, memory, `~/.claude/skills/`, `~/.claude/agents/`, installed plugins' skills, hooks in `~/.claude/settings.json`.

## 2. Find (group by intent, not by wording)

| Kind | Signal | Usual fix |
|---|---|---|
| Repeated work | Same task 3+ times (2 if each time is long) with no skill | Skill, script or subagent |
| Corrections | The user said no / wrong / "I told you" | One rule line (CLAUDE.md) or a hook if it must never happen |
| Knowledge gaps | Weak searches asked 2+ times; facts researched in a chat but not saved | Research once and save (no approval) |
| Repeated discovery | Same paths, IDs, commands or docs looked up across sessions | A note or a reference table |
| Stale guidance | A skill or rule that was wrong, outdated or missing a step | Update it |
| Token waste | Huge outputs, re-reads, retried failing commands, needless subagents or premium models, cuts and resumes | Rule, cheaper subagent, bounded command |
| Dead weight | Skills or agents never used, duplicated, or always-on text only some tasks need | Merge, shorten or delete (propose) |
| Covered but still repeated | A skill exists yet the task is still done by hand | Its description doesn't trigger, or it doesn't work |

## 3. Propose

One ranked table, most savings first: `# | finding (evidence: dates) | change (create / update / delete + path) | saves`. Max 8 rows, drop anything that fails the bar (nothing speculative). Ask which rows to apply; apply only those and confirm one line per file. Knowledge facts are saved without asking.
