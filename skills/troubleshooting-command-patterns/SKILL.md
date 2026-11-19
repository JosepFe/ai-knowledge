---
name: troubleshooting-command-patterns
description: "Proven commands by technology (package managers, MCP servers in VS Code, TLS, WSL, PowerShell encoding and BOM, parallel terminals for long read-only jobs; grows as solved): how-to and diagnose, fix and verify patterns. Use when: how do I X in <tech>, an error seen before, which command fixes X."
argument-hint: "Technology + symptom or error text"
---

# Troubleshooting command patterns

Generic, technology-level patterns with placeholders (`<ns>`, `<pkg>`, `<env>`). Values specific to one team or one machine do not belong here. One file per technology; open only the one you need.

| Technology | File |
|---|---|
| npm/npx, uv/uvx, container images (versions, caches, pinning) | [package-managers-npm-uv-containers.md](./package-managers-npm-uv-containers.md) |
| VS Code MCP servers (start, logs, OAuth, timing) | [vscode-mcp-servers.md](./vscode-mcp-servers.md) |
| TLS certificates (private roots, chain capture, explicit trust) | [tls-certificates.md](./tls-certificates.md) |
| Terminals: long read-only jobs in parallel (plan per environment) | [terminals.md](./terminals.md) |
| PowerShell (UTF-8 BOM on written files, encoding-safe writes) | [powershell.md](./powershell.md) |
| WSL (gh browser login, old CLI shadowing an npm global, slow `/mnt/c` installs) | [wsl.md](./wsl.md) |

## Entry format
```markdown
### <symptom or error text, as it appears>
- Cause: <one line, proven>
- Diagnose: `<read-only command>`
- Fix: `<command>` (user runs it if it changes state)
- Verify: `<command + expected result>`
- Seen: <yyyy-mm-dd>, <context in 3-5 words>
```

## Adding a pattern
- Save when a command was costly to find: it took more than one attempt, a docs lookup, or the user says it was hard to find. How-to commands count, not only fixes.
- Only commands that ran and solved it. Generalize names to placeholders; no secrets, private hostnames, user names or local paths.
- Merge with an existing entry for the same symptom instead of duplicating. Keep each file under about 150 lines.
- State-changing commands (delete, apply, restart, force) are marked `(user runs)` and keep the read-only diagnose step before them.
