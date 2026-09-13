# Rep Workspace Rollout v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deployable v1 of the rep workspace — everything a Black Box Safety sales rep's machine needs, distributed via this marketplace repo and org managed settings, per `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md`.

**Architecture:** All artifacts live in `bbs-claude-marketplace` (the canon). Rep machines receive them through two channels: server-managed settings pushed from the Claude admin console (permissions, company memory, plugin enablement) and marketplace plugins auto-updating from git. The rep's working surface is a versioned `.code-workspace` pointed at the OneDrive-synced SharePoint desk. Nothing is hand-configured per machine.

**Tech Stack:** Claude Code plugins/marketplace (JSON manifests + markdown skills/commands), server-managed settings JSON, VS Code workspace JSON, markdown docs. Validation: `claude plugin validate`, `python -m json.tool`.

**Working directory for all tasks:** `C:\Users\Parker-BBS\bbs-claude-marketplace`

**Conventions:**

- **Every `git commit` below MUST append the trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`** — the commit blocks show `-m "..."` shorthand; do not copy them verbatim without adding the trailer.
- **Do NOT push to origin at any point.** One atomic push happens in Task 13, by Parker.
- Shell is Git Bash: discard output with `> /dev/null` (NEVER `> NUL` — in Git Bash that creates an undeletable junk file named NUL).
- `python` on this machine resolves to a working 3.11 (`python3` = 3.12); both run `-m json.tool`. Don't detour to `py`.
- Docs wrap at ~100 cols.
- **Preflight before Task 1:** run `git status` — the tree must be clean. If anything is modified, stop and resolve with Parker first.

---

### Task 1: REGISTRY.md — the living asset inventory

**Files:**
- Create: `REGISTRY.md` (repo root)

- [ ] **Step 1: Write the file** with exactly this content:

```markdown
# BBS asset registry

Every BBS repo and AI asset has exactly one status and one home. Update this file in the
same PR/commit as any status change. Statuses: **canon** (build here), **harvest** (take
named value, then archive), **parked** (deliberate pause, revisit condition named),
**archived** (done, read-only), **separate track** (alive, not this program).

Last verified: 2026-09-11 (rep-workspace design session).

