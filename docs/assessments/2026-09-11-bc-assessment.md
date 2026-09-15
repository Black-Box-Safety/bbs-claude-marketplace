# Business Central Assessment — Black Box Safety, Inc.

**Prepared 2026-09-11 from live read-only BC data (21 API calls), the rep-workspace rollout
design, MANAGED-SETTINGS.md, and the naspo-quote skill.** Perspective: Microsoft SMB
solutions architect (BC + AI). Companion to
`docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md`.

**Environment:** BC Production, company "Black Box Safety, Inc.", El Cajon CA. License
experience: **Essentials**. Calendar fiscal year, USD. ~150 API v2.0 entity sets exposed
via the read-only "BC MCP (Custom API)" connector.

---

## 1. How BBS uses BC today

### What is genuinely in use — more than most 9-person shops

**Sales quotes exist in BC, in volume.** 601–800 quotes carry a document date in the last
90 days (skip-probes: a record exists at position 600, none at 800). The most recent 200
span only Aug 21–Sep 10 — roughly **10 quotes per business day**, totaling $2.29M excl.
tax across those 200. Salesperson codes are actively maintained (BA-CF 41, CA STATE TEAM
38, BA-JA 29, KQUEZON 23, JEFF 20, HOUSE 15, CARLOS 14, JMAGLIATO 13; only 5 blank). So
quoting does *not* happen entirely outside BC — but see the two gaps below.

**Sales orders: 3,001–4,500 in 90 days** (record at skip 3000, none at 4500) — ~45–70 per
business day. The last 200 span just Sep 8–11. 158/200 carry a customer PO in
externalDocumentNumber; 187/200 fully shipped. Top customers of the last 200: LA Dept of
Water & Power (63 — looks like a per-employee program, e.g. safety-boot vouchers), UCLA
(12), SJSU (9), CSUSM (5), Centinela State Prison, CAL FIRE, CHP. **Shopify orders already
flow into BC**: a generic `SHOPIFY` customer with `SHOP #nnnn` PO references and `SO-`
orders per web sale.

**Sales invoices**: >200 posted in 90 days (INVP- series); of the newest 200: 160 Open,
39 Paid, 1 Canceled; some future-dated to 2026-12-31.

**Purchasing is real.** >200 POs since Jun 13 (some dated out to Dec 17). Of the last 200:
**Grainger 125, Point Blank Enterprises 45**, First Tactical 5, long tail of 1–2s; $316k
excl. tax. The drop-ship model is visible end to end: customer order → Grainger/PBE PO.

**Vendor master: 200+ records** — but it mixes trade suppliers (Grainger, Point Blank,
Streamlight, Damascus) with expense payees (Starbucks, In-N-Out, DoorDash, Hilton,
T-Mobile, United Airlines, "Fuel", "Travel", "MISC VENDORS"). AP/expense coding runs
through BC too.

