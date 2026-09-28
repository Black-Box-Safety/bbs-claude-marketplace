# Runs doctrine.ps1 against fixture stdin. Exit 0 = all pass.
# Usage (Git Bash or PowerShell):
#   powershell -NoProfile -ExecutionPolicy Bypass -File plugins/<plugin>/hooks/tests/run-tests.ps1
#   pwsh -NoProfile -File plugins/<plugin>/hooks/tests/run-tests.ps1
# The same file ships in bbs-foundations and bbs-website; it reads the plugin's own
# doctrine/subscriptions.json and derives the expectations from it, so it is not a second
# copy of the table. tests/parity.py runs the same fixtures through doctrine.py as well.
$ErrorActionPreference = 'Stop'
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$hooks  = Split-Path -Parent $here
$script = Join-Path $hooks 'doctrine.ps1'
$ddir   = Join-Path $hooks 'doctrine'
$own    = Split-Path -Leaf (Split-Path -Parent $hooks)
$table  = Get-Content -LiteralPath (Join-Path $ddir 'subscriptions.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$exe    = (Get-Process -Id $PID).Path

function Run($obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 5
  return ($json | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String)
}
function Parsed($out) {
  if (-not $out.Trim()) { return $null }
  return ($out | ConvertFrom-Json).hookSpecificOutput
}
function Context($out) { $p = Parsed $out; if ($p) { return $p.additionalContext } else { return $null } }
function Expected($name) {
  $t = Get-Content -LiteralPath (Join-Path $ddir ([string]$table.inserts.$name.file)) -Raw -Encoding UTF8
  return ($t -replace "`r`n", "`n")
}
# Independent computation of what a set of candidate names should inject.
function ExpectedFor([string[]]$names) {
  $seen = New-Object System.Collections.Generic.List[string]
  foreach ($s in @($table.subscriptions)) {
    if ($seen.Contains([string]$s.insert)) { continue }
    foreach ($n in $names) { if ($n -like ([string]$s.on)) { $seen.Add([string]$s.insert); break } }
  }
  if ($seen.Count -eq 0) { return $null }
  return (@($seen | ForEach-Object { Expected $_ }) -join "`n`n")
}
# The prefixes a bare typed name is tried under: this plugin, then the table's bare_prefixes.
function Prefixes() {
  $p = New-Object System.Collections.Generic.List[string]; $p.Add($own)
  foreach ($x in @($table.bare_prefixes)) { if ($x -and -not $p.Contains([string]$x)) { $p.Add([string]$x) } }
  return $p
}

$fail = 0
function Check($label, $cond) {
  if ($cond) { Write-Host "PASS  $label" } else { Write-Host "FAIL  $label"; $script:fail++ }
}

# 1. Silence on anything that is not a subscribed name.
Check 'empty stdin is silent' (-not ('' | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim())
Check 'garbage stdin is silent' (-not ('{not json' | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim())
Check 'non-Skill tool is silent' ($null -eq (Context (Run @{ tool_name = 'Bash'; tool_input = @{ command = 'ls' } })))
Check 'unrelated skill is silent' ($null -eq (Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = 'unrelated' } })))
Check 'missing tool_input is silent' ($null -eq (Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill' })))
Check 'non-string skill is silent' ($null -eq (Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = 42 } })))
Check 'unknown event is silent' ($null -eq (Context (Run @{ hook_event_name = 'SessionStart'; command_name = 'bbs-checkup' })))
Check 'typed unrelated prefixed command is silent' ($null -eq (Context (Run @{ hook_event_name = 'UserPromptExpansion'; command_name = 'nobody:unrelated'; command_source = 'user' })))

# 2. PreToolUse: every non-wildcard subscription injects, byte for byte, every insert whose
#    pattern matches that name (a name can sit under an exact pattern AND a plugin:* one).
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -like '*[*]*') { continue }
  $out = Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = [string]$sub.on } }
  $p = Parsed $out
  Check ("PreToolUse {0} -> {1}" -f $sub.on, $sub.insert) ($p -and $p.hookEventName -eq 'PreToolUse' -and $p.additionalContext -eq (ExpectedFor @([string]$sub.on)))
}
# 2b. The same, without hook_event_name (older input shape): tool_name alone routes it.
$first = @($table.subscriptions | Where-Object { [string]$_.on -notlike '*[*]*' })[0]
Check ("PreToolUse without hook_event_name: {0}" -f $first.on) ((Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = [string]$first.on } })) -eq (ExpectedFor @([string]$first.on)))

# 3. A wildcard subscription fires on a concrete name under it; matching is case-insensitive.
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -notlike '*[*]*') { continue }
  $name = ([string]$sub.on) -replace '\*', 'zzz'
  $got = Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = $name } })
  Check ("{0} matches {1} -> {2}" -f $sub.on, $name, $sub.insert) ($got -and $got.Contains((Expected $sub.insert)))
}
Check ("case-insensitive: {0}" -f $first.on.ToUpperInvariant()) ((Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = $first.on.ToUpperInvariant() } })) -eq (ExpectedFor @([string]$first.on)))

# 4. UserPromptExpansion: a typed command, prefixed and bare.
$prefixes = Prefixes
foreach ($sub in @($table.subscriptions)) {
  $on = [string]$sub.on
  if ($on -like '*[*]*' -or $on -notlike '*:*') { continue }
  $bare = $on.Substring($on.IndexOf(':') + 1)
  $out = Run @{ hook_event_name = 'UserPromptExpansion'; expansion_type = 'slash_command'; command_name = $on; command_args = ''; command_source = 'plugin'; prompt = "/$on" }
  $p = Parsed $out
  Check ("typed /{0} (prefixed) -> {1}" -f $on, $sub.insert) ($p -and $p.hookEventName -eq 'UserPromptExpansion' -and $p.additionalContext -eq (ExpectedFor @($on)))
  $cands = @($bare) + @($prefixes | ForEach-Object { "$($_):$bare" })
  $got = Context (Run @{ hook_event_name = 'UserPromptExpansion'; expansion_type = 'slash_command'; command_name = $bare; command_args = 'x'; command_source = 'plugin'; prompt = "/$bare x" })
  Check ("typed /{0} (bare) -> {1}" -f $bare, $sub.insert) ($got -eq (ExpectedFor $cands))
}
# A bare name under a wildcard subscription of this plugin's own prefix.
$ownWild = @($table.subscriptions | Where-Object { [string]$_.on -eq "$($own):*" })
if ($ownWild.Count -gt 0) {
  $got = Context (Run @{ hook_event_name = 'UserPromptExpansion'; command_name = 'anything-at-all'; command_source = 'plugin' })
  Check ("typed bare name under {0}:* -> {1}" -f $own, $ownWild[0].insert) ($got -eq (ExpectedFor (@('anything-at-all') + @($prefixes | ForEach-Object { "$($_):anything-at-all" }))))
}

if ($fail -gt 0) { Write-Host "$fail failure(s)"; exit 1 }
Write-Host 'all pass'
exit 0
