# BBS Sales System — design

**Date:** 2026-11-16 · **Owner:** Parker Marshall · **Status:** DRAFT, awaiting Parker's approval
**Supersedes as parent:** `2026-10-30-rfq-pipeline-folder-first-design.md` and `2026-11-12-dashboard-folder-sync-design.md` become the CA desk's part of this design; nothing in them is deleted.
**Plugin:** `plugins/bbs-sales` (v0.16.2 at `main` 51cf631)

---

## 1. Intent

One way of working every RFQ, for every customer, that gets better each time it runs.

Black Box Safety quotes for California state agencies, Bechtel (Sentinel, Hanford), federal agencies, and local fire, police, utilities and schools. Today two desks have each built half of a good process and every other customer folder has none:

- The **State of CA Agencies** desk has a typed record (`RFQ.md` v2, `rfq_record.py`, a validating hook, sidecar JSON, a scanner and a dashboard) — but only intake ever writes to it. 0 of 50 sidecars have reached `sent` or `outcome`; 2 of 126 quote-log rows carry a final outcome; cost never reaches the record.
- The **Sentinel** desk has rich per-RFQ evidence, a learning loop that compounds (`learning/PROCESS.md`, `margin-tracker.md`, `lessons.md`, rules promoted into `CLAUDE.md`), and a daily-refreshed dashboard whose checklist only marks a step done with evidence — but no record schema, and three status stores (tracker xlsx, stage JSON, site indexes) that disagree.
- Every other folder (USACE Walla Walla, SDGE, Federal Agencies, Hanford, Kern, Air Force…) keeps no RFQ record at all.
- Wins are logged nowhere reliably. On the CA desk, Business Central never records them: quotes that customer POs cite stay Draft (orders are keyed fresh, not through Make Order), and sales orders do not carry the customer's PO number. Sentinel runs Make Order after sending (`sentinel/CLAUDE.md` line 114), so its orders should carry Quote No. The `Customer PO's` folder — 1,044 files filed from the shared PO mailbox — has never been read by any process.

**Why Parker wants it:** a feedback loop. The team should be able to see what it quoted, what it won, at what price and margin, for whom, and what it learned — so each RFQ is priced and run better than the last, and reps understand their work and their customers. Lessons were getting lost in chat.

**The organising idea:** things that depend on a person remembering decay; things fed by a system event fill themselves. The PO folder fills because one person files every PO. So the system takes its facts from events — files written, BC records, a sent-quote mail rule, POs filed — and asks people only to confirm.

## 2. Goals, non-goals, anti-goals

**Goals**
1. Every RFQ for every customer, from now on, has one record in its own folder, and appears on one dashboard with its line items, stage and what it is waiting on.
2. Every stage from logged to outcome is backed by proof (a file or a system event), and the gap between "it happened" and "the record knows" closes nightly without anyone typing.
3. Sent quotes are captured automatically; wins are logged from `Customer PO's`; losses and silences are proposed on a close-out list.
4. Each line's sell price is set with evidence — firm cost, public prices, what agencies paid, what we won at before — and margin bands learn from outcomes.
5. What the team learns on an RFQ is saved in the folder and comes back to the next agent and rep automatically.
6. The `bbs-sales` plugin implements all of this for any desk declared in one registry.

