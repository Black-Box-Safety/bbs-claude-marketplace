---
description: Route "upload a product" through the whole pipeline — intake, pricing, enrichment, storefront — invoking the right skill and agent at each step.
---

# /bbs-add-product

Take a product (or a manufacturer price list) from raw input to a live card + PDP. Move through the stages, handing off to the owning agent at each; do not skip a stage.

1. **Intake** (`catalog-intake` + `price-list-cleaner`) — clean the input, map to the import template, load into Supabase. Verify row count and required fields.
2. **Pricing** (`pricing-contracts` + `contract-discount-loader`) — check the manufacturer's contract eligibility; apply the discount schedule / price mode.
3. **Enrichment** (`product-enrichment` + `family-rollup` / `image-pipeline`) — description, image, variant family. No invented specs; image must load.
4. **Storefront** (`storefront-pages` + `product-page`) — confirm the Supabase→Shopify sync brings the product across, then verify it renders as a card and a PDP with the right price mode, logo, and compliance block.
5. **Cross-sell** (`cross-sell`, optional) — ensure it appears in / generates a related-products strip.

At each step, state what you did and what you verified. If a stage can't complete (missing data, sync not run), stop and say so — flag, don't guess.
