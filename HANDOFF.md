# HANDOFF — the personal-copy cutover

The July 2026 rollout this file used to track is **done**. Deployment moved to
[`docs/ADMIN-RUNBOOK.md`](docs/ADMIN-RUNBOOK.md), the acceptance gate to
[`docs/acceptance/`](docs/acceptance/README.md), and asset status to
[`REGISTRY.md`](REGISTRY.md).

One thread is still open, and it is the reason this file exists: **15 skills exist twice**
— once as a personal copy synced to Parker's claude.ai account, once in the marketplace.
While both exist, whichever loads first wins, silently.

The 2026-09-15 consolidation made this **more urgent, not less**. It is now the highest
open risk in the marketplace.

Last verified: 2026-09-15.

---

## What changed, and why it got worse

Before the consolidation, a duplicate was the *same skill twice* — bad, but both copies
told Claude roughly the same thing. After it, five personal copies have **no marketplace
counterpart by that name**, and they contradict what replaced them:

| Orphaned personal copy | What replaced it | What the stale copy still does |
|---|---|---|
| `bbs-b2b-pricing` | `grainger-pricing` (Grainger MCP) | **Drives the retired `b2b.blackboxsafety.com` punch-out.** Still triggers on "price these Grainger items" |
| `obs-form-filler` | `ca-form-filler` Path A | Points at `/mnt/skills/...`, which does not exist on a real machine |
| `grainger-cart-info` | `rfq-item-extract` | Competes for cart-PDF extraction |
| `grainger-screenshot` | `rfq-item-extract` | Competes for screenshot extraction |
| `dwr-pdf-info` | `rfq-item-extract` | Competes for DWR RFQ extraction |

The remaining ten still shadow a marketplace skill of the same name: `bbs-deck-voice`
(now in `bbs-foundations`), `bbs-po-status`, `bbs-pricelist-import`, `bbs-quote-builder`,
`bbs-rebate-profitability`, `bbs-sourcing`, `ca-form-filler`, `dgs-bpo-item-check`,
`so-search`, `vendor-quote-email`.

Parker is the one person at BBS whose sessions load the stale copy first, so he is the one
person not receiving his own fixes.

---

## How the cutover actually works — confirmed 2026-09-15

**It is not a repo change, and it is not an edit.** Earlier revisions of this file said to
replace each personal `SKILL.md` body with a three-line pointer. That does not work:

> Removing a synced skill from disk was tested. A new session re-synced it
> byte-identical within seconds, and the skill stayed available throughout.

These skills are **account-synced**. They live in Parker's claude.ai account, and the only
place they can be retired is **claude.ai → Settings → Capabilities → Skills**. Nothing in
this repo, and no filesystem operation on any machine, will remove them.

**It is a delete, not a merge.** All 15 were diffed against the marketplace:

- **9 are byte-identical** to the marketplace copy — deleting them loses nothing at all.
- **6 differ only by being worse** — they carry `/mnt/skills/...` and
  `/Users/parkermarshall/...` paths, an unquoted `description:` colon that stops the skill
  loading, and a `PASTE_VENDOR_PROFILE_JSON_HERE` step the single-source rule exists to
  eliminate.

There is nothing in any personal copy worth harvesting. The marketplace copy is canonical
in every case.

---

## Order

1. **The five orphans first.** They are pure contradiction — the thing they duplicated no
   longer exists, so nothing is lost and a live wrong instruction goes away.
   `bbs-b2b-pricing` is the most urgent: it is the only one that will send a rep down a
   retired pricing path.
2. **Then the ten shadows**, as each is exercised. Lower risk — the marketplace copy says
   substantially the same thing, it is just the maintained one.

After each deletion, confirm in a fresh session that the skill is gone and the marketplace
copy triggers in its place. `docs/evals/` measures the triggering half if you want it
checked rather than assumed.

---

## Then the source repos

Same one-at-a-time rule: `price-list-cleaner`, `contract-discount-loader`, `family-rollup`
(in `bbs-database`) → `product-page`, `brand-page-builder` (in `bbs-shopify`) →
`le-lane-tuning`, `supply-lane-tuning` (in `bbs-quote-bot`). `naspo-quote`'s repo cutover
is tracked in `REGISTRY.md` instead.

Any skill that turns out to be company-wide rather than desk-specific belongs in
`bbs-foundations` — leave it and flag it there rather than pointing it at the wrong plugin.
