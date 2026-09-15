---
description: Onboard a new manufacturer — import its catalog, set contract eligibility, and build its brand page in the Field Manual style.
---

# /bbs-new-brand

Bring a new manufacturer fully onto the site.

1. **Catalog** (`catalog-intake`) — import the manufacturer's price list (see `/bbs-add-product` intake) so its products exist in Supabase.
2. **Eligibility** (`pricing-contracts`) — record which contracts the manufacturer is on and set pricing/eligibility accordingly.
3. **Brand page** (`storefront-pages` + `brand-page-builder`) — create the vendor smart-collection, `brand.*` metafields, hero + true-color logo, accent color, and Brands-nav wiring, matching the existing brand pages. Respect the storefront doctrine.
4. **Verify** — the brand page renders in the navy style like the others, and the manufacturer's products show correct price mode and contract block.
