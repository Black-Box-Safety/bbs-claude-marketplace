# PostToolUse hook: check an RFQ.md under "All RFQ's by Agency".
# The PowerShell twin of rfq-record-hook.py. A SHAPE-ONLY SUBSET of the Python checks, writes
# nothing (compiling rfq-state.json is the Python hook's job): title, header Stage present and in
# the enum, the three exact table headers each inside its own section with a separator row, every
# Status Stage cell and Pricing Line stage cell in the enum, every Status Date cell empty or
# YYYY-MM-DD. It may PASS records the Python half rejects (other missing header keys, non-integer
# # cells, bad money cells, duplicate sections). Where both reject, the first stderr line matches
# for single-problem records; a v1 or legacy record (v1 Status header, or no **Stage:** header and no v2 Status table) passes with a systemMessage on stdout; exit 2 on failure, silent exit 0 otherwise. Windows PowerShell 5.1 compatible. Change both or neither.
# Enum comparisons use -ceq / -ccontains: -match and -eq are case-insensitive.

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $h = $raw | ConvertFrom-Json } catch { exit 0 }
if ($null -eq $h) { exit 0 }
$inp = $h.tool_input
if ($null -eq $inp) { exit 0 }
$path = [string]$inp.file_path
if ([string]::IsNullOrEmpty($path)) { exit 0 }

$TREE = "All RFQ's by Agency"
$norm = $path.Replace('\', '/')
if (-not $norm.Contains('/' + $TREE + '/')) { exit 0 }
if (-not $norm.EndsWith('/RFQ.md', [StringComparison]::Ordinal)) { exit 0 }
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { exit 0 }
try { $text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8) } catch { exit 0 }
if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }

$STAGES = @('logged', 'sourcing', 'priced', 'quote built', 'packet built', 'delivered to rep', 'sent', 'outcome')
$LINE_STAGES = @('open', 'sourcing', 'vendor quoted', 'priced', 'quoted', 'substituted', 'parked', 'no bid')
$V1_HEADER = '| Stage | State | Date |'
$LINES_HEADER = '| # | Item / part # | Description | Qty | UOM | Lane |'
$PRICING_HEADER = '| # | Vendor | Vendor ref | Cost | Sell | Strategy | Lead | Line stage | Evidence |'
$STATUS_HEADER = '| Stage | Date | Evidence |'

function Fail($problems) {
  $list = @($problems)
  [Console]::Error.WriteLine('bbs-sales rfq-record: ' + $list.Count + ' problem(s) in RFQ.md')
  foreach ($p in $list) { [Console]::Error.WriteLine($p) }
  exit 2
}

# Cells of a table row, split on unescaped pipes, trimmed.
function Get-Cells([string]$line) {
  $s = $line.Trim()
  if ($s.StartsWith('|')) { $s = $s.Substring(1) }
  if ($s.EndsWith('|')) { $s = $s.Substring(0, $s.Length - 1) }
  $out = @()
  foreach ($c in [regex]::Split($s, '(?<!\\)\|')) { $out += $c.Trim() }
  return , $out
}

# Find the section whose heading matches $headingRe, check its table header (the first '|' line
# after the heading) equals $header exactly and the next line is a '|' separator row, and return
# the data rows (lines are trimmed before the '|' test, like the Python half). Problems go into
# $script:problems. Returns $null when the section or its table is unusable.
function Get-Table($lines, [string]$headingRe, [string]$header, [string]$what) {
  $start = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -cmatch $headingRe) { $start = $i; break }
  }
  if ($start -lt 0) { $script:problems += ($what + ' section missing'); return $null }
  $i = $start + 1
  while ($i -lt $lines.Count -and -not $lines[$i].StartsWith('## ') -and -not $lines[$i].Trim().StartsWith('|')) { $i++ }
  if ($i -ge $lines.Count -or $lines[$i].StartsWith('## ') -or -not ($lines[$i].Trim() -ceq $header)) {
    $script:problems += ($what + ' table header missing or malformed; expected ' + $header)
    return $null
  }
  if (($i + 1) -ge $lines.Count -or -not $lines[$i + 1].Trim().StartsWith('|')) {
    $script:problems += ($what + ' table separator row missing')
    return $null
  }
  $rows = @()
  $j = $i + 2
  while ($j -lt $lines.Count -and $lines[$j].Trim().StartsWith('|')) { $rows += $lines[$j].Trim(); $j++ }
  return , $rows
}

