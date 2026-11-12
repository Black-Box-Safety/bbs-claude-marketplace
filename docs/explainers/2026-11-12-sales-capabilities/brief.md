# CA desk handbook: brief and grounding

**For:** Parker Marshall, who shares the page.
**Audience of the page:** the California state desk — Kim Quezon, Aanya Samarasinghe, Griffin
Forsyth, Joey Magliato. Daily Claude Code users, not technical.
**Written:** 2026-11-12, dispatched by the steward. Page source: `ca-desk-handbook.html` in this
folder; the published Artifact is a copy, this file and the HTML are the truth.

## What it is

One private page, the long-form companion to the Quote Desk Field Card
(the one-screen version Parker already published). The field card says *what changed this
week*; this page says *everything that is installed and what to say to start each job*. It
builds on `docs/explainers/2026-10-01-team-rollout/` (same navy-and-gold palette and faces) but
is written for the sales desk, not for the back-office roles that page served.

Sections, in order: set up once · the quote path into Business Central · the State of CA
Agencies folder · desk memory · every tool by job (with a filter box) · habits · the rules ·
when it says no · coming.

## Grounding (main at 5ae15f3)

| Page claim | Source |
|---|---|
| File before price; gates; NASPO back half; quote is a BC sales quote; rep releases, prints, proofs, sends | `plugins/bbs-sales/commands/ca-rfq.md` Gates 0–8 |
| Review sheet, approval by name, NASPO price = cost exactly, salesperson from the split, SQ number from BC, proof DVBE 2009473 on state / body armor / CSU / UC, tax | `plugins/bbs-sales/skills/bc-quote-entry/SKILL.md` (gates, §7 Close out) |
| Item cards only for missing numbers, vendor and cost, named review | `plugins/bbs-sales/skills/bc-item-entry/SKILL.md`, `plugins/bbs-sales/README.md` "Writes to Business Central" |
| `whoami` in your own terminal; AADSTS and 401/403 meanings | `bc-quote-entry/SKILL.md` "One-time setup"; `bc-item-entry/references/rep-setup.md` error table |
| Desk memory: phrases, levels, wider-than-buyer marked for Parker, retire, OneDrive copies, refusals, no Allow click | `plugins/bbs-sales/skills/desk-remember/SKILL.md`; `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` R7 A3 |
| Folder tree, per-buyer files, institution level for CDCR/CalVet/DSH, landmines | Desk-root `CLAUDE.md` and `_README.md` on SharePoint (State of CA Agencies), read 2026-11-12; `ca-rfq-intake/SKILL.md` |
| Session-start precedent, flags and notes; first-write close-out list; guards (no rename, no near-duplicate, FILLED/ immutable) | `plugins/bbs-sales/hooks/hooks.json`, `hooks/guard-tree.py` |
| Setup steps, one RFQ per session, `/rename`, read-outside-folder answer, "Always keep on this device" | `docs/REP-SETUP.md`; `plugins/bbs-sales/README.md` setup §4; `bbs-checkup.md` check 9 |
| Allow prompt for `bbs-fill` → No, restart, `/bbs-checkup` | Quote Desk Field Card (Parker); `MANAGED-SETTINGS.md` (bbs-fill is allow-listed, so a prompt means a broken install) |
| Tool rows | Each skill's `description:` and `requires:`; `python3 scripts/check_marketplace.py --requirements` |
| "Coming" | `plugins/bbs-sales/README.md` (monthly roll-up, marking old notes); `docs/REP-SETUP.md` (`_inbox/` once Parker's intake flow is live) |

## Added 2026-11-12 at Parker's request (in session)

Parker: make it the one-stop page for Claude and the sales process, include the CA state
dashboard work, tell Joey how to replicate it, and make the goal plain: enable more outbound,
lead-generated sales.

| Page claim | Source |
|---|---|
| Goal band and the outbound section; "one outbound motion a week" | Parker, in session, 2026-11-12; `docs/REP-SETUP.md` "Daily use"; `plugins/bbs-sales/README.md` "The territory, before the RFQ" |
| State purchasing records (SCPRS) for targeting, with the slice label | Organization instructions; `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` connector matrix (everyone reads); `ca-territory-handoff/SKILL.md` |
| Quote Velocity: what it shows, counted by CRM submitted date, no win rate or target, live and private until shared | SharePoint `State of CA Agencies/docs/dashboards/quote-velocity/README.md`, read 2026-11-12 |
| RFQ Pipeline: stages, sections, inferred label, privacy rules; built, in review, not shared | SharePoint `docs/dashboards/rfq-pipeline/README.md` (status as of 2026-11-03), `brief.md`, `STAGE-RULES.md` |
| One-time catch-up prompt is coming | SharePoint `rfq-pipeline/REP-NOTE-rollout-draft.md` (marked HOLD) and `REP-PROMPT-howto.md` |
| Desk-root folders (`docs/`, `sales-process/`, `Business Development/`, `Weekly Summaries/`) | SharePoint folder listing, 2026-11-12 |
| Joey: what transfers, what he can set up, what needs a build | Skill descriptions (`bc-item-entry`, `bc-quote-entry`, `desk-remember` "outside this desk"); company memory R6 (customer-folder `CLAUDE.md`, no quote log outside the CA desk); `hooks.json` (guards key on the tree) |

The pipeline status is from a README dated 2026-11-03. If it has gone live since, change its
label from Coming to Live and add the link.

## Dashboard work: where it lives (pointer map, 2026-11-12)

Parker, in session, 2026-11-12: "The dashboard and quote log should be connected. I want to move
from the CRM being the statement of record to our folders." That is decision 9.1 of the
folder-first spec. The handbook states it as the direction; it is not yet written into the
rulings register in `docs/STEWARD.md`, the desk `CLAUDE.md` or `ca-state-sales-grounding`.

| What | Where |
|---|---|
| Design (folder owns working state, CRM owns existence and submitted date, BC owns money; phases 1 to 5; Parker's seven decisions) | `docs/archive/superpowers/specs/2026-10-30-rfq-pipeline-folder-first-design.md` (scrubbed repo copy; working original in the MASTER store under `State of CA Agencies/docs/superpowers/specs/`) |
| Phase 1, the record: parser, CLI, hook, v1 migration | Merged: #77 (`plugins/bbs-sales/scripts/rfq_record.py`, `hooks/rfq-record-hook.py`) |
| Outcome close-out on first write in a deal folder | Merged: #75 (`hooks/desk-context.py`) |
| Phase 2, the RFQ Pipeline page: scanner, calcs, page, harness, privacy gate, charter, copy, metric sign-off | MASTER store, `State of CA Agencies/docs/dashboards/rfq-pipeline/` (README is the status page; last status read: 2026-11-03, reviewed build not yet published) |
| Quote Velocity (counts by CRM submitted date) | MASTER store, `State of CA Agencies/docs/dashboards/quote-velocity/` |
| Program: roster (Otto, Rhea, Dara, Quinn, Reese, Dex), decisions D01 to D04, build log, learnings | MASTER store, `State of CA Agencies/sales-process/` (`roles/`, `docs/pm/`, `BUILD-LOG.md`, `docs/LEARNINGS.md`) |
| Sessions | "CA State RFQ pipeline: clean data and go live" (2026-11-03 to 11-04); "BBS #77 RFQ record v2" (2026-11-11); steward "BBS Claude marketplace cleanup" |
| Not built | Phase 3 (skills write stages into `RFQ.md`), phase 4 (dashboard buttons and `/ca-rfq-fold` into `RFQ.md` and `quote-log.md`), the scheduled refresh (staged off), the reps' one-time catch-up (on hold) |

What "connected" means today: the scanner reads each deal's `RFQ.md` and the buyer's
`quote-log.md` (`STAGE-RULES.md`, evidence order), so a quote-log outcome reaches the page at the
next manual refresh. The write direction, dashboard to quote log, is phase 4.

## Status labels on tool rows

- `bbs-rebate-profitability` needs `cdata-connect`, which is not on the standard connector list
  (`docs/ADMIN-RUNBOOK.md`), so it carries "ask Parker". `grainger-promo-page` needs SCPRS
  (`ca-procurement-intel`), which everyone reads, so its earlier "ask Parker" label was removed.
- `sam-gov-opportunities` needs the shared SAM.gov key set by the setup script (`-SamGov`); the
  page names Kim and Griffin, as `docs/REP-SETUP.md` does.

## Deliberately left off

- `bbs-website` skills and agents (site maintainers, not reps), `bbs-deck-voice` (Parker's federal
  deck voice), `/bbs-commons-add` and the agent-team skills (maintainer work).
- The CA State Sales Ops roster on SharePoint (Rhea, Otto, Dara and others): role docs for a
  program, not tools a rep invokes. Rhea's charter was read for desk detail only.
- Any real folder name, buyer, account number, price, RFQ or SQ number. Every example is invented
  and the page says so.

## Found while grounding, for Parker

- The desk-root `CLAUDE.md` on SharePoint still names `/ca-rfq-log` and `/ca-rfq-quote`, which
  `/ca-rfq` retired. Restamp it from `workspace/DESK-CLAUDE-template.md` if the template is current.
