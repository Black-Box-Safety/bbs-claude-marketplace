# desk-learn: a reminder to close the loop when a key change lands on a customer desk.
#
# The PowerShell half of desk-learn.py (read its header for the events, the once-per-deal-per-event-
# per-session rule, the ledger, the subagent rule, the outcome close-out rule and the Stop backstop).
# Same output on every input, proven by hooks/tests/desk_learn_parity.py; change both or neither
# (invariant 3). Reminds only: exit 0, never a block, never a write to a customer folder, never
# stderr. Fails open on anything unreadable.
#
# The one Stop switch is the environment variable BBS_DESK_LEARN_STOP: unset or "message" shows the
# rep one line; "continue" lets the hook resume the turn once. Default is message-only. The first Stop
# after a key change only arms; a later Stop speaks.
# Temp dir: the first of TMPDIR, TEMP, TMP that is set, else GetTempPath (which on Windows prefers TMP
# over TEMP, unlike Python and the shell entry, so it is not trusted to pick).
# Windows PowerShell 5.1 compatible. ASCII only (5.1 reads a script without a BOM as ANSI).

$ErrorActionPreference = 'Stop'

$TREE = "All RFQ's by Agency"
$SENTINEL = '/bechtel/sentinel/'
$MARKERS = 'bbs-desk-learn'

$EVENTS = @{
  'stage-sent'      = 'RFQ.md written at stage sent'
  'stage-outcome'   = 'RFQ.md written at stage outcome'
  'quote-log'       = 'quote-log row added or Outcome set'
  'filled'          = 'new file in FILLED/'
  'award'           = 'PO, award or NOA file written'
  'sentinel-log'    = 'Sentinel quote-log appended'
  'sentinel-banner' = 'RFP status banner edited'
}
$REMINDER = 'Key change: {0} in {1}. Close the loop: ask the rep one question. Anything about this buyer or site worth remembering, or a lesson from this deal? If they give words, run `desk-remember` with their own words. If they offer a lesson, show the one-line draft and append it to `learning/lessons.md` only on their yes (if the desk has no `lessons.md`, say so and write nothing). If they say nothing, run `desk_memory.py close --none`.'
$STOP_REASON = 'Key changes were made this session and nothing was captured or closed. Ask the rep one question, once: anything about this buyer or site worth remembering, or a lesson from this deal? If they give words, run `desk-remember` with their own words. If they offer a lesson, show the one-line draft and append it to `learning/lessons.md` only on their yes (if the desk has no `lessons.md`, say so and write nothing). If they say nothing, run `desk_memory.py close --none`. Do not ask again.'
$STOP_MESSAGE = 'bbs-sales: key changes were made this session and nothing was saved for next time. Tell Claude what to remember, or say there is nothing to remember, before you close.'

