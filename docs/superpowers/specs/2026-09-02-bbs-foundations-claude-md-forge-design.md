# bbs-foundations / BBSClaudeMDForge — Design

**Owner:** Parker Marshall (BBS) · **Date:** 2026-09-02 · **Status:** shipped in this PR

## Problem

Fourteen BBS repos and one SharePoint tree carry a `CLAUDE.md`. A read-only sweep of all
of them (2026-09-02) found 25 rules that recur and 19 places where the files contradict
each other or the owner-locked canonical facts: the MRO LPA written `7-25-51-02.03` in 96
places and `7-25-52-02.03` in 10; "5% SB preference" in one file and "BBS is NOT
SB-certified" in another; `claude-opus-4-5` in production config; two different skills both
named `ca-rfq-intake`; a customer-folder import chain that looked wired and resolved zero
references. Each one is a question that routes to Parker.

The generic tools — the `claudeforge` engine and Anthropic's `claude-md-improver` — enforce
a line cap and a quality rubric. Neither knows a BBS fact, and neither has a template for
a customer folder on OneDrive, which has RFQs and reps-and-certs forms instead of a
`package.json`.

## Goal

One skill that writes, audits, and repairs CLAUDE.md files the BBS way, in the plugin the
`bbs-ops` spec reserved for company-wide foundations, such that a teammate who is not
Parker gets the same file Parker would write — and a machine check catches the drift a
human reviewer misses.

## Non-goals

- Replacing `claudeforge` or `claude-md-improver`. Link, don't vendor (the `bbs-ops` rule;
  `github-standards`: a pinned marketplace source beats a hand copy).
- Writing READMEs (`github-standards`) or email (`parker-voice`).
- The other two foundations deliverables (MCP roster, AI-literacy onboarding). Separate plans.
- Fixing the 19 contradictions in their home repos. This PR records the rulings; the fixes
  are per-repo PRs.

## Design

**Plugin:** `plugins/bbs-foundations/` — manifest, README, one skill, one command, skill-bus
hooks, onboarding doc. Marketplace entry appended (the reserved slot); `PLUGINS.md` moved
from "planned" to live.

**Skill:** `bbs-claude-md-forge` (machine name; kebab-case like every other skill in the
fleet — the audit's worst failure is two things with one name). H1 **BBSClaudeMDForge**.
Body under 2,000 words; detail in `references/`:

| Reference | Carries |
|---|---|
| `bbs-doctrine.md` | The 25 recurring rules, grouped, each with its source repo and strongest phrasing |
| `canonical-facts.md` | Exact strings, cert-by-jurisdiction, vehicles, systems of record, signers, model IDs, and a ruling on every contradiction found |
| `templates.md` | Four kinds of place: `code-repo`, `customer-folder`, `plugin`, `data-vault`; section lists and skeletons; the length rules stated once |
| `checklist.md` | Every mechanical check with the real defect that earned it |
| `worked-example.md` | The Bechtel Sentinel tree, including its two mistakes |

**Checker:** `scripts/check_claude_md.py`, stdlib only. Fails on: >150 lines; unresolved
`@` import or markdown link; inline `@` import; sandbox `/mnt/` paths; secret-shaped
strings; placeholders; stale model IDs; wrong LPA number; SB claim; DVBE in a
federal-context file. Warns on: missing maintenance footer; duplicate headings; unchained
children; missing parent import; stale banner dates; San Diego as HQ; em-dash density.
Exit 1 on any FAIL. This is the enforcement that works with nothing else installed.

**Enforcement via skill-bus:** `bbs-claude-md-doctrine` insert, `pre`, subscribed to this
skill, every `claudeforge*` skill and command, `claude-md-management:*`, and
`revise-claude-md`; `monitorSlashCommands` on so typed commands fire it too.
`bbs-grounding-doctrine` moves to its final home here (the `bbs-ops` spec said it would);
`bbs-ops` keeps its copy under the existing "migrates" note until its two subscriptions
are repointed in a follow-up.

**Dependency posture:** references `claudeforge`, `claude-md-improver`, `github-standards`,
and `parker-voice` by name; degrades gracefully when absent (Arthur's rule). The
ClaudeForge fork `Black-Box-Safety/ClaudeForge` is added to this marketplace as a pinned
external plugin so it is one install away and there is one marketplace for the team.

## Decisions

1. **150 lines, hard, no warning threshold** — Parker's call on 2026-09-02, applied to the
   local `claudeforge` install; recorded here so the fork can match.
2. **Line-one `@` imports both directions.** Children import the parent so a session
   started in a subdirectory gets the universal rules; Claude dedupes the cycle.
   Deep-dive bid files are linked, not imported.
3. **Public-record facts only in the skill.** UEI, DVBE number, LPA numbers — what Parker
   prints in his email signature. FEIN, seller's permit, buying account numbers stay in
   `~/.bbs/vendor_profile.json`.
4. **`github-standards` and `parker-voice` stay where they are** (Parker's machine).
   Moving them into foundations is a real decision about Grace's standard; flagged, not made.

## Success criteria

- Checker returns zero FAIL on the Sentinel tree and catches the known defects when they
  are reintroduced.
- Checker run on the sweep clones flags the known contradictions (`bbs-agent` model ID,
  `ca-quote-hub` SB claim) without false FAILs on the strong files (`bbs-database`,
  `bbs-shopify`).
- `skill-bus simulate bbs-foundations:bbs-claude-md-forge` shows the doctrine firing.
- A teammate who is not Parker runs `/bbs-claude-md init` on a repo with no CLAUDE.md and
  gets a file that passes the checker without asking anyone. That is the acceptance gate.
