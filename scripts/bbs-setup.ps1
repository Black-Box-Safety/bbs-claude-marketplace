<#
.SYNOPSIS
  Black Box Safety rep-machine bootstrap. Installs the command-line tools Claude Code leans on.
.DESCRIPTION
  Idempotent: skips anything already installed. Safe to rerun. Uses winget (built into Windows 11).
  Run from any PowerShell window:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1
  Preview without installing:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1 -DryRun
  SAM.gov users (Kim, Griffin) add -SamGov to be asked for the shared SAM.gov API key:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1 -SamGov
#>
param([switch]$DryRun, [switch]$SamGov)

$packages = @(
  @{ Id = 'Git.Git';                 Why = 'Claude Code hooks and the Bash tool run through Git Bash' },
  @{ Id = 'OpenJS.NodeJS.LTS';       Why = 'superpowers-chrome browsing skill (chrome-ws) needs Node' },
  @{ Id = 'Google.Chrome';           Why = 'the browser Claude drives for product research' },
  @{ Id = 'oschwartz10612.Poppler';  Why = 'pdftotext/pdfinfo: RFQ PDFs become text before Claude reads them' },
  @{ Id = 'UB-Mannheim.TesseractOCR'; Why = 'OCR for scanned RFQs and faxed worksheets' },
  @{ Id = 'JohnMacFarlane.Pandoc';   Why = 'Word attachments to markdown' },
  @{ Id = 'astral-sh.uv';            Why = 'runs bbs-workspaces.py for the Desktop launchers, and the bbs-website venvs' },
  @{ Id = 'Python.Python.3.12';      Why = 'the `python` the form-fill, quote, reconciliation and BC item-entry scripts run on; pypdf/pymupdf/openpyxl/msal/msal-extensions install into it below' },
  @{ Id = 'DuckDB.cli';              Why = 'query price lists and SCPRS exports instead of reading them whole' },
  @{ Id = 'jqlang.jq';               Why = 'JSON plumbing for scripts and hooks' },
  @{ Id = 'TheDocumentFoundation.LibreOffice'; Why = 'soffice: quote-builder PDF export and document-skills conversion' },
  # Cmd: skip winget when the command already resolves. The VS Code extension and the Desktop
  # app bundle their own Claude, and a second, winget-managed copy beside a native install is
  # the conflicting-installations case Claude Code's docs warn about.
  @{ Id = 'Anthropic.ClaudeCode';    Cmd = 'claude'; Why = 'the `claude` command this script installs the BBS plugins with' }
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error "winget not found. Install 'App Installer' from the Microsoft Store, then rerun this script."
  exit 1
}

Write-Host "BBS rep-machine bootstrap $(if ($DryRun) { '(dry run - nothing will be installed)' })"
Write-Host ""

$failed = @()
$deferred = @()

