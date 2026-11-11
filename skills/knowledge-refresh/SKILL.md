---
name: knowledge-refresh
description: Re-verify notes that go stale (versions, tools, comparisons, setups) - only the ones past their review date or marked re-check/BROKEN - and update their facts, trust tags and review date. Use when the user says "refresh my notes", "are my notes still current", "refresca Knowledge", "revisa notas viejas" or periodically.
---

# Knowledge refresh

`<plugin>` is two folders up from this skill\'s folder (the `ai-knowledge` plugin root).

Change-driven: re-check only what is old or flagged, never the whole notebook.

1. **Plan**: `python3 <plugin>/scripts/kb.py --stale [days]` (default 180). Show a table `note | last reviewed | flagged facts | action (re-check / skip)` and wait for an "ok" if there are more than ~5 notes.
2. **For each note**:
   - Find what the note claims that can change: versions, flags, prices, limits, URLs, "X is the default".
   - Check against the primary source or by running it (`--version`, `--help`, changelog since the review date). For a repo or tool: only what changed since the date (release notes, `git log --since`).
   - Update in place: fix wrong facts, refresh trust tags (`verified <today>`), mark what you could not check as `re-check`, what no longer works as `BROKEN <today>: why`, remove facts about things that no longer exist.
   - Update `Last reviewed` / `Última revisión` to today.
3. **Many notes** (5+): one subagent per group of notes, in parallel, each editing only its notes and returning max 8 lines (notes updated, facts fixed, facts it could not verify).
4. **Report**: `note | facts fixed | re-check | BROKEN`, and any note that should be split, merged or deleted (propose; don't delete).
