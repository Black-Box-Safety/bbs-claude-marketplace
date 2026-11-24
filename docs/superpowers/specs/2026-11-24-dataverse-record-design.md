# Dataverse as the sales record, folders as the workspace — design

Status: **DRAFT for Parker's approval, 2026-11-24. Nothing here is built.** Author: a Claude
Code session with Parker. Ruling it rests on: `docs/STEWARD.md`, "Dataverse is the record for
accounts, buyers, deals, outcomes and contracts; folders stay the rep's workspace"
(2026-11-24, not yet in effect). Amends `2026-11-16-bbs-sales-system-design.md` where the two
disagree; §11 lists what changes there.

## 1. Intent

A rep saves the buyer's email and attachments to a folder and points Claude at it. That does
not change. What changes is where the record of the deal lives: today a rep types it into the
Sales CRM by hand and Claude writes a second copy into `RFQ.md`. After this design Claude
writes one record, in Dataverse, after the rep approves it, and the folder shows a read-only
copy.

The rule a rep needs: **the folder is where you work; Claude keeps the record.**

## 2. Goals, non-goals, anti-goals

**Goals**
1. One record per account, buyer, deal, outcome and contract, in Dataverse, written by Claude.
2. A rep's steps do not grow. Hand entry of an RFQ in the CRM stops.
3. The account model tells a California institution from a federal office, and knows that DEA
   and FBI are siblings under one department without ever merging them.
4. Every federal and prime contract BBS holds or held is a row that past performance can cite.
5. A long pursuit (a solicitation, a proposal, a vehicle BBS is chasing) is its own record,
   separate from an RFQ, and what it taught is in front of Claude when the next request from
   that account or its department arrives, whether the pursuit was won or lost.
6. The record works from any Claude surface, including a cloud session with no folder on disk.

**Non-goals**
- Moving, renaming or merging customer folders.
- Quote lines, costs and margins in Dataverse (§6.4). Business Central keeps quotes.
- Remembered notes and flags (`LEARNED.md`, `FLAGS.md`). They are context and stay in folders.
- Body armor and CSU/UC, as in the 2026-11-16 design.
- Retiring the Dynamics 365 Sales app. That is a later ruling (O7); nothing is uninstalled here.

**Anti-goals — failure even if it technically works**
- A rep has to open a CRM screen to keep a deal current.
- Two places a rep or an agent can type the same fact.
- A write to Dataverse that no person approved.
- A federal deal recorded against a department-level account, or a California rule (DVBE
  wording, Grainger at cost) applied because an account's channel was guessed.
- A merge of two accounts without Parker's approval of the pair.

## 3. What is there today (read 2026-11-24 through the Sales CRM connector)

- Environment `blackboxsafety.crm.dynamics.com`. The connector authenticates as an application
  user, so every write it makes is attributed to that user, not to the rep.
- **`bbs_rfq`** is live and in daily use: the newest row is `RFQ-005927` (created 11/24), the
  three newest were entered by two reps. 47 custom columns: account, contact, received and due
  dates, quote value, quote method, PO number, bill-to and ship-to, status (`In Progress`,
  `Submitted` seen), and an `Accepted` flag.
- **Outcomes are not recorded.** Zero rows have `Accepted` = yes and zero carry a PO number.
- **A required field produces placeholder data.** Quote value is required, and an in-progress
  row carries $1.00.
- **Accounts: California has hierarchy, federal has none.** CDCR, CalVet, DSH, CHP, Caltrans
  and CAL FIRE each have institutions parented under them. Every federal account read has no
  parent: "Drug Enforcement Administration (DEA)", "DEA El Paso Field Division", "Federal
  Bureau of Investigations", two FBI field offices, "Federal Department of Justice (DOJ)" and
  "United States Department of Justice" all sit flat and unrelated. VA medical centers are
  flat beside an unlinked "Department of Veterans Affairs".
- **Duplicates.** At least eight spellings of CalVet, five of the U.S. Marshals Service, two
  federal DOJ, three California DOJ, two "Nevada Dept. of Corrections".
