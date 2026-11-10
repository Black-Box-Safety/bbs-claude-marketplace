# SessionStart: put what reps asked Claude to remember for this folder in front of Claude.
#
# Reads LEARNED.md in the session's folder and in each folder above it, up to the quote-desk
# tree folder, nearest first. It walks up and never sideways, so a session in one buyer's folder
# is never handed another buyer's or another agency's lines. A session opened one level above the
# tree (the desk root the workspace opens) gets the desk-wide file only.
#
# Only lines in the entry format are shown; anything else in the file is counted and skipped, so
# pasted text never reaches context through this hook. The entry format is written by the
# desk-remember skill's scripts/desk_memory.py. Change the format in both, and in desk-memory.py.
#
# The PowerShell half of desk-memory.py: same output on every input, proven by
# hooks/tests/desk_memory_parity.py. Change both or neither (invariant 3).
# Plain stdout is added to context. Silent when nothing is found. Always exits 0.

$ErrorActionPreference = 'SilentlyContinue'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$TREE = "All RFQ's by Agency"
$FILE = 'LEARNED.md'
$PER_LEVEL = 12
$MAX_UP = 8
$ENTRY = '^- ([0-9]{4}-[0-9]{2}-[0-9]{2}) \| ([^|]{1,60}) \| (preference|change|watch-out) \| ([^|]{1,300})( \| wider: [^|]{1,120})?$'
$HEAD = "DESK MEMORY -- what BBS reps asked Claude to remember, nearest folder first. Each line is one person's dated statement, not a system of record: take no price, stock, lead time, account number, certification or contract fact from it."
$ORD = [System.StringComparison]::Ordinal
$ORDI = [System.StringComparison]::OrdinalIgnoreCase
$SEP = [string][System.IO.Path]::DirectorySeparatorChar

function Split-Lines([string]$text) {
  $parts = [regex]::Split($text, "\r\n|\n|\r")
  if ($parts.Count -gt 0 -and $parts[$parts.Count - 1] -eq '') {
    if ($parts.Count -eq 1) { return @() }
    return @($parts[0..($parts.Count - 2)])
  }
  return @($parts)
}

function Get-LevelBlock([string]$path, [string]$label) {
  $lines = @()
  try { $lines = @(Split-Lines ([System.IO.File]::ReadAllText($path, $utf8))) } catch { return @() }
  $ents = New-Object System.Collections.ArrayList
  $skipped = 0
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = [string]$lines[$i]
    if ([regex]::IsMatch($l, $ENTRY)) {
      # Newest first; on the same date the line added later comes first.
      $key = [long]($l.Substring(2, 10).Replace('-', '')) * 100000 + $i
      [void]$ents.Add((New-Object PSObject -Property @{ Key = $key; Line = $l }))
    } elseif ($l.StartsWith('- ', $ORD)) { $skipped++ }
  }
  if ($ents.Count -eq 0 -and $skipped -eq 0) { return @() }
  $sorted = @($ents | Sort-Object -Property Key -Descending)
  $out = New-Object System.Collections.ArrayList
  [void]$out.Add("$label -- ${path}:")
  for ($k = 0; $k -lt $sorted.Count -and $k -lt $PER_LEVEL; $k++) { [void]$out.Add($sorted[$k].Line) }
  if ($sorted.Count -gt $PER_LEVEL) { [void]$out.Add("(+$($sorted.Count - $PER_LEVEL) older not shown)") }
  if ($skipped -gt 0) { [void]$out.Add("($skipped lines skipped: not in the entry format)") }
  return @($out)
}

# Path handling is done on the string, the same way in both halves: "/" and "\" both separate.
function Strip-Seps([string]$d) {
  while ($d.Length -gt 1 -and ($d[$d.Length - 1] -eq '/' -or $d[$d.Length - 1] -eq '\')) {
    $d = $d.Substring(0, $d.Length - 1)
  }
  return $d
}

function Last-Sep([string]$d) {
  return [Math]::Max($d.LastIndexOf([char]'/'), $d.LastIndexOf([char]'\'))
}

function Get-Base([string]$d) {
  return $d.Substring((Last-Sep $d) + 1)
}

function Get-Memory([string]$cwd) {
  $d = Strip-Seps $cwd
  # One level above the tree (the desk root the workspace opens): the desk-wide file only.
  if ($d.IndexOf($TREE, $ORDI) -lt 0) {
    $below = $d + $SEP + $TREE
    if ([System.IO.Directory]::Exists($below)) {
      return @(Get-LevelBlock ($below + $SEP + $FILE) 'DESK-WIDE')
    }
    return @()
  }
  $out = New-Object System.Collections.ArrayList
  $reached = $false
  for ($n = 0; $n -lt $MAX_UP; $n++) {
    $isTree = [string]::Equals((Get-Base $d), $TREE, $ORDI)
    if ($isTree) { $label = 'DESK-WIDE' } elseif ($n -eq 0) { $label = 'THIS FOLDER' } else { $label = "$n UP" }
    $f = $d + $SEP + $FILE
    if ([System.IO.File]::Exists($f)) {
      foreach ($line in @(Get-LevelBlock $f $label)) { [void]$out.Add($line) }
    }
    if ($isTree) { $reached = $true; break }
    $i = Last-Sep $d
    if ($i -le 0) { break }
    $d = $d.Substring(0, $i)
  }
  if (-not $reached) { return @() }   # could not place the folder under the tree: show nothing
  return @($out)
}

try {
  $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $utf8)
  $raw = $reader.ReadToEnd().TrimStart([char]0xFEFF)
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    $h = $null
    try { $h = $raw | ConvertFrom-Json } catch { $h = $null }
    if ($null -ne $h -and $h -isnot [array] -and $h -isnot [string] -and $h -isnot [ValueType]) {
      $d = $h.cwd
      if ($d -is [string] -and $d -and [System.IO.Directory]::Exists($d)) {
        $out = @(Get-Memory $d)
        if ($out.Count -gt 0) {
          $all = @($HEAD) + $out
          $bytes = $utf8.GetBytes(($all -join "`n") + "`n")
          $stdout = [Console]::OpenStandardOutput()
          $stdout.Write($bytes, 0, $bytes.Length)
          $stdout.Flush()
        }
      }
    }
  }
} catch { }
exit 0