**Item master: >15,000 items** (record exists at skip 15000) — the same order of magnitude
as the 18k Supabase catalog, but a *different* universe: raw manufacturer SKUs
(`010-02704-00`, `3LU92` — that's a Grainger stock number), not the Supabase
`BBS-[MFG]-[SKU]` scheme. Hygiene is poor: numbers like `,LF886V - 4`,
`(2) CUBE 70V WHITE`, `05`, `035`; a large share have unitCost = 0. All sampled items are
type "Inventory" but on-hand is almost universally 0 (occasional 1–3 units) —
**operationally a drop-ship/non-stock business with item cards created ad hoc per deal**.

### What is configured but not used

- **Dimensions: three exist — AREA, CONTRACT, CUSTOMER** (created 2025-03-10). Exactly the
  right skeleton for agency/contract-vehicle reporting. Dimension *values* check errored
  on a field name (noted, not retried per budget), and document-level usage is unverified —
  but three dimensions untouched since creation day, 18 months ago, strongly suggests they
  were scaffolded and never populated. **Flag: unverified.**
- **Quote lifecycle fields**: sentDate set on **0 of 200** recent quotes; acceptedDate on
  **5 of 200**; 195/200 sit at Draft forever. Quotes are typed into BC but their pipeline
  state is not tracked — win rate is uncomputable from BC today.

### What is empty / unused

- **Projects/jobs: 0 records.**
- **Approval workflows: none.** Only the stock Microsoft templates exist, every one
  `enabled: false`.
- Assembly, transfers, physical inventory, fixed-asset locations: standard entity sets
  present, no evidence of use (consistent with drop-ship).

### The AR picture

The 50 oldest unpaid invoices total only **$23.2k** — collections are not on fire. But the
list is dominated by the `SHOPIFY` customer: invoices due-on-receipt, aged Feb–Jun 2026,
for individual buyers. Shopify checkout is card-paid, so these are almost certainly
**paid orders whose payments were never applied in BC** — a cash-application/reconciliation
gap, not a collections problem. The genuine government AR overdue is small and specific:
Santa Ana PD $3,339, CHP Vallejo $2,011 (2 invoices), CHP Golden Gate $2,019, CHP Dublin
$1,019, DSH-Sacramento $611, plus sub-$300 stragglers at CSUM, SJSU, El Dorado Probation.

---

## 2. Gaps vs SMB best practice — ranked by business impact

**Gap 1 — Two quote systems that never meet (highest impact).** BC has an SQ- series
(~10/day). The Claude NASPO workflow builds a *separate* 900001-series quote PDF in the
SharePoint folder, priced via the Grainger MCP, that never touches BC. When a 9000xx quote
wins, someone re-types it as a BC order; the quote itself — pricing, solicitation number,
account — is invisible to `bc_get_sales_document`, `bc_customer_snapshot`, and every future
precedent search. Cost today: re-typing (~10–15 min/win, error-prone on at-cost lines where
a typo *is* margin), no single quote history per buyer, and the Claude connector — assigned
to **everyone** precisely as "quote of record" per MANAGED-SETTINGS.md — can't see the
quotes Claude itself drafted. Effort to fix: process + one skill edit, near zero config.

**Gap 2 — No quote outcome tracking.** sentDate/acceptedDate/validUntilDate unused → no
win rate, no quote-to-order conversion, no aging of open quotes, in a business quoting
~$1M+/month. The rollout's planned "nightly audit" digest has to scrape `quote-log.md`
files because BC can't answer "which quotes are going stale." Cost: bids silently die;
nobody can say what % of CDCR quotes convert. Effort: behavioral (two clicks per quote) —
the hard part is habit, not config.

**Gap 3 — Dimensions scaffolded, (apparently) never populated.** With CONTRACT and
CUSTOMER/AREA empty on documents, BC cannot answer the questions that define this
business: profitability per agency, revenue per contract vehicle, and — critically —
**separating NASPO at-cost rebate revenue from margin business**. Today the P&L blends
$0-margin NASPO lines with normal-margin lines, so gross-margin reporting is structurally
misleading, and rebate-owed-by-Grainger has no BC-side denominator to check payments
against. Cost: no per-agency P&L, no rebate audit trail, misleading margin. Effort: a
focused day or two (populate values, set defaultDimensions on the top ~100 customers and
the CONTRACT value per document) — configuration only, but requires sustained data
discipline afterward.

**Gap 4 — Shopify cash application.** Dozens of aged "unpaid" Shopify invoices that were
paid at checkout. Cost: AR reports are noise, `bc_list_unpaid_invoices` (a rep-facing
tool!) returns false positives, and month-end reconciliation is manual. Effort: modest —
if the native Shopify connector is already the order path, enabling its payout/payment
mapping is configuration; if orders arrive via a custom import, a weekly cash-receipt
journal routine closes it.

**Gap 5 — Item master hygiene.** 15k+ ad-hoc item cards, malformed numbers, zero costs on
a large share, and no linkage to the Supabase 18k-catalog SKU scheme. Cost: `bc_find_item`
(BC text search is case-sensitive, so messy names are doubly unfindable), unreliable
margin per line, duplicated item creation effort. Effort: honest answer — **high** to fix
retroactively; cheap to stop making worse (an item-creation convention + Copilot
analysis-mode dedupe checks). Do not attempt a big-bang renumber.

**Gap 6 — No approvals anywhere.** Zero enabled workflows. For 9 people this is mostly
fine (don't over-govern), but two narrow ones are best practice even at this size: PO
above a threshold, and credit-limit override. Cost today: low, latent. Effort: low
(native BC workflow templates already sit there disabled).

---

## 3. Low-hanging fruit

All items below are configuration-only or near-config, included in BC Essentials + M365,
and near-zero maintenance for a solo self-taught admin.

### 3.1 Make the BC sales quote the system of record for Claude-drafted quotes ⭐ do this first
- **What:** Every Claude/NASPO quote gets entered as a BC sales quote before (or
  immediately after) it goes to the buyer. Connector is read-only — correct posture, keep
  it — so the rep pastes/creates the SQ in the BC client; the naspo-quote skill adds one
  step: "create the BC quote, put the SQ number in `cover_summary.md` and `quote-log.md`;
  put the solicitation number in externalDocumentNumber." Claude then reads it back via
  `bc_get_sales_document` to verify totals match the packet.
- **Value:** kills re-typing on wins; one quote history per buyer; the compliance packet
  and the priced quote become cross-checkable.
- **Effort:** 2–4 hours (skill edit + one team huddle). Zero BC config.
- **Compounds with Claude:** `bc_get_sales_document` becomes the precedent search ("what
  did we quote CMC for these items in March?"), `bc_customer_snapshot` becomes a true
  account review, and the `/bbs-checkup` BC verification exercises the exact tool reps use
  daily.

### 3.2 Use sentDate / acceptedDate / quote-to-order conversion
- **What:** When a quote is emailed, mark it Sent; when won, convert to order in BC (one
  action, carries every line) instead of re-keying.
- **Value:** win rate and stale-quote aging become queryable; conversion eliminates the
  last re-typing step.
- **Effort:** ~1 hour to demonstrate; ongoing cost is two clicks per quote.
- **Compounds:** the planned nightly audit digest can compute "quotes >14 days with no
  sentDate / past validUntilDate" from BC via one `bc_query_entity` filter instead of
  parsing quote-log files.

### 3.3 Populate the existing dimensions (AREA, CONTRACT, CUSTOMER)
- **What:** Define values (CONTRACT = NASPO / CMAS / GSA / OPEN / SHOPIFY; CUSTOMER or
  AREA = agency family: CDCR, CHP, CalFire, CSU/UC, LADWP, FED, LOCAL), then set
  defaultDimensions on customers so documents inherit them with zero per-order effort.
  Verify first whether values already exist (the check errored).
- **Value:** per-agency and per-vehicle revenue/margin; NASPO at-cost revenue finally
  separable from margin business — the rebate denominator Grainger's statements can be
  audited against.
- **Effort:** 6–10 hours once (values + top ~100 customers), then self-maintaining via
  defaults.
- **Compounds:** Claude can filter `bc_query_entity` by dimension for instant "CDCR revenue
  this quarter" answers, and dimension codes give the ca-procurement-intel work a BC-side
  join key.

### 3.4 Teams BC app for reps
- **What:** Install/pin the Business Central app in Teams (admin-center push). Reps paste
  a BC link or search a customer/quote in chat and everyone sees the record card without a
  BC license prompt for lookups.
- **Value:** "where's SO-10012041?" stops being a Parker interrupt.
- **Effort:** 1–2 hours including the setup-guide screenshot section.
- **Compounds:** same M365 connector surface Claude already uses; the rollout's
  Teams-notification intake flow and this land in the same channel habit.

### 3.5 Copilot-in-BC features (included, already licensed)
- **What:** Enable/confirm the free first-party Copilot features: **analysis mode** (ad-hoc
  pivots on lists — the item-dedupe and "orders by agency" tool that otherwise becomes an
  Excel export), **bank reconciliation assist** (directly attacks the Shopify
  cash-application backlog), **sales line suggestions** (paste a buyer's item list into a
  quote), marketing text (skip — story lives in Supabase/Shopify).
- **Effort:** 1–2 hours to switch on (Feature Management / Copilot & AI settings) and demo.
- **Compounds:** doesn't compete with the Claude rollout — Copilot-in-BC lives inside the
  ERP client for the accounting seat, Claude owns the rep workflow. (The rollout's "no
  M365 Copilot" ruling is about the chat assistant splitting the AI habit; in-BC features
  are feature toggles, not a second assistant.)

### 3.6 Late Payment Prediction (free first-party extension)
- **What:** Install from AppSource (Microsoft, $0), it scores open invoices on payment
  history.
- **Value:** modest but real for 30–60-day government AR — flags which CHP/DSH invoices
  will slip.
- **Effort:** ~1 hour. **Prerequisite:** clean the Shopify pseudo-AR first (3.7), or the
  model trains on noise.
- **Compounds:** the nightly audit digest can pair predictions with
  `bc_list_unpaid_invoices(overdueOnly)` for a one-line weekly AR nudge to Teams.

### 3.7 Shopify payment reconciliation
- **What:** First determine how `SHOP #` orders reach BC today. If it's the native
  BC-Shopify connector, enable payout/transaction mapping so checkout payments post
  against the invoices; if a custom path, a weekly cash-receipt journal (Copilot bank-rec
  assist helps) clears the backlog.
- **Value:** AR truth; `bc_list_unpaid_invoices` stops crying wolf to every rep.
- **Effort:** 2–6 hours depending on which path exists.
- **Deliberate flag, not a push:** the **catalog** direction stays with Supabase — the
  18k-product pipeline (family grouping, image-quality gates, category mapping) is
  deliberate and the native connector's item sync would fight it. Native connector for
  *orders/payments* only, items sync **off**. Do not "simplify" the catalog into BC.

### One near-config item to defer, consciously
**Approvals (BC native templates or Power Automate):** enable at most one — PO above $X —
and only after the rollout's v1 gate passes. Nine people, and every approval flow is a
thing that pages the solo admin when it sticks. The rollout already adopts exactly one
Power Automate flow (RFQ intake); keep it that way for now.

---

## 4. What NOT to do

- **AL extensions / per-tenant custom code.** One self-taught admin, no dev pipeline,
  breaking waves twice a year. Anything an AL extension would do here is either config
  (above) or belongs in the Claude/Supabase layer they already maintain.
- **ISV add-ons** (rebate-management suites, EDI packages, quoting add-ons, "government
  contracting" verticals). Subscription cost, upgrade coupling, a second vendor to chase.
  The rebate math is one dimension + one spreadsheet away.
- **BC Premium upgrade.** Manufacturing and service management — nothing in the data
  (0 assembly orders in use, 0 jobs) justifies the per-seat jump.
- **Native Shopify connector item/inventory sync.** Restated deliberately: order/payment
  sync yes (investigate), catalog sync no — it would collide with the Supabase pipeline
  that is the company's actual moat.
- **A retroactive item-master renumbering project.** 15k items feeding years of ledger
  entries; renumbering breaks history and precedent search. Convention going forward +
  dedupe on creation; let the tail age out.
- **Jobs/Projects module for RFQs.** Tempting mapping, wrong tool — RFQ tracking already
  lives in the folder/quote-log system the rollout just standardized.
- **Warehouse management / locations / bins.** On-hand is ~0 across the board; this is
  drop-ship. Any WMS config is pure maintenance load.
- **Broad approval workflows or Copilot Studio agents touching BC.** Both create failure
  modes only Parker can debug; Copilot Studio was already consciously excluded by the
  rollout.
- **E-invoicing setup.** CA agencies pay through Fi$Cal/Cal eProcure and portal
  submission, not Peppol e-invoices. Zero payoff.
- **A second write-capable BC connector for reps.** The read-only posture is the design's
  safety property. If write access ever comes (e.g., Microsoft's first-party BC MCP server
  creating draft quotes), it should be a v2 decision with the same plan→approve→execute
  doctrine, not a convenience add.

---

## 5. Integration with the Claude rollout

| BC item | What it does for Claude on rep machines |
|---|---|
| Quotes in BC (3.1, 3.2) | `bc_get_sales_document` + `bc_customer_snapshot` become the precedent/account-review engine; quote-log.md gains an SQ- cross-reference so folder tracking and ERP agree; the connector-assignment rationale in MANAGED-SETTINGS.md ("quote of record") becomes literally true |
| Dimensions (3.3) | one-filter answers to "CDCR revenue this FY", "NASPO vs margin business" via `bc_query_entity` — the questions reps and Parker ask Claude today and get spreadsheet archaeology |
| Shopify reconciliation (3.7) + Late Payment Prediction (3.6) | `bc_list_unpaid_invoices` becomes trustworthy; the planned nightly audit digest gets a real AR line |
| Teams BC app (3.4) | record cards land in the same Teams channel as the intake-flow notifications — one place reps look |
| Copilot-in-BC (3.5) | covers the in-ERP accounting seat so nobody is tempted to point rep-Claude at write operations |

**Concrete lines for the rollout design's v1.1 / later list:**

1. **v1.1 — naspo-quote skill step:** "create the BC sales quote; record SQ number in
   cover_summary.md and quote-log.md; Claude verifies via bc_get_sales_document." (Pairs
   with the v1 acceptance gate — the unaided rep test should end with an SQ number.)
2. **v1.1 — quote hygiene habit:** mark Sent, convert on win. One paragraph in REP-SETUP.md.
3. **v1.1 — Parker admin task:** verify/populate the AREA / CONTRACT / CUSTOMER dimensions
   and set customer defaults. (First step: check whether dimension values already exist —
   this assessment couldn't verify.)
4. **v1.1 — Teams BC app push** + a screenshot section in the setup guide.
5. **Later — Shopify order-path investigation and payment mapping;** then enable Late
   Payment Prediction.
6. **Later — extend the nightly audit digest with two BC queries:** stale quotes (no
   sentDate, >14 days) and overdue AR (`bc_list_unpaid_invoices overdueOnly`).
7. **Later — item-creation convention doc** so `bc_find_item` quality stops degrading.

**Caveats and unverified items, stated plainly:** dimension *usage* on documents is
unverified (dimensionValues query errored on a wrong field name and was not retried); the
Shopify→BC order mechanism (native connector vs custom import) was not determined; the
count probes give ranges, not exact counts (quotes 601–800, orders 3,001–4,500, items
>15,000); invoice volume beyond 200/90d was not probed; the LADWP order pattern (63 of the
latest 200) is inferred to be an employee program, not confirmed; and the `opportunities`
entity (BC's built-in CRM) was not checked since pipeline is documented as living in
Dynamics 365.

**The headline:** BBS uses BC harder than the typical 9-person distributor — real quotes,
real POs, real AP — and the highest-leverage moves are not new modules but closing three
loops that are already 80% built: **Claude quotes → BC quotes, dimensions → the reporting
they were created for, and Shopify payments → the invoices they already paid.**