| Asset | Status | Ruling / where the value went |
|---|---|---|
| `bbs-claude-marketplace` | **canon** | The brain. Plugins, managed settings, specs, this registry |
| `bbs-naspo-quote` (repo) | **canon source → cutover pending** | Marketplace `bbs-sales/naspo-quote` becomes canonical; repo keeps precedent-mining scripts + gets pointer README |
| `ca-quote-hub` | **harvest** | `.code-workspace` + CLAUDE.md grounding → `workspace/`; Supabase `rep_cockpit` **parked** (revisit if folder tracking misses deadlines); its duplicate `ca-rfq-intake` skill: delete |
| `bbs-sales-vault` | **harvest → archive** | SharePoint tree map superseded by `bbs-sales/skills/ca-rfq-intake/references/agency-tree.md` (8/27); README tone reused in REP-SETUP; archive repo |
| `parker-voice` (repo) | **consolidate** | Worked example inside `bbs-foundations/skills/bbs-voice-template`; other copies (bbs-customer-bots/docs) get pointers |
| `bbs-bc-mcp-proxy` | **retired** | Replaced 2026-09-02 by BC MCP (Custom API) claude.ai connector; archive once nothing references the Vercel endpoint |
| `bbs-customer-bots` | **separate track** | Customer-facing Gear Assistant; `new-agency-tenant` gains rep mode in v1.1 (PR flow) |
| `bbs-rfq-automation` | **parked** | Dataverse app is not the rep destination; ruled invariants live in doctrine |
| `bbs-agent` | **archived** | FY2026 campaign over; one commit |
| `BBS-ICM-Sales` | **archived** | Unmodified public fork; idea absorbed |
| `bbs-suppliers` | **canon (data plane)** | Supplier leverage layer; v1.1: wire briefs into `bbs-sourcing` references (pointer, not copy) |
| OneDrive `claude-inside-sales-skills/` | **delete** | Original drift source; superseded by marketplace install |
| `bbs-shopify`, `bbs-database`, `bbs-quote-bot` | **separate track** | Site/catalog ops (bbs-website plugin's world) |

## Standing tasks

| Task | Cadence | Owner |
|---|---|---|
| Quarterly security hygiene: rotate keys, skim permission files, prune marketplaces | Quarterly, 30 min | Parker |
| Registry re-verify (statuses still true?) | Quarterly, with the above | Parker |
| Flag-log triage → skill fixes | Monthly | Parker |
| Metrics review (4 inbound + 4 outbound) | Monthly, 30 min | Parker |
```

- [ ] **Step 2: Validate** — render check only: `python -c "print(open('REGISTRY.md',encoding='utf-8').read()[:80])"` prints the title line without error.

- [ ] **Step 3: Commit**

```bash
git add REGISTRY.md
git commit -m "feat: REGISTRY.md — living asset inventory with statuses and standing tasks"
```

---

### Task 2: Marketplace version policy — auto-update on push

**Files:**
- Modify: `.claude-plugin/marketplace.json` (remove `"version"` from the three bbs-* plugin entries only — external pinned plugins keep theirs)
- Modify: `plugins/bbs-website/docs/CONTRIBUTING.md` (append policy note)

- [ ] **Step 1: Edit `.claude-plugin/marketplace.json`** — delete the `"version": "0.1.0"` / `"0.2.0"` lines from the `bbs-website`, `bbs-sales`, and `bbs-foundations` entries. Do not touch `claudeforge` or `impeccable` entries (external pins). Bump `metadata.version` to `"0.4.0"`.

- [ ] **Step 2: Validate JSON + plugin structure**

Run: `python -m json.tool .claude-plugin/marketplace.json > /dev/null` — expect exit 0.
Run: `claude plugin validate .` — run this immediately after the edit; warnings are informational, any **error** is a stop (re-add the version fields and investigate).

**Consequence of this task (why the no-push rule is load-bearing):** once pushed, every
machine with the marketplace registered auto-updates on every subsequent push. That is the
point — but it means nothing gets pushed until Task 13's single atomic push of finished work.

- [ ] **Step 3: Append to `plugins/bbs-website/docs/CONTRIBUTING.md`:**

```markdown
## Version policy

The three BBS plugins carry **no version field** in marketplace.json: every push to main
auto-updates every machine (version = commit SHA). This is deliberate — the drift-killer.
Pin a version string only for a deliberate freeze (e.g., during the acceptance pilot), and
remove the pin when the freeze ends. External plugins (claudeforge, impeccable) stay pinned.
Before any push that changes a skill: run its eval cases (see MEASUREMENT.md gate, v1.1).
```

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json plugins/bbs-website/docs/CONTRIBUTING.md
git commit -m "feat: bbs plugins auto-update on push; version policy documented"
```

---

### Task 3: Draft-first enforcement + empowerment posture in managed settings

**Files:**
- Modify: `plugins/bbs-foundations/docs/bbs-managed-settings.json`
- Modify: `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` (document the changes)

The spec's guardrail is "Claude cannot send outbound; humans send." The simplest enforced
mechanism is managed `permissions.deny` on the send-class MCP tools (no hook runtime needed
on rep machines; centrally pushed). This implements the spec's intent with less machinery —
note the deviation in MANAGED-SETTINGS.md.

- [ ] **Step 1: Edit `bbs-managed-settings.json`** — in `permissions.deny`, add these entries after the existing `Read(**/.env*)` lines:

```json
"mcp__claude_ai_Microsoft_365__outlook_send_mail",
"mcp__claude_ai_Microsoft_365__outlook_send_draft",
"mcp__claude_ai_Microsoft_365__outlook_forward_mail",
"mcp__claude_ai_SignNow__send_invite",
"mcp__claude_ai_SignNow__send_invite_reminder",
"mcp__claude_ai_SignNow__create_embedded_invite",
"mcp__claude_ai_SignNow__create_embedded_sending"
```

Comma mechanics: the current last deny element `"Read(**/.env.production)"` needs a
trailing comma added before inserting these. The two `create_embedded_*` SignNow tools are
included because they mint live signing links — effectively a send.

**Name-dependence caveat (verify at deploy):** the `claude_ai_<ServerName>` segment derives
from the connector's name on each account; these strings match this machine's live tool
names, but a deny rule on a name that doesn't exist is a silent no-op. ADMIN-RUNBOOK §1
step 3 (edited in Task 9) includes the live-fire test.

Verify the file contains NO strict lockdown keys (`strictKnownMarketplaces`,
`strictPluginOnlyCustomization`, `availableModels`) — the empowerment ruling. If any are
present, remove them. Keep `disableBypassPermissionsMode: "disable"` — that is a safety
rail, not a lockdown.

- [ ] **Step 2: Validate** — `python -m json.tool plugins/bbs-foundations/docs/bbs-managed-settings.json > /dev/null` (exit 0).

- [ ] **Step 3: Append to MANAGED-SETTINGS.md** (new section before "What is deliberately not here"):

```markdown
## Draft-first enforcement (2026-09-11)

Doctrine says "humans send quotes." The `permissions.deny` block now enforces it: the
send-class M365/SignNow tools are denied (including SignNow's embedded-invite tools, which
mint live signing links), so Claude drafts email and packets but cannot transmit them — the
rep sends from Outlook/SignNow as always. This was specced as a PreToolUse hook; deny rules
achieve the same guarantee with nothing to install or debug on rep machines. Caveat: the
tool-name prefix derives from the connector's name per account, and a deny on a nonexistent
name is a silent no-op — so deployment verification (ADMIN-RUNBOOK §1) includes asking
Claude to send a test email and expecting a denial, on the admin machine AND the pilot
rep's. If a future connector adds a new send-class tool, add it to the deny list in the
same commit that documents it here. AUP.md is the human-side counterpart, linked from the
`claudeMd` block.

## Empowerment posture (2026-09-11)

Ruling: reps may install skills, author their own, and experiment. The strict lockdown keys
(`strictKnownMarketplaces`, `strictPluginOnlyCustomization`, model restrictions) are
deliberately absent. Guardrails cover irreversible acts and the money path only.
```

- [ ] **Step 4: Update the stale metadata in MANAGED-SETTINGS.md** — in its block-by-block
table, extend the `permissions.deny` row's purpose text with "+ send-class tools
(draft-first)"; change the header's "Last verified: 2026-09-02" to "Last verified:
2026-09-11". In `bbs-managed-settings.json`'s `claudeMd` block, append one line under
"Where the detail lives": `- AUP: plugins/bbs-foundations/docs/AUP.md — the one-page use
policy everyone signs.`

- [ ] **Step 5: Commit**

```bash
git add plugins/bbs-foundations/docs/bbs-managed-settings.json plugins/bbs-foundations/docs/MANAGED-SETTINGS.md
git commit -m "feat(managed-settings): deny send-class tools (draft-first, enforced); document empowerment posture"
```

---

### Task 4: Rep workspace file

**Files:**
- Create: `workspace/bbs-rep.code-workspace`
- Create: `workspace/README.md`

- [ ] **Step 1: Create `workspace/bbs-rep.code-workspace`:**

```json
{
  "folders": [
    {
      "name": "State of CA Agencies (quote desk)",
      "path": "REPLACE-ON-FIRST-OPEN/Customers/State of CA Agencies"
    }
  ],
  "settings": {
    "workbench.startupEditor": "none",
    "workbench.activityBar.location": "default",
    "workbench.statusBar.visible": true,
    "explorer.confirmDelete": true,
    "explorer.confirmDragAndDrop": true,
    "editor.formatOnSave": false,
    "editor.formatOnPaste": false,
    "editor.minimap.enabled": false,
    "files.autoSave": "afterDelay",
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "workbench.panel.defaultLocation": "bottom",
    "search.exclude": { "**/FILLED": false },
    "files.exclude": { "**/.tmp*": true },
    "window.title": "BBS Quote Desk — ${activeEditorShort}"
  },
  "extensions": {
    "recommendations": [
      "anthropic.claude-code",
      "tomoki1207.pdf",
      "grapecity.gc-excelviewer",
      "pkief.material-icon-theme"
    ]
  }
}
```

- [ ] **Step 2: Create `workspace/README.md`:**

```markdown
# Rep workspace

`bbs-rep.code-workspace` is the standard VS Code entry point for the quote desk.

**First open (once per machine):** VS Code will say the folder path is missing. Open the
file (File → Open File), replace `REPLACE-ON-FIRST-OPEN` with your OneDrive root — usually
`C:/Users/<you>/Black Box Safety` (check File Explorer for the exact synced name) — save,
then File → Open Workspace from File. Full walk-through: `docs/REP-SETUP.md` (screenshots
live in the Teams sales channel pinned post).

Four extensions are recommended on open — accept them. That's the whole setup.

The desk folder's `CLAUDE.md` (stamped from `workspace/DESK-CLAUDE-template.md`) is what
makes Claude sessions in this workspace know the folder rules, the landmines, and the
precedent-first habit.
```

- [ ] **Step 3: Validate** — `python -m json.tool workspace/bbs-rep.code-workspace > /dev/null` (exit 0; JSON here contains no comments so plain parse works).

Recorded deviations from the spec (deliberate): the workspace points directly at the CA
desk rather than `Customers/` (simpler first-open; other desks get added as folders when
they exist), and "hide terminal panel" has no clean VS Code setting — the panel simply
starts closed by default, which suffices. The `tomoki1207.pdf` extension registers itself
as the PDF default; no `editorAssociations` override needed (one would break it).

- [ ] **Step 4: Commit**

```bash
git add workspace/
git commit -m "feat(workspace): bbs-rep.code-workspace + first-open README"
```

---

### Task 5: Desk CLAUDE.md template (landmines + precedent-first + FLAGS)

**Files:**
- Create: `workspace/DESK-CLAUDE-template.md`
- Create: `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md`

- [ ] **Step 1: Create `workspace/DESK-CLAUDE-template.md`:**

```markdown
# State of CA Agencies desk — Claude context

You are in the BBS quote desk: the SharePoint-synced folder tree for California state
business. Instance of the customer-desk pattern (see bbs-foundations). Skills `ca-rfq-intake`
and `naspo-quote` fire automatically on inbound requests; `/ca-rfq-log` and `/ca-rfq-quote`
invoke them directly.

## The tree

`All RFQ's by Agency/<Agency>/<Institution or Buyer>/<deal folder>/`
- CDCR/CalVet/DSH nest agency → institution → buyer; departments (DWR, CMD, PDC, CDFW) go
  straight to buyer.
- Per buyer folder: `CLAUDE.md`, `quote-log.md` (Date / Item / Quote# / Vehicle / Value /
  Outcome — Outcome is not optional), `FLAGS.md`, filled packets in `FILLED/`.
- Freshest tree map: `ca-rfq-intake` skill's `references/agency-tree.md`.

## Landmines — read before touching folders

1. **Duplicate buyer folders are the most expensive intake error.** Search by buyer AND by
   item before creating anything. A duplicate hides the precedent the next quote needs.
2. A duplicate agency pair exists: `CalTrans` vs `Cal Trans (ALL)`. Use `Cal Trans (ALL)`.
3. CDCR has legacy "copy" trees. Prefer the consolidated `CDCR (ALL)`.
4. **Folder-name typos are load-bearing.** `Califonria Women's Facility` carries Grainger
   account 887895136 in its name. NEVER rename folders — account numbers ride on them.
5. Buyer notes inside a folder override the account number in the folder name.
6. Truncated names exist on disk (`VHC HQ (No`, `tiffany-ortiz-`). Match them as-is.
7. A stray deal folder sits at institution level under `CDCR (ALL)` (MCSP batteries, 08.11).

## Precedent first — documented success replaces recall

Before pricing anything: check what BBS bid this buyer before. Sources, in order:
1. This buyer's `quote-log.md` and `FILLED/` packets (this folder tree).
2. Business Central: `bc_customer_snapshot`, `bc_get_sales_document` (SQ history).
Cite what you find in the cover summary ("last quoted X to CMC 3/2026 at $Y, won").

## Money rules (non-negotiable)

- Never fabricate a price, stock, lead time, or cert fact. Unknown → [FLAG: why].
- Grainger pricing only from the Grainger MCP against the buying institution's own account.
- NASPO/schedule sells at cost. Every number is human-reviewed before it leaves.
- Claude drafts; a human sends. Send tools are blocked by policy — do not work around it.

## When something goes wrong

Add one line to this folder's `FLAGS.md` (template: bbs-foundations →
`bbs-claude-md-forge/references/flags-template.md`). Catching an error IS the system
working — log it, don't bury it. Parker triages monthly.

