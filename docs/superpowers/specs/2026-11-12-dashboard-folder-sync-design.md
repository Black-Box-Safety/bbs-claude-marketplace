# RFQ Pipeline dashboard and deal folders: two-way sync design

Status: **design ruled, nothing built.** Parker confirmed every recommendation in section 12 on
2026-11-12 (recorded in `docs/STEWARD.md`, "Already open for Parker"). Each mechanism stays a
proposal until its slice's PR lands. Date 2026-11-12. Owner: Parker Marshall. Builds on
`2026-10-30-rfq-pipeline-folder-first-design.md` (sections 5.1-5.7, 8, 9, 13), which this document
amends it in the places listed in section 0.1.

## 0. The ruling this design starts from

Parker, 2026-11-12, in session: "The dashboard and quote log should be connected. I want to move from
the CRM being the statement of record to our folders." That decides question 9.1 of the folder-first
spec:

- **The deal folder** (`RFQ.md`, written only through `rfq_record.py`, plus the buyer's
  `quote-log.md`) is the record of working state, **including sent and outcome**.
- **Business Central** stays the record of money (quote totals, orders, invoices).
- **The CRM** is no longer the pipeline record. It becomes a read-only cross-check, then history.

And the ask: "A user can log something as sent in the dashboard or save it to the folders and it goes
each way. Data from the dashboard and folders should reinforce each other. There can be mismatches
now, but going forward we want to ensure there's consistency."

### 0.1 What this amends in the folder-first spec

- 5.3 and 5.4: `sent` no longer comes from the CRM submitted date; the CRM is a cross-check only.
- 5.4: the page's deal key is an opaque key, not the tree path (decision 4).
- 5.6: the fold is person-run (`/ca-rfq-fold`), not the weekday routine, and writes through
  `record-event`.
- 9.1: settled by the ruling above, with sent and outcome moved from the CRM to the folder. That scope
  goes beyond what 9.1 assumed, so the ruling still has to be recorded in the STEWARD register
  (decision 0).

## 1. How this was produced

One round of five viewpoints, run in parallel and read-only, then a synthesis by this session, then an
independent review by Rex against `AGENTS.md` (verdict and fixes in the PR, not here). The viewpoints:

| Viewpoint | Charter | Question it answered |
|---|---|---|
| Rhea (RFQ desk) | `sales-process/roles/` Rhea role doc | How sent and outcome reach `RFQ.md` and `quote-log.md` with no double chore |
| Dara (pipeline build) | Dara role doc; dashboard README, STAGE-RULES, CHARTER-pages | The dashboard mechanism and what the artifact runtime can do |
| Quinn (metrics) | `METRICS-SIGNOFF.md` | Who owns each fact, conflict rules, drift prevention, CRM demotion |
| Sales rep (stand-in for `bbs-sales:sal`) | the rep's day | What the two CA-state reps actually do on a Tuesday |
| `bbs-plugin-github-expert` | plugin craft and the checker | Files that change, PR slices, merge order |

`bbs-sales:sal` is not an agent type this session can spawn, so a general-purpose agent took the
rep's viewpoint from the same brief. Where viewpoints disagreed, section 9 says which way the synthesis
went and why.

## 2. What is true today (verified 2026-11-12)

- The live RFQ Pipeline artifact is a Claude Dashboard typed artifact still holding the **S3** page.
  **S6** is built and unpublished. Its attached data is from the 2026-11-02 scan, stale under its own
  48-hour rule. (Dara, read-only read of the artifact; SharePoint README.)
- The scanner refresh routine exists only as `staged/ca-rfq-pipeline-refresh/SKILL.md`. It is not
  registered and nothing runs on a timer. (Confirmed: folder listing of
  `docs/dashboards/rfq-pipeline/` on SharePoint.)
- The page's only "sent" signal is the CRM submitted date. CRM status is never read as an outcome.
- `rfq-pipeline/` also holds `REP-PROMPT-log-submissions.md` (a catch-up prompt that reads the rep's
  own Outlook Sent mail) and `REP-PROMPT-staging-format.md` (the staging file it writes).
