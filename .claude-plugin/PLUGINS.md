# Plugins in this marketplace

Three plugins, split by the desk that owns the work rather than by subject matter.
Install the one that matches your job; install more than one if you do more than one.

- **bbs-sales** (live) — the California state quote desk, end to end. An inbound RFQ
  is logged, its items are pulled out of whatever the agency sent (DWR PDF, Grainger
  cart, a screenshot), checked against the DGS BPO, priced through the Grainger
  punch-out or vendor sourcing, turned into a customer quote on BBS letterhead, and
  wrapped in the CDCR or CA compliance packet. Also Grainger promo pages and federal
  deck copy. `plugins/bbs-sales`.

- **bbs-ops** (live) — the website pipeline: a manufacturer price list becomes a live
  product page. Catalog import, contract pricing, variant families, enrichment,
  storefront pages, quote-bot lane tuning, and the skill-bus doctrine.
  `plugins/bbs-ops`.

- **bbs-back-office** (live) — what happens after the bid is won, read out of Business
  Central: where an order stands, what a vendor still owes us, and what the deal
  actually earned once Grainger rebates are applied. `plugins/bbs-back-office`.

- **bbs-foundations** (planned, separate spec) — company-wide AI fundamentals: MCP
  connectors (ca-procurement-intel, Grainger, BBS Kit, Microsoft 365, Shopify,
  Supabase), shared company knowledge, and AI-literacy onboarding. When built, append
  another entry to `marketplace.json` with `"source": "./plugins/bbs-foundations"`.

## Where the CA form skills live, and why

`ca-form-filler` and `obs-form-filler` used to sit in `bbs-ops`, which put the CDCR
bid packet inside the website-maintenance plugin. A rep who installed only the sales
plugin — the one matching the work they actually do — did not get them. Both moved to
`bbs-sales` alongside `naspo-quote`, together with `bbs-sourcing`.

The overlap this note used to warn about is real and is **not yet resolved**: the
three form skills cover five of the same nine CA sub-forms, and BBS's vendor facts
are still written down twice, in two shapes —
`ca-form-filler/references/vendor_profile.json` (nested) and
`obs-form-filler/assets/bbs_vendor_profile.json` (flat, read by its fill script).
**Change a cert, address or permit in one and you must change the other.** Collapsing
them into a single shared reference is the next step; co-locating them was the
prerequisite, not the fix.

## Adding a skill

Drop it in `plugins/<plugin>/skills/<name>/`, with `name:` in the SKILL.md frontmatter
matching the folder exactly — the skill-bus matches subscriptions on `plugin:skill`,
so a mismatch silently stops doctrine from firing. Quote the `description:` if it
contains a colon, or the frontmatter will not parse and the skill will not load.
