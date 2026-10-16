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
  (bc-quote-entry does that, after the items exist), or to load the website catalog
  (bbs-pricelist-import).
requires: [business-central, python3, msal, msal-extensions]
---

# BC Item Entry

Creates item cards in Business Central from a spec the rep has read and approved. The
script carries the rules; this file tells you how to get a clean spec in front of the rep
and what you must not do on their behalf.

**Three gates, none of them yours to waive** (ruled by Parker, 2026-10-14; the record is
`docs/STEWARD.md` in the marketplace repo, which is not on a rep's machine).

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

The full checklist, with what an admin confirms in BC and Entra and the expected output of
each step, is `references/rep-setup.md`. The short form:

- The connection values ship with the plugin in `references/bc-connection.json` (tenant,
  client id, environment, company id; **no secret, ever**). Nothing to copy from the shared
  drive. A rep is never handed a file that carries `BC_CLIENT_SECRET`.
- Install the sign-in libraries into the interpreter the skill runs with.
  Mac: `/usr/bin/python3 -m pip install --user msal msal-extensions` (use `/usr/bin/python3`
  for every command here; the python.org build fails TLS verification).
  Windows: `python -m pip install msal msal-extensions`.
  `bbs-setup.sh` and `bbs-setup.ps1` install both as well. A missing library stops the script
  with the exact command for the interpreter that ran it.
- **Run the first `whoami` in your own terminal, not inside a Claude session:**
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/scripts/bc_item_entry.py" whoami`.
  A browser window asks for your own Microsoft work account (a device code if no browser
  can open). The sign-in is cached encrypted, so later runs, Claude's included, do not ask
  again. `whoami` then reads items, vendors and the Item Card web service once each and
  prints PASS or FAIL for the path a commit would take. That proves the reads and the
  sign-in; it does not prove your BC user may write. Write rights are proven once, by the
  one-item delegated commit in `references/rep-setup.md` section 5b, run by Parker or an
  admin under a rep-class permission set before reps use `commit`. BC records your user as
  the creator (in the item's system fields and in the skill's log).
- With more than one cached sign-in, every command takes `--account <you@blackboxsafety.com>`
  (or `BBS_BC_ACCOUNT`); the script never silently picks the first. `logout` removes one.
- App-only (the service principal) is Parker's path, not a rep's: it runs only with
  `BBS_BC_AUTH=app-only` and a secret, the review sheet and log flag it, and the card then
  shows the app as creator instead of the rep.

## Workflow

### 1. Collect the source, not a memory of it

Read the vendor quote, price list, Grainger quote or MCP result that carries the cost.
Note the document number and date; that string becomes `costSource` on every row. Decide
what one unit of cost buys (each, pack of 10, case) and carry that as `costPer`.

### 2. Resolve the vendor and the item numbers before writing the spec

- Vendor: find the number with `bc_query_entity` on `vendors` (name search is
  case-sensitive, so try the exact spelling first) or ask the rep for the V-number. Every
  vendor, Grainger included, is resolved by name through the connector at batch time; no
  vendor number lives in this skill or in your memory. Put the number in `vendorNo` and the
  name in `vendorName`; the script stops if BC's name does not contain the one you wrote,
  and it stops before asking BC if any vendor number in the spec has no name beside it. The
  vendor is who BBS buys from; `manufacturer` is the brand on the product. A distributor's
  name is not a manufacturer: if the brand is not on the quote, ask the rep rather than guess.
- If the rep would rather quote Grainger-stocked equivalents, that is a different batch,
  not a vendor swap: Grainger SKUs as item numbers, Grainger's vendor record, cost from the
  Grainger connector on the customer's account. Never put Grainger's vendor number on another
  vendor's part number.
- If Business Central cannot be reached, stop before the spec. "It isn't in BC, I checked"
  from the rep does not replace the lookup; the check will run it again anyway.
- Item numbers: check each with `bc_find_item`. If a number already exists, show the rep the
  card. Same product: quote the existing number and drop it from the spec. Different product
  (a bare manufacturer part number that collides with something else, which happens): pick a
  number that cannot collide, the Grainger SKU on Grainger-filled buys or a prefixed
  manufacturer number otherwise, and say so in the review. Item numbers are upper-case; BC
  stores them that way and the script stops on lower-case rather than converting.
- Grainger items: number is the Grainger SKU, vendor is Grainger's record looked up by name,
  cost comes from the Grainger MCP or a CSP quote on the buying institution's own account,
  and a blank price is normal because they price at quote time.

### 3. Write the spec file

Save it in the customer's folder in the document store next to the quote it serves, as
`BC-import/items-<yyyy-mm-dd>.json`, so the review sheet and the log land where the
deal lives. With no customer yet (stock items, a vendor onboarding), use the vendor's
folder under `SUPPLIERS/` in the same `BC-import/` form. Field by field:
`references/spec-schema.md`. Rules and edge cases: `references/item-rules.md`. Fill
`preparedBy` with the rep's name exactly as they will approve, and `source` with the
document the costs came from. `costSource` on every row names a document with a number or
date; the script rejects "verbal", "roughly", "estimate", "approximately", "guess" and any
stem of those, and a source with no number in it. A row that overrides `vendorNo` carries
its own `vendorName`.

### 4. Run the check

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/bc-item-entry/scripts/bc_item_entry.py" check "<spec.json>"
```

It writes nothing. It first proves the read path (items, vendors, Item Card web service) and
stops if any of the three fails (a read PASS does not prove write rights; see the setup);
then it validates every field, looks the vendors up,
duplicate-checks every number, writes `<spec>.review.md`, and prints an approval token that
is a hash of the spec. Any failure is a stop with the reason; fix the spec (or have the rep
create the vendor) and run the check again. Every edit to the spec changes the token.

### 5. Put the sheet in front of the rep

Show the review sheet in full. It names the sign-in the commit would write under; if that
line says app-only, say so out loud. Ask the rep to read it and reply with their name to
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
landed; report that list verbatim. Every run of this script, commit included, waits for the
person to click Allow: it is deliberately not on the `bbs-fill` allow list.

The sign-in that writes and the rep who approves are usually the same person. When they
differ (a rep approving in a colleague's session), the script prints a note, the log shows
both names, and that is acceptable only because the approving rep is in the chat. A rep who
has not done the one-time setup either does it, or approves in the chat of someone who has.

### 7. Close out

Tell the rep which item numbers now exist and where the log is. If the run stopped after an
item was created but before its vendor landed, the script says so by number: that item now
exists in BC without a vendor, and the recovery is the Vendor No. field in the BC UI or
`bc_patch_item_vendor.py` in `PM Claude/BC-Write-API` on SharePoint. Tell the rep that
plainly; do not re-run commit for it. The quote is a separate job: `bc-quote-entry` creates
it in BC from its own spec after the rep approves that review sheet by name (`/ca-rfq`
Gate 5), under the same sign-in, and a human releases it in BC and prints the PDF there.
Items that need Extended Text or Item References get those in the BC UI.

## When sign-in or BC says no

| What you see | What it means for the rep |
|---|---|
| `AADSTS65001` or `AADSTS90094` | Consent is missing. A tenant admin grants admin consent for the app's delegated `user_impersonation` permission. |
| `AADSTS50020` | Wrong or personal account. Sign in with the `@blackboxsafety.com` work account. |
| `AADSTS700016` | Wrong client id or tenant. Check `bc-connection.json` or the `BC_*` override in use. |
| `AADSTS53003` | Blocked by Conditional Access. Ask the admin which sign-in flow is allowed. |
| `AADSTS7000218` | The app does not allow public client flows. Admin turns it on (Authentication page). |
| `AADSTS50011` | `http://localhost` is not a registered redirect URI. Admin adds it; `BBS_BC_SIGNIN=device` works meanwhile. |
| `expired_token` | The sign-in code timed out. Run the command again, in your own terminal. |
| HTTP 401 from BC | No BC user for this account, or no licence. A BC admin adds you on the Users page. |
| HTTP 403 from BC | Your permission set lacks item insert, the Item Card page, or vendor read. BC admin, Users page. |
| `CERTIFICATE_VERIFY_FAILED` | Mac, python.org build. Use `/usr/bin/python3`. |
| `No module named 'msal'` | Install into the interpreter the message names: it prints the exact command. |

The script prints the same plain-language line beside the raw code.

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
- Never set `BBS_BC_AUTH=app-only` for a rep's batch, and never hand a rep a file with a
  client secret in it.

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
| "Vendor No. isn't an API field, create the items now and add the vendor in the UI later" | The script sets Vendor No. through the Item Card web service on every item, and checks that service is readable before it creates anything. Readable is not writable: the one-time delegated commit test in rep-setup is what proves a rep's user may PATCH the card. If the vendor step still fails after a create, the script names the item and the recovery; you never plan for that outcome. |
| "Use Parker's service-principal file, it's quicker than signing in" | App-only puts the app's name on the card instead of the rep's and needs a flag for that reason. The rep signs in once; it is cached. |

## Common mistakes

- Cost per case on an item stocked each (PO 791645: $111.15 cost against a $16.40 sell).
  `costPer` must equal `baseUoM`; convert the cost or change the unit.
- Price equal to cost slipping through (PO 813783 lines 830RU2, 256WH9 went out at 0%). The
  script stops on it unless the row says `zeroMarginOk: true` and the rep has seen that.
- Em dashes and curly quotes in descriptions. ASCII only; the script rejects them.
- A bundled $0 accessory entered as a real item. Mark it `includedWith` the parent so the
  zero is explicit, or leave it off the item master.
- The wrong vendor number with the right name in your head. `vendorName` beside every
  vendor number makes the script check the two agree, on every row that overrides the vendor.
- Lower-case item numbers. BC upper-cases Code fields; the script stops so the spec and the
  card agree.
- Treating the quote PDF's SQ number as a BC number. BC assigns numbers; this skill never
  mentions one.
