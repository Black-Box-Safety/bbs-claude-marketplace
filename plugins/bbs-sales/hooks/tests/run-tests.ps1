# Runs the bbs-sales hook scripts against fixture inputs. Exit 0 = all pass.
# Usage (Git Bash or PowerShell):
#   powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1
#   pwsh -NoProfile -File plugins/bbs-sales/hooks/tests/run-tests.ps1
# Runs under whichever PowerShell started it, on Windows, macOS or Linux. tests/parity.py runs
# the same fixtures through the Python halves and checks the two agree.
$ErrorActionPreference = 'Stop'
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$guard = Join-Path (Split-Path -Parent $here) 'guard-tree.ps1'
$ctx   = Join-Path (Split-Path -Parent $here) 'desk-context.ps1'
$exe   = (Get-Process -Id $PID).Path

# Fixture tree under the temp folder
$root = Join-Path ([IO.Path]::GetTempPath()) ("bbs-hook-tests-" + [guid]::NewGuid().ToString('N'))
$tree = Join-Path $root "All RFQ's by Agency"
$cdcr = Join-Path $tree 'CDCR (ALL)'
$mcsp = Join-Path $cdcr 'Mule Creek State Prison'
$filled = Join-Path $mcsp 'FILLED'
$packet = Join-Path $filled 'packet-b.pdf'
New-Item -ItemType Directory -Force -Path $filled | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $tree 'Cal Trans (ALL)') | Out-Null
Set-Content -Path $packet -Value 'x'
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

# A folder outside the desk tree that happens to carry its own quote-log.md (check 15).
$outside = Join-Path $root 'not-the-desk'
New-Item -ItemType Directory -Force -Path $outside | Out-Null
Set-Content -Path (Join-Path $outside 'quote-log.md') -Value '| 2026-04-01 | Decoy row | SQ-9999 | - | 0 | - |'

function Run($script, $obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 5
  return ($json | & $exe -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim()
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
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = $packet; content='y' } }
Check 'overwrite FILLED denied' (Decision $o) 'deny'

# 4. New file in FILLED -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $filled 'packet-c.pdf'); content='y' } }
Check 'new FILLED file allowed' (Decision $o) 'allow'

# 5. Near-duplicate buyer folder via mkdir -> deny (CalTrans vs Cal Trans (ALL))
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mkdir `"$tree\CalTrans`"" } }
Check 'near-duplicate agency folder denied' (Decision $o) 'deny'

# 6. Near-duplicate buyer folder via Write into new folder -> deny (Mule Creek Prison vs Mule Creek State Prison)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path (Join-Path $cdcr 'Mule Creek Prison') 'CLAUDE.md'); content='x' } }
Check 'near-duplicate buyer via Write denied' (Decision $o) 'deny'

# 7. Genuinely new buyer folder -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path (Join-Path $cdcr 'Folsom State Prison') 'CLAUDE.md'); content='x' } }
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

# 11. Rename inside the tree through the PowerShell tool -> deny (same guard, other shell)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='PowerShell'; tool_input=@{ command = "Rename-Item `"$cdcr`" 'CDCR'" } }
Check 'powershell rename inside tree denied' (Decision $o) 'deny'

