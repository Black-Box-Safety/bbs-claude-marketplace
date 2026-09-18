---
name: bbs-pricelist-import
description: "Import a manufacturer price list into the BBS product database (Supabase). Use this skill whenever a BBS rep needs to add a new manufacturer catalog or update pricing for an existing one. Trigger phrases include 'import this price list,' 'load this manufacturer's pricing,' 'add [manufacturer] to the database,' 'update [manufacturer] pricing,' 'run the import for [manufacturer],' or any time a price list file (Excel, CSV, or PDF) needs to be standardized and committed to the bbs-product-database. Also trigger when a rep uploads a raw vendor file and asks what to do next. This skill covers the full pipeline: clean the raw file → validate → preview the diff → commit → detect families → queue image scrape. Do NOT use for NASPO/Grainger punch-out pricing or for BBS quoting workflows — this is catalog management only."
requires: [supabase, python3, pandas, openpyxl]
degrades-without: [firecrawl]
---

# BBS Price List Import

This skill covers the full pipeline for getting a manufacturer's products and pricing into the BBS product database — from a raw vendor file all the way to committed catalog records with families detected and Shopify queued.

**Supabase project:** `oaqkueputgaweojcpaim`
**Repo:** `bbs-database` — wherever it is cloned on this machine. Every command
below runs from that clone's root; `$BBS_DATABASE` stands for it. Ask the rep for
the path once if it isn't obvious from the working directory.
**Python venv:** `./venv/bin/python` (has `supabase`, `pandas`, `openpyxl`, `python-dotenv` installed)

---

## Overview: the 5-stage pipeline

```
Raw vendor file (xlsx/csv/pdf)
       ↓
Stage 1: Clean → BBS template CSV
       ↓
Stage 2: Validate + preview diff
       ↓
Stage 3: Commit to Supabase
       ↓
Stage 4: Detect product families
       ↓
Stage 5: Scrape images/descriptions (if needed)
```

Each stage gates the next. Never skip validation before commit. Never commit without showing the diff first.

---

## Stage 1 — Clean the raw file

Use the `price-list-cleaner` skill, which ships in this same plugin, to convert the raw vendor file into the BBS standard template CSV. The cleaner skill handles all input formats (Excel, CSV, PDF), column mapping, cost column identification, UPC cleaning, variant forward-filling, and category assignment.

**The output must be:** a CSV at `templates/imports/ready/2026-{manufacturer-slug}.csv` with exactly these 14 columns in order:

```
manufacturer_sku, name, description, category, subcategory, upc, nsn,
msrp, map_price, cost, unit_of_measure, country_of_origin, image_url, notes
```

**Before passing to Stage 2, verify:**
- `subcategory` column is blank on every row (subcategory classification runs separately via Session A workflow)
- No rows where `cost > msrp` (column swap — catch this in the cleaner)
- No duplicate `manufacturer_sku` values
- All `category` values are in the valid set (see Valid Categories below)
- `unit_of_measure` defaults to `EA` where blank

### Valid categories
```
Body Armor, Breaching and Rescue, Cases and Bags, Communications,
Duty Gear, Hazmat/CBRN, Illumination, Less Lethal, Medical,
Tactical Equipment, Traffic Safety, Training Equipment,
Uniforms and Apparel, Other
```

> **Note:** The original 8-category taxonomy (`Tactical Equipment`, `Duty Gear`, `Less Lethal`, `Communications`, `Traffic Safety`, `Training Equipment`, `Weapons and Ammunitions`, `Other`) is still in `etl/categories.txt`. The database has been expanded to 13 root categories as of 2026-04-08. When assigning categories, use the current 13-category set above. If a product doesn't fit cleanly, assign `Other` and note it — the Session A classifier will clean up later.

---

## Stage 2 — Validate and preview the diff

Run the import script in **preview mode** (no `--commit` flag):

```bash
cd "$BBS_DATABASE"
source venv/bin/activate

python etl/import.py \
  --manufacturer {slug} \
  --file templates/imports/ready/2026-{slug}.csv
```

This stages rows to `import_staging`, validates each row, and prints:
1. **Exception report** — rows with validation errors (unknown category, missing required field, cost=0 in non-bootstrap mode, invalid UOM)
2. **Diff report** — counts of new / price_change / unchanged / discontinued products against existing DB records

**Review before proceeding:**

| Report item | Action |
|---|---|
| Unknown category | Fix in the CSV — only pre-defined categories accepted; no auto-creation |
| Missing SKU or name | Fix in the CSV |
| `cost = 0` errors | If intentional (initial load, cost TBD), add `--bootstrap` flag. Otherwise fix. |
| `cost > msrp` rows | These are data errors — fix the CSV |
| Large discontinued count | Confirm with Parker before committing — may indicate a column mapping error |
| New product count looks wrong | Sanity-check against the source file row count |

**If the exception report shows > 5% error rate:** stop, fix the CSV, re-run the preview. Don't commit with a high error rate.

### Bootstrap mode

For **new manufacturers where BBS doesn't yet have distributor cost** (e.g., initial load from the NPPGov catalog, or manufacturer shared MSRP-only pricing), add the `--bootstrap` flag:

```bash
python etl/import.py \
  --manufacturer {slug} \
  --file templates/imports/ready/2026-{slug}.csv \
  --bootstrap
```

Bootstrap mode allows `cost = 0` and creates `product_prices` rows with `pricing_status = 'incomplete'`. These are flagged for cost backfill when the actual distributor price list arrives. Do not use bootstrap mode if you have real cost data — `pricing_status = 'incomplete'` means the product won't produce valid quotes.

---

## Stage 3 — Commit

After confirming the diff looks correct, add `--commit`:

```bash
python etl/import.py \
  --manufacturer {slug} \
  --file templates/imports/ready/2026-{slug}.csv \
  --commit
```

(Add `--bootstrap` if applicable.)

**What commit does:**
- Inserts new products into `products` + `product_prices`
- Updates price records for changed products (marks old price `is_current = false`, inserts new)
- Marks discontinued products `is_active = false`
- Creates `price_list_import_logs` rows (new/price_change/unchanged/discontinued)
- Creates `bc_sync_queue` entries (create/update) for every changed product
- Supersedes the prior active import for this manufacturer
- Sets the new import to `status = active`

**After commit, verify row counts in Supabase:**

```sql
-- Product count for this manufacturer
SELECT COUNT(*) FROM products p
JOIN manufacturers m ON m.id = p.manufacturer_id
WHERE m.slug = '{slug}' AND p.is_active = true;

-- Confirm all have current pricing
SELECT COUNT(*) FROM products p
JOIN manufacturers m ON m.id = p.manufacturer_id
JOIN product_prices pp ON pp.product_id = p.id AND pp.is_current = true
WHERE m.slug = '{slug}' AND p.is_active = true;

-- Check bc_sync_queue got populated
SELECT action, status, COUNT(*) FROM bc_sync_queue bsq
JOIN products p ON p.id = bsq.product_id
JOIN manufacturers m ON m.id = p.manufacturer_id
WHERE m.slug = '{slug}'
GROUP BY action, status;
```

Move the CSV to `templates/imports/imported/` after a successful commit.

---

## Stage 4 — Detect product families

Product families group size/color/fit variants of the same base product under one card. Run after every new manufacturer import:

```bash
python etl/detect_families.py --manufacturer {slug}
```

Review the report: it shows detected families, variant counts, dimension types (color/size/fit), base SKUs, and standalone products. The preview runs without writing anything.

If the groupings look correct:

```bash
python etl/detect_families.py --manufacturer {slug} --commit
```

**What this writes:**
- Inserts rows into `product_families` (family_name, family_slug, base_sku, variant_dimensions)
- Updates `products.family_id` and `products.variant_attributes` for each member

**When family detection matters most:** apparel manufacturers (First Tactical, Massif, Tru Spec, Tru-Spec, DriFire) where a single style may have 50+ size/color variants. For single-SKU manufacturers (Holmatro, Hyperspike) this step will produce few or no families — that's normal.

**Red flags to watch for:**
- Families with only 1 member (miscategorized — should be standalone)
- Very large families (>100 variants) — may indicate over-broad name stripping
- Families that span obviously different products — inspect and correct manually if needed

---

## Stage 5 — Image and description scraping

After products are in the database, they need images and descriptions for the Shopify storefront and BC sync.

### Check current coverage first

```sql
SELECT 
  COUNT(*) AS total_active,
  SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) AS has_image,
  SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) AS has_description,
  ROUND(100.0 * SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS image_pct
FROM products p
JOIN manufacturers m ON m.id = p.manufacturer_id
WHERE m.slug = '{slug}' AND p.is_active = true;
```

### Scraping path by manufacturer type

**Shopify storefronts** (most tactical brands): use the `shopify` strategy in `etl/scrape_images.py`. Add an entry to `MANUFACTURERS` in that file:
```python
{"slug": "{slug}", "domain": "{shopify-domain}", "strategy": "shopify", "threshold": 0.4},
```
Then run:
```bash
MFG_FILTER={slug} ./venv/bin/python etl/scrape_images.py
```

**WooCommerce/WordPress sites**: use the `sitemap` or `firecrawl` strategy. Check whether the manufacturer has a product sitemap at `/product-sitemap.xml` first.

**Manufacturers with local asset bundles** (e.g., image zip from the manufacturer): create a dedicated import script following the pattern in `etl/import_damascus.py` or `etl/import_avon_marketing.py`.

**If images aren't available via scraping**: add the `image_url` column to the CSV template before the initial import (Stage 1). Many manufacturer price lists include image URLs — prefer that path when available.

### Manufacturer enrichment (brand descriptions, logos)

For new manufacturers, also run the enrichment script to populate `manufacturers.description`, `manufacturers.tagline`, and `manufacturers.logo_url`:

```bash
./venv/bin/python etl/enrich_manufacturer_descriptions.py --only "{Manufacturer Name}"
```

This uses Firecrawl + Claude to scrape the manufacturer's website and generate a 2-3 sentence brand overview. Results are written to `assets/manufacturer_logos/manufacturer_descriptions.json` and committed to Supabase.

