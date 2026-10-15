---
name: bbs-quote-builder
description: >-
  Build a Black Box Safety, Inc. (BBS) sales quote in the Business Central print
  layout and deliver it as a PDF, numbered with the Business Central SQ number of
  the sales quote it represents. Use this skill whenever a
  BBS rep wants to turn a source document — a vendor cart PDF (Office Depot,
  Staples, Amazon), an RFQ spreadsheet, a customer item list, Grainger pricing,
  or pasted SKUs and quantities — into a formatted, customer-ready price quote.
  Trigger on requests like "make a quote," "build a BBS quote," "quote these
  items," "put this on our letterhead," "create a sales quote," "turn this cart
  into a quote," or any time a rep hands over items/prices and wants the branded
  BBS quote document. Always use this skill for BBS customer-facing quotes so the
  quote number, pricing math, and layout stay uniform. Do NOT use it to create or
  edit quote records in Business Central (a rep does that; this skill only reads
  the quote back), or for vendor sourcing emails (use bbs-sourcing).
requires: [business-central, node, docx-npm, libreoffice]
---

# BBS Quote Builder

Produces a Black Box Safety sales quote PDF in the layout Business Central prints
for BBS quotes (reference SQ-104776; Parker chose this layout on 2026-09-28). The
goal is uniformity: a quote built here should be indistinguishable in form from
one printed out of BC, and every rep's quote should do the pricing math the same
way.

## What the finished quote looks like

- **Header**: BBS logo top-left; `Quote - SQ-######` centered, with the company
  block beneath it — legal name, street, city/state/zip, phone, and the
  certification line for the channel (`certChannel`). All of it is read from
  `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`; nothing is typed.
- **Bill to Address** / **Ship to Address** columns.
- **Metadata grid**: Document Date, Valid to, Payment Terms on the left;
  Shipment Method and optional Solicitation on the right.
- **Optional note lines** under the grid (`notes[]`).
- **Line table**: `Item No. | Description | Qty | Unit Price | Amount`, with
  optional `UOM`, `Country of Origin` and `Lead Time` columns.
- **Totals band**: `Subtotal | Tax % | Tax Basis | Tax Amount | Total`.
- **Optional footer notes** (`footerNotes[]`) and **Page X / Y** bottom-right.

The layout comes from `scripts/build_quote.js` and the bundled
`assets/bbs_logo.png` — do not re-create it by hand, and do not re-crop the logo.

## Workflow

### 1. Read the source and extract line items

The source may be a vendor cart PDF, an RFQ spreadsheet (.xlsx), a customer item
list, or pasted text. Extract for each line: **part number / SKU**, **description**,
**quantity**, **unit of measure**, and **unit cost**.

- Use the appropriate reading approach for the file type (PDF skill / pdf-reading
  for PDFs, xlsx skill for spreadsheets). If items are already visible in the
  conversation, just use them.
- For **Amazon** items, the part number is the **ASIN** (10-char code, e.g.
  `B08N3GCLYP`). If only an `a.co` short link is given, these don't reliably
  resolve to an ASIN via search — ask the rep to paste the ASIN from the product
  page URL. Don't guess an ASIN.
- If a line genuinely has no part number, leave it blank (the script renders an
  em-dash).

### 2. Read the quote back from Business Central

The quote number is the **`SQ-######` number of the Business Central sales quote this
document represents**. BC assigns it when the quote record is created, and a person
creates that record — this skill reads Business Central and never writes to it.

1. **Get the SQ number from the rep.** If the quote doesn't exist in BC yet, ask the rep to
   create it there first and tell you the number. Do not rely on a number you worked out
   yourself: never generate one, never take the highest existing SQ and add one, never
   reuse a number off an old PDF. A predicted number can be taken by another rep a minute
   later and then sits on a customer document pointing at someone else's quote.
2. **Read it back.** `bc_get_sales_document` with the SQ number (it searches quotes), or
   `bc_query_entity` on `salesQuotes` with `filter=number eq 'SQ-######'`.
