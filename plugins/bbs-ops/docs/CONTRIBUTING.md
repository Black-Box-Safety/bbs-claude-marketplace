# Contributing to bbs-ops

1. Scope a change to one pipeline stage; write testable acceptance criteria (Tom's gate).
2. Keep it grounded — no path lets the bot assert an ungrounded fact (Arthur's rule).
3. Skills are copied here from source repos during the transition (copy-not-cut). Until cutover, change a skill HERE and, if it also lives in a source repo, keep them in sync or cut the source over to a pointer (see the plan's migration phase). After cutover, this plugin is the only home.
4. Run `/bbs-review` before shipping. Fold every finding back into a skill, `site-wiring-map`, or an agent — never leave it in chat.
5. Model IDs: `claude-opus-4-8` / `claude-sonnet-5` / `claude-haiku-4-5` only.
