# C# / .NET: official practices and linters

## 1. Rules for agents
- Before using an API, CLI flag or MSBuild property not already in the repo, open the official doc (links below) and cite it in the reply. Can't verify it: say "not verified".
- Repo config wins over generic advice. The repo `.editorconfig`, csproj properties and `NoWarn` entries are deliberate.
- Never add or change analyzers, rulesets, `.editorconfig`, `NoWarn`, `TreatWarningsAsErrors` or lint tooling unless asked. Suggest them as review notes.
- Fix a warning in code first; suppress only with a one-line reason, the way the repo already does (`<NoWarn>$(NoWarn);CAxxxx</NoWarn> <!--why-->`).

## 2. Official best practices
First five bullets: [coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions).
- Modern language features; catch only exceptions you can handle, no bare `System.Exception` without a filter; specific exception types.
- `string`/`int` keywords over runtime type names; string interpolation for short strings, `StringBuilder` in loops; raw string literals over escapes.
- `required` properties to force initialization; collection expressions; `Func<>`/`Action<>` over custom delegates; `using` declarations over `try/finally { Dispose(); }`; `&&`/`||` over `&`/`|`.
- File-scoped namespaces; `using` directives outside the namespace.
- Primary constructor parameters: camelCase on class/struct, PascalCase on records. [identifier names](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/identifier-names)
- Nullable: keep `<Nullable>enable</Nullable>`; use `?` to state intent; prefer null checks, pattern matching or nullable attributes (`NotNullWhen`, ...) over `!`; watch `default` structs and new arrays (null elements, no warning). [nullable reference types](https://learn.microsoft.com/dotnet/csharp/fundamentals/null-safety/nullable-reference-types)
- Async: `async`/`await` for I/O without `Task.Run`; `Task.Run` only for CPU-bound work; `Async` suffix; `async void` only for event handlers; `await Task.WhenAll/WhenAny/Delay` instead of `Wait`/`Result`/`WaitAll`/`Thread.Sleep`; materialize LINQ task projections with `ToArray()`/`ToList()`; if you must block, `GetAwaiter().GetResult()`. [async scenarios](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/async-scenarios)
- Analyzers: CA (quality) rules are on by default for .NET 5+ (`EnableNETAnalyzers`); `AnalysisLevel` (default `latest`) and `AnalysisMode` widen or pin the rule set; IDE (style) rules run on command-line build only with `EnforceCodeStyleInBuild=true` plus a severity in `.editorconfig`. Don't set `EnableNETAnalyzers` when the `Microsoft.CodeAnalysis.NetAnalyzers` package is referenced. [code analysis overview](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/overview), [MSBuild props](https://learn.microsoft.com/dotnet/core/project-sdk/msbuild-props)
- Suppress a rule with `dotnet_diagnostic.<ID>.severity = none` in `.editorconfig`. [code analysis overview](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/overview)

## 3. Official lint/format commands
| Command | Effect | Doc |
|---|---|---|
| `dotnet format --verify-no-changes` | Non-zero exit if any file would change (whitespace, style, analyzers per `.editorconfig`) | [dotnet format](https://learn.microsoft.com/dotnet/core/tools/dotnet-format) |
| `dotnet format whitespace` / `style` / `analyzers` | Run only that rule family; `--diagnostics <IDs>`, `--severity info\|warn\|error`, `--include`/`--exclude <paths>` | same |
| `dotnet format <sln> --include <changed files>` | Fix only the files you touched | same |
| `dotnet build -warnaserror` | All warnings, CA included, become errors (`CodeAnalysisTreatWarningsAsErrors=false` keeps CA as warnings) | [code analysis overview](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/overview) |

Before proposing a change: `dotnet build <sln>` with no new warnings in touched files, `dotnet test <sln>`, and `dotnet format <sln> --verify-no-changes --include <changed files>` so the diff only formats what you changed. `dotnet format` can restore, compile and run analyzers: only run it on trusted code.

## 5. Keeping current
When a repo changes SDK, `.editorconfig`, analyzer or warning settings, or adds `Directory.Build.props`/lint steps, update the section 4 table and its date. Re-read the doc pages above when the SDK major version changes (the default-enabled CA rule list changes per release).
