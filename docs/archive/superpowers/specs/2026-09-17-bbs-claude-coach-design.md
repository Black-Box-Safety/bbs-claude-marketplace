# bbs-claude-coach + plugin-github expert — Design

**Owner:** Parker Marshall (BBS) · **Date:** 2026-09-17 · **Status:** implementing in this PR

## Problem

BBS's ~9-person team has embraced Claude. Almost everyone except Parker is non-technical,
and roles overlap: the same person may cold-outreach, quote, build a one-pager, scout a
supplier, and chase an invoice in one week. The marketplace already ships job plugins
(`bbs-sales`, `bbs-website`, `bbs-back-office`, `bbs-foundations`) and a plain-language
house guide (`docs/TOOLKIT.md`). What is missing:

1. A **reusable build stance** for anyone (agent or human) who designs or reviews Claude
   plugins and GitHub work in this repo — so Parker can re-invoke the expertise without
   re-deriving it.
2. An **interactive coach** that turns TOOLKIT.md into something a teammate can *run*
   (`/bbs-what-can-i-do`, `/bbs-start`, `/bbs-explain-claude`) instead of only read —
   organized by **job to be done**, not by desk or role gate.

`bbs-foundations` PLUGINS.md already reserved "AI-literacy onboarding" as a planned
deliverable. This is that deliverable, as its own plugin so literacy coaching does not
compete with doctrine/forge skills inside `bbs-foundations`.

## Goals

1. **Understand the house** — what a skill, command, plugin, connector (MCP), and hook
   are, in plain words; drafts vs sends; where truth lives.
2. **Start any overlapping job confidently** — given the work in front of someone, name
   the plugin / command / skill / connector that helps, without inventing desk walls.
3. **How to extend** — personal voice skills the right way, propose commons additions,
   ask for shared skills, never teach hand-copies of shared skills into `~/.claude/skills`.
4. **Light AUP protection** — the two rails (humans send; never invent numbers) as
   protection, not control culture. Point at `plugins/bbs-foundations/docs/AUP.md`.

## Non-goals

- Replace or re-route `bbs-sales` / form / pricing work.
- Re-key `vendor_profile.json`, `ca-form-rules.md`, or canonical facts.
- Teach personal copies of shared BBS skills into `~/.claude/skills/` (voice profiles are
  the one intentional exception, owned by `bbs-voice-template`).
- Enterprise RBAC, role-gated plugin walls, or desk silos.
- Merge this PR (session ends at draft PR).

## Design

### Part A — Expert agent (repo-local, not shipped to reps)

**Path:** `.claude/agents/bbs-plugin-github-expert.md`

A durable domain agent Parker (or the steward) re-invokes when designing, reviewing, or
extending Claude Code plugins and the GitHub workflow around this marketplace. Encodes:

- GitHub: branch → PR → review-by-someone-who-did-not-write → merge; conventional
  commits; never force-push; pin-by-SHA (or peeled commit) vs mutable tags; Actions /
  `check_marketplace.py` as the silent-failure gate.
- Anthropic Agent Skills / Claude Code plugins: progressive disclosure; YAML `name` +
  `description` (what + when; <1024 chars; quote colons); lean SKILL.md; references one
  level deep; scripts for deterministic work; `plugin.json` + marketplace entry; commands
  vs skills vs hooks vs agents; pin external, never vendor; marketplace `skills:` lists
  are additive not restrictive (per `docs/COMMONS.md`); validate with `claude plugin
  validate` when available and always `python3 scripts/check_marketplace.py`.
- Org distribution: managed settings inject policy; MCPs are connectors assigned in the
  console, not marketplace plugins.

Negative scope: does not merge its own PRs; does not own commons lifecycle (that is
`commons-curator`); does not rewrite binding-document facts without Parker.

### Part B — Plugin `bbs-claude-coach`

| Piece | Role |
|---|---|
| `plugin.json` | Manifest; category foundations / literacy |
| Skill `bbs-claude-coach` | Fires on "what can I do", "how does Claude work here", "how do I extend", "explain skills vs commands" |
| `/bbs-what-can-i-do` | Job-oriented capability map for the person in front of Claude |
| `/bbs-start` | Given a job description, pick the first concrete step |
| `/bbs-explain-claude` | Plain-language glossary of the five tool kinds + drafts vs sends |
| `references/glossary.md` | Lean definitions; points at `docs/TOOLKIT.md` as the human reading path |
| `references/jobs-map.md` | Job → start here (command / skill / connector); no desk gates |
| `references/how-to-extend.md` | Voice skill, FLAGS.md, propose shared skill, commons via Parker / `/bbs-commons-add` |
| `references/aup-rails.md` | Two rails only; pointer to full AUP — no re-key of cert numbers beyond the standard channel rule already in managed memory |

**Truth-in-one-place rule for this plugin:** interactive coaching copy lives in the
plugin references (what Claude runs). The human reading path stays `docs/TOOLKIT.md`,
which gains a short "run these commands" pointer. Job details (how to fill a form, how
to price) stay in their home plugins — this one only routes.

### Registration

- Append to `.claude-plugin/marketplace.json` and `.claude-plugin/PLUGINS.md`.
- Note in `plugins/bbs-foundations/docs/bbs-managed-settings.json` under
  `enabledPlugins` (Parker must push managed settings for it to reach machines).
- Update root README plugin table / badge counts and `/bbs-checkup` plugin list.
- Do **not** change sales form content or commons pins.

## Decisions

1. **Own plugin, not a foundations skill.** Literacy coaching is a different job from
   writing CLAUDE.md files. Separate plugin keeps selection descriptions from competing.
2. **Name `bbs-claude-coach`.** Clear to non-technical people; avoids colliding with
   `docs/TOOLKIT.md` and with "toolkit" as a metaphor for the whole marketplace.
3. **Organize by job, never by role.** Matches TOOLKIT.md and AGENTS.md small-team reality.
4. **Session ends at draft PR.** Expert agent and steward agree: writer does not merge.

## Done condition

- `python3 scripts/check_marketplace.py` exits 0.
- Expert agent file exists with description + negative scope.
- Plugin validates structurally (manifest, skill frontmatter, marketplace entry).
- Draft PR open against `main`, referencing this spec and the plan.
- If `claude` CLI is absent in the build environment, say so in the PR (do not fake
  `claude plugin validate`).

## Parker actions after merge (out of repo)

1. Add `bbs-claude-coach@bbs-claude-marketplace: true` to live managed settings (this PR
   updates the *template* file).
2. Announce the three commands in the Teams sales channel.
3. Optionally enable for everyone the same way as `bbs-foundations` (recommended — literacy
   is company-wide, not desk-scoped).
