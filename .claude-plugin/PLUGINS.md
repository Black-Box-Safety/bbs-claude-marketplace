# Plugins in this marketplace

- **bbs-website** (live) — the site-maintenance pipeline: a manufacturer price list
  becomes a live product page. Catalog import (`bbs-pricelist-import` runs the five
  stages, `price-list-cleaner` is its first), contract pricing, variant families,
  enrichment, storefront pages, and quote-bot lane tuning. `plugins/bbs-website`.
- **bbs-sales** (live) — the California state quote desk, end to end. An inbound RFQ is
  logged, its items are pulled out of whatever the agency sent (DWR PDF, Grainger cart,
  a screenshot), checked against the DGS BPO, priced through the Grainger punch-out or
  vendor sourcing, turned into a customer quote on BBS letterhead, and wrapped in the
  CDCR or CA compliance packet. Also Grainger promo pages. Federal deck copy moved
  to `bbs-foundations` — a federal pursuit needs none of the other 13 skills here, and
  SDVOSB cert discipline does not belong among California DVBE skills.
  `plugins/bbs-sales`.
- **bbs-back-office** (live) — what happens after the bid is won, read out of Business
  Central: where an order stands, what a vendor still owes us, what a problem order
  actually needs, and what the deal earned once Grainger rebates are applied.
  `plugins/bbs-back-office`.
- **bbs-foundations** (live, first release) — company-wide AI fundamentals. Ships
  `bbs-claude-md-forge` (BBSClaudeMDForge): the BBS way to write, audit, and repair
  CLAUDE.md files, with a deterministic checker and the canonical facts every repo must
  agree on. Also `bbs-voice-template`: how a teammate builds a personal `<first>-voice`
  skill from their own sent mail, with `parker-voice` as the worked example, and
  `bbs-deck-voice`, the voice standard for federal (SDVOSB/GSA) slide copy.
  `plugins/bbs-foundations`. Spec:
  `docs/superpowers/specs/2026-09-02-bbs-foundations-claude-md-forge-design.md`.
  `bbs-grounding-doctrine` lives here and only here; `bbs-website` no longer carries a copy,
  and its two lane-tuning skills receive it from this plugin.
  Still planned, each its own spec: the MCP connector roster (ca-procurement-intel,
  Grainger, BBS KIt, Microsoft 365, Shopify, Supabase) with a degrade-gracefully contract,
  and AI-literacy onboarding. `bbs-order-reconciliation` moved out to `bbs-back-office`,
  where the rest of the post-award work lives.
- **claudeforge** (pinned external) — the generic CLAUDE.md engine `bbs-foundations`
  depends on, pinned to the BBS fork `Black-Box-Safety/ClaudeForge` at `dev` so it updates
  through git and never gets hand-copied. Install it for `/sync-claude-md` and the
  link/drift audits; `bbs-claude-md-forge` works without it.

## Where the CA form skills live, and why

`ca-form-filler` and `obs-form-filler` used to sit in the website plugin, which put the
CDCR bid packet inside site maintenance. A rep who installed only the sales plugin — the
one matching the work they actually do — did not get them. Both moved to `bbs-sales`
alongside `naspo-quote`, together with `bbs-sourcing`.

The overlap this file used to warn about is **resolved**. BBS's vendor facts now live
once, at `plugins/bbs-sales/references/vendor_profile.json`, and every form skill reads
that file — `fill_obs_packet.py` derives its flat view from it rather than keeping a
second copy, so a cert expiry can no longer go stale in one place while a rep submits
binding bids from another.

The rules those forms share — who signs which lines, what the State fills in, why
CalRecycle 74 is never left blank, which certification language applies — live once in
`plugins/bbs-sales/references/ca-form-rules.md`. Field IDs stay in each skill, because a
field ID belongs to a specific PDF: the same STD 204 has different internal names inside
a bound packet than as a standalone download. **Semantics shared, field IDs local.**

If you are about to write a BBS address, cert number or signing rule into a skill, it
belongs in one of those two files instead.

FEIN and seller's permit are committed here deliberately. This repo is BBS-specific and
private, so the canonical-facts rule against committing them — which exists for work that
might be reused elsewhere — does not apply to this file.

## Adding a skill

Drop it in `plugins/<plugin>/skills/<name>/`, with `name:` in the SKILL.md frontmatter
matching the folder exactly — the skill-bus matches subscriptions on `plugin:skill`, so a
mismatch silently stops doctrine from firing. Quote the `description:` if it contains a
colon, or the frontmatter will not parse and the skill will not load at all.