**Non-goals (this program)**
- Renaming the `ca-` skills or commands (it ripples through evals, the coach glossary, canonical facts and the managed `claudeMd`). New desk-agnostic entry points are added beside them.
- Rewriting or migrating old records. v2 records keep validating; old Sentinel RFQs stay as they are.
- Moving, renaming or merging customer folders (`DUPLICATE-TREES.md` cleanup is separate work).
- Replacing the BC quote document. The outbound quote stays the BC print.
- Enterprise price-optimization software, or SCPRS-based outcome matching (it stays in shadow; its backtest failed).
- Retiring the Grok bots (Ollie, Becca, Sloane, Penny). They keep their lanes.
- **Body armor (Jeff's desk).** Not in this build. Intake on a body-armor request stops and routes it to its owner.
- **CSU/UC (Joey's book).** Not in this build, but planned. Parker, 2026-11-17: it is a recurring, order-based book placed mostly through Provision Connect, not RFQ-based, and Joey's existing dashboard (the CSU & UC Book Tracker) should be kept.
  - A brainstorm of how to integrate it as an **order desk** is under way and becomes its own follow-up design.
  - This design only reserves room for it: the `kind` profile key (§6.2).
  - CSU/UC intake routes to Joey, and CSU/UC POs (including UCLA advisories) are classified as out-of-scope orders.

**Anti-goals — failure even if it technically works**
- Any step that only works if a rep keeps a log by hand.
- Anything that sends, submits, releases, or marks a quote lost automatically.
- A fourth status store.
- Cost, margin, supplier names, Grainger account numbers, rebate or SCPRS competitor names reaching anything customer-facing (including BC line comments).
- Card numbers, buyer emails or phones in any record, cache or published page.
- Small-business status on a California form; a markup on a NASPO / California-schedule Grainger line.

## 3. Rulings this design rests on

**Parker, in session 2026-11-16 (earlier session, memory `unified-desk-model-direction`; program `DECISIONS.md` D10):** folders plus interactive dashboards are the target; one desk model from the best of Sentinel and CA, rolled out by desk profile; reps update the CRM (D10.1); a desk that declares a profile may keep a hand-kept outcome record (D10.5, R6 amended); agents in the CA tree always use and update `desk-remember`.

**Parker, in this session 2026-11-16:**

| # | Ruling |
|---|---|
| R-S1 | Quote-sent capture is an **Exchange mail flow rule** copying outbound mail that carries a BC sales-quote PDF to one logging mailbox. Parker creates it. |
| R-S2 | That mailbox is read **metadata only**: a script on Parker's Mac keeps sender, buyer domain, sent timestamp and quote number. Bodies and attachments are never stored or read by Claude. Short retention (about 90 days). Supersedes 2026-10-30 spec §13.8 item 1 and 2026-11-12 spec §7 for this mailbox only. |
| R-S3 | A **Tier 1 PO match** (the PO cites our quote number and the customer and pre-tax total check out) runs in shadow until the matcher is at least 95% precise on 30 or more cases; then it counts as **Won** automatically, and the rep can undo it. Weaker matches always need a rep's confirmation. |
| R-S4 | **Sentinel adopts `RFQ.md`** for new RFQs onward. Its dashboard data is built from those records, collapsing the tracker xlsx, hand indexes and stage JSON into one store. Existing RFQs are untouched. |
| R-S5 | **Folders are the RFQ working record for every customer**, not only California state. Reps keep updating the CRM until each desk passes a parity switch (two weeks where folder and CRM agree), then CRM entry stops for that desk. |
| R-S6 | Build approach: **extend what exists in place**, with the matching engine running as a routine on Parker's Mac (§5). |

**Supersessions these rulings require (recorded in the first PR, §11 S0):**
- `canonical-facts.md` lines ~145–146 (systems of record: CA state only) → every desk with a profile.
- `canonical-facts.md` "What counts as a win" and `METRICS-SIGNOFF.md` Q-A → Tier 1 auto-Won after the shadow bar (R-S3).
- The managed `claudeMd` R6 wording ("outside the CA desk no outcome file is created by hand") → D10.5 wording; Parker re-pastes managed settings after merge.
- Program `DECISIONS.md` D01 scope fence (CA only) → see open ruling O3.
- D10.x and this session's rulings recorded in `docs/STEWARD.md` as RULED. Today D10 exists only in the program's own ledger.

**Rulings this design keeps (must not be lost):** the fold is person-run and approval is by name; a Sent-mail match is evidence, not approval; `no answer` is never set automatically (STEWARD.md ~231–247 items 1, 2, 5); the first stage date written stays and stages never move backward (sync spec §6.4, §7); the opaque deal key with its Keychain hash (D09.2); at-cost is keyed on the BC CONTRACT dimension, never a folder fact (D09.3); SCPRS outcome matching stays in shadow; the privacy gate.

## 4. Constraints

- **Company rules (organization instructions and managed settings):** Claude drafts, a person sends. BC writes are limited to items, Vendor No. patches, and sales quotes with lines, through the BC-Write-API scripts and `bc-item-entry` / `bc-quote-entry`, after the rep approves by name; never release, send, convert or post. Never invent a price, stock, lead time, spec, certification or contract fact — unknown is `[FLAG: why]`. Certification follows the buyer: California state DVBE 2009473 only (BBS is not a California small business); federal and primes SDVOSB; LA County DVBE and City of San Diego SLBE are local credits for those buyers only; one channel per form. NASPO / California-schedule Grainger price is the customer price. Customer folder names are never changed. Body armor (`BA-CA`, `BODYARMOR`, `BA-SRCWL`) and CSU/UC are outside the Kim/Aanya CA book. SCPRS totals are one slice of California procurement. Mail access is the signed-in person's (R-S2 is the recorded exception for the logging mailbox).
- **Marketplace invariants:** every hook ships as Python and PowerShell twins with a parity test; a changed plugin bumps `plugin.json` in the same PR; skill frontmatter carries `requires:` and `degrades-without:`; spec and plan before build; draft PRs, at most five open; reviewed by an agent that is not the author (`rex`); only Parker merges, in the GitHub UI; rulings live in `docs/STEWARD.md`; any script added to the `bbs-fill` ALLOWED list needs its own ruling (R3).
- **Platform facts:**
  - Windows reps may have no Python; the PowerShell `rfq-record` twin validates nothing. Reps never run the engine; they use skills and the dashboard.
  - OneDrive cloud-only placeholders stat fine but fail on open. Anything that reads file contents catches the error and logs "not local".
  - Parker's Mac is the only machine with the OneDrive tree, `python3` and the BC write scripts.
  - Spreadsheets written by scripts store formulas without cached values (the 851791 Price Analysis package view reads blank to a script). Records and sidecars hold values, not formulas.
- **Business Central facts (verified against Microsoft Learn and Microsoft's BCApps source, 2026-11-16):**
  - The API v2 `salesQuote.sentDate` is Sales Header field 153 "Quote Sent to Customer". Only the API `send` action stamps it. Printing does not, and the page's "Send by Email" button does not. So BC cannot be the source of "sent".
  - **Make Order** deletes the quote. The sales order keeps **Quote No.**, which API v2 `salesOrder` does not expose (an OData page is needed). CA desk orders are mostly keyed fresh, so Quote No. is usually empty there. Sentinel runs Make Order after sending, so Sentinel orders should carry it; S5 verifies this.
  - **Archive Quotes** decides whether lost and expired quotes survive. The "Delete Expired Sales Quotes" job destroys them for good.
  - Salesperson `KQUEZON` is used on Sentinel and federal quotes too. Attribution goes by desk and scope filter, never by salesperson code.
- **Customer PO's facts:**
  - 33 weekly folders, flat, with no year level. 822 PDFs and 210 `.msg` files.
  - About 1 PO in 4 cites a quote number.
  - 43% of non-UCLA PDFs have no text layer.
  - 38% of files are UCLA advisories.
  - GSA Advantage PDFs print full purchase-card numbers.
  - A hidden `.BPO Status Report/` holds the DGS BPO tracker.

## 5. Approaches considered

| | Approach | Trade-off | Verdict |
|---|---|---|---|
| **1** | **Extend in place, engine on Parker's Mac.** Generalize `rfq_record.py` (v3) and the hooks through a desk registry; the propose-only outcome engine ships as bbs-sales scripts run by a Mac routine; the CA RFQ Pipeline dashboard gains a desk filter. | Reuses the ~70% already built (#77 merged, #96, #100, the desk-profile branch), its tests and its rulings; OCR stays local so card numbers never leave the machine. Costs: the Mac must be awake; one machine. | **Picked (R-S6).** The engine keeps fetchers separate from the matcher, so fetchers can move to a hosted service later without touching the matcher or the record. |
| 2 | Same plugin generalization; engine as a hosted service (like the SCPRS warehouse on Fly) reading SharePoint and the mailbox through Graph. | Runs without the Mac. Costs: new infrastructure and secrets, a broad app permission on the SharePoint library, cloud OCR (conflicts with keeping GSA card numbers local); nothing on day 1. | Not now. |
| 3 | Clean-slate desk engine with a new record format; migrate CA and Sentinel. | No CA assumptions. Costs: discards merged work, breaks the scanner, dashboard and parity tests, migrates 65 records; months. | Rejected — every reviewer said finish, don't restart. |
| — | Database as the pipeline record (Supabase or an artifact DB). | Easier dashboards. | Dropped: works against R-S5 (folders are the record). |
| — | Sentinel's current pattern everywhere (a routine curates per-desk dashboard JSON from folders). | Fast to show. | Dropped: it is how Sentinel got three disagreeing stores. |

## 6. The system

### 6.1 Life of one RFQ

```
RFQ in ─► logged ─► sourcing ─► priced ─► quote built ─► packet built ─► delivered to rep ─► sent ─► outcome
 proof:   RFQ.md    vendor      Pricing   BC quote no.   signed packet   run handed to       quote    won · lost · no answer
          written   quotes /    rows with read back      PDF in folder   the rep             email    · no bid · cancelled
                    CSP in      cost+sell (bc-log.jsonl)                                     metadata
                    folder                                                                   (logging
                                                                                             mailbox)
 learning:  ## Lessons in RFQ.md at delivered/sent → LEARNED.md / lessons.md; outcome reason + public award price at fold
```

The stages are v2's, unchanged. Which ones apply depends on the vehicle (`applicable_stages`): a BPO skips sourcing and packet; NASPO skips packet unless forms are required. Line-level progress (`LINE_STAGES`) carries the finer detail that Sentinel's stages encode.

**Sentinel stage mapping** (Sentinel `learning/dashboard/STAGE-RULES.md` → v3):

| Sentinel | v3 stage | Note |
|---|---|---|
| Received | logged | |
| Sent to sourcing | sourcing | lines `sourcing` |
| Partially sourced | sourcing | some lines still `open`/`sourcing` |
| Pending pricing | sourcing | all lines `vendor quoted`, no Sell yet |
| Ready to send | priced / quote built / packet built | by checklist evidence: `bc_quote` → quote built; SIGNED reps → packet built |
| Quote sent | sent | |
| Ordered | outcome: won | |
| Lost | outcome: lost | |
| No bid | outcome: no bid | "inferred" stays a flag, never a stage |

Sentinel's six-step checklist (`sourced, priced, bc_quote, released, reps, sent`; "done needs evidence") becomes a **desk-profile option** rendered in the dashboard drawer. `released` (released and printed in BC) is checklist evidence only, never a stage.

### 6.2 Desk registry and profiles

A **desk** is a way of working: where its folders are, how its deal folders are shaped, which vehicles and forms apply, which certification channel and scope filter apply, and where its outcome ledger lives.

- **Machine registry, in two parts** *(call made after the builder check)*:
  - **Profiles** live in `plugins/bbs-sales/references/desks.json`, shipped with the plugin. A profile is a desk type: its rules, guard settings and record profile. The fixed roots for `ca-state` and `bechtel-sentinel` live here too. Adding or changing a profile is a PR.
  - **Customer bindings** live in a data file in the folder tree, `Customers/_Pipeline/desk-bindings.json`. A binding maps one customer root (e.g. `USACE-Walla Walla/`) to an `account`-type profile.
    - It is written only by `rfq_record.py bind-desk`, after the rep approves by name at that customer's first intake.
    - It takes effect immediately and reaches every rep through OneDrive. No PR or plugin update is needed.
    - A binding can never define a profile, point at `ca-state` or `bechtel-sentinel`, or loosen a guard. Those stay in the plugin.
  - Hooks read profiles first, then bindings. A missing or unreadable bindings file means "no account desks", never an error.
  - Python reads both with `json` and PowerShell with `ConvertFrom-Json`, and the parity tests feed both the same fixtures. That is why they are JSON, not Markdown.
- **Human doc:** `plugins/bbs-sales/references/desk-profile.md`, from the unpushed `feat/weekly-report-multi-user-privacy` branch, extended. It explains each key and points at `desks.json`. Reporting keys may stay in each desk's `learning/PROCESS.md`, keyed by `desk_id`.
- **One registry (profiles + bindings).** No other desk list may exist: not `desk_memory.DESKS`, not #100's `SENTINEL` literal, not a registry in the Weekly Summaries `CLAUDE.md`. `desk-post.sh` cannot parse JSON, so it keeps a grep alternation for the plugin roots, and a `check_marketplace.py` check asserts that alternation equals the union of root fragments in `desks.json`. The builder decides how `desk-post.sh` covers bound account roots.
- **Desk facts point at canon, never hold values.** A profile names its certification channel, salesperson rule and forms profile by reference to `canonical-facts.md` / `vendor_profile.json` / `ca-form-rules.md`. It never re-keys a certificate number or a buying-account number.

**Profile keys** (the builder settles exact names):

| Key | Meaning |
|---|---|
| `desk_id` | `ca-state`, `bechtel-sentinel`, … |
| `kind` | `rfq` (every desk in this build) or `order` (reserved for a recurring-order book such as CSU/UC; the follow-up design defines it). Hooks and the scanner skip `order` desks until that design lands. |
| `roots` | Path fragments under the MASTER document store, normally under `Customers/`. CA: `Customers/State of CA Agencies/All RFQ's by Agency/`. Sentinel: `Customers/Bechtel/sentinel/`. Roots outside `Customers/` must be allowed, because the CSU/UC book lives at `BBS CSU UC/`. |
| `deal_depth` | Min/max levels below a root where a deal folder sits (CA 2–3) |
| `deal_name_rule` | Date or ID pattern for deal folders, or `any` (Sentinel `rfq-845311`, `RFP-851791-kp1`; USACE `BPA Call 11.4.26`) |
| `guard` | Which `guard-tree` protections apply. Near-duplicate-sibling denial must be off where siblings like `rfp-825025-*` are normal. |
| `record_profile` | Which header keys are required beyond the core (§6.3) |
| `vehicles` | Allowed vehicle kinds. Only `ca-state` may infer `naspo` or `bpo`. |
| `ledger_level` | Where `quote-log.md`, `FLAGS.md` and `LEARNED.md` live: buyer folder (CA), desk `learning/` (Sentinel), customer root (account desks) |
| `scope_filter` | Reference to the scope rule (CA: `ca-state-sales-grounding` — body armor and CSU/UC out) |
| `cert_channel` | Reference to canon (`dvbe-ca`, `sdvosb-federal`, `local-<buyer>`) |
| `checklist` | Optional evidence checklist for the drawer (Sentinel's six) |
| `expiry_days` | Default outcome window when the quote states none (§6.5) |

**Initial desks:**
- `ca-state`: today's CA behaviour, byte-identical.
- `bechtel-sentinel`: new RFQs only (R-S4).
- `account`: a generic profile for any other customer folder (federal, primes other than Sentinel, local, utility, schools, commercial).
  - It is bound per customer root by a binding (above), e.g. `USACE-Walla Walla/`, `Federal Agencies/`, `SDGE/`, `Bechtel/hanford-DOE/`, `Kern County/`.
  - Its certification channel is derived from the buyer type through canon. Canon covers federal and primes (SDVOSB), California state (DVBE), LA County (DVBE, local) and City of San Diego (SLBE, local). For any other buyer (utilities such as SDGE, other counties, cities and schools), intake writes `[FLAG: certification channel not ruled for this buyer]` and the packet step stops for the rep. See open ruling O10.
  - A customer folder with no binding gets one proposed at its first intake. The rep approves it by name, and that is how the system reaches "every customer going forward" without touching dormant folders.
  - The builder may split `account` into `federal` and `local` if forms or cert rules make one profile awkward.

### 6.3 The record — `RFQ.md` v3

One `RFQ.md` per deal, in the deal's existing folder, with `rfq-state.json` beside it. `rfq_record.py` stays the only parser and writer.

- **Desk comes from the path**, resolved through `desks.json`, never from a header key: a header could disagree with where the file actually sits.
- **Header = required core + profile keys.**
  - Core: `Received`, `Buyer`, `Customer`, `Due`, `Submit via`, `Solicitation #` (any channel key: solicitation, RFP, SCR, Ariba event, bid number, BPA call), `Vehicle`, `Rep`, `BC quote`, `Valid until` (new), `Stage`.
  - The `ca-state` profile adds `Agency / institution`, `Grainger account`, `PC quote`, `CRM RFQ`.
  - `CRM RFQ` stays a `ca-state` key (§6.9).
- **v2 records keep validating** under the CA profile with no edits. `migrate` stays opt-in and is never run in bulk.
- **Vehicle inference.** `vehicle_kind` keyword inference (`rfq_record.py` ~361–367) feeds `NASPO at cost` and the R3 at-cost gate. Outside `ca-state`, no profile may infer `naspo` or `bpo`; the vehicle is stated. Grainger lines follow canon's "Grainger sell rule, by channel": at cost for California state, markup allowed for primes (after the discount ask). On the channels canon leaves open (co-ops, direct federal, private; open ruling O1), Grainger-lane lines get `[FLAG: Grainger sell rule not ruled for this channel]` and no band.
- **Pricing table gains one column:** `| # | Vendor | Vendor ref | Cost | Cost basis | Sell | Strategy | Lead | Line stage | Evidence |`.
  - `Cost basis` says how firm the cost is: `CSP <account-ref>`, `MCP right account`, `MCP wrong account`, `estimate`, `vendor quote <date>`, `BC card`.
  - This is what lets cost reach the record and the dashboard.
  - It never holds a buying-account number, only a reference to the account's profile entry.
- **New prose sections:** `## Lessons` (what this RFQ taught, dated, by whom) and `## Outcome notes` (reason, public award price and vendor where known, with source).
- **Grok lane outputs feed the record only through `rfq_record.py`,** never as direct `RFQ.md` writes.

### 6.4 Lanes and proof

Each stage is a **lane** with a required output. Any worker can fill a lane — a Claude skill, a Grok bot, or a rep — as long as the output exists. The record advances through `rfq_record.py` when a skill finishes a lane, or through the engine's proposal when the proof appears some other way.

| Stage | Required proof | Typical workers today |
|---|---|---|
| logged | `RFQ.md` exists with core header | `ca-rfq-intake`; new `rfq-intake` (non-CA desks); for a deal folder created without a record (e.g. by Ollie on Sentinel), the engine proposes a seeded record and `/rfq-fold` creates it (§6.5) |
| sourcing | a vendor request or CSP request in the folder, or a line with lane `sourcing` | `bbs-sourcing`, `supplier-scout`, `vendor-quote-email`; Becca, Sloane |
| priced | every in-scope line has Cost, Cost basis and Sell, or a stated strategy (`NASPO at cost`, `parked`, `no bid`) | `grainger-pricing`, `naspo-quote`, Pru, Penny |
| quote built | BC quote number read back (`BC-import/*.bc-log.jsonl`) and written to header `BC quote` | `bc-item-entry` → `bc-quote-entry` (**must write the BC quote number and the stage**, which no skill does today) |
| packet built | signed packet PDF in the folder | `naspo-quote`, `ca-form-filler`, Sentinel reps fill |
| delivered to rep | the run ended with the rep holding quote + packet | `/ca-rfq` Gate 8; `/rfq` equivalent |
| sent | first logging-mailbox metadata hit for the BC quote number (later hits = revisions), **or** portal submission evidence (confirmation PDF / screenshot in folder) | Exchange rule (R-S1); rep files portal confirmations (Cal eProcure, Ariba, PIEE) |
| outcome | matched PO (won), recorded loss with source, or folded close-out (`no answer` / `no bid` / `cancelled`) | outcome engine + `/rfq-fold` (§6.5) |

### 6.5 Outcome engine (propose-only)

Three parts, so each can be tested and moved alone.

1. **Fetchers** write one evidence file per night. Proposed location: `Customers/_Pipeline/evidence/YYYY-MM-DD.json`, following the `_Templates & Forms` / `_Unfiled` convention; the builder confirms.
   - **BC:** sales quotes (number, customer, amount, status, valid-until) and sales orders, including **Quote No.** through a published OData page; posted invoice lines for the pricing loop.
   - **Logging mailbox:** per R-S2, metadata only — sender, buyer domain, sent timestamp, and the quote number from the attachment filename or subject.
     - Read through Microsoft Graph with an app registration limited to that one mailbox (an Exchange application access policy). The credential lives in the macOS Keychain.
     - It never downloads bodies or attachments.
     - The exact BC filename pattern ("Sales Quote …") is unverified; the first job of the two-desk proof (§11 S5) confirms it.
   - **Customer PO's:**
     - Classify every file first. UCLA advisories, GSA Advantage orders, DGS BPO releases and receipts, P-card notices, private releases, duplicates, amendments and cancellations are **orders, not RFQ wins**, unless they match a logged RFQ, in which case they are that RFQ's win.
     - For candidate POs, extract a **whitelist only**: quote number (`SQ-1xxxxx`, 5-digit Provision Connect quote#, 900-series), PO number, customer business unit, pre-tax total, line SKUs, PO date. Text-layer PDFs are read directly; image-only PDFs go through **local** `ocrmypdf` / `tesseract`. Full text is discarded in memory and never written.
     - Filer-appended `SQ-`/`so-` numbers in filenames count as evidence.
     - Week comes from the folder name; file dates before about 2026-09-07 are unreliable.
2. **Matcher**: a pure function of evidence plus records. It writes **proposals**, a diff of stage and header changes per deal, to `Customers/_Pipeline/proposals/YYYY-MM-DD.json`. It never touches `RFQ.md`.
   - **Sent:** the first mailbox hit for a BC quote number that a record holds in `BC quote`. A BC quote number with no record becomes a "quote with no RFQ record" item for the rep.
   - **Win evidence differs by desk** *(call made after the builder check; Parker to confirm it fits R-S3)*. `Customer PO's` holds almost no Bechtel or USACE POs, so the matcher reads three sources:
     1. A BC sales order whose **Quote No.** equals the record's `BC quote`. That is Make Order: Sentinel today, CA if O4 is adopted.
     2. A PO file in the deal folder's own `PO/` subfolder (Sentinel convention, e.g. `rfq-845311/PO/PO 851270 Rev. 00.pdf`).
     3. A match in `Customer PO's`.
   - **Won, Tier 1:** exact-key evidence where customer and pre-tax total check out to the cent or within the stated tolerance. Any one of these counts:
     - a PO that cites our quote number;
     - a BC sales order whose Quote No. is the record's BC quote;
     - a PO in the deal's own `PO/` folder.

     Quote numbers are checked against BC, never by regex alone, because Claude-built PDFs reused guessed SQ numbers. All Tier 1 sources share the same shadow bar.
   - **Won, Tier 2 (probable):** customer (FI$Cal business unit → BC customer map) plus pre-tax total plus PO dated 0–90 days after sent, with Grainger item numbers as tie-break. Shown as "+n probable" and never counted until folded.
   - **Agency tracking or RFQ number:** CDCR PR#, DOJ tracking, CMD Estimate# matched against `Solicitation #` or BC quote `externalDocumentNumber`. This counts as Tier 2 unless a quote number also matches.
   - **No answer (proposed only):** sent, outcome window closed, no PO, and no recorded loss. Windows:
     - the quote's own `Valid until`, if set;
     - otherwise CA NASPO/BPO 30 days after sent, CA competitive 45 days (PR #90 item 5);
     - federal and Bechtel 90 days, provisional (98% of CA quote-to-order pairs closed within 90 days) until measured from Sentinel's quote-log.
     - Separately, "silent after send" is flagged at 14 days (D07.3).
   - **Seeded records:** a deal folder in a bound desk with no `RFQ.md` produces a "create record" proposal. Its header is seeded from the README, request email or inbound files, and unknowns are written as `[FLAG]`. This is how Ollie-created Sentinel folders get a record without anyone remembering, and the record is still created only on approval *(call made after the builder check)*.
   - Scope filter applied before matching (body armor, CSU/UC out of the CA book).
3. **Fold**: a new `/rfq-fold` command. It reads the latest proposals, shows a review sheet grouped by rep and desk, and applies what the rep approves by name through `rfq_record.py` (`set-stage`, `set-header`, and a `record-event` that appends the quote-log row — sync spec slices 4–7).
   - **One fold path** *(call made after the builder check)*. `/rfq-fold` replaces the planned `/ca-rfq-fold`; the 2026-11-12 spec's slices 4–7 are retargeted to it.
   - The dashboard drawer keeps one-click capture: **Mark sent** (for portal submissions the mail rule cannot see), **Won**, **Lost + reason**, **No bid**.
   - Clicks land in the artifact's database as an **inbox of proposals**. `/rfq-fold` reads them alongside the engine's proposals and clears each one when it is folded or rejected. It is never a status store: the record stays the only truth.
   - **Tier 1 wins after the shadow bar (R-S3)** are applied by the engine with `--by matcher` and appear on the next fold sheet as "auto-won — undo?".
   - Every applied write is logged with before and after in `Customers/_Pipeline/applied.jsonl`. `set-stage --correct` (#96) reverts.
   - **Shadow mode:** until Parker signs the bar (≥95% precision on ≥30 Tier 1 cases), Tier 1 is proposed like everything else, and a precision report is produced from rep folds. **Quinn** owns the false-positive review and the precision report; Parker signs the pass.
- **Runs as** a routine on Parker's Mac, staged **OFF** until Parker switches it on. n8n or Power Automate is used only for event capture if ever needed. Reps never run it.
- **Ledger.** `quote-log.md` becomes a ledger written by `record-event` from record changes, not by hand. It lives at the profile's `ledger_level`. Sentinel's `learning/quote-log.md` stays its outcome ledger (D10.5), now appended by events for new RFQs.

### 6.6 Learning loop

| Moment | What is captured | Where |
|---|---|---|
| Any time a rep states a preference, change or watch-out | the rep's words, dated, by name (`desk-remember`) — agents use it **always**, on every desk | `LEARNED.md` at the profile's ledger level |
| Process failure caught or missed | blameless FLAGS row | `FLAGS.md` |
| delivered to rep / sent (within 1–2 days) | 1–3 lines: what was hard, what we'd do differently, any vendor/part lesson | `## Lessons` in `RFQ.md`; Gate 9 close-the-loop prompt (#100 `desk-learn` hook) |
| outcome fold | reason (short list: price, lead time, spec/substitution, compliance, no decision), public award price and vendor where findable, rep's guess marked as a guess | `## Outcome notes` in `RFQ.md` |
| monthly, 30 minutes | the last 30 days of losses and silences reviewed for patterns; recurring lessons **promoted** into the desk `CLAUDE.md` / `PROCESS.md` with dated attribution (Sentinel's pattern) | desk `learning/lessons.md` (append-only), desk `CLAUDE.md` |
| quarterly | pricing review (§6.7) | desk `learning/margin-tracker.md` |

- **Loss verification:** rep loss reasons are often wrong, so a stated reason is checked against the public record where one exists: SCPRS line items and California bid/award information on request (SCM 14-04-1); DLA DIBBS award search; a FAR 13.106-3(d) brief explanation or FAR 15.506 debrief. Bechtel awards are not public; Sentinel loss reasons come from the buyer.
- **Context injection** (`desk-memory`, `desk-context`) works from the registry on every desk. Every session that touches a deal sees its `LEARNED.md` chain, recent quote-log precedent, open FLAGS and overdue close-outs.
- Each desk has `learning/PROCESS.md` (the loop) and `learning/lessons.md`; the desk `CLAUDE.md` @-links `PROCESS.md`. The CA desk's `learning/PROCESS.md` (created 2026-11-16) and empty `lessons.md` are the start.

### 6.7 Pricing loop

**Scope:** only lines a rep prices. NASPO and California-schedule lines (Grainger at cost), and any other at-cost contract line, are excluded. At-cost status is keyed on the BC CONTRACT dimension.

**Per-line price panel** (Pru's set). Computed by a script into a `pricing-evidence.json` sidecar in the deal folder. It holds values, not formulas, and is read by the dashboard drawer and the quoting workbook's Price Analysis tab.
- cost and **Cost basis**
- lowest credible same-part public price, with seller, URL, date and grade
- price index (sell ÷ lowest public)
- status: HOLD / EXPOSED / ROOM / THIN
- rebate Y/N
- freight: included, or a separate line at cost
- lead time against the RDD, plus stock
- SUBSTITUTE flag (comps for a substitute are a different product)
- contract ceiling where a vehicle caps the price (GSA MAS, Sourcewell, NPPGov)
- last three won prices, each with date, customer, source and unit
- band target / floor / stretch

**Never customer-facing, and never in BC line comments:** cost, cost basis, CSP or vendor quote numbers, supplier names, Grainger account, rebate, margin, band, floor, status, comps, SCPRS competitor names.

**Learning bands without enough data:**
- **Cells.** 4–6 company-wide cells: desk × lane (Grainger CSP vs non-Grainger) × size (micro under $15K vs package). Today there are 8 won and 3 lost on Sentinel's quote-log and 2 final outcomes on CA, far below 30 per cell.
- **Ladder first.** Until a cell has about 15 decided quotes, show a **ladder** (highest margin won, lowest margin lost) pooled toward the desk band. After that, hit rate by margin band and expected GP (win rate × GP$); target = the band with the highest expected GP; floor = the band below which win rate stops rising; stretch = one band above target.
- **One margin basis.** Nominal, product only, with freight and rebate in their own columns. Compare by **price index**, not margin alone: margin moves with our cost.
- **Review cadence.** Quarterly. Bands move at most 1 point per cycle. No random price tests at this volume. A competitive win rate above 55–60% is read as a sign of under-pricing.

**Data for "last won price":**
- BC posted sales invoice lines: unit price, UoM and qty per unit, date.
- Actual cost from value entries or purchase invoice lines, never item card cost.
- CONTRACT and CUSTOMER dimensions, to exclude at-cost, body armor and CSU/UC lines.
- Item references, to join a Grainger-SKU card to its manufacturer-PN card.
- Archived quote lines, to count losses. This depends on Archive Quotes = Always (§10).
- Customer PO unit prices from the latest revision, confirmed matches only, skipping $0 MOQ lines.

**SCPRS's role** is open ruling O2. Until it is ruled, SCPRS is context only and never moves a sell price, as today.

### 6.8 Dashboard

- **One page.** Extend the existing **CA State RFQ Pipeline** artifact (`S1c4MohDvAVV9VgbJowohY`) into the cross-desk pipeline with a **desk filter**. Do not build a third page.
  - The Sentinel artifact (`Cuxxw7Qn9qU7it5u9pXJRR`) keeps running until the cross-desk page covers Sentinel. Retiring it is Parker's call.
  - Its data becomes a projection of `RFQ.md` sidecars for new RFQs (R-S4), plus the existing hand-curated rows for old ones until they close.
- **Data:** the scanner (`build_rfq_index.py`) reads `desks.json` and walks each desk root.
  - It stays read-only by contract.
  - It reads sidecars, the pricing-evidence sidecar, proposals and the applied log.
  - `rfq_lines.json` is fed from each `RFQ.md` Pricing table, so lines with vendor, cost and sell show **before** a BC quote exists. Live BC lines appear once a quote exists.
  - Location: one copy, versioned in the marketplace (the builder decides between moving it into `bbs-sales/scripts/pipeline/` and keeping it in the CA docs tree with a profile-aware reader).
- **Drawer:**
  - status timeline with proof badges
  - lines with the price panel (internal only)
  - checklist (profile option)
  - waiting-on and next action
  - proposals pending fold
  - one-click capture: Mark sent (portal), Won, Lost + reason, No bid. Each click goes to the fold inbox, never to the record directly (§6.5).
  - lessons
- **Metrics** (Quinn's definitions; each shows its n):
  - **Hit rate** (headline):
    - Formula: won RFQs ÷ RFQs **sent** whose outcome window has closed, per RFQ, in scope, excluding no bid and cancelled; revisions count as one deal.
    - Printed as a floor ("At least x%"), with outcome coverage and the decided-only rate as the upper bound.
    - Under 30 closed RFQs it reads "not established".
    - Segmented by desk and vehicle; never pools NASPO with competitive.
    - A dollar-weighted rate is a second, labelled figure.
  - **Bid rate:** sent ÷ logged, counting RFQs whose due date has passed.
  - **Response time:** median and p75 days from received to sent, and on-time share.
  - **GP$ per quote sent:** trailing 90 days. NASPO line GP is 0; the page says whether rebate is included.
  - **Hit rate by margin band:** rep-priced decided lines only, using the ladder rule above.
  - **Cycle time from sent to PO:** uses the PO's own date, never BC orderDate (orders are re-dated by ship week).
  - **Record health, as KPIs:** share of `RFQ.md` files that validate; share of sent RFQs with a sent date; outcome coverage; share of POs matched to an RFQ; join-key fill (`BC quote`, `CRM RFQ`).
  - **Stale** (over 30 days with no movement) and **expired** quotes, by name and dollars.
- **Privacy gate:** `rfq-pipeline/scripts/privacy_gate.sh`, extended with a 13–16-digit **Luhn-checked card-number class**, plus a test proving a GSA card number is blocked. The gate must pass on every publish. Pages stay private until Parker shares them.

### 6.9 CRM continuity

- **CRM continuity applies only to desks whose reps already keep `bbs_rfqs` records**, which today means California state *(call made after the builder check; confirm under O9)*. Other desks are folder-only from day one. No new CRM entry is created for them, and `CRM RFQ` is a `ca-state` profile key, not a core key. This keeps R-S5 from creating new hand-kept work.
- On the CA desk, write `CRM RFQ` into `RFQ.md` at intake; it is the only shared key.
- A weekly keyed parity check per rep compares folder `sent` with CRM `bbs_rfqs` Submitted.
- The mail-rule capture serves as a third check on `sent`.
- **Per-desk switch** (R-S5): two straight weeks where folder `sent` and CRM Submitted agree within 1 per rep per week, with ≥90% of in-scope deals carrying a sent date (the CA rule, PR #90 item 6). After that, reps stop setting CRM Submitted for that desk.
- The program's one metric stays on `bbs_rfqs` until the CA switch.
- Claude never writes the CRM. When a rep's record needs a change, the rep gets a field table to apply.

## 7. Plugin changes (bbs-sales)

| Area | Change |
|---|---|
| `references/desks.json` (new), `references/desk-profile.md` (from branch) | The registry and its doc (§6.2) |
| `scripts/rfq_record.py` | v3: desk from path; core plus profile-required keys; `Valid until`; `Cost basis` column; `## Lessons` / `## Outcome notes`; `record-event` (quote-log append); no `naspo` inference outside `ca-state`; v2 compatible. #96's `set_stage` rewrite (conflict refusal, `--correct` / `--by`) lands first. |
| Hooks (`guard-tree`, `desk-context`, `desk-memory`, `rfq-record-hook`, `desk-post.sh`, #100's `desk-learn`) | Read `desks.json` instead of the `All RFQ's by Agency` literal (Rex's list: `guard-tree.py:23` / `.ps1:14`, `desk-context.py:30` / `.ps1:22`, `desk-memory.py:37` / `.ps1:30`, `rfq-record-hook.py:24` / `.ps1:26`, `rfq_record.py:908`, `desk_memory.py:46`; Otto counts 23 files containing the string on main — sweep them all). Guard rules per profile. Twins and parity tests change together. CA behaviour byte-identical. |
| `skills/desk-remember` | Profile-driven on every desk; `desk_memory.DESKS` removed in favour of the registry |
| `skills/ca-rfq-intake` | Unchanged name. Writes `CRM RFQ` and `Valid until` when known. |
| `skills/rfq-intake` (new) and `commands/rfq.md` (new) | Desk-agnostic intake and run for non-CA desks. A CA request routes to `ca-rfq-intake` / `/ca-rfq`. An unknown customer folder gets a proposed registry entry, approved by name. Certification channel comes from the profile. |
| `skills/bc-quote-entry` | After the read-back, writes `BC quote` and stage `quote built` through `rfq_record.py`. Comment-line support is the precondition for retiring Sentinel's one-off `bc_build_rfp*.py` scripts (open ruling O5). |
| `commands/ca-rfq.md` | Gate 9 close-the-loop (from #100): `## Lessons`, and the stage write for the gate just run |
| `commands/rfq-fold.md` (new) | Reviews engine proposals and dashboard clicks, folds them by name (§6.5). Replaces the planned `/ca-rfq-fold`. |
| `scripts/rfq_record.py bind-desk` (new subcommand) | Writes an approved customer binding to `Customers/_Pipeline/desk-bindings.json` (§6.2) |
| `scripts/outcomes/` (new) | `fetch_bc`, `fetch_sent`, `fetch_pos` (classify + whitelist extraction + local OCR), `match`, `propose`, `apply`. Pure matcher with fixture tests. Run by a Mac routine (staged OFF). Anything placed on the `bbs-fill` ALLOWED list needs its R3 ruling. |
| `scripts/pricing/` (new) | `price_panel.py` → `pricing-evidence.json`; `ladder.py` → per-cell ladder and bands from records and outcomes |
| `skills/bbs-weekly-sales-report` | Reads the registry (the weekly-report branch) |
| Tests | Fixture tests for the matcher, PO classifier, whitelist extractor (including a card-number redaction test), and v3 parser. Registry parity fixture for the hooks. Added to CI. |

## 8. Governance (light)

**Keep:**
- one steward;
- one non-author reviewer per PR (`rex`);
- the privacy gate with the card class;
- a probe against real data before anything is called done;
- approval by name for record writes;
- automations OFF until Parker switches them on.

**Cut:**
- the IA, UX and tone reviewer gates until a page is shared beyond Parker;
- 15-section charters, replaced by one page in the READ FIRST / DELIVER / RUN / FENCE / REPORT shape;
- pasting all eight traps into every brief (cite them instead);
- BUILD-LOG entries longer than about 10 lines.

One ledger of decisions: STEWARD.md for marketplace rulings, and the program `DECISIONS.md` for program decisions. The 2026-11-12 folder ruling and the §13.8 rulings get copied into `DECISIONS.md`.

## 9. Open rulings for Parker (recommendations given; the builder writes `[FLAG]` until ruled)

| # | Question | Recommendation |
|---|---|---|
| O1 | **Grainger sell rule for the channels still open.** Canon ("Grainger sell rule, by channel") already rules California state at cost (2026-09-18) and **primes such as Bechtel may be marked up** after asking the Grainger account manager for a discount (2026-09-28). That covers Sentinel's 6.0–11.0% Grainger-lane wins. Still open: national and local co-ops (Sourcewell, NPPGov, UC/OMNIA, local co-ops), direct federal, and private. | Rule each open channel as its first priced RFQ arrives. Until then, `[FLAG]` on those lines and no band. |
| O2 | **SCPRS adjustment rule** (Pru's TODO(human)) | Adopt Pru's (a)–(e):<br>(a) SCPRS never sets a sell below the floor, or above lowest VERIFIED public × 0.98.<br>(b) Same-model contestable lines, n≥3, last 12 months, with a median below the floor: mark EXPOSED and re-source first. If they are a large share of package cost, Parker decides no-bid.<br>(c) No VERIFIED public price but contestable n≥3: target 0.98 × the lower of the contestable median and the newest contestable price.<br>(d) Co-op lines and anything under n=3 are context only.<br>(e) On the CA desk, (c) may apply even when a public comp exists. |
| O3 | **Who stewards the parent program.** Otto's charter is CA-only (D01). | The marketplace `steward` owns the parent; Otto keeps the CA profile; Fiona advises on the federal profile. Or amend D01 so Otto owns it all. |
| O4 | **Make Order habit.** Whoever enters orders (po@) uses Make Order when a PO cites a BC quote, so the order keeps Quote No. | Yes: it makes BC a second win source. The matcher does not depend on it. |
| O5 | **Retire Sentinel's ~25 one-off `bc_build_rfp*.py` scripts** in favour of `bc-quote-entry` once it writes comment lines | Yes, after comment-line support lands. |
| O6 | **#98 vs #99** — both supersede R1 and contradict each other | Pick one; this design does not depend on either. |
| O7 | **Body armor and CSU/UC** | *Ruled 2026-11-17:* neither is in this build. CSU/UC is planned as an order desk (follow-up design). Their POs are classified as out-of-scope orders. Body armor is assumed out until Parker says otherwise. |
| O8 | **The program's one metric** (still reads Dynamics) | Hit rate (§6.8) per desk once outcome coverage passes 80%; until then, record health. |
| O9 | **Does D10.1 CRM entry end at each desk's switch, and do desks with no `bbs_rfqs` history stay folder-only?** | Yes to both (§6.9). |
| O10 | **Certification channel for buyers canon does not cover**: utilities (SDGE, PG&E, SCE), counties other than LA County, cities other than San Diego, schools | Rule per buyer type as each first intake arrives. Until ruled, intake flags it and the packet step stops for the rep. |

## 10. Day-1 actions (Parker; no build needed)

Outcomes take calendar time, so evidence collection starts before anything is built.

1. **Create the Exchange mail flow rule** (R-S1).
   - Outbound mail from internal senders, where an attachment's file name matches the BC sales-quote pattern, is BCC'd to a new logging mailbox. Confirm the pattern by emailing one BC-printed quote to yourself.
   - Apply a ~90-day retention policy to that mailbox.
   - Set up read access for the Mac script: an Entra app registration with `Mail.Read` (application), admin consent, and an **Exchange application access policy** restricting that app to the logging mailbox alone. The credential goes in the macOS Keychain. S5 cannot start without this.
   - Before the rule goes live, tell everyone who sends quotes (Kim, Aanya, Griffin and others) that the sender, buyer domain, time and quote number of their quote emails are captured. Recommended.
   - Update the organization-level instruction on mail access, which says mail access is the signed-in person's, to record the R-S2 exception. S0 drafts the text.
2. **BC:** Sales & Receivables Setup → **Archive Quotes = Always**. Confirm the Delete Expired Sales Quotes job is not scheduled.
3. Set `Customer PO's` to **Always keep on this device** on your Mac, so PO reading never hits cloud-only placeholders.
4. Decide O4 (Make Order) with whoever enters orders.
5. Bring open PRs to five or fewer (six are open, #96–#101). Pick O6.

## 11. Build sequence

Each slice is a draft PR in `bbs-claude-marketplace` unless noted. `rex` reviews and Parker merges. Merge order follows Rex.

| Slice | What | Done when |
|---|---|---|
| **S0** | Docs/rulings PR: record D10.x and R-S1…R-S6 in `STEWARD.md`; amend `canonical-facts.md` (systems of record, what counts as a win, R6/D10.5 wording); draft the managed `claudeMd` text and the organization-instruction mail-access exception for Parker to paste | Merged; managed settings and org instructions re-pasted |
| **S1** | #96 (`set_stage` rewrite): fresh review at its current head, merge | Merged |
| **S2** | `desks.json` + loaders in every hook twin, `rfq_record.py`, `desk_memory.py`; `check_marketplace.py` alternation check; CA behaviour byte-identical; parity fixtures on the registry | CI green; CA hook outputs unchanged on fixtures |
| **S3** | #100 merged up from `main` and reworked onto the loader (`desk-learn`, `bechtel-sentinel` profile, Gate 9) | Merged; no desk literal left |
| **S4** | Weekly-report branch reading the registry | Merged |
| **S5** | **Two-desk proof** (read-only script, can run beside S2–S4 once the mail rule has ~2 weeks of data). For each BC quote: sent per mailbox metadata? exact-quote-number PO match? which deal record does it join? Reports the join rate per desk (`ca-state`, `bechtel-sentinel`) and lists every unmatched row. Confirms the BC filename pattern. Writes nothing. | Parker has read the join report |
| **S6** | Schema v3 + `rfq-intake` / `/rfq` for non-CA desks; `bc-quote-entry` writes `BC quote` + `quote built`; Sentinel new RFQs adopt `RFQ.md`; `account` profile bound to the first live customers (USACE Walla Walla, Federal Agencies, SDGE, Hanford, Kern) as their next RFQ arrives | A real non-CA RFQ and a real Sentinel RFQ validate end to end |
| **S7** | Outcome engine (fetchers, classifier, whitelist OCR, matcher, proposals, `/rfq-fold`, applied log, `record-event` quote-log append); privacy gate card class + test; routine staged OFF; Tier 1 in shadow | First fold run by a rep; precision report started |
| **S8** | Dashboard: registry-aware scanner, desk filter, lines before BC, price-panel drawer (internal), Quinn's metrics, record health; Sentinel data from sidecars for new RFQs; publish privately (page 1 publishes privately now, without waiting) | Parker opens the page; privacy gate passes |
| **S9** | Pricing loop: `Cost basis` in use, `price_panel.py`, `ladder.py`, quarterly review routine staged OFF; SCPRS rule after O2 | One live RFQ priced with the panel |
| **S10** | Learning: `## Lessons` / `## Outcome notes` in use on all desks, per-desk `lessons.md` + `PROCESS.md`, monthly review routine staged OFF | First monthly review held |

## 12. Left to the builder

- Exact key names in `desks.json` and v3, provided §6.2–6.3 hold.
- Whether `account` is one profile or splits into `federal` and `local`.
- Scanner location (§6.8) and `_Pipeline/` exact paths.
- Tolerances for Tier 1 totals (tax, freight, rounding) and the FI$Cal business-unit → BC customer map.
- OCR tooling details, as long as it is local and whitelist-only.
- How `rfq-intake` and `ca-rfq-intake` share code.
- Dashboard layout within the existing page's design system.

## 13. Sources

- **Scouting reports (2026-11-16, read-only):** Sentinel desk; CA desk; bbs-sales plugin; `Customer PO's`; other customer folders. Digest kept in the session scratchpad and summarised in §1, §4.
- **Agent reviews of the proposal (2026-11-16):** Otto, Dara, Quinn, Pru, Rex. Every change they asked for is folded into §3, §6, §8, §11.
- **Key repo and folder files:**
  - `plugins/bbs-sales/scripts/rfq_record.py`
  - `docs/STEWARD.md` (~231–264)
  - `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md` (~135–160, 184–199, 261–265)
  - `Customers/State of CA Agencies/docs/dashboards/rfq-pipeline/` (`STAGE-RULES.md`, `METRICS-SIGNOFF.md`, `scprs/OUTCOME-RULE.md`, `scripts/privacy_gate.sh`)
  - `Customers/State of CA Agencies/sales-process/docs/pm/DECISIONS.md` (D01, D07–D10)
  - `Customers/Bechtel/sentinel/learning/` (`PROCESS.md`, `margin-tracker.md`, `quote-log.md`, `dashboard/STAGE-RULES.md`)
- **Web research (2026-11-16):**
  - Microsoft Learn on BC: sales-how-make-offers, across-how-to-archive-documents, salesQuote and salesOrder API v2.0, marketing-set-up-email-logging, sales-order-agent; Microsoft BCApps source (Sales Header field 153, `EmailRecords`).
  - Exchange mail flow rule conditions; RBAC for Applications.
  - Phocas "State of Sales in Distribution 2026" via Distribution Strategy Group (2026-09-21).
  - Pipedrive on manual BCC (2026-01-09).
  - Esker / Conexiom / Rossum order-automation benchmarks (vendor).
  - Clozd on win/loss accuracy (vendor, 2026).
  - ProfitOptics safe zones (2026-01-06); Umbrex on win rate by discount; Zigaflow on under-pricing (2026-08-09).
  - BCG industrial distributors (2023); Distribution Strategy Group pricing leakage (2026-06-04).
  - FAR 13.106-3 and 15.506 (FAC 2026-01); DGS SCM 14-04-1; GSA OIG A240054-1 (2026-08-13).
