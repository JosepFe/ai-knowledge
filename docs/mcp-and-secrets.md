# MCP servers, secrets and a new machine

## Checking MCP servers

`scripts/mcp_status.py` is read-only. It lists the MCP servers defined in `ai-config` and shows whether each one is in Claude Code and whether its token file exists. It never reads or prints a token. It needs `ai_config_dir` in `config.json`.

```bash
python3 $K/mcp_status.py
```

## Checklist for a new computer

1. Clone `ai-config` and run `node claude/install.js --mcp=common` (groups in `mcp/groups.json`).
2. Install this plugin and run "set up ai-knowledge" to write this machine's paths.
3. Save each token on this machine with `/secrets` or `mcp/set-mcp-secret.sh <server>`. Tokens are never copied between machines.
4. Restart the session and run `/mcp`. `mcp_status.py` should show `yes` in both columns for the servers you use.

## Secret entry panel (`mods/secret-entry`)

A Claude Code mod, not a skill. It adds `/secrets`, a panel that saves one value into any file, for example a project's `.env`:

1. Type the file path (absolute, WSL form such as `/mnt/c/...`).
2. Type the variable name.
3. Paste the value and press Enter.

Only that variable changes; the other lines are kept, and the file is set to mode 600. The value never goes through the chat.

- The MCP buttons fill the file and variable for a token in `~/.config/ai-knowledge/local/mcp/<server>.env`, using the same encoding as `mcp/set-mcp-secret.sh` in ai-config. The folder is created with mode 700 by `setup`, and it lives outside any repo.
- The value field shows what you type. Use the terminal script for anything you would rather not see on screen.
- The MCP servers still read their tokens from ai-config until their configuration points to this folder. That is a separate change in ai-config.
- Loading it needs the mods setting turned on in Claude Code. Claude asks once.
