# State of CA Agencies folder migration — debrief

**Prepared 2026-09-11.** The migration sessions themselves ran on other machines (office
Mac / work desktop) and are not in this machine's conversation archive (exhaustively
searched: vector + text + raw grep, zero hits). This debrief is reconstructed from
artifacts: skill files, repo trees, and commit messages. Companion to
`docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md`.

## Timeline (reconstructed)

- **2026-07-24 — ca-quote-hub created.** Its CLAUDE.md documents the pre-migration mess:
  SharePoint bid history at `Customers/<Agency>/…` with the explicit landmine "**CDCR has
  4 duplicate trees — prefer the `CDCR` folder, ignore `copy` variants**." Shipped a
  Supabase pipeline (`rfqs`, `rep_cockpit`) plus a `/ca-rfq-intake` skill that scans
  Outlook and inserts into Supabase — a *different* skill under the same name as today's
  folder-based one.
- **2026-08-11 — bbs-sales-vault scaffolded.** Its `document-store-map.md` ("Observed
  2026-08-11") is the pre-migration snapshot: `Customers/State of CA Agencies/` was
  **flat**, ad-hoc slug folders (`caltrans-rescue-gear`, `chp-ems-rfq`, `julie-wade-book`,
  `emily-aguiar-cmc`, `dustin-noel-731`, `tiffany-ortiz-` — note the truncated trailing
  hyphen), plus `_ARCHIVE-2026-07/` and `_Unfiled/` ("triage debt"). The vault's standard
  for new deals was `yyyymmdd-<customer>-<shortdesc>`.
- **Between 2026-08-11 and 2026-08-27 — the actual migration** into
  `All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`, on another
  machine. No session record exists here.
- **2026-08-27 — bbs-naspo-quote repo created** (2 commits, 4 minutes apart): the skill
  was authored *without* the `All RFQ's by Agency` level, then immediately fixed
  ("Correct the CA folder path: it nests under All RFQ's by Agency"). Vendored into
  `bbs-claude-marketplace` the same day. Built from the CMC metal-detectors run (quote
  900008, 8/27/26) and precedent mining: **~440 PDFs, ~300 classified** (113 CalRecycle
  74, 72 PD 843, 46 quotes…). `references/agency-tree.md` (observed-on-disk map, latest
  deal 08.27) was generated then.
- **2026-09-11 — rep-workspace rollout design** (this repo): marketplace copy becomes
  canonical; duplicate `ca-rfq-intake` to be deleted; bbs-sales-vault harvested→archived;
  Supabase `rep_cockpit` parked in favor of folder tracking + `quote-log.md`.

## (a) Current state of the tree (per agency-tree.md snapshot, ~8/27/26)

~24 agency folders under `All RFQ's by Agency/`, agency folders carrying Grainger accounts
in their names (`CMC - 887895111 - California Men's Colony`). CDCR consolidated as
`CDCR (ALL)` with ~12 institutions; CalVet/DSH/Caltrans/CalFire similar. Legacy slugs
survived the move with old names *inside* the new tree (`caltrans-rescue-gear`,
`chp-ems-rfq`, `dustin-noel-731`).

## (b) Convention in force

`Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`

- CDCR/CalVet/DSH nest agency→institution→buyer; departments (DWR, CMD, PDC, CDFW) nest
  straight to buyer.
- Deal folder = lowercase item + optional vehicle + arrival date
  (`metal detectors naspo 8.27.26`).
- Per buyer folder: `CLAUDE.md` + `quote-log.md` (one row per request:
  Date/Item/Quote#/Vehicle/Value/Outcome). Filled packets go in a `FILLED/` subfolder.
- **Rejected conventions:** the vault's `yyyymmdd-<customer>-<shortdesc>` slug (skill
  explicitly says it "does not apply here"), and the pathless
  `Customers/State of CA Agencies/<Agency>/...` (fixed 8/27).
- **Tension observed:** reps actually name deals `MM.DD - desc - buyer` (date-first) — the
  observed tree is dominated by that form, not the skill's item-first form.

## (c) Landmines — anyone building on these folders must know

1. **Duplicate buyer folders** are "the most common intake error and the most expensive" —
   precedent search misses them. Search by buyer AND by item before creating anything.
2. The CDCR **"4 duplicate trees / copy variants"** problem was never cleaned, only routed
   around.
3. A **duplicate agency pair exists right now**: `CalTrans` (holding
   `caltrans-rescue-gear`) vs `Cal Trans (ALL)` (holding the districts).
4. A stray deal folder sits at institution level:
   `08.11 - Karena Brusatori - Batteries - MCSP` directly under `CDCR (ALL)` — MCSP has no
   institution folder.
5. **Folder-name typos are load-bearing** (`Califonria Women's Facility` carries account
   887895136) — do NOT "fix" names; account numbers ride on them.
6. Truncated names exist on disk: `VHC HQ (No`, `tiffany-ortiz-`.
7. **Buyer notes inside a folder override the account in the folder name.**
8. OneDrive local path varies per machine — unresolved open question in the rollout spec.
9. `_Unfiled/` and `_ARCHIVE-2026-07/` state unknown post-migration.

## (d) Unfinished migration work

- Duplicate `ca-rfq-intake` (ca-quote-hub vs marketplace) still collides — deletion
  planned, not confirmed done.
- `document-store-map.md` harvest into bbs-foundations planned, not done (and it is stale —
  pre-migration).
- bbs-sales-vault archive pending.
- Source-repo cutover of naspo-quote pending.
- `scaffold_folder_context.py` exists to stamp `CLAUDE.md` across the tree but no evidence
  it ran tree-wide.
- Power Automate `_inbox/` intake flow and the nightly duplicate-buyer-folder audit are
  designs only.
- The v1 acceptance gate (a non-Parker rep runs intake+quote unaided) has not been run.

## Implications for the rep workspace (design inputs)

- The desk root `CLAUDE.md` must carry landmines 1–7 verbatim — they are exactly the
  context a rep's Claude session needs before touching folders.
- `/bbs-checkup` (or the nightly audit) should detect duplicate agency/buyer folders —
  the `CalTrans` pair is a ready-made test case.
- The naming-convention tension (item-first vs date-first deal folders) needs a ruling —
  pick the reps' observed date-first form or retrain; a convention nobody follows is worse
  than none.
- `agency-tree.md` is the freshest tree map (8/27) and supersedes the vault's
  `document-store-map.md` (8/11, pre-migration) — harvest the *former*, archive the latter.
