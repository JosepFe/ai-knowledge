# AI Knowledge

A Claude Code plugin for **knowledge management and research**: Claude searches your own markdown notes before researching, researches with sources, saves what it verifies back into your notes with a trust tag and date, keeps stale notes fresh, can pit two agents against each other for decisions, and learns from your past sessions to improve your setup. A hook warns when a secret shows up in any tool output.

Works with any folder of markdown notes (an Obsidian vault, a docs folder, a wiki checkout). Companion to [ai-kickstart](https://github.com/JosepFe/ai-kickstart), which covers building software; this one covers knowing things.

## The loop

```
question ─▶ search your notes (BM25) ─▶ hit and fresh? ─▶ answer from the notes
                     │ weak / stale
                     ▼
             research: primary sources, run it locally, cross-check
                     ▼
             answer with citations ─▶ save verified facts (source + date + trust tag)
                                                   ▼
             weak searches, stale notes, sessions ─▶ refresh notes / config-review proposals
```

## What's included

| Type | Name | Purpose |
|---|---|---|
| Skill | `knowledge-search` | Keyword (BM25) search over your notes, plus health signals: weak searches, stale notes, oversized files, always-on budget |
| Skill | `research` | Notes first → sources → cross-check → cited answer → save findings. Quick / standard / deep |
| Skill | `save-knowledge` | Save a verified fact into the right note, with source, date and trust tag; update instead of duplicating |
| Skill | `knowledge-refresh` | Re-verify only notes past their review date or flagged `re-check` / `BROKEN` |
| Skill | `duel` | Two independent subagents (different models or stances), optional debate, a judge decides. Opt-in: ~3x cost |
| Skill | `config-review` | Mine past sessions for repeated work, corrections, knowledge gaps, token waste and dead weight; ranked proposals |
| Hook | SessionStart | Adds the short curation rules (notes first, save what you verify, propose config changes) to every session, plus your own rules |
| Hook | PostToolUse | Warns `SECRET EXPOSED` when a token or key appears in a tool call or its output; logs it masked for rotation |
| Scripts | `scripts/kb.py`, `scripts/sessions.py` | The search engine and the session digest (Python 3, no dependencies) |

### Trust tags

Every saved fact carries one: `verified YYYY-MM-DD` (checked by running it or against the primary source), `from <source> YYYY-MM-DD` (copied, not checked), `re-check` (probably outdated) or `BROKEN YYYY-MM-DD: why` (no longer works, kept so nobody retries it). Notes that go stale carry `Last reviewed: YYYY-MM-DD` under the title.

## Installation

```
/plugin marketplace add JosepFe/ai-knowledge
/plugin install ai-knowledge@ai-knowledge
```

Then tell it where your notes are, in `~/.config/ai-knowledge/config.json` (see [`config.example.json`](config.example.json)):

| Key | Meaning |
|---|---|
| `knowledge_dirs` | Folders with your markdown notes (searched recursively) |
| `default_notes_dir` | Where new notes go when nothing fits |
| `save_with` | Optional: name of your own skill that knows your note format (folders, frontmatter, indexes); `save-knowledge` follows it |
| `extra_rules` | Your own always-on rules (language, what must never go into notes) |
| `weak_score`, `max_note_kb` | Thresholds for weak searches and oversized notes |

Without a config the hooks stay silent and the skills ask where your notes are. Requires Python 3. State (search log, masked secret log) lives in `~/.local/state/ai-knowledge/`.

## Usage

```
do I have notes on traefik certificates?     → knowledge-search
research whether X supports Y / compare A vs B → research
save this                                    → save-knowledge
refresh my old notes                         → knowledge-refresh
give me two opinions on this design          → duel
what do we keep repeating? / review my setup → config-review
```

The skills also understand requests in Spanish.

## License

[MIT](LICENSE)