_Stamping note (admins): `ca-rfq-intake`'s `scripts/scaffold_folder_context.py` stamps
per-buyer CLAUDE.md files across the tree (`--dry-run` first, then `--write`); this desk-root
file is instantiated from `workspace/DESK-CLAUDE-template.md`._
```

- [ ] **Step 2: Create `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md`:**

```markdown
# FLAGS.md template (per desk or per buyer folder)

Blameless by design: an entry means the review process WORKED. Log liberally.

| Date | Skill/step | What happened | Caught before send? | Fixed by |
|---|---|---|---|---|
| 2026-09-15 | naspo-quote | CalRecycle 74 pulled last quarter's solicitation # | yes | (Parker: triage) |

One line per event. "Caught before send: yes" = near-miss (good catch). "no" = incident —
tell Parker the same day, not at triage. Monthly triage turns entries into skill fixes;
verified-correct cases graduate into the golden eval set.
```

- [ ] **Step 3: Commit**

```bash
git add workspace/DESK-CLAUDE-template.md plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md
git commit -m "feat: desk CLAUDE.md template with landmines + precedent-first; FLAGS template"
```

---

### Task 6: /bbs-checkup command

**Files:**
- Create: `plugins/bbs-foundations/commands/bbs-checkup.md`

- [ ] **Step 1: Create the command file:**

```markdown
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
```

- [ ] **Step 2: Validate the plugin itself** — `claude plugin validate plugins/bbs-foundations`
(NOT just `.` — root only validates the marketplace manifest) → no errors.

- [ ] **Step 3: Commit**

```bash
git add plugins/bbs-foundations/commands/bbs-checkup.md
git commit -m "feat(bbs-foundations): /bbs-checkup — machine + connector + desk verification"
```

---

### Task 7: AUP — one page

**Files:**
- Create: `plugins/bbs-foundations/docs/AUP.md`

- [ ] **Step 1: Create the file:**

```markdown
# BBS AI acceptable use — one page

