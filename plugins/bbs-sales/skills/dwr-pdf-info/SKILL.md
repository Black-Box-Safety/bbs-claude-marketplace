---
name: dwr-pdf-info
description: >
  Extracts item and quantity information from California Department of Water
  Resources (DWR) Request for Quotation PDFs — both text-selectable and
  scanned/image-based. Use this skill whenever Aanya uploads a DWR RFQ PDF
  and specifies a mode: "Grainger", "Sourcing", or "Mixed". Trigger phrases
  include: "DWR PDF Info — Grainger", "DWR PDF Info — Sourcing", "DWR PDF
  Info — Mixed", or any request to pull items/quantities from a DWR RFQ PDF.
  Always identify the mode from Aanya's message before producing output.
  Never guess the mode — if not specified, ask.
---

# DWR PDF Info

Extracts line item data from DWR Request for Quotation PDFs and returns it in
one of three formats depending on the mode Aanya specifies.

---

## Trigger Format

Aanya will upload a DWR RFQ PDF and include one of:
- `DWR PDF Info — Grainger`
- `DWR PDF Info — Sourcing`
- `DWR PDF Info — Mixed`

---

## PDF Structure

DWR RFQs are 2-column table PDFs (sometimes scanned/image-based). Each line
item has:

| Field | Location | Notes |
|-------|----------|-------|
| **DWR Line #** | `Item #` column | 4-digit zero-padded, e.g. `0001`, `0008` |
| **Material/Description** | `Material / Description` column | Main description in normal text |
| **Item identifier** | Italic sub-line below description | Either `GRAINGER ITEM # XXXXX` or vendor/sourced info (see below) |
| **Quantity** | `Quantity` column | Integer |
| **Unit** | `Unit` column | e.g. `each`, `Pack` |

### Identifying Grainger vs. Sourced lines

- **Grainger:** Italic sub-line contains `GRAINGER ITEM #` → extract the
  alphanumeric code that follows (e.g. `GRAINGER ITEM # 5WL36` → `5WL36`)
- **Sourced:** Italic sub-line contains anything else — vendor name, website
  URL, SKU, model number, etc. Examples:
  - `SNAP-ON.com Item: K4LA` → SKU is `K4LA`
  - `uline.com Item# S-827` → SKU is `S-827`
  - `LOWES Item #137836 | Model #124011` → SKU is `137836` (use first/primary #)
  - `goodway.com / RAM-4 Service Kit # RAM4-SVC-KIT` → SKU is `RAM4-SVC-KIT`
  - `Vendor Blast One / SKU APBEDP10` → SKU is `APBEDP10`
- **Amazon items:** When the vendor is Amazon, always prefer the **ASIN** as the
  item # over any other identifier (UPC, Item #, Model #). ASIN format is always
  10 characters starting with `B0` (e.g. `B00063XSQY`, `B0DDCPFHZH`).
- **No clear SKU:** If the italic sub-line is only a URL, a brand name with no
  SKU, or too vague to identify a specific item # (e.g. `filterking.com` with
  no part number) → use the DWR line number as fallback in the Item # column
  and append a flag: `⚠️ [DWR LINE 0006] — No obvious item # found, please verify`

### Page overflow handling

DWR RFQs are 2 pages. Occasionally a line item's description and Grainger # 
appear at the bottom of page 1 with no QTY, and the QTY appears on page 2
(or vice versa). Always cross-reference by DWR line number (e.g. `0007`) to
reunite split data across pages. Never leave a matched line number's data
incomplete.

---

## Mode 1: Grainger

**Use when:** All items on the RFQ are Grainger items.

**Output:** Plain code block, one entry per line, in `ITEM#,QTY` format.
Same format as the `grainger-cart-info` skill.

```
54GD34,1
3LX95,10
3LX96,10
```

Follow with: `X Grainger items extracted from [filename].`

---

## Mode 2: Sourcing

**Use when:** All items on the RFQ are sourced (no Grainger items).

