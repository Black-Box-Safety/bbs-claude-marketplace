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
  @{ Id = 'astral-sh.uv';            Why = 'runs bbs-workspaces.py for the Desktop launchers, and the bbs-website venvs' },
  @{ Id = 'Python.Python.3.12';      Why = 'the `python` the form-fill, quote and reconciliation scripts run on; pypdf/pymupdf/openpyxl install into it below' },
  @{ Id = 'DuckDB.cli';              Why = 'query price lists and SCPRS exports instead of reading them whole' },
  @{ Id = 'jqlang.jq';               Why = 'JSON plumbing for scripts and hooks' },
  @{ Id = 'TheDocumentFoundation.LibreOffice'; Why = 'soffice: quote-builder PDF export and document-skills conversion' }
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error "winget not found. Install 'App Installer' from the Microsoft Store, then rerun this script."
  exit 1
}

Write-Host "BBS rep-machine bootstrap $(if ($DryRun) { '(dry run - nothing will be installed)' })"
Write-Host ""

$failed = @()

foreach ($p in $packages) {
  winget list --id $p.Id --exact --accept-source-agreements > $null 2>&1
  if ($LASTEXITCODE -eq 0) {
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

# winget writes Node's and Python's PATH entries to the registry, not to this window. Reload
# them so the npm and pip steps below can usually finish on the first run instead of the rerun.
if (-not $DryRun) {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path', 'User')
}

# Some skills need npm libraries, not winget packages: bbs-quote-builder builds the quote
# .docx with `docx`, and the pptx skill builds decks with `pptxgenjs`. If npm still does not
# resolve, these finish on the rerun the closing line asks for.
$npmPackages = @(
  @{ Name = 'docx';      Why = 'bbs-quote-builder builds the quote .docx with it' },
  @{ Name = 'pptxgenjs'; Why = 'the pptx skill builds slide decks with it' }
)
if (Get-Command npm -ErrorAction SilentlyContinue) {
  foreach ($n in $npmPackages) {
    npm ls -g $n.Name > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Host ("[ok]      {0} (npm global)" -f $n.Name)
    } elseif ($DryRun) {
      Write-Host ("[would]   {0,-28} {1}" -f $n.Name, $n.Why)
    } else {
      Write-Host ("[install] {0,-28} {1}" -f $n.Name, $n.Why)
      npm install -g $n.Name | Out-Null
      if ($LASTEXITCODE -ne 0) {
        Write-Warning ("npm could not install {0} globally; the skill that needs it prompts on first use." -f $n.Name)
        $failed += $n.Name
      }
    }
  }
  # Node's require() never looks in the npm global folder on its own, so a global `docx` is
  # invisible to build_quote.js and to /bbs-checkup's `node -e "require('docx')"` without
  # NODE_PATH. Point it there, once, for this user.
  $npmRoot = (npm root -g 2>$null | Select-Object -First 1)
  if ($npmRoot) {
    $npmRoot = $npmRoot.Trim()
    $nodePath = [Environment]::GetEnvironmentVariable('NODE_PATH', 'User')
    $onPath = $nodePath -and (($nodePath -split ';') -contains $npmRoot)
    if ($onPath) {
      Write-Host ("[ok]      NODE_PATH includes {0}" -f $npmRoot)
    } elseif ($DryRun) {
      Write-Host ("[would]   {0,-28} {1}" -f 'NODE_PATH', "add $npmRoot so node finds the global docx/pptxgenjs")
    } else {
      Write-Host ("[install] {0,-28} {1}" -f 'NODE_PATH', "add $npmRoot so node finds the global docx/pptxgenjs")
      $newNodePath = if ($nodePath) { "$nodePath;$npmRoot" } else { $npmRoot }
      [Environment]::SetEnvironmentVariable('NODE_PATH', $newNodePath, 'User')
      $env:NODE_PATH = $newNodePath
    }
  }
} elseif (-not $DryRun) {
  Write-Host "[later]   docx and pptxgenjs need Node on PATH; reopen VS Code and rerun this script to add them."
}

# Python libraries the form-fill (ca-form-filler, naspo-quote), quote and reconciliation
# (bbs-order-reconciliation) scripts import. They install into the winget Python above. The
# Microsoft Store alias under \WindowsApps\ answers to `python` without being one (it exits
# non-zero without throwing), so it is skipped - install-desktop-launchers.ps1 does the same.
$pyPackages = @('pypdf', 'pymupdf', 'openpyxl')
$realPython = Get-Command python -CommandType Application -All -ErrorAction SilentlyContinue |
  Where-Object { $_.Source -notlike '*\WindowsApps\*' } |
  Select-Object -First 1
if ($realPython) {
  & $realPython.Source -c "import pypdf, fitz, openpyxl" > $null 2>&1
  $pyHave = ($LASTEXITCODE -eq 0)
  if ($pyHave) {
    Write-Host ("[ok]      {0}" -f ($pyPackages -join ', '))
  } elseif ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
  } else {
    Write-Host ("[install] {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
    & $realPython.Source -m pip install --upgrade --quiet $pyPackages 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "python -m pip could not install the PDF/Excel libraries; the form-fill scripts print the exact pip command when first run."
      $failed += 'python packages (pypdf/pymupdf/openpyxl)'
    }
  }
} elseif (-not $DryRun) {
  Write-Host "[later]   pypdf/pymupdf/openpyxl need Python on PATH; reopen VS Code and rerun this script to add them."
}

Write-Host ""
if ($failed.Count -gt 0) {
  Write-Host ("Finished with {0} item(s) to install by hand: {1}" -f $failed.Count, ($failed -join ', '))
} else {
  Write-Host "Done."
}
Write-Host "Close and reopen VS Code or Cursor so PATH picks up the new tools. If any line above said [later], run this script once more after reopening to finish those, then run /bbs-checkup in Claude."
