# Spec — the commons as a managed toolbox

*Written 2026-09-16, before implementation. Plan: `docs/superpowers/plans/2026-09-16-commons-toolbox.md`.*

---

## The problem

`docs/COMMONS.md` rules a tier of third-party plugins into the marketplace and then
maintains it by hand. Three things are wrong with that, and all three are the quiet kind.

**1. The refresh procedure does not fit two of the three upstreams.** The ruling says
"quarterly, check each upstream for a newer tag." `anthropics/skills` has **zero tags** —
it is a rolling `main`, so "check for a newer tag" is a no-op that returns clean forever.
`caveman` publishes fast enough that the quarterly cadence is simply too slow: it shipped
`v2.7.0` on 2026-09-14 — **ten days** after the `v2.6.0` release the pin points at, and
**one day** after `COMMONS.md` was last verified. A procedure that
reports "nothing to do" while the pin rots is worse than no procedure, because it is
believed.

**2. The pin is the only thing recorded.** Nothing captures *how* an upstream publishes,
*when* it was last checked, *by whom*, or *by what method*. So every refresh re-derives
all of it, and a refresh that re-derives is a refresh that can re-derive differently.

**3. What a pin selects was never recorded.** The `caveman` entry is described in
`COMMONS.md` as "opt-in terse mode" — singular. The pinned tree ships **20 skills and 6
command files**. Roughly half those skills (`safe-refactor`, `surgical-patch`,
`lean-build`, `investigate-first`, `migration`, `verify-and-stop`, `caveman-commit`,
`caveman-review`, …) are developer-facing and compete for selection against BBS skills in
a rep's session. The ruling and the artifact disagree, and the artifact wins.

The failure mode is this repo's usual one. Nothing crashes. A rep gets a skill nobody
decided to give them, or keeps a pin that a Windows fix has already superseded, and the
first symptom is a wrong document.

## Who this is for

BBS reps. Not technical, on Windows, Microsoft 365. Their day is inbound RFQs, pulling
line items out of PDFs and spreadsheets and screenshots, pricing against vendor accounts,
building quotes, filling California compliance packets, sourcing email, and prospecting.
Every judgement below resolves toward that person, not toward an engineer.

## Design

### A. The commons entry gains a release model

A pin answers *what code*. It does not answer *what to do next quarter*. Each commons
entry additionally records, in `docs/COMMONS.md`:

| Field | What it is |
|---|---|
| **Release model** | `tagged`, `rolling`, or `multi-train` |
| **Train** | for `multi-train`, which tag prefix is authoritative |
| **Cadence** | derived from the release model, not chosen |
| **Provenance** | date verified · method · tag object · peeled commit · verifier |

Cadence follows the model rather than the calendar:

- **rolling** → monthly. There is no tag to wait for; the only signal is commit date.
- **tagged** → quarterly, *unless* the upstream's own tag rate is faster than that, in
  which case it is treated as multi-train and checked monthly.
- **multi-train** → monthly. Interleaved trains mean a release you care about can be
  buried between four you do not.

`caveman` is the worked example. It carries **nine** tag prefixes — `v`, `bin-v`, `cli-v`,
`sdk-ts-v`, `sdk-python-v`, `middleware-ts-v`, `middleware-python-v`, `pi-v`,
`pre-caveman-` — across 54 tags. The authoritative train for the plugin is bare `v`.

### B. Resolution rules that are easy to get wrong

Three mechanical rules, each of which produces a plausible wrong answer when skipped.

1. **Resolve annotated tags to commits.** All three upstreams tag annotated, so
   `git rev-parse v2.7.0` returns the **tag object**, not the code. Recording it yields a
   40-character SHA that exists, looks right, and is not the tree anyone will get.
   `git rev-list -n1 <tag>` is the peeled commit. For `caveman` v2.7.0 the tag object is
   `e6c5e68b…` and the commit is `8b0c1d36…`; nothing about either announces which is
   which.
2. **Sort with `sort -V`, then filter to the train.** Lexical sort puts `v1.9.0` above
   `v1.10.0`. `superpowers-chrome` has both, so this is not hypothetical.
3. **Read `hooks/hooks.json`, not only `plugin.json`.** `obra/superpowers` at `v6.3.0`
   declares no `hooks` key in its manifest and still installs a `SessionStart` hook from
   `hooks/hooks.json`. An agent that checked the manifest alone would conclude the hook
   was gone and silently reverse a standing Parker-only ruling.

### C. What gets diffed at refresh

Not the repository — reps do not receive the repository. Three surfaces:

- **The plugin manifest, especially `hooks`.** A hook runs on every session on every
  machine without anyone installing anything. This is the highest-blast-radius field in
  any third-party tree.
- **The `skills:` paths the entry selects**, and the total skill and command **counts**.
  The count diff is the cheap machine-checkable proxy for scope creep: a jump from 20 to
  30 says "read the changelog" without anyone having to read it first.
- **`LICENSE*` and `LICENSING.md`.** Licenses change between releases, and a split-license
  repo can move a directory across the line.

### D. The three hard filters are re-checked, not grandfathered

