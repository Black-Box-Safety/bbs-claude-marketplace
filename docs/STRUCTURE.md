# Structure — where a new thing goes

The placement guide for this repo. It answers one question: *I have a new thing; where does
it live so that it exists exactly once?* It points at the rules; it does not restate them.
Invariants are in [`AGENTS.md`](../AGENTS.md). Review questions and the branch and version
rules are in [`MAINTAINER-GUIDE.md`](MAINTAINER-GUIDE.md) §3 and §4.

---

## 1. Placement

Work down the table and stop at the first row that fits.

| You have | It goes | Because |
|---|---|---|
| A fact (price rule, cert, form ID, signer, contract number, model ID) | Its one home in the `AGENTS.md` table. Everything else points at it | Invariant 2. A second copy goes stale |
| A ruling from Parker | One dated entry in the rulings register in [`STEWARD.md`](STEWARD.md), quoting Parker, in the PR that acts on it | Rex holds any PR that changes a binding fact without one |
| Something learned about one customer, buyer or agency | The desk folder tree on SharePoint, never this repo | Customer knowledge is data, and buying-account numbers ride on it |
| The same job for a different customer, form or agency | A **profile inside the existing skill** | Sibling skills compete on descriptions and can silently pick wrong; profiles route on document content |
| A new job a rep asks for in their own words | A **skill**, in the plugin whose desk owns the job | Skills are chosen by description; one job, one skill |
| An order or gate over skills that already exist | A **command** in that plugin | A command sequences; it carries no domain facts of its own |
| Something that must happen every time, whether or not Claude remembers | A **hook** in the plugin's `hooks/`, PowerShell and Python twins with a parity test | A rule in prose is a request. A hook is a control |
| A named expert with a lane, used by reps | A plugin agent in `plugins/<plugin>/agents/` | Plugin agents ignore `hooks`, `mcpServers` and `permissionMode`; if it needs those it is not a plugin agent |
| An agent that builds, reviews or maintains this repo | `.claude/agents/` | It ships to no rep machine |
| A script a skill runs | That skill's `scripts/`. Run through `bbs-fill` if it fills a form | Deterministic work belongs in code, and the allow-list is how it runs without a prompt |
| A tool written by someone else | A pin in `marketplace.json`, through [`COMMONS.md`](COMMONS.md) | Pin, never vendor |
| A design for a build | `docs/superpowers/specs/` then `docs/superpowers/plans/`, both dated | The PR cites them; once the last slice ships, they move to `docs/archive/superpowers/` |
| A dated finding or audit | `docs/assessments/` | It records what was true that day and is not updated |
| A whole new **plugin** | See §2. The answer is usually no | Every plugin is another version to bump and another install to explain |

## 2. When a new plugin is justified

Add a plugin only when at least one of these is true. Otherwise the work is a skill or a
profile in a plugin that exists.

1. **A different set of people installs it.** `bbs-website` is not on a sales rep's mind.
2. **It guards a different folder tree with its own hooks.** A second desk with its own
   tree is a plugin; a second agency in the same tree is a profile.
3. **It is infrastructure other plugins run through** (`bbs-tools`, `bbs-foundations`).

Size alone is not a reason. `bbs-sales` carries the most skills because one desk does the
most jobs. Split it when rule 1 or 2 becomes true for part of it, not when a count is
reached. A split renames every `plugin:skill` the doctrine hooks match on and needs a
`renames` entry, so it is a ruling, not a refactor.

## 3. The queue

The branch and version rules are in `MAINTAINER-GUIDE.md` §4, "Branches and versions".
These three keep the queue from becoming the problem it was on 2026-11-06, when eleven
open PRs held two duplicate pairs and three claims on one version number.

- **Five open PRs at most.** At five, the next session reviews or closes one before it
  opens another. Review is the scarce step; opening more work does not speed it up.
- **A draft with no push for fourteen days is closed with a one-line reason**, or picked
  up that day. Closing loses nothing: the branch can be reopened from its last commit.
- **Before creating a file, search the open PRs for it.** Two PRs that create the same
  file are one PR too many, and the second one is found at merge time.

## 4. The documents, one job each

| Document | Its one job |
|---|---|
| `AGENTS.md` | Invariants and where facts live. Read by every agent |
| `CLAUDE.md` | What is specific to Claude Code in this repo |
| `README.md` | What the marketplace is and how to install it |
| `REGISTRY.md` | Every BBS repo and asset, one status each |
| `HANDOFF.md` | The one open cutover (account-synced personal skills). Delete when it is done |
| `docs/STRUCTURE.md` | This file: placement |
| `docs/STEWARD.md` | How a work session runs, and the rulings register: what Parker ruled, when, in his words |
| `docs/MAINTAINER-GUIDE.md` | How to review and maintain; branch and version rules |
| `docs/COMMONS.md` | The life of a third-party pin |
| `docs/ADMIN-RUNBOOK.md`, `ADMIN-CLEANUP.md` | What only an admin can do, outside git |
| `docs/REP-SETUP.md`, `CURSOR-SETUP.md` | Getting one machine working |
| `docs/SYSTEM-OVERVIEW.md`, `OPERATING-LAYER.md` | The primer and the pointer map, for a reader new to the system |
| `docs/MEASUREMENT.md` | What is counted and from where |
| `docs/SESSION-HANDOFF-<date>.md` | The latest handoff. Dated narrative, never edited after its day; the previous one moves to `docs/archive/session-handoffs/` |
| `docs/archive/` | Finished specs, plans and old handoffs. History only; nothing live points here as a source of truth |

A new document needs a job no row above already does. If a row does it, edit that file.

---

Owner: Parker Marshall. Last verified 2026-11-10.
