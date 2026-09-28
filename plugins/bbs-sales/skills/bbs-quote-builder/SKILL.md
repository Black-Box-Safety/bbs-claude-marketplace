---
name: bbs-quote-builder
description: >-
  Build a Black Box Safety, Inc. (BBS) sales quote on company letterhead in the
  standard SQ-104032 format and deliver it as a PDF, numbered with the Business
  Central SQ number of the sales quote it represents. Use this skill whenever a
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

Produces a Black Box Safety sales quote PDF that matches the company-standard
SQ-104032 layout. The goal is uniformity: every rep's quote should look
identical and do the pricing math the same way, so customers and colleagues see
one consistent BBS document.

## What the finished quote looks like

A single-page (or multi-page if needed) document with:

- **Header**: "Sales Quote - {SQ number}" title (the Business Central number),
  BBS company block on the left (name, address, email, phone, website), BBS logo
  top-right, "Page X / Y".
- **Bill to** / **Ship to** columns.
- **Metadata block**: Solicitation (optional), Shipment Method, Document Date,
  Valid to.
- **Line-item table**: columns `# | Part # | Description | Qty | UOM | Unit Price | Amount`,
  with an optional `Lead Time` column before Unit Price.
- **Totals**: right-aligned Subtotal, Sales Tax (if any), Total.

The logo and exact layout are produced by `scripts/build_quote.js` using the
bundled `assets/bbs_logo.png` — do not re-create the layout by hand, and do not
re-crop the logo.

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
   create it there first and tell you the number. Do not wait on a number you worked out
   yourself: never generate one, never take the highest existing SQ and add one, never
   reuse a number off an old PDF. A predicted number can be taken by another rep a minute
   later and then sits on a customer document pointing at someone else's quote.
2. **Read it back.** `bc_get_sales_document` with the SQ number (it searches quotes), or
   `bc_query_entity` on `salesQuotes` with `filter=number eq 'SQ-######'`.
3. **Confirm it is the right record**: the customer on the BC quote is the customer this
   document is for. Say which customer you found; if it is a different one, stop.
4. **Take the header from the record** rather than re-typing it: bill-to and ship-to
   address fields, `documentDate`, `validUntilDate`. Where the rep's source disagrees with
   BC, show both and ask.
5. **If the BC quote already has lines**, compare them with the lines you are about to
   print — item, quantity, total. A mismatch is a `[FLAG: …]` for the rep, not something
   to resolve by picking one side.

**If there is no SQ number, it doesn't resolve, or Business Central is unreachable, stop**
and tell the rep: `Quote number: [MISSING — NEEDS INPUT] — no Business Central sales quote
to read back.` There is no fallback. The retired local 900001 series is not one, and
neither is a placeholder "to fix later".

Copy `number`, `customerNumber` and `customerName` from the read-back into the spec's
`bcQuote` block. The script refuses to build without it.

### 3. Confirm the things that vary every time

Before building, ALWAYS confirm these with the rep — they change per quote and
getting them wrong is costly:

1. **Pricing method and rate** — this is the single most error-prone part, so
   confirm it explicitly every time. See "Pricing" below. BBS's house default
   for non-Grainger lines is **20% gross margin**, but never assume — confirm the
   method (margin, markup or at-cost) AND the rate. The script has no default
   and fails without one.
2. **Tax** — ask whether to add sales tax and at what rate. Tax is based on the
   **ship-to jurisdiction**. Pre-tax quotes are common and fully supported.

Also confirm Bill-to and Ship-to against the BC header. For RFQs, the ship-to
drives the tax rate; if only an agency HQ address is on the document, confirm
it's the real delivery point before relying on it.

### 4. Pricing

**Grainger lines are at cost, always.** The Grainger MCP `unitPrice` is the
customer price and is never marked up — the rule and its reason live in
`grainger-pricing` §2 and in canon
(`bbs-foundations/skills/bbs-claude-md-forge/references/bbs-doctrine.md` #19).
Mark every such line `"source": "grainger"` with the MCP `unitPrice` as its
`unitCost`; the script then prints it unchanged whatever `pricing.method` says.

For every other line, the rep chooses the method. These are different and
produce different numbers:

- **Margin** (BBS default): `sell = cost ÷ (1 − rate)`. A 20% margin on a $6.49
  cost → $6.49 ÷ 0.80 = **$8.11**. The profit is 20% *of the sell price*.
- **Markup**: `sell = cost × (1 + rate)`. A 20% markup on $6.49 → $6.49 × 1.20 =
  **$7.79**. The profit is 20% *of the cost*.
- **At cost**: `sell = cost`. For a whole quote sold at cost — a state schedule
  or NASPO order, where `naspo-quote` sets this for you.

"Mark it up 20%" colloquially can mean either margin or markup — so restate the
method and show a one-line example before generating if there's any ambiguity.
The script takes `pricing.method` = `"margin"`, `"markup"` or `"at-cost"` and
`pricing.rate` as a decimal.

`unitCost` in the spec is always the **vendor cost**; the script derives the
customer Unit Price. Never pre-apply the markup to the cost yourself.

### 5. Estimated pricing flag

If unit costs are estimates (e.g. online retail rather than confirmed vendor
quotes), set `estimatedPricing: true`. The script appends a `*` to every price
and adds a footnote. Use this for any quote built before real vendor costs are
in — it keeps the rep honest with the customer and reminds them to revise.

### 6. Optional Lead Time column

`columns.leadTime: true` adds a **Lead Time** column, filled from
`items[].leadTime` (em-dash when a line has none). It narrows the description,
so turn it on only when the customer asked for lead times or they differ by
line. Lead times come from a tool result (e.g. `grainger_availability`) or the
vendor's written quote — never estimated.

### 7. Build the spec and generate the docx

Write a JSON spec (schema in `references/spec-schema.md`) and run:

```bash
# SKILL_DIR is the folder holding this SKILL.md — wherever the plugin installed.
cd "$SKILL_DIR"
npm install docx        # first run only
node scripts/build_quote.js /path/to/spec.json /path/to/output.docx
```

The script reads the BBS logo from `assets/bbs_logo.png` relative to its own
location, so it does not care where the spec or the output live. It runs
offline and exits with an `ERROR:` line — building nothing — if `bcQuote` is
missing or malformed, the pricing method is missing, or the spec still uses the
retired `quoteNumber` field. Its last line echoes the SQ number, the BC
customer, the pricing basis and the totals; check that against what the rep
expects before converting.

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
all line items, correct totals, tax line correct, estimate footnote present if
flagged, Grainger lines unchanged from the MCP price. Confirm the math on at least one line
(cost → sell → amount) matches the chosen method.

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
