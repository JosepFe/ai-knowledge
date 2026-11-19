# WSL: browser logins and shadowed CLIs

### `gh auth login` in WSL: `xdg-open: x-www-browser: not found`, then a terminal prompt `github.com cookie: ... Allow? (Y/N/Always/neVer)`
- Cause: WSL has no GUI browser, so `xdg-open` falls back to lynx/w3m inside the terminal; the device login never completes and `hosts.yml` keeps an invalid token (`git ls-remote` fails with `Invalid username or token`).
- Diagnose: `gh auth status` (shows `The token in ~/.config/gh/hosts.yml is invalid`); `git config --get-regexp '^credential\..*helper'` (expect `gh auth git-credential`).
- Fix: quit lynx (`q`, `y`), then `sudo apt install -y wslu; gh config set browser wslview; gh auth logout -h github.com -u <user>; gh auth login -h github.com -p https -w` and authorize the org SSO in the Windows browser (or open `https://github.com/login/device` manually and type the code).
- Verify: `gh auth status` shows `Logged in`; `git ls-remote https://github.com/<org>/<repo>.git HEAD` prints a hash.
- Seen: <yyyy-mm-dd>, <context>

### `copilot plugin install` / `copilot update`: `error: Invalid command format. Did you mean: copilot -i "..."?`
- Cause: an old standalone Copilot CLI in `~/.local/bin` shadows a newer npm global `@github/copilot` on `PATH`; old versions lack the `plugin`/`update` subcommands.
- Diagnose: `command -v copilot; copilot --version; npm ls -g --depth=0 | grep -i copilot`
- Fix (user runs): `mv ~/.local/bin/copilot ~/.local/bin/copilot.<ver>.bak; hash -r`; then rerun the failed command (e.g. `build-cli copilot setup`). Update later with `npm i -g @github/copilot@latest`.
- Verify: `command -v copilot` points to the npm bin and `copilot --version` shows the npm version.
- Seen: <yyyy-mm-dd>, <context>

### Vitest / `ng serve` / Playwright on a repo under `/mnt/c`: `[vitest-pool]: Failed to start forks worker ... Timeout waiting for worker to respond`
- Cause: the 9P mount of `/mnt/c` is too slow to load `node_modules`; workers time out at random (each run a different spec file is missing).
- Fix: run the gates from a copy on the Linux disk: `rsync -a --exclude node_modules --exclude .angular /mnt/c/Repos/<repo>/ ~/<repo>/ && cd ~/<repo>/frontend && npm ci`, then copy the new or changed files back by name (`diff -rq --exclude node_modules ...` to check).
- Verify: `npm test` runs every spec file in seconds (Playwright parity: ~10 s instead of timeouts).
- Seen: <yyyy-mm-dd>, <context>
- Also applies to `npm install` / `ng update` on `/mnt/c`: they run for 10+ min with no output (a Node project, 2026-11-10); on `~/<repo>` the same install takes ~40 s. Move to the Linux disk before upgrading.

### `ng update` to Angular 21/22: `npm error Cannot read properties of null (reading 'edgesOut')`
- Cause: `@analogjs/vitest-angular` pulls `@analogjs/vite-plugin-angular`, whose required peer `@angular-devkit/build-angular` breaks npm's peer resolution once Angular moves to 21+.
- Fix: drop analog and use the native Vitest builder (as in my_finances): `angular.json` test target `"builder": "@angular/build:unit-test"` with `"include": ["src/**/*.spec.ts"]`, delete `vitest.config.ts` and the analog `test-setup.ts`, add `jsdom`; set the target versions in `package.json`, `rm -rf node_modules package-lock.json && npm install`, then `npx ng update <pkg> --migrate-only --from=<old> --allow-dirty` for `@angular/core`, `@angular/cli`, `angular-eslint`.
- Verify: `ng build --configuration production`, `ng lint`, `ng test --no-watch --coverage`, `npm audit`.
- Seen: <yyyy-mm-dd>, <context>

### testcontainers (pytest) in WSL with only Podman Desktop on Windows: no `docker`/`podman` CLI in the distro
- Cause: the Podman machine is another WSL distro; its API is not exposed to yours by default.
- Fix: `"/mnt/c/Program Files/RedHat/Podman/podman.exe" machine ssh -- "nohup podman system service --time=0 tcp:127.0.0.1:2375 >/tmp/podman-api.log 2>&1 &"`, then `export DOCKER_HOST=tcp://127.0.0.1:2375 TESTCONTAINERS_RYUK_DISABLED=true TESTCONTAINERS_HOST_OVERRIDE=127.0.0.1` (WSL2 distros share localhost). Python env without `python3-venv`: `uv venv .venv && uv pip install -p .venv/bin/python -r requirements-dev.txt`.
- Verify: `curl -s http://127.0.0.1:2375/_ping` prints `OK`; pytest starts the Postgres container. Stop: `podman.exe machine ssh -- "pkill -f 'podman system service --time=0 tcp:127.0.0.1:2375'"`.
- Limit: scripts that bind-mount distro folders into containers (`docker run -v /tmp/...`) don't work this way (the machine can't see your distro's paths).
- Seen: <yyyy-mm-dd>, <context>
