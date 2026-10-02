# Admin runbook — Parker's operating manual

Everything the solo admin does, with exact steps. Companion: REP-SETUP.md (reps: VS Code,
Mac and Windows), CURSOR-SETUP.md (maintainer guide for later; not rep onboarding),
MEASUREMENT.md (metrics), ADMIN-CLEANUP.md (one-time machine cleanup).

## 0. Prerequisites (before ANY deployment)

1. **Push `main`** from the admin machine (`git push origin main`). Every artifact below — the
   plugins, `/bbs-checkup`, the workspace file — reaches machines only via the marketplace, and
   the marketplace serves whatever is on `main`. Nothing in §1–§3 works against an unpushed repo.
2. **Rotate the two leaked keys** (found 2026-09-11): Firecrawl (dashboard → new key) and
   Grainger gateway (issue new; place per machine in `~/grainger-api/mcp/.env`, readable by
   your user only — Windows: keep it out of shared/synced folders). Strip old values from
   `~/.claude/settings.local.json` and `~/.claude/remote-settings.json` per ADMIN-CLEANUP.md.

## Parker's control surface (ruled 2026-10-01, R4)

Everything that can be set centrally is set from Parker's machine and reaches every rep
without the rep touching a settings file. Nothing is merged into a rep's own
`~/.claude/settings.json`; `/bbs-checkup` only verifies.

| What | Where it is set | How it reaches each machine |
|---|---|---|
| Plugins, marketplace, permissions (allow and deny), env, company CLAUDE.md | Managed settings — `plugins/bbs-foundations/docs/bbs-managed-settings.json` | The admin-console paste (§1) |
| Connectors (Grainger, Business Central, Microsoft 365, SCPRS, Sales CRM) | Org connector assignment | The claude.ai account (§3) |
| Signature PNGs | OneDrive `MASTER/Signatures/` (§3b) | OneDrive sync |
| Local tools (Git Bash, Python and its PDF libraries, Node, pdftotext, LibreOffice) | The bootstrap — `scripts/bbs-setup.ps1` / `scripts/bbs-setup.sh` | Once per machine |

### Onboarding a new person, step by step

1. **Roster and profile.** Add them to `plugins/bbs-sales/references/vendor_profile.json`
   `authorized_representatives` (name, title, email — from the M365 directory and their own
   signature, never inferred) and, if counsel's authorization covers them, to
   `signature_delegation.delegates`, in a PR. `signature_image` stays `null` for now.
2. **Signature PNG.** They send it to the spec in §3b; drop it in `MASTER/Signatures/`, then
   set their `signature_image` in a second small PR (or the same one, once the file is there).
3. **Connectors.** Assign their account the connectors their role needs (§3).
4. **Managed settings.** Re-paste `bbs-managed-settings.json` (§1) if it changed since the
   last paste. It is the same file for everyone, so a new person needs no edit to it.
5. **Their machine.** They run the bootstrap once (`docs/REP-SETUP.md` step 1), restart VS
   Code, then run `/bbs-checkup` and send you the report. Every line should be ✅; the
   signature line says whether their own PNG resolved.

## 1. Push managed settings (the deployment step that has stalled twice)

1. Open claude.ai → admin settings → Claude Code → managed settings.
2. Paste `plugins/bbs-foundations/docs/bbs-managed-settings.json` (review MANAGED-SETTINGS.md
   "Before pasting" first).
3. On ONE machine: restart Claude Code, run `/status` (managed source should win), `/mcp`
   (Grainger, BC, SCPRS, CRM, M365 connectors all listed — they come from the admin console, not
   from settings), then `/plugin marketplace update` and `/bbs-checkup`. **Live-fire the
   send rail:** ask Claude to send you a test email — expect an Allow prompt, not a silent
   send; approve it and check it arrives (`/permissions` should list the send tools under
   Ask). Rules on wrong tool names fail silently, so this test is not optional. Repeat it once on the pilot rep's machine. The Desktop
   app's **Code** tab is tested after the console blocks in §3, not here: there connectors
   arrive from the app and our ask and deny rules are not documented to match. **Cursor Agent chat is not covered by this deny list.** The stamped
   `.cursor/rules/bbs-invariants.mdc` is the control there; do not treat a Claude Code
   send-denial as proof Cursor cannot send. Ask Claude to open Chrome and search a product — expect it to run without
   a permission prompt (the browser tool is on the managed allow list). Then run `/context` and
   record the startup context size (managed CLAUDE.md + plugin skill descriptions + MCP tool
   schemas) in the deployment note; if MCP tool schemas dominate, trim connector assignments per
   role (§3) before rollout.
