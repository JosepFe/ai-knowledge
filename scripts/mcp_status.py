#!/usr/bin/env python3
"""Read-only status of the MCP servers: what ai-config defines, what Claude Code has, and whether each token file exists.

  mcp_status.py            table: server, group, in Claude Code, token file present
  mcp_status.py --json     the same as JSON

Needs `ai_config_dir` in ~/.config/ai-knowledge/config.json (the ai-config repo). Token files are checked for existence only; their contents are never read or printed.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CONFIG, HOME, load_config  # noqa: E402

CFG = load_config()


def template(repo):
    text = (repo / "mcp" / "mcp.template.jsonc").read_text(encoding="utf-8")
    return json.loads(re.sub(r"(?m)^\s*//.*$", "", text))["servers"]


def groups(repo):
    path = repo / "mcp" / "groups.json"
    found = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {server: group for group, servers in found.items() for server in servers}


def claude_servers():
    path = HOME / ".claude.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})


NEW_DIR = Path(os.path.expanduser("~/.config/ai-knowledge/local/mcp"))


def token_location(repo, name):
    """Where the token file is: this plugin's folder, the ai-config folder, or nowhere."""
    if (NEW_DIR / f"{name}.env").exists():
        return "ai-knowledge"
    if (repo / "local" / "mcp" / f"{name}.env").exists():
        return "ai-config"
    return False


def rows():
    if not CFG.get("ai_config_dir"):
        sys.exit(f"ai_config_dir is not set in {CONFIG}.")
    repo = Path(CFG["ai_config_dir"]).expanduser()
    if not repo.is_dir():
        sys.exit(f"ai_config_dir not set or not found ({CONFIG}). Point it at your ai-config clone.")
    servers, group, claude = template(repo), groups(repo), claude_servers()
    out = []
    for name in servers:
        out.append({
            "server": name,
            "group": group.get(name, "-"),
            "in_claude_code": name in claude,
            "token_file": token_location(repo, name),
        })
    return out


if __name__ == "__main__":
    data = rows()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
    else:
        print(f"{'server':16} {'group':14} {'claude':8} token")
        for r in data:
            print(f"{r['server']:16} {r['group']:14} {'yes' if r['in_claude_code'] else 'no':8} {(r['token_file'] or 'no')}")
        missing = [r["server"] for r in data if not r["in_claude_code"]]
        if missing:
            print(f"\nNot in Claude Code: {', '.join(missing)}. Add with: node claude/install.js --mcp=<server>")
