---
name: brand-page-builder
description: 'Create an enriched manufacturer brand page in the BBS "Field Manual" Shopify theme, matching the existing 24 brand pages. Use whenever a new manufacturer/vendor is added to the catalog and needs a brand collection page — i.e. a vendor smart-collection + brand.* metafields + a CDN hero image + a true-color logo + a per-brand accent color + Brands-nav wiring, in the established navy style. Triggers: "add a brand page", "create a brand page for <X>", "new manufacturer page", "brand page like the others", "onboard <manufacturer> brand page".'
requires: [supabase, shopify, shopify-cli]
degrades-without: [firecrawl]
---
> **BBS Website pipeline — stage: Storefront.** See `site-wiring-map` for how this fits the whole flow.

# Brand Page Builder

Produces one enriched manufacturer **brand collection page** identical in style to the existing 24
(Team Wendy, Avon, Streamlight, …). The foundational system already exists — this skill ADDS a
brand to it; it does not bootstrap it.

## Assumes already in place (built 2026-06-07)
- Theme **BBS — Field Manual** (live, `gid://shopify/OnlineStoreTheme/159152439547`), store
  `bbs-supabase-test.myshopify.com` (storefront password `pm-sample`).
- `snippets/brand-hero.liquid` (the navy hero, reads `collection.metafields.brand.*`, accent +
  contrast guard, logo `color`/`screen`/`whiten` treatments), the `main-collection.liquid` guard
  (renders brand-hero when `brand.overview` is set), `snippets/vendor-logo.liquid` (vendor→logo
  asset map), `sections/brand-index.liquid` (+ `/pages/brands`), and the **20 `brand.*` collection
  metafield definitions** (namespace `brand`).
- Supabase project `oaqkueputgaweojcpaim`, table `manufacturers` with the profile columns
  (migration `20260606_manufacturer_profile_fields.sql`).
- Reference: `docs/runbooks/2026-06-06-brand-pages.md`, `docs/brand/brand-pages-status-2026-06-07.md`.

> Data-layer note: manufacturer *enrichment data* ideally originates in the `bbs-database` repo
> (`etl/enrich_manufacturer_descriptions.py`). If the `manufacturers` row is already enriched, reuse
> it; only scrape here if it's missing. The page artifact (collection/metafields/logo/theme) is
> owned by this repo.

## Secrets (never hardcode/commit)
- Firecrawl: `$FIRECRAWL_KEY` (ask the user / env). Supabase service key + Shopify auth come from the
  connected MCP / CLI. Shopify CLI is authed for `--only` live pushes.

## Inputs
`name` (exact Shopify product **vendor** string), `slug`, `website`. Precondition: products with
that vendor already exist in the store (otherwise the smart collection is empty — confirm first via
`productVendors` or a product search).

## Procedure
1. **Confirm the vendor + counts.** Query Shopify `productVendors` to get the EXACT vendor string
   (e.g. "S&S Precision", not "ss-precision"). The smart-collection rule must match it verbatim.
2. **Enrich the profile (sourced, no fabrication).** Reuse the Supabase `manufacturers` row if
   populated; else Firecrawl-scrape the brand's own site (homepage + about/history/contact) for:
   overview (2–3 sentences), history, founded_year, headquarters, specialties[4–6], product_lines
   (verify against our actual SKUs), certifications, socials. Record `profile_source_urls`; set
   `profile_status='enriched'` (or `needs_review` if founded/HQ/overview can't be verified — never
   invent). Marketing voice = authoritative, mission-focused, gov/LE/military buyer.
3. **Hero image.** Pick a wide (≥1600px) in-use/flagship image from the brand's site. Create the
   collection with it as `image` (Shopify CDN-ingests it → optimized). If the host blocks hotlinking
   (HTTP 403), download with a browser UA + `sharp`-trim, then staged-upload to Shopify.
4. **Accent color.** Choose a brand-true hex. The hero applies a contrast guard
   (`color_contrast` vs navy `#051c2c`, threshold **2.2** → else falls back to gold) — pick a color
   that reads on navy (bright/warm); reds ~2.4 pass, near-black fails (fine, it falls back).