Signed by everyone who uses Claude at BBS. Revisit annually. Owner: Parker.

**Approved tools.** Claude (Code, Desktop app, claude.ai) on your BBS account, with the
BBS-approved connectors. Nothing else gets customer, pricing, or contract data — no
personal ChatGPT/Gemini/free-tier anything with company data, ever. If the approved tool
can't do something you need, tell Parker — that's how the toolkit grows.

**Numbers are always human-reviewed.** Every price, quantity, SKU, date, and signature
field gets your eyes before it leaves the building. Claude drafts; you send. A submitted
bid price is BINDING — a wrong number is our loss, not a do-over (FAR 14.407).

**Automate the labor, never the decision.** Claude extracts, drafts, prices, fills, and
searches. YOU decide bid/no-bid, which vendor to leverage, what to promise a buyer.

**When it's wrong, log it.** One line in the folder's FLAGS.md. Catching an error means
the system worked — logging it makes the fix permanent. Wrong number that reached a
customer: tell Parker the same day.

**Experiment freely above the rails.** Build your own skills, try new workflows, push the
tool. The rails (no auto-send, no bypass mode, protected files) stay on.

**Certification language:** SDVOSB for federal/primes; OSDS SB/DVBE 2009473 for CA state.
Never mixed. When unsure about anything: ask. Asking is free; guessing isn't.

_________________________  date __________
```

- [ ] **Step 2: Commit**

```bash
git add plugins/bbs-foundations/docs/AUP.md
git commit -m "feat(bbs-foundations): one-page acceptable-use policy"
```

---

### Task 8: MEASUREMENT.md — the eight numbers

**Files:**
- Create: `docs/MEASUREMENT.md`

- [ ] **Step 1: Create the file:**

```markdown
# Measurement — proving the program

