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
- `vendorName` is a tripwire on every vendor number in the spec: the check stops when BC's
  name for the number does not contain it, and a vendor number with no name anywhere in the
  spec is an error before BC is even asked. No vendor number is carried in a file or in
  anyone's head, Grainger's included: every vendor is resolved by name through the BC
  connector when the spec is written, and the examples here write `V#####`.
- Mixed batches (one vendor's parts plus a Grainger hoist) put `vendorNo` and `vendorName`
  on each row that differs from the top-level vendor.
- A vendor whose BC address does not match the quote's letterhead is worth a question to
  the rep before the check, not after the items exist.

## Cost

- The source names a document. The script rejects any stem of verbal, estimate, approx,
  roughly, guess, ballpark, phone, "from memory", "last time", typical, TBD and later, so
  "estimated", "approximately" and "Guesstimate" all fail; and it rejects a source with no
  number or date in it. `scripts/test_bc_item_entry.py` holds those words as a test.
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

- 1-20 ASCII characters, upper-case: BC stores Code fields upper-case, so a lower-case
  number in the spec would not match the card BC creates, and the duplicate check would
  miss it. The script stops on lower-case rather than silently converting. Apostrophes are
  allowed and escaped by the script.
- Grainger-filled buys use the Grainger SKU as the number, with the customer's tag at the
  front of the quote-line description, not the item description.
- Bare manufacturer part numbers collide: Ergodyne `3174` was already a Dynarex bandage in
  BC. When the check reports "already exists", read the card the script prints. Same
  product: quote that number and drop the row. Different product: use a number that cannot
  collide and tell the rep why.
- The script will not patch an existing card for any reason. Vendor or cost fixes on
  existing items are a separate, explicit request (`bc_patch_item_vendor.py` in
  `PM Claude/BC-Write-API` on SharePoint covers the vendor).
- If a commit creates an item and then the Vendor No. step fails (the Item Card web service
  rejects the PATCH, or the read-back disagrees), the item exists in BC without a vendor.
  The script says so by number, names the recovery (set Vendor No. in the BC UI or run
  `bc_patch_item_vendor.py`), and stops; re-running commit would stop on the duplicate gate.
  `whoami` and `check` read `Item_Card_Excel` first so that this is rare, not routine.

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

- Connection values ship with the plugin in `references/bc-connection.json`: tenant, client
  id, environment, company id, and nothing else (the script and the marketplace checker both
  stop on any other key). The company name is read from BC at run time. `BBS_BC_ENV_FILE`
  and `BC_*` environment variables override the file; every run prints where each value
  came from.
- Default is the rep's own sign-in (delegated): a browser window first, a device code if
  that cannot open. The token cache is encrypted with `msal-extensions` (Keychain on a Mac,
  DPAPI on Windows); without that library it is a 0600 file in a 0700 `~/.bbs`. With more
  than one cached account, `--account` or `BBS_BC_ACCOUNT` picks one; the script never
  silently takes the first. `logout` removes a cached account. The log and the item card
  record the signed-in user.
- App-only (the service principal) runs only with `BBS_BC_AUTH=app-only` and a
  `BC_CLIENT_SECRET` in `BBS_BC_ENV_FILE` or the environment. A secret without the flag is
  ignored and said so. Commit refuses app-only without the flag, and the review sheet and
  log flag an app-only run because the card then shows the app as creator, not the rep. A
  rep is never given a file that carries `BC_CLIENT_SECRET`.
- `whoami` and `check` read items, vendors and `Item_Card_Excel` (`$top=1` each) before
  anything else. If any of the three fails, nothing is checked or committed: a commit with
  `Item_Card_Excel` unreachable would create items with no vendor. A read PASS does not
  prove write rights; `rep-setup.md` section 5b (one delegated commit under a rep-class
  permission set, once) is what does.
- An empty units-of-measure list from BC is a stop, not a skipped check.
- What each sign-in or BC error means for the rep is the table in SKILL.md; the script
  prints the same plain-language line next to the raw code. A 401 on write with a 200 on
  read means the rep's BC user lacks a permission set covering item write. That is a BC
  admin fix, not a script fix.
- `CERTIFICATE_VERIFY_FAILED` on a Mac means a python.org build is ahead of `/usr/bin` on
  PATH; `bbs-fill` runs `python3` from PATH, and the bootstrap's `/usr/bin/python3` does not
  have the problem. Fix the PATH rather than the script.
- The script runs through `bbs-fill` (on its allow list by ruling, Parker 2026-10-16); the
  rep's named sign-off on the review sheet is the gate, with no Allow click on top.