foreach ($p in $packages) {
  if ($p.Cmd -and (Get-Command $p.Cmd -CommandType Application -ErrorAction SilentlyContinue)) {
    Write-Host ("[ok]      {0}" -f $p.Id)
    continue
  }
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

# Installed is not the same as on PATH, and /bbs-checkup resolves every tool by name. LibreOffice,
# Tesseract and Git's bash.exe never put themselves on PATH, so a clean run of this script used to
# leave soffice, tesseract and bash "missing" for ever. For each command that does not resolve,
# look where its installer puts it and add that folder to the user PATH.
#   Reject: a hit that answers to the name without being the tool - the Microsoft Store python
#   stub under \WindowsApps\, and WSL's System32\bash.exe, which is not Git Bash.
#   Prepend: go ahead of that stub, whose folder is already on the user PATH, so a plain `python`
#   in a terminal reaches the real one.
$WinGetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
$WinGetPkgs  = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
$tools = @(
  @{ Cmd = 'git';       Dirs = @("$env:ProgramFiles\Git\cmd", "$env:LOCALAPPDATA\Programs\Git\cmd") },
  @{ Cmd = 'bash';      Dirs = @("$env:ProgramFiles\Git\bin", "$env:LOCALAPPDATA\Programs\Git\bin"); Reject = @('*\System32\*', '*\WindowsApps\*') },
  @{ Cmd = 'node';      Dirs = @("$env:ProgramFiles\nodejs") },
  @{ Cmd = 'python';    Dirs = @("$env:LOCALAPPDATA\Programs\Python\Python312", "$env:ProgramFiles\Python312"); Reject = @('*\WindowsApps\*'); Prepend = $true },
  @{ Cmd = 'pdftotext'; Dirs = @($WinGetLinks, "$WinGetPkgs\oschwartz10612.Poppler_*\poppler-*\Library\bin") },
  @{ Cmd = 'tesseract'; Dirs = @("$env:ProgramFiles\Tesseract-OCR", "$env:LOCALAPPDATA\Programs\Tesseract-OCR") },
  @{ Cmd = 'pandoc';    Dirs = @("$env:LOCALAPPDATA\Pandoc", "$env:ProgramFiles\Pandoc", $WinGetLinks) },
  @{ Cmd = 'uv';        Dirs = @($WinGetLinks, "$WinGetPkgs\astral-sh.uv_*", "$env:USERPROFILE\.local\bin") },
  @{ Cmd = 'duckdb';    Dirs = @($WinGetLinks, "$WinGetPkgs\DuckDB.cli_*") },
  @{ Cmd = 'jq';        Dirs = @($WinGetLinks, "$WinGetPkgs\jqlang.jq_*") },
  @{ Cmd = 'soffice';   Dirs = @("$env:ProgramFiles\LibreOffice\program", "${env:ProgramFiles(x86)}\LibreOffice\program") },
  @{ Cmd = 'claude';    Dirs = @("$env:USERPROFILE\.local\bin", $WinGetLinks, "$WinGetPkgs\Anthropic.ClaudeCode_*") }
)

function Find-Tool($Tool) {
  Get-Command $Tool.Cmd -CommandType Application -All -ErrorAction SilentlyContinue |
    Where-Object { $src = $_.Source; -not ($Tool.Reject | Where-Object { $src -like $_ }) } |
    Select-Object -First 1
}

function Add-UserPath([string]$Dir, [switch]$Prepend) {
  # Read and write the raw registry value. [Environment]::SetEnvironmentVariable would expand
  # every %USERPROFILE%-style entry already in the user PATH and store it back as plain text.
  $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
  $raw = $key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
  $parts = @($raw -split ';' | Where-Object { $_ })
  if ($parts -notcontains $Dir) {
    $parts = if ($Prepend) { @($Dir) + $parts } else { $parts + $Dir }
    $key.SetValue('Path', ($parts -join ';'), [Microsoft.Win32.RegistryValueKind]::ExpandString)
  }
  $key.Close()
  if (($env:Path -split ';') -notcontains $Dir) {
    $env:Path = if ($Prepend) { "$Dir;$env:Path" } else { "$env:Path;$Dir" }
  }
  $script:pathChanged = $true
}

$pathChanged = $false
foreach ($t in $tools) {
  $hit = Find-Tool $t
  if ($hit) {
    Write-Host ("[ok]      {0,-28} {1}" -f $t.Cmd, $hit.Source)
    continue
  }
  $dir = $null
  foreach ($pattern in $t.Dirs) {
    if ($pattern -notmatch '^[A-Za-z]:\\') { continue }   # an unset env var, e.g. no ProgramFiles(x86)
    $dir = Get-Item -Path $pattern -ErrorAction SilentlyContinue |
      Sort-Object Name -Descending |
      Where-Object { Test-Path (Join-Path $_.FullName "$($t.Cmd).exe") } |
      Select-Object -First 1 -ExpandProperty FullName
    if ($dir) { break }
  }
  if (-not $dir -and $DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f $t.Cmd, 'check after the winget installs above')
  } elseif (-not $dir) {
    Write-Host ("[missing] {0,-28} not installed - see the winget lines above" -f $t.Cmd)
    $failed += $t.Cmd
  } elseif ($DryRun) {
    Write-Host ("[would]   {0,-28} add {1} to PATH" -f $t.Cmd, $dir)
  } else {
    Write-Host ("[path]    {0,-28} add {1} to PATH" -f $t.Cmd, $dir)
    Add-UserPath $dir -Prepend:([bool]$t.Prepend)
  }
}