$V1_NOTICE = 'bbs-sales: this RFQ.md is still in the v1 or legacy format, so it was not checked and no rfq-state.json was written. Run python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rfq_record.py" migrate "<path>" --dry-run to see whether it converts.'
$lines = [regex]::Split($text, "\r\n|\n")
# Legacy/v1 detection (same rule as rfq_record.is_v1): v1 Status header inside "## Status", or
# no **Stage:** header line (before the first "## ") and no v2 Status table inside "## Status".
$inStatus = $false; $seenH2 = $false; $hasStage = $false; $hasV2Status = $false; $hasV1Status = $false
foreach ($l in $lines) {
  if ($l.StartsWith('## ')) { $seenH2 = $true; $inStatus = ($l.TrimEnd() -ceq '## Status'); continue }
  if (-not $seenH2 -and $l.Contains('**Stage:**')) { $hasStage = $true }
  if ($inStatus -and $l.Trim() -ceq $V1_HEADER) { $hasV1Status = $true }
  if ($inStatus -and $l.Trim() -ceq $STATUS_HEADER) { $hasV2Status = $true }
}
if ($hasV1Status -or (-not $hasStage -and -not $hasV2Status)) {
  [Console]::Out.WriteLine((@{ systemMessage = $V1_NOTICE } | ConvertTo-Json -Compress))
  exit 0
}

$problems = @()

$first = $null
foreach ($l in $lines) { if ($l.Trim().Length -gt 0) { $first = $l; break } }
if ($null -eq $first -or -not $first.StartsWith('# ')) {
  Fail @('title (H1) missing')
}

# Header Stage: must be present and one of the eight stages (case-sensitive).
$stageVal = $null
foreach ($l in $lines) {
  if ($l.StartsWith('## ')) { break }
  $m = [regex]::Match($l, '\*\*Stage:\*\*[ \t]*((?:(?!\*\*).)*)')
  if ($m.Success) { $stageVal = $m.Groups[1].Value.Trim(); break }
}
if ($null -eq $stageVal) { $problems += 'header key missing: Stage' }
elseif (-not ($STAGES -ccontains $stageVal)) { $problems += "Header Stage '" + $stageVal + "' is not an allowed value" }

$statusRows = Get-Table $lines '^## Status\s*$' $STATUS_HEADER 'Status'
Get-Table $lines '^## Lines \(' $LINES_HEADER 'Lines' | Out-Null
$pricingRows = Get-Table $lines '^## Pricing\s*$' $PRICING_HEADER 'Pricing'

$n = 0
foreach ($r in $statusRows) {
  $n++
  $c = Get-Cells $r
  if ($c.Count -ne 3) { $problems += 'Status row has ' + $c.Count + ' cells, expected 3: ' + $r; continue }
  if (-not ($STAGES -ccontains $c[0])) { $problems += 'Status row ' + $n + " Stage '" + $c[0] + "' is not an allowed value" }
  if ($c[1].Length -gt 0 -and -not ($c[1] -cmatch '^\d{4}-\d{2}-\d{2}$')) { $problems += 'Status row ' + $n + " Date '" + $c[1] + "' is not YYYY-MM-DD" }
}
foreach ($r in $pricingRows) {
  $c = Get-Cells $r
  if ($c.Count -ne 9) { $problems += 'Pricing row has ' + $c.Count + ' cells, expected 9: ' + $r; continue }
  if ($c[7].Length -gt 0 -and -not ($LINE_STAGES -ccontains $c[7])) { $problems += 'Pricing row ' + $c[0] + " Line stage '" + $c[7] + "' is not an allowed value" }
}
if ($problems.Count -gt 0) { Fail $problems }
exit 0
