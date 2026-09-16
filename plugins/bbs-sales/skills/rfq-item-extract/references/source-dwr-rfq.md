# Source: DWR Request for Quotation PDF

California Department of Water Resources RFQs, text-selectable or scanned.

## Structure

Two-column table PDFs, usually 2 pages. Each line item has:

| Field | Where | Notes |
|---|---|---|
| DWR line # | `Item #` column | 4-digit zero-padded, e.g. `0001`, `0008` |
| Material / description | `Material / Description` column | normal text |
| Item identifier | italic sub-line below the description | either `GRAINGER ITEM #` or vendor/sourced info |
| Quantity | `Quantity` column | integer |
| Unit | `Unit` column | `each`, `Pack`, … |

## Grainger vs sourced

- **Grainger** — the italic sub-line contains `GRAINGER ITEM #`; take the alphanumeric
  code after it (`GRAINGER ITEM # 5WL36` → `5WL36`).
- **Sourced** — anything else: a vendor name, URL, SKU or model number.
  - `SNAP-ON.com Item: K4LA` → `K4LA`
  - `uline.com Item# S-827` → `S-827`
  - `LOWES Item #137836 | Model #124011` → `137836` (first/primary number)
  - `goodway.com / RAM-4 Service Kit # RAM4-SVC-KIT` → `RAM4-SVC-KIT`
  - `Vendor Blast One / SKU APBEDP10` → `APBEDP10`
- **Amazon** — always prefer the **ASIN** over any UPC, item # or model #. ASINs are 10
  characters starting `B0` (`B00063XSQY`, `B0DDCPFHZH`).
- **No clear SKU** — the sub-line is only a URL or a brand with no part number (e.g.
  `filterking.com`). Use the DWR line number in the Item # column and flag it:
  `⚠️ [DWR LINE 0006] — No obvious item # found, please verify`

## Page overflow

A line's description and Grainger # sometimes sit at the bottom of page 1 with the
quantity on page 2, or the reverse. **Cross-reference by DWR line number** (`0007`) to
reunite split rows. Never leave a matched line number incomplete.

## The three modes

The rep names the mode. Never guess it — ask if it is not given.

### Grainger — every item is a Grainger item

A plain code block, `ITEM#,QTY`, one per line, then `X Grainger items extracted from
[filename].`

```
54GD34,1
3LX95,10
3LX96,10
```

### Sourcing — no Grainger items

A copy-pasteable table, these columns only:

| Item # | Material / Description | Quantity | Unit |
|---|---|---|---|

Item # is the vendor SKU or model from the italic sub-line, or the DWR line number plus a
flag below the table. Do **not** add Recycled Content %, Unit Price or Extension columns.

### Mixed — both

The Sourcing table plus one column on the right:

| Item # | Material / Description | Quantity | Unit | ProCo Input |
|---|---|---|---|---|

ProCo Input holds `ITEM#,QTY` for a confirmed Grainger line, `ITEM#,QTY*` for an assumed
Grainger line, and stays blank for a sourced or flagged line.

## Duplicate lines — never collapse them

A DWR RFQ routinely lists the same item # and description on more than one line. That is
**intentional**: the customer is splitting one order across departments for their own
record keeping. Always keep them as separate rows, in every mode.

Collapsing them is the expensive failure on this path. Two departments each ordering 10
become a single line of 10, the bid is short by half, and nothing anywhere reports an
error — the cross-source de-duplication rule in `SKILL.md` explicitly does not apply here.

Note the repeat after any flags, as an FYI and never as a warning or an error:

```
📋 Note: Lines 0001 and 0002 appear to be duplicates (same item, likely split by
department).
```

## Assumed Grainger detection — Mixed mode only

After the first pass, re-read the sourced lines. Mark one **Assumed Grainger** only if
**all four** hold:

1. The sub-line does **not** say `GRAINGER ITEM #`.
2. It carries **no recognizable vendor or manufacturer name** — no Snap-On, Amazon, HP,
   Uline, Lowes, Goodway, Bullard, or any other brand or retailer. Vendor context beats
   pattern matching: if a vendor name is present it is **not** assumed Grainger, whatever
   the number looks like.
3. The item # matches the Grainger shape: 5–7 characters (never 4 or fewer), starts with a
   digit, mixes letters and numbers — `5A293`, `53XV70`, `1AV23`, `54YR33`.
4. It does **not** match a known non-Grainger shape: pure numerics (UPCs, model numbers
   like `46094`, `259574`), Amazon ASINs (`B0XXXXXXXX`), or short letters-first Snap-On
   codes (`F111`, `FZ2`).

Put `ITEM#,QTY*` in ProCo Input and flag it below the table:

```
🔍 [DWR LINE 0010] — Item # 5A293 assumed Grainger based on format. No vendor
name found in sub-line. Please verify before submitting.
```

The asterisk and the flag are the point: an assumed match is a guess, and it is labelled
as one so a human confirms it before it reaches a bid.