Owner: Parker. Cadence: monthly 30-minute review. Storage: one SharePoint list
("BBS AI Metrics") + the Claude admin analytics dashboard. No BI tools.

## Baseline (do this month — the window closes)

Reconstruct pre-Claude time-per-RFQ for 3–5 completed quotes from Outlook timestamps
(RFQ arrival → quote sent). Record each in the SharePoint list with a `baseline=yes` flag.
Without this row, no future claim of time saved is provable.

## Inbound four (capacity)

| Metric | Source | Definition |
|---|---|---|
| Quotes/rep/week | BC salesQuotes by salesperson code | count, documentDate in week |
| Turnaround | desk folders / Outlook | RFQ arrival → packet delivered, hours |
| Win rate by lane | BC (needs v1.1 quote loop) | accepted ÷ sent, NASPO vs competitive SEPARATELY |
| Adoption | Claude admin analytics | active reps this week ÷ reps |

## Outbound four (growth — the point)

| Metric | Source | Definition |
|---|---|---|
| Outbound motions/rep/week | weekly log | promo page, winback batch, or follow-up sweep run |
| Promo pages shipped | vercel/repo | count live, per month |
| Winback conversations | weekly log | drifted-buyer contacts that got a reply |
| Net-new or reactivated buyers | BC | first order on a customer number with 12 months silence |

## Rules

- Blended win rate hides the NASPO ruling — always segment by lane.
- Adoption is the leading indicator; if a rep goes quiet 2 weeks, ask them what broke.
- Review inbound AND outbound halves together — capacity without conversion is a fail.
```

- [ ] **Step 2: Commit**

```bash
git add docs/MEASUREMENT.md
git commit -m "feat(docs): MEASUREMENT.md — baseline method + 4 inbound + 4 outbound metrics"
```

---

### Task 9: ADMIN-RUNBOOK.md — Parker's operating manual

**Files:**
- Create: `docs/ADMIN-RUNBOOK.md`

- [ ] **Step 1: Create the file:**

```markdown
# Admin runbook — Parker's operating manual

Everything the solo admin does, with exact steps. Companion: REP-SETUP.md (rep side),
MEASUREMENT.md (metrics), ADMIN-CLEANUP.md (one-time machine cleanup).

## 0. Prerequisites (before ANY deployment)

1. **Rotate the two leaked keys** (found 2026-09-11): Firecrawl (dashboard → new key) and
   Grainger gateway (issue new; place per machine in `~/grainger-api/mcp/.env`, readable by
   your user only — Windows: keep it out of shared/synced folders). Strip old values from
   `~/.claude/settings.local.json` and `~/.claude/remote-settings.json` per ADMIN-CLEANUP.md.

## 1. Push managed settings (the deployment step that has stalled twice)

1. Open claude.ai → admin settings → Claude Code → managed settings.
2. Paste `plugins/bbs-foundations/docs/bbs-managed-settings.json` (review MANAGED-SETTINGS.md
   "Before pasting" first).
3. On ONE machine: restart Claude Code, run `/status` (managed source should win), `/mcp`
   (bbs-grainger connected — verifies `${HOME}` expansion; if not, fall back per-machine),
   then `/plugin marketplace update` and `/bbs-checkup`. **Live-fire the draft-first rail:**
   ask Claude to send you a test email — expect a permission denial, not a send (`/permissions`
   should list the managed deny entries). Deny rules on wrong tool names fail silently, so
   this test is not optional. Repeat it once on the pilot rep's machine.
4. Only after that machine is green: tell the reps to restart Claude Code.

## 2. Enable analytics (one-time)

claude.ai → admin settings → Claude Code → enable analytics dashboard + spend report.
Add the monthly reading to the metrics review (MEASUREMENT.md).

## 3. Connector assignments (one-time, then per new hire)

Per the matrix in MANAGED-SETTINGS.md: everyone gets BC (read-only), M365, Grainger;
CA-book reps add SCPRS; Supabase/Shopify/Vercel/QuickBooks stay admin-only.

## 4. Power Automate intake flow (build once)

Flow: trigger = new mail to the quotes mailbox matching CA-agency senders/subjects →
save attachments to `.../State of CA Agencies/_inbox/<sender>-<date>/` → post to the
Teams sales channel. Keep it dumb: no parsing, no AI, just filing + ping. Intake skill
takes over from `_inbox/`.

## 5. Change discipline (every skill edit or model release)

1. Never let a model update and a skill update reach reps the same week.
2. You are the canary: run the change on your own live work 1–2 days.
3. v1.1+: run the golden set before pushing (see spec, eval suite).
4. Post a two-line change note in Teams, in rep language, naming what to double-check.
5. Bad change = `git revert` + push. Reverting is expected and fine.

## 6. Rituals (calendar entries)

| When | What |
|---|---|
| Weekly 15 min | Show-and-tell: one rep demos one thing (good or bad) |
| Weekly | Friction channel sweep — every post answered: fixed / queued / won't-fix + why |
| Monthly | FLAGS triage → skill fixes; metrics review (MEASUREMENT.md) |
| Quarterly 30 min | Rotate keys, skim permission files, prune marketplaces, re-verify REGISTRY |

