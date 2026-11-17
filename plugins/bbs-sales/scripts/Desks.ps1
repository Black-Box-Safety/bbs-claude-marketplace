# Index convention: Start/End are native .NET (UTF-16) indices into the original $Path, ready for .Substring; callers wrap Find-BbsDeskRootAll in @(...).
# Desk registry loader, PowerShell twin of scripts/desks.py. Dot-source it:  . "$PSScriptRoot\..\scripts\Desks.ps1"
# PS 5.1-safe (no ?., no ternary, no -AsHashtable, no ConvertFrom-Json -Depth). Never throws from Get-BbsDesks.
#
#   Get-BbsDeskRegistryPath                 -> [string]
#   Get-BbsDesks [-Path <string>]           -> [pscustomobject]@{ Desks = <object[]>; Error = <string or $null> }
#   Find-BbsDeskRoot    -Path -Desks        -> [pscustomobject]@{ Desk; Root; Start; End } or $null
#   Find-BbsDeskRootAll -Path -Desks        -> object[]   (callers wrap the call in @( ) so zero or one result is still an array)
#
# Semantics match desks.py: '\' -> '/' on the path and on each root; ASCII-only case folding (Python's re.I|re.A,
# so U+212A KELVIN SIGN is NOT a 'k'); only kind 'rfq' desks are searched; leftmost start wins, then the longer
# root, then desk-then-root order; find_all is non-overlapping and ordered by start. Start and End are UTF-16 indices
# (not Python's code points; desks_parity.py converts when comparing).

$script:BbsDesksRoot = $PSScriptRoot

# Must equal FALLBACK in desks.py as JSON (Task 10's checker compares them). The apostrophe is written ' so the
# literal needs no quote doubling.
$FALLBACK_JSON = '[{"desk_id":"ca-state","kind":"rfq","roots":["All RFQ\u0027s by Agency"],"deal_depth":[2,3],"deal_name_rule":"date","rep_min_depth":2,"guard":{"no_rename":true,"near_duplicate":true,"filled_immutable":true},"record_profile":"ca-v2"}]'

$script:BbsDeskKeys = @('desk_id', 'kind', 'roots', 'deal_depth', 'deal_name_rule', 'rep_min_depth', 'guard', 'record_profile')
$script:BbsGuardKeys = @('no_rename', 'near_duplicate', 'filled_immutable')

function Get-BbsDeskRegistryPath {
  $e = $env:BBS_DESKS_FILE
  if (-not [string]::IsNullOrEmpty($e)) { return $e }
  $p = Join-Path (Join-Path $script:BbsDesksRoot '..') 'references'
  $p = Join-Path $p 'desks.json'
  return [System.IO.Path]::GetFullPath($p)
}

function Get-BbsFallbackDesks {
  # Fresh copy every call (the Python side deep-copies). @() because a one-element JSON array unrolls in the pipeline.
  # 5.1 writes a JSON array as ONE object (no enumeration), so @() would nest it; 7 enumerates. ,@($parsed) is right on both.
  $parsed = ConvertFrom-Json $FALLBACK_JSON
  return ,@($parsed)
}

function Test-BbsInt($v) {
  # JSON integers only: booleans are [bool], floats are [double]/[decimal].
  return (($v -is [int]) -or ($v -is [long]))
}

function Test-BbsKeySet($obj, [string[]]$keys) {
  $names = @()
  foreach ($p in $obj.PSObject.Properties) { $names += $p.Name }
  if ($names.Count -ne $keys.Count) { return $false }
  foreach ($k in $keys) {
    if (-not ($names -ccontains $k)) { return $false }
  }
  return $true
}

