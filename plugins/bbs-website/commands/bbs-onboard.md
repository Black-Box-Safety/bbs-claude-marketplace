---
description: Onboard a team member to the BBS site pipeline — walk the flow and roster, confirm the doctrine hook is live, and point at the wiring map.
---

# /bbs-onboard

Welcome a new maintainer. Do these in order:

0. **Confirm they opened `workspace/bbs-web.code-workspace`.** If they are still in the quote-desk folder or a single repo, point them at `workspace/README.md` and stop until Shopify, the database, the quote bot, and customer-bots are in the same window.
1. **Invoke the `site-wiring-map` skill** and summarize it for the user: the three repos, the two sync gaps, and the task→skill→agent table. Mention `bbs-customer-bots` as the multi-tenant sibling of the production quote bot.
2. **Confirm the doctrine hook is live.** Read this plugin's `hooks/hooks.json` and `hooks/doctrine/subscriptions.json`; confirm the two doctrine files it names exist, and that an interpreter resolves on this machine — `pwsh`, `powershell`, or `python3` (`Get-Command` / `command -v`; the hook tries them in that order). There is nothing to wire — the hook is active whenever the plugin is loaded. If none resolves (a Mac without the Xcode command-line tools' `python3` and without `brew install powershell`), say so: the skills run without their guardrail text until one is installed.
3. **Walk the agent roster** (from the plugin README): the seven pipeline agents (catalog-intake, pricing-contracts, product-enrichment, storefront-pages, quote-bot, data-qa, cross-sell), plus the reviewers arthur, tom, and business-review — one sentence each on when to call them.
4. **Give the first task:** invite the user to run `/bbs-add-product` on a real product and watch it reach a card + PDP. Tell them this is the success test: they should complete it without asking Parker.
