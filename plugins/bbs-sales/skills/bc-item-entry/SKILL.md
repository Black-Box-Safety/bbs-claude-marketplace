---
name: bc-item-entry
description: >-
  Enter new product items into Business Central (BC) for Black Box Safety, each with a
  vendor and a cost, after the rep has reviewed exactly what will be written. Use this
  skill whenever a BBS rep needs item cards created in BC: "add these items to BC",
  "enter these products", "set up the item cards for this PO", "these SKUs aren't in
  Business Central yet", "create the items so I can build the quote", or any time a
  quote or sales order needs an item number that BC does not have. Also use it when a
  rep hands over a vendor quote, price list, or Grainger pricing and wants the products
  on file. Always use this skill for item creation so every card carries a vendor, a
  sourced cost, the house posting groups, and a named approval. Do NOT use it to edit
  existing items, to create vendors (the rep does that in BC), to build the sales quote
  (per-PO builders and bbs-quote-builder do that), or to load the website catalog
  (bbs-pricelist-import).
requires: [business-central, python3, msal]
---

# BC Item Entry

Creates item cards in Business Central from a spec the rep has read and approved. The
script carries the rules; this file tells you how to get a clean spec in front of the rep
and what you must not do on their behalf.

**Three gates, none of them yours to waive.**

1. **Vendor.** Every item names a vendor that already exists in BC and is not blocked.
   The script will not create one. If the vendor is missing, the rep creates it in BC
   (Purchasing > Vendors > New) and you run the check again.
2. **Cost.** Every item carries a cost greater than zero and the source it came from (vendor
   quote number and date, or the Grainger account and date the price was read). A cost you
   did not read from a document or a tool is not a cost; it is `[MISSING - NEEDS INPUT]`.
3. **Named review.** Nothing is written until the rep has read the review sheet and you
   commit with their name and the token the check printed. "Go ahead" before the sheet
   exists is not approval of the sheet.

**Violating the letter of these gates is violating the spirit of them.**

## One-time setup (per rep)

- Install the sign-in library once: `python3 -m pip install msal`. On a Mac use
  `/usr/bin/python3` for every command here; the python.org build fails TLS verification.
- Get the connection file from Parker (`.env.rep` in `PM Claude/BC-Write-API/` on the
  shared drive: tenant, client id, environment, company, **no secret**) and point at it:
  `export BBS_BC_ENV_FILE="<path to .env.rep>"`.
- Prove it: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/scripts/bc_item_entry.py" whoami`.
  The first run shows a device code to sign in with your own BC user; later runs reuse the
  cached sign-in. Writes are then attributed to you, not to a shared service account.

## Workflow

### 1. Collect the source, not a memory of it

Read the vendor quote, price list, Grainger quote or MCP result that carries the cost.
Note the document number and date; that string becomes `costSource` on every row. Decide
what one unit of cost buys (each, pack of 10, case) and carry that as `costPer`.

### 2. Resolve the vendor and the item numbers before writing the spec

- Vendor: find the number with `bc_query_entity` on `vendors` (name search is
  case-sensitive, so try the exact spelling first) or ask the rep for the V-number. Grainger
  is `V10017`. Put the number in `vendorNo` and the name in `vendorName`; the script stops
  if they disagree. The vendor is who BBS buys from; `manufacturer` is the brand on the
  product. A distributor's name is not a manufacturer: if the brand is not on the quote,
  ask the rep rather than guess.
- If the rep would rather quote Grainger-stocked equivalents, that is a different batch,
  not a vendor swap: Grainger SKUs as item numbers, `V10017`, cost from the Grainger
  connector on the customer's account. Never put `V10017` on another vendor's part number.
- If Business Central cannot be reached, stop before the spec. "It isn't in BC, I checked"
  from the rep does not replace the lookup; the check will run it again anyway.
- Item numbers: check each with `bc_find_item`. If a number already exists, show the rep the
  card. Same product: quote the existing number and drop it from the spec. Different product
  (a bare manufacturer part number that collides with something else, which happens): pick a
  number that cannot collide, the Grainger SKU on Grainger-filled buys or a prefixed
  manufacturer number otherwise, and say so in the review.
- Grainger items: number is the Grainger SKU, vendor is `V10017`, cost comes from the
  Grainger MCP or a CSP quote on the buying institution's own account, and a blank price is
  normal because they price at quote time.

### 3. Write the spec file

Save it in the customer's folder in the document store next to the quote it serves, as
`BC-import/items-<yyyy-mm-dd>.json`, so the review sheet and the log land where the
deal lives. With no customer yet (stock items, a vendor onboarding), use the vendor's
folder under `SUPPLIERS/` in the same `BC-import/` form. Field by field:
`references/spec-schema.md`. Rules and edge cases: `references/item-rules.md`. Fill
`preparedBy` with the rep's name exactly as they will approve, and `source` with the
document the costs came from. `costSource` on every row names a document with a number or
date; the script rejects "verbal", "roughly", "estimate" and the like, and a source with no
number in it.