- **Parser gap 1:** `set_stage` (`plugins/bbs-sales/scripts/rfq_record.py:440`) refuses a backward
  move but **silently overwrites** the date and evidence of a stage already set. That breaks the v2
  rule "a correction is a new Evidence note, not a silent rewrite". `--force` leaves no trace.
- **Parser gap 2:** `set_stage` lets `outcome` be written while `sent` has no date.
- **Vocabulary drift:** `rfq_record.OUTCOMES` includes `no bid`. `desk-context.py:40` `FINAL` is
  `won|lost|no answer`, and the quote-log template wording omits `no bid`. A No bid deal would be
  listed for close-out forever.
- **No code writes `quote-log.md`.** Rows are hand-written, have no deal key, author or timestamp, and
  the Outcome cell mixes the value with free text.
- **Doctrine still names the CRM as the pipeline record** in several places: `canonical-facts.md`
  "Systems of record", the managed-settings template, `ca-rfq-intake/SKILL.md`, `naspo-quote/SKILL.md`,
  `bbs-weekly-sales-report/SKILL.md`, `bbs-daily-rep-summary`, `ca-territory-handoff`, and the
  organization instructions and deployed managed memory ("Dynamics 365 for pipeline").

## 3. Principles

1. **One owner per fact; every other store is evidence for it.** No fact has two writers.
2. **One write path into the folder.** Every entry point, whether a dashboard click, a rep in chat or
   a Sent-mail match, becomes a *proposed event*. One CLI call applies it to `RFQ.md` and
   `quote-log.md` together.
3. **Evidence proposes; a person decides.** Nothing inferred (Sent mail, BC order, CRM, SCPRS) becomes
   sent or outcome without a rep's approval by name. Approval is batched so that it costs one line,
   not one line per deal.
4. **Never silent.** A disagreement is shown and listed. It is never resolved by overwrite.
5. **No new chore.** A rep records nothing the system can already see. They confirm it.

## 4. Who owns which fact (proposal)

| Fact | Owning store | Who writes it | How other stores learn it |
|---|---|---|---|
| Sent date | `RFQ.md` Status `sent` row | `rfq_record.py record-event`, applied by `/ca-rfq-fold` or in a `/ca-rfq` session after the rep approves | Parser rewrites `rfq-state.json`; the scanner carries it to `rfqs.json`; the dashboard decision is marked folded; the `quote-log.md` row is patched in the same call. CRM and BC learn nothing. |
| Outcome (`won`, `lost`, `no answer`, `no bid`) | `RFQ.md` Status `outcome` row | Same path | Same; the quote-log Outcome cell carries the enum value only. |
| Stage | `RFQ.md` header `Stage` (highest dated Status row) | Skills through the parser only (spec 5.3) | `rfq-state.json`, then the scanner. Inferred stages never reach sent or outcome. |
| Lines and pricing | `RFQ.md` Pricing table | Pricing and sourcing skills through `upsert-pricing` | Scanner to `rfq_lines.json`. Once a BC quote exists, its lines are the binding copy. |
| Quote value | Business Central sales quote total (excl. tax) | BC-Write-API after the rep approves (existing rule) | Page reads BC live by key, else the BC-import snapshot, else the Pricing sum. Each value is labelled with its source. Never the CRM value, and never copied into `quote-log.md` by the fold. |
| BC quote number | Business Central; `RFQ.md` `**BC quote:**` holds the key | Set when the quote is read back from BC | Scanner. A number found only in a filename is shown as "probable". |
| BC order on the quote | Business Central | BC | Shown on the page and proposed to the rep as `won`. Never written as an outcome on its own. |
| CRM RFQ key | `RFQ.md` `**CRM RFQ:**` | Read-only lookup at intake | Scanner; used only for the cross-check during demotion. |
| Decision audit (who clicked, when, what) | Dashboard database decision document | The page, on click | `/ca-rfq-fold` reads it; the folded `RFQ.md` Evidence carries its key. |

## 5. Both directions

### 5.1 Dashboard to folder (proposal)

1. **Click.** The drawer offers Mark sent (date input, default today Pacific, no future dates),
   Won, Lost, No answer, No bid. A click writes a decision document (5.4) and the page shows it at
   once with the chip "recorded on the dashboard, not yet in the folder".
