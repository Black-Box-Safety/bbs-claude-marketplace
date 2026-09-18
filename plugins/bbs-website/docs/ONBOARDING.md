# Onboarding — maintaining the BBS website

You don't need to be an AI expert. Open [`workspace/bbs-web.code-workspace`](../../../workspace/bbs-web.code-workspace) first (replace `REPLACE-REPOS-ROOT`, or run `scripts/install-desktop-launchers.sh`). Then run `/bbs-onboard` and follow it. In one sitting you should:

1. Read the `site-wiring-map` (three repos, two sync gaps, task→skill→agent table). The web workspace also includes `bbs-customer-bots`, the multi-tenant Gear Assistant that is a sibling of the production quote bot.
2. Confirm the skill-bus guardrails are wired (the command does this).
3. Meet the agent roster — who to call for what.
4. Do the real test: run `/bbs-add-product` on one product and see it render as a card + PDP.

If you finished #4 without asking Parker, the plugin did its job. If you got stuck, note where and run `/bbs-review` so the gap gets fixed in the docs — that's how this stays a living tool.
