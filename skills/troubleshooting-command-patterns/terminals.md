# Terminals: long read-only jobs in parallel

### Run several long read-only CLI jobs at once (terragrunt run-all plan per env, multi-account checks)
- One terminal per job: launch each command with `mode=async`. Sync commands share one shell; subagents don't get their own terminals either. Launch all jobs back to back, then end the turn; completion notifications arrive by themselves (no polling, no sleep).
- Each command is self-contained: `Set-Location <absolute env dir>;` + env vars + command + log. Never rely on the state of a previous terminal.
- Check the first output line `The stack at <path>`: it must be the env dir. If it shows the repo root, `run-all` hits every env with the wrong profile: kill that terminal and relaunch.
- Read-only only (`plan`, `validate`, `describe`, `get`). Apply/destroy/modify commands go to the user.
- Exit code 1 + `NativeCommandError` is PowerShell wrapping stderr; judge by `Plan:` lines and `level=error`.

Template (terragrunt plan per env):
```powershell
Set-Location <repo-clone>\environments\<env>; $env:TERRAGRUNT_DOWNLOAD='C:\Temp'; $env:AWS_PROFILE='<env>'; $env:VAULT_ADDR='<vault-url>'; $env:TG_NON_INTERACTIVE='true'; terragrunt run-all plan -target="<address>" -no-color 2>&1 | Tee-Object C:\Temp\<repo>-plan-<env>.log
```
- `TERRAGRUNT_DOWNLOAD=C:\Temp` keeps `.terragrunt-cache` paths under the Windows path limit.
- One terminal per env; regions run in parallel inside `run-all`.

Report: grep the logs instead of re-reading terminals:
```powershell
Select-String -Path C:\Temp\<repo>-plan-*.log -Pattern '^Plan:|^\s+[~+-] |# .* will be|level=error'
```
Table per env/region: plan counts and changed attributes. Flag anything beyond the expected change (e.g. `password`, subnet group drift) and say whether apply is safe or a narrower CLI change is better.
- Seen: <yyyy-mm-dd>, <context>
