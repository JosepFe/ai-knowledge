# Working rules (generic)

- Read before writing: the target file, its neighbours and what it depends on. Copy the closest existing example.
- Minimal diff: only what was asked. No refactors, renames or reformatting that were not requested.
- No new scripts, helper files or summary documents unless asked. Extend existing ones.
- No state-changing git (commit, push, checkout, reset, rebase, tag) unless asked. Read-only git is fine.
- Never run commands that change live systems (apply, delete, deploy, write to a secret store). Print the command for the user to run.
- Prefer the dedicated tools (file, search, MCP) over shell commands when one fits.
- Never guess a flag, API or version: check the official docs and cite the source. If it cannot be checked, say so.
- Keep long command output out of the context: use limits, filters and `--tail`.
- Never print, log or echo a secret. If one appears in output, say so first.
- Answer the exact question, tersely. Reply in the user's language.