2. **Fold.** At the start of the rep's next desk session, a SessionStart line says "3 dashboard
   decisions to fold: run /ca-rfq-fold". `/ca-rfq-fold` reads that rep's pending decisions, reads each
   deal's `RFQ.md` through the parser, and shows one review sheet:
   `deal · field · record now · proposed · source · clicked by · at`.
3. **Approve by name, once per batch.** The rep replies `approve fold, 3 rows, <rep name>` and may
   drop rows by number. "Yes" or "looks good" does not count.
4. **Apply.** For each approved row, `rfq_record.py record-event` writes the Status row and patches
   the `quote-log.md` row in one call (5.3). Then, and only then, the decision is marked `folded`.
5. **Round trip to the page.** `/ca-rfq-fold` ends by offering a rescan and re-upload of the touched
   deals, with the person's approval, so the page reflects the folder within minutes instead of
   waiting for the next refresh.

**Latency:** the clicker sees the click at once. The folder has it at the next fold, offered the same
day. Other viewers see it after the fold and rescan (or at once, under the shared-collection option in
decision 3).

**Fallback if the page cannot write to the database** (spike pending, 5.4): the drawer button copies
`/ca-rfq-fold sent <deal8> 2026-11-12` to the clipboard, the way "Pick up this RFQ" does, and the rep
pastes it into their own session. The same approval and the same CLI apply. No database is needed.

### 5.2 Folder to dashboard (proposal)

A sent date or outcome written in the folder, whether by a `/ca-rfq` session, the catch-up prompt's
staging fold or `/ca-rfq-fold`, is in `rfq-state.json` immediately (the PostToolUse hook compiles it).
It reaches the page by **the scanner**, which reads `rfq-state.json` and builds `rfqs.json`:

| Path | How fast |
|---|---|
| Fold in a session, with the rescan it offers | Minutes |
| Weekday refresh routine, once Parker switches it on | Next 07:00: up to about 24 hours, about 66 over a weekend |
| Today (routine staged off) | Whenever someone runs the scan by hand |

When the scan shows a folder value and a pending decision agree, the page treats the decision as folded
(the scanner reads `decisions_applied` from the sidecar, 5.3), so the artifact database never needs a
second write. When they disagree, the page shows a conflict chip and lists it in Record health. It does
not pick one.

### 5.3 The one write path: `record-event` (proposal)

New CLI command in `plugins/bbs-sales/scripts/rfq_record.py`:

```
rfq_record.py record-event <RFQ.md> sent|outcome --value <enum> --date YYYY-MM-DD
    --source dashboard|sent-items|rep-stated|bc-order --by <person> --approved-by <person>
    --decision-id <key> [--correct "<reason>"] [--dry-run]
```

- Writes the `RFQ.md` Status row first. Evidence carries source, by, at and the key, for example
  `won - dashboard, <rep>, 2026-11-12T10:41-08:00 [dec:3f9a1c2e]` (fictional).
- Then rewrites `rfq-state.json` (the parser already does this after every write).
- Then patches the buyer's `quote-log.md` row through a new stdlib module `quote_log.py`. The row is
  found by deal key, else by the BC or PC quote number. With no match it refuses; the review sheet
  proposes adding a row. It never matches by date proximity.
- Adds `decisions_applied` (the keys) to `rfq-state.json`.
- **Idempotent:** the same key already in Evidence means `RFQ.md` is skipped and only `quote-log.md`
  is re-checked. A run that died between the two writes can therefore be finished by running it again.
  Two files cannot be written atomically, so a failed second write fails loudly and names the file.
- Never writes the quote-log Value column; money belongs to BC.
- Refuses while a OneDrive conflict copy of either file exists (spec 13.4).

### 5.4 Dashboard mechanism (proposal; Dara)

**What the artifact runtime can do** (Dara, from the type docs and the stored declaration):
- **Can:** keep a database per artifact that survives republishes, updates live for open viewers,
  knows the viewer's identity, and offers a short lease.
- **Cannot:** transactions or version-checked writes on those documents (last writer wins, and a
  retried update can apply twice), read SharePoint or `RFQ.md` live (folder facts arrive only as
  uploaded files), or run on a timer.
