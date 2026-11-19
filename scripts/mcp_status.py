#!/usr/bin/env python3
"""Read-only status of the MCP servers: what the private template defines, what Claude Code has, and whether each token file exists.

  mcp_status.py            table: server, in Claude Code, token file present
  mcp_status.py --json     the same as JSON

The template is ~/.config/ai-knowledge/local/mcp/mcp.template.jsonc (the same file the mcp-updates hook reads).
Without it, the servers configured in Claude Code are listed. Token files are checked for existence only;
their contents are never read or printed.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HOME  # noqa: E402

LOCAL_DIR = Path(os.path.expanduser("~/.config/ai-knowledge/local/mcp"))
TEMPLATE = LOCAL_DIR / "mcp.template.jsonc"


def template():
    if not TEMPLATE.exists():
        return {}
    text = TEMPLATE.read_text(encoding="utf-8")
    return json.loads(re.sub(r"(?m)^\s*//.*$", "", text)).get("servers", {})


def claude_servers():
    path = HOME / ".claude.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})


def rows():
    servers, claude = template(), claude_servers()
    names = list(servers) + [n for n in claude if n not in servers]
    return [{
        "server": name,
        "in_template": name in servers,
        "in_claude_code": name in claude,
        "token_file": (LOCAL_DIR / f"{name}.env").exists(),
    } for name in names]


if __name__ == "__main__":
    data = rows()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    if not TEMPLATE.exists():
        print(f"No template at {TEMPLATE}: listing the servers in Claude Code only.\n")
    if not data:
        print("No MCP servers in the template or in Claude Code (claude.ai connectors are not listed).")
        sys.exit(0)
    print(f"{'server':20} {'template':9} {'claude':8} token")
    for r in data:
        yn = lambda v: "yes" if v else "no"  # noqa: E731
        print(f"{r['server']:20} {yn(r['in_template']):9} {yn(r['in_claude_code']):8} {yn(r['token_file'])}")
    missing = [r["server"] for r in data if r["in_template"] and not r["in_claude_code"]]
    if missing:
        print(f"\nIn the template but not in Claude Code: {', '.join(missing)}. Add them with `claude mcp add`.")
