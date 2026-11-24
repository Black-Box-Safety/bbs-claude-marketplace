# The folder leads, the record follows — design (short version)

Status: **DRAFT for Parker's approval, 2026-11-24. Nothing here is built.** This replaces the
longer draft of the same date (in git history), after Parker's direction in session: "i dont
want to unnecessarily build something, we dont need complex, but simple and working", and
"yes" to shrinking the design to the plan below. Rulings: `docs/STEWARD.md`, the three
2026-11-24 entries.

## 1. Intent

A rep saves the buyer's email and attachments into the deal folder and points Claude at it.
That is the whole of the rep's job, and it does not change. Claude registers the deal in
Dataverse from that folder, and Business Central reports the win. Nobody types a record.

**The folder is where you work; Claude keeps the record.**

## 2. What is already there (read 2026-11-24)

An outside builder's admin account owns a working Dataverse and Power Automate build
(September 2025 to April 2026). Reps use part of it every day.

| Piece | State | Verdict |
|---|---|---|
| `bbs_rfq` table (rows numbered to `RFQ-005927`), email history on each row, Teams notice on reassignment | In use | Keep |
| Flows that create the row when a rep tracks an email, or mail reaches the RFQ inbox | In use; a second step for the rep on top of saving to the folder. Parker: "it just isnt as efficient as the workflow i created" | Keep until step 4 works, then retire |
| A SharePoint folder per RFQ in a separate `account` library, with the attachments | Created automatically; reps work in the Customers tree instead | Stop creating |
| Flows that read RFQ documents, convert attachments and generate two state forms | Parker: "the document automation from that we do not use" | Switch off |
| Duplicate detection | All nine built-in rules inactive; at least eight spellings of CalVet, five of the U.S. Marshals Service | Switch on |
| Win or loss | Never recorded: no row is accepted, none has a PO number | Step 5 |
| Microsoft's sales agent flows | Installed, in draft | Leave in draft |

## 3. The plan

| # | Change | Kind | Done when |
|---|---|---|---|
| 1 | Activate duplicate detection on account name; merge duplicates from a sheet Parker approves, pair by pair | Setting | No approved pair left unmerged; a new duplicate account is caught |
| 2 | Turn on auditing for `account` and `bbs_rfq` | Setting | A change shows who made it |
| 3 | Move the kept flows off the outside builder's admin account to an owner BBS controls | Setting | No kept flow is owned by that account |
| 4 | Claude creates and updates the `bbs_rfq` row from the deal folder, after the rep approves | New ability | A rep logs a deal by pointing Claude at a folder, without tracking the email |
| 5 | One flow: a new Business Central sales order marks the matching `bbs_rfq` row won, with order number, amount and customer PO | New flow | A converted quote shows as won with no one typing |
| 6 | Switch off the unused document and form flows and the per-RFQ folder creation; after step 4 is proven, the row-creating flows | Switch off | Those flows are off and nothing a rep uses broke |

Order: 1 to 3 first, they are settings. Then 4, then 5. Step 6's first half any time after
checking that the document flow is not called by a flow that is still needed.

### Step 4 in detail

- **Key the row on the folder path.** Pointing Claude at the same folder twice finds the same
  row. [FLAG: whether the tools can find-or-create in one call was not verified; if not,
  Claude looks the row up, then writes.]
- **What Claude writes:** account, buyer, received and due dates, the folder path, and later
  the Business Central quote number, the value, the sent date, and an outcome the rep states.
  Quote value stops being a required column; it is what produced $1.00 placeholder rows.
- **A person approves.** Claude shows what it will create or change and on which account; the
  rep approves by name.
