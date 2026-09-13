# Rep Workspace v1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the v1.1 items Parker ruled on 2026-09-13 without waiting on the v1 pilot: the
`commons` tier of curated third-party plugins (browser, caveman, Anthropic document skills), a
rep-machine bootstrap script, quote-desk guard hooks, and the `supplier-scout` agent.

**Architecture:** Everything lands on branch `v1.1`, never `main`, so the v1 pilot runs on
untouched code; Parker merges after the acceptance gate. Third-party plugins are pinned by tag or
commit as external entries in `marketplace.json` under category `commons` (the same mechanism
`impeccable` already uses) and documented in `docs/COMMONS.md`; nothing is vendored. Hooks are
PowerShell scripts invoked in exec form (no shell, no Node dependency) from
`plugins/bbs-sales/hooks/hooks.json`. The bootstrap script is idempotent `winget`.

**Tech Stack:** Claude Code plugin/marketplace JSON, PowerShell 5.1 (Windows 11 rep machines),
`winget`, markdown. Validation: `claude plugin validate`, `python -m json.tool`, the hook test
script in this plan.

**Working directory:** `C:\Users\Parker-BBS\bbs-claude-marketplace`, branch `v1.1` (already
created from `main` at `af0ba2b`).

**Conventions:** Commit trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` on
every commit. Git Bash: `> /dev/null`, never `> NUL`. Docs wrap at ~100 cols. **Push only the
`v1.1` branch** (Task 8). All repo blobs are LF; the working copy shows CRLF via autocrlf — write
LF and let git normalize.

**Design notes (no brainstorm was possible — Parker was asleep; assumptions stated):**

- `commons` is a **category of pinned external plugins**, not a plugin of its own. A plugin
  cannot depend on other plugins, so a `bbs-commons` meta-plugin would be empty. The name lives
  on the category, `docs/COMMONS.md`, and the README section.
- Anthropic's `document-skills` (docx, pdf, xlsx) comes from the official `anthropics/skills`
  marketplace, pinned to a commit. `pptx` is left out (1 MB of scripts reps rarely need; add on
  request). `internal-comms` is bundled in Anthropic's `example-skills` with a dozen unrelated
  skills, so it is left out too.
- `superpowers-chrome` self-labels beta. Parker ruled full browser access anyway; the pilot will
  tell. Its skill mode needs Node.js, so the bootstrap installs Node LTS and Chrome.
- Hooks 1 (no folder renames), 2 (no near-duplicate buyer folders), 3 (`FILLED/` immutable) and 7
  (precedent at session start) ship. Hook 6 (PreCompact injection) is dropped: Claude Code
  hooks cannot inject compaction instructions; the desk CLAUDE.md line already covers it. Hook 4
  (unsourced-price Stop hook) waits on a price-cell format ruling.
- `supplier-scout` uses Firecrawl tools when the connector is assigned and falls back to
  `WebSearch`/`WebFetch` otherwise; Firecrawl scope for reps is Parker's open ruling.
- `bbs-sourcing` stays in `bbs-website` (REGISTRY says the move is a separate decision); only
  its Step 5c changes to dispatch the agent.

---

### Task 1: Commons entries in the marketplace manifest

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add three plugin entries** after the `impeccable` entry (inside the `plugins`
  array, comma-separated), exactly:

```json
    {
      "name": "superpowers-chrome",
      "source": {
        "source": "url",
        "url": "https://github.com/obra/superpowers-chrome.git",
        "ref": "v3.0.5"
      },
      "description": "Commons: drives the rep's real Chrome over the DevTools protocol (logged-in sessions, product research on distributor and agency sites). Skill mode needs Node.js (bbs-setup.ps1 installs it). Upstream self-labels beta; pinned to a release tag, refreshed quarterly per docs/COMMONS.md.",
      "version": "3.0.5",
      "author": {
        "name": "Jesse Vincent"
      },
      "keywords": [
        "browser",
        "chrome",
        "commons",
        "external",
        "research"
      ],
      "category": "commons"
    },
    {
      "name": "caveman",
      "source": {
        "source": "url",
        "url": "https://github.com/JuliusBrussee/caveman.git",
        "ref": "v2.6.0"
      },
      "description": "Commons: terse output mode (/caveman lite|full|ultra) that cuts roughly two-thirds of output tokens while keeping technical content exact. Opt-in per session; ruled in 2026-09-13. Pinned to a release tag.",
      "version": "2.6.0",
      "author": {
        "name": "Julius Brussee"
      },
      "keywords": [
        "commons",
        "external",
        "tokens",
        "style"
      ],
      "category": "commons"
    },
    {
      "name": "document-skills",
      "source": {
        "source": "url",
        "url": "https://github.com/anthropics/skills.git",
        "ref": "34040c9c568585f6929bedeaad110ad08f079624"
      },
      "strict": false,
      "skills": [
        "./skills/docx",
        "./skills/pdf",
        "./skills/xlsx"
      ],
      "description": "Commons: Anthropic's official document skills — Word (tracked changes, comments), PDF (extract, merge, fill, annotate), Excel (formulas, charts). RFQ worksheets, bid PDFs, price lists. Pinned to a commit of anthropics/skills; pptx deliberately excluded.",
      "author": {
        "name": "Anthropic"
      },
      "keywords": [
        "commons",
        "docx",
        "external",
        "pdf",
        "xlsx"
      ],
      "category": "commons"
    }
