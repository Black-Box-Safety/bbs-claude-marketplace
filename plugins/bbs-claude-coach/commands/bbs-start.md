---
description: Given the job in front of you, pick the first concrete Claude step at BBS — one clear start, no desk gates. Runs the bbs-claude-coach skill.
argument-hint: "[what you are trying to finish]"
---

# /bbs-start

Run the `bbs-claude-coach` skill in **start-here** mode.

1. If `$ARGUMENTS` is empty, ask: "What are you trying to finish in the next half hour?"
2. Match it to `references/jobs-map.md`. If two rows fit, pick the closer one and say why.
3. Give **exactly one** first step (a `/command` to type, or one plain sentence to ask
   Claude). Name the plugin area and whether a connector is required.
4. Say what they will review before anything leaves the building (the draft / the numbers).
5. Point at `/bbs-explain-claude` if they want the vocabulary, `/bbs-what-can-i-do` for the
   wider map, and `references/how-to-extend.md` if the real need is a missing tool.
6. Do not invent prices, certs, or form fields. Do not send anything.
