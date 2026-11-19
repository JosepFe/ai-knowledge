---
name: mcp-inventory
description: List the MCP servers connected to Claude Code, whether each token is present, and what each one can do (read-only, read and write, or write only), so access can be kept tight. Use when asked which MCP servers are connected, what permissions they have, or to review MCP access.
---

# MCP inventory

Shows what is connected and what each connection can do. Never prints a token value.

## 1. Connected servers and token files

Run from the plugin root:

```bash
python3 $K/mcp_status.py
```

It lists each server, its group, whether Claude Code has it, and whether its token file exists. Show the table as it is.

## 2. Permissions of each token

The agent cannot read token files, by design. Permissions are read by a script that Josep runs on his machine. It prints scope names only:

```bash
python3 $K/mcp_scopes.py
```

For each server it prints `read`, `write`, or both, from the token's scopes, and says what it could not check. Ask Josep to paste the output, and do not ask him for the token.

Only GitLab and GitHub classic tokens are checked. For other providers, the script says "not checked"; do not guess their scopes.

## 3. Access level per server

Classify from the scopes in step 2 and from the server's tools:

| Level | Meaning |
|---|---|
| read-only | Only read scopes. Safe to keep connected. |
| read and write | Can change data. Keep only if the work needs it. |
| write only | Rare. Check it is intended. |
| not checked | Provider not verified by the script. |

## 4. What to return

- A table: server, token present, access level, and the reason in a few words.
- Servers with more access than their work needs, first, with the change to make (for example, a read-only token).
- Do not change any token or configuration. Changes are proposals for Josep.
