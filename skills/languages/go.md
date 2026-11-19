<!-- Part of the `languages` skill: official Go practices (Effective Go, modules, gofmt, go vet, go test -race, govulncheck). -->

## 1. Rules for agents
- Before using any API, flag or option not already in the repo, open the official doc (links below or `pkg.go.dev/<import path>`) and cite it in the reply. If it can't be checked, say "not verified".
- Repo config wins: never add or change linters, `Makefile` lint/test targets, `go.mod` `go` line or tool versions unless asked. Suggest them as review notes instead.

## 2. Official best practices
- Formatting is `gofmt`'s job; don't hand-align or fight it. Tabs for indent, no line limit: https://go.dev/doc/effective_go#formatting
- Doc comments directly above top-level declarations: https://go.dev/doc/comment
- Names: short lower-case single-word packages, no `Get` prefix on getters, `-er` one-method interfaces, `MixedCaps` not underscores: https://go.dev/doc/effective_go#names
- Early return on errors, drop the needless `else`: https://go.dev/doc/effective_go#if
- Errors: return `error` as last value; error strings name their origin (`"image: unknown format"`): https://go.dev/doc/effective_go#errors
- Library code avoids `panic`; `panic`/`recover` only inside a package, never exposed to callers: https://go.dev/doc/effective_go#panic
- Concurrency: "share memory by communicating"; a mutex is fine for simple counters: https://go.dev/doc/effective_go#sharing
- Effective Go dates from 2009 and doesn't cover generics or modules (note at the top of the doc). Use the module docs for those.
- Layout: keep non-exported code under `internal/`; servers put commands in `cmd/<name>/`; split shareable packages into their own module: https://go.dev/doc/modules/layout
- Code Review Comments (go.dev/wiki/CodeReviewComments): not verified (not found in `golang/website` `_content/wiki/`).

## 3. Official lint/format/test commands (run before proposing a change)
| Tool | Command | Doc |
|---|---|---|
| gofmt | `gofmt -l .` (list), `gofmt -d .` (diff), `gofmt -w .` (fix); `-s` simplifies | https://pkg.go.dev/cmd/gofmt |
| go fmt | `go fmt ./...` (package-level gofmt) | https://go.dev/doc/effective_go#formatting |
| go vet | `go vet ./...`; list checks `go tool vet help`; non-zero exit on findings | https://pkg.go.dev/cmd/vet |
| go test | `go test ./...`; data races `go test -race ./...` | https://go.dev/doc/articles/race_detector |
| govulncheck | `go install golang.org/x/vuln/cmd/govulncheck@latest` then `govulncheck ./...` (reports only vulns in called code) | https://go.dev/doc/tutorial/govulncheck |

- `go vet` is heuristic: treat reports as guidance, not proof (cmd/vet doc).
- Non-official, only if the repo already uses them: golangci-lint, staticcheck.

## 5. Keeping current
When a repo bumps Go, controller-runtime/k8s libs, or changes Makefile lint/test targets, update section 4 with the new facts and the date (`verified YYYY-MM-DD`).