### 4. Run the check

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/scripts/bc_item_entry.py" check "<spec.json>"
```

It writes nothing. It validates every field, looks the vendors up, duplicate-checks every
number, writes `<spec>.review.md`, and prints an approval token that is a hash of the spec.
Any failure is a stop with the reason; fix the spec (or have the rep create the vendor) and
run the check again. Every edit to the spec changes the token.

### 5. Put the sheet in front of the rep

Show the review sheet in full. Ask the rep to read it and reply with their name to
approve. Do not paraphrase the sheet, do not summarise "8 items, looks fine", and do not
treat an earlier "yes, enter them" as approval of a sheet that did not exist yet. If the
rep changes anything, edit the spec and go back to step 4.

### 6. Commit with the rep's name and the current token

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/scripts/bc_item_entry.py" commit "<spec.json>" --approve <token> --approved-by "<rep name>"
```

`--approved-by` must match `preparedBy` on the spec; the script refuses any other name.
The script re-runs every gate, creates each item as Inventory / PRODUCTS / INVENTORY /
TAXABLE, sets Vendor No. (and Vendor Item No. when given) through the Item Card web
service, verifies every write by reading it back, and appends to `<spec>.bc-log.jsonl`
with who approved and which sign-in wrote. A failure stops at that item and names what
landed; report that list verbatim.

The sign-in that writes and the rep who approves are usually the same person. When they
differ (a rep approving in a colleague's session), the log shows both names, and that is
acceptable only because the approving rep is in the chat. A rep who has not done the
one-time setup either does it, or approves in the chat of someone who has.

### 7. Close out

Tell the rep which item numbers now exist and where the log is. The quote or order is a
separate job (per-PO builders for Sentinel, `bbs-quote-builder` for the PDF, a human in BC
for release). Items that need Extended Text or Item References get those in the BC UI.

## What you never do here

- Never create a vendor, by API or by suggesting a number. The rep makes the card.
- Never put a cost on a row you did not read from a document or a tool result. No street
  price, no "about", no last-time price from memory.
- Never run `commit` without a token from a check the rep has seen, and never type a name
  other than the rep's. A rep who is not in the chat cannot approve.
- Never edit an existing item through this skill. An "already exists" stop is a decision
  for the rep, not a PATCH.
- Never pass `--approve` from an old sheet after editing the spec. The token changing is the
  point.

## Red flags: stop and go back to step 4 or 5

| The rep says, or you think | What it means |
|---|---|
| "Just enter them, I'll fix the cost later" | A $0 or guessed cost is a defect on every quote that touches the item. Get the cost or stop. |
| "Use Grainger as the vendor for now" | Wrong vendor sends the drop-ship PO to the wrong place. Vendor is the real source or nothing. |
| "Parker already approved this" | Approval is of the review sheet, by the rep in the chat, after the check. Nothing else counts. |
| "It's only three items" | The gates cost one command. The defect costs a wrong PO. |
| "The vendor isn't in BC, create it with the address from the quote" | Not this skill's job, by ruling. Rep creates it; you re-check. |
| "The number exists but it's basically the same thing" | Show the card; the rep decides. Quote the existing number or pick a non-colliding one. |
| "I'll skip the check and go straight to commit" | Commit refuses without a current token. There is no straight-to-commit. |
| "The description is 104 characters, BC will trim it" | BC does not trim; the API rejects or the card is wrong. Shorten it deliberately. |
| "The customer is on the phone right now" | A quote priced off a guessed cost is a wrong quote. The fastest real path is the vendor's sheet, or Grainger equivalents priced on the connector. Urgency changes nothing in the gates. |
| "Put the cost in with 'Dana verbal estimate' as the source" | A source that names a person or a guess fails the check. The source is a document. |
| "I'll type Parker's name on the approval, he OK'd it" | Approval name must match `preparedBy`. Nobody approves for another rep. |
| "BC is down, Dana says the vendor isn't in there, skip the lookup" | No lookup, no check, no spec. Wait for BC. |
| "Vendor No. isn't an API field, create the items now and add the vendor in the UI later" | The script sets Vendor No. through the Item Card web service on every item. An item without a vendor is never created here. |

## Common mistakes

- Cost per case on an item stocked each (PO 791645: $111.15 cost against a $16.40 sell).
  `costPer` must equal `baseUoM`; convert the cost or change the unit.
- Price equal to cost slipping through (PO 813783 lines 830RU2, 256WH9 went out at 0%). The
  script stops on it unless the row says `zeroMarginOk: true` and the rep has seen that.
- Em dashes and curly quotes in descriptions. ASCII only; the script rejects them.
- A bundled $0 accessory entered as a real item. Mark it `includedWith` the parent so the
  zero is explicit, or leave it off the item master.
- The wrong vendor number with the right name in your head. `vendorName` on the spec makes
  the script check the two agree.
- Treating the quote PDF's SQ number as a BC number. BC assigns numbers; this skill never
  mentions one.