- **Open, needs a spike** on a throwaway Dashboard artifact, never the live one: whether the Dashboard
  type's page script can reach the database at all (its documented page scripts expose `d3` and `dash`,
  and `dash` has no write verb). Also unconfirmed: whether a typed artifact's database rules can be
  changed.

**Collection, recommended per rep:** `data/users/<self>/decisions/<deal8>.<field>`. Here `deal8` is
an opaque 8-hex deal key (Dara reports the built S6 page uses one for `#rfq-` links; not verified here, so treat it as part of the proposal). It is **never the folder path**, because
buyer folder names carry buying-account numbers. `/ca-rfq-fold` resolves it locally through
`deal_paths.json`, which stays off the published page (spec 13.6).

Fields: `deal8, field, value, date, by (user id), at, status (pending | folded | held | rejected),
hold_reason, key = hash(deal8|field|value|date), supersedes`.

- One document per deal and field, so a second click replaces the first.
- A click after a fold that changes the value goes back to `pending` with `supersedes`. The fold then
  shows it as a correction.
- Per rep keeps reps at Viewer or Contributor, not Editor, and matches the own-session rule: each rep
  folds their own clicks. The cost is that until a click is folded and rescanned, only the clicker sees
  it. The alternative is a shared root collection, which needs every rep to be an Editor (decision 3).

### 5.5 What the page shows for a click not yet folded (proposal)

- **Deal row and drawer timeline:** a chip, "Sent 11/12, recorded on the dashboard, not yet in the
  folder".
- **Tiles:** they count the record only, with a floor note ("+1 recorded on the dashboard"). They never
  mix the two silently. Quinn signs the tile definition.
- **Record health:**
  - decisions pending more than one business day;
  - decisions held as conflicts;
  - decisions held with `no record`, meaning the deal has no `RFQ.md`. The fold never creates one.
- **Header:** "Folder data as of <scan time>", so a stale page is visibly stale.

## 6. Consistency going forward

### 6.1 Write-time checks (parser, proposal)

- **Same stage, same date, same evidence:** no-op. A repeated fold changes nothing.
- **Same stage, different date:** refused with `conflict` unless `--correct "<reason>"` is given. A
  correction appends to Evidence (`corrected from <old> to <new> by <who> <when>: <reason>`). It never
  replaces it.
- **`outcome` without a dated `sent`:** refused, except `no bid`.
- **`sent` date:** not before `Received`, and not after today in Pacific time.
- **`--force`:** writes `forced by <who> <when> from <stage>` into Evidence. Record health counts these
  notes.
- **The quote-log hook:** the existing `rfq-record-hook.py` also validates `quote-log.md` under the
  tree. A bad table shape, or a bad row carrying a `[dec:` marker, exits 2. Legacy hand-written rows
  only warn, so months of history do not block work.

### 6.2 Fold-back safe to run twice

Covered by the key in Evidence plus `decisions_applied` in the sidecar (5.3). The order of the steps is
fixed:

1. `RFQ.md`
2. sidecar
3. `quote-log.md`
4. mark the decision folded

A failure at any step leaves the decision `pending`, and a rerun completes it. The parser refuses some
decisions. Each of those becomes `held` with the reason and is shown on the page; it is never dropped.

### 6.3 A timestamp and an author on every fact

Every Status Evidence cell written through `record-event` carries `source, by, at` and, from a fold,
the decision key. The new quote-log rows carry `Source`, `By` and `Recorded` columns (6.5).

### 6.4 Stages never move backward

- **Parser:** unchanged rule, plus the `--force` trace.
- **Page:** shows the later of the record stage and a pending decision, never the earlier. A pending
  decision at or below the record stage shows one of two chips: "already in record" when it matches, or
  "conflict: record says lost" when it does not. In either case it stays held.
- **Date fill (proposal):** filling a missing `sent` date on a deal already at `outcome` leaves the
  header Stage unchanged. Today `set_stage` refuses it as backward, so slice 3 adds an explicit
  exception: a lower stage may get a date only when its row is empty and the date is not after the
  higher stage's date, with a test. Never through `--force`.

