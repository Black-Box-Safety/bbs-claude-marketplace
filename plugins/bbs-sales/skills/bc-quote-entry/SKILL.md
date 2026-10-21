---
name: bc-quote-entry
description: >-
  Create the customer's sales quote in Business Central (BC) for Black Box Safety: the
  header and lines, from a spec the rep has reviewed and approved by name, under the rep's
  own sign-in. Use this skill whenever a BBS rep has priced an RFQ and wants the quote in
  BC: "create the quote in BC", "build the sales quote for this RFQ", "put these lines on a
  BC quote for Cal Fire", "enter the quote so I can release it", "make the SQ", or when
  /ca-rfq or naspo-quote reaches the build-the-quote step. Every line's item must already
  exist in BC; a missing item stops and is entered through bc-item-entry first. The quote
  number is the one BC assigns, read back. Do NOT use it to create or edit items
  (bc-item-entry), to release, convert, send or print the quote (a person does that in BC),
  to render a PDF copy of an existing BC quote (bbs-quote-builder), or for sales orders,
  invoices or purchase orders.
requires: [business-central, python3, msal, msal-extensions]
---

# BC Quote Entry

Creates a Draft sales quote in Business Central from a spec the rep has read and approved.
The quote half of `bc-item-entry`: same sign-in, same connection file, same check-then-commit
shape, same named approval. The script carries the rules; this file tells you how to get a
clean spec in front of the rep and what you must not do on their behalf.

