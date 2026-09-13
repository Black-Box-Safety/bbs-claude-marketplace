---
description: Verify this machine's BBS Claude setup end to end — plugins, connectors, desk folder — and say exactly what to tell Parker if something fails.
---

# /bbs-checkup

Run every check below in order. Never skip one because an earlier one failed. Produce the
report format at the end. Read-only: create/modify nothing, send nothing.

## Checks

1. **Plugins.** Confirm the bbs-foundations, bbs-sales, and bbs-website plugins are loaded
   (their skills appear in your available skills). Report each present/absent.
2. **Marketplace freshness.** Run `claude plugin marketplace list` via Bash if available;
   note whether bbs-claude-marketplace is registered. If the command is unavailable, say so.
3. **Business Central connector.** Call `bc_get_company_info` (read-only). PASS = company
   name returns. FAIL modes: tool absent (connector not enabled for this account) or error
   (if `Internal_CompanyNotFound`, the fix is: restart the Claude session, retry once).
4. **Grainger MCP.** Call `grainger_search` with query "3M 8511". PASS = results return.
   FAIL = tool absent (MCP not configured) or connection error (local server down).
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

## Report format

For each check: ✅ PASS / ❌ FAIL / ⚠️ WARN + one line. Then:

- If everything passed: "Setup healthy. Nothing to do."
- For each FAIL, one copy-pasteable sentence for Teams, e.g.:
  "Parker — /bbs-checkup: Grainger MCP not responding on my machine (check 4), everything
  else passes. — <name>"

Never attempt to fix a FAIL yourself (no installs, no config edits) — the report is the fix.