# Claude Code reads CLAUDE_CODE_GIT_BASH_PATH from the environment (documented by Anthropic):
# which bash.exe runs the Bash tool and every plugin hook. Without Git Bash, Claude Code falls
# back to PowerShell and the plugins' shell hooks error. It depends on this machine, so it is
# saved here. The machine-independent variables (CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS,
# CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE) live once, in the managed settings' `env`
# (bbs-managed-settings.json, 2026-10-01); this script sets the timeout only for its own
# install run below and no longer saves either one. A copy an earlier version saved is
# left alone: it holds the same value, and removing it before Parker re-pastes the
# managed settings would drop the timeout on that machine in between.
$userEnv = [ordered]@{}
$env:CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS = '600000'
$gitBash = @("$env:ProgramFiles\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if ($gitBash) {
  $userEnv['CLAUDE_CODE_GIT_BASH_PATH'] = $gitBash
} elseif (-not $DryRun) {
  Write-Host "[missing] Git Bash                     Git.Git did not install - see the winget lines above"
  $failed += 'Git Bash'
}
foreach ($name in $userEnv.Keys) {
  $want = $userEnv[$name]
  if ([Environment]::GetEnvironmentVariable($name, 'User') -eq $want) {
    Write-Host ("[ok]      {0}" -f $name)
  } elseif ($DryRun) {
    Write-Host ("[would]   {0,-28} set to {1}" -f $name, $want)
  } else {
    Write-Host ("[install] {0,-28} set to {1}" -f $name, $want)
    [Environment]::SetEnvironmentVariable($name, $want, 'User')
    Set-Item -Path "env:$name" -Value $want
  }
}
if ($pathChanged -and -not $DryRun) {
  # The PATH edit went straight to the registry, which Windows does not announce, so VS Code
  # started from the Start menu would not see it until sign-out. Every SetEnvironmentVariable
  # call at User scope does announce, so rewrite one variable with its own value.
  if ($userEnv.Contains('CLAUDE_CODE_GIT_BASH_PATH')) {
    [Environment]::SetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', $userEnv['CLAUDE_CODE_GIT_BASH_PATH'], 'User')
  }
}

# The shared BBS SAM.gov API key, for the sam-gov-opportunities skill (one account, one key
# for the team: Parker, 2026-10-02). It is a credential, so it is never in this script or the
# repo: the person running the bootstrap pastes it when asked (Parker supplies it), and it is
# saved to the user environment like CLAUDE_CODE_GIT_BASH_PATH above. Input is hidden and the
# value is never printed. Only the people who use SAM.gov need it, so the prompt is opt-in:
# run with -SamGov to be asked. Its expiry date is in bbs-foundations canonical-facts.md,
# "Federal codes"; to replace it, clear the variable and rerun with -SamGov.
# Read-Host needs a person at a console: it throws under -NonInteractive or redirected input,
# so both are checked first and the step is skipped quietly instead.
$noConsole = [Console]::IsInputRedirected -or -not [Environment]::UserInteractive -or
  ([Environment]::GetCommandLineArgs() | Where-Object { $_ -match '^-NonI' })
