# PreToolUse guard for the BBS quote-desk folder tree ("All RFQ's by Agency").
# Reads the hook JSON on stdin. Silent (exit 0, no output) = allow.
# Deny = JSON with hookSpecificOutput.permissionDecision = "deny" and a reason Claude can relay.
#
# Rules (from workspace/DESK-CLAUDE-template.md landmines):
#   1. Never rename or move anything inside the tree -- folder names carry account numbers.
#   2. Never create a buyer/agency folder whose name is a near-duplicate of a sibling.
#   3. Files under FILLED/ are submitted packets: never overwrite one.

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $h = $raw | ConvertFrom-Json } catch { exit 0 }

$TREE = "All RFQ's by Agency"
$tool = $h.tool_name
$in   = $h.tool_input

function Deny([string]$reason) {
  @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } |
    ConvertTo-Json -Compress -Depth 4
  exit 0
}

function Normalize([string]$name) {
  $n = $name.ToLowerInvariant() -replace '\(all\)', ''
  return ($n -replace '[^a-z0-9]', '')
}

# Word tokens, so "Mule Creek Prison" and "Mule Creek State Prison" can be compared.
function Tokens([string]$name) {
  $n = $name.ToLowerInvariant() -replace '\(all\)', ' '
  return @(($n -replace '[^a-z0-9]', ' ') -split '\s+' | Where-Object { $_ })
}

function Levenshtein([string]$a, [string]$b) {
  if ($a.Length -eq 0) { return $b.Length }
  if ($b.Length -eq 0) { return $a.Length }
  $prev = 0..$b.Length
  for ($i = 1; $i -le $a.Length; $i++) {
    $cur = @($i) + (@(0) * $b.Length)
    for ($j = 1; $j -le $b.Length; $j++) {
      $cost = if ($a[$i-1] -eq $b[$j-1]) { 0 } else { 1 }
      $cur[$j] = [Math]::Min([Math]::Min($cur[$j-1] + 1, $prev[$j] + 1), $prev[$j-1] + $cost)
    }
    $prev = $cur
  }
  return $prev[$b.Length]
}

# One swapped adjacent pair ("cdrc" for "cdcr"). Plain Levenshtein scores a transposition 2,
# and loosening the short-name threshold to 2 would collide real siblings like CDPH and CDCR,
# so the swap is checked on its own.
function IsTransposition([string]$a, [string]$b) {
  if ($a.Length -ne $b.Length -or $a.Length -lt 2) { return $false }
  $diff = @(0..($a.Length - 1) | Where-Object { $a[$_] -ne $b[$_] })
  if ($diff.Count -ne 2 -or ($diff[1] - $diff[0]) -ne 1) { return $false }
  return ($a[$diff[0]] -eq $b[$diff[1]] -and $a[$diff[1]] -eq $b[$diff[0]])
}

# Two folder names are near-duplicates when one is a typo of the other, or when one names the
# same buyer with a word dropped or added ("Mule Creek Prison" vs "Mule Creek State Prison").
function IsNearDuplicate([string]$new, [string]$existing) {
  $want = Normalize $new
  $have = Normalize $existing
  if (-not $want -or -not $have) { return $false }
  if ($want -eq $have) { return $true }
  if ($want.Length -ge 6 -and (Levenshtein $want $have) -le 2) { return $true }
  # Agency acronyms (CDCR, CALPIA) are too short for the rule above: one wrong or swapped
  # letter there is a typo, not a different buyer.
  if ($want.Length -ge 4 -and $want.Length -le 5 -and $have.Length -ge 4 -and $have.Length -le 5) {
    if ((Levenshtein $want $have) -le 1 -or (IsTransposition $want $have)) { return $true }
  }
  $wantT = Tokens $new
  $haveT = Tokens $existing
  if ($wantT.Count -ge 2 -and $haveT.Count -ge 2) {
    $shared = @($wantT | Where-Object { $haveT -contains $_ })
    if ($shared.Count -ge 2 -and ($shared.Count -eq $wantT.Count -or $shared.Count -eq $haveT.Count)) { return $true }
  }
  return $false
}

