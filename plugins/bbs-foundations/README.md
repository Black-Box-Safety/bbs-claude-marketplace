<p align="center">
  <img src="https://img.shields.io/badge/scope-what%20the%20whole%20company%20stands%20on-051c2c" alt="Company-wide foundations">
  <img src="https://img.shields.io/badge/skills-3-b19800" alt="3 skills">
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

Nothing beyond the marketplace if your machine already receives the org's managed settings —
`docs/bbs-managed-settings.json` is that file, and [`docs/MANAGED-SETTINGS.md`](docs/MANAGED-SETTINGS.md)
explains every block. Optional, and worth it:

```bash
/plugin install claudeforge@bbs-claude-marketplace   # cap enforcement, chain repair, /sync-claude-md
```

The plugin's own hook (`hooks/hooks.json`, a `PreToolUse` hook on the Skill tool) injects
the BBS doctrine whenever this skill, any `claudeforge` skill, or Anthropic's
`claude-md-improver` runs, and the grounding doctrine whenever a `bbs-foundations`,
`bbs-sales`, `bbs-claude-coach` or quote-bot lane-tuning skill runs. The text lives in
`hooks/doctrine/*.md` and the subscriptions in `hooks/doctrine/subscriptions.json`; nothing
to wire — it is active the moment the plugin is installed. Interpreter: pwsh 7 if present,
else Windows PowerShell 5.1, else python3 (`hooks/doctrine.py`, same logic). A Mac needs
nothing beyond the Xcode command-line tools.

A second hook keeps customer folders documented. When a session starts in, or Claude
writes a file in, a folder under `MASTER/Customers/<customer>/`, it checks for a
`CLAUDE.md` between there and the customer root. None: Claude is told to create one with
this skill before it finishes (once per customer per session on writes). One there, at
session start: Claude is told to keep it current. The text lives in
`hooks/customer-folder/`; `customer-folder.ps1` and `customer-folder.py` are the same
logic, proven byte for byte by `hooks/tests/customer_folder_parity.py`. The managed
`claudeMd` states the same rule, so it holds on a machine where no hook runs.

## Command

| Command | Does |
|---|---|
| `/bbs-claude-md [init\|audit\|sync] [path]` | Runs the checker, decides the kind of place, drafts or repairs from the matching template, hands cap and chain repair to `claudeforge` if present. Nothing is written until you say go; nothing is committed. |
| `/bbs-my-voice [first-name]` | Samples your real Sent Items, fills the voice profile with you, and writes a personal `<first>-voice` skill into your own `~/.claude/skills/`. Never touches a repo. |
| `/bbs-workspaces [discover\|request\|custom]` | Finds BBS folders on **this** computer and writes VS Code workspaces for them (quote desk, web, admin, or a custom set of folders you already have). Puts a logo'd launcher on the Desktop. |

## The rules that don't bend

**150 lines, hard, no warning threshold.** Over it, split into a sub-file and chain. A
README is measured in words, not lines — different artifact, `github-standards` owns it.

**`@` imports load only at column one.** `**Chain:** @utah/CLAUDE.md` looks wired and loads
nothing. The Bechtel Sentinel tree shipped that way and the link checker reported "0
references" — which is the tell. Root imports children; children import `@../CLAUDE.md`
so a session started in a subdirectory still gets the universal rules.

**Cert language follows the channel, and so does small-business status.** SDVOSB for
federal and primes, where BBS **is** a small business under SBA size standards; OSDS
**DVBE** `2009473` for California state, where BBS is **not** a small business (state SB
revenue threshold exceeded) and the 5% SB preference is never claimed. The DVBE incentive
applies on competitive solicitations and never on LPA orders or storefront copy. The
checker fails a federal-context file that makes a DVBE claim. Reasoning: `canonical-facts.md`, "Small-business status is channel-dependent".

**Point, never copy.** Money is in Business Central, catalog in Supabase, documents in
SharePoint, BBS form values in `plugins/bbs-sales/references/vendor_profile.json`. A fact stated twice drifts;
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
