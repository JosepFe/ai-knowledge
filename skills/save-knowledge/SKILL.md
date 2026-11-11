---
name: save-knowledge
description: Save a verified, reusable fact or finding into the user's notes with source, date and trust tag, updating an existing note instead of duplicating. Use after research or after verifying something by running it, or when the user says "save this", "note this down", "apunta esto", "guárdalo en mis notas".
---

# Save knowledge

Config: `~/.config/ai-knowledge/config.json`. If it names a skill in `save_with` (the user's own note conventions: folders, frontmatter, language, indexes), **follow that skill for where and how to write**, and apply the rules below on top. Otherwise write to `default_notes_dir`.

## What to save

- Verified, reusable facts a future chat would otherwise rediscover: how something works, a command that solved a problem, a version or limit, a comparison result, a decision and why.
- Not: guesses, one-off values (an ID, a pod name), things any official doc says in the first paragraph, the chat's own history, **secrets, tokens, passwords or personal data**.

## How

1. **Search first** (`knowledge-search`) and update the existing note or line; fix facts that turned out wrong instead of adding contradicting ones.
2. **One fact per bullet** with its source and a trust tag:
   - `verified YYYY-MM-DD` — checked by running it or against the primary source.
   - `from <source> YYYY-MM-DD` — copied from docs, a post or an answer, not checked.
   - `re-check` — probably outdated, to verify.
   - `BROKEN YYYY-MM-DD: <why>` — no longer works; keep it so nobody retries it.
   - Example: `- gitleaks 8.19+ replaces protect/detect with git/dir subcommands. Source: gitleaks --help v8.30.1, verified 2026-11-10.`
3. **Notes that go stale** (versions, prices, tool comparisons, service setups) get a line under the title: `Last reviewed: YYYY-MM-DD` (or `Última revisión: YYYY-MM-DD` in Spanish notes), so `knowledge-refresh` can find them.
4. A note that grows into a repeatable workflow (3+ steps used more than once): propose turning it into a skill (`config-review`).
5. Report in one line: `Knowledge saved: <path>`. No approval needed for facts.