### 6.5 quote-log.md becomes a copy written by the CLI (proposal)

Proposed columns going forward:

`| Date | Deal | Item | Quote # | Vehicle | Value | Sent | Outcome | Outcome ref | Source | By | Recorded |`

- **Deal:** the path below `All RFQ's by Agency/` with buying-account numbers written `[acct]`. This
  is the join key.
- **Outcome:** blank until decided, then exactly one of `won`, `lost`, `no answer`, `no bid`. `sent`
  lives only in the Sent column, so one fact is not held twice.
- **Outcome ref:** PO number, who won, or `n/a`.
- **Value:** stays whatever intake wrote. The fold never touches it.
- **Older rows** are left as written.
- **Same PR:** the template (`buyer-context-template.md`), `desk-context.py` and `.ps1` (`FINAL` gains
  `no bid`) and `hooks/tests/parity.py` change together (invariant 3).
- **Single source for the outcome list:** `rfq_record.OUTCOMES`. The PowerShell twin is held to it by a
  parity fixture.

## 7. Sent-date sources: which wins (proposal)

| Rank | Source | Role |
|---|---|---|
| 1 | Outlook Sent mail: first message to the buyer's address carrying the quote, Pacific date | Strongest evidence of the date. Proposed to the rep, never applied by itself. Visible only in the signed-in rep's own session, because Claude cannot see a teammate's mailbox. |
| 2 | Rep statement: dashboard click or "sent it today" in chat | The only source for portal, Provision Connect or form submissions that leave no email. Evidence says "rep stated". |
| 3 | CRM submitted date | Cross-check only, while the CRM is being demoted (section 8). |
| 4 | BC `sentDate` | Ignored. BBS never sends from BC, so it is blank or a button date. Cross-check only if it ever fills reliably. |

- **Rank** decides what is *proposed*. The **first date written stays** unless the rep approves a
  `--correct`.
- A same-day "Mark sent" click later confirmed by a Sent-mail match is shown on the fold sheet as
  "evidence to add". Like every other write to `RFQ.md`, it lands only with the batch approval.
- A disagreement of more than one business day goes on the reconciliation or Record health list. It is
  never overwritten.

**Outcome sources:**
- `won`: a rep statement, or a BC order on the quote shown as a hint and folded only after approval.
- `lost` and `no bid`: the rep only.
- `no answer`: proposed on the close-out list once the silence threshold passes (decision 5), and
  folded only with approval.
- **CRM Won/Lost and SCPRS awards:** shown beside the outcome, never as it.

## 8. CRM demotion order (proposal)

Quote Velocity counts submissions weekly from the CRM submitted date. The order keeps that count whole
until the folders can carry it:

1. **Now: the Pipeline page stops reading the CRM as a source.** The CRM submitted date moves to the
   drawer as "CRM said ..." and into Record health when it differs by more than a day. Quote Velocity
   is unchanged. (The separate Quote Velocity redesign session is not touched by this design.)
2. **Back-fill.** Each rep runs the existing catch-up prompt once over their own Sent mail for open
   deals. The staged rows fold through `/ca-rfq-fold`. The one-time reconciliation report (section 10)
   clears the rest.
3. **Short parallel run.** Reps record sent on the dashboard (or by confirming Sent-mail matches) and
   still click CRM Submitted. Quote Velocity adds a "folder sent vs CRM submitted" line per rep per week
   under its Logging gaps.
4. **Switch.** When both counts agree within 1 per rep per week for the agreed number of weeks and at
   least the agreed share of in-scope deals carry a recorded sent date (decision 6), Quote Velocity
   counts from the folder `sent` date. CRM-only rows show as "unrecorded". Earlier weeks keep their CRM
   counts, and the page states the switch date.
5. **Stop.** Reps stop clicking CRM Submitted, the day after the switch.
6. **Doctrine.** The canon, skill lines and template that name the CRM as the pipeline record are
   updated in the first repo PR (section 11, PR 1). The organization instructions and the deployed
   managed memory are **Parker console actions**. No agent edits them.

## 9. Human gates, and keeping them light (proposal)

