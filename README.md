# AI Knowledge

**Make Claude Code use — and grow — your own notes.**

A Claude Code plugin for knowledge management and research. Before researching anything, Claude searches your markdown notes; when it does research, it cites sources and saves what it verified back into your notes, with a date and a trust tag. Stale notes get re-checked, decisions can get two independent opinions, and your past sessions are mined to improve your setup. A hook warns you whenever a secret shows up in a tool's output.

Works with any folder of markdown notes: an Obsidian vault, a docs folder, a wiki checkout. Everything runs locally; nothing is sent anywhere except what Claude Code already sends.

Companion to [ai-kickstart](https://github.com/JosepFe/ai-kickstart) (building software). This one is about knowing things.

---

## Getting started (5 minutes)

### 1. Prerequisites

| Need | Check | Install |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | `claude --version` | see the Claude Code docs |
| Python 3.8+ (no packages needed) | `python3 --version` | Debian/Ubuntu `sudo apt install python3` · macOS `brew install python` · Windows: use WSL or [python.org](https://www.python.org/downloads/) |
| A folder of markdown notes | — | any folder works, even an empty one to start |

### 2. Install

Inside Claude Code:

```
/plugin marketplace add JosepFe/ai-knowledge
/plugin install ai-knowledge@ai-knowledge
```

### 3. Configure (one-time questionnaire)

Start a new session and say:

```
set up ai-knowledge
```

Claude looks for your notes (Obsidian vaults, folders with many `.md` files) and asks one short round of questions:

1. Which folders to search.
2. Where new notes go when nothing fits.
3. The language your notes are written in.
4. Your note format: it reads a few notes and proposes what it sees (frontmatter, wikilinks, headings), or uses your own note-writing skill.
5. What must never be saved (for example employer or client data). Secrets and personal data are always excluded.
6. Which hooks you want.

It writes `~/.config/ai-knowledge/config.json`, runs a test search and shows you the result. Run it again any time to change something. Until you configure it, the plugin only reminds Claude to suggest the setup.

### 4. First steps

```
do I have notes on <topic>?
research whether <tool> supports <feature>
compare <A> and <B> for <use case>, give me two opinions
```

From now on, a verified fact found while working ends up in your notes, and Claude says so in one line: `Knowledge saved: <path>`.

---

## How it works

```
question ─▶ search your notes (BM25) ─▶ found and fresh? ─▶ answer from your notes
                     │ weak / stale
                     ▼
             research: primary sources, run it locally, cross-check
                     ▼
             answer with citations ─▶ save verified facts (source + date + trust tag)
                                                   ▼
             weak searches, stale notes, sessions ─▶ refresh notes / config-review proposals
```

### Trust tags

Every saved fact carries one, so you know how much to rely on it:

| Tag | Meaning |
|---|---|
| `verified YYYY-MM-DD` | Checked by running it or against the primary source |
| `from <source> YYYY-MM-DD` | Copied from docs or a post, not checked |
| `re-check` | Probably outdated |
| `BROKEN YYYY-MM-DD: why` | No longer works; kept so nobody tries it again |

Notes that go stale (versions, tools, comparisons) carry `Last reviewed: YYYY-MM-DD` under the title, so `knowledge-refresh` can find them.

## What's included

| Type | Name | What it does | Say |
|---|---|---|---|
| Skill | `setup` | The one-time questionnaire above | "set up ai-knowledge" |
| Skill | `knowledge-search` | Keyword (BM25) search over your notes, ignoring accents and case; health signals (weak searches, stale notes, oversized files) | "do I have notes on X?" |
| Skill | `research` | Notes first → sources → cross-check → cited answer → save findings. Quick, standard or deep | "research…", "compare X and Y" |
| Skill | `save-knowledge` | Save a verified fact into the right note with source, date and trust tag; updates instead of duplicating | "save this" |
| Skill | `knowledge-refresh` | Re-verify only notes past their review date or flagged `re-check` / `BROKEN` | "refresh my notes" |
| Skill | `duel` | Two independent subagents (different models or stances), optional debate, a judge decides. About 3x the cost of one answer, so opt-in | "two opinions", "debate this" |
| Skill | `config-review` | Mine past sessions for repeated work, your corrections, knowledge gaps, token waste and unused skills; ranked proposals | "what do we keep repeating?" |
| Hook | SessionStart | Adds 4 short rules to each session: notes first, save what you verify, propose (don't apply) config changes, don't present unverified facts as verified. Plus your own rules | automatic |
| Hook | PostToolUse | Warns `SECRET EXPOSED` when a token or private key appears in a tool call or its output; logs it masked (last 4 characters) | automatic |

The skills also understand requests in Spanish.

## What changes in your sessions

- **Always on (if enabled)**: about 5 short lines of rules added at session start, and a millisecond-scale secret check after each tool call.
- **Claude may write to your notes**: verified facts, without asking, always announced as `Knowledge saved: <path>`. Changes to skills, hooks or rules are only proposed and need your "yes".
- **Nothing else** is installed or modified outside your notes and the plugin's own state folder.

## Privacy and files

| Path | Content |
|---|---|
| `~/.config/ai-knowledge/config.json` | Your settings (folders, language, rules) |
| `~/.local/state/ai-knowledge/searches.log` | Your search queries and scores (to detect knowledge gaps) |
| `~/.local/state/ai-knowledge/exposed-secrets.log` | Type, tool and last 4 characters of exposed secrets; never the value |

All local. Delete them any time.

## Configuration reference

`~/.config/ai-knowledge/config.json` (see [`config.example.json`](config.example.json)):

| Key | Default | Meaning |
|---|---|---|
| `knowledge_dirs` | `[]` | Folders with your markdown notes, searched recursively |
| `default_notes_dir` | `""` | Where new notes go when nothing fits |
| `notes_language` | `""` | Language of new notes |
| `note_conventions` | `""` | How your notes look (frontmatter, links, headings) |
| `save_with` | `""` | Name of your own skill that writes notes your way; `save-knowledge` follows it |
| `extra_rules` | `[]` | Your own always-on rules |
| `session_rules`, `secret_scan` | `true` | Turn each hook on or off |
| `weak_score` | `4.0` | Best search score below this counts as a knowledge gap |
| `min_coverage` | `0.5` | With 2+ keywords, if no top-5 result holds this share of them, the search is weak (one common word scoring high is not an answer) |
| `max_note_kb` | `16` | Notes above this size are flagged |
| `exclude` | `.obsidian`, `.git`… | Folder names skipped when searching |

## Command-line tools

The skills run these for you; they are also handy directly:

```bash
K=$(ls -d ~/.claude/plugins/cache/ai-knowledge/ai-knowledge/*/scripts | tail -1)
python3 $K/kb.py traefik certificate      # search
python3 $K/kb.py --misses 30              # weak searches in the last 30 days
python3 $K/kb.py --stale 180              # notes not reviewed in 6 months + re-check/BROKEN facts
python3 $K/kb.py --stats                  # oversized notes, long skills, always-on text
python3 $K/sessions.py 2026-11-01         # digest of your sessions since a date
```

## Updating and uninstalling

```
/plugin marketplace update ai-knowledge
/plugin uninstall ai-knowledge@ai-knowledge
```

Uninstalling leaves your notes and `~/.config/ai-knowledge/` untouched; delete that folder and `~/.local/state/ai-knowledge/` if you want everything gone.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "ai-knowledge is installed but not configured" | Run "set up ai-knowledge" |
| Searches find nothing useful | Use the words your notes use (tool names, error text), in your notes' language; check `knowledge_dirs` |
| Too many `WEAK` searches, or none | Adjust `weak_score` or `min_coverage` (`kb.py --misses` shows the history) |
| `SECRET EXPOSED` on an example token | Expected when example text uses the real token format; rotate if it was real |
| Hooks not running | `python3` must be on the `PATH` Claude Code sees; restart the session after installing |

## License

[MIT](LICENSE)
