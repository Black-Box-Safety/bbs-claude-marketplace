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
  @{ Id = 'astral-sh.uv';            Why = 'fast Python env manager for the bbs-website venvs' },
  @{ Id = 'Python.Python.3.12';      Why = 'the python the form-fill, quote and reconciliation scripts run on; pypdf/pymupdf/openpyxl install into it below' },
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

# Some skills need npm libraries, not winget packages: bbs-quote-builder builds the quote
# .docx with `docx`, and the pptx skill builds decks with `pptxgenjs`. Node arrives above but
# its PATH only lands after VS Code reopens, so on a first run npm may not resolve yet - these
# succeed on the rerun the script already asks for.
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
} elseif (-not $DryRun) {
  Write-Host "[later]   docx and pptxgenjs need Node on PATH; reopen VS Code and rerun this script to add them."
}

# Python libraries the form-fill (ca-form-filler, naspo-quote), quote and reconciliation
# (bbs-order-reconciliation) scripts import. They install into the winget Python above, whose
# PATH also lands only after VS Code reopens - so a first run defers them to the rerun.
$pyPackages = @('pypdf', 'pymupdf', 'openpyxl')
if (Get-Command python -ErrorAction SilentlyContinue) {
  if ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
  } else {
    Write-Host ("[install] {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
    python -m pip install --upgrade --quiet $pyPackages 2>&1 | Out-Null
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
