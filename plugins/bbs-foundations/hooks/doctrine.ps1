# PreToolUse hook, matcher "Skill": inject BBS doctrine before a subscribed skill runs.
#
# Reads the hook JSON on stdin. If tool_input.skill matches a pattern in
# doctrine/subscriptions.json (beside this script), prints
#   {"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"<doctrine>"}}
# with every matched insert's file, verbatim, joined by a blank line. Otherwise prints
# nothing. Always exit 0: a hook error must never block a skill. Never writes a file.
#
# Written to the Windows PowerShell 5.1 subset so the same file runs under powershell.exe
# on a rep machine and under pwsh 7 on a Mac. The doctrine files are the truth; this
# script re-keys nothing. Subscriptions: doctrine/subscriptions.json.

trap { exit 0 }
$ErrorActionPreference = 'Stop'

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
$h = $raw | ConvertFrom-Json
if ($h.tool_name -ne 'Skill') { exit 0 }
$skill = $h.tool_input.skill
if (-not ($skill -is [string]) -or [string]::IsNullOrWhiteSpace($skill)) { exit 0 }

$dir   = Join-Path $PSScriptRoot 'doctrine'
$table = Get-Content -LiteralPath (Join-Path $dir 'subscriptions.json') -Raw -Encoding UTF8 | ConvertFrom-Json

# Only * is a wildcard in a subscription pattern; neutralise the other -like metacharacters.
function Matches([string]$name, [string]$pattern) {
  $p = $pattern -replace '\[', '`[' -replace '\]', '`]' -replace '\?', '`?'
  return ($name -like $p)
}

$matched = New-Object System.Collections.Generic.List[string]
foreach ($sub in @($table.subscriptions)) {
  if (-not $sub.insert -or -not $sub.on) { continue }
  if ($matched.Contains([string]$sub.insert)) { continue }
  if (Matches $skill ([string]$sub.on)) { $matched.Add([string]$sub.insert) }
}
if ($matched.Count -eq 0) { exit 0 }

$parts = New-Object System.Collections.Generic.List[string]
foreach ($name in $matched) {
  $ins = $table.inserts.$name
  if (-not $ins -or -not $ins.file) { continue }
  $path = Join-Path $dir ([string]$ins.file)
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  if ($null -eq $text) { continue }
  # An autocrlf checkout would otherwise inject \r; the file's own bytes are LF.
  $parts.Add(($text -replace "`r`n", "`n"))
}
if ($parts.Count -eq 0) { exit 0 }
$context = $parts -join "`n`n"

# JSON string literal with every non-ASCII character escaped, so the bytes on stdout are
# the same under 5.1's OEM console code page and pwsh's UTF-8.
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
    elseif ($code -lt 0x20 -or $code -gt 0x7E) { [void]$sb.Append(('\u{0:x4}' -f $code)) }
    else { [void]$sb.Append($ch) }
  }
  [void]$sb.Append('"')
  return $sb.ToString()
}

$out = '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":' + (JsonString $context) + '}}'
[Console]::Out.Write($out)
exit 0
