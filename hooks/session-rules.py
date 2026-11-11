#!/usr/bin/env python3
"""SessionStart: add the knowledge-curation rules (and the user's extra rules) to the session context. Keep it short: it is always-on."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import load_config  # noqa: E402

cfg = load_config()
if not cfg["knowledge_dirs"]:
    print("ai-knowledge is installed but not configured: when the user asks about notes or research, suggest running the `ai-knowledge:setup` skill first (one-time, ~2 minutes).")
    sys.exit(0)
if not cfg["session_rules"]:
    sys.exit(0)
kb = Path(__file__).resolve().parent.parent / "scripts" / "kb.py"
rules = [
    f"Knowledge first: before researching a technical question, search the user's notes with `python3 {kb} <keywords>` and read only the returned line ranges. Research only on a weak or missing hit.",
    "Save what you verify: a reusable fact learned by research or by running something goes into the notes (skill `save-knowledge`) with its source and date and a trust tag (`verified YYYY-MM-DD`, `from <source> YYYY-MM-DD`, `re-check`, `BROKEN YYYY-MM-DD: why`). Report it in one line: `Knowledge saved: <path>`. No approval needed; never save secrets or personal data.",
    "Propose, don't apply, changes to skills, agents, hooks or rules: end the reply with `AI config proposal: <create|update> <path>: <why>` plus 1-3 bullets and `Apply?`. Declined: don't re-propose in this chat.",
    "Never present a `from`, `re-check` or `BROKEN` fact as verified.",
]
if cfg["notes_language"]:
    rules.append(f"Notes are written in {cfg['notes_language']}.")
rules += cfg.get("extra_rules", [])
print("ai-knowledge rules:\n" + "\n".join(f"- {r}" for r in rules))
