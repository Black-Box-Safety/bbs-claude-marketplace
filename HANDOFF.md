# HANDOFF — the personal-copy cutover

The July 2026 rollout this file used to track is **done**. The repo is pushed, the
marketplace is live, and what was one `bbs-ops` plugin is now four. Deployment moved to
[`docs/ADMIN-RUNBOOK.md`](docs/ADMIN-RUNBOOK.md), the acceptance gate to
[`docs/acceptance/`](docs/acceptance/README.md), and asset status to
[`REGISTRY.md`](REGISTRY.md).

One thread from it is still open, and it is the reason this file still exists: **15 skills
exist twice** — once as a personal copy synced to Parker's account, once in the
marketplace. While both copies exist, whichever loads first wins, silently. That is the
fleet audit's worst failure mode, and it is now the gap between a fix landing in the
marketplace and a rep actually getting it.

Last verified: 2026-09-15.

## Why this matters more than it did in July

In July this was three skills. Porting the personal skill set into the marketplace made it
fifteen — every skill below now has a marketplace copy that is the maintained one, and a
personal copy that shadows it in Parker's own sessions.

Concretely: the `obs-form-filler` hardening of 2026-09-14 — checkbox on-state validation,
and the refusal to truncate a quote too long for the worksheet — is live in the marketplace
and **absent from the personal copy Parker's sessions load first**. Parker is currently the
one person at BBS not getting his own bug fixes.

## The cutover

Per skill, one commit each — never en masse, so a bad pointer is one revert and not a
rollback of the set. For each, replace the personal `SKILL.md` **body** with a three-line
pointer to the marketplace copy, keeping the frontmatter `name` and `description` so
triggering is unchanged until the personal copy is deleted.

Order matters: start with the skills whose marketplace copy has already done real work.

**Tier 1 — the marketplace copy is ahead of the personal one, cut over first:**

| Skill | Marketplace home | Why first |
|---|---|---|
| `obs-form-filler` | `bbs-sales` | Personal copy lacks the checkbox and truncation fixes |
| `ca-form-filler` | `bbs-sales` | Personal copy has no vendor profile and points at `/mnt/skills` |
| `bbs-pricelist-import` | `bbs-website` | Personal copy hardcodes a path on one Mac |
| `dgs-bpo-item-check` | `bbs-sales` | Personal copy documents a container-only path |
| `bbs-quote-builder` | `bbs-sales` | Personal copy calls a container-only LibreOffice wrapper |

**Tier 2 — copies are equivalent; cut over as each is exercised:**

`bbs-sourcing`, `bbs-b2b-pricing`, `bbs-deck-voice`, `bbs-po-status`,
`bbs-rebate-profitability`, `dwr-pdf-info`, `grainger-cart-info`, `grainger-screenshot`,
`so-search`, `vendor-quote-email`.

**Then the source repos**, same one-commit-each rule: `price-list-cleaner`,
`contract-discount-loader`, `family-rollup` (in `bbs-database`) → `product-page`,
`brand-page-builder` (in `bbs-shopify`) → `le-lane-tuning`, `supply-lane-tuning` (in
`bbs-quote-bot`). `naspo-quote`'s repo cutover is tracked in `REGISTRY.md` instead.

Any skill that turns out to be company-wide rather than desk-specific belongs in
`bbs-foundations` — leave it and flag it there rather than pointing it at the wrong plugin.

## Known gaps

Not blockers; log them through `/bbs-review` so Arthur and Tom can prioritise.

| Gap | Status |
|---|---|
| `bbs-sourcing` references companion `references/` files (vendor directory, email templates, triage, input-handling) that exist nowhere | **Open**, verified 2026-09-15. Add them or trim the refs. `vendor-quote-email` covers part of what the email-template file was meant to hold. |
| `image-pipeline` is a documented stub — the Sirv/Firecrawl workflow is not codified | **Open**, verified 2026-09-15 |
| `family-rollup` depends on the unmerged `bbs-database` branch `feature/nonapparel-family-expansion` | **Unverified** — status lives in that repo, not this one |
| `ca-form-filler` expects a vendor-profile JSON that was never shipped | **Closed** 2026-09-15. It ships at `plugins/bbs-sales/references/vendor_profile.json` and is now the single source both form skills read. |

---

Owner: Parker. This file is done when the table above is empty and no skill exists twice.
