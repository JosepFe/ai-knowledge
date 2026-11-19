---
name: commits
description: Write commit messages and PR or MR titles and bodies in conventional commits format, with a body that feeds release notes, and never add Co-Authored-By or any Claude attribution. Use when: commit, commit message, PR title, MR description, haz commit, mensaje de commit.
argument-hint: "what changed, and whether to commit now"
---

# Commits

## Message format

```
type(scope): short imperative summary

- What changes for the user, one line each (only when the summary is not enough)
- BREAKING CHANGE: what breaks and what to do, if anything
```

- **type**: `feat` (new capability), `fix` (wrong behaviour corrected), `chore` (maintenance, ignores, tooling), `docs`, `refactor`, `test`.
- **scope**: the part of the repo, short (`kb`, `kickstart`, `ci`). Optional.
- **summary**: under 72 characters, in the language the repo already uses, no final period.
- **body**: say what changes for the user, not which files moved. Release notes are built from it, so leave out internal churn.

## Attribution

Never add `Co-Authored-By`, "Generated with", or any line that names a tool or model as author or contributor, in commits, PR titles or PR bodies. Josep asked for this explicitly.

Before committing, check the message: `git log -1 --format=%B` must not contain `Co-Authored-By`. If it does, amend the message only if the commit is not pushed yet.

## Staging

- Stage only the files for this change, by name. Do not use `git add -A` when the working tree has changes that are not part of this task.
- Show Josep the file list and the message, and commit when he says so.

## Rewriting history

Never amend, rebase or force-push a commit that is already on the remote without Josep's explicit approval. If a pushed commit has a wrong message, say so and wait.

## PR and MR text

- Title: the same as the main commit's summary.
- Body: the `What changes` list from the commit body, then how to check it. No attribution line.