5. **Logo (must read in COLOR on the dark hero).** Get the official logo; classify treatment:
   - `color` — transparent light/colored logo → use as-is (filter:none).
   - `screen` — full-color logo on a solid BLACK field → `mix-blend-mode:screen` drops the black.
   - `whiten` — last resort, single-color/dark mark.
   Optimize with `sharp` (trim, ≤1000px, PNG/keep SVG), save as `theme/assets/mfr-<handle>.<ext>`,
   add a `when '<handle>'` case in `snippets/vendor-logo.liquid`, and add `<handle>` to the matching
   list (`color_logos` / `screen_logos`) in BOTH `snippets/brand-hero.liquid` and
   `sections/brand-index.liquid` (default = whiten).
6. **Create the smart collection** (built-in `create-collection`): title=`name`,
   `ruleSet {appliedDisjunctively:false, rules:[{column:VENDOR, relation:EQUALS, condition:name}]}`,
   `sortOrder:BEST_SELLING`, `descriptionHtml`, `image`=hero. (Auto-publishes to Online Store
   publication `gid://shopify/Publication/186720616699`.) Capture the collection GID + handle.
   Smart-collection product counts populate **asynchronously** — re-poll after ~60s, don't trust 0.
7. **Set `brand.*` metafields** (`metafieldsSet`, owner=collection GID). Keys + types:
   overview/history `multi_line_text_field`; tagline/headquarters/country/lead_time
   `single_line_text_field`; founded_year `number_integer`; brand_color `color`; authorized
   `boolean`; website/hero_image_url/social_linkedin/social_youtube `url`;
   specialties/certifications/product_lines/contract_vehicles/quote_methods
   `list.single_line_text_field`; hero_image/logo `file_reference`. (Omit contract_vehicles/
   quote_methods/lead_time to use the theme defaults: GSA·NASPO·DGS LPA·Sourcewell / 5–10 BD /
   Agency PO·P-card·GovCard.)
8. **Mirror to Supabase** `manufacturers`: set the enriched fields + `shopify_collection_id`,
   `shopify_synced_at`, `brand_color`, `hero_image_url`, `profile_*`.
9. **Wire the nav:** append `<handle>` to the `brand_handles` default in `sections/header.liquid` and
   the `default_handles` in `sections/brand-index.liquid` (keep ordered by catalog size).
10. **Deploy:** `shopify theme push --store bbs-supabase-test.myshopify.com --theme 159152439547
    --path theme --only <changed assets + vendor-logo.liquid + brand-hero.liquid +
    brand-index.liquid + header.liquid> --allow-live`. Commit on a branch + PR (repo guardrail:
    plan→approve, `--only`, never blind full push).
11. **VERIFY VISUALLY (definition of done).** The store is password-gated, so screenshot the live
    page via Firecrawl and actually look at it (logo in true color, hero image, stats, no white box):
    ```
    POST https://api.firecrawl.dev/v1/scrape  (Bearer $FIRECRAWL_KEY)
    { "url":"https://bbs-supabase-test.myshopify.com/collections/<handle>",
      "formats":["screenshot"], "waitFor":2000,
      "actions":[
        {"type":"wait","milliseconds":1200},
        {"type":"click","selector":"input[type=password]"},
        {"type":"write","text":"pm-sample"},
        {"type":"press","key":"ENTER"},
        {"type":"wait","milliseconds":3500},
        {"type":"executeJavascript","script":"window.location.href='/collections/<handle>'"},
        {"type":"wait","milliseconds":4500},
        {"type":"screenshot"} ] }
    ```
    Download `data.screenshot` and inspect. (Lesson learned: a parent CSS `filter` once silently
    whitened every hero logo and a green "deployed" hid it — never call done without seeing pixels.)

## Guardrails
- No invented facts — source profile copy; flag unverifiable as `needs_review`.
- Live theme pushes `--only`, never blind; plan → approve → execute for DB/live changes.
- Logo/hero imagery is manufacturer-sourced: co-marketing OK for the internal demo; confirm reuse
  rights before any public launch.

## Scale (batch onboarding)
For several brands at once, fan out subagent-driven (one agent per brand for enrich + logo sourcing,
then batch the Shopify writes), exactly as the original 24 were built — see
`docs/brand/brand-pages-status-2026-06-07.md`.
