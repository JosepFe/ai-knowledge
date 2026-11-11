---
name: knowledge-search
description: Search the user's own notes (markdown knowledge base) by keyword before researching, and check the notes' health (weak searches, stale notes, size). Use when unsure whether the notes already cover something, "do I have notes on X", "busca en mis notas", "qué tengo sobre X", or before any research.
---

# Knowledge search

The notebook is the set of folders in `~/.config/ai-knowledge/config.json` (`knowledge_dirs`). The script is `../../scripts/kb.py` relative to this skill's folder (`<plugin>` below = the plugin root).

## Search first

```bash
python3 <plugin>/scripts/kb.py <keywords> [--top N]
```

- BM25 keyword ranking per heading section; accents and case are ignored. Prints `score  file:line  heading` plus matching lines.
- Read only the returned line ranges, not whole files.
- Keywords, not questions: use the words the notes would use (tool names, exact error text, both English and the notes' language). One retry with synonyms before giving up.
- A `WEAK` line means the notes don't really cover it: research (skill `research`) and save the result (skill `save-knowledge`). Every search is logged in `~/.local/state/ai-knowledge/searches.log`.

## Health signals

| Command | Shows | Next step |
|---|---|---|
| `kb.py --misses [days]` | Weak searches, most repeated first | Research and save the ones asked 2+ times |
| `kb.py --stale [days]` | Notes reviewed more than N days ago (default 180) and facts marked `re-check` / `BROKEN` | Skill `knowledge-refresh` |
| `kb.py --stats` | Notes over `max_note_kb`, skills over 80 lines, always-on text over 13k chars, weak-search ratio | Split notes; move skill detail to reference files; trim always-on rules (propose first) |

Weak searches over 20% for weeks, or more than ~500 notes: propose a semantic (embedding) search with a local model. Not before.
