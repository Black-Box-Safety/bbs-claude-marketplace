# Quote rules and edge cases

What the script enforces and why. Rules marked **[script]** are checked by
`scripts/bc_quote_entry.py`; the rest are judgment calls for you and the rep before the spec
is written. The source of most of them is the BC write SOP (`BC-WRITE-SOP-RULES.md` in
`PM Claude/BC-Write-API` on SharePoint, sections 1, 3 and 4.7) and the quote built live for
CAL FIRE Atwater on 2026-10-16, which this skill replaces.

## The header BC gets

| Field | Value | Why |
|---|---|---|
| `customerNumber` | from the spec, must exist and be unblocked **[script]** | Resolved by number; BC's name search is case-sensitive and a near-miss returns nothing |
| `documentDate` | the day of the commit **[script]** | SOP: document date is the creation date |
| `validUntilDate` | **never sent** **[script]** | BC computes document date + 60 days, which is the SOP's rule; sending it overrides that silently |
| `externalDocumentNumber` | from the spec, 1-35 chars, unique across sales quotes **[script]** | The agency's solicitation or the customer's PO. BC accepts duplicates; the duplicate gate is this script's, and it stops on any quote that already carries the number, whatever its status, because the rep decides whether that is a re-quote |
| `shortcutDimension1Code` (CONTRACT) | from the spec, on the list below **[script]** | The one BBS-specific rule in quote entry and the one the SOP never wrote down. `OPEN` unless the deal rides a vehicle |
| `shortcutDimension2Code` (CUSTOMER) | **not sent** | Inherits from the customer's default dimensions (verified: `C10001` came back `DGS`) |
| `salesperson` | from the spec, the owner's code **[script]** | Writable on POST (`SQ-104848`, `KQUEZON`); the read-back gate compares it. Which code is the owner's is the section "Whose quote it is" below |
| `shipTo*` | PATCHed after the POST with `If-Match`, then gated **[script]** | A quote inherits the customer's default ship-to, which is not always the job's destination (`C11312` defaults to Utah; the PO shipped to Vandenberg, a different tax jurisdiction). The gate runs before a single line exists |
| payment terms, shipment method | inherit from the customer card, read back and compared to the card **[script]** | The sheet shows both so the rep can see NET 30 when the solicitation says Net 45 and decide in BC. This skill does not patch terms |
| status | left `Draft` **[script]** | The API has no release action; a person releases in BC and that is where tax is calculated |

## Whose quote it is

