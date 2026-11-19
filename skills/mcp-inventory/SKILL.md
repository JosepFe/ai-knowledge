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

## 4. Risk and the minimum scopes

For each token with a check, name the scopes that are broad and say what they allow:

| Scope | Why it matters |
|---|---|
| `api` | Full API access: create, change and delete. Review first. |
| `write_repository`, `write_registry`, `write_virtual_registry` | Pushes code and images. |
| `self_rotate` | The token can replace itself. |
| `ai_features`, `read_virtual_registry` | Narrower; say so only if relevant. |

Then suggest the smallest set that matches the server's work. For a server that only reads, for example GitLab used for queries: `read_api` and `read_repository`. Only add write scopes if the work needs them, and say which work does.

## 5. What to return

- A table: server, token present, access level, risk (low, medium or high), and the reason in a few words.
- The broad scopes found, one line each, and the minimum set suggested.
- Servers with more access than their work needs, first.
- Do not change any token or configuration. Changes are proposals for Josep: he creates the new token and saves it with `/secrets`, then revokes the old one.
