# Two skills for running a long program with a team of Claude agents

Two companion skills, company-neutral, distilled from a working multi-repo program. Install the
plugin from the marketplace and fill in one profile file.

**Runtime assumption.** Written for Claude Code sessions that can spawn child sessions and be woken
by pull-request events (the web or remote product). On a local terminal a "child session" is a
separate terminal session or a subagent, and the check-in and wake rules in the steward skill do
not apply.

**Words these skills use**

- **Principal** — the one human who decides; the steward reports to them and never invents their rulings.
- **Steward** — the single planning agent; plans, charters, reviews, keeps the ledgers. Never builds product code.
- **Owner / teammate** — a named agent that builds one lane and lands draft PRs.
- **Lane** — one owner's mission, in a sentence. A **slice** is a lane that is one pipeline stage or product
  column; a **cross-cutting** lane is one horizontal concern (database, security, UI coherence) across slices.
- **Human gate** — an action only a person may take (sending to an outside party, a production write). Code
  never crosses one; a recorded ruling may lift one rung at a time.
- **Charter** — the fenced, single-task prompt the steward writes for one owner's session.
- **Carry-forward register** — the program-wide list of "not wrong yet, will be" items, each with a trigger.
- **Opening gap list** — the dated list of concrete gaps an owner ships with; its first work queue.

| Skill | What it does | Invoke when |
|---|---|---|
| `roster-builder` | Builds and maintains a **roster** of named, lane-owned delivery agents: lane pin-down, grounding scans, a house-spec role doc with an opening gap list, one roster table, thin per-repo wrappers, optional harness chains. | "We need someone who owns X", "set up a team", "charter / refresh an agent". |
| `project-steward` | Runs as the **one steward**: plans and sequences, chunks work into session tasks for named owners, writes fenced charters, runs the bounded review loop, keeps the ledgers (decisions, carry-forward register, learnings, facts, board), hands off with a launch prompt. | "Be the steward", "what runs next", "review this PR against its charter", "hand off". |

## Install

```
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace
/plugin install agent-team@bbs-claude-marketplace
```

To try it before installing: `claude --plugin-dir ./agent-team` (this session only). The skills
answer to `/agent-team:roster-builder` and `/agent-team:project-steward`. Do not copy the skill
folders into a repo's `.claude/skills/`: a copy stops receiving fixes.

## Adopt

Install as above, then follow the five-step **Adoption order** in `roster-builder/SKILL.md`: fill the
program profile (the only place your company's nouns go), create the three ledgers, commit the
role-doc spec, charter a minimum viable roster, launch the first steward session.

## The principles both skills encode (why this works)

- **Orientation beats capability.** What an agent reads first, what it may touch, what it must never
  do, and who it hands to matter more than which model it runs.
- **Names and lanes.** One sticky owner per lane makes dispatch legible to a human in ten seconds.
- **Grounded, dated, bounded.** Role docs assert only what a scan found; every owner ships with a
  numbered register of real gaps and reports deltas against it.
- **Procedure as data.** Which skills load and in what order a session runs are lookups, not judgments.
- **One steward, fenced children.** The steward plans, reviews and keeps ledgers; children deliver one
  draft PR each and never merge, edit ledgers, or spawn a steward.
- **Ledgers with rules.** A decision ledger (never invent the principal's rulings), a carry-forward
  register with triggers and a cap, an append-only learnings ledger, a per-session facts ledger.
- **Bounded review.** Independent blind seats, one synthesis, adjudication as a conversation, one fix
  round.
- **Humans hold the gates.** Code never crosses a gate; a gate may be lifted only by a recorded ruling.

## What was deliberately left out

Anything tied to one product's domain, stack, or people: pipeline stage names, specific tools and
connectors, database runbooks, a particular dashboard, and the originating program's own decisions
and scar tissue. If your program needs those, they belong in your profile, your role docs, and your
own decisions ledger, not in these skills.
