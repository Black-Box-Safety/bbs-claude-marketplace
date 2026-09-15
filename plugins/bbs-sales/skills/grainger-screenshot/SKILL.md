---
name: grainger-screenshot
description: >-
  Extract part numbers and quantities from a screenshot or image of a Grainger page — a cart,
  order or item table shared as PNG, JPG or similar. Use when Grainger items arrive as a
  picture rather than as a PDF or text and the rep wants them pulled out. Always output [Part
  Number or Grainger Item #],[QTY] lines, never a table or prose. Do NOT use for a Grainger
  cart saved as a PDF (use grainger-cart-info), a DWR Request for Quotation PDF (use dwr-pdf-
  info), checking DGS BPO eligibility (use dgs-bpo-item-check), or pricing items (use
  bbs-b2b-pricing).
---

# Grainger Screenshot

Extracts part numbers and quantities from a screenshot of a Grainger table or cart view.

## Input

An image (screenshot) of a Grainger page — typically a cart, order, or item table showing part numbers (Grainger Item # or Manufacturer Part #) and quantities.

## Instructions

1. Examine the screenshot carefully.
2. Identify the column containing part numbers. This may be labeled:
   - **Grainger Item #** (preferred — use if present)
   - **Mfr. Model #** or **Manufacturer Part #** (use if no Grainger Item # column)
   - Any similar identifier column
3. Identify the quantity column (typically labeled **Qty**, **Quantity**, or **QTY**).
4. For each line item in the table, output one entry in this exact format:

```
[Part Number or Grainger Item #],[QTY]
```

No header row. No extra text. No table formatting. One item per line.

## Output Example

```
6YPH8,2
4CZ16,1
7AA83,5
```

## Edge Cases

- **Multiple pages visible**: Extract all visible items.
- **Both Grainger Item # and Mfr Part # present**: Use the Grainger Item # (the one that looks like a short alphanumeric code, e.g. `6YPH8`).
- **Quantity is blank or unclear**: Use `1` as the default and note the assumption after the list.
- **Item is struck through or marked removed**: Skip it.
- **Header rows or subtotal rows**: Skip them — only include true line items.

After the list, briefly note any assumptions made (e.g., defaulted a quantity, skipped an unclear row).