function Test-BbsDesksData($data) {
  # Returns an error string naming the offending key, or $null. Mirrors _check() in desks.py.
  if (-not ($data -is [System.Management.Automation.PSCustomObject])) { return 'schema_version must be 1' }
  $ver = $null
  $desks = $null
  foreach ($p in $data.PSObject.Properties) {
    if ($p.Name -ceq 'schema_version') { $ver = $p.Value }
    elseif ($p.Name -ceq 'desks') { $desks = $p.Value }
  }
  # Python's 1 == True == 1.0, so a boolean true or a numeric 1 passes.
  $verOk = $false
  if ($ver -is [bool]) { $verOk = [bool]$ver }
  elseif (($ver -is [int]) -or ($ver -is [long]) -or ($ver -is [double]) -or ($ver -is [decimal])) { $verOk = ($ver -eq 1) }
  if (-not $verOk) { return 'schema_version must be 1' }
  if (-not ($desks -is [System.Array]) -or $desks.Count -lt 1) { return 'desks must be a non-empty list' }
  $seen = @{}
  foreach ($d in $desks) {
    if (-not ($d -is [System.Management.Automation.PSCustomObject])) { return 'desks entry must be an object' }
    if (-not (Test-BbsKeySet $d $script:BbsDeskKeys)) { return ('desk keys must be exactly ' + ($script:BbsDeskKeys -join ', ')) }
    $did = $d.desk_id
    if (-not ($did -is [string]) -or -not [regex]::IsMatch($did, '^[a-z][a-z0-9-]*\z')) { return ('desk_id invalid: ' + $did) }
    if ($seen.ContainsKey($did)) { return ('desk_id duplicate: ' + $did) }
    $seen[$did] = $true
    $kind = $d.kind
    if (-not ($kind -is [string]) -or -not (($kind -ceq 'rfq') -or ($kind -ceq 'order'))) { return ('kind must be rfq or order in ' + $did) }
    $r = $d.roots
    if (-not ($r -is [System.Array]) -or $r.Count -lt 1) { return ('roots must be a non-empty list of non-empty strings in ' + $did) }
    foreach ($x in $r) {
      if (-not ($x -is [string]) -or $x.Length -lt 1) { return ('roots must be a non-empty list of non-empty strings in ' + $did) }
    }
    $dd = $d.deal_depth
    $ddOk = (($dd -is [System.Array]) -and ($dd.Count -eq 2))
    if ($ddOk) { $ddOk = ((Test-BbsInt $dd[0]) -and (Test-BbsInt $dd[1])) }
    if ($ddOk) { $ddOk = (($dd[0] -ge 1) -and ($dd[0] -le $dd[1])) }
    if (-not $ddOk) { return ('deal_depth must be [min, max] with 1 <= min <= max in ' + $did) }
    $rule = $d.deal_name_rule
    if (-not ($rule -is [string]) -or -not ($rule -ceq 'date')) { return ('deal_name_rule must be date in ' + $did) }
    $rmd = $d.rep_min_depth
    if (-not (Test-BbsInt $rmd) -or $rmd -lt 1) { return ('rep_min_depth must be an int >= 1 in ' + $did) }
    $g = $d.guard
    $gOk = ($g -is [System.Management.Automation.PSCustomObject])
    if ($gOk) { $gOk = (Test-BbsKeySet $g $script:BbsGuardKeys) }
    if ($gOk) {
      foreach ($gp in $g.PSObject.Properties) {
        if (-not ($gp.Value -is [bool])) { $gOk = $false }
      }
    }
    if (-not $gOk) { return ('guard must hold booleans ' + ($script:BbsGuardKeys -join ', ') + ' in ' + $did) }
    if (-not ($d.record_profile -is [string])) { return ('record_profile must be a string in ' + $did) }
  }
  return $null
}

function Get-BbsDesks {
  [CmdletBinding()]
  param([string]$Path)
  try { return (Get-BbsDesksCore $Path) }
  catch {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ('desks registry unreadable: ' + $_.Exception.GetType().Name + '; using built-in fallback') }
  }
}

