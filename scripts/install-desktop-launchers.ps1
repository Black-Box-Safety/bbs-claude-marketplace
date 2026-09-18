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
python $script @args
