---
name: setup
description: One-time setup of the ai-knowledge plugin - find the user's markdown notes, ask a short questionnaire (folders, where new notes go, language, note format, what must never be saved, hooks) and write ~/.config/ai-knowledge/config.json, then run a test search. Use right after installing, when the session says ai-knowledge is not configured, or when the user says "set up ai-knowledge", "configure my notes", "configura ai-knowledge".
---

# Set up ai-knowledge

Config file: `~/.config/ai-knowledge/config.json` (keys and defaults in `../../config.example.json` and `../../scripts/common.py`). If it exists, show it and ask what to change instead of starting over. Reply in the user's language.

## 1. Check

`python3 --version` (3.8+). Missing: give the install command for their OS and stop.

## 2. Find candidate folders (read-only, bounded)

```bash
find ~ -maxdepth 5 -type d -name .obsidian -not -path '*/.Trash*' 2>/dev/null | head -20     # Obsidian vaults
find ~ -maxdepth 4 -type f -name '*.md' -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null \
  | xargs -r -n1 dirname | sort | uniq -c | sort -rn | head -15                              # folders with many notes
```

Skip code repos (a `.git` next to a README) unless the user says they keep notes there.

## 3. Questionnaire (one round, options plus "other")

1. **Folders to search**: the candidates found (multi-select). Inside a big vault, suggest the knowledge folders rather than the whole vault (journals and to-do lists add noise).
2. **Where new notes go** when nothing fits: a folder inside the first choice (e.g. `Knowledge/Inbox`) or another path.
3. **Notes language**: English · Spanish · other.
4. **Note format**: read 3-5 recent notes from the chosen folders and propose what you see (frontmatter keys, `[[wikilinks]]` or markdown links, heading style, one topic per note). Options: "use what you found" · "plain markdown" · "I have a skill for my notes" (its name goes in `save_with`).
5. **Never save**: options to combine: employer or client data · personal data of other people · nothing extra (secrets and personal data are always excluded).
6. **Hooks**: both (recommended) · only the secret warning · only the session rules · none.

## 4. Write and test

- Write the config (create the folder), with `~` expanded paths, `notes_language`, `note_conventions` (one or two lines describing the format found), `save_with` if any, `extra_rules` from question 5, `session_rules` and `secret_scan` from question 6. Show the file.
- Test: `python3 ../../scripts/kb.py <a word from one of their note titles> --top 3` and `python3 ../../scripts/kb.py --stats | head`. Show both.
- Tell them: the hooks apply from the next session; try "do I have notes on <topic>?" or "research <question>"; re-run this skill any time to change the setup.