**Output:** A readable chat table with these columns only:

| Item # | Material / Description | Quantity | Unit |
|--------|----------------------|----------|------|

- **Item #** = Vendor SKU / Model # extracted from the italic sub-line
- If no clear SKU: use DWR line number as fallback + flag below table
- Do NOT include: Recycled Content %, Unit Price, Extension
- Table must be copy-pasteable from chat

Follow with any flags on separate lines below the table.

---

## Mode 3: Mixed

**Use when:** RFQ contains both Grainger and sourced items.

**Output:** Same table as Sourcing mode, with one additional column on the right:

| Item # | Material / Description | Quantity | Unit | ProCo Input |
|--------|----------------------|----------|------|-------------|

- **Item #** = Vendor SKU / Model # (same logic as Sourcing)
- **ProCo Input column:**
  - If confirmed Grainger line → `ITEM#,QTY` (e.g. `5WL36,4`)
  - If sourced line → leave blank
  - If **Assumed Grainger** (see below) → `ITEM#,QTY` with a `*` suffix (e.g. `5A293,4*`)
  - If flagged (no clear SKU) → leave ProCo Input blank, flag below table

Follow with any flags on separate lines below the table.

### Assumed Grainger Detection (Mixed mode only)

After the first pass, run a second pass on all sourced lines. Flag a line as
**Assumed Grainger** only if ALL four conditions are met:

1. The sub-line does **not** say `GRAINGER ITEM #`
2. The sub-line has **no recognizable manufacturer or vendor name**
   (e.g. no Snap-On, Amazon, HP, Uline, Lowes, Goodway, Bullard, Grainger,
   or any other brand/retailer). Manufacturer context takes priority over
   pattern matching — if a vendor name is present, it is NOT assumed Grainger
   regardless of part number format.
3. The extracted item # matches the **Grainger alphanumeric pattern**:
   - 5 to 7 characters long (never 4 or fewer)
   - Starts with a number
   - Mix of letters and numbers (e.g. `5A293`, `53XV70`, `1AV23`, `54YR33`)
4. The item # does **not** match a known non-Grainger format:
   - Pure numeric strings (UPCs, model numbers like `46094`, `259574`)
   - Amazon ASINs (`B0XXXXXXXX`)
   - Snap-On style short codes (`F111`, `FZ2` — too short, often letters-first)

**Assumed Grainger items:** populate ProCo Input as `ITEM#,QTY*` and add a
flag below the table:
```
🔍 [DWR LINE 0010] — Item # 5A293 assumed Grainger based on format. No vendor
name found in sub-line. Please verify before submitting.
```

---

## Flags

Flags are always listed below the output (table or code block), never inline.

**No SKU found:**
```
⚠️ [DWR LINE 0006] — No obvious item # found. Sub-line read: "filterking.com". Please verify and update manually.
```

**Assumed Grainger (Mixed mode only):**
```
🔍 [DWR LINE 0010] — Item # 5A293 assumed Grainger based on format. No vendor name found in sub-line. Please verify before submitting.
```

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| PDF is scanned/image-based | Read visually page by page; apply same logic. Note at top of output: `📄 Source: image-based PDF — extracted by visual read.` |
| Line item split across pages | Cross-reference by DWR line number to reunite # and QTY |
| Grainger # present but no QTY found anywhere | Output item with `QTY:?` and flag it |
| Mode not specified by Aanya | Ask before proceeding — never guess |
| Multiple SKUs on one sourced line (e.g. Lowes Item # + Model #) | Use the first/primary item # listed |
| Duplicate line items (same item # and description appearing more than once) | Always keep as separate rows — never collapse. DWR customers intentionally duplicate lines for departmental record keeping. Do note duplicates informally at the end of the output (after any flags) as a simple FYI, e.g. "📋 Note: Lines 0001 and 0002 appear to be duplicates (same item, likely split by department)." — never as a warning or error. |
