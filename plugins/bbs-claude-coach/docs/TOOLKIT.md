# Your Claude toolkit at BBS — what it is, how to use it, how to make it better

You already use Claude. This explains the *extras* the company adds on top, in plain words,
so you understand what you are working with and feel free to push it further. It is not a
rulebook and it is not about control — it is a shared toolkit meant to make your job easier
and to grow as you find new uses for it.

**Prefer talking it through?** In Claude, run `/bbs-explain-claude` (what the pieces are),
`/bbs-what-can-i-do` (what you can do by job), or `/bbs-start` (one first step for the work
in front of you). Those commands ship in the `bbs-claude-coach` plugin, next to this file.

At BBS one person keeps the toolkit consistent so every machine works the same way and gets
improvements automatically. The setup script Parker posts in Teams (one for a Windows PC,
one for a Mac) installs the tools and every plugin, and managed settings keep them current;
you don't install or update anything by hand. You just use it — and tell us when it should
do more.

## The five kinds of tools, in plain words

You do not need to memorize these. But knowing what each one *is* means you understand what
Claude is doing instead of it feeling like magic.

- **Skill** — a playbook Claude follows for a specific job. You do not call it; Claude
  notices the job and uses it. "Log this RFQ," "price these Grainger items," "make a brand
  page" each trigger a skill.
- **Command** — a shortcut you type, always starting with `/`. It kicks off a job on
  purpose. `/bbs-checkup` checks your setup; `/bbs-my-voice` teaches Claude to write like you.
- **Plugin** — a bundle of related skills and commands for one area (the quote desk, the
  website, company foundations). Installing a plugin gives you everything inside it.
- **Connector (MCP)** — a live link to a real system so Claude reads real data instead of
  guessing: Business Central for orders and invoices, Grainger for pricing, Outlook and
  Teams for your mail and messages.
- **Hook** — something that runs quietly in the background. Ours mostly injects the company
  rules into a job so the guardrails are always there without you thinking about them.

## What you can do with it, by the job in front of you

Everyone gets the whole toolkit. Roles at a small company overlap — the same person might
scout a supplier in the morning, quote an agency at noon, and build a one-pager at night —
so nothing is locked to a "desk." Use whatever the task needs.

The job map itself lives in one place, `../skills/bbs-claude-coach/references/jobs-map.md`,
which is what `/bbs-what-can-i-do` reads, so the table you get from Claude and the table
in this guide can never disagree. Run that command, or open the file.

If you are not sure what is possible, ask Claude "what can you help me with here?" — it can
see its own tools and will tell you.

## Two rules that never bend — and everything else is yours

These two exist to protect you, not to limit you:

1. **Claude drafts; you send.** Every quote, price, email, and form is a draft until you
   review it and send it yourself. Claude cannot send on its own — that rail is on for
   everyone by design.
2. **Never an invented number.** No price, stock, lead time, or certification from memory or
   the open web. If Claude does not know, it flags it rather than guessing.

Above those two rails, **experiment freely.** Try new prompts, new workflows, new uses. You
cannot break the company by exploring, and the rails stay on while you do.

## Make it better — this is yours to extend

The toolkit grows *because* people push it. You are invited to:

- **Teach it your voice.** Run `/bbs-my-voice` once and your drafts stop sounding like a
  chatbot.
- **Ask for a new tool.** If Claude can almost do something but not quite, say so in the
  Teams sales channel in one line — what you wanted, what happened. That is how the toolkit
  grows; a missing tool is a request, not a dead end.
- **Log it when Claude is wrong.** One line in the folder's `FLAGS.md`. Catching a mistake
  is the system working — it turns into a fix everyone gets.
- **Build your own skill — you already have the tool for it.** If you find yourself
  explaining the same job to Claude twice, that job wants to be a skill. Ask Claude to use
  **`skill-creator`**: it interviews you about how the job works and writes the skill for
  you — no technical background needed, just describe how you do your own work well.
  (`skill-creator` reaches reps only through the additive marketplace load described in
  the marketplace repo's `docs/COMMONS.md`, so it may be absent on some machines.) The house
  rules a skill must follow live in the marketplace repo's `AGENTS.md`, "When the work is a
  skill" — it does not ship with the plugin; Parker applies them in review. Send the draft to Parker as a PR
  (or a Teams message) for review — not through `bbs-claude-md-forge`, which only writes
  and audits `CLAUDE.md` files — and if it helps everyone, Parker folds it into the shared
  toolkit so the whole team gets it.

When something you built or asked for turns out to help everyone, it gets added to the
shared toolkit so the whole team gets it.

## How the toolkit reaches you and stays current (for Parker)

Everything a machine runs is decided in exactly two places, so "supply the team" is two
levers, not a scramble:

- **The content** — every skill, command, plugin, and hook — lives in this repository
  (`bbs-claude-marketplace`). Change it with a branch and a reviewed PR; when it merges,
  every registered machine picks it up automatically. Nothing is copied between computers.
- **The policy** — which plugins are on, which connectors each person has, the company
  memory, and the two rails — is pushed once from the Claude admin console (**Managed
  settings**, on our Teams plan). It cannot be overridden on a rep's machine, and it
  refreshes on its own, so a change reaches everyone without anyone reinstalling anything.

External tools made by other people are **pinned** (referenced at a fixed version), never
copied in, so they keep getting their authors' fixes. Add one with `/bbs-commons-add`, which
walks the safety checks and stops at a PR. Connectors (Business Central, Grainger, Outlook,
Teams) are assigned per person from the console — that is the one place role differences
live, and it is fine for a person to have several.

Reps do none of this. They run `/bbs-checkup` once to confirm their toolkit is healthy, and
`/bbs-checkup` prints the exact sentence to send Parker if anything is off.

---
Owner: Parker Marshall. A plain-language companion to the marketplace repo's
`docs/REP-SETUP.md` (mechanics) and `docs/ADMIN-RUNBOOK.md` (admin steps), which do not ship
with the plugin. Lives inside `bbs-claude-coach` so a rep's install carries it. Last verified 2026-09-24.
