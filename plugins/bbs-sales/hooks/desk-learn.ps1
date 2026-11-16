# desk-learn: a reminder to close the loop when a key change lands on a customer desk.
#
# The PowerShell half of desk-learn.py (read its header for the events, the once-per-deal-per-event-
# per-session rule, the ledger and the Stop backstop). Same output on every input, proven by
# hooks/tests/desk_learn_parity.py; change both or neither (invariant 3). Reminds only: exit 0,
# never a block, never a write to a customer folder, never stderr. Fails open on anything unreadable.
#
# The one Stop switch is the environment variable BBS_DESK_LEARN_STOP: unset or "message" shows the
# rep one line; "continue" lets the hook resume the turn once. Default is message-only.
# Windows PowerShell 5.1 compatible. ASCII only (5.1 reads a script without a BOM as ANSI).

$ErrorActionPreference = 'Stop'

$TREE = "All RFQ's by Agency"
$SENTINEL = '/bechtel/sentinel/'
$MARKERS = 'bbs-desk-learn'
$STATE_FRESH_SECONDS = 5
$STOP_ENV = 'BBS_DESK_LEARN_STOP'

$EVENTS = @{
  'stage-sent'      = 'RFQ stage moved to sent'
  'stage-outcome'   = 'RFQ stage moved to outcome'
  'quote-log'       = 'quote-log row added or Outcome set'
  'filled'          = 'new file in FILLED/'
  'award'           = 'PO, award or NOA file written'
  'sentinel-log'    = 'Sentinel quote-log appended'
  'sentinel-banner' = 'RFP status banner edited'
}
$REMINDER = 'Key change: {0} in {1}. Close the loop: ask the rep one question. Is there anything about this buyer or site to remember? If so, run `desk-remember` with their words. Did this deal teach a lesson? If so, propose one `lessons.md` line and append it on their yes.'
$STOP_REASON = 'Key changes were made this session and nothing was captured or closed. Ask the rep one question, once: is there anything about this buyer or site to remember, or a lesson from this deal? If they give words, run `desk-remember` with them. If they say nothing, record it with `desk_memory.py close --none` through `bbs-fill`. Do not ask again.'
$STOP_MESSAGE = 'bbs-sales: key changes were made this session and nothing was saved for next time. Tell Claude what to remember, or say there is nothing to remember, before you close.'