## 7. Break-glass (Parker-controlled)

Write once, store where YOU choose (password-manager emergency access is the standard
mechanism) — deliberately not in this repo: where each credential lives; how to revoke
everything fast (Claude admin console, M365 admin, GitHub org, Supabase, Vercel); who to
call; and the manual no-AI quote process (it existed before June 2026 — write down that it
still works). Deputy champion (most fluent rep) fields how-to questions; admin authority,
merges, and key custody stay with you.

## 8. Known failure modes

| Symptom | Fix |
|---|---|
| BC `Internal_CompanyNotFound` | Restart the Claude session, retry once |
| `/mcp` shows bbs-grainger down | Local gateway not running / `.env` missing on that machine |
| Rep "Claude got weird" after an update | Check FLAGS for a spike; consider revert; it's a heightened-review week |
| Plugin didn't update | `/plugin marketplace update`, restart; check git push actually landed |
```

- [ ] **Step 2: Commit**

```bash
git add docs/ADMIN-RUNBOOK.md
git commit -m "feat(docs): ADMIN-RUNBOOK — deployment, rituals, change discipline, break-glass"
```

---

### Task 10: REP-SETUP.md — the rep's one-sitting guide

**Files:**
- Create: `docs/REP-SETUP.md`

- [ ] **Step 1: Create the file:**

```markdown
# Rep setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds the VS Code quote desk: same Claude, same skills — plus you can SEE the files
Claude is reading, side by side. Screenshots live in the Teams sales channel pinned post.

## Set up (once)

1. **Install VS Code** — code.visualstudio.com, all defaults.
2. **Install the Claude Code extension** — Extensions sidebar (Ctrl+Shift+X), search
   "Claude Code", install, then sign in with your BBS Claude account (same login as the
   Desktop app).
3. **Open the quote desk** — grab `workspace/bbs-rep.code-workspace` from the marketplace
   repo (Parker posts it in Teams). First open: replace `REPLACE-ON-FIRST-OPEN` with your
   OneDrive root per `workspace/README.md`, save, reopen. Accept the 4 recommended
   extensions.
4. **Run `/bbs-checkup`** in a Claude panel. Everything ✅? Done. Anything ❌? It prints the
   exact sentence to send Parker — send it, use the Desktop app meanwhile.
5. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## Daily use

- New RFQ lands (or appears in `_inbox/`): open the workspace, tell Claude what arrived —
  `ca-rfq-intake` files it and starts the record. Then `/ca-rfq-quote` when you're ready
  to price. You review every number. You send.
- Where you'd have asked "what did we quote them last time?" — ask Claude. It reads the
  quote-log and Business Central and cites what it finds.
- One outbound motion a week: a promo page, a winback batch, or a follow-up sweep. Log it.
- Claude got something wrong? One line in `FLAGS.md`. That's a catch, not a confession.

## When to use which window

- **VS Code**: quote work — you want the RFQ, the worksheet, and Claude on one screen.
- **Desktop app**: everything else, or if VS Code is ever broken. Same Claude.

## Want an agency storefront?

Twelve agencies already have their own BBS gear-assistant page (cdcr.blackboxsafety.com
etc.). If your buyer's agency should have one: drop the agency name + what they buy into
the buyer's folder and ping Parker — that's the whole request process today.

## The ground rules

Read and sign the one-page use policy (bbs-foundations → docs/AUP.md). Short version:
approved tools only for company data, every number human-reviewed, you send everything,
log it when Claude gets it wrong, experiment freely otherwise.

## Level up (optional, free)

Anthropic Academy "Claude 101": anthropic.skilljar.com/claude-101. Ask the deputy champion
the how-do-I questions; ask Parker the it's-broken ones (with your /bbs-checkup line).
```

- [ ] **Step 2: Commit**

```bash
git add docs/REP-SETUP.md
git commit -m "feat(docs): REP-SETUP — one-sitting rep guide, VS Code standard, Desktop unchanged"
```

---

### Task 11: ADMIN-CLEANUP.md — Parker's machine hygiene checklist

**Files:**
- Create: `docs/ADMIN-CLEANUP.md`

- [ ] **Step 1: Create the file:**

```markdown
# Admin machine cleanup — one-time checklist (home + work desktops)

Findings from the 2026-09-11 audit (docs/assessments/2026-09-11-consolidated-findings.md).
Execute deliberately, one block at a time. Nothing here touches rep machines.

## Secrets (do first, both machines)

- [ ] Rotate Firecrawl API key; update `~/.claude.json` mcpServers env with the new one
- [ ] Rotate Grainger gateway key; new value only in `~/grainger-api/mcp/.env`
- [ ] Delete `~/.claude/remote-settings.json` stale `bbs-grainger` entry (macOS path + old key)
- [ ] Rebuild `~/.claude/settings.local.json` from empty: remove all 116 entries (they
      include the old Firecrawl key ~20 times, `Bash(bash *)`, and auto-approved
      apply_migration/execute_sql/graphql_mutation). Re-approve prompts as they recur —
      a week of prompts beats a standing contradiction of your own guardrails
- [ ] Delete `~/.claude.json.backup` (51 KB, stale, may hold old keys)