```

- [ ] **Step 2: Bump `metadata.version`** from `"0.4.0"` to `"0.5.0"`.

- [ ] **Step 3: Validate**

Run: `python -m json.tool .claude-plugin/marketplace.json > /dev/null; echo $?` → `0`.
Run: `claude plugin validate . --strict` → `Validation passed`. If it rejects `strict`/`skills`
on an entry, report BLOCKED with the output (the official Anthropic marketplace uses exactly this
shape, so a rejection means a CLI version difference worth knowing about).

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(commons): pin superpowers-chrome v3.0.5, caveman v2.6.0, anthropic document-skills (docx/pdf/xlsx) as commons entries"
```

---

### Task 2: COMMONS.md — the curation record

**Files:**
- Create: `docs/COMMONS.md`
- Modify: `REGISTRY.md` (one row)
- Modify: `README.md` (plugin table + one sentence)

- [ ] **Step 1: Create `docs/COMMONS.md`** with exactly:

```markdown
# Commons — curated third-party plugins

**What it is.** Generally applicable skills and plugins, made by other people, that a BBS rep is
likely to find genuinely useful. Nothing BBS-specific lives here; that belongs in `bbs-sales`
or `bbs-foundations`. Ruled 2026-09-13.

**The bar.** Quality first, tokens second: a plugin gets in if it works out of the box, is
maintained upstream, and matches a task reps actually do. Context cost is a tiebreaker, not a
veto. Anything that needs a per-machine API key stays out.

**How it ships.** Each item is a pinned external entry in `.claude-plugin/marketplace.json`
under `category: "commons"`, enabled for everyone through managed settings. Pins are release
tags where the upstream cuts them, a commit SHA otherwise. Nothing is copied into this repo.

## Current roster

| Plugin | Pin | Why reps have it | Watch for |
|---|---|---|---|
| `superpowers-chrome` | `v3.0.5` | Drives the rep's own Chrome: product research on distributor and agency sites, logged-in sessions included. Full browser access is a standing ruling; no deny rules touch it | Upstream says beta. Needs Node.js (bootstrap installs it). If a rep hits a crash, log it in FLAGS |
| `caveman` | `v2.6.0` | Opt-in terse mode. Cuts output tokens roughly two-thirds; technical content stays exact. `/caveman lite` is a good default for long sessions | Off by default; never forced on |
| `document-skills` (Anthropic) | commit `34040c9c` | Word, PDF, Excel handling with real scripts: fill and merge PDFs, read tracked changes, build spreadsheets with formulas. RFQ worksheets and bid packets are exactly this | `pptx` excluded on purpose. Skills carry Python scripts; `uv` from the bootstrap covers the runtime |

## Considered, not included (yet)

| Candidate | Reason |
|---|---|
| humanizer / avoid-ai-writing | Already inside `bbs-voice-template` (35 patterns vendored from blader/humanizer) |
| superpowers (full) | Developer workflow; its session hook injects a large mandatory block. Parker-only |
| Playwright MCP | Isolated browser, no logins, ~25 tool schemas per session |
| `pptx`, `internal-comms` | Bundled with unrelated skills or rarely needed; add on request |
| meeting-insights-analyzer, sanitize, csv-data-summarizer | Community skills; useful, unreviewed. Brainstorm after the pilot |
| claude-persona | Marketing tier, burns seat limits; admin only |

## Refresh

Quarterly, with key rotation: check each upstream for a newer tag, read its changelog, bump the
pin, run `claude plugin validate . --strict`, push. If an upstream goes quiet for two quarters,
decide: fork under Black-Box-Safety or drop.

## Propose an addition

One line in the Teams sales channel: what it does, the task it would replace, a link. Parker
tries it a week on live work first. Same bar as above.

*Maintainer: Parker Marshall · Last verified: 2026-09-13*
```

- [ ] **Step 2: REGISTRY.md** — insert a row before the `bbs-suppliers` row:

```markdown
| Commons (pinned third-party plugins) | **canon** | `docs/COMMONS.md`; entries in `marketplace.json` under `category: commons`; refreshed quarterly |
```

- [ ] **Step 3: README.md** — in `## The plugins`, after the `impeccable` row, add:

```markdown
| `superpowers-chrome` · `caveman` · `document-skills` | **Commons**: pinned third-party plugins reps get by default — real-Chrome browsing, opt-in terse mode, Anthropic's Word/PDF/Excel skills | [docs/COMMONS.md](docs/COMMONS.md) |
```

