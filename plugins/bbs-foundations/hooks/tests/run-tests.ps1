# Runs doctrine.ps1 against fixture stdin. Exit 0 = all pass.
# Usage (Git Bash or PowerShell):
#   powershell -NoProfile -ExecutionPolicy Bypass -File plugins/<plugin>/hooks/tests/run-tests.ps1
#   pwsh -NoProfile -File plugins/<plugin>/hooks/tests/run-tests.ps1
# The same file ships in bbs-foundations and bbs-website; it reads the plugin's own
# doctrine/subscriptions.json and derives the expectations from it, so it is not a second
# copy of the table.
$ErrorActionPreference = 'Stop'
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$hooks  = Split-Path -Parent $here
$script = Join-Path $hooks 'doctrine.ps1'
$ddir   = Join-Path $hooks 'doctrine'
$table  = Get-Content -LiteralPath (Join-Path $ddir 'subscriptions.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$exe    = (Get-Process -Id $PID).Path

function Run($obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 5
  return ($json | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String)
}
function Context($out) {
  if (-not $out.Trim()) { return $null }
  return (($out | ConvertFrom-Json).hookSpecificOutput).additionalContext
}
function Expected($name) {
  $t = Get-Content -LiteralPath (Join-Path $ddir ([string]$table.inserts.$name.file)) -Raw -Encoding UTF8
  return ($t -replace "`r`n", "`n")
}

$fail = 0
function Check($label, $cond) {
  if ($cond) { Write-Host "PASS  $label" } else { Write-Host "FAIL  $label"; $script:fail++ }
}

# 1. Empty stdin and a non-Skill tool: silent.
Check 'empty stdin is silent' (-not ('' | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim())
Check 'non-Skill tool is silent' ($null -eq (Context (Run @{ tool_name = 'Bash'; tool_input = @{ command = 'ls' } })))
Check 'unrelated skill is silent' ($null -eq (Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = 'unrelated' } })))
Check 'garbage stdin is silent' (-not ('{not json' | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim())

# 2. Every non-wildcard subscription injects, byte for byte, every insert whose pattern
#    matches that name (a name can sit under an exact pattern AND a plugin:* one), joined
#    by a blank line in table order. The expectation is computed here independently.
function ExpectedFor([string]$name) {
  $seen = New-Object System.Collections.Generic.List[string]
  foreach ($s in @($table.subscriptions)) {
    if ($seen.Contains([string]$s.insert)) { continue }
    if ($name -like ([string]$s.on)) { $seen.Add([string]$s.insert) }
  }
  return (@($seen | ForEach-Object { Expected $_ }) -join "`n`n")
}
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -like '*[*]*') { continue }
  $got = Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = [string]$sub.on } })
  Check ("{0} -> {1}" -f $sub.on, $sub.insert) ($got -eq (ExpectedFor ([string]$sub.on)))
}

# 3. A wildcard subscription fires on a concrete name under it.
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -notlike '*[*]*') { continue }
  $name = ([string]$sub.on) -replace '\*', 'zzz'
  $got = Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = $name } })
  Check ("{0} matches {1} -> {2}" -f $sub.on, $name, $sub.insert) ($got -and $got.Contains((Expected $sub.insert)))
}

if ($fail -gt 0) { Write-Host "$fail failure(s)"; exit 1 }
Write-Host 'all pass'
exit 0
