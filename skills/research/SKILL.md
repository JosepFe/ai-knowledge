---
name: research
description: Research a mostly technical question end to end - notes first, then sources, cross-check, a short answer with citations, and the verified findings saved to the user's notes. Use when the user asks to investigate, compare, evaluate or find out something ("investiga", "compara X e Y", "qué opción es mejor", "research", "evaluate", "is X still true"). Optional duel mode for decisions.
---

# Research

## 1. Frame (one short message, no questions unless it's ambiguous)

Restate the question, what a good answer looks like (a fact, a comparison table, a recommendation) and the depth: **quick** (one answer, 2+ sources), **standard** (comparison or how-to, 3-5 sources) or **deep** (market or architecture decision: use the `deep-research` skill if available).

## 2. Notes first

`knowledge-search` with 2-3 keyword sets. If the notes answer it and the fact is not stale or `re-check`, answer from the notes (cite `file:line`) and stop.

## 3. Sources

- Primary first: official docs, changelogs, release notes, the repo itself (`gh`, README, issues), specs. Then reputable secondary sources. Forums and blogs only to find leads.
- Prefer running a check locally (`--version`, `--help`, a tiny test) over reading about it: that turns `from` into `verified`.
- Record each source as you go: URL or command, date, what it says.
- Independent reads in parallel; heavy mechanical reading (long docs, many pages) can go to a cheap subagent that returns only the facts with their source.

## 4. Cross-check

- Every claim in the answer has a source. Claims with a single secondary source are marked as such.
- Conflicting sources: say so, prefer the newer primary one, and explain the difference in one line.
- Versions and dates matter: state which version or date a fact applies to.

## 5. Answer

Lead with the answer or recommendation, then a table when comparing (criteria as rows), then sources as links. Say what was not verified. Keep it short; offer depth instead of dumping it.

## 6. Save

Hand the reusable findings to `save-knowledge` (trust tags, `Last reviewed` for anything that will go stale). Report `Knowledge saved: <path>`.

## Duel mode

For a decision with real trade-offs ("which one should I use", architecture, buying something expensive), or when the user asks for "two opinions": run the `duel` skill in `review` or `build` mode with this question as the brief, then save the verdict and its reasons.
