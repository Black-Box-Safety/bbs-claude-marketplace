---
description: Onboard a team member to the BBS site pipeline — walk the flow and roster, wire the skill-bus guardrails, and point at the wiring map.
---

# /bbs-onboard

Welcome a new maintainer. Do these in order:

1. **Invoke the `site-wiring-map` skill** and summarize it for the user: the three repos, the two sync gaps, and the task→skill→agent table.
2. **Confirm the skill-bus is active.** Check for `.claude/skill-bus.json` in the working repo. If the BBS doctrine subscriptions are not present, run the `skill-bus:onboard` skill to wire them from this plugin's `hooks/skill-bus.json`, then confirm with `skill-bus:list-subs`.
3. **Walk the agent roster** (from the plugin README): the seven pipeline agents (catalog-intake, pricing-contracts, product-enrichment, storefront-pages, quote-bot, data-qa, cross-sell), plus the reviewers arthur, tom, and business-review — one sentence each on when to call them.
4. **Give the first task:** invite the user to run `/bbs-add-product` on a real product and watch it reach a card + PDP. Tell them this is the success test: they should complete it without asking Parker.
