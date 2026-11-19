<!-- Part of the `languages` skill: official PowerShell (PSScriptAnalyzer, approved verbs, Set-StrictMode) and Bash (GNU manual, ShellCheck) practices. -->

## 1. Rules for agents
- Before using a cmdlet, parameter, builtin or flag not already in the repo, check the official doc and cite the link: PowerShell https://learn.microsoft.com/powershell/, Bash https://www.gnu.org/software/bash/manual/bash.html.
- Repo config wins: follow existing scripts, `PSScriptAnalyzerSettings.psd1` / `.shellcheckrc` and CI. Never add or change linters, formatters or CI lint jobs unless asked; put such ideas in review notes.

## 2. Official best practices
PowerShell
- PSScriptAnalyzer rules (severity + default state): https://learn.microsoft.com/powershell/utility-modules/psscriptanalyzer/rules/readme (source `PowerShell/PSScriptAnalyzer` `docs/Rules/README.md`). Always-enabled highlights:
  - Error: `AvoidUsingConvertToSecureStringWithPlainText`, `AvoidUsingUsernameAndPasswordParams`, `AvoidUsingComputerNameHardcoded`.
  - Warning: `AvoidUsingCmdletAliases`, `AvoidUsingWriteHost`, `AvoidUsingInvokeExpression`, `AvoidUsingPlainTextForPassword`, `AvoidUsingEmptyCatchBlock`, `AvoidGlobalVars`, `PossibleIncorrectComparisonWithNull` (`$null -eq $x`), `UseApprovedVerbs`, `UseShouldProcessForStateChangingFunctions`, `UseDeclaredVarsMoreThanAssignments`, `UsePSCredentialType`.
  - Enabled by default: `AvoidUsingPositionalParameters`, `UseSingularNouns`, `ProvideCommentHelp`. Formatting rules (`PlaceOpenBrace`, `UseConsistentIndentation`, `UseConsistentWhitespace`) are disabled unless a settings file enables them.
- Approved verbs: https://learn.microsoft.com/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands. Verb-Noun, list with `Get-Verb`; no synonyms (`Remove`, never `Delete`); `New` creates, `Set` modifies, `Invoke` sync vs `Start` async; reserved: `ForEach`, `Ping`, `Sort`, `Tee`, `Where`.
- Strict mode: https://learn.microsoft.com/powershell/module/microsoft.powershell.core/set-strictmode. `2.0` blocks uninitialized variables, non-existent properties and method-style function calls `f(a,b)`; `3.0` adds bad array indexes. `-Version Latest` is not deterministic across PowerShell releases (doc caution). An `about_Strict_Mode` topic was not found in `MicrosoftDocs/PowerShell-Docs`; `Set-StrictMode` is the reference.

Bash
- Reference: GNU Bash manual https://www.gnu.org/software/bash/manual/bash.html. Not verified: not readable through GitHub (no official repo there); check it on the web before citing `set` options or expansions.
- ShellCheck (non-official, de-facto linter; `koalaman/shellcheck` README) flags: unquoted `$var`/`$@`, `export VAR=$(cmd)` masking exit codes, `for f in $(ls ...)`, variables in `printf` format strings, `rm -rf "$DIR/"*`, `[ ... && ... ]`, backticks (use `$()`), `cat file | grep`. Gallery: https://github.com/koalaman/shellcheck#gallery-of-bad-code.

## 3. Lint / format / validate before proposing a change
PowerShell (PSScriptAnalyzer is Microsoft's official analyzer)
```powershell
Install-Module -Name PSScriptAnalyzer -Scope CurrentUser
Invoke-ScriptAnalyzer -Path ./scripts -Recurse            # add -Settings ./PSScriptAnalyzerSettings.psd1 if the repo has one
```
Cmdlet reference: https://learn.microsoft.com/powershell/module/psscriptanalyzer.

Bash
```bash
bash -n script.sh            # syntax only (GNU manual; not verified in this pass)
shellcheck script.sh         # non-official; non-zero exit on findings
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable script.sh
```
The ShellCheck README recommends pinning a specific version to avoid surprise CI breaks.

## 5. Keeping current
- Re-read the PSScriptAnalyzer rules table when the module version used locally/CI changes (rules and default states change between releases).