and change the badge on line 5 from `plugins-3%20BBS%20%2B%202%20pinned` to
`plugins-3%20BBS%20%2B%205%20pinned` with alt text `Three BBS plugins plus five pinned external`.
Also in `## Repo layout`, change the manifest comment to
`# manifest: 3 BBS plugins (unpinned) + 5 external (pinned, 3 of them commons)`.

- [ ] **Step 4: Validate** — `awk 'length > 100 && !/^\|/ && !/img.shields/' docs/COMMONS.md README.md` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add docs/COMMONS.md REGISTRY.md README.md
git commit -m "docs(commons): curation record, roster, refresh cadence; README + REGISTRY pointers"
```

---

### Task 3: Managed settings — enable commons, allow the browser tool

**Files:**
- Modify: `plugins/bbs-foundations/docs/bbs-managed-settings.json`
- Modify: `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md`

- [ ] **Step 1: `enabledPlugins`** — add, keeping alphabetical order among the
  `@bbs-claude-marketplace` keys:

```json
    "caveman@bbs-claude-marketplace": true,
    "document-skills@bbs-claude-marketplace": true,
    "superpowers-chrome@bbs-claude-marketplace": true,
```

- [ ] **Step 2: `permissions.allow`** — append after `"Bash(python3 -m py_compile:*)"` (add the
  comma):

```json
      "mcp__plugin_superpowers-chrome_chrome__use_browser"
```

Rationale to keep in mind: every browser action prompting for permission would kill the flow
Parker described; the ruling is zero prompts on browsing. The tool name is the plugin-scoped MCP
name and is identical on every machine because the plugin name is fixed by our marketplace.

- [ ] **Step 3: Validate** — `python -m json.tool plugins/bbs-foundations/docs/bbs-managed-settings.json > /dev/null; echo $?` → `0`.

- [ ] **Step 4: MANAGED-SETTINGS.md** — (a) in the block-by-block table, `enabledPlugins` row:
  change the plugin list to
  `` `bbs-foundations`, `bbs-sales`, `bbs-website`, `claudeforge`, `impeccable`, `skill-bus`, plus the commons: `superpowers-chrome`, `caveman`, `document-skills` — all on, for everyone ``;
  (b) `permissions.allow` row purpose column: append ` + the superpowers-chrome browser tool
  (full browser access is a ruling; prompts per click would defeat it)`; (c) new section before
  `## What is deliberately not here`:

```markdown
## Commons (2026-09-13)

Three pinned third-party plugins ship to everyone: `superpowers-chrome` (real-Chrome browsing),
`caveman` (opt-in terse mode), and Anthropic's `document-skills` (docx/pdf/xlsx). Curation,
bar, and refresh cadence: `docs/COMMONS.md`. The browser tool is on the allow list on purpose —
reps browse to find products, and the pricing-source rule (no price from the open web) is a
rule about where numbers come from, not a restriction on browsing.
```

  (d) header `Last verified: 2026-09-11` → `Last verified: 2026-09-13`.

- [ ] **Step 5: Commit**

```bash
git add plugins/bbs-foundations/docs/bbs-managed-settings.json plugins/bbs-foundations/docs/MANAGED-SETTINGS.md
git commit -m "feat(managed-settings): enable commons plugins for everyone; allow the browser tool without prompts"
```

---

### Task 4: bbs-setup.ps1 — rep machine bootstrap

**Files:**
- Create: `scripts/bbs-setup.ps1`
- Modify: `docs/REP-SETUP.md`

- [ ] **Step 1: Create `scripts/bbs-setup.ps1`** exactly:

```powershell
<#
.SYNOPSIS
  Black Box Safety rep-machine bootstrap. Installs the command-line tools Claude Code leans on.
.DESCRIPTION
  Idempotent: skips anything already installed. Safe to rerun. Uses winget (built into Windows 11).
  Run from any PowerShell window:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1
  Preview without installing:
    powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1 -DryRun
#>
param([switch]$DryRun)

$packages = @(
  @{ Id = 'Git.Git';                 Why = 'Claude Code hooks and the Bash tool run through Git Bash' },
  @{ Id = 'OpenJS.NodeJS.LTS';       Why = 'superpowers-chrome browsing skill (chrome-ws) needs Node' },
  @{ Id = 'Google.Chrome';           Why = 'the browser Claude drives for product research' },
  @{ Id = 'oschwartz10612.Poppler';  Why = 'pdftotext/pdfinfo: RFQ PDFs become text before Claude reads them' },
  @{ Id = 'UB-Mannheim.TesseractOCR'; Why = 'OCR for scanned RFQs and faxed worksheets' },
  @{ Id = 'JohnMacFarlane.Pandoc';   Why = 'Word attachments to markdown' },
  @{ Id = 'astral-sh.uv';            Why = 'Python runtime for form-fill and document-skills scripts, zero config' },
  @{ Id = 'DuckDB.cli';              Why = 'query price lists and SCPRS exports instead of reading them whole' },
  @{ Id = 'jqlang.jq';               Why = 'JSON plumbing for scripts and hooks' }
)

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error "winget not found. Install 'App Installer' from the Microsoft Store, then rerun this script."
  exit 1
}

Write-Host "BBS rep-machine bootstrap $(if ($DryRun) { '(dry run — nothing will be installed)' })"
Write-Host ""

$installed = winget list --accept-source-agreements 2>$null | Out-String
$failed = @()

foreach ($p in $packages) {
  if ($installed -match [regex]::Escape($p.Id)) {
    Write-Host ("[ok]      {0}" -f $p.Id)
    continue
  }
  if ($DryRun) {
    Write-Host ("[would]   {0,-28} {1}" -f $p.Id, $p.Why)
    continue
  }
  Write-Host ("[install] {0,-28} {1}" -f $p.Id, $p.Why)
  winget install --id $p.Id --exact --silent --accept-package-agreements --accept-source-agreements | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Warning ("winget exit {0} for {1}. Install it by hand later; nothing else here depends on it." -f $LASTEXITCODE, $p.Id)
    $failed += $p.Id
  }
}

Write-Host ""
if ($failed.Count -gt 0) {
  Write-Host ("Finished with {0} item(s) to install by hand: {1}" -f $failed.Count, ($failed -join ', '))
} else {
  Write-Host "Done."
}
Write-Host "Close and reopen VS Code so PATH picks up the new tools, then run /bbs-checkup in Claude."
```

- [ ] **Step 2: Dry-run test**

Run (Git Bash): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bbs-setup.ps1 -DryRun`
Expected: a header line, then one `[ok]` or `[would]` line per package (9 lines), then `Done.`
and the reopen-VS-Code line. No `[install]` lines, no errors. Paste the output in the report.

- [ ] **Step 3: REP-SETUP.md** — in `## Set up (once)`, insert a new step 1 and renumber the
  rest (VS Code becomes 2, extension 3, workspace 4, `/bbs-onboard` 5, `/bbs-checkup` 6,
  `/bbs-my-voice` 7):

```markdown
1. **Run the bootstrap** — download `scripts/bbs-setup.ps1` from the marketplace repo (Parker
   posts it in Teams with the workspace file), then in PowerShell:
   `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1`. It installs Git, Node, Chrome,
   and the PDF/OCR/Office command-line tools Claude uses to read RFQs. Two minutes, safe to rerun.
```

  Also in `## Daily use`, add a bullet after the "what did we quote them last time" bullet:

```markdown
- Need to find a product or a supplier? Ask Claude to open Chrome and look. It drives your own
  browser, logged in as you. Prices still come from Grainger or a vendor quote, never from a web
  page — Claude knows the rule.
```

- [ ] **Step 4: Validate** — `awk 'length > 100' docs/REP-SETUP.md` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add scripts/bbs-setup.ps1 docs/REP-SETUP.md
git commit -m "feat(setup): bbs-setup.ps1 winget bootstrap (git, node, chrome, poppler, tesseract, pandoc, uv, duckdb, jq); REP-SETUP step 1 + browsing bullet"
```

---

### Task 5: Quote-desk guard hooks in bbs-sales

**Files:**
- Create: `plugins/bbs-sales/hooks/hooks.json`
- Create: `plugins/bbs-sales/hooks/guard-tree.ps1`
- Create: `plugins/bbs-sales/hooks/desk-context.ps1`
- Create: `plugins/bbs-sales/hooks/tests/run-tests.ps1`
- Modify: `plugins/bbs-sales/.claude-plugin/plugin.json` (add `"hooks": "./hooks/hooks.json"`)
- Modify: `plugins/bbs-sales/README.md` (new section)

- [ ] **Step 1: Write the test script first** — `plugins/bbs-sales/hooks/tests/run-tests.ps1`:

```powershell
# Runs the bbs-sales hook scripts against fixture inputs. Exit 0 = all pass.
# Usage (Git Bash or PowerShell):  powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1
$ErrorActionPreference = 'Stop'
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$guard = Join-Path (Split-Path -Parent $here) 'guard-tree.ps1'
$ctx   = Join-Path (Split-Path -Parent $here) 'desk-context.ps1'