# Given an absolute path inside the tree, find the first directory segment that does not exist
# yet and compare it against its existing siblings. Returns the offending existing path or $null.
function NearDuplicate([string]$path) {
  $idx = $path.IndexOf($TREE, [StringComparison]::OrdinalIgnoreCase)
  if ($idx -lt 0) { return $null }
  $rootDir = $path.Substring(0, $idx + $TREE.Length)
  $rest = $path.Substring($idx + $TREE.Length).Trim('\', '/')
  if (-not $rest) { return $null }
  $segments = $rest -split '[\\/]'
  $parent = $rootDir
  foreach ($seg in $segments) {
    $candidate = Join-Path $parent $seg
    if (Test-Path -LiteralPath $candidate) { $parent = $candidate; continue }
    # $seg is new. Is it a directory-ish segment? Treat as folder unless it has a file extension.
    if ($seg -match '\.[A-Za-z0-9]{1,5}$') { return $null }
    if (-not (Test-Path -LiteralPath $parent)) { return $null }
    foreach ($sib in Get-ChildItem -LiteralPath $parent -Directory -ErrorAction SilentlyContinue) {
      if (IsNearDuplicate $seg $sib.Name) { return $sib.FullName }
    }
    return $null   # first new segment is distinct; deeper segments are its children
  }
  return $null
}

switch ($tool) {
  { $_ -in 'Bash', 'PowerShell' } {
    $cmd = [string]$in.command
    if (-not $cmd) { exit 0 }
    if ($cmd.IndexOf($TREE, [StringComparison]::OrdinalIgnoreCase) -lt 0) { exit 0 }
    if ($cmd -match '(^|[\s;&|(])(mv|ren|rename|Rename-Item|Move-Item|git\s+mv)\b') {
      Deny "Blocked: renaming or moving inside '$TREE' is never allowed -- folder names carry Grainger account numbers and buyer identity (desk CLAUDE.md landmine 4). If a folder is truly misnamed, tell Parker."
    }
    # Deletes anywhere near a FILLED path, or a redirect whose TARGET is inside FILLED. Reading
    # a packet (cat, pdftotext ... > elsewhere) stays allowed.
    if ($cmd -match '[\\/]FILLED[\\/]' -and $cmd -match '(^|[\s;&|(])(rm|del|Remove-Item)\b') {
      Deny "Blocked: files under FILLED/ are submitted packets and immutable. Do not delete them; save a new version alongside (e.g. -v2)."
    }
    if ($cmd -match '>{1,2}\s*("[^"]*[\\/]FILLED[\\/]|[^\s"|;&]*[\\/]FILLED[\\/])') {
      Deny "Blocked: redirecting output into FILLED/ would overwrite a submitted packet. Write the new file alongside it (e.g. -v2)."
    }
    # Write-only cmdlets and tee: a FILLED path anywhere in the command is the target.
    if ($cmd -match '[\\/]FILLED[\\/]' -and $cmd -match '(^|[\s;&|(])(Set-Content|Add-Content|Out-File|tee)\b') {
      Deny "Blocked: writing into FILLED/ would overwrite a submitted packet. Write the new file alongside it (e.g. -v2)."
    }
    # Copies: the LAST path token is the destination. Copying a packet OUT of FILLED is fine.
    if ($cmd -match '(^|[\s;&|(])(cp|copy|Copy-Item|Move-Item|mv)\b') {
      $tokens = [regex]::Matches($cmd, '"[^"]+"|\S+') | ForEach-Object { $_.Value.Trim('"') }
      $dest = ($tokens | Where-Object { $_ -match '[\\/]' -and $_ -notmatch '^-' } | Select-Object -Last 1)
      if ($dest -and $dest -match '[\\/]FILLED[\\/]') {
        Deny "Blocked: copying onto FILLED/ would overwrite a submitted packet. Copy to a new name alongside it (e.g. -v2)."
      }
    }
    if ($cmd -match '(^|[\s;&|(])(mkdir|md|New-Item)\b') {
      $m = [regex]::Match($cmd, '"([^"]*' + [regex]::Escape($TREE) + '[^"]*)"')
      $target = if ($m.Success) { $m.Groups[1].Value } else { ($cmd -split '\s+' | Where-Object { $_ -like "*$TREE*" } | Select-Object -First 1) }
      if ($target) {
        $dup = NearDuplicate $target
        if ($dup) { Deny "Blocked: '$target' is a near-duplicate of the existing folder '$dup'. Duplicate buyer folders hide precedent (landmine 1). Use the existing folder, or ask Parker if this is genuinely a different buyer." }
      }
    }
    exit 0
  }
  { $_ -in 'Write', 'Edit', 'MultiEdit', 'NotebookEdit' } {
    $p = [string]$in.file_path
    if (-not $p) { $p = [string]$in.notebook_path }
    if (-not $p) { exit 0 }
    if ($p.IndexOf($TREE, [StringComparison]::OrdinalIgnoreCase) -lt 0) { exit 0 }
    if ($p -match '[\\/]FILLED[\\/]' -and (Test-Path -LiteralPath $p)) {
      Deny "Blocked: '$p' is a submitted packet under FILLED/ and is immutable. Save a new version alongside it (e.g. add -v2) instead of overwriting."
    }
    $dup = NearDuplicate $p
    if ($dup) { Deny "Blocked: this path would create a folder that near-duplicates '$dup'. Duplicate buyer folders hide precedent (landmine 1). Write into the existing folder, or ask Parker if this is genuinely a different buyer." }
    exit 0
  }
  default { exit 0 }
}
