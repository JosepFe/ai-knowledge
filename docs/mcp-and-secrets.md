# MCP servers, secrets and a new machine

## Where things live

- **Tokens**: `~/.config/ai-knowledge/local/mcp/<server>.env`, one file per MCP server, mode 600, in a folder with mode 700 that `setup` creates outside any repo. The agent cannot read this folder (the guard hook blocks it).
- **Server list**: `~/.config/ai-knowledge/local/mcp/mcp.template.jsonc`, a private file with a `servers` object (each entry has `command` and `args`, with the version pinned). The `mcp-updates` hook reads it once a day and tells you when a pinned server has a newer release.
- **Claude Code**: the servers you actually use are registered with `claude mcp add` (user scope).

## Checking MCP servers

`scripts/mcp_status.py` is read-only. It lists the servers in the template and in Claude Code, and whether each token file exists. It never reads or prints a token. Without a template it lists the servers in Claude Code only.

```bash
python3 $K/mcp_status.py
```

## Checklist for a new computer

1. Install this plugin and run "set up ai-knowledge" to write this machine's paths and create the private folders.
2. Copy your private template to `~/.config/ai-knowledge/local/mcp/` (it holds no secrets).
3. Register each server with `claude mcp add` and save its token with `/secrets`. Tokens are never copied between machines.
4. Restart the session and run `/mcp`. `mcp_status.py` should show `yes` in every column for the servers you use.

## Secret entry panel (`mods/secret-entry`)

A Claude Code mod, not a skill. It adds `/secrets`, a panel that saves one value into any file, for example a project's `.env`:

1. Type the file path (absolute, WSL form such as `/mnt/c/...`).
2. Type the variable name.
3. Paste the value and press Enter.

Only that variable changes; the other lines are kept, and the file is set to mode 600. The value never goes through the chat.

- The MCP buttons fill the file and variable for a token in `~/.config/ai-knowledge/local/mcp/<server>.env`.
- The value field shows what you type. Use the terminal script for anything you would rather not see on screen.
- Loading it needs the mods setting turned on in Claude Code. Claude asks once.
