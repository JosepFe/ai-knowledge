# AI Knowledge

**Make Claude Code use — and grow — your own notes.**

A Claude Code plugin for knowledge management and research. Before researching, Claude searches your markdown notes; verified findings are saved back into them with a source, a date and a trust tag. It also includes skills for usage reports, releases, commits, language practices and troubleshooting commands, plus a hook that warns when a secret shows up in a tool's output.

Works with any folder of markdown notes. Everything runs locally.

Companion to [ai-kickstart](https://github.com/JosepFe/ai-kickstart), which is about building software.

## Install

Needs Claude Code and Python 3.8+ (no packages). Inside Claude Code:

```
/plugin marketplace add JosepFe/ai-knowledge
/plugin install ai-knowledge@ai-knowledge
```

Then start a session and say `set up ai-knowledge`. The one-time questionnaire asks which folders to search, where new notes go, the language, your note format, what must never be saved, and which hooks to enable. It writes `~/.config/ai-knowledge/config.json` and runs a test search.

Until you configure it, the plugin only reminds Claude to suggest the setup.

## Use

```
do I have notes on <topic>?
research whether <tool> supports <feature>
compare <A> and <B> for <use case>, give me two opinions
```

When Claude saves a fact, it says so in one line: `Knowledge saved: <path>`.

## What it contains

| Name | Type | What it does |
|---|---|---|
| `setup` | skill | One-time questionnaire and test search |
| `knowledge-search` | skill | Keyword search over your notes, with health signals (weak searches, stale notes) |
| `research` | skill | Notes first, then sources, cross-check and a cited answer; saves what it verified |
| `save-knowledge` | skill | Saves a verified fact with source, date and trust tag; updates instead of duplicating |
| `knowledge-refresh` | skill | Re-verifies only notes past their review date or flagged `re-check` / `BROKEN` |
| `duel` | skill | Two independent opinions and a judge. About 3x the cost, so opt-in |
| `config-review` | skill | Mines past sessions for repeated work, corrections and token waste; ranked proposals |
| `usage-report` | skill | Tokens, time and processes from past sessions, with periods, versions and HTML |
| `release` | skill | Picks the version bump, writes release notes from commits, tags after your approval |
| `commits` | skill | Conventional commit messages whose body feeds the release notes |
| `languages` | skill | Official practices and lint/format commands per language |
| `troubleshooting-command-patterns` | skill | Proven commands per technology |
| `explorer` | agent | Haiku, read-only: reads docs, logs and repos, returns a short report |
| `implementer` | agent | Sonnet, files only (no Bash): writes code, config or diagrams from a closed brief |
| SessionStart | hook | Adds a few short rules to each session |
| PostToolUse | hook | Warns `SECRET EXPOSED` when a token appears in a tool's output; logs it masked |
| `mods/secret-entry` | mod | `/secrets` panel to save one value into any file. See [docs/mcp-and-secrets.md](docs/mcp-and-secrets.md) |

Trust tags on saved facts: `verified YYYY-MM-DD`, `from <source> YYYY-MM-DD`, `re-check`, `BROKEN YYYY-MM-DD: why`.

## Configuration

Settings live in `~/.config/ai-knowledge/config.json`. The full list is in [config.example.json](config.example.json). The keys you are most likely to change:

| Key | Meaning |
|---|---|
| `knowledge_dirs` | Folders with your notes, searched recursively |
| `default_notes_dir` | Where new notes go when nothing fits |
| `notes_language`, `note_conventions` | Language and layout of your notes |
| `save_with` | Your own skill that writes notes your way |
| `extra_rules` | Your own always-on rules |
| `weak_score`, `weak_ratio`, `min_coverage` | When a search counts as a knowledge gap |
| `session_rules`, `secret_scan` | Turn each hook on or off |

## Privacy

Everything stays on your machine:

- `~/.config/ai-knowledge/config.json`: your settings.
- `~/.local/state/ai-knowledge/searches.log`: your search queries and scores.
- `~/.local/state/ai-knowledge/exposed-secrets.log`: type and last 4 characters of an exposed secret. Never the value.

Claude writes to your notes only verified facts, and announces each one. Changes to skills, hooks or rules are proposed and need your approval.

## Command-line tools

```bash
K=$(ls -d ~/.claude/plugins/cache/ai-knowledge/ai-knowledge/*/scripts | tail -1)
python3 $K/kb.py <keywords>               # search
python3 $K/kb.py --misses 30              # weak searches in the last 30 days
python3 $K/kb.py --stale 180              # notes not reviewed recently
python3 $K/usage.py 2026-11-01 --md       # tokens and time since a date (numbers only)
```

## Updating and uninstalling

```
/plugin marketplace update ai-knowledge
/plugin uninstall ai-knowledge@ai-knowledge
```

Uninstalling keeps your notes and `~/.config/ai-knowledge/`. Delete those folders too if you want everything gone.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "installed but not configured" | Run "set up ai-knowledge" |
| Searches find nothing useful | Use the words your notes use, in their language; check `knowledge_dirs` |
| Too many `WEAK` searches, or none | Adjust `weak_score` or `min_coverage`; `kb.py --misses` shows the history |
| `SECRET EXPOSED` on an example token | Expected with example text; rotate only if the token was real |
| Hooks not running | `python3` must be on the `PATH` Claude Code sees; restart the session |

## License

[MIT](LICENSE)