if ([Environment]::GetEnvironmentVariable('SAM_GOV_API_KEY', 'User')) {
  Write-Host "[ok]      SAM_GOV_API_KEY              set (value not shown)"
} elseif (-not $SamGov) {
  Write-Host "[skip]    SAM_GOV_API_KEY              only for SAM.gov users; rerun with -SamGov to add it"
} elseif ($DryRun) {
  Write-Host "[would]   SAM_GOV_API_KEY              ask for the BBS SAM.gov key from Parker"
} elseif ($noConsole) {
  $deferred += 'SAM_GOV_API_KEY (rerun with -SamGov in a PowerShell window and paste the key from Parker)'
} else {
  $secure = $null
  try {
    $secure = Read-Host -AsSecureString "Paste the BBS SAM.gov API key from Parker (input hidden; press Enter to skip)"
  } catch { $secure = $null }
  if (-not $secure -or $secure.Length -eq 0) {
    Write-Host "[skip]    SAM_GOV_API_KEY              not set; rerun with -SamGov to add it"
    $deferred += 'SAM_GOV_API_KEY (rerun with -SamGov and paste the key from Parker)'
  } else {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $samKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim() }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    if (-not $samKey -or $samKey -match '\s') {
      Write-Host "[skip]    SAM_GOV_API_KEY              that paste was empty or had spaces; rerun with -SamGov and paste the key alone"
      $deferred += 'SAM_GOV_API_KEY (rerun with -SamGov and paste the key alone)'
    } else {
      [Environment]::SetEnvironmentVariable('SAM_GOV_API_KEY', $samKey, 'User')
      Write-Host "[install] SAM_GOV_API_KEY              saved to your user environment (value not shown)"
    }
    Remove-Variable samKey -ErrorAction SilentlyContinue
  }
  $secure = $null
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
  # invisible to build_quote.js (and to /bbs-checkup, which resolves it from that script's
  # folder) without NODE_PATH. Point it there, once, for this user.
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
      # A User NODE_PATH shadows a Machine one, so carry any Machine entries into it.
      $parts = @()
      foreach ($v in @($nodePath, [Environment]::GetEnvironmentVariable('NODE_PATH', 'Machine'), $npmRoot)) {
        if ($v) { foreach ($e in ($v -split ';')) { if ($e -and ($parts -notcontains $e)) { $parts += $e } } }
      }
      $newNodePath = $parts -join ';'
      [Environment]::SetEnvironmentVariable('NODE_PATH', $newNodePath, 'User')
      $env:NODE_PATH = $newNodePath
    }
  }
} elseif ($DryRun) {
  Write-Host ("[would]   {0,-28} {1}" -f 'docx, pptxgenjs, NODE_PATH', 'after Node is on PATH (npm global + NODE_PATH)')
} else {
  Write-Host "[later]   docx and pptxgenjs need Node on PATH: close this PowerShell window, open a new one, run the script again, then reopen VS Code."
  $deferred += 'docx, pptxgenjs'
}

# Python libraries the form-fill (ca-form-filler, naspo-quote), quote and reconciliation
# (bbs-order-reconciliation) scripts import, plus msal and msal-extensions, which bc-item-entry
# needs to sign the rep in to Business Central and keep the token encrypted with DPAPI. They install into the winget Python above. The
# Microsoft Store alias under \WindowsApps\ answers to `python` without being one (it exits
# non-zero without throwing), so it is skipped - install-desktop-launchers.ps1 does the same.
$pyPackages = @('pypdf', 'pymupdf', 'openpyxl', 'msal', 'msal-extensions')
$realPython = Get-Command python -CommandType Application -All -ErrorAction SilentlyContinue |
  Where-Object { $_.Source -notlike '*\WindowsApps\*' } |
  Select-Object -First 1
if ($realPython) {
  & $realPython.Source -c "import pypdf, fitz, openpyxl, msal, msal_extensions" > $null 2>&1
  $pyHave = ($LASTEXITCODE -eq 0)
  if ($pyHave) {
    Write-Host ("[ok]      {0}" -f ($pyPackages -join ', '))
  } elseif ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
  } else {
    Write-Host ("[install] {0,-28} {1}" -f 'python packages', ($pyPackages -join ', '))
    & $realPython.Source -m pip install --upgrade --quiet $pyPackages 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "python -m pip could not install the PDF/Excel/sign-in libraries; the form-fill scripts print the exact pip command when first run."
      $failed += 'python packages (pypdf/pymupdf/openpyxl/msal/msal-extensions)'
    }
  }
} elseif ($DryRun) {
  Write-Host ("[would]   {0,-28} {1}" -f 'python packages', (($pyPackages -join ', ') + ' after Python is on PATH'))
} else {
  Write-Host "[later]   pypdf/pymupdf/openpyxl/msal/msal-extensions need Python on PATH: close this PowerShell window, open a new one, run the script again, then reopen VS Code."
  $deferred += 'pypdf, pymupdf, openpyxl, msal, msal-extensions'
}

