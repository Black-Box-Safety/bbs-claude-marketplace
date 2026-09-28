# Thin wrapper. Prefer: python3 scripts/bbs-workspaces.py request --yes --install-desktop
param(
    [string]$OneDrive,
    [string]$Repos,
    [string]$Dest
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$wsScript = Join-Path $Root "scripts\bbs-workspaces.py"
$wsArgs = @("request", "--yes", "--install-desktop")
if ($OneDrive) { $wsArgs += @("--onedrive", $OneDrive) }
if ($Repos) { $wsArgs += @("--repos", $Repos) }
if ($Dest) { $wsArgs += @("--dest", $Dest) }
# bbs-setup.ps1 installs uv, so try it first. Then the py launcher. A bare
# "python" is last and only if it is a real install: the Microsoft Store alias
# under \WindowsApps\ exits non-zero without throwing, so it is skipped.
$realPython = Get-Command python -CommandType Application -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -notlike "*\WindowsApps\*" } |
    Select-Object -First 1
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run --no-project --python 3 python $wsScript @wsArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 $wsScript @wsArgs
} elseif ($realPython) {
    & $realPython.Source $wsScript @wsArgs
} else {
    Write-Error "No Python found (uv, py, or python). Run scripts\bbs-setup.ps1 first, then retry."
    exit 1
}
exit $LASTEXITCODE