| Path | Where approval by name sits | How it stays light |
|---|---|---|
| Dashboard click to folder | `/ca-rfq-fold` review sheet, one phrase per batch | Offered at session start only when something is pending; rows can be dropped |
| Sent-mail match to folder | Same sheet, source `sent-items` | Matches arrive pre-filled; the rep only confirms |
| Rep says it in a `/ca-rfq` session | The same phrase, in that session | No context switch |
| BC order proposed as won | Same sheet | Shown with the SO number as evidence |
| No answer after silence | Weekly close-out list, same phrase | One batch a week |
| Reconciliation rows | The report, approved by row or by group | One-time |
| Rescan and re-upload after a fold | One yes | Optional; the refresh routine does it otherwise |

**Disagreements settled in synthesis:**
- **Should sent from Sent mail fold with no approval?** The rep viewpoint said yes, to remove a chore.
  Rhea and Quinn said no. Synthesis: **no for now**, because the batch phrase costs one line. Revisit
  after 30 folds with no error (decision 2).
- **Should silence auto-close as No answer?** The rep viewpoint said yes, with a chance to object.
  Rhea said never automatic. Synthesis: **proposed and batched, never automatic** (decision 5).
- **CRM Submitted click:** the rep viewpoint said retire it now, to avoid the double chore. Quinn said
  run in parallel until Quote Velocity can switch. Synthesis: a **short parallel run with an explicit
  exit test** (decision 6). The back-fill is what keeps it short.

## 10. Existing mismatches: one-time reconciliation report (proposal)

A read-only report, built in a desk session by a person with access to BC, the CRM and their own Sent
mail. **Nothing is corrected automatically.** One row per deal and fact where stores disagree:

`deal8 · buyer (no account numbers) · fact · RFQ.md value (by/at) · pending decision · quote-log · BC (quote, order) · CRM (keyed or probable) · Sent-mail hit · proposed value · basis (keyed | probable) · action [accept | keep record | mark unknown | park] · approver · approved at`

Groups:

- (a) sent with no record;
- (b) dates disagree by more than a day;
- (c) quote-log Outcome free text that cannot be read as an enum value;
- (d) a BC order with no outcome;
- (e) a deal with no CRM key, or a CRM record with no folder (matched one to one);
- (f) a BC-import value with no `BC quote` key.

Each approved row becomes a decision with `by` set to the approving rep and folds through the normal
path. A "probable" row never moves a stage without that approval.

Fictional example: deal `a1b2c3d4` "Valves 10.2.26"; RFQ.md sent blank; CRM probable 10/03; Sent mail
10/02 with the quote PDF attached; proposed sent 10/02 from Sent mail; action accept; approver: the
rep.

The report is not a script in this repo: a local script cannot reach BC or the CRM, and spec 13.7's
Record health already owns the comparison. It is a run of Record health in "full history" mode,
written to the rep's session for review.

## 11. Build slices, in merge order (proposal; each is one draft PR)

| # | Slice | Changes | Done when |
|---|---|---|---|
| 1 | `docs:` canon and doctrine | `canonical-facts.md` systems of record; managed-settings template; `ca-rfq-intake`, `naspo-quote`, `bbs-weekly-sales-report`, `bbs-daily-rep-summary`, `ca-territory-handoff` lines naming the CRM as pipeline record | Checker exits 0; the PR body lists the Parker console actions |
| 2 | `fix:` outcome vocabulary | `desk-context.py` and `.ps1` `FINAL` gains `no bid` from one source; template wording; parity fixture | Parity and unit tests pass; a `no bid` row is no longer listed as stale |
| 3 | `fix(rfq-record):` parser checks | Section 6.1 checks in `set_stage`; `--correct`; `--force` trace; conflict-copy refusal; date-fill exception (6.4); tests with placeholder fixtures | Same-stage rewrite refused; repeated identical write is a no-op; outcome-before-sent refused; date fill allowed only into an empty lower row |
| 4 | `feat:` quote-log module and `record-event` | New `scripts/quote_log.py`; `record-event`; `decisions_applied` in the sidecar; template columns (6.5); `outcome-closeout.md` and `ca-rfq-intake` step 5 write through the CLI | Tests cover rerun after a half-write, refused overwrite, no-match refusal, Value untouched |
| 5 | `feat:` quote-log check in the record hook | `rfq-record-hook.py` matches `quote-log.md`; `.ps1` notice; `parity.py`; `hooks.json` description | A bad marked row exits 2; a legacy row warns; the `.ps1` notice is asserted |
| 6 | `feat:` `/ca-rfq-fold` | New `commands/ca-rfq-fold.md`; reads an exported decisions file (or the clipboard form); review sheet; approval phrase; applies through `record-event`; offers the rescan | A dry run on three placeholder decisions writes nothing before approval and lands all five buttons |
| 7 | Outside the repo (SharePoint) | Database spike on a throwaway Dashboard; S6 publish and privacy gate; drawer capture block; scanner reads `decisions_applied`; Record health additions | Monday's click is in the folder and on the page the same day after a fold |

