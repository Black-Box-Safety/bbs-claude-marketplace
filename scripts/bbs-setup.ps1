<#
.SYNOPSIS
  Black Box Safety rep-machine bootstrap. Installs the command-line tools Claude Code leans on.
.DESCRIPTION
  Idempotent: skips anything already installed. Safe to rerun. Uses winget (built into Windows 11).
  Run from any PowerShell window:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1
  Preview without installing:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1 -DryRun
#>
param([switch]$DryRun)

$packages = @(
  @{ Id = 'Git.Git';                 Why = 'Claude Code hooks and the Bash tool run through Git Bash' },
  @{ Id = 'OpenJS.NodeJS.LTS';       Why = 'superpowers-chrome browsing skill (chrome-ws) needs Node' },
  @{ Id = 'Google.Chrome';           Why = 'the browser Claude drives for product research' },
  @{ Id = 'oschwartz10612.Poppler';  Why = 'pdftotext/pdfinfo: RFQ PDFs become text before Claude reads them' },
  @{ Id = 'UB-Mannheim.TesseractOCR'; Why = 'OCR for scanned RFQs and faxed worksheets' },
  @{ Id = 'JohnMacFarlane.Pandoc';   Why = 'Word attachments to markdown' },
  @{ Id = 'astral-sh.uv';            Why = 'Python runtime for form-fill and document-skills scripts, zero config' },
  @{ Id = 'DuckDB.cli';              Why = 'query price lists and SCPRS exports instead of reading them whole' },
  @{ Id = 'jqlang.jq';               Why = 'JSON plumbing for scripts and hooks' }
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error "winget not found. Install 'App Installer' from the Microsoft Store, then rerun this script."
  exit 1
}

Write-Host "BBS rep-machine bootstrap $(if ($DryRun) { '(dry run - nothing will be installed)' })"
Write-Host ""

$installed = winget list --accept-source-agreements 2>$null | Out-String
$failed = @()

foreach ($p in $packages) {
  if ($installed -match [regex]::Escape($p.Id)) {
    Write-Host ("[ok]      {0}" -f $p.Id)
    continue
  }
  if ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f $p.Id, $p.Why)
    continue
  }
  Write-Host ("[install] {0,-28} {1}" -f $p.Id, $p.Why)
  winget install --id $p.Id --exact --silent --accept-package-agreements --accept-source-agreements | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Warning ("winget exit {0} for {1}. Install it by hand later; nothing else here depends on it." -f $LASTEXITCODE, $p.Id)
    $failed += $p.Id
  }
}

Write-Host ""
if ($failed.Count -gt 0) {
  Write-Host ("Finished with {0} item(s) to install by hand: {1}" -f $failed.Count, ($failed -join ', '))
} else {
  Write-Host "Done."
}
Write-Host "Close and reopen VS Code so PATH picks up the new tools, then run /bbs-checkup in Claude."