$STAGE_RE = '(?m)^\*\*Stage:\*\*[ \t]*(.+?)[ \t]*\r?$'
$DATA_ROW = '(?m)^\|[ \t]*(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./][0-9]{1,2}[./](?:[0-9]{2}|[0-9]{4}))[ \t]*\|'
$BANNER = '(?m)^(?:>[ \t]*)?\*\*Status'
$AWARD = '(?i)(?:^|[^A-Za-z])(?:PO|NOA|award|purchase[ _-]?order|notice[ _-]of[ _-]award)(?:[^A-Za-z]|$)'
$SET_STAGE = @'
rfq_record\.py["']?\s+set-stage\s+("[^"]*"|'[^']*'|\S+)\s+["']?(sent|outcome)["']?(?=\s|$)
'@
$MEMORY_CAPTURE = @'
desk_memory\.py["']?\s+(?:add|close)(?=\s|$)
'@
$APPEND_LOG = @'
(?:>>|\btee[ \t]+-a)[ \t]*(?:"([^"\n]*?quote-log\.md)"|'([^'\n]*?quote-log\.md)'|([^\s"';&|]*quote-log\.md))
'@
$FILLED_TOKEN = '(?i)/FILLED/'
$CLOSEOUT = '(?i)\bper BC\b|\bno order in BC\b|\[FLAG'
$ABSOLUTE = '^(?:/|[A-Za-z]:/|~)'

function Norm([string]$p) { return $p.Replace('\', '/') }

function Get-Resolved([string]$n, [string]$cwd) {
  if ($n -eq '' -or $cwd -eq '' -or [regex]::IsMatch($n, $ABSOLUTE)) { return $n }
  return ($cwd.TrimEnd('/') + '/' + [regex]::Replace($n, '^\./', ''))
}

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

function Get-TmpDir {
  foreach ($v in 'TMPDIR', 'TEMP', 'TMP') {
    $x = [Environment]::GetEnvironmentVariable($v)
    if ($x) { return (Join-Path $x $MARKERS) }
  }
  return (Join-Path ([System.IO.Path]::GetTempPath()) $MARKERS)
}

function Read-Text([string]$path) {
  $b = [System.IO.File]::ReadAllBytes($path)
  $skip = 0
  if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { $skip = 3 }
  return [System.Text.Encoding]::UTF8.GetString($b, $skip, $b.Length - $skip)
}

function Get-StageOf([string]$text) {
  $m = [regex]::Match($text, $STAGE_RE)
  if ($m.Success) { return $m.Groups[1].Value.Trim().ToLowerInvariant() }
  return $null
}

function Get-StagePath([string]$folder) { return (Join-Path (Get-TmpDir) ('stage--' + (Get-Safe $folder.ToLowerInvariant()))) }

function Get-LastStage([string]$folder) {
  try { return (Read-Text (Get-StagePath $folder)).Trim() } catch { return $null }
}

function Set-LastStage([string]$folder, [string]$st) {
  try {
    New-Item -ItemType Directory -Force -Path (Get-TmpDir) | Out-Null
    [System.IO.File]::WriteAllText((Get-StagePath $folder), $st, (New-Object System.Text.UTF8Encoding($false)))
  } catch { }
}

function Get-Pairs([string]$tool, $inp) {
  $out = New-Object System.Collections.ArrayList
  if ($tool -eq 'Edit') { [void]$out.Add(@([string]$inp.old_string, [string]$inp.new_string)) }
  elseif ($tool -eq 'MultiEdit') {
    if ($null -ne $inp.edits) {
      foreach ($e in @($inp.edits)) { if ($null -ne $e) { [void]$out.Add(@([string]$e.old_string, [string]$e.new_string)) } }
    }
  }
  return ,$out
}

function Get-NewTexts([string]$tool, $inp) {
  $out = New-Object System.Collections.ArrayList
  if ($tool -eq 'Write') { [void]$out.Add([string]$inp.content) }
  else { foreach ($p in (Get-Pairs $tool $inp)) { [void]$out.Add([string]$p[1]) } }
  return ,$out
}

function Get-StageMoved([string]$tool, $inp, [string]$folder) {
  $moved = $null
  if ($tool -eq 'Write') {
    $ns = Get-StageOf ([string]$inp.content)
    if ($ns) {
      if (($ns -eq 'sent' -or $ns -eq 'outcome') -and $ns -ne (Get-LastStage $folder)) { $moved = $ns }
      Set-LastStage $folder $ns
    }
    return $moved
  }
  foreach ($p in (Get-Pairs $tool $inp)) {
    $ns = Get-StageOf ([string]$p[1])
    if ($ns) {
      if (($ns -eq 'sent' -or $ns -eq 'outcome') -and $ns -ne (Get-StageOf ([string]$p[0]))) { $moved = $ns }
      Set-LastStage $folder $ns
    }
  }
  return $moved
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
    $folder = Get-FolderOf $n
    $st = Get-StageMoved $tool $inp $folder
    if ($st) { Add-Found ('stage-' + $st) $folder }
  }
  elseif ($base -ceq 'quote-log.md') {
    $ev = Get-LogEvent $n
    if ($ev -and (Test-AnyMatch $texts $DATA_ROW)) {
      if (Test-AnyMatch $texts $CLOSEOUT) { Add-Found 'closeout' (Get-FolderOf $n) }
      else { Add-Found $ev (Get-FolderOf $n) }
    }
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

function Get-BashEvents($inp, [string]$cwd) {
  $cmd = [string]$inp.command
  $ncmd = Norm $cmd
  if ([regex]::IsMatch($cmd, $MEMORY_CAPTURE)) { $script:capture = $true }
  $m = [regex]::Match($cmd, $SET_STAGE)
  if ($m.Success) {
    $rfq = Get-Resolved (Norm ($m.Groups[1].Value.Trim([char]34, [char]39))) $cwd
    $d = Get-Dir $rfq
    if ($d -eq '') { $d = 'RFQ' }
    Set-LastStage $d $m.Groups[2].Value
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
    $n = Get-Resolved (Norm $g) $cwd
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
  $cwd = Norm ([string]$h.cwd)
  $script:found = New-Object System.Collections.ArrayList
  $script:capture = $false
  if ($tool -eq 'Bash') { Get-BashEvents $inp $cwd }
  elseif ($tool -eq 'Write' -or $tool -eq 'Edit' -or $tool -eq 'MultiEdit') { Get-FileEvents $tool $inp }
  else { return $null }
  $sid = Get-Safe ([string]$h.session_id)
  if ($script:capture -and $sid -ne '') { Add-Ledger $sid 'C' }
  $subagent = $false
  if ($h.agent_id) { $subagent = $true }
  $new = New-Object System.Collections.ArrayList
  foreach ($pair in $script:found) {
    $ev = $pair[0]
    $folder = Norm $pair[1]
    if ($ev -eq 'closeout') {
      if ($sid -ne '') { Add-Ledger $sid "Q`tquote-log" }
      continue
    }
    if ($subagent) {
      if ($sid -ne '') { Add-Ledger $sid ("K`t" + $ev) }
      continue
    }
    if ($sid -ne '') {
      $mk = Join-Path (Get-TmpDir) ($sid + '--' + $ev + '--' + (Get-Safe $folder.ToLowerInvariant()))
      if (Test-Path -LiteralPath $mk) { continue }
      New-Marker $mk
      Add-Ledger $sid ("K`t" + $ev)
    }
    [void]$new.Add(@($ev, $folder))
  }
  if ($new.Count -eq 0) { return $null }
  if ($new.Count -eq 1) {
    $name = Get-CleanName (Get-Base $new[0][1])
    if ($name -eq '') { $name = 'this folder' }
    $text = ($REMINDER -f $EVENTS[$new[0][0]], $name)
  } else {
    $evs = New-Object System.Collections.ArrayList
    foreach ($p in $new) { if (-not $evs.Contains($EVENTS[$p[0]])) { [void]$evs.Add($EVENTS[$p[0]]) } }
    $text = ($REMINDER -f ([string]::Join('; ', $evs.ToArray())), ([string]$new.Count + ' folders'))
  }
  return '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "' + (Esc $text) + '"}}'
}

function Get-LedgerState([string]$sid) {
  $p = $false
  $a = $false
  try { $text = Read-Text (Get-LedgerPath $sid) } catch { return @($false, $false) }
  foreach ($l in [regex]::Split($text, '\r\n|\n|\r')) {
    if ($l.StartsWith("K`t")) { $p = $true; $a = $false }
    elseif ($l -ceq 'C') { $p = $false; $a = $false }
    elseif ($l -ceq 'S' -and $p) { $a = $true }
  }
  return @($p, $a)
}

function Invoke-Stop($h) {
  $sid = Get-Safe ([string]$h.session_id)
  if ($sid -eq '') { return $null }
  $st = Get-LedgerState $sid
  if (-not $st[0]) { return $null }
  if (-not $st[1]) { Add-Ledger $sid 'S'; return $null }
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