3. **Confirm it is the right record by the sell-to customer.** A BC quote carries two
   customers and they often differ — a Caltrans district is the sell-to customer while
   the Department of Transportation is the bill-to. The check uses the **sell-to**
   `customerNumber` (and `customerName`): it must be the customer this document is for.
   On the `naspo-quote` path, compare it with the "BC customer ID" in the buyer's
   `<Buyer Name>.txt`. Say which customer you found; if it is a different one, stop.
4. **Take the header from the record** rather than re-typing it:
   - bill-to and ship-to address fields → `billTo`, `shipTo`
   - `documentDate`, `validUntilDate` → `documentDate`, `validTo`
   - `paymentTermsId` → look it up in `paymentTerms` (`bc_query_entity`,
     `filter=id eq <paymentTermsId>`) and print its `displayName` as `paymentTerms`
   - `shipmentMethodId` → look it up in `shipmentMethods` the same way →
     `shipmentMethod`

   Where the rep's source disagrees with BC, show both and ask — a `[FLAG: …]`, never a
   silent overwrite. If BC has no payment terms or shipment method (the id is all
   zeros), ask the rep; the script has no default for either. **If the BC bill-to address fields are empty** (it happens), say
   so and ask the rep for the bill-to address — do not print a name-only Bill to block.
5. **If the BC quote already has lines**, compare them with the lines you are about to
   print — item, quantity, total. A mismatch is a `[FLAG: …]` for the rep, not something
   to resolve by picking one side. Compare **tax** the same way: the spec's `taxRate`
   against the BC lines' `taxPercent` (or, with no line tax detail, the header
   `totalTaxAmount` against the tax the document will print). A mismatch is a
   `[FLAG: …]`; never overwrite either side silently.

**If there is no SQ number, it doesn't resolve, or Business Central is unreachable, stop**
and tell the rep: `Quote number: [MISSING — NEEDS INPUT] — no Business Central sales quote
to read back.` There is no fallback. The retired local 900001 series is not one, and
neither is a placeholder "to fix later".

Copy the sell-to `number`, `customerNumber` and `customerName` from the read-back into
the spec's `bcQuote` block. The script refuses to build without it, and prints a
`WARNING:` if that customer name appears in neither the Bill to nor the Ship to block.

### 3. Confirm the things that vary every time

Before building, ALWAYS confirm these with the rep — they change per quote and
getting them wrong is costly:

1. **Pricing method and rate** — this is the single most error-prone part, so
   confirm it explicitly every time. See "Pricing" below. The rep chooses the
   method (margin, markup or at-cost) AND the rate for non-Grainger lines; there
   is no house figure to fall back on, and the script fails without one. If
   there are Grainger lines, also confirm whether they are at cost on this
   channel (see "Pricing").
2. **Certification channel** — `certChannel` picks the certification line on the
   header, and there is no default. `california` prints DVBE (California state
   agencies — never SB; BBS is not a California small business), `federal`
   prints SDVOSB (federal agencies and primes), `none` prints no line (local or
   commercial buyers, unless the rep says otherwise). The strings come from
   `vendor_profile.json`; the channel rule is canon — `bbs-foundations`
   `references/canonical-facts.md`, "Small-business status is channel-dependent". For `california` the script checks the
   DVBE expiration in the profile against the document date: expired stops the
   build, within 30 days warns — pass that warning to the rep.
3. **Tax** — ask whether to add sales tax and at what rate. Tax is based on the
   **ship-to jurisdiction**. Pre-tax quotes are common and fully supported. Check
   the rate against the BC quote's tax (step 2.5). The script accepts only a
   decimal from 0 to under 0.2 (`0.0875`, not `8.75` or `"0.0875"`).

Also confirm Bill-to and Ship-to against the BC header. For RFQs, the ship-to
drives the tax rate; if only an agency HQ address is on the document, confirm
it's the real delivery point before relying on it.

### 4. Pricing

**Whether Grainger lines are at cost depends on the channel.** The rule lives
once, in "Grainger sell rule, by channel" in
`bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md` —
read it there rather than recalling it. On a channel canon lists as open, ask
the rep; never infer.

