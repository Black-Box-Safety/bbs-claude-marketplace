# PostToolUse fallback for the RFQ record check. It validates NOTHING.
#
# The RFQ record has one validator: rfq-record-hook.py over scripts/rfq_record.py. hooks.json runs
# python3 first; this script runs only when no working python3 is on PATH. A second, partial copy
# of the record format here would decide differently from the Python half and would be a second
# home for the format (AGENTS.md invariants 2 and 3), so this half says the check did not run
# instead of running part of it.
#
# For an RFQ.md under "All RFQ's by Agency" (same path test as the Python half, backslashes
# normalised): stdout {"systemMessage": NOTICE}, exit 0, writes nothing. Anything else, including
# garbage on stdin: silent exit 0. hooks/tests/parity.py asserts the notice text.
# Windows PowerShell 5.1 compatible.

$NOTICE = 'bbs-sales: RFQ record check needs python3; this edit was not checked. Install Python 3 (rerun the bootstrap) so RFQ.md is validated and rfq-state.json is written.'

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $h = $raw | ConvertFrom-Json } catch { exit 0 }
if ($null -eq $h -or $h -is [array]) { exit 0 }
$inp = $h.tool_input
if ($null -eq $inp) { exit 0 }
$path = [string]$inp.file_path
if ([string]::IsNullOrEmpty($path)) { exit 0 }

$norm = $path.Replace('\', '/')
if (-not $norm.Contains("/All RFQ's by Agency/")) { exit 0 }
if (-not $norm.EndsWith('/RFQ.md', [StringComparison]::Ordinal)) { exit 0 }

# Built by hand, not ConvertTo-Json, so 5.1 and 7 emit the same bytes.
$esc = $NOTICE.Replace('\', '\\').Replace('"', '\"')
[Console]::Out.WriteLine('{"systemMessage": "' + $esc + '"}')
exit 0
