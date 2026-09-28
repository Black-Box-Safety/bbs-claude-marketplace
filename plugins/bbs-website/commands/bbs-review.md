---
description: Run Arthur (architecture) and Tom (delivery/quality) against recent changes, and write findings back into the plugin so it improves like the site.
---

# /bbs-review

The continuous-improvement pass. Keep the plugin sharpening itself.

1. **Scope** — determine the repo and the recent changes to review (`git diff`, recent commits, or a range the user names).
2. **Dispatch reviewers in parallel:**
   - `arthur` — architecture: the deterministic/generative boundary, tool/API-route contracts, model routing + escalation, grounding, prompt-cache, Supabase/RLS + proxy security.
   - `tom` — delivery/quality: acceptance criteria, prompt/knowledge governance, eval coverage, production-readiness, onboarding/legibility.
3. **Check doctrine coverage** — read `hooks/doctrine/subscriptions.json` and list this plugin's skills; any `bbs-website:*` skill that no subscription pattern matches is a coverage gap. Add the missing subscription to that table (the text stays in `hooks/doctrine/*.md`).
4. **Write findings back** — do not leave a finding in chat. Update the relevant skill, `site-wiring-map`, or an agent. Architecture findings go to Arthur's areas, delivery to Tom's.
5. **Report** — summarize what changed and what was deferred, with the reason.