Mark every Grainger-priced line `"source": "grainger"` with the MCP `unitPrice`
as its `unitCost` — or, on a prime, the discounted cost the rep obtained from
BBS's Grainger account manager — and state the channel's rule in the spec:

- `pricing.method: "at-cost"` — the whole quote is at cost (a CA state schedule
  or NASPO order; `naspo-quote` sets this for you).
- `pricing.graingerAtCost: true` — Grainger lines at cost, other lines by the
  method. Only on a channel canon rules at cost.
- `pricing.graingerAtCost: false` — Grainger lines follow the method like any
  other line. Only when the rep has said so for this channel.

If a spec has Grainger lines and states none of these, the script exits 1:
there is no default either way. If canon does not settle the channel and the
rep hasn't said, ask — do not pick one.

For non-Grainger lines the rep chooses the method and rate. The three methods
produce different numbers:

- **Margin**: `sell = cost ÷ (1 − rate)`. A 20% margin on a $6.49
  cost → $6.49 ÷ 0.80 = **$8.11**. The profit is 20% *of the sell price*.
- **Markup**: `sell = cost × (1 + rate)`. A 20% markup on $6.49 → $6.49 × 1.20 =
  **$7.79**. The profit is 20% *of the cost*.
- **At cost**: `sell = cost`. For a whole quote sold at cost — a state schedule
  or NASPO order, where `naspo-quote` sets this for you.

"Mark it up 20%" colloquially can mean either margin or markup — so restate the
method and show a one-line example before generating if there's any ambiguity.
The script takes `pricing.method` = `"margin"`, `"markup"` or `"at-cost"` and
`pricing.rate` as a decimal below 1 — so markup is capped under 100%, which also
catches a percent typed as `20` instead of `0.20`. Discount (negative) lines are
not supported.

The Grainger rule only reaches lines that carry the tag: an untagged Grainger
line in a margin quote **is** marked up, even with `graingerAtCost: true`. Tag
every line priced through `grainger-pricing`, and check the count in step 9.

`unitCost` in the spec is always the **vendor cost**; the script derives the
customer Unit Price. Never pre-apply the markup to the cost yourself.

### 5. Estimated pricing flag

If unit costs are estimates (e.g. online retail rather than confirmed vendor
quotes), set `estimatedPricing: true`. The script appends a `*` to every price
and adds a footnote. Use this for any quote built before real vendor costs are
in — it keeps the rep honest with the customer and reminds them to revise.

### 6. Optional columns and notes

Turn columns on only when they earn their place — each one narrows the
description.

- `columns.uom` — a **UOM** column. Use when units vary (Pack, Box, Case); skip
  it when everything is Each. With it on, every line needs its `uom` from the
  source — there is no default, because a pack price printed as "Each" is a
  wrong number.
