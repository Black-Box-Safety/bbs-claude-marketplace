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
# Independent computation of what a name should inject. $bare = the typed-command rule for
# a name with no colon: bare patterns as is, plugin:suffix by suffix, plugin:* skipped.
function ExpectedFor([string]$name, [bool]$bare) {
  $seen = New-Object System.Collections.Generic.List[string]
  foreach ($s in @($table.subscriptions)) {
    if ($seen.Contains([string]$s.insert)) { continue }
    $on = [string]$s.on
    $hit = $false
    if (-not $bare -or $on.IndexOf(':') -lt 0) { $hit = ($name -like $on) }
    else {
      $suffix = $on.Substring($on.IndexOf(':') + 1)
      if ($suffix -ne '*' -and $suffix -ne '**') { $hit = ($name -like $suffix) }
    }
    if ($hit) { $seen.Add([string]$s.insert) }
  }
  if ($seen.Count -eq 0) { return $null }
  return (@($seen | ForEach-Object { Expected $_ }) -join "`n`n")
}
function Typed([string]$name, [string]$source) {
  return (Run @{ hook_event_name = 'UserPromptExpansion'; expansion_type = 'slash_command'; command_name = $name; command_args = 'x'; command_source = $source; prompt = "/$name x" })
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

# 2. PreToolUse: every non-wildcard subscription injects, byte for byte, every insert whose
#    pattern matches that name (a name can sit under an exact pattern AND a plugin:* one).
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -like '*[*]*') { continue }
  $out = Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = [string]$sub.on } }
  $p = Parsed $out
  Check ("PreToolUse {0} -> {1}" -f $sub.on, $sub.insert) ($p -and $p.hookEventName -eq 'PreToolUse' -and $p.additionalContext -eq (ExpectedFor ([string]$sub.on) $false))
}
# 2b. The same, without hook_event_name (older input shape): tool_name alone routes it.
$first = @($table.subscriptions | Where-Object { [string]$_.on -notlike '*[*]*' })[0]
Check ("PreToolUse without hook_event_name: {0}" -f $first.on) ((Context (Run @{ tool_name = 'Skill'; tool_input = @{ skill = [string]$first.on } })) -eq (ExpectedFor ([string]$first.on) $false))

# 3. A wildcard subscription fires on a concrete name under it; matching is case-insensitive.
foreach ($sub in @($table.subscriptions)) {
  if ([string]$sub.on -notlike '*[*]*') { continue }
  $name = ([string]$sub.on) -replace '\*', 'zzz'
  $got = Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = $name } })
  Check ("{0} matches {1} -> {2}" -f $sub.on, $name, $sub.insert) ($got -and $got.Contains((Expected $sub.insert)))
}
Check ("case-insensitive: {0}" -f $first.on.ToUpperInvariant()) ((Context (Run @{ hook_event_name = 'PreToolUse'; tool_name = 'Skill'; tool_input = @{ skill = $first.on.ToUpperInvariant() } })) -eq (ExpectedFor ([string]$first.on) $false))

# 4. UserPromptExpansion: a typed command, prefixed (whole-pattern match) and bare (the
#    retired plugin's bare-name rule: plugin:* skipped, plugin:suffix by suffix).
foreach ($sub in @($table.subscriptions)) {
  $on = [string]$sub.on
  if ($on -like '*[*]*') { continue }
  if ($on -like '*:*') {
    $p = Parsed (Typed $on 'plugin')
    Check ("typed /{0} (prefixed) -> {1}" -f $on, $sub.insert) ($p -and $p.hookEventName -eq 'UserPromptExpansion' -and $p.additionalContext -eq (ExpectedFor $on $false))
    $bare = $on.Substring($on.IndexOf(':') + 1)
  } else { $bare = $on }
  $got = Context (Typed $bare 'plugin')
  Check ("typed /{0} (bare) -> {1} only, plugin:* skipped" -f $bare, $sub.insert) ($got -and $got -eq (ExpectedFor $bare $true))
}
# 4b. Bare names that only a plugin:* pattern could claim get nothing (the retired injection plugin's rule).
foreach ($n in @('brainstorming', 'bbs-checkup', 'ca-rfq', 'anything-at-all')) {
  Check ("typed bare /{0} is silent" -f $n) (($null -eq (ExpectedFor $n $true)) -and ($null -eq (Context (Typed $n 'plugin'))))
}
# 4c. A bare name under a bare pattern gets that insert and NOT the plugin:* ones.
$barePat = @($table.subscriptions | Where-Object { [string]$_.on -notlike '*:*' -and [string]$_.on -notlike '*[*]*' })
if ($barePat.Count -gt 0) {
  $got = Context (Typed ([string]$barePat[0].on) 'plugin')
  $others = @($table.inserts.PSObject.Properties.Name | Where-Object { $_ -ne [string]$barePat[0].insert })
  $leak = $false; foreach ($o in $others) { if ($got -and $got.Contains((Expected $o))) { $leak = $true } }
  Check ("typed bare /{0} -> {1} and no other insert" -f $barePat[0].on, $barePat[0].insert) ($got -eq (Expected $barePat[0].insert) -and -not $leak)
}
# 4d. An MCP server's prompt named like a skill is not a skill.
Check 'mcp_prompt expansion is silent' ($null -eq (Context (Run @{ hook_event_name = 'UserPromptExpansion'; expansion_type = 'mcp_prompt'; command_name = [string]$first.on; command_source = 'mcp' })))
Check 'typed unrelated prefixed command is silent' ($null -eq (Context (Typed 'nobody:unrelated' 'user')))

if ($fail -gt 0) { Write-Host "$fail failure(s)"; exit 1 }
Write-Host 'all pass'
exit 0
