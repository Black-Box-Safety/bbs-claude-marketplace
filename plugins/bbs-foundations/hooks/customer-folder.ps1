# Remind a session working in a customer folder to keep that customer's CLAUDE.md. Two events:
#   SessionStart  — cwd is the place. Inside MASTER/Customers/<customer>/: no CLAUDE.md between
#                   cwd and the customer root -> customer-folder/missing.md; one there ->
#                   customer-folder/present.md naming the nearest.
#   PostToolUse   — tool_input.file_path (or notebook_path) is the place. Missing only, and once
#                   per customer per session: a marker in the temp dir keyed on session_id stops
#                   it repeating on every write. SessionStart always speaks, so a compacted
#                   session hears it again.
#
# A customer folder is a child of a folder named Customers whose parent's name ends in
# "Black Box Safety - MASTER" (the Mac and Windows OneDrive shapes both do). Two are not this
# hook's: State of CA Agencies is the bbs-sales quote desk, whose learning lives in buyer-level
# CLAUDE.md, quote-log.md and FLAGS.md (ca-rfq-intake), and a folder named "DO NOT USE ..." is a
# dead tree. Both stay silent. Prints
#   {"hookSpecificOutput":{"hookEventName":"<event>","additionalContext":"<text>"}}
# or nothing. Always exit 0: a hook error must never block a tool.
#
# Written to the Windows PowerShell 5.1 subset, like doctrine.ps1. customer-folder.py is the
# same logic for a machine with python3 and no PowerShell; the two must agree byte for byte
# (tests/customer_folder_parity.py). The texts live in customer-folder/*.md; this script
# re-keys nothing. Paths go through System.IO, not the provider, so [ ] in a folder name is
# a character, not a wildcard.

trap { exit 0 }
$ErrorActionPreference = 'Stop'

try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false } catch { }
$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
$raw = $raw.TrimStart([char]0xFEFF)
$h = $raw | ConvertFrom-Json

$event = [string]$h.hook_event_name
$start = $null
if ($event -eq 'SessionStart') {
  $start = $h.cwd
} elseif ($event -eq 'PostToolUse') {
  $ti = $h.tool_input
  if ($null -ne $ti -and $ti -isnot [string]) {
    $start = $ti.file_path
    if (-not $start) { $start = $ti.notebook_path }
  }
} else { exit 0 }
if (-not ($start -is [string]) -or [string]::IsNullOrWhiteSpace($start)) { exit 0 }

$MasterSuffix = 'black box safety - master'
$NotOurs = 'state of ca agencies'
$DeadPrefix = 'do not use'

# The Customers/<customer> folder at or above $s, or $null.
function CustomerRoot([string]$s) {
  $p = $s.TrimEnd('/', '\')
  if ($p -eq '') { $p = $s }
  for ($i = 0; $i -lt 64; $i++) {
    $parent = [System.IO.Path]::GetDirectoryName($p)
    if (-not $parent -or $parent -ceq $p) { return $null }
    $up = [System.IO.Path]::GetDirectoryName($parent)
    $upName = ''
    if ($up) { $upName = [System.IO.Path]::GetFileName($up) }
    if ([System.IO.Path]::GetFileName($parent).ToLowerInvariant() -ceq 'customers' -and
        $upName.ToLowerInvariant().EndsWith($MasterSuffix, [StringComparison]::Ordinal)) {
      $name = [System.IO.Path]::GetFileName($p)
      $low = $name.ToLowerInvariant()
      # Hidden, the CA quote desk, or a dead tree.
      if ($name.StartsWith('.', [StringComparison]::Ordinal) -or $low -ceq $NotOurs -or
          $low.StartsWith($DeadPrefix, [StringComparison]::Ordinal)) { return $null }
      # A file sitting in Customers/.
      if (-not [System.IO.Directory]::Exists($p)) { return $null }
      return $p
    }
    $p = $parent
  }
  return $null
}

# The CLAUDE.md closest to $s, looking up as far as $root, or $null.
function NearestClaudeMd([string]$s, [string]$root) {
  $d = $s
  if (-not [System.IO.Directory]::Exists($s)) { $d = [System.IO.Path]::GetDirectoryName($s) }
  for ($i = 0; $i -lt 64; $i++) {
    if (-not $d) { return $null }
    $f = [System.IO.Path]::Combine($d, 'CLAUDE.md')
    if ([System.IO.File]::Exists($f)) { return $f }
    if ($d -ceq $root) { return $null }
    $parent = [System.IO.Path]::GetDirectoryName($d)
    if (-not $parent -or $parent -ceq $d) { return $null }
    $d = $parent
  }
  return $null
}

function Text([string]$fname, [string]$name, [string]$target) {
  $path = [System.IO.Path]::Combine((Join-Path $PSScriptRoot 'customer-folder'), $fname)
  $t = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
  $t = $t.TrimStart([char]0xFEFF)
  $t = ($t -replace "`r`n", "`n").TrimEnd([char]10)
  $t = $t.Replace('{name}', $name)
  $t = $t.Replace('{target}', $target)
  return $t
}

function Safe([string]$s) { return ($s -creplace '[^A-Za-z0-9]+', '-') }

$root = CustomerRoot $start
if (-not $root) { exit 0 }
$found = NearestClaudeMd $start $root
$name = [System.IO.Path]::GetFileName($root)

$sid = $h.session_id
$marker = $null
if ($sid -is [string] -and -not [string]::IsNullOrWhiteSpace($sid)) {
  $marker = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), 'bbs-customer-folder', ((Safe $sid) + '--' + (Safe $name)))
}

if ($found) {
  if ($event -ne 'SessionStart') { exit 0 }
  $context = Text 'present.md' $name $found
} else {
  if ($event -eq 'PostToolUse' -and $marker -and [System.IO.File]::Exists($marker)) { exit 0 }
  $context = Text 'missing.md' $name ([System.IO.Path]::Combine($root, 'CLAUDE.md'))
  if ($marker) {
    # No marker: the reminder repeats, it never blocks.
    try {
      [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($marker))
      [System.IO.File]::WriteAllText($marker, '')
    } catch { }
  }
}

# JSON string literal in exactly the form Python's json.dumps(ensure_ascii=True) emits, so
# the bytes on stdout are the same from either script and under 5.1's OEM console page.
function JsonString([string]$s) {
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append('"')
  foreach ($ch in $s.ToCharArray()) {
    $code = [int]$ch
    if ($ch -eq '"')      { [void]$sb.Append('\"') }
    elseif ($ch -eq '\')  { [void]$sb.Append('\\') }
    elseif ($ch -eq "`n") { [void]$sb.Append('\n') }
    elseif ($ch -eq "`r") { [void]$sb.Append('\r') }
    elseif ($ch -eq "`t") { [void]$sb.Append('\t') }
    elseif ($ch -eq "`b") { [void]$sb.Append('\b') }
    elseif ($ch -eq "`f") { [void]$sb.Append('\f') }
    elseif ($code -lt 0x20 -or $code -gt 0x7F) { [void]$sb.Append(('\u{0:x4}' -f $code)) }
    else { [void]$sb.Append($ch) }
  }
  [void]$sb.Append('"')
  return $sb.ToString()
}

$out = '{"hookSpecificOutput":{"hookEventName":"' + $event + '","additionalContext":' + (JsonString $context) + '}}'
[Console]::Out.Write($out)
exit 0