Ruled by Parker, in session, 2026-10-16, and recorded in canonical-facts.md ("Salesperson
follows the account split, quote by quote") and `/ca-rfq` Gate 5: on a California state quote the
salesperson is the Account Manager who owns the agency, quote by quote. Parker holds no accounts
on the state book; state work Parker runs still lands under Kim or Aanya.

| Spec `book` | Who | `agency` | `salesperson` the check accepts |
|---|---|---|---|
| `ca-state` | Kim Quezon | CDCR, CHP, CAL FIRE, CMD, CDFW, Cal OES, DOJ, DPR, DWR, DCC, CCC, ABC, DOC, State Water Board (SWRCB / CWB), OIG, POST, Horse Racing Board, Gambling Control Commission | `KQUEZON` **[script]** |
| `ca-state` | Aanya Samarasinghe | every other California state agency (DGS, Caltrans, DSH, CalVet, DMV, CDFA, CARB, DTSC, CalRecycle, DOR, DCA, CNRA, ...) | `AANYA` **[script]** (the code exists in BC since 2026-09-14) |
| `higher-ed` | Joey Magliato | CSU, UC | `JMAGLIATO` or `UNIVERSITY` **[script]** |
| `body-armor` | Parker Marshall | any; CONTRACT must be `BODYARMOR`, `BA-CA` or `BA-SRCWL` **[script]** | not gated |
| `other` | outside the state book (federal primes, local, private) | none | not gated |

- `CA STATE TEAM` was the shared Parker-and-Aanya bucket. It is never set on a new quote, in
  any book, even where the customer card still defaults to it; the check stops on it
  **[script]**. Historic quotes keep it.
- `PMARSHALL` never goes on a state quote **[script]**: Parker holds no accounts there.
- A body-armor CONTRACT on `book: ca-state` stops (body armor is outside the Kim/Aanya book;
  set `body-armor`), and CSU or UC on `book: ca-state` stops (set `higher-ed`) **[script]**.
- **Cross-check against the customer card.** `check` reads the customer's default CUSTOMER
  dimension (`customers({id})/defaultDimensions`). `CALFIRE`, `DCR`, `CHP`, `CMD`, `DFW`,
  `OES` and `CWB` name Kim's agencies; `DGS`, `DOT` and `DSH` name Aanya's; `CSU` and `UC`
  name Joey's. When the card names the other owner the check stops; when it carries `AGNCY`,
  `MUNC`, `UNAFLTD` or nothing, it cannot confirm the agency and the sheet says so, and the
  spec's `agency` decides **[script]**. A card that could not be read is a flag on the sheet,
  not a stop.
- The agency list and the codes are copied into the script from canonical-facts and held as a
  test (`test_bc_quote_entry.py`, `Owner`). When an agency moves or a code changes, change
  canon, the script and the test together.
- The CAL FIRE Atwater quote of 2026-10-16 is the precedent for the rule: its spec carried
  `CA STATE TEAM` and CAL FIRE is Kim's, so under this skill it would carry `KQUEZON`.

## The CONTRACT list

The codes the script accepts, copied from section 1 of the write SOP (verified against
General Ledger Setup) and held as a test in `scripts/test_bc_quote_entry.py`. When BC gains a
code, change the SOP, the script and the test together.

`OPEN` (open market) · `NASPO` (Grainger NASPO 7-25-51-02.03) · `NPPGOV` (NPPGov PS25650) ·
`GSA` · `OMNIA` (Grainger OMNIA CA) · `EMRKT` (Grainger GEUS eMarketplace) · `ICPT` ·
`UCOP` (Grainger UC) · `BODYARMOR` · `BA-CA` (body armor, state LPA 1-23-84-07) ·
`BA-SRCWL` (body armor Sourcewell 091924) · `WWG-SRCWL` (Grainger Sourcewell) · `DODIG` ·
`QB LEGACY` · `BBSACCOUNTINGONLY`

`BODYARMOR`, `BA-CA` and `BA-SRCWL` sit outside the California-state book worked by the state
team; `QB LEGACY` and `BBSACCOUNTINGONLY` are accounting codes, not sales vehicles. The script
accepts them because they exist; the sheet names the code so the rep sees it.

## The lines BC gets

| Field | Value | Why |
|---|---|---|
| `sequence` | `line x 10000` **[script]** | Explicit sequence is accepted on POST and keeps BC's own spacing |
| `lineType` | `Item` **[script]** | Every line is an item line; a freight line uses the existing `SHIPPING` item |
| `lineObjectNumber` | the item number, which must already exist as Inventory and unblocked **[script]** | **Never create an item as a side effect of quoting** (SOP 4.4 rule 6). A missing number stops with the `bc-item-entry` instruction; this script has no create or patch path for items |
| `description` | from the spec, 1-100 ASCII **[script]** | Overrides the card text on this quote only; carries the customer's tag or PO line. ASCII because downstream exports are (`SQ-104848` had to be patched for an em dash) |
| `quantity`, `unitOfMeasureCode` | from the spec; the UoM must exist in BC **[script]** | |
| `unitPrice` | from the spec, explicit, greater than zero **[script]** | SOP: a zero price means neither the item card nor customer pricing produced one and a human must. Explicit on every line so the card's price or a customer price list cannot slip in unseen |
| `locationId` | `DROPSHIP` (`006fd057-c685-ef11-ac23-6045bdecc5e4`) **[script]** | The customer-card default per SOP; `locationId` is line-level only on this API, so it is sent on every line |
| `taxCode`, `itemVariantId`, discounts | not sent | Tax follows the item's tax group; nothing here discounts a line |

## Cost and price

- `unitCost` is BBS's cost for one unit, read from `costSource`. It is not written to BC; it
  is what makes the margin gate and the GM% column honest. The sheet shows the card's cost
  beside it when they differ; the card is not patched from here.
- `costSource` names a document with a number or date. The guess-word list is
  `bc-item-entry`'s: verbal, estimate, approx, roughly, about, ballpark, phone, from memory,
  guess, last time, typical, TBD, later, in any form. **[script]**
- Price below cost stops. Price equal to cost stops unless the line, or the spec, says
  `zeroMarginOk: true` **[script]**. On a NASPO or other Grainger-schedule quote the Grainger
  price is the customer price by contract, so `zeroMarginOk` at the top level with a
  `pricingBasis` that says "Grainger at cost on NASPO" is the normal shape, not an exception.
  On an open-market quote a line at cost is a question for the rep.
- The lines must sum to `quoteTotalExclTax` to the cent before anything is written, and BC's
  `totalAmountExcludingTax` must equal it after **[script]**. Tax is excluded on both sides;
  it is calculated on release.
- The Grainger price, when a line is Grainger-filled, was read on the **buying institution's
  own account** through the Grainger connector, and `costSource` records the account and
  date. A different account returns a different price that still looks valid.

## Order of operations in a commit, and what each failure leaves behind

1. Token and name: the token must match the spec on disk and `--approved-by` must be the
   `preparedBy` name. Nothing has touched BC yet.
2. Every gate again (customer, items, duplicate, field rules, sum). Nothing written yet.
3. `POST salesQuotes` with the header. **From here a draft exists.** The script prints the SQ
   number BC assigned the moment it has it.
4. `GET` the header for its etag, `PATCH` the ship-to with `If-Match`, `GET` again and gate on
   customer, every `shipTo*` value, payment terms and shipment method equal to the customer
   card, CONTRACT, salesperson and external document number. **A failed gate stops with the
   SQ number named and no lines added**: an empty draft the rep deletes in the BC UI. Do not
   re-run commit for it; the duplicate gate would stop on the external document number, which
   is correct, and the fix is the empty draft, not a second one.
5. `POST salesQuoteLines`, one per spec line. **A failed line stops with the SQ number and
   the lines that landed**: a partial draft the rep finishes or deletes in BC. Same rule: no
   re-run.
6. `GET ...?$expand=salesQuoteLines` and compare every line (item, qty, UoM, price,
   description) and the total with the spec. A mismatch stops with the SQ number; the quote
   exists and the rep checks it in BC before it goes anywhere.
7. Append to `<spec>.bc-log.jsonl`: who approved, which sign-in wrote, the SQ number, every
   event. The sheet and the log are the record; nothing is written to the spec itself.

Never: release, `makeOrder`, `makeInvoice`, `send`, post, or any PATCH after the header
gate. Tax lives on the released quote, and a person releases.

## Scope

- One quote per spec. A second revision is a new spec with its own external document number
  or a change the rep makes in BC.
- The item half is `bc-item-entry`. Two skills write to Business Central and this is the
  second; both stay off the `bbs-fill` allow list so every run waits for the Allow click.
- Rendering a PDF copy of a quote that already exists in BC is `bbs-quote-builder`, only when
  a rep asks for one; the customer document is the PDF BC prints from the released quote.
- Sales orders, invoices, purchase orders and vendor quotes are out of scope and out of the
  write scope Parker authorized (create items, patch Vendor No., create sales quotes and
  lines).

## Authentication

Shared with `bc-item-entry`: the script imports its sibling's connection loading, sign-in,
HTTP helpers and error table rather than copying them, so there is one connection file
(`bc-item-entry/references/bc-connection.json`), one token cache and one error table for
both skills. Default is the rep's own delegated sign-in; app-only runs only with
`BBS_BC_AUTH=app-only` and is flagged on the sheet and in the log because the quote then
shows the service principal as creator. `whoami` here reads customers, items, sales quotes
and units of measure once each (`$top=1`), which is the read path a commit depends on; a
read PASS does not prove write rights. The error table in `bc-item-entry`'s SKILL.md applies
verbatim; a 403 on `POST salesQuotes` with a 200 on the reads means the rep's BC user lacks a
permission set covering sales quote insert, which a BC admin fixes.
