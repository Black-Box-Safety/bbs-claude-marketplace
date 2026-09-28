# Inject BBS doctrine before a subscribed skill runs. Two events, one table:
#   PreToolUse (matcher "Skill")   — Claude called the Skill tool; tool_input.skill is the name.
#   UserPromptExpansion            — the user typed /name; command_name is the name, usually
#                                    bare ("bbs-checkup", command_source "plugin"), sometimes
#                                    prefixed ("bbs-foundations:bbs-checkup").
#
# Reads the hook JSON on stdin. If the name matches a pattern in doctrine/subscriptions.json
# (beside this script), prints
#   {"hookSpecificOutput":{"hookEventName":"<event>","additionalContext":"<doctrine>"}}
# with every matched insert's file, verbatim, joined by a blank line. Otherwise prints
# nothing. Always exit 0: a hook error must never block a skill. Never writes a file.
#
# Written to the Windows PowerShell 5.1 subset so the same file runs under powershell.exe
# on a rep machine and under pwsh 7 on a Mac. doctrine.py is the same logic for a machine
# with python3 and no PowerShell; the two must agree byte for byte (tests/parity.py).
# The doctrine files are the truth; this script re-keys nothing.

trap { exit 0 }
$ErrorActionPreference = 'Stop'

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
$raw = $raw.TrimStart([char]0xFEFF)
$h = $raw | ConvertFrom-Json

$event = [string]$h.hook_event_name
if (-not $event) { if ($h.tool_name -eq 'Skill') { $event = 'PreToolUse' } else { exit 0 } }

if ($event -eq 'PreToolUse') {
  if ($h.tool_name -ne 'Skill') { exit 0 }
  $name = $null
  if ($null -ne $h.tool_input) { $name = $h.tool_input.skill }
} elseif ($event -eq 'UserPromptExpansion') {
  if ([string]$h.expansion_type -eq 'mcp_prompt') { exit 0 }   # an MCP server's prompt is not a skill
  $name = $h.command_name
} else { exit 0 }
if (-not ($name -is [string]) -or [string]::IsNullOrWhiteSpace($name)) { exit 0 }

$dir   = Join-Path $PSScriptRoot 'doctrine'
$table = Get-Content -LiteralPath (Join-Path $dir 'subscriptions.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$subs  = @($table.subscriptions)

# Only * is a wildcard in a subscription pattern; neutralise the other -like metacharacters.
function Matches([string]$n, [string]$pattern) {
  $p = $pattern -replace '\[', '`[' -replace '\]', '`]' -replace '\?', '`?'
  return ($n -like $p)
}

# A name with a colon (every tool call; a typed /plugin:name) matches the whole pattern.
# A bare typed name does not say which plugin it came from, and the retired injection
# plugin's rule for it is kept verbatim: a bare pattern matches as is; a plugin:suffix
# pattern matches the name against its suffix; a plugin:* (or plugin:**) pattern is
# skipped, because a bare name cannot claim a whole plugin. So a typed /bbs-checkup gets
# nothing and a typed /bbs-claude-md-forge gets the CLAUDE.md doctrine only.
$isBare = ($event -eq 'UserPromptExpansion' -and $name -notlike '*:*')
function SubMatches([string]$n, [string]$pattern, [bool]$bare) {
  if (-not $bare) { return (Matches $n $pattern) }
  $i = $pattern.IndexOf(':')
  if ($i -lt 0) { return (Matches $n $pattern) }
  $suffix = $pattern.Substring($i + 1)
  if ($suffix -eq '*' -or $suffix -eq '**') { return $false }
  return (Matches $n $suffix)
}

$matched = New-Object System.Collections.Generic.List[string]
foreach ($sub in $subs) {
  if (-not $sub.insert -or -not $sub.on) { continue }
  if ($matched.Contains([string]$sub.insert)) { continue }
  if (SubMatches $name ([string]$sub.on) $isBare) { $matched.Add([string]$sub.insert) }
}
if ($matched.Count -eq 0) { exit 0 }

$parts = New-Object System.Collections.Generic.List[string]
foreach ($ins in $matched) {
  $spec = $table.inserts.$ins
  if (-not $spec -or -not $spec.file) { continue }
  $path = Join-Path $dir ([string]$spec.file)
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  if ($null -eq $text) { continue }
  # An autocrlf checkout would otherwise inject \r; the file's own bytes are LF.
  $parts.Add(($text -replace "`r`n", "`n"))
}
if ($parts.Count -eq 0) { exit 0 }
$context = $parts -join "`n`n"

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
