# Sources: Grainger cart PDF and Grainger screenshot

Two ways the same cart arrives. Both produce `ITEM#,QTY` lines.

## Cart PDF — saved or printed from grainger.com/cart

Each line item follows a consistent pattern in the extracted text:

```
Item # [ITEM_NUMBER]
[QTY]
Qty
Web Price $X.XX / each
```

The quantity is the standalone integer on the line immediately before `Qty`. Item numbers
follow `Item #` and are alphanumeric (`60KA44`, `38W367`, `1VXP2`).

```python
import re
pattern = re.compile(r'Item\s+#\s+(\S+)\s+(\d+)\s+Qty', re.MULTILINE)
matches = pattern.findall(pdf_text)

seen, results = set(), []
for item, qty in matches:
    if item not in seen:          # "Recently Viewed" can bleed in; first wins
        seen.add(item)
        results.append((item, qty))
```

### Edge cases

| Situation | Handling |
|---|---|
| Image-only / scanned PDF | Read it visually and extract to the same `ITEM#,QTY` format — regex will not work. Slower and slightly less reliable on large carts; ask for a text-selectable PDF when accuracy matters. **Always note at the top of the output that the source was image-based.** |
| "Recently Viewed" bleeds in | De-duplication handles it — first occurrence wins |
| Quantity missing or ambiguous | Flag that item: `[ITEM#] — QTY unclear, please verify` |
| Multi-page cart | The pattern spans pages; no special handling |
| Not actually a Grainger cart | No `Item #` pattern found → say so. Do not extract from it anyway |

## Screenshot — a cart, order or item table shared as an image

Read the image and find the columns.

**Part number column**, in order of preference:

1. **Grainger Item #** — use it if present (short alphanumeric, e.g. `6YPH8`)
2. **Mfr. Model #** or **Manufacturer Part #** — only if there is no Grainger Item #
3. any similar identifier column

**Quantity column** is usually labelled `Qty`, `Quantity` or `QTY`.

### Edge cases

| Situation | Handling |
|---|---|
| Both Grainger Item # and Mfr Part # present | Use the Grainger Item # |
| Multiple pages visible | Extract everything visible |
| Quantity blank or unclear | Default to `1` and note the assumption after the list |
| Row struck through or marked removed | Skip it |
| Header or subtotal rows | Skip them — line items only |

After the list, note any assumption you made in one line.
