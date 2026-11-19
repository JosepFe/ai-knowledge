<!-- Part of the `languages` skill: official Python practices (PEP 8, PEP 257, PEP 621, packaging guide). -->

## 1. Rules for agents
- Before using a stdlib function, argument or `pyproject.toml` key not already in the repo, check the official doc and cite the link in the reply: stdlib https://docs.python.org/3/library/, packaging https://packaging.python.org/en/latest/.
- Repo config wins: follow existing `pyproject.toml` / `[tool.*]` tables and CI. Never add or change linters, formatters or CI lint jobs unless asked; put such ideas in review notes.
- PEP 8 itself says project-specific guides take precedence and "do not break backwards compatibility just to comply with this PEP".

## 2. Official best practices
PEP 8 https://peps.python.org/pep-0008/
- 4 spaces per indent; spaces, not tabs; never mix them.
- Max 79 chars (72 for docstrings/comments); a team may agree on up to 99, comments still 72. Wrap with implicit continuation in `()`, not backslashes.
- New code: break lines before binary operators.
- Two blank lines around top-level defs/classes, one between methods.
- Imports: one per line, at file top, grouped stdlib / third party / local with a blank line between groups; absolute imports preferred; avoid `from x import *`.
- Pick one string-quote style and keep it; triple-quoted strings use `"""`.
- Naming: modules/packages short lowercase; classes `CapWords`; exceptions end in `Error`; functions/variables `lower_case_with_underscores`; `self`/`cls`; trailing `_` to avoid keyword clashes (`class_`); never `l`, `O`, `I` as single-letter names.

PEP 257 https://peps.python.org/pep-0257/
- `"""Triple double quotes"""`; one-liner is an imperative phrase ending in a period ("Return X."), not the signature.
- Multi-line: summary line, blank line, details; closing quotes on their own line.
- A script's docstring should be usable as its usage message.

pyproject.toml: PEP 621 https://peps.python.org/pep-0621/ (Final; canonical spec now https://packaging.python.org/en/latest/specifications/pyproject-toml/) and guide https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- Always have `[build-system]` (`requires`, `build-backend`).
- `[project]`: `name` required and never dynamic; `version` required (static or listed in `dynamic`); `requires-python` for the minimum version; `dependencies` as PEP 508 strings.
- CLI entry points in `[project.scripts]` (`name = "pkg.module:func"`).
- `license` is now an SPDX expression + `license-files` (PEP 639); the PEP 621 table form is deprecated.
- Tool settings belong in `[tool.<name>]`, defined by each tool.

## 3. Lint / format / validate before proposing a change
- CPython ships no official linter or formatter. Syntax check: `python -m py_compile <file>.py` (https://docs.python.org/3/library/py_compile.html; not verified in this pass).
- Non-official tools, run only if the repo configures them (`[tool.ruff]`, `[tool.black]`, `[tool.mypy]` or CI job):
  - ruff: `ruff check <path>`, `ruff format --check <path>`
  - black: `black --check <path>`
  - mypy: `mypy <path>`
- Run the repo's own tests/CLI (`python -m <pkg> --help`) after edits.

## 5. Keeping current
- Re-check PEP 8 / packaging guide links if a review cites a rule that isn't here.