---

## Adding a brand-new manufacturer

If the manufacturer slug doesn't exist in the `manufacturers` table yet, add it before running the import:

```sql
INSERT INTO manufacturers (name, slug, mfg_code, bc_vendor_no, website)
VALUES (
  '{Full Manufacturer Name}',
  '{slug}',           -- e.g. 'point-blank'
  '{CODE}',           -- 2-5 char code, e.g. 'PB' — must be unique
  '{BC vendor no}',   -- from Business Central vendor card, e.g. 'V-00123'
  '{website url}'
);
```

**MFG code rules:**
- 2–5 characters, uppercase
- Used in BBS SKU generation: `BBS-{CODE}-{MFG_SKU}`
- Must be unique across all manufacturers
- Check existing codes in `docs/SESSION-HANDOFF.md` before picking one

**BC vendor no:** get this from BC's vendor card for the manufacturer. If BBS doesn't yet have a BC vendor record for this manufacturer, leave it `NULL` — BC sync will error on those products until it's populated.

---

## Quick reference: common manufacturer slugs and codes

| Manufacturer | Slug | MFG Code | Notes |
|---|---|---|---|
| Point Blank | `point-blank` | `PB` | 0 products loaded — priority |
| Point Blank Enterprises | `point-blank-enterprises` | `PBE` | Parent of Paraclete |
| 5.11 Tactical | `511-tactical` | `511` | Pending |
| Safariland | `safariland` | `SAF` | Pending |
| Propper | `propper` | `PROP` | Pending |
| Carhartt | `carhartt` | `CAR` | Pending |
| Tru Spec | `tru-spec` | `TS` | Pending |
| DriFire | `drifire` | `DF` | Pending |
| Mechanix Wear | `mechanix-wear` | `MECH` | Pending |
| Ergodyne | `ergodyne` | `ERGO` | Pending |
| MIRA Safety | `mira-safety` | `MS` | Profile enriched, products not loaded |
| Nightstick (Bayco) | `nightstick` | `NS` | Loaded — use `nightstick` slug |

---

## Updating an existing price list (annual refresh)

Same pipeline. The diff report will show:
- **New products** — SKUs added since last import
- **Price changes** — cost or MSRP changed
- **Unchanged** — no change, just logged
- **Discontinued** — SKUs in the old list but absent from the new one

A high discontinued count on an annual refresh is expected (5–15% is normal). If it's >30%, confirm with the manufacturer that the new file is complete — sometimes manufacturers send a partial list by accident.

After a price refresh, the `bc_sync_queue` will have `update` entries for every changed product. Once the BC sync worker is running, these will push updated pricing to BC automatically.

---

## Troubleshooting

**"Manufacturer not found" error on import:**
Run `python etl/seed.py` first, or manually INSERT the manufacturer into Supabase.

**Import completes but product count is much lower than expected:**
Check the exception report — a bad category name or missing required field will silently skip rows. Also check for duplicate `manufacturer_sku` values in the CSV (only first occurrence is kept).

**Family detection produces no families for an apparel manufacturer:**
The name stripping algorithm may not be recognizing the color/size pattern. Check the naming convention in the CSV — names need to follow the format `Base Name, COLOR, SIZE` for auto-detection to work. If the manufacturer uses a different convention, the `detect_families.py` script may need a manufacturer-specific extension.

**Shopify sync queue not getting populated after import:**
The trigger on the `products` table (migration 013) auto-enqueues on INSERT and UPDATE. If the queue isn't growing, check that migration 013 was applied. If the trigger is firing but causing constraint errors (`shopify_sync_queue_dedup_idx` violation), this is the known bug where duplicate `(product_id, action='update')` rows conflict. Workaround: `DELETE FROM shopify_sync_queue WHERE status = 'pending' AND product_id IN (SELECT id FROM products WHERE manufacturer_id = '{mfg_id}')` before re-running the import. The permanent fix is `ON CONFLICT (product_id, action) DO NOTHING` in migration 013 — this hasn't been applied yet.

**BC sync queue showing pending but nothing processing:**
The BC sync consumer process is not running. This is a known infrastructure gap (Azure VM provisioning blocked). The queue entries are correct and will process once the consumer is operational — no action needed on the import side.

**`cost > msrp` rows in exception report:**
Column swap in the cleaner step. The higher number is MSRP; the lower is cost. Go back to Stage 1 and fix the column mapping.

**Bootstrap import followed by real cost data:**
When a real price list arrives for a manufacturer previously imported in bootstrap mode, run the standard import (no `--bootstrap`). The diff will show `price_change` for every product that now has a real cost. After commit, verify `pricing_status = 'complete'` for the new import's rows:
```sql
SELECT pricing_status, COUNT(*) 
FROM product_prices pp
JOIN price_list_imports pli ON pli.id = pp.price_list_import_id
JOIN manufacturers m ON m.id = pli.manufacturer_id
WHERE m.slug = '{slug}' AND pp.is_current = true
GROUP BY pricing_status;
```
