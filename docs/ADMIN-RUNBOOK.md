# Admin runbook — Parker's operating manual

Everything the solo admin does, with exact steps. Companion: REP-SETUP.md (rep side),
MEASUREMENT.md (metrics), ADMIN-CLEANUP.md (one-time machine cleanup).

## 0. Prerequisites (before ANY deployment)

1. **Push `main`** from the admin machine (`git push origin main`). Every artifact below — the
   plugins, `/bbs-checkup`, the workspace file — reaches machines only via the marketplace, and
   the marketplace serves whatever is on `main`. Nothing in §1–§3 works against an unpushed repo.
2. **Rotate the two leaked keys** (found 2026-09-11): Firecrawl (dashboard → new key) and
   Grainger gateway (issue new; place per machine in `~/grainger-api/mcp/.env`, readable by
   your user only — Windows: keep it out of shared/synced folders). Strip old values from
   `~/.claude/settings.local.json` and `~/.claude/remote-settings.json` per ADMIN-CLEANUP.md.

## 1. Push managed settings (the deployment step that has stalled twice)

1. Open claude.ai → admin settings → Claude Code → managed settings.
2. Paste `plugins/bbs-foundations/docs/bbs-managed-settings.json` (review MANAGED-SETTINGS.md
   "Before pasting" first).
3. On ONE machine: restart Claude Code, run `/status` (managed source should win), `/mcp`
   (Grainger, BC, SCPRS, CRM, M365 connectors all listed — they come from the admin console,
   not from settings),
   then `/plugin marketplace update` and `/bbs-checkup`. **Live-fire the draft-first rail:**
   ask Claude to send you a test email — expect a permission denial, not a send (`/permissions`
   should list the managed deny entries). Deny rules on wrong tool names fail silently, so
   this test is not optional. Repeat it once on the pilot rep's machine. Repeat the send test once
   in the Desktop app as well — managed settings govern both surfaces; confirm rather than assume.
   Then run `/context` and record the startup context size (managed CLAUDE.md + plugin skill
   descriptions + MCP tool schemas) in the deployment note; if MCP tool schemas dominate, trim
   connector assignments per role (§3) before rollout.
4. Only after that machine is green: tell the reps to restart Claude Code.

## 2. Enable analytics (one-time)

claude.ai → admin settings → Claude Code → enable analytics dashboard + spend report.
Add the monthly reading to the metrics review (MEASUREMENT.md).

## 3. Connector assignments (one-time, then per new hire)

Per the matrix in MANAGED-SETTINGS.md: everyone gets BC MCP (Custom API, read-only, interim),
M365, Grainger, Sales CRM; CA-book reps add SCPRS; BC Chat Connector is retired — unassign it;
Supabase/Shopify/Vercel/QuickBooks stay admin-only.

## 3a. First-deployment sequence (once, in this order)

1. §0 → §1 → §2 → §3 above, on the admin machine.
2. **Stamp the desk-root CLAUDE.md** on the pilot machine from `workspace/DESK-CLAUDE-template.md`
   (`/bbs-claude-md init` at the desk root, or `ca-rfq-intake`'s `scaffold_folder_context.py
   --dry-run` then `--write` for per-buyer folders). `/bbs-checkup` check 6 expects it.
3. Post `workspace/bbs-rep.code-workspace` + the REP-SETUP link in the Teams sales channel;
   pin it; add the first-open screenshots to that post.
4. Pick the pilot rep and date. Gate: rep runs `/bbs-checkup` clean, logs one real RFQ,
   produces one packet, unaided. Record PASS/FAIL in `docs/acceptance/YYYY-MM-DD-<initials>.md`.
5. Start ADMIN-CLEANUP.md on both admin machines.
6. Capture the baseline this month (MEASUREMENT.md) — the window closes.
7. Inventory the BBS Marketing SharePoint folder and locate Joey's skill — feeds the
   bbs-marketing plugin decision in v1.1.

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
| Rep "Claude got weird" after an update | Check FLAGS for a spike; consider revert; it's a heightened-review week |
| Plugin didn't update | `/plugin marketplace update`, restart; check git push actually landed |
