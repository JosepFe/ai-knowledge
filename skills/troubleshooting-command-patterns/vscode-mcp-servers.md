# VS Code MCP servers

### A server "doesn't work" or is missing tools in chat
- Diagnose: latest log of that server (state, `initialize` wait, stderr):
  `$d = gci "$env:APPDATA\Code\logs" -Directory | sort LastWriteTime -Desc | select -First 1; gci $d.FullName -Recurse -Filter '*<server>.log' | % { Get-Content $_.FullName -Tail 15 }`
- Read: `Waiting for server to respond to initialize` repeated = still installing/starting; `Discovered N tools` = healthy; stderr lines show the real error.
- Seen: <yyyy-mm-dd>, <context>

### Measure a stdio server's startup time outside VS Code
- Diagnose: send one JSON-RPC `initialize` line on stdin and time the first response, e.g. `'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' | <command> <args>` with `Measure-Command`.
- Seen: <yyyy-mm-dd>, <context>

### Remote MCP OAuth fails: `Invalid redirect_uri` during dynamic client registration
- Cause: the authorization server only allows some callback URIs (e.g. `http://localhost:*/callback`); VS Code registers `http://127.0.0.1:33418` and `https://vscode.dev/redirect`.
- Diagnose: `Invoke-RestMethod <server>/.well-known/oauth-protected-resource/<path>` and `<auth-server>/.well-known/oauth-authorization-server`; POST a test registration with the candidate `redirect_uris` to the `registration_endpoint` and read the 400 message.
- Fix: run the server through `npx -y mcp-remote@<version> <url> --host localhost --callback-path /callback` (stdio) so the registered URI matches; tokens are cached in `~/.mcp-auth`.
- Verify: `npx -y -p mcp-remote@<version> mcp-remote-client <url> --host localhost --callback-path /callback` lists the tools.
- Seen: <yyyy-mm-dd>, <context>

### Claude Code in WSL: `mcp-remote` server times out after 30000ms
- Cause: first start waits for browser SSO, but the sign-in URL goes to the MCP stderr, not a console, so the process hangs and holds the sign-in lock (`Another instance is running the sign-in for this server on port <port>`). `wsl -e bash -lc` also picks the system Node 18 (`/usr/bin/node`), where `mcp-remote@0.15.1` crashes with `ReferenceError: File is not defined` (undici needs Node 20+).
- Fix: kill the stuck instance (`ps -eo pid,etime,args | grep "mcp-remote https"`), then sign in once from PowerShell with Node 22: `wsl -e bash -lc 'PATH=$HOME/.local/node22/bin:$PATH npx -y -p mcp-remote@<version> mcp-remote-client <url> --host localhost --callback-path /callback'` and open the printed URL in the Windows browser. If the lock is stale, delete `*_lock.json` in the mcp-remote token cache folder.
- Verify: `claude mcp list` shows `Connected`, then `/mcp` -> reconnect in the open session.
- Seen: <yyyy-mm-dd>, <context>
