---
name: languages
description: Best practices and linters/formatters per language (C#/.NET, Go, TypeScript/Angular, Python, PowerShell/Bash, Terraform/Terragrunt/Packer HCL, Ansible). Use when: write or review code, fix lint or format errors (ESLint, Prettier, dotnet format, ruff, tflint, shellcheck), pick the right check command.
argument-hint: "Language + what you're writing or the error to fix"
---

# Languages

One file per language; open only the one you need. Each has the official rules for code, with doc links, and the official lint, format and test commands.

| Language | File |
|---|---|
| C# / .NET | [csharp-dotnet.md](./csharp-dotnet.md) |
| Go | [go.md](./go.md) |
| TypeScript / Angular | [typescript-angular.md](./typescript-angular.md) |
| Python | [python.md](./python.md) |
| PowerShell / Bash | [powershell-bash.md](./powershell-bash.md) |
| Terraform / Terragrunt / Packer HCL | [terraform-hcl.md](./terraform-hcl.md) |
| Ansible | [ansible.md](./ansible.md) |

## Rules (all languages)
- Before using an API, flag, option, MSBuild property or resource argument that isn't already in the repo, check the official documentation linked in the language file and cite it. If it can't be verified, say so instead of guessing.
- The repo's own configuration wins: never add or change linters, formatters, analyzers, tsconfig, eslint, `.editorconfig` or CI lint jobs unless asked. Official practices the repo doesn't follow go in as review notes, not changes.
- Before proposing a change, run the language's official check commands from its file, using the repo's own config.
