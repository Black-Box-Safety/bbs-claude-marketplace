---
name: grainger-cart-info
description: >
  Extracts Grainger Item Numbers and Quantities from a customer's saved Grainger
  cart PDF and returns them in "ITEM#,QTY" format ready to paste into the BBS
  Grainger purchasing portal. Use this skill whenever a customer sends a Grainger
  cart PDF instead of a standard item list, or when Aanya asks to "pull items
  from a Grainger cart", "extract Grainger item numbers from a PDF", "get the
  item numbers and quantities from this cart", or any similar request involving
  a Grainger cart printout or saved PDF. Always output results in the
  ITEM#,QTY concatenated format — never a table or prose list.
  Note: This skill handles Grainger cart PDFs only. For other PDF formats or
  non-Grainger sources, separate skills will be built and may reference this one.
---

# Grainger Cart Info

Extracts Grainger Item Numbers and Quantities from a customer's Grainger cart
PDF. Output format: `ITEM#,QTY` — one entry per line, ready to paste into the
BBS Grainger purchasing portal.

---

## Input

A Grainger cart PDF saved/printed from grainger.com/cart. The PDF will be
uploaded by Aanya and available in context (Claude can read the text directly —
no file tool needed unless the PDF is image-only/scanned).

---

## How the Grainger Cart PDF is Structured

Each line item in the cart follows this consistent pattern in the extracted text:

```
Item # [ITEM_NUMBER]
[QTY]
Qty
Web Price $X.XX / each
```

The quantity appears as a standalone integer on the line immediately before the
word `Qty`. Item numbers follow `Item #` and are alphanumeric (e.g. `60KA44`,
`38W367`, `1VXP2`).

**Important:** The last page of the PDF contains a "Products You Have Recently
Viewed" section which may repeat item numbers with qty "1" and "Add to Cart"
buttons. These are NOT cart items — stop parsing before this section.

---

## Parsing Logic

Use this regex against the full PDF text:

```python
import re

pattern = re.compile(r'Item\s+#\s+(\S+)\s+(\d+)\s+Qty', re.MULTILINE)
matches = pattern.findall(pdf_text)
```

Each match returns `(item_number, qty)`.

**De-duplicate:** If the same item number appears more than once (can happen if
the "Recently Viewed" section bleeds through), keep only the first occurrence.

```python
seen = set()
results = []
for item, qty in matches:
    if item not in seen:
        seen.add(item)
        results.append((item, qty))
```

---

## Output Format

Return results as a plain code block, one entry per line:

```
ITEM#,QTY
```

Example:
```
60KA44,1
54DD03,1
2GKZ6,2
29RV11,12
38W367,40
```

Then follow with a brief summary line:
`X items extracted from [PDF filename].`

No table, no headers, no extra formatting — just the code block and the count.
The user will copy and paste this directly into the Grainger portal.

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| PDF is image-only / scanned (no selectable text) | Claude can still read scanned PDFs visually (like reading a photo), but automated regex parsing won't work. In this case, Claude will extract Item Numbers and QTYs by visual inspection and return them in the same `ITEM#,QTY` format. For very large carts this is slower and slightly less reliable — if accuracy is critical, ask Aanya to provide a text-selectable PDF when possible. Always note at the top of the output if the source was image-based. |
| "Recently Viewed" items bleed into results | De-duplication handles this — first occurrence wins |
| QTY is missing or ambiguous | Flag that specific item with a note: `[ITEM#] — QTY unclear, please verify` |
| Multi-page cart | Pattern works across all pages; no special handling needed |
| Customer uploaded wrong file | If no `Item #` pattern is found, inform Aanya the file doesn't appear to be a Grainger cart PDF |
