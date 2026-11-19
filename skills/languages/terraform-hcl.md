<!-- Part of the `languages` skill: official Terraform/Terragrunt/Packer HCL practices (style guide, fmt/validate; tflint non-official). -->

## 1. Rules for agents
- Before using a resource/data source argument or attribute not already in the repo, read it in the Terraform MCP registry docs (`search_providers` -> `get_provider_details`, pinned provider version) and cite it. Modules: `search_modules` -> `get_module_details`. Terraform language/functions: https://developer.hashicorp.com/terraform/language. Terragrunt blocks/functions/flags: `gruntwork-io/terragrunt` docs (https://terragrunt.gruntwork.io/docs/). Packer: https://developer.hashicorp.com/packer/docs.
- Check flags against the tool version the repo pins (section 4); Terragrunt renamed many commands/flags (CLI redesign).
- Repo config wins: never add or change linters, formatters, pre-commit hooks or CI lint jobs unless asked; put such ideas in review notes.

## 2. Official best practices (style guide https://developer.hashicorp.com/terraform/language/style)
- Run `terraform fmt` and `terraform validate` before committing.
- 2-space indent; align `=` of consecutive single-line arguments; arguments first, then nested blocks, separated by one blank line.
- Meta-arguments first (`count`/`for_each`), then arguments, blocks, `lifecycle`, `depends_on`.
- `#` comments only (`//`, `/* */` not idiomatic); comment only what isn't obvious.
- Resource names: descriptive nouns, underscores, no resource type in the name, type and name double-quoted.
- Variables: `type` + `description` always; `default` if optional; `sensitive = true` for secrets (still plain text in state); `validation` only for real constraints. Outputs: `description` always.
- Use locals, `count` and `for_each` sparingly; define data sources before the resources using them.
- Always a default provider config; `alias` first in aliased provider blocks.
- Files: `terraform.tf`, `providers.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `locals.tf`, `backend.tf`; local modules in `./modules/<name>`.
- Commit `.terraform.lock.hcl`; never commit state, `.terraform/`, saved plans or secret `.tfvars`.
- Pin Terraform (`required_version`), providers (`required_providers`) and modules.
- Linting: Terraform has no built-in linter; TFLint is third-party (non-official).

## 3. Lint / format / validate before proposing a change
Terraform (https://developer.hashicorp.com/terraform/cli/commands/fmt, `.../validate`)
```bash
terraform fmt -check -diff -recursive    # non-zero exit if unformatted; drop -check to rewrite
terraform validate                        # needs init; checks syntax/types, not provider-side values
```
Terragrunt (source `gruntwork-io/terragrunt` `docs/src/data/commands/hcl/{fmt,validate}.mdx`)
```bash
terragrunt hcl fmt --check               # new CLI; legacy name: terragrunt hclfmt
terragrunt hcl validate                  # legacy: hclvalidate; --inputs replaces validate-inputs
terragrunt plan                          # read-only; never apply
```
CLI redesign renames (`docs/src/content/docs/08-migrate/03-cli-redesign.md`): `run-all` -> `run --all`, `--terragrunt-non-interactive` -> `--non-interactive`, `TERRAGRUNT_*` -> `TG_*`.
Packer (https://developer.hashicorp.com/packer/docs/commands/fmt, `.../validate`)
```bash
packer fmt -check -diff -recursive packer
packer validate -syntax-only packer      # full validate also evaluates the config (Vault reads in locals need VAULT_* env; inferred)
```
Non-official: `tflint` only if the repo has `.tflint.hcl` or a CI job.

## 5. Keeping current
- When `docker/terraform` or `docker/packer` bump tool versions, or a repo changes its image tag or adds fmt/validate/tflint jobs, update section 4 with repo:path and date.
- After a Terragrunt upgrade, re-check the CLI redesign page before suggesting command/flag names.