# Fixture tree under %TEMP%
$root = Join-Path $env:TEMP ("bbs-hook-tests-" + [guid]::NewGuid().ToString('N'))
$tree = Join-Path $root "All RFQ's by Agency"
$cdcr = Join-Path $tree 'CDCR (ALL)'
$mcsp = Join-Path $cdcr 'Mule Creek State Prison'
New-Item -ItemType Directory -Force -Path (Join-Path $mcsp 'FILLED') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $tree 'Cal Trans (ALL)') | Out-Null
Set-Content -Path (Join-Path $mcsp 'FILLED\packet-b.pdf') -Value 'x'
Set-Content -Path (Join-Path $mcsp 'quote-log.md') -Value @(
  '| Date | Item | Quote# | Vehicle | Value | Outcome |',
  '|---|---|---|---|---|---|',
  '| 2026-03-04 | Nitrile gloves | SQ-1001 | NASPO | 2400 | won |'
)
Set-Content -Path (Join-Path $mcsp 'FLAGS.md') -Value @(
  '| Date | Skill/step | What happened | Caught before send? | Fixed by |',
  '|---|---|---|---|---|',
  '| 2026-09-15 | naspo-quote | wrong solicitation # | yes | (Parker: triage) |'
)

function Run($script, $obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 5
  return ($json | powershell -NoProfile -ExecutionPolicy Bypass -File $script | Out-String).Trim()
}
function Decision($out) {
  if (-not $out) { return 'allow' }
  try { return ((($out | ConvertFrom-Json).hookSpecificOutput).permissionDecision) } catch { return "unparseable: $out" }
}

$fails = 0
function Check($name, $got, $want) {
  if ($got -eq $want) { Write-Host "PASS  $name" } else { Write-Host "FAIL  $name  (got '$got', want '$want')"; $script:fails++ }
}

# 1. Rename inside the tree via Bash -> deny
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mv `"$cdcr`" `"$tree\CDCR`"" } }
Check 'bash mv inside tree denied' (Decision $o) 'deny'

# 2. Rename outside the tree -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = 'mv a.txt b.txt' } }
Check 'bash mv elsewhere allowed' (Decision $o) 'allow'

# 3. Overwrite an existing FILLED file -> deny
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $mcsp 'FILLED\packet-b.pdf'); content='y' } }
Check 'overwrite FILLED denied' (Decision $o) 'deny'

# 4. New file in FILLED -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $mcsp 'FILLED\packet-c.pdf'); content='y' } }
Check 'new FILLED file allowed' (Decision $o) 'allow'

# 5. Near-duplicate buyer folder via mkdir -> deny (CalTrans vs Cal Trans (ALL))
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Bash'; tool_input=@{ command = "mkdir `"$tree\CalTrans`"" } }
Check 'near-duplicate agency folder denied' (Decision $o) 'deny'

# 6. Near-duplicate buyer folder via Write into new folder -> deny (Mule Creek Prison vs Mule Creek State Prison)
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $cdcr 'Mule Creek Prison\CLAUDE.md'); content='x' } }
Check 'near-duplicate buyer via Write denied' (Decision $o) 'deny'

# 7. Genuinely new buyer folder -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Write'; tool_input=@{ file_path = (Join-Path $cdcr 'Folsom State Prison\CLAUDE.md'); content='x' } }
Check 'new distinct buyer allowed' (Decision $o) 'allow'

# 8. Edit of an ordinary file in the tree -> allow
$o = Run $guard @{ hook_event_name='PreToolUse'; tool_name='Edit'; tool_input=@{ file_path = (Join-Path $mcsp 'quote-log.md'); old_string='a'; new_string='b' } }
Check 'edit quote-log allowed' (Decision $o) 'allow'

# 9. Session start inside a buyer folder -> precedent + flags in stdout
$o = Run $ctx @{ hook_event_name='SessionStart'; source='startup'; cwd = $mcsp }
Check 'session context has precedent' ($o -match 'PRECEDENT' -and $o -match 'SQ-1001') $true
Check 'session context has flags'     ($o -match 'OPEN FLAGS' -and $o -match 'wrong solicitation') $true

# 10. Session start outside any buyer folder -> silent
$o = Run $ctx @{ hook_event_name='SessionStart'; source='startup'; cwd = $root }
Check 'session context silent outside tree' ($o -eq '') $true

Remove-Item -Recurse -Force $root
Write-Host ""
if ($fails -eq 0) { Write-Host "ALL PASS"; exit 0 } else { Write-Host "$fails FAILED"; exit 1 }
```

- [ ] **Step 2: Run it to see it fail** — `powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1`
  Expected: errors because `guard-tree.ps1` and `desk-context.ps1` do not exist yet.

- [ ] **Step 3: Create `plugins/bbs-sales/hooks/guard-tree.ps1`** exactly:

```powershell
# PreToolUse guard for the BBS quote-desk folder tree ("All RFQ's by Agency").
# Reads the hook JSON on stdin. Silent (exit 0, no output) = allow.
# Deny = JSON with hookSpecificOutput.permissionDecision = "deny" and a reason Claude can relay.
#
# Rules (from workspace/DESK-CLAUDE-template.md landmines):
#   1. Never rename or move anything inside the tree — folder names carry account numbers.
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
    $want = Normalize $seg
    foreach ($sib in Get-ChildItem -LiteralPath $parent -Directory -ErrorAction SilentlyContinue) {
      $have = Normalize $sib.Name
      if ($have -eq $want) { return $sib.FullName }
      if ($want.Length -ge 6 -and (Levenshtein $want $have) -le 2) { return $sib.FullName }
    }
    return $null   # first new segment is distinct; deeper segments are its children
  }
  return $null
}