- `columns.countryOfOrigin` — a **Country of Origin** column, for federal or
  Buy American-sensitive bids. **Print only a documented origin.** On a federal
  or prime document an origin is a certification, so a guessed one is a false
  certification. Each line's `countryOfOrigin` needs a `countryOfOriginSource`
  naming where it is documented (a tool result, the manufacturer's spec sheet,
  the vendor's written quote) or the script refuses to build. A line with no
  documented origin: leave `countryOfOrigin` out — the cell prints blank and the
  script prints a `[FLAG: …]` for the rep. There is no default origin.
- `columns.leadTime` — a **Lead Time** column from `items[].leadTime` (em-dash
  when a line has none). Lead times come from a tool result (e.g.
  `grainger_availability`) or the vendor's written quote — never estimated.
- `notes[]` — free-text lines under the metadata grid (BC prints things like
  "75 day lead time" there). Rep-supplied.
- `footerNotes[]` — small grey lines under the totals band, e.g. "Quote valid
  through date shown. Pricing subject to product availability. Reference quote
  number on any resulting order." Rep-supplied.
- `taxBasis` — only when tax applies to less than the full subtotal (e.g. a
  non-taxable line). It must not exceed the subtotal; check it against the BC
  quote's tax the same way as the rate. A `taxBasis` with no tax rate prints a
  `WARNING:` — usually one of the two is a mistake.

### 7. Build the spec and generate the docx

Write a JSON spec (schema in `references/spec-schema.md`) and run:

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/bbs-quote-builder/scripts/build_quote.js" /path/to/spec.json /path/to/output.docx
```

Run it exactly so — through `bbs-fill`, no `cd`, nothing chained: the managed settings
allow `Bash(bbs-fill *)`, and `bbs-fill` (the `bbs-tools` plugin) runs only vetted scripts.
If `bbs-fill` is not found, the `bbs-tools` plugin is missing; rerun the bootstrap, and
meanwhile use `node` in its place, which asks for permission.

`bbs-setup.ps1` (Windows) and `bbs-setup.sh` (Mac) install `docx` globally and set
NODE_PATH — nothing to do (restart VS Code after running it). If `build_quote.js` says docx
is missing (no bootstrap), run `npm install docx` inside
`${CLAUDE_PLUGIN_ROOT}/skills/bbs-quote-builder` once per plugin update.

The script reads the BBS logo from `assets/bbs_logo.png` relative to its own
location, so it does not care where the spec or the output live. It runs
offline and exits with an `ERROR:` line — building nothing — if `bcQuote` is
missing or malformed, a required field is missing (`certChannel`, dates,
addresses, payment terms, shipment method, descriptions), the pricing or tax
values are invalid, a country of origin has no source, or the spec still uses
the retired `quoteNumber` field. It reads the company block from
`vendor_profile.json` and fails if that file or a key in it is missing. Its
last lines echo the SQ number, the BC customer, the certification line, the
pricing basis, the totals and any `[FLAG: …]` count; check them against what
the rep expects before converting.

### 8. Convert to PDF (this skill delivers PDF)

The rep wants a PDF. Convert the generated docx:

```bash
soffice --headless -env:UserInstallation=file:///tmp/loprofile \
  --convert-to pdf /path/to/output.docx
```

Earlier revisions of this skill called a LibreOffice wrapper under
`/mnt/skills/public/docx`, which exists only inside a Claude session. `soffice`
directly is the portable equivalent.

If the conversion fails with a profile or lock error (common when several
conversions run in one session), point it at a fresh profile directory and
retry:

```bash
soffice --headless -env:UserInstallation=file:///tmp/loprofile-$$ \
  --convert-to pdf --outdir /output/dir /path/to/output.docx
```

Then copy the PDF to the outputs directory and present it. The default
deliverable is **PDF only** — generate the docx as an intermediate, but present
the PDF unless the rep also asks for the editable Word file.

### 9. Verify before presenting

Render the first page (e.g. `pdftoppm -png -r 100 output.pdf preview`) and
eyeball it: the SQ number in the title is the one you read back, logo present,
the certification line right for the channel, all line items, correct totals
band, estimate footnote present if flagged, Grainger lines priced by the rule
the spec states, and every flagged blank origin reported to the rep. Confirm the math on at
least one line (cost → sell → amount) matches the chosen method.

Check the script's `Pricing:` line: the Grainger count it echoes ("N Grainger
line(s) at cost", or "… (graingerAtCost false)") must equal the number of lines
priced through `grainger-pricing`. If it is lower, a Grainger line is untagged
and has been priced by the method — fix the spec and rebuild.

## Naming

Name the output `{Customer}_Quote_{SQ number}.pdf` (e.g.
`VHC_Yountville_Quote_SQ-104797.pdf`). Keep it recognizable.

## Reference files

- `references/spec-schema.md` — full JSON spec schema with a worked example.

## Notes on data integrity

This skill makes a customer-facing financial document. Don't invent prices, part
numbers, addresses, or quote numbers — the number exists in Business Central
before it exists on the document. If a cost is unknown, either get it from the rep or mark
the quote estimated (step 5). For competitive California state RFQs where you
need real vendor pricing, that sourcing happens in the `bbs-sourcing` skill
first — this skill formats the result.