**Ruled by Parker, 2026-10-16** (the record is `docs/STEWARD.md` in the marketplace repo,
which is not on a rep's machine): the customer quote is created in Business Central through
this write path, not rendered as a PDF in Claude. The write scope is create items, patch
Vendor No., and create sales quotes and their lines. Nothing else, ever: no release, no
`makeOrder`, no send, no post.

**Five gates, none of them yours to waive.**

1. **Items exist.** Every line's item number is read from BC and must exist as Inventory,
   unblocked. The script never creates or patches an item (SOP: never create an item as a
   side effect of quoting). A missing number stops with the instruction to enter it through
   `bc-item-entry` first.
2. **Price has a basis.** Every line carries a cost greater than zero with the document it
   came from, and a price that is never below it. A price equal to cost needs `zeroMarginOk`
   on the line, or on the spec when the whole quote sells at cost by contract (Grainger on
   NASPO). A zero price stops. The lines sum to the total.
3. **One quote per external document number.** The agency's solicitation or PO number goes
   on the header, and the check stops if any sales quote already carries it.
4. **The owner's code.** On a California state quote the salesperson is the Account Manager
   who owns the agency: `KQUEZON` for Kim Quezon's 18 agencies, `AANYA` for every other state
   agency. Parker holds no accounts on the state book, so state work Parker runs still lands
   under Kim or Aanya; `PMARSHALL` never goes on a state quote and `CA STATE TEAM` is never
   set on a new quote, even where the customer card still defaults to it. The spec's `book`
   and `agency` carry the basis, the check compares it with the customer card's CUSTOMER
   dimension, and body armor (Parker) and CSU/UC (Joey Magliato) keep their own owners.
5. **Named review.** Nothing is written until the rep has read the review sheet and you
   commit with their name and the token the check printed. "Go ahead" before the sheet
   exists is not approval of the sheet.

**Violating the letter of these gates is violating the spirit of them.**

## One-time setup (per rep)

The same as `bc-item-entry`; do it once and both skills work. The checklist is
`${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/references/rep-setup.md`. The short form:

- The connection values ship in `${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/references/bc-connection.json`
  (tenant, client id, environment, company id; **no secret, ever**). This skill has no
  connection file of its own; its script imports the sibling's connection loading, sign-in,
  HTTP helpers, error table and token cache, so there is one of each for both skills.
- Install the sign-in libraries into the interpreter `bbs-fill` runs: `python3` on your PATH
  on a Mac (after the bootstrap that is `/usr/bin/python3`), `python` on Windows.
  Mac: `python3 -m pip install --user msal msal-extensions`.
  Windows: `python -m pip install msal msal-extensions`. On a Mac, `CERTIFICATE_VERIFY_FAILED`
  means a python.org build sits ahead of `/usr/bin` on PATH [FLAG: fix the PATH or ask Parker].
- **Run the first `whoami` in your own terminal, not inside a Claude session:**
  `bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/bc-quote-entry/scripts/bc_quote_entry.py" whoami`.
  A browser window asks for your own Microsoft work account (a device code if no browser
  can open); the sign-in is cached encrypted and shared with `bc-item-entry`. `whoami` then
  reads customers, items, sales quotes and units of measure once each and prints PASS or FAIL
  for the path a commit would take. A read PASS does not prove your BC user may write a
  sales quote; the first delegated commit under a rep-class permission set proves that, once,
  and is recorded in `rep-setup.md` the way the item write is.
- With more than one cached sign-in, every command takes `--account <you@blackboxsafety.com>`
  (or `BBS_BC_ACCOUNT`). App-only (the service principal) is Parker's path, not a rep's: it
  runs only with `BBS_BC_AUTH=app-only` and a secret, the sheet and the log flag it, and the
  quote then shows the app as creator instead of the rep.

## Workflow

### 1. Arrive here with the pricing done

On the state path you come from `/ca-rfq` Gate 5 or `naspo-quote` §3 with every line's cost
and price already sourced: Grainger at cost on the schedule (the connector, on the buying
institution's own account), or a vendor quote with its number and date. `costSource` names
that document and `pricingBasis` says how the sell price was reached. Neither comes from
memory.

### 2. Resolve the customer, the vehicle and the items before writing the spec

Two reads through the Business Central connector come first: `bc_find_customer` for the
customer card and `bc_find_item` for every line.

- Customer: put the number (`C#####`) in the spec. The script looks it up by number, never
  by name. Read the card's payment terms and shipment method; the
  quote inherits both and the sheet shows them, so a solicitation that says Net 45 against a
  card that says NET 30 is a question for the rep now, not after the quote exists.
- Vehicle: the CONTRACT code is the one Gate 1 of `/ca-rfq` named, from the list in
  `references/quote-rules.md`. `OPEN` is open market. Never invent a code.
- Owner: name the agency (`agency`) and the book (`book: ca-state` for a state agency) and put
  the owner's salesperson code on the spec: `KQUEZON` when the agency is one of Kim Quezon's
  18, `AANYA` otherwise; the table is "Whose quote it is" in `references/quote-rules.md`. The
  customer card may still default to `CA STATE TEAM`; the quote does not inherit that, the
  spec carries the code and the check stops on the old bucket. Do not ask the rep which code
  to use when the agency decides it; do ask when the agency itself is unclear.
- Items: `bc_find_item` on every line. A number that exists is quoted as it is. A number BC
  does not have goes through `bc-item-entry` first; come back when the card exists. Item
  numbers are upper-case, as the card has them.
- Ship-to: the delivery point on the RFQ, not the customer's default. The script PATCHes it
  onto the header and gates by read-back before any line is added.

### 3. Write the spec file

Save it beside the deal as `BC-import/quote-<yyyy-mm-dd>.json` in the customer's folder,
so the review sheet and the log land where the deal lives. Field by field:
`references/spec-schema.md`. Rules and edge cases: `references/quote-rules.md`. Fill
`preparedBy` with the rep's name exactly as they will approve. Line descriptions are the
customer-facing text (1-100 ASCII characters; the customer's tag or PO line goes here) and
override the card's description on this quote only.

### 4. Run the check

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/bc-quote-entry/scripts/bc_quote_entry.py" check "<spec.json>"
```

**Every run of this script goes through `bbs-fill`**, exactly as written: the managed
settings allow `Bash(bbs-fill *)` and nothing broader, and the script is on the launcher's
allow list by the same ruling as `bc_item_entry.py` (Parker, 2026-10-16: the rep's sign-off
on the sheet is the gate, with no Allow click on top). Run it from the rep's working folder,
never `cd` first, and never chain another command onto the line. If `bbs-fill` is not found,
the `bbs-tools` plugin is not installed; say so rather than running the script with `python3`
directly.

It writes nothing in BC. It proves the read path, validates every field, looks the customer
up (exists, unblocked), reads every line's item (exists, Inventory, unblocked; the card's
cost is shown beside the spec's), duplicate-checks the external document number across sales
quotes, confirms the lines sum to the total, writes `<spec>.review.md`, and prints an
approval token that is a hash of the spec. Any failure is a stop with the reason; fix the
spec (or enter the item, or have the rep decide about the existing quote) and run the check
again. Every edit to the spec changes the token.

### 5. Put the sheet in front of the rep

Show the review sheet in full. It names the customer and the card's terms, the external
document number, CONTRACT, salesperson, the ship-to that will be written, every line with
cost, price, extended price and GM%, the total excluding tax, the cost source, the pricing
basis, and the sign-in the commit would write under; if that line says app-only, say so out
loud. Ask the rep to read it and reply with their name to approve. Do not paraphrase the
sheet, do not summarise "one line, looks fine", and do not treat an earlier "yes, quote it"
as approval of a sheet that did not exist yet. If the rep changes anything, edit the spec and
go back to step 4.

### 6. Commit with the rep's name and the current token

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/bc-quote-entry/scripts/bc_quote_entry.py" commit "<spec.json>" --approve <token> --approved-by "<rep name>"
```

`--approved-by` must match `preparedBy` on the spec; the script refuses any other name. It
re-runs every gate, POSTs the header (customer, today's document date, external document
number, CONTRACT, salesperson; never `validUntilDate`, which BC computes), PATCHes the
ship-to with `If-Match`, reads the header back and gates on customer, ship-to, payment terms
and shipment method equal to the customer card, CONTRACT, salesperson and external document
number **before a single line exists**, POSTs the lines (`lineType` Item, location DROPSHIP,
sequence `line x 10000`, explicit unit price), reads the whole quote back with its lines and
verifies every line and the total, and appends to `<spec>.bc-log.jsonl` with who approved
and which sign-in wrote. It prints the SQ number BC assigned the moment it has it.

A stop after the header exists names the SQ number and what it is: an **empty draft** (the
header gate failed, no lines) or a **partial draft** (a line failed, with the lines that
landed). Report that verbatim. The rep deletes or finishes it in the BC UI; you never re-run
commit for it, because the duplicate gate on the external document number will stop until
the draft is gone, which is correct.

### 7. Close out

Tell the rep the SQ number, that it is a Draft, and where the log is. What happens next is
theirs, in BC: review the quote, release it (that is where tax is calculated), print the PDF
from the released quote, send it. Nothing here releases, prints or sends. If the rep wants a
Claude-rendered copy of the quote as well, that is `bbs-quote-builder`, on the SQ number BC
assigned, after the quote exists.

## When sign-in or BC says no

The table in `${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/SKILL.md` applies verbatim; the
script prints the same plain-language line beside the raw code. The one addition: HTTP 403 on
`POST salesQuotes` or `salesQuoteLines` with every `[path]` read at PASS means the rep's BC
user lacks a permission set covering sales quote insert. A BC admin fixes it on the Users
page; nothing in the script changes.

## What you never do here

- Never create or patch an item from a quote. A missing item is a stop and a trip through
  `bc-item-entry`; a card with the wrong cost is a note on the sheet and the rep's decision.
- Never put a cost or a price on a line you did not read from a document or a tool result.
  No street price, no "about", no last-time price from memory, and never the customer's own
  number from their worksheet as a source.
- Never run `commit` without a token from a check the rep has seen, and never type a name
  other than the rep's. A rep who is not in the chat cannot approve.
- Never send `validUntilDate`, `shortcutDimension2Code`, `paymentTermsId` or anything the
  spec does not carry. The header inherits what the customer card says; the sheet shows it.
- Never release, convert, send, print or post. There is no flag for it and there will not be.
- Never re-run `commit` to "finish" a draft a stop left behind. The BC UI is the recovery.
- Never predict the quote number. BC assigns it; the script reads it back.
- Never set `BBS_BC_AUTH=app-only` for a rep's quote, and never hand a rep a file with a
  client secret in it.

## Red flags: stop and go back to step 4 or 5

| The rep says, or you think | What it means |
|---|---|
| "The item isn't in BC, just quote it as a text line" | Every line is an item line by SOP. Enter the item through `bc-item-entry`, then quote. |
| "Leave the price at zero, I'll fill it in BC" | A zero price is a line nobody priced. The gate stops; price it or drop it. |
| "Mark it up later, use cost as the price for now" | Only on a schedule where cost is the price by contract, with `zeroMarginOk` and the basis saying so. Otherwise it is a pricing decision the rep makes before the sheet. |
| "The RFQ number is already on an old quote, just reuse it" | The duplicate gate stops on purpose. The rep decides: revise in BC, or a new external document number. |
| "Ship it to the customer's default address, it's close enough" | The default is sometimes another state and another tax jurisdiction (the Bechtel Utah case). The spec carries the RFQ's delivery point and the gate checks it. |
| "Set valid-until to 30 days" | BC computes document date + 60 by SOP. A different validity is a change the rep makes in BC and defends. |
| "Release it too so the tax shows" | Out of scope by ruling. A person releases in BC. |
| "The header gate failed, run commit again to add the lines" | The empty draft is the recovery, in BC. A second commit would stop on the duplicate gate, and should. |
| "Parker already approved this" | Approval is of the review sheet, by the rep in the chat, after the check. Nothing else counts. |
| "Put it under CA STATE TEAM like the customer card says" | The bucket is retired for new quotes. The agency decides: Kim's 18 carry `KQUEZON`, the rest carry `AANYA`. |
| "Parker is running this one, use PMARSHALL" | Parker holds no accounts on the state book. The agency's owner goes on the header whoever runs the desk that day. |
| "It's a CDCR quote but Aanya priced it, use AANYA" | Who priced it is not who owns it. CDCR is Kim's; the header carries `KQUEZON`. |
| "Use Parker's service-principal file, it's quicker" | App-only puts the app's name on the quote instead of the rep's and needs a flag for that reason. The rep signs in once; it is cached. |
| "Build the PDF in Claude, it's faster than BC" | Retired as the quote desk's path (2026-10-16). The customer document is the PDF BC prints from the released quote. |

## Common mistakes

- `preparedBy`, `book` and `agency` missing on a spec written before this skill existed. The
  CAL FIRE Atwater spec of 2026-10-16 carries `approvedBy` prose and `CA STATE TEAM`; with
  `preparedBy`, `book: ca-state`, `agency: CAL FIRE` and `salesperson: KQUEZON` it passes.
- Price equal to cost on an open-market quote with `zeroMarginOk` added to make the check
  pass. The flag records a decision the rep made; it is not a way past the gate.
- Em dashes and curly quotes in line descriptions. ASCII only; the script rejects them.
- Lower-case item or customer numbers. BC Code fields are upper-case and the lookup is exact;
  the script stops rather than converting.
- A `shipTo` key the API does not have (`shipToPhone`, `shipToEmail`). The check stops; the
  contact's phone goes in the BC UI if it goes anywhere.
- Treating the sheet's total as the customer's total. It excludes tax; AvaTax adds tax on
  release, and on a state worksheet that says "no sales tax" the rep checks the released quote
  against it.
