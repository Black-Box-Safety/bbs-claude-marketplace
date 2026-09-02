<p align="center">
  <img src="https://img.shields.io/badge/scope-what%20the%20whole%20company%20stands%20on-051c2c" alt="Company-wide foundations">
  <img src="https://img.shields.io/badge/skills-1-b19800" alt="1 skill">
  <img src="https://img.shields.io/badge/CLAUDE.md-150%20lines%2C%20hard-0b3d5c" alt="150-line cap">
</p>

# bbs-foundations

The plugin for what the whole company stands on, as opposed to any one job. `bbs-website`
maintains the website; `bbs-sales` runs the California quote desk. This one carries the
rules both of them inherit, and the first of those rules is how to write the file Claude
reads before it reads anything else.

Fourteen BBS repos and one SharePoint tree already have a `CLAUDE.md`. They were written
by hand over a year, mostly by one person, and they drifted: two different LPA numbers for
the same contract, a claim of SB certification BBS does not hold, model IDs three releases
old, an `@` import chain that looked wired and loaded nothing. Every one of those is a
question a teammate eventually has to ask Parker. This plugin exists to stop asking.

**Jump to:** [The skill](#the-skill) · [Setup](#setup) · [Command](#command) · [The rules that don't bend](#the-rules-that-dont-bend) · [What's planned](#whats-planned)

## The skill

| Skill | Fires when | Stops at |
|---|---|---|
| `bbs-claude-md-forge` | Anyone asks to create, audit, fix, or sync a `CLAUDE.md` in a BBS repo or customer folder; a folder has no `CLAUDE.md` and an agent keeps re-deriving the same facts; a file is over 150 lines or contradicts another repo | A file under the cap, chained correctly, with zero checker failures and every fact pointing at its system of record |
| `bbs-voice-template` | A teammate wants Claude to draft email that sounds like *them*, not like a chatbot; someone asks to "make my own voice skill" or to strip AI tells from a draft | A personal `<first>-voice` skill in their own `~/.claude/skills/`, built from their real sent mail, never committed to a repo |

Its H1 is **BBSClaudeMDForge**. It wraps the `claudeforge` engine and Anthropic's
`claude-md-improver` without copying either — both update on their own — and supplies what
they do not know: four BBS kinds of place (a code repo, a plugin, a private data vault, and
a customer folder on OneDrive that is not git at all), the 25 rules that recur across BBS
repos, the exact strings, and a deterministic checker that fails on a wrong LPA number the
same way it fails on a broken link. If neither tool is installed, everything here still
works.

## Setup

Nothing beyond the marketplace. Optional, and worth it:

```bash
/plugin install claudeforge@bbs-claude-marketplace   # cap enforcement, chain repair, /sync-claude-md
```

The skill-bus subscriptions in `hooks/skill-bus.json` inject the BBS doctrine whenever
this skill, any `claudeforge` skill, or Anthropic's `claude-md-improver` runs. Wire them
once with `/skill-bus:onboard`, or let `/bbs-onboard` do it.

## Command

| Command | Does |
|---|---|
| `/bbs-claude-md [init\|audit\|sync] [path]` | Runs the checker, decides the kind of place, drafts or repairs from the matching template, hands cap and chain repair to `claudeforge` if present. Nothing is written until you say go; nothing is committed. |
| `/bbs-my-voice [first-name]` | Samples your real Sent Items, fills the voice profile with you, and writes a personal `<first>-voice` skill into your own `~/.claude/skills/`. Never touches a repo. |

## The rules that don't bend

**150 lines, hard, no warning threshold.** Over it, split into a sub-file and chain. A
README is measured in words, not lines — different artifact, `github-standards` owns it.

**`@` imports load only at column one.** `**Chain:** @utah/CLAUDE.md` looks wired and loads
nothing. The Bechtel Sentinel tree shipped that way and the link checker reported "0
references" — which is the tell. Root imports children; children import `@../CLAUDE.md`
so a session started in a subdirectory still gets the universal rules.

**Cert language follows the channel.** SDVOSB for federal and primes; OSDS SB/DVBE
`2009473` for California state, where the 5% SB preference and the DVBE incentive apply on
competitive solicitations and never on LPA orders or storefront copy. The checker fails a
federal-context file that makes a DVBE claim.

**Point, never copy.** Money is in Business Central, catalog in Supabase, documents in
SharePoint, BBS form values in `~/.bbs/vendor_profile.json`. A fact stated twice drifts;
the sweep found the MRO LPA number written two ways in 106 places.

## What's planned

The spec reserved this plugin for three things; this release ships the first. Still to
come, each its own plan: the MCP connector roster the team relies on (Grainger, Business
Central, Microsoft 365, Supabase, Shopify, ca-procurement-intel) with a degrade-gracefully
contract for skills that reference them; and AI-literacy onboarding for a team that is
not native with AI. `bbs-grounding-doctrine` now lives here as the spec said it would;
`bbs-website` still carries a copy under a "migrates" note until its subscriptions are
repointed.

---

<sub>Part of the Black Box Safety plugin marketplace. Sibling to <code>bbs-website</code> and <code>bbs-sales</code>. Black Box Safety, Inc. · SDVOSB / CA DVBE · El Cajon, CA.</sub>