# 12. Deleting a submitted packet through the shell -> deny
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "rm `"$packet`"" } }
Check 'bash rm of FILLED packet denied' (Decision $o) 'deny'

# 13. Reading a submitted packet through the shell -> allow (immutable, not unreadable)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "cat `"$packet`"" } }
Check 'bash cat of FILLED packet allowed' (Decision $o) 'allow'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "pdftotext `"$packet`" > `"$root\out.txt`"" } }
Check 'bash redirect FROM FILLED elsewhere allowed' (Decision $o) 'allow'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "echo y > `"$packet`"" } }
Check 'bash redirect INTO FILLED denied' (Decision $o) 'deny'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "cp `"$root\new.pdf`" `"$packet`"" } }
Check 'bash cp ONTO FILLED packet denied' (Decision $o) 'deny'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "cp `"$packet`" `"$root\copy.pdf`"" } }
Check 'bash cp OUT of FILLED allowed' (Decision $o) 'allow'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='PowerShell'; tool_input=@{ command = "Set-Content -Path `"$packet`" -Value y" } }
Check 'powershell Set-Content onto FILLED denied' (Decision $o) 'deny'

$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "echo y | tee `"$packet`"" } }
Check 'bash tee onto FILLED denied' (Decision $o) 'deny'

# 14. Acronym typo folder via mkdir -> deny (CDRC vs CDCR)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mkdir `"$tree\CDRC (ALL)`"" } }
Check 'acronym typo agency folder denied' (Decision $o) 'deny'

# 15. Session start outside the tree, in a folder that has a quote-log.md -> silent
$o = Run $ctx @{ hook_event_name='SessionStart'; source='startup'; cwd = $outside }
Check 'session context silent outside tree with quote-log' ($o -eq '') $true

# 16. PostToolUse: first write in a dated deal folder (3-level and 2-level agencies). parity.py holds the
#     full matrix; these prove the PowerShell half on its own. BBS_TODAY pins today; the temp dir is
#     fresh per run so markers never leak between cases.
$env:BBS_TODAY = '2026-10-30'
function RunPost($path, $sid) {
  $t = Join-Path $root ("tmp-" + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $t | Out-Null
  $env:TMPDIR = $t; $env:TEMP = $t; $env:TMP = $t
  $p = @{ hook_event_name='PostToolUse'; tool_name='Write'; tool_input=@{ file_path = $path } }
  if ($sid) { $p.session_id = $sid }
  return (Run $ctx $p)
}
function AddedContext($out) {
  if (-not $out) { return '' }
  try { return ($out | ConvertFrom-Json).hookSpecificOutput.additionalContext } catch { return "unparseable: $out" }
}
$joe = Join-Path (Join-Path $cdcr 'CAL - Calipatria State Prison - 887895116') 'Joe Ketner'
New-Item -ItemType Directory -Force -Path (Join-Path $joe '9.14.26') | Out-Null
Set-Content -Path (Join-Path $joe 'CLAUDE.md') -Value '# Joe Ketner'
Set-Content -Path (Join-Path $joe 'quote-log.md') -Value @(
  '| Date | Item | Quote # | Vehicle | Value | Outcome |',
  '|---|---|---|---|---|---|',
  '| 9.14.26 | V-belts | 900021 | OBS 4007(A) | 3668.70 | priced, awaiting signature |',
  '| 10.7.26 | Refrigerants | SQ-105100 | OBS 4007(B) | 23981.10 | packet signed, not sent |',
  '| 2026-03-04 | Nitrile gloves | SQ-1001 | NASPO | 2400 | won |',
  '| 7.13.23 | Gloves | SQ-0001 | NASPO | 100 | sent |'
)
Set-Content -Path (Join-Path $joe 'FLAGS.md') -Value @(
  '| Date | What | Status |', '|---|---|---|',
  '| 2026-10-23 | worksheet rows overwritten | open |',
  '| 10.2.26 | old radio bug | closed 10.3.26 |',
  '- 9.20.26 bullet flag one'
)
$c = AddedContext (RunPost (Join-Path (Join-Path $joe '9.14.26') 'form.pdf') 's1')
Check 'first write names the buyer files' ($c -match 'BUYER DESK -- first write in 9\.14\.26 for CDCR \(ALL\)/CAL - Calipatria State Prison - 887895116/Joe Ketner' -and $c -match 'quote-log\.md --') $true
Check 'first write: precedent newest first' ($c.IndexOf('| 10.7.26 |') -ge 0 -and $c.IndexOf('| 10.7.26 |') -lt $c.IndexOf('| 9.14.26 |') -and $c.IndexOf('| 9.14.26 |') -lt $c.IndexOf('| 2026-03-04 |')) $true
Check 'first write: two stale rows, oldest first' ($c -match 'OUTCOMES TO CLOSE -- 2 quote-log rows older than 30 days' -and $c.LastIndexOf('| 7.13.23 | Gloves') -lt $c.LastIndexOf('| 9.14.26 | V-belts')) $true
Check 'first write: flags incl. bullet, closed dropped' ($c -match 'worksheet rows overwritten' -and $c -match 'bullet flag one' -and $c -notmatch 'old radio bug') $true

$kelly = Join-Path (Join-Path $tree 'CARB - Air Resource Board - 888161763') 'Kelly Peng'
New-Item -ItemType Directory -Force -Path (Join-Path (Join-Path $kelly '10.12.26') 'SacHQ') | Out-Null
Set-Content -Path (Join-Path $kelly 'quote-log.md') -Value @('| Date | Item | Quote # | Vehicle | Value | Outcome |', '|---|---|---|---|---|---|', '| 10.28.26 | Office supplies | SQ-105283 | OPEN | 190.76 | logged |')
$c = AddedContext (RunPost (Join-Path (Join-Path (Join-Path $kelly '10.12.26') 'SacHQ') 'quote.pdf') 's1')
Check 'two-level agency: CLAUDE.md missing, no close-out' ($c -match 'MISSING: CLAUDE\.md, FLAGS\.md -- create from' -and $c -notmatch 'OUTCOMES TO CLOSE') $true

$o = RunPost (Join-Path $joe 'quote-log.md') 's1'
Check 'silent: file directly in the buyer folder' ($o -eq '') $true
$o = RunPost (Join-Path (Join-Path $joe 'AIU-21') 'form.pdf') 's1'
Check 'silent: deal folder without a date' ($o -eq '') $true

# Once per buyer per session: same temp dir, second write silent.
$t = Join-Path $root 'tmp-once'
New-Item -ItemType Directory -Force -Path $t | Out-Null
$env:TMPDIR = $t; $env:TEMP = $t; $env:TMP = $t
$pj = @{ hook_event_name='PostToolUse'; tool_name='Write'; session_id='once'; tool_input=@{ file_path = (Join-Path (Join-Path $joe '9.14.26') 'form.pdf') } }
$first = Run $ctx $pj
$again = Run $ctx $pj
Check 'once per buyer per session' ($first -ne '' -and $again -eq '') $true

Remove-Item -Recurse -Force $root
Write-Host ""
if ($fails -eq 0) { Write-Host "ALL PASS"; exit 0 } else { Write-Host "$fails FAILED"; exit 1 }
