---
name: price-list-cleaner
description: Clean and convert manufacturer price lists into the BBS (Black Box Safety) standard import template. Use this skill whenever the user provides a raw manufacturer price list file (Excel, CSV, or PDF) and needs it prepared for import into the BBS product database. Also trigger when the user mentions cleaning, prepping, formatting, or converting a price list, price sheet, or product catalog for Black Box Safety, BBS, or import. This includes any file from a manufacturer containing SKUs, product descriptions, and pricing columns that needs to be standardized.
requires: [python3, pymupdf]
---
> **BBS Website pipeline — stage: Intake.** See `site-wiring-map` for how this fits the whole flow.

# BBS Price List Cleaner

You are cleaning a raw manufacturer price list into the BBS standard import template format. Every manufacturer sends pricing data in a different format — some are clean flat CSVs, some are complex multi-sheet Excel workbooks with merged cells, some are PDFs with table layouts that need OCR-style extraction. Your job is to understand the source format, map it correctly, and produce a clean CSV ready for the BBS ETL import pipeline.

## The BBS Template

The output CSV must have exactly these columns in this order:

```
manufacturer_sku,name,description,category,subcategory,upc,nsn,msrp,map_price,cost,unit_of_measure,country_of_origin,image_url,notes
```

### Column Rules

| Column | Required | Notes |
|---|---|---|
| `manufacturer_sku` | Yes | The manufacturer's part number/SKU. Must be unique per row. |
| `name` | Yes | Product name with ALL differentiating info (see naming rules below). |
| `description` | No | Additional detail if available. Often left blank if name is descriptive enough. |
| `category` | Yes | Must be one of the valid categories listed below. |
| `subcategory` | No | **Always leave blank.** Subcategory taxonomy is TBD. |
| `upc` | No | Clean numeric string — no spaces, no scientific notation, no dashes. |
| `nsn` | No | National Stock Number if available. Usually blank. |
| `msrp` | Yes | Manufacturer's suggested retail price. Must be numeric > 0. |
| `map_price` | No | Minimum advertised price. Include when available, blank when not. |
| `cost` | Yes | BBS distributor cost. Column name varies wildly by manufacturer. |
| `unit_of_measure` | Yes | Default to `EA`. Only change if source specifies otherwise. |
| `country_of_origin` | No | 2-letter country code or full name if available. |
| `image_url` | No | Product image URL if available. Usually blank. |
| `notes` | No | Anything useful that doesn't fit elsewhere (e.g., article numbers). |

### Valid Categories

```
Communications, Duty Gear, Less Lethal, Other, Tactical Equipment,
Traffic Safety, Training Equipment, Weapons and Ammunitions
```

Category assignment depends on understanding what the manufacturer makes. Common mappings:
- **Tactical Equipment**: body armor, plate carriers, helmets, shields, breaching tools, tactical harnesses, pouches/load bearing
- **Duty Gear**: flashlights, apparel/uniforms, holsters, belts, handcuffs/restraints, bags
- **Less Lethal**: OC spray, batons, conducted energy devices
- **Communications**: acoustic hailing devices, speakers, communication equipment
- **Weapons and Ammunitions**: optics/sights, suppressors, firearm components
- **Training Equipment**: inert training units, red guns, training doors, safety kits
- **Traffic Safety**: traffic wands, safety lights

When a manufacturer spans multiple categories (e.g., ASP makes batons AND handcuffs AND lights), assign each product to the correct category — don't default everything to one.

## The Workflow

Follow these steps in order. The key principle: **examine before you act**. Every manufacturer is different, so never assume the structure.

### Step 1: Examine the Source File

Read the file and understand its structure before writing any transformation code.

**For Excel/CSV files:**
- List all sheet names
- Show columns, shape, and first 10-20 rows of each relevant sheet
- Identify which sheet(s) contain the actual product data
- Check for header rows that aren't on row 0 (common — often 1-5 rows of title/notes before headers)
- Look for section headers mixed into data rows (e.g., "BATONS" as a row with no SKU)
- Check for a "discontinued" or "obsolete" sheet/column to exclude

**For PDF files:**
- Check total page count
- Extract and display text from first 3-5 pages to understand the table layout
- Identify column structure: what are the headers? Do they shift between pages?
- Check for side-by-side tables (common in body armor catalogs)
- Check for section headers embedded in the data flow
- Use `fitz` (PyMuPDF) for text extraction. Try block-based extraction (`page.get_text("blocks")`) first — it preserves table structure better than plain text.

**Present findings to the user** before proceeding: "Here's what I see — X products, columns are Y, cost appears to be in the Z column. Does this look right?"

### Step 2: Identify Column Mappings

Map the source columns to BBS template columns. The tricky one is always **cost** — it goes by many names:

| Source Column Name | What It Usually Is |
|---|---|
| Distributor, Distributor Price, Distributor 35% | Cost |
| Dealer, Dealer Price, Dealer 1-29 | Cost |
| Wholesale Price, Reseller Price, Quantity Buyer | Cost |
| "50+15" or "50+10" (Point Blank/Paraclete) | Cost (50% + 15% off retail) |
| Percentage discount off MSRP | Calculate: `MSRP * (1 - discount%)` |
| Retail, MSRP, List Price | MSRP (not cost!) |
| MAP, MAP 20% | MAP price |

If uncertain which column is cost, ask the user. Getting this wrong is the worst possible mistake.

### Step 3: Handle Product Variants

Different manufacturers handle variants differently:

**Apparel/gear with size + color variants** (e.g., Massif, First Tactical, Tru Spec):
- Each SKU/UPC combination gets its own row
- Name format: `{Style Name}, {Color}, {Size}`
- The source often has the first row with full details and subsequent rows with only the varying fields — forward-fill the shared fields (name, MSRP, cost)

**Body armor with ballistic package ratings** (e.g., Point Blank, Paraclete):
- Each carrier + package combo is its own product
- Name format: `{Carrier/Section Name}, {Package Rating}`
- Example: "Elite Gen V - One Carrier, EXKII"

**Products with color but no size** (e.g., S&S Precision, SureFire):
- Color is usually embedded in the SKU and description already
- Use the description as-is

### Step 4: Clean and Transform

Write a Python script using pandas to:

1. **Read the source** with the correct sheet, header row, and encoding
2. **Filter out non-product rows**: section headers, blank rows, totals, notes
3. **Filter out discontinued/obsolete items** if flagged in the source
4. **Map columns** to the BBS template
5. **Clean prices**: remove `$`, commas; convert to float; round to 2 decimals
6. **Clean UPCs**: remove spaces; handle scientific notation (`int(float(upc))`); remove dashes
7. **Deduplicate** by manufacturer_sku (keep first occurrence)
8. **Remove items with no MSRP or MSRP = 0**
9. **Assign categories** based on product type
10. **Leave subcategory blank**
11. **Output as CSV** to `templates/2026-{manufacturer-slug}.csv`

### Step 5: Validate and Report

After building the output, print a summary:
- Total product count
- MSRP range
- Count of products with UPC, MAP, cost
- Products by category (if multiple)
- Any products that were skipped and why
- Sample of 10-15 products showing SKU, name, MSRP, cost

## Naming Rules

Product names are critical — they're how humans identify products in the catalog. Rules:

1. **Include all differentiating information**: model, variant, size, color, rating, configuration
2. **Do NOT include the manufacturer name** in the product name. The manufacturer is identified separately at import time via the `--manufacturer` flag.
3. **Incorporate important spec details** from descriptions when the base name is too generic. For example, SABRE spray names should include the formula level and OC concentration.
4. **For abbreviated/truncated names**, expand them using the full description or long description column if available.
5. **Title case is preferred** for readability, but preserve acronyms and model numbers in their original case (e.g., "EXKIIIA", "MK-9", "TLR-1 HL").

## PDF-Specific Patterns

PDFs are the hardest format. Common patterns from body armor catalogs (Point Blank, Paraclete):

- **Side-by-side tables**: Split blocks into columns by x-position before parsing
- **Section headers in separate blocks**: Use a two-pass approach — first identify section name blocks, then match them to nearby data blocks
- **Combined blocks** (section + STYLE CODE + data in one block): Parse the section name from lines before "STYLE CODE"
- **Shifting column positions**: Some manufacturers change column layout between sections (e.g., S&S Precision uses different columns for different product lines)
- **Multiple table header formats**: "STYLE CODE", "PLATE #", "STYLE #", "Style Code" — handle all of them
- **Price format variations**: `$1,234.00` on separate lines, `$ 1,234.00` with spaces, just `1234` as a number

## Common Pitfalls

- **Don't confuse MSRP with cost.** Double-check that the higher number is MSRP and the lower is cost. If cost > MSRP, something is wrong.
- **Watch for merged cells in Excel.** They create NaN values in pandas that need forward-filling.
- **PDF text extraction interleaves columns.** Sort blocks by position and process columns independently.
- **Scientific notation UPCs.** `8.46357e+11` must become `846357100001`. Always cast through `int(float(x))`.
- **Section headers that look like data.** "BATONS" or "HELMETS" as a row will pass through if you only filter on null prices — also check that the SKU column has a valid product identifier.
- **Percentage-based pricing.** Some manufacturers give "35% off retail" instead of an explicit cost column. Calculate: `cost = msrp * (1 - 0.35)`.
