---
name: release
description: "Create a version for a repo: choose major, minor or patch, tag the merged commit on main, and write the release notes from the commits since the previous tag. Use when: nueva versión, new version, release, tag, release notes, bump."
argument-hint: "repo path, and the version if Josep already chose one"
---

# Release

Works on the repo Josep names (for example `ai-knowledge` or `ai-kickstart`). Creating a tag and a GitHub release changes shared state, so the steps below stop for approval before anything is pushed.

## 1. Find the current state

- Last tag: `git describe --tags --abbrev=0`. If there is none, the last version is in the manifest (`.claude-plugin/plugin.json` or `package.json`) and in the commit messages. Say so.
- Confirm the commits to release are on `main`: `git merge-base --is-ancestor <commit> main`. If not, stop and tell Josep to merge first. Never tag a feature branch.
- Read the commits since the last tag: `git log <last-tag>..main --oneline`.

## 2. Choose the bump

- **major**: breaking change for users: a renamed or removed skill, command or setting, a changed default that alters results, or a changed file format.
- **minor**: new skill, command, setting or script that users can use. Nothing breaks.
- **patch**: fixes, docs and internal changes only.

Pick one, say which and why in one line. If Josep already gave the version, use his and only check that it fits this rule.

## 3. Write the release notes

Group the commits by what changes for the user (new, changed, fixed). Keep only what changes how the repo is used; drop refactors, formatting and internal churn. One line per item, plain language, Spanish or English as the repo already uses. Mention breaking changes first.

## 4. Update the manifests

Set the new version in every manifest the repo has (`plugin.json`, `marketplace.json`, `package.json`, as present). Commit that as `chore: release vX.Y.Z` on `main`. Do not run the commit if the manifests already show the version.

## 5. Show, then tag

Show Josep the version, the bump reason, the notes and the tag target. Wait for "ok".

After approval:
- `git tag -a vX.Y.Z -m "vX.Y.Z"` on the release commit
- `git push origin main vX.Y.Z`
- `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <notes>` only if Josep asks for a GitHub release

Report the tag, the commit hash and the release URL.

## Rules

- Tags for old versions point at the commit that shipped them, found by the commit message that names the version. Confirm each one with Josep before creating it.
- Never move or delete a tag that is already pushed.
- Never add attribution lines to release notes beyond the ones the repo already uses.
