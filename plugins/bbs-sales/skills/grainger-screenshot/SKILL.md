---
name: grainger-screenshot
description: Extracts part numbers and quantities from a Grainger screenshot — typically a screenshot of a table or cart view showing items and quantities. Use this skill whenever Aanya uploads a screenshot (PNG, JPG, or similar image) of a Grainger page and asks to extract item/part numbers and quantities. Trigger phrases include "Grainger screenshot", "pull items from this screenshot", "extract from this Grainger image", "get the part numbers from this screenshot", or any time a Grainger table or cart is shared as an image rather than a PDF or text. Always output results in the [Part Number or Grainger Item #],[QTY] format — never a table or prose description.
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