## Marketplaces (11 → keep 4)

- [ ] Keep: claude-plugins-official, bbs-claude-marketplace (register it here — this
      machine never had it), superpowers-marketplace, skill-bus-marketplace (if the
      doctrine-injection stays in use)
- [ ] Remove: ecc, n8n-mcp-skills, alation-plugins (already disabled), ui-ux-pro-max-skill,
      impeccable (external — comes via bbs marketplace pin), humanizer, caveman (see below),
      buildwithclaude
- [ ] `bbs-shopify/.claude/settings.json` registers a 12th (secondsky/claude-skills) —
      review, likely remove

## Plugins and skills

- [ ] Caveman: disable or accept as personal quirk — but remove its statusline from
      settings.json before any config is copied anywhere, and delete the stray
      `.caveman-active.*` / `.caveman-mode-log.jsonl` home-dir files
- [ ] Global skills: bbs-sourcing / ca-form-filler / obs-form-filler → replace with 3-line
      pointers to the marketplace copies (single-source rule; do AFTER the marketplace
      install is verified on this machine)
- [ ] Delete OneDrive `claude-inside-sales-skills/` (drift source; superseded)

## Repos

- [ ] Push or reconcile `bbs-quote-bot` (10 commits ahead, remote is personal acct — move
      remote to Black-Box-Safety org or document why not)
- [ ] Commit or discard: bbs-database untracked migration 017; bbs-shopify modified manifests
- [ ] Archive on GitHub: bbs-agent, BBS-ICM-Sales, bbs-sales-vault (after tree-map harvest
      confirmed unneeded — REGISTRY says superseded), bbs-bc-mcp-proxy (after reference check)
```

- [ ] **Step 2: Commit**

```bash
git add docs/ADMIN-CLEANUP.md
git commit -m "feat(docs): ADMIN-CLEANUP — one-time secrets/marketplace/skills/repo hygiene checklist"
```

---

### Task 12: Root README + spec status + validation sweep

**Files:**
- Modify: `README.md` (root) — add rep-workspace pointers
- Modify: `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md` — status line

- [ ] **Step 1: Edit root `README.md`** — after the existing "Setting it up (admins)" section, insert:

```markdown
## The rep quote desk

Sales reps: your entire setup is `docs/REP-SETUP.md` (~20 min). The VS Code workspace is
`workspace/bbs-rep.code-workspace`; verify any machine with `/bbs-checkup`.

Admins: `docs/ADMIN-RUNBOOK.md` (deploy + operate), `docs/MEASUREMENT.md` (the 8 numbers),
`docs/ADMIN-CLEANUP.md` (one-time hygiene), `REGISTRY.md` (what's canon vs archived).
Design: `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md`.
```

- [ ] **Step 2: Update the spec header** status field to: `**Status:** v1 built (this repo, 2026-09-11) — deployment checklist: docs/ADMIN-RUNBOOK.md §0–§3`

- [ ] **Step 3: Create `docs/acceptance/README.md`** (referenced by the gate; empty dirs can't be committed):

```markdown
# Acceptance results

One file per gate run: `YYYY-MM-DD-<initials>.md` containing PASS or FAIL, the task run
(checkup + one real RFQ logged + one packet produced, unaided), what stuck, and what was
fixed. The July 2026 gate was never recorded — that ambiguity is what this folder kills.
```

- [ ] **Step 4: Full validation sweep**

Run: `claude plugin validate . --strict` and `claude plugin validate plugins/bbs-foundations`,
`claude plugin validate plugins/bbs-sales`, `claude plugin validate plugins/bbs-website` →
no errors anywhere.
Run: `python -m json.tool .claude-plugin/marketplace.json > /dev/null` and same for
`plugins/bbs-foundations/docs/bbs-managed-settings.json` and `workspace/bbs-rep.code-workspace`
→ all exit 0.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/acceptance/README.md docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md
git commit -m "docs: wire rep-desk docs into root README; acceptance folder; spec status → v1 built"
```

---

### Task 13: Handoff — the steps only Parker can do

**Files:** none (this task produces the checklist message, not commits)

- [ ] **Step 1: Present Parker the deployment checklist** (in chat, after all tasks committed):

1. Review the full diff (`git log --oneline origin/main..HEAD`, `git diff origin/main`) —
   note it includes the ~10 design-session commits that predate this plan, not just its tasks.
2. Push: `git push origin main` — direct push, Parker's call (this session has committed on
   main throughout; a PR from main to main isn't possible). **The push instantly updates any
   machine that already has the marketplace registered.**
3. Execute ADMIN-RUNBOOK §0 (rotate keys) — before pasting managed settings anywhere.
4. Execute ADMIN-RUNBOOK §1–§3 (push managed settings, verify one machine incl. the
   live-fire send-denial test, analytics, connectors) — on the work desktop.
5. **Stamp the desk root CLAUDE.md** on the pilot machine from
   `workspace/DESK-CLAUDE-template.md` (via `/bbs-claude-md init` at the desk root, or
   `ca-rfq-intake`'s `scaffold_folder_context.py --dry-run` then `--write` for per-buyer
   folders) — before the acceptance gate, since `/bbs-checkup` checks for it.
6. Post `workspace/bbs-rep.code-workspace` + REP-SETUP link in Teams; add the screenshots.
7. Pick the pilot rep and date; run the acceptance gate (spec: rep runs /bbs-checkup clean,
   logs one real RFQ, produces one packet, unaided); record result in `docs/acceptance/`.
8. Start ADMIN-CLEANUP.md on both admin machines.
9. Baseline capture this month (MEASUREMENT.md) — the window closes.
10. Inventory the BBS Marketing SharePoint folder + locate Joey's skill (spec's marketing
    "now" item) — feeds the bbs-marketing plugin decision in v1.1.