$STAGE_RE = '(?m)^\*\*Stage:\*\*[ \t]*(.+?)[ \t]*\r?$'
$DATA_ROW = '(?m)^\|[ \t]*(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./][0-9]{1,2}[./](?:[0-9]{2}|[0-9]{4}))[ \t]*\|'
$BANNER = '(?m)^>[ \t]*\*\*Status'
$AWARD = '(?i)(?:^|[^A-Za-z])(?:PO|NOA|award|purchase[ _-]?order|notice[ _-]of[ _-]award)(?:[^A-Za-z]|$)'
$SET_STAGE = @'
rfq_record\.py["']?\s+set-stage\s+("[^"]*"|'[^']*'|\S+)\s+["']?(sent|outcome)["']?(?=\s|$)
'@
$MEMORY_CAPTURE = @'
desk_memory\.py["']?\s+(?:add|close)(?=\s|$)
'@
$APPEND_LOG = @'
>>[ \t]*(?:"([^"\n]*?quote-log\.md)"|'([^'\n]*?quote-log\.md)'|([^\s"';&|]*quote-log\.md))
'@
$FILLED_TOKEN = '(?i)/FILLED/'

function Norm([string]$p) { return $p.Replace('\', '/') }

function Get-Safe([string]$s) {
  $r = [regex]::Replace($s, '[^A-Za-z0-9]+', '-').Trim('-')
  if ($r.Length -gt 150) { $r = $r.Substring($r.Length - 150) }
  return $r
}

function Get-CleanName([string]$s) {
  $sb = New-Object System.Text.StringBuilder
  foreach ($ch in $s.ToCharArray()) {
    $c = [int]$ch
    if ($c -ge 32 -and $c -lt 127) { [void]$sb.Append($ch) } else { [void]$sb.Append('?') }
  }
  $t = ([regex]::Replace($sb.ToString(), ' +', ' ')).Trim(' ')
  if ($t.Length -gt 80) { $t = $t.Substring(0, 80) }
  return $t
}

function Test-Ca([string]$n) { return $n.ToLowerInvariant().Contains(('/' + $TREE + '/').ToLowerInvariant()) }
function Test-Sentinel([string]$n) { return $n.ToLowerInvariant().Contains($SENTINEL) }
function Get-Dir([string]$n) { $i = $n.LastIndexOf('/'); if ($i -ge 0) { return $n.Substring(0, $i) } else { return '' } }
function Get-Base([string]$n) { $i = $n.LastIndexOf('/'); if ($i -ge 0) { return $n.Substring($i + 1) } else { return $n } }

function Get-FolderOf([string]$n) {
  $d = Get-Dir $n
  if ($d.ToLowerInvariant().EndsWith('/filled')) { $d = Get-Dir $d }
  return $d
}

function Get-TmpDir { return (Join-Path ([System.IO.Path]::GetTempPath()) $MARKERS) }

function Read-Text([string]$path) {
  $b = [System.IO.File]::ReadAllBytes($path)
  $skip = 0
  if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { $skip = 3 }
  return [System.Text.Encoding]::UTF8.GetString($b, $skip, $b.Length - $skip)
}

function Get-NewTexts([string]$tool, $inp) {
  $out = New-Object System.Collections.ArrayList
  if ($tool -eq 'Write') { [void]$out.Add([string]$inp.content) }
  elseif ($tool -eq 'Edit') { [void]$out.Add([string]$inp.new_string) }
  elseif ($tool -eq 'MultiEdit') {
    if ($null -ne $inp.edits) {
      foreach ($e in @($inp.edits)) { if ($null -ne $e) { [void]$out.Add([string]$e.new_string) } }
    }
  }
  return ,$out
}

function Get-StageMoved([string]$path) {
  try { $m = [regex]::Match((Read-Text $path), $STAGE_RE) } catch { return $null }
  if (-not $m.Success) { return $null }
  $st = $m.Groups[1].Value.Trim().ToLowerInvariant()
  if ($st -ne 'sent' -and $st -ne 'outcome') { return $null }
  try {
    $state = Join-Path (Split-Path -Parent ([System.IO.Path]::GetFullPath($path))) 'rfq-state.json'
    $prev = [string]((Read-Text $state) | ConvertFrom-Json).stage
    $age = ([DateTime]::UtcNow - (Get-Item -LiteralPath $state).LastWriteTimeUtc).TotalSeconds
  } catch { return $st }
  if ($prev -eq $st -and $age -gt $STATE_FRESH_SECONDS) { return $null }
  return $st
}

function Get-LogEvent([string]$n) {
  if ((Test-Sentinel $n) -and (Get-Dir $n).ToLowerInvariant().EndsWith('/learning')) { return 'sentinel-log' }
  if (Test-Ca $n) { return 'quote-log' }
  return $null
}

function Add-Found([string]$ev, [string]$folder) {
  [void]$script:found.Add(@($ev, $folder))
}

function Test-AnyMatch($texts, [string]$re) {
  foreach ($t in $texts) { if ([regex]::IsMatch([string]$t, $re)) { return $true } }
  return $false
}

function Get-FileEvents([string]$tool, $inp) {
  $path = [string]$inp.file_path
  $n = Norm $path
  if ([string]::IsNullOrEmpty($n)) { return }
  $base = Get-Base $n
  $low = $n.ToLowerInvariant()
  $ca = Test-Ca $n
  $sen = Test-Sentinel $n
  if ($low.EndsWith('/learning/lessons.md')) { $script:capture = $true }
  $texts = Get-NewTexts $tool $inp
  if ($base -ceq 'RFQ.md' -and $ca) {
    $st = Get-StageMoved $path
    if ($st) { Add-Found ('stage-' + $st) (Get-FolderOf $n) }
  }
  elseif ($base -ceq 'quote-log.md') {
    $ev = Get-LogEvent $n
    if ($ev -and (Test-AnyMatch $texts $DATA_ROW)) { Add-Found $ev (Get-FolderOf $n) }
  }
  elseif ($base -ceq 'CLAUDE.md' -and $sen) {
    $rest = $low.Substring($low.IndexOf($SENTINEL) + $SENTINEL.Length)
    $slashes = $rest.Length - $rest.Replace('/', '').Length
    if ($slashes -ge 2 -and (Test-AnyMatch $texts $BANNER)) { Add-Found 'sentinel-banner' (Get-FolderOf $n) }
  }
  elseif ($ca -and $low.Contains('/filled/')) {
    if ($tool -eq 'Write') { Add-Found 'filled' (Get-FolderOf $n) }
  }
  elseif (($ca -or $sen) -and [regex]::IsMatch($base, $AWARD)) {
    Add-Found 'award' (Get-FolderOf $n)
  }
}

function Get-PrefixBefore([string]$s, [int]$idx) {
  $start = 0
  $found = $false
  for ($i = $idx - 1; $i -ge 0; $i--) {
    if ($s[$i] -eq '"' -or $s[$i] -eq "'") { $start = $i + 1; $found = $true; break }
  }
  if (-not $found) {
    for ($i = $idx - 1; $i -ge 0; $i--) {
      if ($s[$i] -eq ' ' -or $s[$i] -eq "`t" -or $s[$i] -eq "`n") { $start = $i + 1; break }
    }
  }
  return $s.Substring($start, $idx - $start)
}

function Get-BashEvents($inp) {
  $cmd = [string]$inp.command
  $ncmd = Norm $cmd
  if ([regex]::IsMatch($cmd, $MEMORY_CAPTURE)) { $script:capture = $true }
  $m = [regex]::Match($cmd, $SET_STAGE)
  if ($m.Success) {
    $rfq = Norm ($m.Groups[1].Value.Trim([char]34, [char]39))
    $d = Get-Dir $rfq
    if ($d -eq '') { $d = 'RFQ' }
    Add-Found ('stage-' + $m.Groups[2].Value) $d
  }
  if ($cmd.Contains('bbs-fill')) {
    $f = [regex]::Match($ncmd, $FILLED_TOKEN)
    if ($f.Success) { Add-Found 'filled' (Get-PrefixBefore $ncmd $f.Index) }
  }
  foreach ($a in [regex]::Matches($cmd, $APPEND_LOG)) {
    $g = $a.Groups[1].Value
    if ($g -eq '') { $g = $a.Groups[2].Value }
    if ($g -eq '') { $g = $a.Groups[3].Value }
    $n = Norm $g
    $ev = Get-LogEvent $n
    if ($ev) { Add-Found $ev (Get-Dir $n) }
  }
}

function New-Marker([string]$path) {
  try {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
    New-Item -ItemType File -Force -Path $path | Out-Null
  } catch { }
}

function Get-LedgerPath([string]$sid) { return (Join-Path (Get-TmpDir) ($sid + '.ledger')) }

function Add-Ledger([string]$sid, [string]$line) {
  try {
    New-Item -ItemType Directory -Force -Path (Get-TmpDir) | Out-Null
    [System.IO.File]::AppendAllText((Get-LedgerPath $sid), $line + "`n", (New-Object System.Text.UTF8Encoding($false)))
  } catch { }
}

function Esc([string]$s) { return $s.Replace('\', '\\').Replace('"', '\"') }

function Invoke-PostTool($h) {
  $inp = $h.tool_input
  if ($null -eq $inp) { return $null }
  $tool = [string]$h.tool_name
  $script:found = New-Object System.Collections.ArrayList
  $script:capture = $false
  if ($tool -eq 'Bash') { Get-BashEvents $inp }
  elseif ($tool -eq 'Write' -or $tool -eq 'Edit' -or $tool -eq 'MultiEdit') { Get-FileEvents $tool $inp }
  else { return $null }
  $sid = Get-Safe ([string]$h.session_id)
  if ($script:capture -and $sid -ne '') { Add-Ledger $sid 'C' }
  $lines = New-Object System.Collections.ArrayList
  foreach ($pair in $script:found) {
    $ev = $pair[0]
    $folder = Norm $pair[1]
    $key = Get-Safe $folder.ToLowerInvariant()
    $name = Get-CleanName (Get-Base $folder)
    if ($sid -ne '') {
      $mk = Join-Path (Get-TmpDir) ($sid + '--' + $ev + '--' + $key)
      if (Test-Path -LiteralPath $mk) { continue }
      New-Marker $mk
      Add-Ledger $sid ("K`t" + $ev + "`t" + $name)
    }
    if ($name -eq '') { $name = 'this folder' }
    [void]$lines.Add(($REMINDER -f $EVENTS[$ev], $name))
  }
  if ($lines.Count -eq 0) { return $null }
  $text = [string]::Join("`n", $lines.ToArray())
  $esc = (Esc $text).Replace("`n", '\n')
  return '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "' + $esc + '"}}'
}

function Test-Pending([string]$sid) {
  try { $text = Read-Text (Get-LedgerPath $sid) } catch { return $false }
  $p = $false
  foreach ($l in [regex]::Split($text, '\r\n|\n|\r')) {
    if ($l.StartsWith("K`t")) { $p = $true }
    elseif ($l -ceq 'C') { $p = $false }
  }
  return $p
}

function Invoke-Stop($h) {
  $sid = Get-Safe ([string]$h.session_id)
  if ($sid -eq '' -or -not (Test-Pending $sid)) { return $null }
  $mk = Join-Path (Get-TmpDir) ($sid + '--stop')
  if (Test-Path -LiteralPath $mk) { return $null }
  $mode = ''
  if ($env:BBS_DESK_LEARN_STOP) { $mode = $env:BBS_DESK_LEARN_STOP.Trim().ToLowerInvariant() }
  if ($mode -eq 'continue') {
    if ($h.stop_hook_active -eq $true) { return $null }
    New-Marker $mk
    return '{"decision": "block", "reason": "' + (Esc $STOP_REASON) + '"}'
  }
  New-Marker $mk
  return '{"systemMessage": "' + (Esc $STOP_MESSAGE) + '"}'
}

try {
  $raw = [Console]::In.ReadToEnd()
  if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
  try { $h = $raw | ConvertFrom-Json } catch { exit 0 }
  if ($null -eq $h -or $h -is [array]) { exit 0 }
  if ([string]$h.hook_event_name -ceq 'Stop') { $out = Invoke-Stop $h } else { $out = Invoke-PostTool $h }
  if ($out) { [Console]::Out.WriteLine($out) }
} catch { }
exit 0
