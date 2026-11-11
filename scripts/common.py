"""Shared helpers: config and state paths for ai-knowledge."""
import json
import os
from pathlib import Path

HOME = Path.home()
CONFIG = Path(os.environ.get("AI_KNOWLEDGE_CONFIG", HOME / ".config" / "ai-knowledge" / "config.json"))
STATE = Path(os.environ.get("AI_KNOWLEDGE_STATE", HOME / ".local" / "state" / "ai-knowledge"))

DEFAULTS = {
    "knowledge_dirs": [],      # folders with markdown notes (the "notebook")
    "exclude": [".obsidian", ".git", "node_modules", ".trash"],
    "save_with": "",           # optional skill that knows the user's note format (e.g. "apunta-knowledge")
    "default_notes_dir": "",   # where new notes go when nothing fits
    "extra_rules": [],         # personal rules added to the session rules
    "weak_score": 4.0,         # top BM25 score below this counts as a weak search
    "min_coverage": 0.5,       # with 2+ keywords, a top-5 result must hold this share of them (else weak)
    "max_note_kb": 16,         # notes above this size are flagged by --stats
    "notes_language": "",      # language new notes are written in (e.g. "English", "Spanish")
    "note_conventions": "",    # how notes look when there is no save_with skill (frontmatter, links, headings)
    "session_rules": True,     # SessionStart hook adds the curation rules
    "secret_scan": True,       # PostToolUse hook warns about exposed secrets
}


def load_config():
    cfg = dict(DEFAULTS)
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    cfg["knowledge_dirs"] = [str(Path(os.path.expanduser(d))) for d in cfg["knowledge_dirs"]]
    return cfg


def state_file(name):
    STATE.mkdir(parents=True, exist_ok=True)
    return STATE / name