API key · license · rep-appropriateness. These are intake filters today. They become
**every-refresh** filters, because an upstream's business model changes faster than its
code. `caveman` grew a hosted, token-gated `proxy/` lane under BSL-1.1 with an explicit
commercial boundary between two quarterly checks. Nothing about the pin bump would have
surfaced that.

### E. The liveness clock

"Quiet for two quarters → fork or drop" needs a defined clock. It is the **last commit on
the default branch**, not the last release. A repo can go six months without a tag and be
under daily development; `anthropics/skills`, with no tags at all, would otherwise be
permanently overdue for a fork decision.

### F. One agent owns the whole lifecycle

`.claude/agents/commons-curator.md`. One agent for one durable domain — the third-party
commons across **evaluate → pin → validate → refresh → retire** — rather than one agent
per task.

It lives in `.claude/agents/` and not in `plugins/*/agents/`, because a plugin agent
silently ignores `hooks`, `mcpServers` and `permissionMode`, and a curator whose tool
surface cannot be constrained is a curator that can merge its own work.

Its negative scope is as load-bearing as its scope: it does not write BBS skills, does not
touch `scripts/check_marketplace.py` (review-side), does not edit managed settings or
hooks, does not merge, and does not move the two BBS forks (`claudeforge`, `impeccable`)
that sit outside commons on moving refs.

## The four changes this design lands

1. **`caveman` → `v2.7.0`.** Not "newer is better." v2.7.0 rewrites both hook commands to
   prepend `HOOK_ROOT=$(printf %s "${CLAUDE_PLUGIN_ROOT}" | sed 's|^/\([a-zA-Z]\)/|\1:/|')`,
   converting an MSYS/Git-Bash `/c/...` path back into `C:/...`. v2.6.0 invokes `node`
   against the unconverted path. **BBS reps are on Windows** and their Bash tool runs
   through Git Bash (`scripts/bbs-setup.ps1` installs `Git.Git` for exactly that reason).
   This is a fix for our platform, which is why the bump is worth taking.
2. **A `skills:` filter on `caveman`** — `./skills/caveman` and `./skills/caveman-help`.
   This aligns the artifact to the 2026-09-13 ruling ("opt-in terse mode"); it does not
   make a new ruling. `caveman-help` is included because it is a one-shot reference card
   with a narrow `/caveman-help` trigger, and a non-technical rep needs to be able to ask
   what the modes are.
3. **`./skills/pptx` added to `document-skills`.** Same commit, no new pin. The reason is
   a dangling pointer, not a capability wish: `bbs-deck-voice`'s own description ends
   *"use the pptx skill for assembly"* — the marketplace ships a skill that points at
   something it deliberately withholds. That is precisely the defect class this repo
   exists to catch, and it is currently being shipped by the repo itself.
4. **`superpowers-chrome` and the `document-skills` SHA are left alone.** Both verified
   current on 2026-09-16. A refresh that changes nothing is a successful refresh.

## The pptx caveat, stated rather than resolved

`pptx`'s own SKILL.md lists its runtime as `pptxgenjs` (npm) · `markitdown[pptx]`,
`Pillow`, `defusedxml`, `lxml` (pip) · **LibreOffice (`soffice`)** · `pdftoppm` (Poppler).

Against `scripts/bbs-setup.ps1`: Node is installed (`OpenJS.NodeJS.LTS`), `uv` is
installed (`astral-sh.uv`), Poppler is installed (`oschwartz10612.Poppler`). **LibreOffice
is not installed and is not listed.** The SKILL.md also assumes `pptxgenjs` is
preinstalled, which is true of Anthropic's sandbox and not of a rep's laptop.

So on a rep machine today: authoring a `.pptx` should work once `pptxgenjs` is fetched;
the **visual-QA and PDF-conversion paths, which go through `soffice`, will not**. Behaviour
was not tested on a rep machine by this session.

This does not block the change — `docx` and `xlsx` already reference `soffice` and already
have the same gap, so adding `pptx` does not introduce it. It does have to be **recorded**,
in the `COMMONS.md` "Watch for" column and in the PR, because `bbs-deck-voice` output is a
customer-facing federal deliverable and silent visual-QA failure on one of those is the
outcome this repo is built to prevent.

## Non-goals

- No BBS skills. `plugins/*/skills/` is untouched.
- No checker code. Commons assertions are proposed in the PR body as follow-up; the
  checker is review-side and a checker written by the thing it validates encodes that
  thing's assumptions.
- No `README.md`, no hooks, no `bbs-managed-settings.json`, no `models.json`.
- No change to the `bbs-sales` description in `marketplace.json`.
- No new upstreams beyond `pptx`. `ComposioHQ/awesome-claude-skills` was evaluated in full
  and yielded zero installable additions; manufacturing one to look responsive would be
  the same failure as manufacturing a price.

## Open questions for Parker

Recorded in the PR body, not decided here: account-synced duplication of `docx`/`pdf`/
`xlsx`/`pptx`, and the apparent misidentification of `mercury-mcp` in `docs/STEWARD.md`.

---

Owner: Parker Marshall. Verified 2026-09-16.
