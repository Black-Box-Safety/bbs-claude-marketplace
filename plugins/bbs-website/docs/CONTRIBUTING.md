# Contributing to bbs-website

1. Scope a change to one pipeline stage; write testable acceptance criteria (Tom's gate).
2. Keep it grounded — no path lets the bot assert an ungrounded fact (Arthur's rule).
3. Skills are copied here from source repos during the transition (copy-not-cut). Until cutover, change a skill HERE and, if it also lives in a source repo, keep them in sync or cut the source over to a pointer (see the plan's migration phase). After cutover, this plugin is the only home.
4. Run `/bbs-review` before shipping. Fold every finding back into a skill, `site-wiring-map`, or an agent — never leave it in chat.
5. Model IDs: `claude-opus-4-8` / `claude-sonnet-5` / `claude-haiku-4-5` only.

## Version policy

The three BBS plugins carry **no version field** in marketplace.json: every push to main
auto-updates every machine (version = commit SHA). This is deliberate — the drift-killer.
Pin a version string only for a deliberate freeze (e.g., during the acceptance pilot), and
remove the pin when the freeze ends. External plugins (claudeforge, impeccable) track branch refs
today (dev, main); pin them to a tag or SHA before rollout. Before any push that changes a
skill: run its eval cases (v1.1 golden-set gate; program metrics live in `docs/MEASUREMENT.md`).
