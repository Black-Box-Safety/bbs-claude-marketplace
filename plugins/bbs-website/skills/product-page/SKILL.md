---
name: product-page
description: Use when changing BBS storefront product cards, PDPs, collection grids, pricing display, brand logos, lead times, compliance chips, contract vehicles, quote/RFQ flow, or product metafields — or when a card/PDP renders wrong (missing logo, wrong price mode, absent contract block).
requires: [shopify, shopify-cli, node]
---
> **BBS Website pipeline — stage: Storefront.** See `site-wiring-map` for how this fits the whole flow.

# BBS Product Card + PDP System

Shipped 2026-07-22 (Phase 1). Spec: `docs/superpowers/specs/2026-07-22-product-card-pdp-redesign-design.md`. Post-ship state + fast-follow list: `docs/HANDOFF-2026-07-22-card-pdp-redesign.md`.

## Where behavior lives

| Want to change | Touch |
|---|---|
| Brand logo / vendor quote-only / vendor lead time | `manufacturer` metaobject entry (Admin → Custom data), NOT Liquid. Snippets read `shop.metaobjects.manufacturer[vendor \| handleize]` |
| Per-product quote-only, lead time, mfr part #, UOM, bullets, specs, fits, docs, restriction | `bbs.*` product metafields (12 typed definitions exist) |
| Card anatomy | `theme/snippets/product-card.liquid` + base.css "Product Cards (paper)" |
| PDP skeleton | `theme/sections/main-product.liquid` (idbar → buy col → Overview/Specs/Contracts/Docs) |
| Price/quote decision | `theme/snippets/product-pricing-mode.liquid` ONLY — shared by card, PDP, JSON-LD, COPY LINE. Never fork the logic |
| RFQ payload format | `rfq_line_items` capture in `theme/sections/main-cart.liquid` (pipe format + line-item properties) |

## Hard rules

- **Precedence** (pricing + lead time): product metafield > manufacturer metaobject > `price_min == 0`. Product-level values silently override vendor-wide — check before debugging.
- **Contract numbers NEVER hardcoded** — only from `contract_vehicle` metaobject (`name`/`number` fields). PDP falls back to name-only chips from legacy string/tags.
- **Cert language verbatim**: "Federal Service-Disabled Veteran-Owned Small Business (SDVOSB) · California-certified DVBE, OSDS #2009473." Never unqualified "certified small business". See memory `reference_cert_jurisdiction_doctrine`.
- Reference-list metafields: use the `| size` FILTER (`.count`/`.size` properties are shape-fragile).
- Lead times render only from vetted data — never invent defaults.
- CHP carrier bundles (`product.chp-carrier.json` → `main-product-chp-carrier.liquid`, 6 products via templateSuffix) are a separate protected system — generic PDP changes must not touch them.
- Card is one big `<a>` — no nested interactive elements.

## Tools (idempotent, dry-run default, `--apply` writes; env `SHOPIFY_STORE_DOMAIN` + `SHOPIFY_ADMIN_API_TOKEN`, or run mutations via Shopify MCP)

- `scripts/setup-manufacturer-metaobjects.mjs` — definition + 46-brand seed; re-run to add brands in bulk
- `scripts/setup-metafield-definitions.mjs` — the 12 `bbs.*` definitions
- `scripts/seed-golden-skus.mjs` — 5 test products exercising every render path (pry bar=thin/fallback-brand, First Tactical, Streamlight=key_specs, Paraclete=quote-only+vehicles, ASP=restricted LE)

## Deploy + verify (landmines)

- Confirm live theme id first (`shopify theme list` — it has swapped before; CLAUDE.md holds current).
- `--only` push **silently no-ops for NEW files when run from repo root** — `cd theme/` first, always verify via pull-and-diff after.
- Storefront verification: curl clean-cookie flow (POST `form_type=storefront_password&password=pm-sample` to /password w/ cookie jar) — the shared Playwright browser profile gets cookie-poisoned by concurrent sessions.
- Dev themes 404 on `?preview_theme_id=` — use `shopify theme dev` proxy.
- Test all card surfaces: /collections/all, home (featured/preferred strips), /search — one snippet renders everywhere.
