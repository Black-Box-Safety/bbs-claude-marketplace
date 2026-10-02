---
description: Verify this machine's BBS Claude setup end to end — plugins, connectors, desk folder — and say exactly what to tell Parker if something fails.
---

# /bbs-checkup

Run every check below in order. Never skip one because an earlier one failed. Produce the
report format at the end. Read-only: create/modify nothing, send nothing.

## Checks

1. **Plugins.** Confirm the bbs-foundations, bbs-sales, bbs-marketing, bbs-back-office, bbs-website,
   bbs-claude-coach, bbs-tools, claudeforge, impeccable, superpowers-chrome, caveman, and
   document-skills plugins are loaded (their skills appear in your available skills).
   Report each present/absent. For each absent one, run `claude plugin list --json` via Bash
   if `claude` resolves (read-only) and quote that plugin's `errors` text, or say it is not
   installed at all — the cause goes in the Teams line. Fix: rerun `scripts/bbs-setup.ps1`
   (Windows) or `scripts/bbs-setup.sh` (Mac) — its last section installs every plugin in the
   marketplace and prints the error for any that still fails. Then always add one more line for the retired injection
   plugin, whichever way it goes: "✅ retired plugin absent" when nothing named `skill-bus`
   is loaded, or "⚠️ skill-bus still loaded — retired 2026-09-28, see ADMIN-RUNBOOK §1a"
   when it is. That is a WARN, not a FAIL, and you do not uninstall it yourself.
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
   exists beside it and is non-empty. PASS = both parse and every named file exists. FAIL =
   a file missing or a parse error → the fix is `/plugin marketplace update` then restart;
   if it persists, report it. Also check an interpreter resolves — PowerShell
   `Get-Command pwsh, powershell, python3 -ErrorAction SilentlyContinue`, or
   `command -v pwsh powershell python3` — WARN, not FAIL, if none does: the hook fails open
   and the skills run without their guardrail text until one is installed (macOS:
   `brew install powershell`, or the Xcode command-line tools for `python3`). On Windows a
   `python3` found only under `\WindowsApps\` is the Microsoft Store stub and does not
   count as resolving. Windows
   only: `where.exe bash` must resolve too (Git Bash, from `scripts/bbs-setup.ps1`);
   without it Claude Code hands the hook command to PowerShell, which cannot parse it, and
   every skill call shows a hook error — WARN, fix is the bootstrap (REP-SETUP step 1): it
   puts Git's `bin` folder on PATH and sets `CLAUDE_CODE_GIT_BASH_PATH`, which Git's own
   installer does neither of.
   Nothing to wire and nothing to run: the hook is active whenever the plugin is loaded.
10. **Bootstrap tools.** Resolve `node`, `pdftotext`, `pandoc`, and `uv` on PATH
    (`command -v` on macOS; `where.exe` / `Get-Command` on Windows). PASS = all four
    resolve. WARN (not FAIL) for any missing one, naming it and pointing at
    `scripts/bbs-setup.ps1` (Windows, REP-SETUP step 1) or `scripts/bbs-setup.sh` (macOS,
    REP-SETUP step 1). Also resolve `soffice` (LibreOffice): WARN if missing —
    quote-builder PDF export and document-skills conversion need it. A tool can be installed
    and still not resolve: LibreOffice and Tesseract never add themselves to PATH, and a
    window opened before the install keeps the old PATH. The fix is the same either way —
    rerun the bootstrap (it finds installed tools and adds their folders to PATH), then close
    every VS Code window and reopen it.
    Then the libraries the document-producing skills import (form-fill, quote builder,
    reconciliation), using the interpreter `bbs-setup.ps1` installed them into:
    - **Python.** Windows: the first `python` from
      `Get-Command python -CommandType Application -All` whose path is not under
      `\WindowsApps\` (that is the Microsoft Store stub; if it is the only hit, python is
      missing). macOS: `python3`. Run `<that interpreter> -c "import pypdf, fitz, openpyxl"`.
    - **docx.** Resolve it the way `build_quote.js` does — from the script's own folder plus
      NODE_PATH, not from the current folder. Find the installed bbs-sales plugin root (as
      in check 9), then run
      `node -e "require.resolve('docx',{paths:[process.argv[1]]})" "<bbs-sales root>/skills/bbs-quote-builder/scripts"`.
      If bbs-sales is not installed, skip this probe (informational).
    PASS = both exit 0. WARN (not FAIL) for a missing python or a failed import, naming it.
    Windows fix: `scripts/bbs-setup.ps1` — if its last run said `[later]` or `Not done yet`,
    close that PowerShell window, open a new one, run the script again, then reopen VS Code.
    Any OS, docx only: `npm install docx` inside `<bbs-sales root>/skills/bbs-quote-builder`
    (once per plugin update). Mac fix: rerun `scripts/bbs-setup.sh`, which installs the same
    libraries, then quit and reopen VS Code (Cmd+Q) so it reads the new NODE_PATH.

11. **Signature images.** Find the installed bbs-sales plugin root (as in check 9) and read
    its `references/vendor_profile.json` (read-only). Find the synced
    `Black Box Safety - MASTER` folder on this machine (on a Teams-site sync its name carries
    a "… - " prefix; it is the library the desk folder in check 6 lives in). For each person
    in `signature_delegation.delegates`, resolve their `signature_image`: a `MASTER/...`
    path is joined onto that folder. Report one line per person:
    - `null` → "not provided yet" (informational, not a WARN).
    - Path set and the file exists and its first bytes are a PNG header
      (`\x89PNG`, e.g. `python3 -c "print(open(p,'rb').read(8))"` or PowerShell
      `Get-Content -AsByteStream -TotalCount 8`) → PASS.
    - Path set but the file is missing, empty, online-only and will not download, or not a
      PNG → WARN, naming the path. If that person is the one running the checkup (match the
      Microsoft 365 `get_me` email from check 5 to their recorded email), say so plainly:
      "your own signature will not be applied until this file syncs" — fix: in OneDrive,
      right-click `Signatures` → "Always keep on this device"; if the file is not there at
      all, send your PNG to Parker (ADMIN-RUNBOOK §3b).
    Never open, copy or display an image; check presence and header bytes only.

12. **Managed permissions and the form launcher.** Resolve `bbs-fill` on PATH
    (`command -v bbs-fill`; it comes from the `bbs-tools` plugin's `bin/` and exists only
    while that plugin is enabled). Then run `bbs-fill` with no arguments: it must print its
    usage line ("REFUSED — usage: …", exit 64) and run nothing — that is the expected
    answer, and it shows the launcher runs on this machine. Then ask the rep to type
    `/permissions` and read you two things: whether **Allow** lists `Bash(bbs-fill *)`,
    and whether **Deny** lists the Outlook `outlook_send_mail` tool. PASS = `bbs-fill`
    resolves, prints its usage, and both rules are listed. WARN, naming which part failed:
    `bbs-fill` missing → rerun the bootstrap and restart (bbs-tools not installed); a rule
    missing → the managed settings on this machine are older than the current file: restart
    Claude Code, and if it is still missing tell Parker to re-paste them (ADMIN-RUNBOOK §1).
    Never edit any settings file yourself.

## Report format

For each check: ✅ PASS / ❌ FAIL / ⚠️ WARN + one line. Then:

- If everything passed: "Setup healthy. Nothing to do."
- For each FAIL, one copy-pasteable sentence for Teams, e.g.:
  "Parker — /bbs-checkup: Grainger MCP not responding on my machine (check 4), everything
  else passes. — <name>"

Never attempt to fix a FAIL yourself (no installs, no config edits) — the report is the fix.
