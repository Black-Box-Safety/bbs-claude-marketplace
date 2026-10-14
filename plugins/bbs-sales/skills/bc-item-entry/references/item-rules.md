# Item rules and edge cases

What the script enforces and why, with the cases that have already gone wrong once. The
script is the checker for every rule marked **[script]**; the rest are judgment calls for
you and the rep before the spec is written.

## The card BC gets

| Field | Value | Source of the rule |
|---|---|---|
| Type | `Inventory`, always **[script]** | Parker, 2026-09-04: never Non-Inventory. The first API item was created Non-Inventory on an inference from old data and had to be patched |
| Gen. Prod. Posting Group | `PRODUCTS` **[script]** | The Product template, which the API cannot apply, so the value is sent explicitly |
| Inventory Posting Group | `INVENTORY` **[script]** | Same |
| Tax Group | `TAXABLE` **[script]** | Same |
| Base UoM | explicit, must exist in BC **[script]** | `EA` for 95% of items; packs and cases carry their real code |
| Description | 1-100 ASCII, manufacturer first **[script]** | SOP limit; house style is "Carr Lane CL-2500-SHR-1 Swivel Hoist Ring", not "Hoist ring by Carr Lane" |
| Description 2 | up to 50 ASCII **[script]** | Overflow only |
| Unit Cost | > 0, per base UoM **[script]** | Parker's ruling for this skill: no item without a cost |
| Unit Price | optional, never below cost **[script]** | Blank is normal for Grainger items |
| Vendor No. | existing, unblocked vendor **[script]** | Parker's ruling for this skill: no item without a vendor. Set through the Item Card web service, because the v2.0 items entity does not expose it |
| Vendor Item No. | optional **[script]** | Same route |
| Item Category, Replenishment, Costing Method, Lead Time, Reorder fields, Tariff, Country of Origin, Item Tracking, Warehouse | left blank or at BC default | BBS leaves these blank by design (`#GK4-M` reference card) |

## Vendors

- The vendor must exist and not be blocked. The script stops otherwise and prints the BC
  steps; it never creates one. There is no house Vendor Card SOP as of 2026-10-14
  [FLAG: SOP gap], so a rep unsure of payment terms or posting groups asks Parker before
  saving the card.
- `vendorName` on the spec is a tripwire: the check stops when BC's name for the number
  does not contain it. `V10017` is Grainger; `V11469` is Geisler, the Carr Lane
  distributor. Do not carry other numbers in your head; look them up.
- Mixed batches (Carr Lane rings plus a Grainger hoist) put the vendor on each row.
- A vendor whose BC address does not match the quote's letterhead is worth a question to
  the rep before the check, not after the items exist.

## Cost

- Cost is the vendor's price to BBS for one base unit, before freight and tax. A quote line
  that bundles freight or adds a card fee is not the cost; note the fee in `source` and
  keep the cost clean.
- `costPer` must equal `baseUoM`. PO 791645 carried item 99700 at a $111.15 case cost
  against a $16.40 each sell; the margin reports were wrong until someone noticed.
- Grainger cost comes from the Grainger MCP or a CSP quote on the **buying institution's
  own account**. A different account returns a different price that still looks valid.
  Record the account in `costSource`.
- An expired vendor quote is still the only cost you have; record its date and let the rep
  decide whether to re-quote before committing. The script does not check dates.
- A cost in a currency other than USD is a stop; BBS items are USD.

## Price

- Price below cost is a stop. Price equal to cost is a stop unless the row carries
  `zeroMarginOk: true`, because PO 813783 sent two lines at 0% that the PO then locked.
- Missing price is a warning, not a stop. Normal for Grainger items; an exception for
  anything else, so the rep sees it on the sheet.

## Item numbers

- 1-20 ASCII characters. Apostrophes are allowed and escaped by the script.
- Grainger-filled buys use the Grainger SKU as the number, with the customer's tag at the
  front of the quote-line description, not the item description.
- Bare manufacturer part numbers collide: Ergodyne `3174` was already a Dynarex bandage in
  BC. When the check reports "already exists", read the card the script prints. Same
  product: quote that number and drop the row. Different product: use a number that cannot
  collide and tell the rep why.
- The script will not patch an existing card for any reason. Vendor or cost fixes on
  existing items are a separate, explicit request (`bc_patch_item_vendor.py` in the
  BC-Write-API folder covers the vendor).

## Units of measure

- Pack and case items carry the pack code as base UoM (`PK10`, `PK3`, `CS`) when the vendor
  sells and the customer buys by the pack. If the vendor sells each and the customer buys a
  pack, stock each and let the quote line carry the pack; do not invent a pack cost.
- The script validates the code against BC's own list and prints that list when a code is
  wrong.

## Bundled accessories

- A $0 line on a vendor quote (a power cord shipped with a switch) is not an item with a
  cost. Either leave it off the item master and mention it in the parent's `displayName2`,
  or enter it with `includedWith` naming the parent so the zero is explicit and reviewed.

## Descriptions

- ASCII only: hyphens, not em dashes; straight quotes, not curly. Downstream exports are
  ASCII-only and SQ-104848 had to be patched for this.
- Shorten deliberately when over 100: drop marketing words, keep manufacturer, model,
  size, rating. Never let the API decide what to cut.
- Service items (labor, freight estimate) are out of scope; they follow the Service template
  in the BC UI. The `SHIPPING` item already exists for freight lines.

## Scope

- Body armor and higher-education items follow the same card rules; the book split is a
  quoting matter, not an item matter.
- This skill does not build quotes, orders, or vendor POs. Sentinel POs use the per-PO
  builders in `PM Claude/BC-Write-API/`; customer PDFs use `bbs-quote-builder`.
- Website catalog loading is `bbs-pricelist-import` (Supabase), a different system.

## Authentication

- Default is the rep's own sign-in (device code, `msal`), cached in
  `~/.bbs/bc_token_cache.json`. The log records the signed-in user.
- `BBS_BC_ENV_FILE` with `BC_CLIENT_SECRET` present switches to the shared service
  principal. Parker's connection file for reps (`.env.rep`) carries no secret on purpose.
- A 401 on write with a 200 on read means the rep's BC user lacks a permission set covering
  item write. That is a BC admin fix, not a script fix.
- `CERTIFICATE_VERIFY_FAILED` on a Mac means the python.org build; use `/usr/bin/python3`.
