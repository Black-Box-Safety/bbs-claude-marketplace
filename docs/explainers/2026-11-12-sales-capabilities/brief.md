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

## Status labels on tool rows

- `grainger-promo-page` needs `ca-procurement-intel`; `bbs-rebate-profitability` needs
  `cdata-connect`. Neither is on the standard connector list (`docs/ADMIN-RUNBOOK.md` §3), so both
  carry "ask Parker" rather than being shown as ready.
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