- **`bbs_customertype` is empty** on every account read, so nothing marks state from federal.
- The account table also holds suppliers and at least one individual.
- The account carries `bbs_graingeraccountnumber`. Buying-account numbers therefore already
  live in Dataverse; they are never projected into git or a published page.
- **The connector cannot create a record.** It reads and updates only, updates are off unless
  the deployment sets `CRM_ALLOW_WRITES=1`, and an update uses `If-Match: *` (last write wins).
- [FLAG: total row counts, the status and customer-type option values, which app screen reps
  use to enter `bbs_rfq`, and where the connector's source lives were not read.]

## 4. State and federal are different businesses

One schema has to carry both without pretending they are the same. The differences that shape
the model:

| | California state | Federal |
|---|---|---|
| Who asks, who buys, who uses | Usually one person at one institution | Often three parties: the end user, a contracting office that may sit elsewhere, and a program or small-business office |
| Hierarchy | Agency → institution. Shallow and stable | Department → component → office or site. DOJ → FBI → a field office |
| Rhythm | Constant small requests from known buyers | Occasional solicitations, or orders against a contract BBS already holds |
| Request types | NASPO or LPA order, BPO order, informal competitive quote | Micro-purchase, RFQ, BPA call, full proposal, sources-sought response |
| Where it arrives | The buyer's email | Email, SAM.gov, GSA eBuy, Unison, DIBBS, a prime's portal |
| Certification | DVBE 2009473 only; never small business | SDVOSB; small business per NAICS; nonmanufacturer rule |
| Price rule | Grainger price is the customer price on state schedules | No at-cost rule; set per solicitation |
| Paperwork | State form packet | Reps and certs, FAR and DFARS clauses, country of origin per line |
| What a win leaves behind | A PO | A contract with a number, a period and a contracting officer: past performance |
| Outcome evidence | The PO in `Customer PO's` | An award notice, often public; sometimes a debrief or a protest |
| Record weight | Desk: every request is a deal | Contract account or positioned account (§5.4) |

Certification, price rule and paperwork are **not** stored per deal. They follow from the
account's channel and stay where they are ruled today (canon, the channel `CLAUDE.md`, the
skills). Dataverse stores the channel; it does not restate the rule.

## 5. Accounts

### 5.1 One table, three levels

Use the standard `account` table and its existing parent lookup. Add a level so a query can
tell a department from an office:

| Level | California state | Federal | Prime |
|---|---|---|---|
| 1 Organization | Agency (CDCR) | Department (DOJ, VA, DoD) | Company (Bechtel National) |
| 2 Component | usually none | Agency or component (FBI, DEA, USMS, ATF) | Program (Sentinel, WTP) |
| 3 Buying unit | Institution or facility | Office, field division, medical center, district | Site |

**A deal attaches to the lowest level known, never to level 1.** DEA and FBI are two level-2
accounts with the same level-1 parent. That one link is what lets Claude answer "what have we
done inside DOJ" for an FBI opportunity without ever treating DEA's buyers, contracts or
prices as FBI's.

### 5.2 New columns on `account`

| Column | Purpose |
|---|---|
| `bbs_channel` | CA state, Federal, Prime, State and local, Commercial. Drives which rules apply. Required before any deal is created |
| `bbs_level` | 1, 2 or 3 as above |
| `bbs_weight` | Desk, Contract account, Positioned account, Dormant (§5.4) |
| `bbs_bccustomerno` | The Business Central customer number. One account, one BC customer, where BC has one |
| `bbs_folderpath` | Path under `MASTER/Customers/`, as the folder is named today |
| `bbs_agencycode`, `bbs_officecode` | Federal only: the department or sub-tier code and the contracting office code, so a public award record can be matched to the account |
| `bbs_recordkind` | Customer, Supplier, Other. Keeps suppliers and individuals out of customer views without deleting them |

`bbs_customertype` exists and is empty. [FLAG: read its options before deciding whether
`bbs_channel` replaces it or fills it.]

### 5.3 Relationships that are not parent and child

Hierarchy cannot express these, and each one changes how a deal is worked:

