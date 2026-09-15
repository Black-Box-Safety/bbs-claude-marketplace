---
name: grainger-cart-info
description: >-
  Extract Grainger item numbers and quantities from a saved or printed Grainger shopping-cart
  PDF and return them as ITEM#,QTY lines ready to paste into the BBS Grainger purchasing
  portal. Use when a customer or rep supplies a cart exported from grainger.com as a PDF and
  wants the line items pulled out. Always output the concatenated ITEM#,QTY format, never a
  table or prose. Do NOT use for a Grainger cart shared as a screenshot or image (use
  grainger-screenshot), a DWR Request for Quotation PDF (use dwr-pdf-info), any other agency
  RFQ or worksheet PDF, checking whether items are on the DGS BPO (use dgs-bpo-item-check), or
  pricing items (use bbs-b2b-pricing). This skill reads Grainger cart PDFs only. If the PDF is
  not a Grainger cart, say so rather than extracting from it anyway.
---

# Grainger Cart Info

Extracts Grainger Item Numbers and Quantities from a customer's Grainger cart
PDF. Output format: `ITEM#,QTY` — one entry per line, ready to paste into the
BBS Grainger purchasing portal.

---

## Input

A Grainger cart PDF saved/printed from grainger.com/cart. The PDF will be
uploaded by the rep and available in context (Claude can read the text directly —
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
| PDF is image-only / scanned (no selectable text) | Claude can still read scanned PDFs visually (like reading a photo), but automated regex parsing won't work. In this case, Claude will extract Item Numbers and QTYs by visual inspection and return them in the same `ITEM#,QTY` format. For very large carts this is slower and slightly less reliable — if accuracy is critical, ask the rep to provide a text-selectable PDF when possible. Always note at the top of the output if the source was image-based. |
| "Recently Viewed" items bleed into results | De-duplication handles this — first occurrence wins |
| QTY is missing or ambiguous | Flag that specific item with a note: `[ITEM#] — QTY unclear, please verify` |
| Multi-page cart | Pattern works across all pages; no special handling needed |
| Customer uploaded wrong file | If no `Item #` pattern is found, inform the rep the file doesn't appear to be a Grainger cart PDF |