switch ($tool) {
  'Bash' {
    $cmd = [string]$in.command
    if (-not $cmd) { exit 0 }
    if ($cmd.IndexOf($TREE, [StringComparison]::OrdinalIgnoreCase) -lt 0) { exit 0 }
    if ($cmd -match '(^|[\s;&|(])(mv|ren|rename|Rename-Item|Move-Item|git\s+mv)\b') {
      Deny "Blocked: renaming or moving inside '$TREE' is never allowed — folder names carry Grainger account numbers and buyer identity (desk CLAUDE.md landmine 4). If a folder is truly misnamed, tell Parker."
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
```

- [ ] **Step 4: Create `plugins/bbs-sales/hooks/desk-context.ps1`** exactly:

```powershell
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
    $out.Add("PRECEDENT — $ql (most recent rows; cite these before pricing):")
    Get-Content -LiteralPath $ql -Tail 12 | ForEach-Object { $out.Add($_) }
  }
  if (Test-Path -LiteralPath $fl) {
    $rows = Get-Content -LiteralPath $fl | Where-Object { $_ -match '^\|\s*\d{4}-\d{2}-\d{2}' } | Select-Object -Last 5
    if ($rows) {
      $out.Add("OPEN FLAGS — $fl (latest; do not repeat these mistakes):")
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
```

- [ ] **Step 5: Create `plugins/bbs-sales/hooks/hooks.json`** exactly:

```json
{
  "description": "bbs-sales quote-desk guards: no renames inside the tree, no near-duplicate buyer folders, FILLED/ is immutable; buyer precedent and open FLAGS injected at session start. PowerShell, exec form, Windows rep machines.",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "powershell",
            "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "${CLAUDE_PLUGIN_ROOT}/hooks/guard-tree.ps1"],
            "timeout": 15,
            "statusMessage": "bbs-sales: checking quote-desk folder rules"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "powershell",
            "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "${CLAUDE_PLUGIN_ROOT}/hooks/desk-context.ps1"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Register in `plugins/bbs-sales/.claude-plugin/plugin.json`** — add after the
  `"skills": "./skills/"` line (with the comma on the preceding line):

```json
  "hooks": "./hooks/hooks.json"
```

- [ ] **Step 7: Run the tests** — `powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1`
  Expected: 11 `PASS` lines and `ALL PASS`, exit 0. If any FAIL, fix the script under test (not
  the test) and rerun. Then `python -m json.tool plugins/bbs-sales/hooks/hooks.json > /dev/null`
  and `claude plugin validate plugins/bbs-sales` → passes.

- [ ] **Step 8: Document** — append to `plugins/bbs-sales/README.md` before its last section
  (`## Rollout guide`):

```markdown
## Hooks (v1.1)

Deterministic guards, PowerShell, shipped with the plugin. They fire on Windows rep machines
without any per-machine setup.

| Hook | When | What it does |
|---|---|---|
| `guard-tree.ps1` | Before Bash / Write / Edit | Denies renames or moves inside `All RFQ's by Agency` (folder names carry account numbers); denies creating a buyer or agency folder whose name near-duplicates a sibling (case, spaces, `(ALL)`, two typos); denies overwriting anything under `FILLED/` |
| `desk-context.ps1` | Session start inside a buyer folder | Puts the last rows of `quote-log.md` and the latest `FLAGS.md` entries in front of Claude before the first prompt |

A denial shows up as a permission refusal with a one-line reason Claude relays. Test locally:
`powershell -File plugins/bbs-sales/hooks/tests/run-tests.ps1`.
```

- [ ] **Step 9: Commit**

```bash
git add plugins/bbs-sales/hooks plugins/bbs-sales/.claude-plugin/plugin.json plugins/bbs-sales/README.md
git commit -m "feat(bbs-sales): quote-desk guard hooks — no renames, no near-duplicate buyer folders, FILLED immutable; precedent injected at session start; tests"
```

---

### Task 6: supplier-scout agent + bbs-sourcing hand-off

**Files:**
- Create: `plugins/bbs-sales/agents/supplier-scout.md`
- Modify: `plugins/bbs-website/skills/bbs-sourcing/SKILL.md` (Step 5c)

- [ ] **Step 1: Create `plugins/bbs-sales/agents/supplier-scout.md`** exactly:

```markdown
---
name: supplier-scout
description: Finds supplier options for an RFQ line item BBS has never sourced — manufacturer, authorized distributors, alternates, MOQ, lead time, published price with URL and date. Use when a part number or product is unknown, when the vendor directory has no fit, or when the rep wants more options on a high-dollar line. Returns a supplier-options table; never writes files or sends anything.
model: inherit
disallowedTools: Write, Edit, MultiEdit, NotebookEdit, Bash
---

You are BBS's supplier scout. A rep hands you one line item (description, part number if any,
quantity, the buying agency) and you come back with real supplier options a rep can act on.
You do research. You never write files, never send anything, never place an order.

## Order of sources — cheapest and most trusted first

1. **SCPRS** (`market_product_search`, `market_last_sales` if available): who has sold this
   item to a California agency already, at what price and when. A prior seller is a supplier
   lead and a price reference.
2. **Business Central** (`bc_find_item`): does BBS already stock or sell it. If yes, stop and
   say so — the rep does not need a scout.
3. **Firecrawl**, when its tools are present: `firecrawl_search` for the manufacturer's part
   page and "where to buy" pages; `firecrawl_scrape` to read a specific page; `firecrawl_agent`
   for a deep multi-source pass on a genuinely obscure item (set `maxCredits` to 500; it runs
   async — kick off, then poll `firecrawl_agent_status`).
4. **`WebSearch` and `WebFetch`** always available. Search the exact part number in quotes,
   then the manufacturer's site, then distributor sites. Fetch the page before you trust a
   snippet.

## Rules that never bend

- **A price is valid only from a page you actually fetched, with its URL and today's date.**
  Search-result snippets and shopping widgets are wrong often enough to be dangerous. If you
  did not fetch the page, the price cell is `null` with the note "not fetched".
- **Never a Grainger price from the web.** Grainger pricing is account-specific and comes from
  `grainger_price` against the buying institution's own account, run by the rep's skill, not
  by you. If Grainger carries the item, say "Grainger carries it (SKU X) — price via account"
  and leave the price cell `null`.
- **Rank credibility:** manufacturer's own store or authorized distributor (verified on the
  manufacturer's "where to buy" page) > B2B wholesaler with a real address and phone > retail
  marketplace (Amazon, eBay — benchmark only, never preferred).
- **Never fabricate.** No part number, MOQ, lead time, or contact you did not read. Unknown is
  `null`.
- **Correct the premise when it is wrong.** If the part number does not match the description,
  say so first and offer the likely intended item.

## Output — exactly this shape

Start with two lines: **Item as understood** (your restatement, any correction) and **BBS
history** (BC + SCPRS findings in one sentence each, or "none").

Then the table, one row per supplier, best option first:

| Supplier | Role | Part # / SKU | Price (unit) | Price source (URL, date) | MOQ | Lead time | Contact path | Notes |
|---|---|---|---|---|---|---|---|---|

`Role` is one of: manufacturer, authorized distributor, wholesaler, marketplace. Unknowns are
`null`, never blank, never guessed.

Finish with **Alternates** (equivalent items, one line each, with why they qualify) and **What
the rep should do next** (one or two sentences: which supplier to email first, what to ask).

Keep the whole answer under 40 lines. The rep reads it between two other tasks.
```

- [ ] **Step 2: Edit `plugins/bbs-website/skills/bbs-sourcing/SKILL.md` Step 5c** — replace the
  heading and first paragraph:

```markdown
### 5c. Search online for new vendors

Do this when the BBS directory doesn't cover the item, or when the rep wants more options for a high-dollar line.
```

  with:

```markdown
### 5c. Scout suppliers for items the directory doesn't cover

Do this when the BBS directory doesn't cover the item, or when the rep wants more options for a high-dollar line. Dispatch the `supplier-scout` agent (bbs-sales plugin) with the line item, quantity, and buying agency; it checks SCPRS and Business Central first, then the web (Firecrawl when assigned, `WebSearch`/`WebFetch` otherwise), and returns a supplier-options table with every price tied to a fetched URL and date. Rank its rows with the credibility list below before presenting them.
```

  Leave the credibility ranking and the "Present web-found vendors to the rep for approval"
  sentence as they are.

- [ ] **Step 3: Validate** — `claude plugin validate plugins/bbs-sales` and
  `claude plugin validate plugins/bbs-website` → both pass. Confirm the agent frontmatter parses:
  `head -6 plugins/bbs-sales/agents/supplier-scout.md` shows `name`, `description`, `model`,
  `disallowedTools`. Check the bbs-website manifest: if `plugins/bbs-website/.claude-plugin/plugin.json`
  declares an `"agents"` field, add the same field to bbs-sales' plugin.json pointing at
  `./agents/`; if it does not (agents auto-discover from `agents/`), add nothing.

- [ ] **Step 4: Commit**

```bash
git add plugins/bbs-sales/agents/supplier-scout.md plugins/bbs-website/skills/bbs-sourcing/SKILL.md plugins/bbs-sales/.claude-plugin/plugin.json
git commit -m "feat(bbs-sales): supplier-scout agent — SCPRS/BC first, Firecrawl or WebSearch, prices only from fetched pages; bbs-sourcing 5c dispatches it"
```

(If plugin.json was not modified, drop it from the `git add`.)

---

### Task 7: Docs sweep — runbook, registry, backlog, execution log

**Files:**
- Modify: `docs/ADMIN-RUNBOOK.md` (§1 step 3, §3a)
- Modify: `docs/superpowers/plans/2026-09-13-v1.1-backlog.md` (mark shipped)
- Modify: `REGISTRY.md` (supplier-scout note on `bbs-suppliers` row unchanged; add nothing else)
- Modify: `plugins/bbs-sales/README.md` (agent mention in the skills/commands area)

- [ ] **Step 1: ADMIN-RUNBOOK §1 step 3** — after the Desktop-app send-test sentence, add:
  `Ask Claude to open Chrome and search a product — expect it to run without a permission prompt (the browser tool is on the managed allow list).`
  Re-wrap to ≤100 cols.

- [ ] **Step 2: ADMIN-RUNBOOK §3a** — add a step between the current 3 (Teams post) and 4
  (pilot): `Post \`scripts/bbs-setup.ps1\` in the same Teams post; reps run it before anything else (REP-SETUP step 1).` Renumber.

- [ ] **Step 3: Backlog** — in `docs/superpowers/plans/2026-09-13-v1.1-backlog.md`, add a
  section at the top (after the intro paragraph):

```markdown
## Shipped in v1.1 (branch `v1.1`, 2026-09-13) — see `2026-09-13-rep-workspace-v1.1.md`

Commons (superpowers-chrome, caveman, Anthropic document-skills) as pinned marketplace entries
with `docs/COMMONS.md`; browser tool on the managed allow list; `scripts/bbs-setup.ps1`
bootstrap; bbs-sales guard hooks (renames, near-duplicate folders, FILLED immutable, precedent
at session start); `supplier-scout` agent wired from `bbs-sourcing` 5c. Still open below:
Firecrawl scope, unsourced-price Stop hook, community skills, statusline meter, bbs-sourcing
move, headless runner, precedent index, evals, BC swap.
```

- [ ] **Step 4: bbs-sales README** — in the section listing commands (`## Commands`), add one
  line after the table or list: `Agent: \`supplier-scout\` — supplier options for an item BBS has never sourced; dispatched by \`bbs-sourcing\` step 5c or directly ("find supplier options for MSA 10082709").`

- [ ] **Step 5: Validate** — `awk 'length > 100 && !/^\|/' docs/ADMIN-RUNBOOK.md plugins/bbs-sales/README.md docs/superpowers/plans/2026-09-13-v1.1-backlog.md` prints nothing (or only pre-existing table rows).

- [ ] **Step 6: Commit**

```bash
git add docs/ADMIN-RUNBOOK.md docs/superpowers/plans/2026-09-13-v1.1-backlog.md plugins/bbs-sales/README.md
git commit -m "docs(v1.1): runbook browser check + bootstrap post; backlog marks shipped items; bbs-sales README lists supplier-scout"
```

---

### Task 8: Full validation, push the branch, merge instructions

**Files:** none new.

- [ ] **Step 1: Validation sweep**

```bash
claude plugin validate . --strict
claude plugin validate plugins/bbs-foundations
claude plugin validate plugins/bbs-sales
claude plugin validate plugins/bbs-website
python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo ok
python -m json.tool plugins/bbs-foundations/docs/bbs-managed-settings.json > /dev/null && echo ok
python -m json.tool plugins/bbs-sales/hooks/hooks.json > /dev/null && echo ok
powershell -NoProfile -ExecutionPolicy Bypass -File plugins/bbs-sales/hooks/tests/run-tests.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bbs-setup.ps1 -DryRun
git ls-files --eol $(git diff --name-only main..HEAD) | grep -v "i/lf" || echo "eol ok"
```

All pass, all `i/lf`.

- [ ] **Step 2: Push the branch only**

```bash
git push -u origin v1.1
```

- [ ] **Step 3: Leave Parker the merge instruction** (chat, and the summary at the end of this
  plan's execution log):

```bash
# after the v1 pilot passes:
git checkout main && git pull && git merge --no-ff v1.1 && git push origin main
# then on one machine: /plugin marketplace update, restart, /bbs-checkup, try "open Chrome and find MSA 10082709"
```

---

## Self-review notes

- **Coverage vs rulings:** commons (Tasks 1–3), browser allow (3), caveman (1, 3), CLI tools
  (4), hooks 1/2/3/7 (5), supplier-scout (6), docs (7). Deferred items are named in the design
  notes and the backlog section (Task 7).
- **Placeholders:** none; every file has full content. The only runtime-variable value is
  `${CLAUDE_PLUGIN_ROOT}`, substituted by Claude Code.
- **Consistency:** hook script names match between `hooks.json`, tests, and README;
  `supplier-scout` name matches the agent frontmatter, the 5c text, and the README line;
  package IDs in `bbs-setup.ps1` were verified with `winget show --exact` on 2026-09-13.
