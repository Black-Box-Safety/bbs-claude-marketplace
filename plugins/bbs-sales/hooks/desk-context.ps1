# Quote-desk buyer context, two events:
#   SessionStart  cwd inside the desk tree: put that buyer's newest quote-log rows and open FLAGS
#                 entries in front of Claude before the first prompt.
#   PostToolUse   first Write/Edit inside a dated deal folder (<Agency>/<Buyer>/<Item M.D.YY>/ or
#                 <Agency>/<Institution>/<Buyer>/<Item M.D.YY>/): the same rows and flags, the
#                 buyer's CLAUDE.md / quote-log.md / FLAGS.md named as the files to keep current,
#                 and the buyer's quote-log rows older than 30 days with no final outcome listed
#                 for close-out. Once per buyer per session (temp-dir marker keyed on session_id).
#
# The PowerShell half of desk-context.py: same output on every input, proven by
# hooks/tests/parity.py. Change both or neither (invariant 3).
# SessionStart prints plain text; PostToolUse prints hookSpecificOutput JSON. Silent when the
# folder shape is unclear or nothing relevant is found. Always exits 0. BBS_TODAY=YYYY-MM-DD pins
# "today" for the tests.

$ErrorActionPreference = 'SilentlyContinue'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$TREE = "All RFQ's by Agency"
$BUYER_FILES = @('CLAUDE.md', 'quote-log.md', 'FLAGS.md')
$STALE_DAYS = 30
$DEAL_START = '^\s*[0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})(?![0-9])'
$DEAL_END = '[ _-][0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})\s*$'
$DEAL_ISO = '[ _-][0-9]{4}-[0-9]{2}-[0-9]{2}\s*$'
$ISO = '^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})$'
$MDY = '^([0-9]{1,2})[./]([0-9]{1,2})[./]([0-9]{2}|[0-9]{4})$'
$DATE_TOKEN = '(?<![0-9])([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4}))(?![0-9])'
$ICASE = [System.Text.RegularExpressions.RegexOptions]::IgnoreCase

function Split-Lines([string]$text) {
  $parts = [regex]::Split($text, "\r\n|\n|\r")
  if ($parts.Count -gt 0 -and $parts[$parts.Count - 1] -eq '') {
    if ($parts.Count -eq 1) { return @() }
    return @($parts[0..($parts.Count - 2)])
  }
  return @($parts)
}

function Read-Text([string]$path) {
  return [System.IO.File]::ReadAllText($path, $utf8)
}

function Get-Cells([string]$line) {
  $t = $line.Trim()
  if (-not $t.StartsWith('|')) { return $null }
  $t = $t.Substring(1)
  if ($t.EndsWith('|')) { $t = $t.Substring(0, $t.Length - 1) }
  $out = @()
  foreach ($c in $t.Split('|')) { $out += $c.Trim() }
  return , $out
}

function Parse-Date([string]$s) {
  $m = [regex]::Match($s, $ISO)
  if ($m.Success) {
    $y = [int]$m.Groups[1].Value; $mo = [int]$m.Groups[2].Value; $d = [int]$m.Groups[3].Value
  } else {
    $m = [regex]::Match($s, $MDY)
    if (-not $m.Success) { return $null }
    $mo = [int]$m.Groups[1].Value; $d = [int]$m.Groups[2].Value; $y = [int]$m.Groups[3].Value
    if ($m.Groups[3].Value.Length -eq 2) { $y += 2000 }
  }
  if ($y -lt 1 -or $y -gt 9999 -or $mo -lt 1 -or $mo -gt 12 -or $d -lt 1 -or $d -gt [DateTime]::DaysInMonth($y, $mo)) { return $null }
  return , @($y, $mo, $d)
}

function Date-Key($t) { return [long]$t[0] * 10000 + [long]$t[1] * 100 + [long]$t[2] }

function Day-Number($t) {
  $dt = New-Object DateTime -ArgumentList @([int]$t[0], [int]$t[1], [int]$t[2])
  return [long][math]::Floor($dt.Ticks / 864000000000)
}