4. Only after that machine is green: tell the reps to restart Claude Code.

## 1a. Retire the skill-bus plugin on every existing machine (once, after 2026-09-28)

Ruled 2026-09-28: the third-party `joeymnguyen/skill-bus` plugin is retired. The doctrine
it injected now rides the plugins' own hooks (`plugins/*/hooks/hooks.json`), so nothing
needs wiring — but a repo change cannot uninstall a plugin that is already on a machine,
and a machine that still has it injects the doctrine twice. On the admin machines and
each rep machine, in Claude Code:

1. `/plugin uninstall skill-bus@skill-bus-marketplace`
2. `/plugin marketplace remove skill-bus-marketplace` (the retired marketplace)
3. Delete the per-machine copies the retired plugin made, if present: `~/.claude/skill-bus.json`,
   and at the desk root `.claude/skill-bus.json` and `.claude/skill-bus-telemetry.jsonl`
   (both retired; `.gitignore` keeps a stale one out of a commit).
4. Re-paste managed settings (§1) — the pasted copy no longer registers the marketplace
   or enables the plugin, so a machine that never had it stays clean.
5. `/plugin marketplace update`, restart, `/bbs-checkup`: check 1 always prints one line
   for the retired plugin ("retired plugin absent" is the one you want; "still loaded — see
   §1a" means steps 1–2 did not take) and check 9 finds both `hooks.json` files and every
   doctrine file they name.
   On the first Windows rep machine, run one `bbs-sales:*` skill and confirm the grounding
   doctrine appears once in context — the hook's Windows PowerShell 5.1 path was written to
   that subset but could not be executed by the builder (only pwsh 7 was).

## 2. Enable analytics (one-time)

claude.ai → admin settings → Claude Code → enable analytics dashboard + spend report.
Add the monthly reading to the metrics review (MEASUREMENT.md).

## 3. Connector assignments (one-time, then per new hire)

Per the matrix in MANAGED-SETTINGS.md: everyone gets BC MCP (Custom API, read-only, interim),
M365, Grainger, Sales CRM; CA-book reps add SCPRS; BC Chat Connector is retired — unassign it;
Supabase/Shopify/Vercel/QuickBooks stay admin-only.

**Block the send tools in the console too (ruled 2026-10-02).** In the claude.ai admin
console's connector tool controls, set to `blocked` every connector tool that
`plugins/bbs-foundations/docs/bbs-managed-settings.json` `permissions.deny` names (its
`mcp__claude_ai_<connector>__<tool>` entries; currently the SignNow and QuickBooks
send-class tools). Do **not** block the Outlook and Teams send tools: since 2026-10-02 they
are in `permissions.ask` so Claude can send with a person's Allow, and `blocked` would
remove them everywhere, Claude Code included. A connector the org has not connected has nothing to block yet; when one is connected,
block its send tools here before assigning it to anyone.
Why: the managed deny's connector entries are not documented to match in the Desktop app's
Code tab, and managed settings do not reach Desktop chat or Cowork. The docs say the desktop
app and claude.ai chat apply `blocked`; Cowork is unverified. `blocked` is org-wide: it
removes these tools from every member's chat too, admins included. When a deny entry is
added there, block the same tool here in the same change (ask entries are not blocked). After setting the blocks, ask
Claude in a Desktop app Code session to send you a test email: expect an Allow prompt before
it goes out. If it sends without asking, the Desktop app is not applying our ask rules;
tell the steward, and tell reps to send from VS Code until that is settled.

Those assignments are **claude.ai connectors** (Claude Code, Desktop, and the Claude Code
extension inside Cursor/VS Code). Reps do not use Cursor (ruled 2026-09-28).
Cursor's own Plugins list is a separate surface, Parker/Griffin only: Outlook and Teams
are send-capable and never go on a rep machine (Cursor has no org-wide deny); Supabase /
Vercel / Firecrawl stay Parker/Griffin; never copy `~/.cursor/mcp.json` onto a rep
machine. Role matrix: `docs/CURSOR-SETUP.md`.

## 3a. First-deployment sequence (once, in this order)

1. §0 → §1 → §2 → §3 above, on the admin machine.
2. **Stamp the desk-root CLAUDE.md** on the pilot machine from `workspace/DESK-CLAUDE-template.md`
   (`/bbs-claude-md init` at the desk root, or `ca-rfq-intake`'s `scaffold_folder_context.py
   --dry-run` then `--write` for per-buyer folders). `/bbs-checkup` check 6 expects it.
   On Cursor machines, also copy `.cursor/rules/bbs-invariants.mdc` to
   `{desk}/.cursor/rules/bbs-invariants.mdc` (same file; do not rewrite it). Cursor does
   not load this repo's `AGENTS.md` when the workspace is only the quote-desk folder.
3. Post the `workspace/` catalog + `/bbs-workspaces` (discovers folders on that machine
   and writes Desktop launchers with the BBS logo) in the Teams sales channel; pin it.
   `scripts/bbs-clone-web-stack.sh` is for site maintainers who still need git clones.
4. Post `scripts/bbs-setup.ps1` (Windows) and `scripts/bbs-setup.sh` (Mac) in the same
   Teams post, labelled **Windows PC** and **Mac**; reps run the one for their computer
   before anything else. Each script installs the tools, puts them on PATH, and installs
   every plugin in the marketplace. **Machines set up before 2026-10-01** (Kim, Aanya): post
   the new scripts and have each rep rerun theirs. The earlier version left `soffice`,
   `tesseract` and Git's `bash` off PATH and installed no plugins. Re-paste managed settings
   (§1) too: `bbs-marketing` was added to `enabledPlugins`.
5. Pick the pilot rep and date. Gate: rep runs `/bbs-checkup` clean, logs one real RFQ,
   produces one packet, unaided. Record PASS/FAIL in `docs/acceptance/YYYY-MM-DD-<initials>.md`.
6. Start ADMIN-CLEANUP.md on both admin machines.
7. Capture the baseline this month (MEASUREMENT.md) — the window closes.
8. Inventory the BBS Marketing SharePoint folder and locate Joey's skill — feeds the
   bbs-marketing plugin decision in v1.1.

## 3b. Signature images (once per person, then whenever one changes)

Counsel's authorization lets the six delegates sign for each other on quoting forms under
the limit (`plugins/bbs-sales/references/ca-form-rules.md`, "Delegated signatures"). The
scripts stamp each person's own PNG of record; they never type a name.

**Where:** `MASTER/Signatures/<first>-<last>.png` in the synced `Black Box Safety - MASTER`
library — all lowercase, hyphenated: `jackson-dalton.png`, `parker-marshall.png`,
`griffin-forsyth.png`, `joey-magliato.png`, `kim-quezon.png`,
`aanya-samarasinghe.png`. Nowhere else: Parker's last image lived in a Bechtel RFP folder
and broke when that folder was renamed (2026-09-28).

**The image each person sends:**

- PNG, transparent background, black ink.
- Cropped tight to the ink — no white border, no name or date under it.
- At least 600 px wide.
- Their own signature, signed for this purpose. Never a scan cut from a past bid.

**Turning one on:** drop the file in `MASTER/Signatures/`, then set that person's
`signature_image` in `plugins/bbs-sales/references/vendor_profile.json` to the
`MASTER/Signatures/...` path, in a PR. Until then it is `null`, and that person's lines
come out blank and flagged for a hand signature. One-time move, **before** the PR that
introduced this section merges (it needs no merge, and once reps pull that version a
missing file stops every signed packet): copy Parker's and Jackson's current images to
`MASTER/Signatures/parker-marshall.png` and `MASTER/Signatures/jackson-dalton.png`.

The PNGs are credentials: never commit one, never paste one into a chat, and keep the
folder's sharing to BBS staff.

## 4. Power Automate intake flow (build once)

Flow: trigger = new mail to the quotes mailbox matching CA-agency senders/subjects →
save attachments to `.../State of CA Agencies/_inbox/<sender>-<date>/` → post to the
Teams sales channel. Keep it dumb: no parsing, no AI, just filing + ping. v1: the rep tells
Claude what arrived; an `_inbox/` sweep step lands in `ca-rfq-intake` in v1.1.

## 5. Change discipline (every skill edit or model release)

1. Never let a model update and a skill update reach reps the same week.
2. You are the canary: run the change on your own live work 1–2 days.
3. v1.1+: run the golden set before pushing (see spec, eval suite).
4. Post a two-line change note in Teams, in rep language, naming what to double-check.
5. Bad change = `git revert` + push. Reverting is expected and fine.
6. After any CLAUDE.md or managed `claudeMd` edit: `/context` to confirm it loaded, `/doctor`
   to prune what Claude can derive on its own.

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
| `/mcp` missing Grainger / BC / CRM | Connector not assigned to that user in the admin console (§3). Admin machines only: local `grainger-api` gateway not running |
| Cursor Agent cannot price Grainger | Expected. Pricing connectors live on the Claude Code extension, not Cursor MCP. Open the Claude Code panel; `/mcp` there |
| Rep "Claude got weird" after an update | Check FLAGS for a spike; consider revert; it's a heightened-review week |
| Plugin didn't update | `/plugin marketplace update`, restart; check git push actually landed |
