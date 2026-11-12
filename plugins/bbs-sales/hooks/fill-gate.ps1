# PreToolUse gate for the bbs-fill launcher (Bash). The PowerShell half of fill-gate.py.
#
# Prints an "allow" decision only when the whole Bash command is exactly one invocation of this
# plugin's own launcher, "<root>/scripts/bbs-fill", on a script that is on the launcher's ALLOWED
# list, "<root>/skills/<entry>". Otherwise it prints nothing, which leaves the call to the normal
# permission flow. It never denies and never asks.
#
# Spec: docs/superpowers/specs/2026-11-11-bbs-fill-into-bbs-sales.md, section 3 (RULED 2026-11-11).
# Both halves must decide identically on every input (hooks/tests/fill_gate_parity.py); change
# both or neither. Grammar and rules: see fill-gate.py's header. The lexer works on code points
# (surrogate pairs decoded; a lone surrogate rejects), never on UTF-16 units, and uses no Unicode
# category tables. Runs on Windows PowerShell 5.1 and pwsh 7. ASCII-only source.

$ErrorActionPreference = 'Stop'
$REASON = 'bbs-fill: vetted script '
$ENTRY  = '^"([a-z0-9-]+/scripts/[A-Za-z0-9_.-]+\.(?:py|js))"$'
$UNQUOTED = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./:,=+@%-'

# Opt-in trace for the parity test (BBS_FILL_GATE_DEBUG=1): why a command got no decision.
# Off by default, so a normal run writes nothing to stderr.
function Write-Why([string]$why) {
  if ($env:BBS_FILL_GATE_DEBUG -eq '1') { [Console]::Error.WriteLine('fill-gate: ' + $why) }
  return $null
}

function Test-Bad([int]$cp) {
  return ($cp -lt 0x20) -or ($cp -ge 0x7F -and $cp -le 0x9F) -or ($cp -eq 0x2028) -or ($cp -eq 0x2029) -or ($cp -ge 0xD800 -and $cp -le 0xDFFF)
}

function Get-CodePoints([string]$s) {
  $list = New-Object System.Collections.Generic.List[int]
  $i = 0
  while ($i -lt $s.Length) {
    $c = $s[$i]
    if ([char]::IsHighSurrogate($c) -and ($i + 1) -lt $s.Length -and [char]::IsLowSurrogate($s[$i + 1])) {
      $list.Add([char]::ConvertToUtf32($c, $s[$i + 1])); $i += 2
    } else {
      $list.Add([int]$c); $i += 1   # a lone surrogate stays a surrogate code point; Test-Bad rejects it
    }
  }
  return ,$list.ToArray()
}

function Get-Text([int[]]$cps, [int]$from, [int]$to) {
  $sb = New-Object System.Text.StringBuilder
  for ($k = $from; $k -lt $to; $k++) { [void]$sb.Append([char]::ConvertFromUtf32($cps[$k])) }
  return $sb.ToString()
}

function Get-Words([string]$cmd) {
  $cps = Get-CodePoints $cmd
  $n = $cps.Length
  $words = New-Object System.Collections.Generic.List[string]
  $cur = $null
  $i = 0
  while ($i -lt $n) {
    $cp = $cps[$i]
    if (Test-Bad $cp) { return $null }
    if ($cp -eq 0x20) {
      if ($null -ne $cur) { $words.Add($cur); $cur = $null }
      $i += 1
    } elseif ($cp -eq 0x27) {
      $j = $i + 1
      while ($j -lt $n -and $cps[$j] -ne 0x27) {
        if (Test-Bad $cps[$j]) { return $null }
        $j += 1
      }
      if ($j -ge $n) { return $null }
      $cur = [string]$cur + (Get-Text $cps ($i + 1) $j)
      $i = $j + 1
    } elseif ($cp -eq 0x22) {
      $j = $i + 1
      while ($true) {
        if ($j -ge $n) { return $null }
        $d = $cps[$j]
        if ($d -eq 0x22) { break }
        if ((Test-Bad $d) -or $d -eq 0x24 -or $d -eq 0x60 -or $d -eq 0x21) { return $null }
        if ($d -eq 0x5C -and ($j + 1) -lt $n) {
          $e = $cps[$j + 1]
          if ($e -eq 0x24 -or $e -eq 0x60 -or $e -eq 0x22 -or $e -eq 0x5C) { return $null }
        }
        $j += 1
      }
      $cur = [string]$cur + (Get-Text $cps ($i + 1) $j)
      $i = $j + 1
    } elseif ($cp -lt 0x80 -and $UNQUOTED.IndexOf([char]$cp) -ge 0) {
      if ($cp -eq 0x3D -and $null -eq $cur) { return $null }
      $cur = [string]$cur + [string][char]$cp
      $i += 1
    } else {
      return $null
    }
  }
  if ($null -ne $cur) { $words.Add($cur) }
  if ($words.Count -eq 0) { return $null }
  return ,$words.ToArray()
}