function Today-Number {
  $raw = $env:BBS_TODAY
  if ($raw) { $t = Parse-Date $raw; if ($t) { return Day-Number $t } }
  $n = Get-Date
  return Day-Number @($n.Year, $n.Month, $n.Day)
}

function Get-LogRows([string[]]$lines) {
  $script:logHeader = $null
  $rows = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i]
    $c = Get-Cells $l
    if ($null -eq $c) { continue }
    if ([regex]::IsMatch($l.Trim(), '^\|[\s:|-]+$') -or $c[0] -eq '') { continue }
    if ($c[0].ToLowerInvariant() -eq 'date') {
      if ($null -eq $script:logHeader) { $script:logHeader = $l }
      continue
    }
    $d = Parse-Date $c[0]
    $k = 0
    if ($d) { $k = Date-Key $d }
    $rows += [pscustomobject]@{ Idx = $i; Line = $l; Cells = $c; D = $d; Key = [long]$k }
  }
  return , $rows
}

function Get-Recent($rows, [int]$n) {
  $sorted = @($rows | Sort-Object -Property @{ Expression = { $_.Key * 1000000 + (999999 - $_.Idx) }; Descending = $true })
  if ($sorted.Count -gt $n) { return @($sorted[0..($n - 1)]) }
  return $sorted
}

function Get-Stale($rows) {
  $now = Today-Number
  $out = @()
  foreach ($r in $rows) {
    if ($null -eq $r.D) { continue }
    if (($now - (Day-Number $r.D)) -le $STALE_DAYS) { continue }
    $outcome = ''
    if ($r.Cells.Count -gt 5) { $outcome = [regex]::Replace($r.Cells[5], '^[`*_ ]+', '') }
    if ([regex]::IsMatch($outcome, '^(won|lost|no answer)\b', $ICASE) -or $outcome.ToLowerInvariant().Contains('[flag')) { continue }
    $out += $r
  }
  return @($out | Sort-Object -Property @{ Expression = { $_.Key * 1000000 + $_.Idx } })
}

function Get-FlagEntries([string[]]$lines, [int]$n) {
  $ents = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i]
    $c = Get-Cells $l
    $d = $null
    if ($null -ne $c) {
      if ([regex]::IsMatch($l.Trim(), '^\|[\s:|-]+$') -or $c[0] -eq '') { continue }
      $d = Parse-Date $c[0]
      if ($null -eq $d) { continue }
      if ([regex]::IsMatch($c[$c.Count - 1], '^(closed|resolved)\b', $ICASE)) { continue }
    } else {
      $m = [regex]::Match($l, '^\s*[-*]\s+(.*)$')
      if (-not $m.Success) { continue }
      $body = $m.Groups[1].Value
      if ([regex]::IsMatch($body, '^(\[x\]|~~|closed\b|resolved\b)', $ICASE)) { continue }
      $t = [regex]::Match($body, $DATE_TOKEN)
      if ($t.Success) { $d = Parse-Date $t.Groups[1].Value }
    }
    $k = 0
    if ($d) { $k = Date-Key $d }
    $ents += [pscustomobject]@{ Sort = [long]$k * 1000000 + $i; Line = $l }
  }
  $sorted = @($ents | Sort-Object -Property @{ Expression = { $_.Sort }; Descending = $true })
  if ($sorted.Count -gt $n) { $sorted = @($sorted[0..($n - 1)]) }
  return @($sorted | ForEach-Object { $_.Line })
}

function Get-PrecedentBlock([string]$path) {
  $rows = Get-LogRows (Split-Lines (Read-Text $path))
  $header = $script:logHeader
  $pick = @(Get-Recent $rows 12)
  $out = @("PRECEDENT -- $path (newest first; cite these before pricing):")
  if ($null -ne $header -and $pick.Count -gt 0) { $out += $header }
  foreach ($r in $pick) { $out += $r.Line }
  return $out
}

function Get-FlagsBlock([string]$path) {
  $ents = @(Get-FlagEntries (Split-Lines (Read-Text $path)) 5)
  if ($ents.Count -eq 0) { return @() }
  return @("OPEN FLAGS -- $path (latest; do not repeat these mistakes):") + $ents
}