| Relationship | Example | How it is recorded |
|---|---|---|
| A contracting office buys for an end user | A VA network contracting office awards for several medical centers; Washington Headquarters Services awards the DoD OIG vest BPA | Two lookups on the deal and the contract: **customer** (who issues the order) and **end user** (who receives it) |
| A prime buys for a government program | Bechtel buys for Sentinel under Northrop's Air Force contract | **End customer** lookup on the contract, pointing at the government account |
| A partner refers the deal | Grainger Huntsville referrals | **Referred by** lookup on the deal |

For a California deal all of these are empty or equal to the customer, which is the
structural difference between the two businesses in one sentence. No generic relationship
table in the first build; three named lookups cover every case found on disk.

### 5.4 Weight decides how much record an account gets

| Weight | Accounts | Deals | Contracts |
|---|---|---|---|
| **Desk** (CA state, Sentinel) | Full hierarchy | Every request | Vehicles only |
| **Contract account** (USACE Walla Walla, DoD OIG) | Yes | One per call or order | One row per contract, kept current |
| **Positioned account** | Yes, with buyers | Only when a request arrives | Past contracts, for citing |
| **Dormant** | Row only | None | None |

### 5.5 Cleaning what is there

Propose-only. Claude produces a sheet per department or agency: the level each account should
take, the parent it should get, and the pairs that look like duplicates. Parker approves the
sheet by name; only then are parents set, and merges are done one approved pair at a time.
Federal first: DOJ and its components, then VA. No account is deleted.

## 6. Deals, outcomes and contracts

### 6.1 Deal: extend `bbs_rfq`, do not replace it

Reps already use it, its rows are numbered up to `RFQ-005927`, and that number is the `CRM RFQ` key
`RFQ.md` already carries.

| Add | Notes |
|---|---|
| `bbs_stage` | The eight stages in `rfq_record.py` `STAGES`. That list stays the one source |
| `bbs_outcome`, `bbs_outcomedate`, `bbs_outcomeevidence`, `bbs_lossreason` | `OUTCOMES` from the same file. Replaces the unused `Accepted` flag |
| `bbs_sentdate` | From evidence, never from a BC field (2026-11-16 design §4) |
| `bbs_bcquote` | The SQ number. The quote itself stays in Business Central |
| `bbs_requesttype` | State order, informal competitive, micro-purchase, RFQ, BPA call. A proposal or a sources-sought response is a pursuit (§6.3), not a deal |
| `bbs_solicitationno`, `bbs_portal`, `bbs_setaside`, `bbs_naics` | Federal; empty on a state deal |
| `bbs_vehicle`, `bbs_contractid` | The vehicle, and the contract row when the deal is an order under one |
| `bbs_pursuitid` | The pursuit this request came out of, when there is one (§6.3) |
| `bbs_enduserid`, `bbs_referredbyid` | §5.3 |
| `bbs_folderpath`, `bbs_desk` | The deal folder; the desk id from `desks.json` |

**Which fields a deal must have is decided by the writer from the account's channel and the
request type, not by a required column.** Required columns are what produced the $1.00 rows.
Quote value stops being required (O5).

A child table, `bbs_rfqevent` (stage, date, evidence, entered for which rep), is the status
log. It is the audit trail the application-user attribution otherwise loses.

### 6.2 Contract: a new table, `bbs_contract`

Number, type (BPA, IDIQ, purchase order, task order, LPA), customer, end user, end customer,
period start and end, option years, ceiling, set-aside, NAICS, contracting officer and COR
(contact lookups), where the award document is, and three past-performance fields: a
questionnaire or CPARS on file (yes, no, requested), relevance tags, and **citable**, which
only Parker sets. Dollars invoiced are read from Business Central when asked, never stored.

Seeded, row by row with a source, from the candidate list in
`Federal Biz Dev/federal-sales-team/research/inventory-files.md` §3. A row whose evidence was
not found stays not citable.

### 6.3 Pursuit: a separate record from a deal

A deal is a request with lines to price now: hours to days, ends in a quote and a PO. A
pursuit is something BBS is chasing over weeks or months: a solicitation, a proposal, a
sources-sought response, a cooperative vehicle, a large program. They differ in every way
that matters to a record, so they are two tables, not one table with a type column.

