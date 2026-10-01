# How to extend the toolkit

The toolkit grows because people push it. You cannot break the company by exploring — the
two rails stay on while you do (see `aup-rails.md`).

## 1. Teach it your voice (personal, encouraged)

Run `/bbs-my-voice` once. That builds a personal `<first>-voice` skill from your real Sent
Items into **your own** `~/.claude/skills/`. It is yours (phone, signature, tells) and is
**never** committed to a shared repo. Re-run when your writing changes.

This is the **only** intentional "personal skill in `~/.claude/skills/`" path at BBS.

## 2. Log when Claude is wrong

One line in the folder's `FLAGS.md`. Catching a mistake means review worked; monthly
triage turns entries into shared fixes everyone gets.

## 3. Ask for a new shared tool

If Claude can almost do something but not quite, say so in the Teams sales channel in one
line — what you wanted, what happened. A missing tool is a request, not a dead end.

For something that should help the whole company, Parker (or a PR into this marketplace)
adds it to a plugin. **Do not** copy a shared BBS skill folder into `~/.claude/skills/` —
that fork goes stale and silently disagrees with the company copy.

## 4. Describe a workflow you repeat

If you explain the same job to Claude twice, that job wants to be a skill. You do not have
to be technical: write how you do the job well (inputs, steps, what "done" looks like,
what must never be guessed). Ask Claude to draft it with `skill-creator` (reaches reps only
through the additive marketplace load described in the marketplace repo, so it may be absent
on some machines). The house rules for a skill live in the marketplace repo's `AGENTS.md`,
"When the work is a skill" — it does not ship with the plugin; Parker applies them in review. Send
the draft to Parker as a PR (or a Teams message) for review — not through
`bbs-claude-md-forge`, which only writes and audits `CLAUDE.md` files — so shared skills
land in the marketplace, not as a private copy of a company playbook.

## 5. Propose an outside tool (commons)

Generally useful third-party plugins are pinned, never copied. Parker / the commons path
(the marketplace repo's `docs/COMMONS.md`, often `/bbs-commons-add` when available) runs the safety checks and
stops at a PR. Things that need a personal API key stay out.

## What "extend" is not

| Do | Don't |
|---|---|
| Personal voice via `/bbs-my-voice` | Copy `bbs-sales` skills into `~/.claude/skills/` |
| FLAGS.md + Teams one-liner | Bypass send denials or invent prices to "make it work" |
| PR / Parker for shared playbooks | Vendor (hand-copy) Anthropic or commons code into the repo |
| Experiment above the rails | Turn off managed settings or ask Claude to send mail |
