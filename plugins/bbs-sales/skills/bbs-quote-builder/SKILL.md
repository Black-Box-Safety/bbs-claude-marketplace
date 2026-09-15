---
name: bbs-quote-builder
description: >-
  Build a Black Box Safety, Inc. (BBS) sales quote on company letterhead in the
  standard SQ-104032 format and deliver it as a PDF. Use this skill whenever a
  BBS rep wants to turn a source document — a vendor cart PDF (Office Depot,
  Staples, Amazon), an RFQ spreadsheet, a customer item list, or pasted SKUs and
  quantities — into a formatted, customer-ready price quote. Trigger on requests
  like "make a quote," "build a BBS quote," "quote these items," "put this on our
  letterhead," "create a sales quote," "turn this cart into a quote," or any time
  a rep hands over items/prices and wants the branded BBS quote document. Always
  use this skill for BBS customer-facing quotes so numbering, the 900001-series
  format, the margin/markup math, and the letterhead layout stay uniform across
  the company. Do NOT use this skill to pull existing quote records out of
  Business Central (this skill builds the document from source data), and do NOT
  use it for internal vendor sourcing emails (use bbs-sourcing for that).
---

# BBS Quote Builder

Produces a Black Box Safety sales quote PDF that matches the company-standard
SQ-104032 layout. The goal is uniformity: every rep's quote should look
identical and do the pricing math the same way, so customers and colleagues see
one consistent BBS document.

## What the finished quote looks like

A single-page (or multi-page if needed) document with:

- **Header**: "Sales Quote - {number}" title, BBS company block on the left
  (name, address, email, phone, website), BBS logo top-right, "Page X / Y".
- **Bill to** / **Ship to** columns.
- **Metadata block**: Solicitation (optional), Shipment Method, Document Date,
  Valid to.
- **Line-item table**: columns `# | Part # | Description | Qty | UOM | Unit Price | Amount`.
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

### 2. Confirm the three things that vary every time

Before building, ALWAYS confirm these with the rep — they change per quote and
getting them wrong is costly:

1. **Quote number** — prompt for it (BBS uses the **900001 series**, e.g.
   `900003`). Do not auto-assign.
2. **Pricing method and rate** — this is the single most error-prone part, so
   confirm it explicitly every time. See "Pricing: margin vs. markup" below.
   BBS's house default is **20% gross margin**, but never assume — confirm the
   method (margin or markup) AND the rate.
3. **Tax** — ask whether to add sales tax and at what rate. Tax is based on the
   **ship-to jurisdiction**. Pre-tax quotes are common and fully supported.

Also confirm Bill-to and Ship-to. For RFQs, the ship-to drives the tax rate; if
only an agency HQ address is on the document, confirm it's the real delivery
point before relying on it.

### 3. Pricing: margin vs. markup

These are different and produce different numbers. Confirm which the rep wants:

- **Margin** (BBS default): `sell = cost ÷ (1 − rate)`. A 20% margin on a $6.49
  cost → $6.49 ÷ 0.80 = **$8.11**. The profit is 20% *of the sell price*.
- **Markup**: `sell = cost × (1 + rate)`. A 20% markup on $6.49 → $6.49 × 1.20 =
  **$7.79**. The profit is 20% *of the cost*.

"Mark it up 20%" colloquially can mean either — so restate the method and show a
one-line example before generating if there's any ambiguity. The script takes
`pricing.method` = `"margin"` or `"markup"` and `pricing.rate` as a decimal.

`unitCost` in the spec is always the **vendor cost**; the script derives the
customer Unit Price. Never pre-apply the markup to the cost yourself.

### 4. Estimated pricing flag

If unit costs are estimates (e.g. online retail rather than confirmed vendor
quotes), set `estimatedPricing: true`. The script appends a `*` to every price
and adds a footnote. Use this for any quote built before real vendor costs are
in — it keeps the rep honest with the customer and reminds them to revise.

### 5. Build the spec and generate the docx

Write a JSON spec (schema in `references/spec-schema.md`) and run:

```bash
# SKILL_DIR is the folder holding this SKILL.md — wherever the plugin installed.
cd "$SKILL_DIR"
npm install docx        # first run only
node scripts/build_quote.js /path/to/spec.json /path/to/output.docx
```

The script reads the BBS logo from `assets/bbs_logo.png` relative to its own
location, so it does not care where the spec or the output live.

### 6. Convert to PDF (this skill delivers PDF)

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

### 7. Verify before presenting

Render the first page (e.g. `pdftoppm -png -r 100 output.pdf preview`) and
eyeball it: logo present, all line items, correct totals, tax line correct,
estimate footnote present if flagged. Confirm the math on at least one line
(cost → sell → amount) matches the chosen method.

## Naming

Name the output `{Customer}_Quote_{number}.pdf` (e.g.
`VHC_Yountville_Quote_900001.pdf`). Keep it recognizable.

## Reference files

- `references/spec-schema.md` — full JSON spec schema with a worked example.

## Notes on data integrity

This skill makes a customer-facing financial document. Don't invent prices, part
numbers, or addresses. If a cost is unknown, either get it from the rep or mark
the quote estimated (step 4). For competitive California state RFQs where you
need real vendor pricing, that sourcing happens in the `bbs-sourcing` skill
first — this skill formats the result.