| | Deal (`bbs_rfq`) | Pursuit (`bbs_pursuit`, new) |
|---|---|---|
| Cycle | Hours to days | Weeks to months |
| Stages | `STAGES` in `rfq_record.py` | Identified, qualifying, bid or no-bid decided, shaping, response in work, submitted, decided |
| What it holds | Lines, a quote number, a sent date | Estimated value, decision date, incumbent, competitors, teaming and supplier commitments, bid or no-bid reason |
| Notes | Rare | The point: calls, site visits, questions and answers, debrief |
| Ends in | Won, lost, no answer, no bid, cancelled | Awarded, lost, no bid, cancelled, withdrawn by the buyer |
| A win creates | A PO | Usually a **contract** row (§6.2), which then receives deals |

**It is a pursuit when** more than a quote is owed, or there is nothing to price yet, or a
win would create a contract or a vehicle. Otherwise it is a deal. The channel does not decide
it: the California body armor LPA and a NASPO rebid are pursuits; an FBI micro-purchase is a
deal.

**How they connect.** Pursuit → contract → deals, for a BPA or a vehicle. Pursuit → deals
directly, when a buyer met during a pursuit later sends a request; the deal carries
`bbs_pursuitid`. Nothing is copied between them.

**What a pursuit leaves behind, won or lost.** Notes are kept as dated entries on the pursuit
(Dataverse's standard notes on the row), written by Claude after the rep approves, from the
rep's own words or a document. At close, three fields are required: why it went the way it
did, what BBS learned (the winner and the price where the award is public, the requirement
that hurt, the contact worth keeping), and what to do next and when. A lost pursuit is not
closed until they are filled.

**How those insights reach the next RFQ.** When a deal is opened on an account, Claude reads
the pursuits on that account, on its parent, and on its siblings under the same level-1
organization, and shows the rep the closing fields of each. A lost FBI proposal is in front
of whoever works the next DEA request. This is a read through the hierarchy in §5.1, not a
second copy of the lesson.

**What is there today.** The Sales app's standard `opportunity` table holds a handful of rows
of exactly this kind (a $2.3M university program, SWAT kits, "NASPO"), entered by three reps;
most were not touched after the day they were created. `lead` holds two rows. The eight
newest opportunities span September 2025 to June 2026. [FLAG: full counts not read.]

**Why a new table and not `opportunity`** (ruled 2026-11-24, O10). `opportunity` belongs to the Sales app Parker has
ruled BBS will stop using; Microsoft lists it among the tables that app installs. A record
BBS means to keep should not depend on an app BBS means to drop. The few existing rows are
copied across on an approved sheet. [FLAG: whether `opportunity` survives an uninstall of the
Sales app was not verified; it no longer decides anything, since the new table is ruled.]

**Who opens and owns one** (ruled 2026-11-24, O12). Any rep may open a pursuit and assign its
owner. The owner is the row's owner in Dataverse and the person Claude asks for the close-out
fields.

**The pursuit's documents** live in a folder like any other; the row carries its path. The
folder is where the proposal is written; the row is where its status and lessons are.

### 6.4 What stays out of Dataverse

Line items, vendor costs, sell prices and margin stay in `RFQ.md`'s working tables and in the
Business Central quote. They are working papers with cost data in them, and the 2026-11-16
anti-goals keep cost out of anything broadly visible. Whether line-level outcomes are later
needed for the pricing loop is open (O2).

## 7. How Claude writes

### 7.1 Approaches considered

| | Approach | Trade-off | Verdict |
|---|---|---|---|
| **1** | **The connector gains a create tool, limited to named tables and columns; managed settings put create and update in `ask`.** | Works on every surface, including cloud. Each write shows the rep an Allow prompt. Needs a connector change and the application user's role widened. | **Recommended.** |
| 2 | A script run through the fill launcher, with a review sheet, like the Business Central writes. | Reuses a proven pattern. Runs only where the folder tree and Python are, which today is one Mac. | No: it rebuilds the single-machine limit this design removes. |
| 3 | A Power Automate flow as the write endpoint. | Server-side. Adds a second place where write logic lives and a licensing question. | Not for writes. Fits events (§9). |

### 7.2 Rules for a write

- **One writer.** `rfq_record.py` stays the only code that changes a deal. It writes Dataverse
  first, then renders the folder copy. A skill never calls the connector's write tools itself.
- **A person approves.** Claude shows the review sheet (what will be created or changed, on
  which account); the rep approves by name; the Allow prompt is the second check.
- **Search before create,** for accounts and contacts, by name and by parent. This is the
  duplicate-buyer-folder rule applied to rows.
- **Reps do not create level-1 or level-2 accounts.** Claude proposes; Parker approves.
- **No delete.** Updates carry the row's version, so a stale write fails instead of winning.
- **The rep is the owner** of the row; the event log names who it was entered for.

## 8. What the rep and the session see

- **Intake.** The rep points Claude at the folder. Intake resolves the account and buyer,
  shows the sheet, and on approval creates the deal. The rep never opens the CRM.
- **Folder copy.** `RFQ.md`'s header and status table and the buyer's `quote-log.md` are
  rendered from Dataverse and marked generated. The existing guard hook rejects a hand edit to
  those parts. The lines and pricing tables stay hand-and-skill edited as now.
- **Session start.** The existing hooks keep reading the folder copy, so a local session is
  oriented exactly as today. A session with no folder on disk reads the same facts from
  Dataverse on its first step.
- **Lag is stated, not hidden.** A write from a cloud session reaches the folder copy at the
  next refresh. The copy prints when it was generated.
- **A read view.** One dashboard reads Dataverse for Parker and the reps, so the pipeline is
  visible when Claude is not in the loop (O6).

## 9. Events

Power Automate, cloud side: a new file in `Customer PO's` and a new message in the shared
quote mailbox each raise a **proposal** (a possible win, a possible sent date). A proposal
changes nothing until a rep approves it. This moves the fetch half of the outcome engine off
Parker's Mac; the matcher is unchanged. [FLAG: Power Automate entitlement not checked.]

## 10. Transition

1. **Nothing changes for reps** until step 4. They keep entering `bbs_rfqs` by hand.
2. Schema additions and the connector change ship. The account cleanup sheets for DOJ and VA
   are approved and applied.
3. **Pilot:** one rep, the CA desk, two weeks. Claude creates the deal; the rep also enters it
   by hand; the two are compared row by row.
4. **Switch,** per desk: when the pilot matches, reps stop hand entry. This is the moment the
   2026-11-24 ruling takes effect for that desk, and canon's Systems of record rows change in
   the same pull request.
5. Outcomes backfill from the desk quote-logs, as proposals a rep approves.
6. Contracts are seeded; Sentinel and the contract accounts join.

## 11. What this changes in the 2026-11-16 design

| There | Here |
|---|---|
| Folders are the record (R-S5) | Dataverse is the record; the folder holds a rendered copy |
| Claude never writes the CRM (§6.9) | Claude writes it, through one writer, after approval |
| Reps stop CRM entry when folders and CRM agree for two weeks | Reps stop when Claude's entries and theirs agree for two weeks |
| The one metric stays on `bbs_rfqs` until the switch | It stays on `bbs_rfqs`, permanently |
| Engine fetchers on Parker's Mac | Fetchers move to cloud events (§9) |
| Unchanged | One writer per deal, the stage and outcome lists, propose-only outcomes, the desk registry, the learning loop, the pricing loop |

Slices of that build that add hand-kept or script-kept state to markdown should pause until
this design is ruled on. The registry (S2, merged) and the record validator are reused.

## 12. Open rulings for Parker

| # | Question | Recommendation |
|---|---|---|
| O1 | Write approval: approval by name plus the Allow prompt, or the Allow prompt alone | Both, as with Business Central |
| O2 | Line items in Dataverse later, for line-level win rates | Not in this build; revisit with the pricing loop |
| O3 | Outreach and pre-RFQ pipeline: which table holds it once the Sales app is not the tool | [FLAG: not read today.] Decide after the deal switch |
| O4 | Who may create or re-parent level-1 and level-2 accounts | Parker only |
| O5 | Make quote value optional on `bbs_rfq` | Yes |
| O6 | Who builds and owns the read view | The existing RFQ pipeline dashboard, repointed |
| O7 | When, and whether, the Dynamics 365 Sales app is retired, and what license reps then need | Ask the Microsoft partner before anything is removed. Microsoft's table-licensing page says custom tables need a Power Apps license; what a rep needs when only Claude touches the data was not confirmed |
| O8 | Who makes the Dataverse schema change (the earlier outside builder, or in house) | [MISSING — NEEDS INPUT] |
| O9 | `bbs_customertype`: reuse or replace with `bbs_channel` | Read its options first |
| O10 | Pursuits in a new `bbs_pursuit` table, or in the Sales app's `opportunity` table | **RULED 2026-11-24: new table.** |
| O11 | Federal pursuits: the federal-sales-team program names the Sweetspot platform for pursuit work. One home for a pursuit's status | **RULED 2026-11-24: Dataverse holds status.** Sweetspot stays a drafting and search tool. That program's own ledger (`Federal Biz Dev/federal-sales-team/docs/pm/DECISIONS.md`) needs the same entry; it is on SharePoint and was not edited from here |
| O12 | Who may open a pursuit, and who signs the bid or no-bid decision | **RULED 2026-11-24: "the rep can assign."** Read as: any rep may open a pursuit and assign its owner. [FLAG: the ruling does not name who signs bid or no-bid. This draft assumes the assigned owner decides and records the reason; Parker to confirm or name someone else] |

## 13. Build sequence

| Slice | What | Done when |
|---|---|---|
| D0 | This design and its open rulings ruled | Recorded in the register |
| D1 | Schema: account columns, `bbs_rfq` columns, `bbs_rfqevent`, `bbs_contract` | Columns read back through the connector |
| D2 | Connector: limited create, versioned update; managed settings `ask`; checker registry row | A create is refused outside the named tables |
| D3 | Account sheets for DOJ and VA, approved and applied | DEA and FBI share a parent; no approved pair left unmerged |
| D4 | `rfq_record.py` writes through; intake creates the deal; folder copy rendered | The CA pilot rep logs a deal without opening the CRM |
| D5 | Pilot, then the CA switch | Two weeks of matching entries; canon rows changed |
| D6 | Outcomes: proposals from events, backfill | A won deal carries its PO and date |
| D7 | Contracts seeded; Sentinel and contract accounts join | A federal bid can list citable contracts by department |
| D7a | `bbs_pursuit`, its close-out fields, and the hierarchy read at deal intake; existing opportunities copied on an approved sheet | Opening a deal on one component shows a closed pursuit at a sibling component |
| D8 | Sales app retirement, if ruled | — |

## 14. Sources

- Sales CRM connector, read 2026-11-24: the eight newest `opportunities` and all `leads`; `WhoAmI`; attribute metadata for `bbs_rfq` and
  `account`; the three newest `bbs_rfqs` rows; accounts matching DOJ, FBI, DEA, Marshals, VA,
  Bechtel and Corrections; accounts with a parent; `bbs_accepted eq true` and
  `bbs_ponumber ne null` (both empty).
- Microsoft Learn, "License requirements for tables" and "Restricted tables requiring
  Dynamics 365 licenses", read 2026-11-24.
- `plugins/bbs-sales/scripts/rfq_record.py` (`STAGES`, `OUTCOMES`, `HEADER_KEYS_V2`).
- `docs/superpowers/specs/2026-11-16-bbs-sales-system-design.md`.
- SharePoint, read 2026-11-24: `Customers/Federal Agencies/CLAUDE.md`;
  `Customers/State of CA Agencies/docs/archive/migration/CUSTOMERS-RESTRUCTURE-PLAN.md`;
  `Federal Biz Dev/federal-sales-team/research/inventory-files.md`.
- The state and federal comparison in §4 combines those files with general federal
  procurement practice. Rows not traceable to a BBS file are the author's summary, for Parker
  to correct.

---

Owner: Parker Marshall. Drafted 2026-11-24.
