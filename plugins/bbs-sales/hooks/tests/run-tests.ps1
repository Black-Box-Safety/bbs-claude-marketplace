# Runs the bbs-sales hook scripts against fixture inputs. Exit 0 = all pass.
# Usage (Git Bash or PowerShell):  powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1
$ErrorActionPreference = 'Stop'
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$guard = Join-Path (Split-Path -Parent $here) 'guard-tree.ps1'
$ctx   = Join-Path (Split-Path -Parent $here) 'desk-context.ps1'

# Fixture tree under %TEMP%
$root = Join-Path $env:TEMP ("bbs-hook-tests-" + [guid]::NewGuid().ToString('N'))
$tree = Join-Path $root "All RFQ's by Agency"
$cdcr = Join-Path $tree 'CDCR (ALL)'
$mcsp = Join-Path $cdcr 'Mule Creek State Prison'
New-Item -ItemType Directory -Force -Path (Join-Path $mcsp 'FILLED') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $tree 'Cal Trans (ALL)') | Out-Null
Set-Content -Path (Join-Path $mcsp 'FILLED\packet-b.pdf') -Value 'x'
Set-Content -Path (Join-Path $mcsp 'quote-log.md') -Value @(
  '| Date | Item | Quote# | Vehicle | Value | Outcome |',
  '|---|---|---|---|---|---|',
  '| 2026-03-04 | Nitrile gloves | SQ-1001 | NASPO | 2400 | won |'
)
Set-Content -Path (Join-Path $mcsp 'FLAGS.md') -Value @(
  '| Date | Skill/step | What happened | Caught before send? | Fixed by |',
  '|---|---|---|---|---|',
  '| 2026-09-15 | naspo-quote | wrong solicitation # | yes | (Parker: triage) |'
)

function Run($script, $obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 5
  return ($json | powershell -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim()
}
function Decision($out) {
  if (-not $out) { return 'allow' }
  try { return ((($out | ConvertFrom-Json).hookSpecificOutput).permissionDecision) } catch { return "unparseable: $out" }
}

$fails = 0
function Check($name, $got, $want) {
  if ($got -eq $want) { Write-Host "PASS  $name" } else { Write-Host "FAIL  $name  (got '$got', want '$want')"; $script:fails++ }
}

# 1. Rename inside the tree via Bash -> deny
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mv `"$cdcr`" `"$tree\CDCR`"" } }
Check 'bash mv inside tree denied' (Decision $o) 'deny'

# 2. Rename outside the tree -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = 'mv a.txt b.txt' } }
Check 'bash mv elsewhere allowed' (Decision $o) 'allow'

# 3. Overwrite an existing FILLED file -> deny
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $mcsp 'FILLED\packet-b.pdf'); content='y' } }
Check 'overwrite FILLED denied' (Decision $o) 'deny'

# 4. New file in FILLED -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $mcsp 'FILLED\packet-c.pdf'); content='y' } }
Check 'new FILLED file allowed' (Decision $o) 'allow'

# 5. Near-duplicate buyer folder via mkdir -> deny (CalTrans vs Cal Trans (ALL))
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mkdir `"$tree\CalTrans`"" } }
Check 'near-duplicate agency folder denied' (Decision $o) 'deny'

# 6. Near-duplicate buyer folder via Write into new folder -> deny (Mule Creek Prison vs Mule Creek State Prison)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $cdcr 'Mule Creek Prison\CLAUDE.md'); content='x' } }
Check 'near-duplicate buyer via Write denied' (Decision $o) 'deny'

# 7. Genuinely new buyer folder -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $cdcr 'Folsom State Prison\CLAUDE.md'); content='x' } }
Check 'new distinct buyer allowed' (Decision $o) 'allow'

# 8. Edit of an ordinary file in the tree -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Edit'; tool_input=@{ file_path = (Join-Path $mcsp 'quote-log.md'); old_string='a'; new_string='b' } }
Check 'edit quote-log allowed' (Decision $o) 'allow'

# 9. Session start inside a buyer folder -> precedent + flags in stdout
$o = Run $ctx @{ hook_event_name='SessionStart'; source='startup'; cwd = $mcsp }
Check 'session context has precedent' ($o -match 'PRECEDENT' -and $o -match 'SQ-1001') $true
Check 'session context has flags'     ($o -match 'OPEN FLAGS' -and $o -match 'wrong solicitation') $true

# 10. Session start outside any buyer folder -> silent
$o = Run $ctx @{ hook_event_name='SessionStart'; source='startup'; cwd = $root }
Check 'session context silent outside tree' ($o -eq '') $true

Remove-Item -Recurse -Force $root
Write-Host ""
if ($fails -eq 0) { Write-Host "ALL PASS"; exit 0 } else { Write-Host "$fails FAILED"; exit 1 }
