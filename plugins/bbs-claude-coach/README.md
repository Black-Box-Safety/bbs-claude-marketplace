<p align="center">
  <img src="https://img.shields.io/badge/scope-understand%20%C2%B7%20start%20%C2%B7%20extend-051c2c" alt="Understand, start, extend">
  <img src="https://img.shields.io/badge/skills-1-b19800" alt="1 skill">
  <img src="https://img.shields.io/badge/for-everyone%20at%20BBS-0b3d5c" alt="For everyone at BBS">
</p>

# bbs-claude-coach

The empowerment plugin. It does not quote an agency or fill a form — `bbs-sales` and the
other job plugins do that. This one helps you **understand** the toolkit, **start** whatever
job is in front of you, and **extend** it when you find a gap.

Everyone gets the whole toolkit. Roles at BBS overlap, so nothing here is locked to a desk.

**Jump to:** [Commands](#commands) · [Skill](#skill) · [The two rails](#the-two-rails) ·
[Human reading path](#human-reading-path)

## Commands

| Command | Does |
|---|---|
| `/bbs-what-can-i-do` | Shows what Claude can help with, by the job in front of you |
| `/bbs-start` | Given what you are about to do, picks the first concrete step |
| `/bbs-explain-claude` | Plain-language explanation of skills, commands, plugins, connectors, hooks |

## Skill

| Skill | Fires when |
|---|---|
| `bbs-claude-coach` | Someone asks what they can do with Claude here, how the toolkit works, how to start a job, how to extend it, or what the safety rails mean — without asking you to run a quote or fill a form |

## The two rails

Protection, not control:

1. **Claude drafts; you send.**
2. **Never an invented number** (price, stock, lead time, cert). Unknown gets flagged.

Full one-pager: `bbs-foundations` → `docs/AUP.md`.

## Human reading path

[`docs/TOOLKIT.md`](docs/TOOLKIT.md) is the plain-language house guide. These
commands are the interactive version of the same idea.

## Setup

On a managed machine Parker enables `bbs-claude-coach@bbs-claude-marketplace` in managed
settings (same place as the other BBS plugins). Until then:

```text
/plugin install bbs-claude-coach@bbs-claude-marketplace
```

No connectors required — this plugin teaches and routes; the job plugins need the live
links (Business Central, Grainger, and so on).

---

<sub>Spec: `docs/superpowers/specs/2026-09-17-bbs-claude-coach-design.md` · Owner: Parker
Marshall · Last verified 2026-09-24.</sub>
