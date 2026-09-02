---
name: image-pipeline
description: 'Prepare and place BBS product/brand imagery — scrape or receive source images, optimize, push to the Sirv CDN, and wire the resulting URLs into Supabase product image fields and Shopify metafields. Use when a product has no image, an image is broken or wrong, or a new brand needs a hero/logo. NOTE: this workflow is being formalized; follow the documented steps and record any gap for /bbs-review.'
---

> **BBS Website pipeline — stage: Enrichment.** See `site-wiring-map`.

# Image Pipeline (forming)

This skill is a documented stub. The CDN workflow (Sirv) and enrichment scraping (Firecrawl) exist in practice but are not yet a single codified skill. Until they are:

1. **Source** — obtain the manufacturer image (supplier import, or Firecrawl scrape of the manufacturer product page). Reference the Firecrawl MCP by name; if it is not installed, fall back to a manual image hand-off and note it.
2. **Optimize** — size/compress to the storefront's card and PDP dimensions.
3. **Host** — upload to the Sirv CDN; capture the canonical URL.
4. **Wire** — write the URL to the Supabase product image field (so both the storefront and the quote-bot `image_url` fallback pick it up) and, for brands, the `brand.*` hero/logo metafield.

**Known gap:** codify steps 1–3 as a script under `bbs-database`/`bbs-shopify` and replace this stub. Log the gap for `/bbs-review` so Arthur/Tom prioritize it.
