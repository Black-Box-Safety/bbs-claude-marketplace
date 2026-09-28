---
name: contract-discount-loader
description: Load or update a cooperative/government contract whose pricing is a discount off MSRP by manufacturer into the BBS (Black Box Safety) product database contract-pricing subsystem. Use this skill whenever the user wants to apply a new contract, refresh contract pricing, or load a manufacturer discount schedule — e.g. "apply our NPPGov contract", "load the new Sourcewell discounts", "update the PS25650 pricing", "here's the June discount sheet for <contract>", or hands over an Excel/CSV of brands and percent-off values tied to a contract. Also trigger for any request about contract eligibility (which manufacturers are/aren't on a contract) or making non-contracted products show as unavailable under a contract. This is the right skill any time a contract's per-manufacturer discount-off-MSRP schedule needs to land in the database.
requires: [supabase, python3]
---
> **BBS Website pipeline — stage: Pricing.** See `site-wiring-map` for how this fits the whole flow.

# BBS Contract Discount Loader

**Location:** this skill operates inside the bbs-database repo (locate it via `site-wiring-map`; do
not assume an absolute path) — the loader, migrations, and `.env` all live there. Start by changing
into that repo's root so the relative paths below resolve, regardless of where the session was
launched.

You are loading a contract's pricing into the BBS product database. The common contract shape
at BBS is **a discount off MSRP, set per manufacturer** (cooperative/GPO vehicles like NPPGov,
Sourcewell, NASPO). The infrastructure already exists — your job is to map a messy real-world
discount file onto it cleanly, idempotently, and with eligibility working.

## How contract pricing is modeled (read first)

The schema is in `db/migrations/004_contracts.sql`; the resolution view is
`product_contract_prices` (`db/migrations/006_contract_price_view.sql`, extended by `016`).

- `contracts` — one row per contract, keyed in practice on `contract_number`.
- `contract_pricing_rules` — the discount rules. For MSRP-discount contracts:
  `discount_type='percentage'`, `discount_value` a **fraction** (0.15 = 15% off), `category_id`
  NULL (manufacturer-wide), `effective_to` NULL (the active rule). Price resolves to
  `round(msrp * (1 - discount), 2)`.
- `contract_product_overrides` — fixed per-SKU "market basket" prices (rare; not used by a pure
  discount sheet).
- `product_contract_prices` view — resolves price + `is_eligible` per product per contract.
  **Eligibility is the key behavior:** a product is eligible under a contract only if its
  manufacturer has a pricing rule (or an override). Products from non-contracted manufacturers
  resolve to `is_eligible=false`, `price_source='unpriced'`, `contract_price=NULL` — i.e. *not
  available under that contract*. This is how "manufacturers not on the contract show as inactive"
  is implemented. You don't need a separate flag — the rules ARE the eligibility list.

## The loader

`etl/import_contract_pricing.py` does the work and is **idempotent** — safe to re-run when a
discount file is refreshed (it upserts the contract and updates rules in place). Pure logic
(format normalization, brand→manufacturer resolution, max-discount collapse) is unit-tested in
`tests/test_import_contract_pricing.py`; extend those tests when you change that logic.

```bash
source venv/bin/activate
python etl/import_contract_pricing.py \
  --xlsx ~/Downloads/<discount-file>.xlsx \
  --contract-number <NUMBER> --contract-name "<Name>"
```

Credentials come from `.env` (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`) — these reach data tables
via PostgREST. DDL (the view migration) does **not** go through them; see step 5.

## Workflow

### 1. Understand the discount file
Read it (it's usually a flattened `Brand | Discount` export of a richer `Category × Brand ×
Discount` schedule). Expect mess:
- **Mixed formats** in the discount column — numeric fractions (`0.1` = 10%) *and* percent strings
  (`"15%"`). The loader's `normalize_discount` handles both; verify nothing else sneaks in.
- **Duplicate brands** because a brand appears under multiple contract categories, sometimes at
  **different rates**. BBS policy: collapse to one manufacturer-level rule using the **MAX
  discount** (a contract price is a ceiling — honoring the larger discount avoids overcharging a
  member). `collapse_max_discount` does this.
- **Junk rows** (a trailing `—`/blank) — skipped.

### 2. Map brands → manufacturers
The loader matches brand names case/space-insensitively against the `manufacturers` table, plus an
explicit `BRAND_ALIASES` map for spelling/rename drift (e.g. `DirFire→DriFire`,
`Eberlestrock→Eberlestock`, `Sirchie→Evident (formerly Sirchie)`). Same-entity duplicates like
**Point Blank / Point Blank Enterprises** are applied to both rows. When a file introduces a new
variant, add it to `BRAND_ALIASES` (or the Point Blank set) rather than hand-editing data.

The loader **reports unmatched brands instead of dropping them.** Always resolve a non-empty
unmatched list before considering the load done.

### 3. Create missing manufacturers
Brands on the contract but absent from `manufacturers` must be created first (a pricing rule
FK-references a manufacturer). Note: a brand at **0% is still on-contract** (eligible, sold at
MSRP) — distinct from non-contracted — so create those too. Dispatch a **subagent** to create the
rows idempotently (skip-by-name, resolve `slug`/`mfg_code` collisions, `mfg_code` ≤5 chars,
`is_active=true`); see the pattern already used for the NPPGov load. Then re-run the loader so the
new brands resolve.

### 4. Load and verify
Run the loader (step "The loader"). Then **run it a second time** — a clean re-run reports
`0 inserted, N updated`, proving idempotency. Verify eligibility against the live view:
- A contracted manufacturer's product → a discounted `contract_price`, `price_source` like
  `mfg_rule`, `is_eligible=true`. Spot-check the math (`msrp * (1 - discount)`).
- A non-contracted manufacturer's product → `contract_price=NULL`, `price_source='unpriced'`,
  `is_eligible=false`.

### 5. Apply the eligibility view migration (only if not already applied)
The `is_eligible` column lives in migration `018_contract_eligibility.sql`. The contract is
**functional without it** (eligibility is derivable from `price_source='unpriced'`), so don't
block the load on it. To apply it:
- `python db/run_migrations.py` needs `SUPABASE_DB_PASSWORD` (Supabase Dashboard → Settings →
  Database). If you don't have it, the **SQL Editor** is the fast path: paste the migration's
  `CREATE OR REPLACE VIEW …` and run.
- **Gotchas seen in production:**
  - *"table name specified more than once" (42712)* = the SQL Editor still had previous text;
    select-all, clear, paste once.
  - *"cannot drop columns from view" (42P16)* = the live view has drifted from the migration
    (hand-added columns not in git — happens often here). `CREATE OR REPLACE` may only **append**
    columns, never drop/reorder. Query the live column set
    (`select * from product_contract_prices limit 1`), make the new definition a superset in the
    same order, append the new column last, and update the migration file to match reality.

### 6. Record it
Write/refresh a canonical reference at `docs/contracts/<contract-slug>.md` (facts, dates, covered
categories, the discount schedule, the eligibility rule, reload command) and add a memory pointer.
This keeps future sessions consistent — see `docs/contracts/nppgov.md` as the template.

## Definition of done
1. All brands mapped (unmatched list empty); missing manufacturers created.
2. Contract + rules loaded; second run is idempotent.
3. Eligibility verified: contracted priced, non-contracted `unpriced`/ineligible.
4. View migration applied (or explicitly flagged as pending with the reason).
5. Reference doc + memory updated; work committed.

## Notes
- This repo's Supabase project has been on the Free plan; if you hit quota/billing errors from the
  REST API, surface it — the data loads via that API and apps read through it.
- Don't invent compliance restrictions from a contract's category structure. Per BBS, category
  breakdowns are not sales limits unless specifically called out.
