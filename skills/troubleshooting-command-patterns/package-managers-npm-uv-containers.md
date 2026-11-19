# Package managers and images: npm/npx, uv/uvx, container registries

### Latest published version of a package or image (to pin or compare)
- Diagnose:
  - npm: `npm view <pkg> version`
  - PyPI: `(Invoke-RestMethod https://pypi.org/pypi/<pkg>/json).info.version`
  - Docker Hub: `(Invoke-RestMethod "https://hub.docker.com/v2/repositories/<ns>/<repo>/tags?page_size=10&ordering=last_updated").results.name`
- Seen: <yyyy-mm-dd>, <context>

### Does a CLI flag / env var really exist? (before writing it in config)
- Diagnose: `npm view <pkg> readme | Select-String '<flag>|<ENV_VAR>'`, PyPI: `((Invoke-RestMethod https://pypi.org/pypi/<pkg>/json).info.description -split "`n") | Select-String '<flag>'`, Go/Python CLIs: `<cli> --help 2>&1 | Select-String '<flag>'`
- Seen: <yyyy-mm-dd>, <context>

### `npx -y <pkg>` (unpinned) silently runs an old cached version
- Cause: npx reuses the copy already in its cache instead of fetching the latest.
- Diagnose: `Get-ChildItem "$env:LOCALAPPDATA\npm-cache\_npx" -Directory | % { Get-Content "$($_.FullName)\node_modules\<pkg>\package.json" -ErrorAction SilentlyContinue | ConvertFrom-Json | Select-Object name, version }`
- Fix: pin `<pkg>@<version>` (and `uvx <pkg>@<version>`, image `:<tag>`), bump deliberately.
- Seen: <yyyy-mm-dd>, <context>

### Slow first start right after pinning a new version
- Cause: one-time download of the pinned version into a new npx/uv cache entry (or image pull); later starts are normal.
- Diagnose: time a second start; if still slow, the package itself is slow (check its logs).
- Seen: <yyyy-mm-dd>, <context>

### lazydocker on Windows with Podman: no Services/stack panel, stack up/down does nothing
- Cause: lazydocker runs `docker-compose` for all stack actions (default `commandTemplates.dockerCompose`); with only Podman + podman-compose it fails silently. It also only shows the stack of the folder it was started in (no all-stacks view, unlike Portainer).
- Fix: in `%APPDATA%\lazydocker\config.yml` set `commandTemplates.dockerCompose: podman-compose`; start lazydocker from the compose folder (`U`/`D` = up/down project). Stack start/stop/restart from any folder: `customCommands.containers` with `podman stop --filter label=com.docker.compose.project={{ .Container.ProjectName }}` (same for start/restart), run with `c` on any stack container.
- Verify: in the compose folder `podman-compose config --quiet` exits 0 (lazydocker's detection check); Services panel appears.
- Seen: <yyyy-mm-dd>, <context>