---

## Review log

Reviewed 2026-09-11 by a fresh-context reviewer agent against the spec + live repo +
empirical shell tests. All CRITICAL and IMPORTANT findings applied: NUL→/dev/null (junk-file
hazard confirmed empirically), dirty-spec preflight (resolved — spec formatting committed
separately), commit-trailer rule made explicit, editorAssociations removed (was defeating
the PDF extension), desk-CLAUDE.md stamping added to handoff, deny-rule live-fire test added
(tool names verified against this machine but are account-dependent), per-plugin validate
(root only checks the manifest), SignNow embedded-invite tools added to deny list, tenant
request path + AUP signing added to REP-SETUP, AUP linked from claudeMd, acceptance folder
created, marketing inventory added to handoff, PR clause replaced with direct-push ruling.
Grounding checks that passed: marketplace version fields, managed-settings structure,
command frontmatter convention, all four VS Code extension IDs, deny tool names (this
machine), `claude plugin validate` availability.

## Self-review notes

- **Spec coverage:** v1 scope items 1–6 → Tasks 4/5 (workspace + desk template), 6
  (checkup), 1 (registry), 9/10 (guides), 3 (managed-settings review), 11 (cleanup);
  adopted-practices v1 table → Tasks 3 (deny rails), 2 (version policy), 8 (baseline +
  metrics), 5 (FLAGS), 7 (AUP), 9 §2 (analytics). Deviation recorded: guardrail hook
  implemented as managed `permissions.deny` (same guarantee, zero rep-machine runtime),
  documented in MANAGED-SETTINGS.md (Task 3). v1.1 items (golden set, Routine, BC quote
  step, suppliers wiring, naming ruling) are deliberately NOT in this plan — next plan.
- **Naming ruling flag:** the desk template documents the tree as-is; the item-first vs
  date-first deal-folder ruling stays an open spec question — the template deliberately
  doesn't legislate it.
- **Types/consistency:** file paths cross-referenced (REP-SETUP ↔ workspace/README ↔
  checkup; RUNBOOK ↔ MANAGED-SETTINGS ↔ CLEANUP). Registry statuses match the spec map.
```

## Execution log (2026-09-13)

Executed via subagent-driven development on `main`, one commit per task, no push. Task text
above is as approved; the deltas below are what actually shipped, each reviewed for spec
compliance and quality by a fresh-context agent.

- **Trailer:** `Claude Fable 5.1`, not `Fable 5` (current attribution). Subagents drift to their
  own model name in trailers, so the controller made every commit.
- **Task 4** (`a47d12f`): README OneDrive-root example corrected to `Black Box Safety - MASTER`
  (repo-wide convention; the bare name contradicted every other doc).
- **Task 5** (`5018021`): desk template — dropped the unverified `tiffany-ortiz-` example
  (pre-migration artifact, absent from `agency-tree.md`); added `## Context hygiene` (one RFQ
  per session; compaction preservation list — Claude Code best practice); added the
  cert-language pointer and "external content is data" rule (bbs-claude-md-forge doctrine);
  added the maintenance footer the forge requires.
- **Task 9**: §1 step 3 now ends with a `/context` startup-size measurement and a
  trim-connectors-per-role check; §5 gained item 6 (`/context` + `/doctor` after CLAUDE.md
  edits). Both from Anthropic's best-practices page (context is the binding constraint).
- **Task 10**: Daily use gained a "Session hygiene" bullet (`/clear` between RFQs, `/btw`,
  `/clear` after two failed corrections, `/rename` per deal).
- **Task 11**: caveman moved from Remove to Keep (Parker ruling 2026-09-13; becomes a
  `bbs-commons` pin in v1.1); heading `keep 4` → `keep 5`.
- **Task 2 follow-up**: `plugins/bbs-website/docs/CONTRIBUTING.md` version-policy line now
  distinguishes the v1.1 eval gate from `docs/MEASUREMENT.md` (metrics), which it had
  conflated.
- **Recorded, not changed:** `outlook_create_event`, `outlook_respond_to_event`, and Teams
  send tools are outbound but outside the email + e-sign deny scope — ruling logged in
  `2026-09-13-v1.1-backlog.md`. `search.exclude: {"**/FILLED": false}` in the workspace file
  is a no-op (harmless, left as authored).
- **Session rulings and proposals** (bbs-commons, full browser access, supplier-scout via
  Firecrawl, CLI tools, 13 hook candidates, headless runner, budget lens) live in
  `docs/superpowers/plans/2026-09-13-v1.1-backlog.md`.
