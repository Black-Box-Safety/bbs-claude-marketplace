# SessionStart: when a session opens inside a buyer folder (or a few levels below one),
# put that buyer's recent precedent and open flags in front of Claude before the first prompt.
# Plain stdout is added to context. Silent when nothing relevant is found.

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $h = $raw | ConvertFrom-Json } catch { exit 0 }
$dir = [string]$h.cwd
if (-not $dir -or -not (Test-Path -LiteralPath $dir)) { exit 0 }

$out = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt 5 -and $dir; $i++) {
  $ql = Join-Path $dir 'quote-log.md'
  $fl = Join-Path $dir 'FLAGS.md'
  if (Test-Path -LiteralPath $ql) {
    $out.Add("PRECEDENT -- $ql (most recent rows; cite these before pricing):")
    Get-Content -LiteralPath $ql -Tail 12 | ForEach-Object { $out.Add($_) }
  }
  if (Test-Path -LiteralPath $fl) {
    $rows = Get-Content -LiteralPath $fl | Where-Object { $_ -match '^\|\s*\d{4}-\d{2}-\d{2}' } | Select-Object -Last 5
    if ($rows) {
      $out.Add("OPEN FLAGS -- $fl (latest; do not repeat these mistakes):")
      $rows | ForEach-Object { $out.Add($_) }
    }
  }
  if ($out.Count -gt 0) { break }
  $parent = Split-Path -Parent $dir
  if ($parent -eq $dir) { break }
  $dir = $parent
}

if ($out.Count -gt 0) { $out -join "`n" }
exit 0
