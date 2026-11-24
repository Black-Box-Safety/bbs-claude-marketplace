# bbs-desk

One file: `output-styles/bbs-desk.md`, an output style named **BBS Desk**.

Claude Code's standard instructions are written for software engineering. One person at
Black Box Safety uses it for that. Everyone else quotes, buys, bills and supports customers.
This plugin makes a session start as an operations teammate without the rep doing anything.

## What it does

The style is **forced** (`force-for-plugin: true`): while this plugin is enabled, every
session uses it, and a person's own `outputStyle` setting does not override it. It tells
Claude to:

- settle the job, the customer or deal folder, and the system of record before answering;
- run scripts and lookups quietly and report what was produced, not how;
- answer in business words, lead with the answer, mark what is missing;
- never debug at a rep: say what broke and the line to send Parker;
- not build software mid-job.

It holds no company fact. Prices, certifications, signatures and sends stay governed by
company memory (the managed `claudeMd` block), the folder's `CLAUDE.md` and each skill.

## What it does not do

- It is an instruction, not a guard. Anything that must happen every time is a hook.
- It does not reach subagents (Sal, Brenda and the rest keep their own instructions).
- Per Anthropic's output-styles page, a custom style drops Claude Code's built-in software
  engineering section only where the full system prompt is in use; on the shorter prompt
  there is no such section to drop. Which prompt a rep's default model gets has not been
  confirmed here.

## Turning it off

Disable the plugin. Tested 2026-11-24 on Claude Code 2.1.331: a project `outputStyle`
setting does **not** override a forced plugin style; disabling the plugin does. A session
started inside a source-code repository is told to do engineering work properly, so the
style is safe there, and that exception is what a maintainer's coding session relies on.

Managed settings enable this plugin for everyone (Parker, in session, 2026-11-24). Managed
`enabledPlugins` locks a plugin on, for Parker too, so the off switch is that row in
`bbs-foundations/docs/bbs-managed-settings.json`, not a setting on one machine.

---

Owner: Parker Marshall. Last verified 2026-11-24.
