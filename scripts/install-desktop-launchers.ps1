# Write machine-local workspace copies and a Desktop launcher folder (Windows).
#
#   .\scripts\install-desktop-launchers.ps1 `
#     -OneDrive "$env:USERPROFILE\Black Box Safety - MASTER" `
#     -Repos "$HOME\bbs"
#
# Does not modify the templates in workspace/. Filled copies go to ~/bbs-workspaces/.

param(
    [Parameter(Mandatory = $true)][string]$OneDrive,
    [Parameter(Mandatory = $true)][string]$Repos,
    [string]$Dest = (Join-Path $HOME "bbs-workspaces")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent }

$OneDrive = $OneDrive.TrimEnd("\", "/")
$Repos = $Repos.TrimEnd("\", "/")
# Workspace JSON wants forward slashes.
$OneDriveJson = $OneDrive -replace "\\", "/"
$ReposJson = $Repos -replace "\\", "/"

if ($OneDrive -match "REPLACE-" -or $Repos -match "REPLACE-") {
    throw "Pass real paths, not the REPLACE-* tokens."
}

$DesktopDir = Join-Path ([Environment]::GetFolderPath("Desktop")) "BBS Workspaces"
New-Item -ItemType Directory -Force -Path $Dest, $DesktopDir | Out-Null

function Fill-Workspace([string]$Src, [string]$Out) {
    $text = Get-Content -Raw -Path $Src
    $text = $text.Replace("REPLACE-ON-FIRST-OPEN", $OneDriveJson)
    $text = $text.Replace("REPLACE-ONEDRIVE-ROOT", $OneDriveJson)
    $text = $text.Replace("REPLACE-REPOS-ROOT", $ReposJson)
    Set-Content -Path $Out -Value $text -NoNewline -Encoding utf8
}

Fill-Workspace (Join-Path $Root "workspace\bbs-rep.code-workspace") (Join-Path $Dest "bbs-rep.code-workspace")
Fill-Workspace (Join-Path $Root "workspace\bbs-web.code-workspace") (Join-Path $Dest "bbs-web.code-workspace")
Fill-Workspace (Join-Path $Root "workspace\bbs-admin.code-workspace") (Join-Path $Dest "bbs-admin.code-workspace")

function Write-Bat([string]$Name, [string]$Target) {
    $bat = Join-Path $DesktopDir "Open $Name.bat"
    @"
@echo off
where cursor >nul 2>&1 && start "" cursor "$Target" && exit /b 0
where code >nul 2>&1 && start "" code "$Target" && exit /b 0
start "" "$Target"
"@ | Set-Content -Path $bat -Encoding ascii
}

Write-Bat "Quote Desk" (Join-Path $Dest "bbs-rep.code-workspace")
Write-Bat "Web" (Join-Path $Dest "bbs-web.code-workspace")
Write-Bat "Admin" (Join-Path $Dest "bbs-admin.code-workspace")

@"
BBS Cursor / VS Code workspaces
===============================

Double-click an Open *.bat file in this folder.

  Quote Desk   California state agency folders
  Web          storefront, catalog, quote bot, agency tenants
  Admin        document store, marketplace, vault, suppliers

Filled workspace files live in: $Dest
Templates (do not edit these for a path): $Root\workspace
"@ | Set-Content -Path (Join-Path $DesktopDir "README.txt") -Encoding utf8

Write-Host "Wrote filled workspaces to $Dest"
Write-Host "Wrote Desktop launchers to $DesktopDir"
Start-Process explorer.exe $DesktopDir