function Get-BbsDesksCore([string]$Path) {
  if ([string]::IsNullOrEmpty($Path)) { $Path = Get-BbsDeskRegistryPath }
  $name = [System.IO.Path]::GetFileName($Path)

  if (-not [System.IO.File]::Exists($Path)) {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name not found ($Path); using built-in fallback") }
  }
  $bytes = $null
  try { $bytes = [System.IO.File]::ReadAllBytes($Path) }
  catch {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name unreadable ($Path): " + $_.Exception.GetType().Name + '; using built-in fallback') }
  }
  # Python's json.load rejects a UTF-8 BOM; .NET would strip it silently, so refuse it here too.
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name invalid JSON ($Path): UTF-8 BOM; using built-in fallback") }
  }
  $text = $null
  try { $text = (New-Object System.Text.UTF8Encoding($false, $true)).GetString($bytes) }
  catch {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name unreadable ($Path): not UTF-8; using built-in fallback") }
  }
  if ([string]::IsNullOrWhiteSpace($text)) {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name invalid JSON ($Path): empty; using built-in fallback") }
  }
  $data = $null
  try { $data = $text | ConvertFrom-Json -ErrorAction Stop }
  catch {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name invalid JSON ($Path): " + $_.Exception.Message + '; using built-in fallback') }
  }
  $err = Test-BbsDesksData $data
  if ($null -ne $err) {
    return [pscustomobject]@{ Desks = (Get-BbsFallbackDesks); Error = ("$name schema error ($Path): $err; using built-in fallback") }
  }
  $list = $null
  foreach ($p in $data.PSObject.Properties) {
    if ($p.Name -ceq 'desks') { $list = $p.Value }
  }
  return [pscustomobject]@{ Desks = $list; Error = $null }
}

function ConvertTo-BbsAsciiLower([string]$s) {
  # Lower-case A-Z only. Anything else, including U+212A, is left alone, as re.I|re.A does.
  if ([string]::IsNullOrEmpty($s)) { return '' }
  $sb = New-Object System.Text.StringBuilder
  foreach ($ch in $s.ToCharArray()) {
    $c = [int]$ch
    if ($c -ge 65 -and $c -le 90) { [void]$sb.Append([char]($c + 32)) }
    else { [void]$sb.Append($ch) }
  }
  return $sb.ToString()
}

function Add-BbsDeskMatches([string]$Path, [object[]]$Desks, $Into) {
  # Appends one record per root occurrence to the [ArrayList] $Into, in desk-then-root-then-position order.
  $s = ConvertTo-BbsAsciiLower ($Path.Replace('\', '/'))
  $seq = $Into.Count
  foreach ($d in $Desks) {
    if (-not ($d.kind -ceq 'rfq')) { continue }
    foreach ($root in $d.roots) {
      $needle = ConvertTo-BbsAsciiLower ($root.Replace('\', '/'))
      foreach ($m in [regex]::Matches($s, [regex]::Escape($needle))) {
        [void]$Into.Add([pscustomobject]@{
          Desk = $d; Root = $root; Start = $m.Index; End = ($m.Index + $m.Length); Len = $m.Length; Seq = $seq
        })
        $seq++
      }
    }
  }
}

function ConvertTo-BbsDeskMatch($m, [string]$Path) {
  [pscustomobject]@{
    Desk = $m.Desk; Root = $m.Root
    Start = $m.Start; End = $m.End
  }
}

function Find-BbsDeskRoot {
  [CmdletBinding()]
  param([string]$Path, [object[]]$Desks)
  if ($null -eq $Path) { $Path = '' }
  $all = New-Object System.Collections.ArrayList
  Add-BbsDeskMatches $Path $Desks $all
  $best = $null
  foreach ($m in $all) {
    # Strict comparisons, so on a full tie the earlier (desk-then-root) record stays.
    if ($null -eq $best -or $m.Start -lt $best.Start -or ($m.Start -eq $best.Start -and $m.Len -gt $best.Len)) { $best = $m }
  }
  if ($null -eq $best) { return $null }
  return (ConvertTo-BbsDeskMatch $best $Path)
}

function Find-BbsDeskRootAll {
  [CmdletBinding()]
  param([string]$Path, [object[]]$Desks)
  if ($null -eq $Path) { $Path = '' }
  $all = New-Object System.Collections.ArrayList
  Add-BbsDeskMatches $Path $Desks $all
  # Seq is the last key, so the order never depends on Sort-Object being stable.
  $sorted = @($all | Sort-Object -Property @{ Expression = 'Start'; Descending = $false }, @{ Expression = 'Len'; Descending = $true }, @{ Expression = 'Seq'; Descending = $false })
  $out = New-Object System.Collections.ArrayList
  $pos = 0
  foreach ($m in $sorted) {
    if ($m.Start -ge $pos) {
      [void]$out.Add((ConvertTo-BbsDeskMatch $m $Path))
      $pos = $m.End
    }
  }
  return $out.ToArray()
}
