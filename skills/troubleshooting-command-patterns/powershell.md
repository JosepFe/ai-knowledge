# PowerShell: encoding and file writes

### Text file starts with an invisible BOM (EF BB BF), so frontmatter or the first heading isn't recognized
- Cause: Windows PowerShell 5.1 `Set-Content -Encoding UTF8`, `Out-File` and `>` write UTF-8 *with* BOM. A BOM before `---` can hide a SKILL.md/agent frontmatter from strict parsers; before `# Title` it breaks heading detection (`search.js` chunks, `Last reviewed` checks).
- Find (repo-wide, skips `.git`, `local`):
```powershell
Get-ChildItem <repo> -Recurse -File -Include *.md,*.json,*.js | ? { $_.FullName -notmatch '\\(\.git|node_modules|local)\\' } | ? { $b=[IO.File]::ReadAllBytes($_.FullName); $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF } | % FullName
```
- Fix (content unchanged, BOM removed):
```powershell
$f = (Resolve-Path <file>).Path; $t = [IO.File]::ReadAllText($f); [IO.File]::WriteAllText($f, $t.TrimStart([char]0xFEFF), (New-Object Text.UTF8Encoding $false))
```
- Prevent: write files with `[IO.File]::WriteAllText(<path>, <text>, (New-Object Text.UTF8Encoding $false))` or the editor's edit tool, not `Set-Content`/`Out-File` in Windows PowerShell 5.1 (PowerShell 7 defaults to no BOM). `[IO.File]` paths are resolved from the process directory, not `Set-Location`: pass absolute paths.
- Seen: <yyyy-mm-dd>, <context>