function Get-SessionStart([string]$d) {
  if ($d.IndexOf($TREE, [StringComparison]::OrdinalIgnoreCase) -lt 0) { return @() }
  $out = @()
  for ($i = 0; $i -lt 5 -and $d; $i++) {
    $ql = Join-Path $d 'quote-log.md'
    $fl = Join-Path $d 'FLAGS.md'
    if (Test-Path -LiteralPath $ql) { $out += Get-PrecedentBlock $ql }
    if (Test-Path -LiteralPath $fl) { $out += Get-FlagsBlock $fl }
    if ($out.Count -gt 0) { break }
    $parent = Split-Path -Parent $d
    if ($parent -eq $d) { break }
    $d = $parent
  }
  return $out
}

function Find-Buyer([string]$path) {
  $end = -1
  foreach ($m in [regex]::Matches($path, [regex]::Escape($TREE), $ICASE)) {
    $a = $m.Index; $b = $m.Index + $m.Length
    if (($a -eq 0 -or '/\'.IndexOf($path[$a - 1]) -ge 0) -and $b -lt $path.Length -and '/\'.IndexOf($path[$b]) -ge 0) { $end = $b; break }
  }
  if ($end -lt 0) { return $null }
  $sep = [string]$path[$end]
  $comps = @([regex]::Split($path.Substring($end + 1), '[\\/]+') | Where-Object { $_ -ne '' })
  if ($comps.Count -lt 4) { return $null }
  foreach ($c in $comps) { if ($c.StartsWith('.')) { return $null } }
  $j = -1
  for ($k = 0; $k -lt $comps.Count - 1; $k++) {
    $c = $comps[$k]
    if ([regex]::IsMatch($c, $DEAL_START) -or [regex]::IsMatch($c, $DEAL_END) -or [regex]::IsMatch($c, $DEAL_ISO)) { $j = $k; break }
  }
  if ($j -lt 2 -or $j -gt 3) { return $null }
  $buyerDir = $path.Substring(0, $end) + $sep + ($comps[0..($j - 1)] -join $sep)
  if (-not (Test-Path -LiteralPath $buyerDir -PathType Container)) { return $null }
  $have = $false
  foreach ($f in $BUYER_FILES) { if (Test-Path -LiteralPath (Join-Path $buyerDir $f) -PathType Leaf) { $have = $true } }
  if (-not $have) {
    foreach ($e in @(Get-ChildItem -LiteralPath $buyerDir -Force)) {
      if (-not $e.PSIsContainer) { continue }
      foreach ($f in @('CLAUDE.md', 'quote-log.md')) {
        if (Test-Path -LiteralPath (Join-Path $e.FullName $f) -PathType Leaf) { return $null }
      }
    }
  }
  return [pscustomobject]@{ Dir = $buyerDir; Rel = ($comps[0..($j - 1)] -join '/'); Deal = $comps[$j] }
}

function Get-Safe([string]$s) { return [regex]::Replace($s, '[^A-Za-z0-9]+', '-') }

function Get-FirstWrite($h) {
  $ti = $h.tool_input
  $p = $null
  if ($null -ne $ti) { $p = $ti.file_path }
  if (-not ($p -is [string]) -or [string]::IsNullOrWhiteSpace($p)) { return @() }
  $loc = Find-Buyer $p
  if ($null -eq $loc) { return @() }
  $buyerDir = $loc.Dir

  $sid = $h.session_id
  $marker = $null
  if (($sid -is [string]) -and -not [string]::IsNullOrWhiteSpace($sid)) {
    $marker = Join-Path (Join-Path ([System.IO.Path]::GetTempPath()) 'bbs-desk-buyer') ((Get-Safe $sid) + '--' + (Get-Safe $loc.Rel))
    if (Test-Path -LiteralPath $marker) { return @() }
  }

  $out = @("BUYER DESK -- first write in $($loc.Deal) for $($loc.Rel) (once per session). Keep this buyer's files current in ${buyerDir}:",
           "  CLAUDE.md -- how they buy, what we learned (add a line only when something surprised you)",
           "  quote-log.md -- one row per request; set the Outcome when you learn it",
           "  FLAGS.md -- one entry for anything that went wrong, caught before send or not")
  $missing = @()
  foreach ($f in $BUYER_FILES) { if (-not (Test-Path -LiteralPath (Join-Path $buyerDir $f) -PathType Leaf)) { $missing += $f } }
  if ($missing.Count -gt 0) {
    $out += ("MISSING: " + ($missing -join ', ') + " -- create from the ca-rfq-intake skill's references/buyer-context-template.md " +
             "(FLAGS.md: bbs-foundations, bbs-claude-md-forge/references/flags-template.md).")
  }
  $ql = Join-Path $buyerDir 'quote-log.md'
  $fl = Join-Path $buyerDir 'FLAGS.md'
  if (Test-Path -LiteralPath $ql -PathType Leaf) {
    $out += Get-PrecedentBlock $ql
    $rows = Get-LogRows (Split-Lines (Read-Text $ql))
    $stale = @(Get-Stale $rows)
    if ($stale.Count -gt 0) {
      $out += "OUTCOMES TO CLOSE -- $($stale.Count) quote-log rows older than $STALE_DAYS days have no final outcome (won / lost / no answer):"
      $top = $stale
      if ($stale.Count -gt 10) { $top = @($stale[0..9]) }
      foreach ($r in $top) { $out += $r.Line }
      if ($stale.Count -gt 10) { $out += "(+$($stale.Count - 10) more)" }
      $out += ((Split-Lines (Read-Text (Join-Path (Join-Path $PSScriptRoot 'desk-context') 'outcome-closeout.md'))) -join "`n")
    }
  }
  if (Test-Path -LiteralPath $fl -PathType Leaf) { $out += Get-FlagsBlock $fl }

  if ($marker) {
    try {
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $marker) | Out-Null
      New-Item -ItemType File -Force -Path $marker | Out-Null
    } catch { }
  }
  return $out
}

function ConvertTo-JsonString([string]$s) {
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append('"')
  foreach ($ch in $s.ToCharArray()) {
    $c = [int]$ch
    if ($c -eq 34) { [void]$sb.Append('\"') }
    elseif ($c -eq 92) { [void]$sb.Append('\\') }
    elseif ($c -eq 10) { [void]$sb.Append('\n') }
    elseif ($c -eq 13) { [void]$sb.Append('\r') }
    elseif ($c -eq 9) { [void]$sb.Append('\t') }
    elseif ($c -eq 8) { [void]$sb.Append('\b') }
    elseif ($c -eq 12) { [void]$sb.Append('\f') }
    elseif ($c -lt 32 -or $c -gt 126) { [void]$sb.Append(('\u{0:x4}' -f $c)) }
    else { [void]$sb.Append($ch) }
  }
  [void]$sb.Append('"')
  return $sb.ToString()
}

function Emit([string]$text) {
  $bytes = $utf8.GetBytes($text)
  $stdout = [Console]::OpenStandardOutput()
  $stdout.Write($bytes, 0, $bytes.Length)
  $stdout.Flush()
}

try {
  $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $utf8)
  $raw = $reader.ReadToEnd().TrimStart([char]0xFEFF)
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    $h = $null
    try { $h = $raw | ConvertFrom-Json } catch { $h = $null }
    if ($null -ne $h -and $h -isnot [array] -and $h -isnot [string] -and $h -isnot [ValueType]) {
      if ($h.hook_event_name -eq 'PostToolUse') {
        $out = @(Get-FirstWrite $h)
        if ($out.Count -gt 0) {
          $ctx = $out -join "`n"
          Emit ('{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":' + (ConvertTo-JsonString $ctx) + '}}')
        }
      } else {
        $d = [string]$h.cwd
        if ($d -and (Test-Path -LiteralPath $d)) {
          $out = @(Get-SessionStart $d)
          if ($out.Count -gt 0) { Emit (($out -join "`n") + "`n") }
        }
      }
    }
  }
} catch { }
exit 0