# The BBS plugins. Managed settings enable them and Claude Code installs them at session start,
# but in the background: a plugin whose install fails (a clone timeout, antivirus holding a
# file) is simply absent, and /bbs-checkup can only say so. Installing from here shows the
# error. The list is every plugin in the marketplace's own marketplace.json - everyone gets
# every plugin (MANAGED-SETTINGS.md) - less any that bbs-managed-settings.json sets to false,
# and less any entry keyworded 'maintainer': maintainer-tier tools are in the catalog for
# Parker to install by hand, never pushed to a rep machine (docs/COMMONS.md; Parker, 2026-10-28).
# Nothing is copied into this script, so a plugin added to the marketplace is picked up.
$marketplace = 'bbs-claude-marketplace'
$claudeCmd = Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $claudeCmd) {
  if ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f 'BBS plugins', 'after Claude Code is on PATH')
  } else {
    Write-Host "[later]   the BBS plugins need the claude command on PATH: close this PowerShell window, open a new one, run the script again, then reopen VS Code."
    $deferred += 'BBS plugins'
  }
} else {
  $claude = $claudeCmd.Source
  $mkt = $null
  try {
    $mkt = (& $claude plugin marketplace list --json 2>$null | Out-String | ConvertFrom-Json) |
      Where-Object { $_.name -eq $marketplace } | Select-Object -First 1
  } catch { }
  if ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f $marketplace, $(if ($mkt) { 'update, then install every plugin in it' } else { 'add, then install every plugin in it' }))
  } else {
    $out = if ($mkt) { & $claude plugin marketplace update $marketplace 2>&1 }
           else      { & $claude plugin marketplace add "Black-Box-Safety/$marketplace" 2>&1 }
    if ($LASTEXITCODE -ne 0) {
      Write-Warning ("could not {0} the {1} marketplace:" -f $(if ($mkt) { 'update' } else { 'add' }), $marketplace)
      $out | Select-Object -Last 5 | ForEach-Object { Write-Host "          $_" }
      $failed += "$marketplace marketplace"
    }
    try {
      $mkt = (& $claude plugin marketplace list --json 2>$null | Out-String | ConvertFrom-Json) |
        Where-Object { $_.name -eq $marketplace } | Select-Object -First 1
    } catch { $mkt = $null }
    $catalog = if ($mkt) { Join-Path $mkt.installLocation '.claude-plugin\marketplace.json' }
    $policy  = if ($mkt) { Join-Path $mkt.installLocation 'plugins\bbs-foundations\docs\bbs-managed-settings.json' }
    if (-not $catalog -or -not (Test-Path $catalog)) {
      Write-Warning "the marketplace is not on this machine, so the plugin list cannot be read. Send this window to Parker."
      $failed += 'BBS plugins'
    } else {
      $blocked = @()
      if (Test-Path $policy) {
        $blocked = (Get-Content $policy -Raw | ConvertFrom-Json).enabledPlugins.PSObject.Properties |
          Where-Object { $_.Value -eq $false } | ForEach-Object { $_.Name }
      }
      $want = (Get-Content $catalog -Raw | ConvertFrom-Json).plugins |
        Where-Object { @($_.keywords) -notcontains 'maintainer' } |
        ForEach-Object { "$($_.name)@$marketplace" } |
        Where-Object { $blocked -notcontains $_ }
      $have = @{}
      try {
        foreach ($i in (& $claude plugin list --json 2>$null | Out-String | ConvertFrom-Json)) {
          if ($i.installPath -and (Test-Path $i.installPath) -and -not $i.errors) { $have[$i.id] = $true }
        }
      } catch { }
      foreach ($id in $want) {
        if ($have[$id]) {
          Write-Host ("[ok]      {0}" -f $id)
          continue
        }
        Write-Host ("[install] {0}" -f $id)
        $out = & $claude plugin install $id --scope user 2>&1
        if ($LASTEXITCODE -ne 0) {
          Write-Warning ("{0} did not install. Claude Code said:" -f $id)
          $out | Select-Object -Last 5 | ForEach-Object { Write-Host "          $_" }
          $failed += $id
        }
      }
    }
  }
}

Write-Host ""
if ($failed.Count -gt 0) {
  Write-Host ("Finished with {0} item(s) to install by hand: {1}" -f $failed.Count, ($failed -join ', '))
}
if ($deferred.Count -gt 0) {
  Write-Host ("Not done yet - still to add: {0}" -f ($deferred -join '; '))
  Write-Host "To finish: close this PowerShell window, open a new one, run the script again, then reopen VS Code."
}
if ($failed.Count -eq 0 -and $deferred.Count -eq 0) {
  if ($DryRun) { Write-Host "Dry run complete." } else { Write-Host "Done." }
}
Write-Host "Close every VS Code or Cursor window and quit the Claude Desktop app (a window you reopen keeps the old PATH), start it again, then run /bbs-checkup in Claude."