Every touched skill and command keeps `requires: [python3]`. If `/ca-rfq-fold` reads the artifact
database directly instead of an exported file, that needs a new system in the checker's registry, and
the checker belongs to the review side. Reading an exported file avoids that.

Dependency Dara named, not verified here: the S6 publish and its privacy gate come before slice 7.

## 12. Decisions only Parker can make

**RULED 2026-11-12:** Parker, in session: "I confirm your recommendations." Every item below is
ruled as recommended. Item 10 remains a console action for Parker; item 9 takes effect only after
slice 7 passes.

Recommendation first on each.

0. **Record the 2026-11-12 ruling in the register.** *Recommend: Parker records it in `docs/STEWARD.md`
   as RULED, with its scope: the folder owns working state including sent and outcome, BC owns money,
   the CRM is a cross-check until the Quote Velocity switch (decision 6).* Slice 1 does not change
   canon before that entry exists.

1. **Is the fold person-run?** *Recommend: yes, `/ca-rfq-fold` in the rep's own session, with approval
   by name per batch.* An unattended routine would edit binding records with no approval. At most a
   routine *proposes* the batch, and it stays staged off.
2. **Does a dashboard click, or a Sent-mail match, count as the approval itself?** *Recommend: no for
   now.* The click is the rep's statement and the fold phrase is the approval. Revisit after 30 folds
   with no error.
3. **Where do dashboard decisions live?** *Recommend: per rep (`data/users/<self>/decisions`), reps
   stay Viewer or Contributor,* after a spike on a throwaway artifact proves the page can write. The
   alternative is a shared collection, which needs reps to be Editors. If the spike fails, use the
   clipboard command (5.1) and no database.
4. **The deal key on the page.** *Recommend: an opaque 8-hex key, resolved locally through
   `deal_paths.json`; never the folder path.* This settles the conflict between spec 5.4 (deal_id = path)
   and 13.6 (paths stay local) in favour of 13.6.
5. **No answer.** *Recommend: proposed on the close-out list 30 days after sent (45 for competitive
   bids), folded only with the batch approval; never automatic.*
6. **When Quote Velocity switches and CRM Submitted stops.** *Recommend: after 2 consecutive weeks where
   folder sent and CRM submitted agree within 1 per rep per week and at least 90% of in-scope deals since
   the back-fill carry a recorded sent date. Reps stop clicking CRM Submitted the next day.* Quinn
   suggested 4 weeks; 2 is recommended because the back-fill does most of the work.
7. **quote-log.md columns change** (6.5), which touches the template, `desk-context` and its parity
   tests. *Recommend: yes, going forward only; older rows untouched.*
8. **A value for a cancelled or no-award solicitation.** *Recommend: add `cancelled` to the outcome
   enum, in one place (`rfq_record.OUTCOMES`), with a checker fixture.* Until ruled, the fold refuses to
   map a cancellation to lost or no answer and holds it with a flag.
9. **Turning on the weekday refresh routine.** *Recommend: yes, once slice 7 passes,* so folder-to-page
   latency drops from manual to under a day without anyone remembering to rescan.
10. **Doctrine edits outside the repo.** *Recommend: Parker updates the organization instructions and
    managed memory line "Dynamics 365 Sales for pipeline" to "deal folders for working state; Dynamics
    365 for history"* when slice 1 merges, so agents stop being told the old rule.