- **Search before create,** for the account and the buyer.
- **Which tool.** Microsoft's Dataverse MCP server, each rep signed in as themselves under a
  role that allows create and update on these rows and nothing else. Fallback: BBS's own
  connector gains a create tool. A sandbox test decides: create and update a deal from the
  Desktop app, VS Code and a cloud session, and confirm delete and table tools are refused.
  The server is billed per call for agents built outside Copilot Studio.
  [FLAG: the rate and whether BBS's licenses are exempt were not read.]
- **Why not a flow on the folder.** Microsoft's documentation says files arriving by sync or
  by move do not trigger flows; reps save through OneDrive sync.
- **Accepted:** a request no rep opens in Claude gets no row. Nothing is quoted without that
  session.

### Step 5 in detail

- Parker, 2026-11-24: orders "are converted frm quote". Make Order carries the quote number
  onto the order, which is the link the flow needs. [FLAG: the 2026-11-16 sales-system design
  §4 says California desk orders are mostly keyed fresh. Check twenty recent orders before
  building.]
- **One small addition in Business Central is needed.** The order's Quote No. is not among
  the fields the Business Central connector returns for `salesOrders`, nor in the order
  archive (read 2026-11-24). Either expose that one field, or match on customer plus the
  customer PO number where the rep entered it.
- **Lost** is not automatic: a quote past its valid-until date with no order is put to the
  rep, who gives the outcome and the reason.

## 4. Pursuits

A long solicitation, proposal or vehicle is still a different thing from an RFQ: weeks to
months, notes are the point, and what it taught matters after a loss. In this version it is
**a type on the `bbs_rfq` row, not a new table** (ruled 2026-11-24, superseding the same
day's new-table ruling). A pursuit row adds an estimated value, a decision date, and three
close-out fields required before it is closed: why it went the way it did, what BBS learned,
and what to do next and when. Dated notes sit on the row. Any rep may open one and assign its
owner. Dataverse holds its status.

When a deal is opened on an account, Claude reads the pursuits on that account and on the
accounts sharing its parent, and shows the rep their close-out fields. That is how a lost FBI
proposal reaches the next DEA request, and it needs the parent links in §5.

## 5. Later, only when wanted

- **Parent links for federal accounts.** California institutions already have parents; DEA,
  FBI and the Justice Department accounts sit flat. Setting parents is data cleanup on the
  existing column, done from the same approved sheet as step 1. No build.
- **A contracts table** for federal past performance: number, type, period, ceiling,
  contracting officer, where the award document is, and a citable flag only Parker sets.
- **Connection roles** (contracting office versus end user; prime versus end customer),
  a built-in feature, when a federal deal first needs it.

## 6. Not doing

Opportunities and quotes inside the Sales app; the built-in Business Central and Sales sync;
sequences, forecasting and conversation intelligence; Microsoft's sales agents; Copilot
Studio; the Outlook sales add-in; Dataverse business skills; a second copy of the deal
rendered into the folder; line items, costs or margins in Dataverse. `RFQ.md`, the quote
log, remembered notes and flags stay in the folder exactly as they are.

## 7. Not verified

- BBS's Sales license tier, and whether one flow across Business Central and Dataverse is
  covered by it.
- Whether auditing is already on; whether a row Claude creates triggers duplicate detection.
- Whether the unused document flow consumes paid AI capacity. Microsoft states seeded
  AI Builder credits stop for licenses bought or renewed from 2026-11-01.
- Whether the Dataverse MCP server connects from every surface a rep uses.
- What reps need for a license if the Sales app is later dropped. Nothing here drops it.

## 8. Sources

- Sales CRM connector, read 2026-11-24: `bbs_rfq` and `account` columns and newest rows;
  accounts by name and by parent; opportunities and leads; tracked emails; document
  locations and sites; cloud flows and their owners; duplicate rules; notes and tasks.
- Business Central connector, read 2026-11-24: fields of `salesOrders`, `salesQuoteArchives`
  and `salesOrderArchives`.
- Microsoft 365 connector, read 2026-11-24: the `account` library folder for one RFQ.
- A review of Microsoft Learn by a research subagent, 2026-11-24, with page links, covering
  email tracking, SharePoint document locations, Business Central triggers and webhooks,
  duplicate detection, auditing, flow ownership, the Sales features in §6 and the SharePoint
  file-trigger limitation. Its judgments are its own; its Learn citations were not re-read.
- Microsoft Learn, read directly 2026-11-24: the Dataverse MCP server tool list and billing
  note; the Dataverse plugin for AI agents reference and security pages; table licensing.

---

Owner: Parker Marshall. Drafted 2026-11-24.
