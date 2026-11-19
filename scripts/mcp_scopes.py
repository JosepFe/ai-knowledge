#!/usr/bin/env python3
"""Print the scopes of each MCP token that can be checked. Never prints a token value.

  mcp_scopes.py          run on your own machine; reads the token files in ~/.config/ai-knowledge/local/mcp
                         and asks the provider which scopes each token has

Checked: GitLab (personal access token, /personal_access_tokens/self) and GitHub classic tokens
(scopes in the x-oauth-scopes header). Other providers are reported as not checked.
"""
import json
import os
import urllib.request
from pathlib import Path

LOCAL = Path(os.path.expanduser("~/.config/ai-knowledge/local/mcp"))
GITLAB_URL = "https://gitlab.com/api/v4/personal_access_tokens/self"
GITHUB_URL = "https://api.github.com/user"
TOKEN_VARS = {"gitlab": "GITLAB_PERSONAL_ACCESS_TOKEN", "github": "GITHUB_PERSONAL_ACCESS_TOKEN"}
READ = ("read", "api", "read_api", "read_repository", "read_registry", "read_user", "public_repo", "repo")


def read_var(path, name):
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()
    return None


def fetch(url, token, header):
    value = token if header == "PRIVATE-TOKEN" else f"Bearer {token}"
    req = urllib.request.Request(url, headers={header: value})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.headers, r.read()


def gitlab(token):
    _, body = fetch(GITLAB_URL, token, "PRIVATE-TOKEN")
    scopes = json.loads(body).get("scopes", [])
    return scopes


def github(token):
    headers, _ = fetch(GITHUB_URL, token, "Authorization")
    return [s.strip() for s in headers.get("x-oauth-scopes", "").split(",") if s.strip()]


def level(scopes):
    if not scopes:
        return "no scopes reported"
    has_read = any(s in READ for s in scopes)
    has_write = any(s not in READ for s in scopes)
    return "read and write" if has_read and has_write else ("read-only" if has_read else "write only")


def main():
    checks = {"gitlab": gitlab, "github": github}
    for server, var in TOKEN_VARS.items():
        token = read_var(LOCAL / f"{server}.env", var)
        if not token:
            print(f"{server}: no token file here")
            continue
        try:
            scopes = checks[server](token)
            print(f"{server}: {level(scopes)} ({', '.join(scopes) or 'none'})")
        except urllib.error.HTTPError as exc:
            print(f"{server}: check failed (HTTP {exc.code}; 401 means the token is invalid or expired, 404 means the endpoint differs on this server)")
        except Exception as exc:
            print(f"{server}: check failed ({type(exc).__name__})")
    for name in sorted(p.stem for p in LOCAL.glob("*.env")):
        if name not in TOKEN_VARS:
            print(f"{name}: not checked (provider not supported by this script)")


if __name__ == "__main__":
    main()
