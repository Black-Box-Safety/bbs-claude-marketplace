---
description: Verify this machine's BBS Claude setup end to end — plugins, connectors, desk folder — and say exactly what to tell Parker if something fails.
---

# /bbs-checkup

Run every check below in order. Never skip one because an earlier one failed. Produce the
report format at the end. Read-only: create/modify nothing, send nothing.

## Checks

1. **Plugins.** Confirm the bbs-foundations, bbs-sales, bbs-back-office, bbs-website,
   bbs-claude-coach, claudeforge, impeccable, superpowers-chrome, caveman, and
   document-skills plugins are loaded (their skills appear in your available skills).
   Report each present/absent. If a plugin named `skill-bus` is still loaded, report it as
   ⚠️ WARN with the sentence "retired 2026-09-28 — Parker uninstalls it per
   ADMIN-RUNBOOK §1a"; it is not a FAIL and you do not uninstall it.
2. **Marketplace freshness.** Run `claude plugin marketplace list` via Bash if available;
   note whether bbs-claude-marketplace is registered. If the command is unavailable, say so.
3. **Business Central connector** (BC MCP Custom API, interim — tool names change at the
   Microsoft swap). Call `bc_get_company_info` (read-only). PASS = company name returns.
   FAIL modes: tool absent (connector not enabled for this account) or error
   (if `Internal_CompanyNotFound`, the fix is: restart the Claude session, retry once).
4. **Grainger MCP.** Call `grainger_search` with query "3M 8511". PASS = results return.
   FAIL = tool absent (connector not assigned to this account) or connection error.
5. **Microsoft 365 connector.** Call `get_me`. PASS = the rep's own name/email returns.
6. **Desk folder.** Verify the directory `All RFQ's by Agency` exists under the workspace
   folder (list directories; Glob matches files, so check the folder itself, e.g. by listing
   its children). PASS = present with children. Also check a `CLAUDE.md` exists at the desk
   root.
7. **Duplicate-agency scan.** List directories directly under `All RFQ's by Agency/`.
   Flag any pair whose names normalize to the same string ignoring case/spaces/`(ALL)`
   (known live pair: `CalTrans` vs `Cal Trans (ALL)` — expected until Parker merges them;
   report it as KNOWN, new pairs as NEW).
8. **OneDrive sync health.** Note the desk folder's most recently modified file and its
   timestamp; if nothing changed in 7+ days on a weekday-active desk, flag possible sync
   stall (informational, not FAIL).
9. **Doctrine hooks.** For each of the bbs-foundations and bbs-website plugins, locate its
   installed root (`claude plugin list` via Bash, or the plugin's path in `/plugin`), then
   confirm: `hooks/hooks.json` parses as JSON (read it; a Python or PowerShell parse if
   available), and every file named in `hooks/doctrine/subscriptions.json` under `inserts`
   exists beside it and is non-empty (four in all: `bbs-claude-md-doctrine.md`,
   `bbs-grounding-doctrine.md`, `bbs-storefront-doctrine.md`, `bbs-catalog-doctrine.md`).
   PASS = both parse and all four exist. FAIL = a file missing or a parse error → the fix is
   `/plugin marketplace update` then restart; if it persists, report it. Also check that
   `pwsh` or `powershell` resolves (`Get-Command pwsh, powershell` / `command -v`): WARN,
   not FAIL, if neither does — the hook fails open and the skills run without their
   guardrail text until PowerShell is installed (macOS: `brew install powershell`).
   Nothing to wire and nothing to run: the hook is active whenever the plugin is loaded.
10. **Bootstrap tools.** Run `where.exe node pdftotext pandoc uv` via Bash (or PowerShell
    `Get-Command`). PASS = all four resolve. WARN (not FAIL) for any missing one, naming it and
    pointing at `scripts/bbs-setup.ps1` (REP-SETUP step 1).

## Report format

For each check: ✅ PASS / ❌ FAIL / ⚠️ WARN + one line. Then:

- If everything passed: "Setup healthy. Nothing to do."
- For each FAIL, one copy-pasteable sentence for Teams, e.g.:
  "Parker — /bbs-checkup: Grainger MCP not responding on my machine (check 4), everything
  else passes. — <name>"

Never attempt to fix a FAIL yourself (no installs, no config edits) — the report is the fix.