function Get-Canon([string]$path) {
  $p = $path.Replace('\', '/')
  if ($p -cmatch '^([A-Za-z]):/') { $p = '/' + $Matches[1].ToLowerInvariant() + $p.Substring(2) }
  $p = [regex]::Replace($p, '/+', '/')
  if ($p.Length -gt 1 -and $p.EndsWith('/')) { $p = $p.Substring(0, $p.Length - 1) }
  foreach ($seg in $p.Split('/')) { if ($seg -ceq '.' -or $seg -ceq '..') { return $null } }
  return $p
}

function Get-Allowed([string]$launcher) {
  try { $text = [IO.File]::ReadAllText($launcher, (New-Object System.Text.UTF8Encoding($false, $true))) }
  catch { return (Write-Why ('allowed: cannot read ' + $launcher + ': ' + $_.Exception.Message)) }
  if ($text.IndexOf([char]13) -ge 0) { return (Write-Why 'allowed: the launcher has a CR') }
  $lines = $text -split "`n"
  $start = -1
  for ($k = 0; $k -lt $lines.Count; $k++) { if ($lines[$k].Trim() -ceq 'ALLOWED=(') { $start = $k; break } }
  if ($start -lt 0) { return (Write-Why 'allowed: no ALLOWED=( line') }
  $out = New-Object System.Collections.Generic.List[string]
  for ($k = $start + 1; $k -lt $lines.Count; $k++) {
    $s = $lines[$k].Trim()
    if ($s -ceq ')') {
      if ($out.Count -gt 0) { return ,$out.ToArray() }
      return (Write-Why 'allowed: empty list')
    }
    if ($s.Length -eq 0) { continue }
    if ($s -cnotmatch $ENTRY) { return (Write-Why ('allowed: malformed entry ' + $s)) }
    $out.Add($Matches[1])
  }
  return (Write-Why 'allowed: no closing )')
}

function Test-Link([string]$p) {
  # A missing path is not a link here; the existence checks in Get-Decision refuse it.
  if (-not (Test-Path -LiteralPath $p)) { return $false }
  $item = Get-Item -LiteralPath $p -Force
  # Compare as a number: PowerShell's [bool] of a FileAttributes value is not a zero test.
  return ((([int]$item.Attributes) -band 0x400) -ne 0)
}

function Test-AnyLink([string]$root, [string[]]$parts) {
  $p = $root
  if (Test-Link $p) { return $true }
  foreach ($part in $parts) {
    $p = [IO.Path]::Combine($p, $part)
    if (Test-Link $p) { return $true }
  }
  return $false
}

function Get-Decision($h) {
  if ($null -eq $h -or $h.tool_name -cne 'Bash') { return (Write-Why 'step 1') }
  $ti = $h.tool_input
  if ($null -eq $ti) { return (Write-Why 'step 2') }
  $cmd = $ti.command
  if ($cmd -isnot [string]) { return (Write-Why 'step 3') }
  $dds = $ti.dangerouslyDisableSandbox
  if ($null -ne $dds -and -not ($dds -is [bool] -and $dds -eq $false)) { return (Write-Why 'step 4') }
  $rootEnv = $env:CLAUDE_PLUGIN_ROOT
  if ([string]::IsNullOrEmpty($rootEnv)) { return (Write-Why 'step 5') }
  $rootNative = $rootEnv.TrimEnd('/', '\')
  if ($rootNative.Length -eq 0) { $rootNative = $rootEnv }
  $root = Get-Canon $rootEnv
  if ([string]::IsNullOrEmpty($root)) { return (Write-Why 'step 6') }
  $words = Get-Words $cmd
  if ($null -eq $words -or $words.Length -lt 2) { return (Write-Why ('step 7 words=' + ($words -join '|'))) }
  $w0 = Get-Canon $words[0]
  $w1 = Get-Canon $words[1]
  if ($null -eq $w0 -or $null -eq $w1 -or $w0 -cne ($root + '/scripts/bbs-fill')) { return (Write-Why ('step 8 w0=' + $w0 + ' root=' + $root)) }
  $prefix = $root + '/skills/'
  if (-not $w1.StartsWith($prefix, [StringComparison]::Ordinal)) { return (Write-Why 'step 9') }
  $entry = $w1.Substring($prefix.Length)
  $launcher = [IO.Path]::Combine([IO.Path]::Combine($rootNative, 'scripts'), 'bbs-fill')
  $allowed = Get-Allowed $launcher
  if ($null -eq $allowed -or -not ($allowed -ccontains $entry)) { return (Write-Why ('step 10 entry=' + $entry + ' allowed=' + ($allowed -join ','))) }
  $entryParts = $entry.Split('/')
  if (Test-AnyLink $rootNative @('scripts', 'bbs-fill')) { return (Write-Why 'step 11') }
  if (Test-AnyLink $rootNative (@('skills') + $entryParts)) { return (Write-Why 'step 12') }
  $script = [IO.Path]::Combine($rootNative, 'skills')
  foreach ($part in $entryParts) { $script = [IO.Path]::Combine($script, $part) }
  if (-not [IO.File]::Exists($launcher) -or -not [IO.File]::Exists($script)) { return (Write-Why 'step 13') }
  return $entry
}

try {
  $stdin = [Console]::OpenStandardInput()
  $ms = New-Object System.IO.MemoryStream
  $stdin.CopyTo($ms)
  $raw = (New-Object System.Text.UTF8Encoding($false, $true)).GetString($ms.ToArray())
  if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
  $h = $raw | ConvertFrom-Json
  $entry = Get-Decision $h
} catch {
  [void](Write-Why ('exception: ' + $_.Exception.Message + ' at ' + $_.InvocationInfo.PositionMessage))
  $entry = $null
}
if ($entry) {
  $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'allow'; permissionDecisionReason = ($REASON + $entry) } }
  [Console]::Out.Write(($out | ConvertTo-Json -Compress -Depth 4))
}
exit 0
