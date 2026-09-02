# HANDOFF — bbs-ops plugin, remaining steps

> **2026-09-02:** the plugin described below was renamed `bbs-ops` → `bbs-website` (directory `plugins/bbs-website`, install `bbs-website@bbs-claude-marketplace`). Paths and names in this handoff are as they were on 2026-07-23.

**State as of 2026-07-23:** the `bbs-ops` plugin is fully built, statically validated, and
committed locally in this repo (`bbs-claude-marketplace`). It has NOT been pushed, NOT been
installed live, and the source repos have NOT been cut over. Everything below is what's left.
Built on the home desktop; the interactive steps happen on the office machine.

## What's done

- Marketplace manifest (one plugin `bbs-ops`; `bbs-foundations` reserved in `.claude-plugin/PLUGINS.md`).
- 12 skills (`site-wiring-map` + 11 ported copy-not-cut), 10 agents, 4 commands, 3 skill-bus
  doctrine inserts / 13 subscriptions (all targets resolve).
- A deep review found and fixed 10 defects (skill-bus no-match, dangling agent names, a stale
  Grainger architecture description in quote-bot, form numbers, README links, gap notes).
- Design spec + plan live in the `bbs-quote-bot` repo under `docs/superpowers/`.

## Step 1 — Push (once, from any machine with gh auth to the Black-Box-Safety org)

```bash
cd bbs-claude-marketplace
gh repo create Black-Box-Safety/bbs-claude-marketplace --private --source=. --remote=origin --push
```

At the office machine after that: `git clone https://github.com/Black-Box-Safety/bbs-claude-marketplace`.

## Step 2 — Install live (interactive Claude Code session, office machine)

```
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace
/plugin install bbs-ops@bbs-claude-marketplace
/bbs-onboard
```

Then confirm skill-bus fires on the plugin's own skills (this was the old gap): invoke the
`product-page` skill and check `.claude/skill-bus-telemetry.jsonl` shows a `match` (not
`no_match`) for `bbs-ops:product-page` with `bbs-storefront-doctrine`.

## Step 3 — Acceptance gate (the real test)

A Black Box team member who is NOT Parker, guided only by `/bbs-onboard` + `site-wiring-map`,
runs `/bbs-add-product` on one real product and sees it render as a card + PDP — without asking
Parker. Record pass/fail. This is the definition of done for the whole project.

## Step 4 — Source-repo cutover (ONLY after Step 3 passes)

Per-skill, one commit each — never en masse. For each moved skill, replace the source
`SKILL.md` body (keep frontmatter name/description) with a pointer to the plugin. Order:
bbs-sourcing, ca-form-filler, obs-form-filler (global `~/.claude/skills`) → price-list-cleaner,
contract-discount-loader, family-rollup (bbs-database) → product-page, brand-page-builder
(bbs-shopify) → le-lane-tuning, supply-lane-tuning (bbs-quote-bot). See plan Task 20 in
`docs/superpowers/plans/2026-07-22-bbs-ops-plugin.md` (this repo).

Any skill that turns out to belong to `bbs-foundations` (company-wide, not site-only) stays
put and is flagged for the foundations plan — do not point it here.

## Known gaps logged for /bbs-review (not blockers)

- `bbs-sourcing` skill references companion `references/` files (vendor directory, email
  templates, triage, input-handling) that don't exist in any source; add them or trim the refs.
- `ca-form-filler` expects a vendor-profile JSON created on first-run; not shipped.
- `image-pipeline` is a documented stub — codify the Sirv/Firecrawl workflow into a real script.
- `family-rollup` depends on the unmerged bbs-database branch `feature/nonapparel-family-expansion`.
