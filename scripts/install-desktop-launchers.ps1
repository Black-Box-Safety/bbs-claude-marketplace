# Thin wrapper. Prefer: python3 scripts/bbs-workspaces.py request --yes --install-desktop
param(
    [string]$OneDrive,
    [string]$Repos,
    [string]$Dest
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $Root "scripts\bbs-workspaces.py"
$args = @("request", "--yes", "--install-desktop")
if ($OneDrive) { $args += @("--onedrive", $OneDrive) }
if ($Repos) { $args += @("--repos", $Repos) }
if ($Dest) { $args += @("--dest", $Dest) }
# bbs-setup.ps1 installs uv, not a bare python. Try the interpreters a rep machine may have.
if (Get-Command python -ErrorAction SilentlyContinue) {
    python $script @args
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 $script @args
} elseif (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run --no-project --python 3 python $script @args
} else {
    Write-Error "No Python found (python, py, or uv). Run scripts\bbs-setup.ps1 first, then retry."
    exit 1
}
