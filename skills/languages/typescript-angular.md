<!-- Part of the `languages` skill: official Angular style guide, angular-eslint, TypeScript strict options. -->

## 1. Rules for agents
- Before using any Angular API, CLI flag, ESLint rule or tsconfig option not already in the repo, open the official doc (links below, `angular.dev/api/...`, `typescriptlang.org/tsconfig#<option>`) and cite it. If it can't be checked, say "not verified".
- Repo config wins: never add or change `tsconfig*.json`, `eslint.config.js`, `.prettierrc`, `angular.json` lint options or package versions unless asked. Suggest them as review notes instead.
- If the style guide conflicts with the file you edit, keep the file consistent (the guide says so itself).

## 2. Official best practices
Angular style guide: https://angular.dev/style-guide
- Hyphenated file names matching the class; tests next to code as `<name>.spec.ts`; component `.ts/.html/.css` share one name.
- Organize by feature, not by type (no `components/`, `services/` folders); one concept per file; avoid `utils.ts`/`helpers.ts`.
- Prefer `inject()` over constructor injection.
- Group Angular properties (injected deps, inputs, outputs, queries) before methods; keep components on presentation; move complex template logic to TS (`computed`).
- `protected` for members used only by the template; `readonly` for `input`/`output`/`model`/queries.
- `[class]`/`[style]` bindings over `NgClass`/`NgStyle`; name handlers for what they do (`saveUserData()`, not `handleClick()`).
- Keep lifecycle hooks short (call named methods) and implement the hook interfaces (`implements OnInit`).
Error handling: https://angular.dev/best-practices/error-handling
- Handle errors at the call site (`try/catch`, RxJS `catchError`); `ErrorHandler` is for reporting unexpected/fatal errors. `TestBed` rethrows by default.
- `provideBrowserGlobalErrorListeners()` forwards window `error`/`unhandledrejection` to `ErrorHandler`.
Runtime performance (zone pollution, skipping subtrees, slow computations): https://angular.dev/best-practices/runtime-performance
TypeScript `strict`: https://www.typescriptlang.org/tsconfig#strict
- Enables the whole strict family (e.g. `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `useUnknownInCatchVariables`, `strictBuiltinIteratorReturn`); individual checks can be turned off. TS upgrades may add checks under `strict` and new errors.

## 3. Official lint/format/test commands (run before proposing a change)
| Tool | Command | Doc |
|---|---|---|
| angular-eslint | `ng lint` (via `@angular-eslint/builder`) | https://github.com/angular-eslint/angular-eslint#readme |
| Type check / build | `ng build` | https://angular.dev/cli/build (not verified) |

- angular-eslint needs ESLint 9+ and flat config (`eslint.config.js`) only; its major version tracks Angular's (`@angular-eslint@22` for Angular 22).
- angular-eslint keeps no formatting rules; formatting belongs to Prettier.
- Type-checked typescript-eslint presets (`strictTypeChecked`) are stronger but slower.

## 5. Keeping current
When the portal bumps Angular, TypeScript, ESLint/angular-eslint or changes tsconfig/eslint config, update section 4 with the new facts and the date (`verified YYYY-MM-DD`).
