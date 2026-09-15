---
name: rfq-item-extract
description: >-
  Pull item numbers and quantities out of whatever a customer or agency sent, and return them
  in the format the next step needs. Three sources: a Grainger cart saved or printed as a PDF;
  a screenshot or image (PNG, JPG) of a Grainger cart, order or item table; and a California
  Department of Water Resources Request for Quotation PDF — spoken of as DWR, a DWR RFQ, or
  "the DWR PDF" — including scanned and image-only files. Use whenever a rep wants the items
  pulled out of a file or an image: "get the item numbers and quantities", "pull the items
  from this cart", "extract from this screenshot", "DWR PDF info". Output is ITEM#,QTY lines
  ready to paste into the Grainger purchasing portal, or the DWR sourcing table. Do NOT use to
  price items (grainger-pricing), to check DGS BPO eligibility (dgs-bpo-item-check), or to
  fill state forms (ca-form-filler) — this produces the list those consume. If a rep says only
  "check these items", ask whether they mean price or BPO eligibility.
---

# Extract items from what the agency sent

One skill for every way a list of items arrives. It reads the file, identifies the source,
and returns the list in the shape the next step expects. It does not price anything, check
eligibility, or fill a form — it produces the list those skills consume.

## Identify the source first

| What arrived | Path | Output |
|---|---|---|
| PDF saved or printed from grainger.com/cart | Grainger cart | `ITEM#,QTY` lines |
| PNG/JPG of a Grainger cart, order or item table | Grainger screenshot | `ITEM#,QTY` lines |
| DWR Request for Quotation PDF | DWR RFQ | depends on mode — ask |

If the file is none of these — a different agency's RFQ, a vendor worksheet, a
spreadsheet — say so rather than extracting from it anyway. A wrong item number reaches a
bid; a clear "this is not a format I read" costs a question.

The mechanics of each source — the cart's text pattern, the screenshot's column
preference, the DWR table's structure and its three modes — are in
`references/source-grainger.md` and `references/source-dwr-rfq.md`. Read the one that
matches before extracting.

## Rules that hold for every source

1. **Never invent an item number or a quantity.** A line you cannot read is a flagged
   line, not a guess. These lists become bids.
2. **Flag an inference as an inference.** The DWR path can mark a line "assumed Grainger"
   from its number's shape — it gets an asterisk and a flag so a human confirms it. Apply
   the same instinct anywhere else you infer.
3. **Note when the source was an image.** Visual reading is slower and less reliable than
   parsing text; the rep should know which one produced their list.
4. **De-duplicate, first occurrence wins.** Carts repeat items in "Recently Viewed"
   sections.
5. **Output the format, and nothing else.** `ITEM#,QTY` means a plain code block, one
   entry per line, no headers and no prose inside it — the rep pastes it straight into the
   Grainger portal. Put the count and any flags *after* the block.

## Grainger cart PDF

Parse the text, de-duplicate, output the block, then
`X items extracted from [filename].` Scanned or image-only carts are read visually into
the same format, with a note at the top that the source was image-based. Details and edge
cases: `references/source-grainger.md`.

## Grainger screenshot

Find the part-number column — prefer **Grainger Item #** over a manufacturer part number —
and the quantity column. Output the same `ITEM#,QTY` block. Skip struck-through rows,
headers and subtotals; default an unclear quantity to `1` and say so afterwards. Details:
`references/source-grainger.md`.

## DWR RFQ PDF

The rep names a mode — **Grainger**, **Sourcing**, or **Mixed**. Each produces a different
shape, so **never guess the mode; ask if it was not given.**

- **Grainger** — every line is a Grainger item → `ITEM#,QTY` block.
- **Sourcing** — no Grainger items → a copy-pasteable table of Item # / Description /
  Quantity / Unit.
- **Mixed** — both → that table plus a ProCo Input column carrying `ITEM#,QTY` for the
  Grainger lines.

Structure, vendor-SKU rules, page-overflow handling and the assumed-Grainger test:
`references/source-dwr-rfq.md`.

## What happens next

The list usually goes to one of three places, and the rep should say which:

- **Pricing** → `grainger-pricing` prices it through the Grainger MCP against the buying
  facility's account.
- **BPO eligibility** → `dgs-bpo-item-check` checks the part numbers against the DGS list.
- **A bid packet** → `ca-form-filler` takes the line items into the state forms.

---

Owner: Parker. Last verified 2026-09-15.
