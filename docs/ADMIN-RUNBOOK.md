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
   this test is not optional. Repeat it once on the pilot rep's machine. Then run `/context`
   and record the startup context size (managed CLAUDE.md + plugin skill descriptions + MCP
   tool schemas) in the deployment note; if MCP tool schemas dominate, trim connector
   assignments per role (§3) before rollout.
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
| `/mcp` shows bbs-grainger down | Local gateway not running / `.env` missing on that machine |
| Rep "Claude got weird" after an update | Check FLAGS for a spike; consider revert; it's a heightened-review week |
| Plugin didn't update | `/plugin marketplace update`, restart; check git push actually landed |
