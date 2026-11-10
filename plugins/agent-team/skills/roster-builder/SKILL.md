---
name: roster-builder
description: >-
  Stand up and maintain a roster of named, lane-owned delivery agents for a multi-repo program run
  with Claude Code. Pins each agent's lane, grounds it in real repo scans, writes its role doc to
  a house spec with a dated opening gap list, adds one roster row, writes thin per-repo wrappers,
  and wires the skills and session chains it should walk. Use when the user says "we need someone
  who owns X", "charter an agent for Y", "set up a team of agents", "add a teammate", "our
  subagents are generic and nobody knows who does what", "bring in expertise from a catalog", or
  asks to review or refresh an existing agent's charter. Company-neutral; every program-specific
  noun comes from docs/pm/PROGRAM-PROFILE.md, never from this skill. Do NOT use to run the
  program once the roster exists (that is project-steward), to hand a sales territory or
  account book between people, or to write a CLAUDE.md.
requires: []
---

# Roster Builder

Turns a pile of generic subagents into a **team**: one durable, named owner per lane, each
grounded in the real repos, each with a bounded work queue, all coordinated by one steward
(see the companion `project-steward` skill). The output is not "an agent" — it is a roster
that a human can read in ten seconds and say *"Dee has the database; Val audits; the steward plans."*

A **lane** is one owner's mission in a sentence; a **human gate** is an action only a person may
take. Generic catalog agents carry neither, so nobody dispatches them; this skill makes named,
grounded owners instead (the principles are in the package README).

## Setup — the program profile (do once)

This skill never names a company, a person, a repo or a gate. Those live in one file the adopter
fills in: `docs/pm/PROGRAM-PROFILE.md` (template in
[references/program-profile.template.md](references/program-profile.template.md)). It names the
principal (the human who decides), the repos and what each owns, the human gates (actions code
must never take alone), the model tiers in use, the lint-enforced boundaries, and where the roster,
role docs and ledgers live. **If the profile does not exist, create it first** — ask the user for
the slots you cannot infer from the repos, and do not guess the gates.

## Adoption order (day 0, once)

1. Fill the program profile in the home repo.
2. Create the three ledgers there with their rules blocks: `DECISIONS.md`, `carry-forward-register.md`,
   `LEARNINGS.md` (schemas in `${CLAUDE_PLUGIN_ROOT}/skills/project-steward/references/`:
   `decision-ledger.md`, `carry-forward-register.md`, `learnings-ledger.md`). Start the roster from [references/roster-template.md](references/roster-template.md).
3. Commit [references/role-doc-spec.md](references/role-doc-spec.md) as `<roles-dir>/_ROLE-STYLE.md`.
4. Charter the minimum viable roster below.
5. Launch the first steward session from the `project-steward` launch template with an empty handoff.

## Minimum viable roster (read before chartering anyone)

Chartering is expensive and the temptation is to charter everything. Do not. Start with:

1. **One steward** (`project-steward` skill) — plans, sequences, reviews, keeps the ledgers.
2. **Three to five slice owners** — one per pipeline stage or product surface that has a real
   backlog *today*.
3. **One or two cross-cutting owners** only where a horizontal concern already bites: usually
   the database/migration lineage and a read-only security auditor.

Charter the next owner when a lane has ≥3 concrete gap-list items nobody owns — not because the
org chart looks incomplete. A roster of twenty before the product has users is scaffolding; a
roster of six that ships is a team.

## The workflow

### Step 1 — Pin the lane (prerequisite, not paperwork)

Establish, via AskUserQuestion when the user hasn't said, and confirm back in one block:

1. **Lane** — the single mission, one sentence, owned *end to end*.
2. **Shape** — a numbered **slice** (one pipeline stage / product column) or an unnumbered
   **cross-cutting** surface (serves every slice on one horizontal concern: UI coherence,
   schema, security, observability, workspace).
3. **Overlap check (binding)** — read every current charter in the roster. If ≥50% of the proposed
   lane sits inside an existing owner's charter, recommend extending that owner, say so, and
   stop unless overruled.
4. **Repos** — which it edits; which it only reads. Wrappers go only in repos it edits.
5. **Autonomy posture** — unattended-safe work vs draft-PR-only vs read-only. Name the human
   gates that border the lane. A read-only auditor never fixes in place; a builder lands draft
   PRs; nobody crosses a gate.
6. **Model tier** — from the program profile's current list only; never a retired or dated ID.
7. **Name** — one common first name, ideally alliterative with the lane. Check for collisions.

### Step 2 — Ground it (scans, not priors)

Dispatch read-only Explore subagents to map the lane's actual surface — routes, tables,
contracts, tests, configs. Require **real file paths** and a list of loose ends. The loose ends
become the **opening gap list**: numbered, dated, each item citing file:line, each with a
severity. A teammate without a gap list starts every session searching for purpose.

If distilling from a catalog agent: read it for topic coverage, then write from scratch. Never
copy its text, its handshake rituals, or its model pins.

### Step 3 — Author the role doc

Write `<roles-dir>/<name>-<lane>.md` to the house spec in
[references/role-doc-spec.md](references/role-doc-spec.md) (first person, senior voice, ~150–220
lines, the required sections in order). Gate it with
[references/role-doc-checklist.md](references/role-doc-checklist.md). Three things the checklist
exists for because each was missed once:

- **Skill-id verification, both directions.** A wired id that doesn't resolve silently never
  fires; a vendored on-disk path a reviewer flags as "unresolvable" is a false positive. Check
  the session listing *and* the disk.
- **Fact verification.** Every version, count, status or date comes from a source read this
  session — never from a sibling role doc, which may itself be stale.
- **The gap-list loop.** The owner keeps its opening gap list versioned, reports what changed
  since last session, and closes an item only with proof (a merged PR, a passing probe, a
  screenshot). A fixed list that a human edits is what makes an agent improve measurably instead
  of auditing open-endedly.

### Step 4 — Roster row + wrappers

- **Roster table** (`<roster-file>`, shape in [references/roster-template.md](references/roster-template.md)):
  one row — number (or `—` for cross-cutting), lane, name, model, primary repos — plus a role-doc
  link and a one-line charter with chartering date and provenance. Match the existing rows' voice.
- **Wrapper** in each repo it edits: `<repo>/.claude/agents/<name>-<lane>.md`, ~12 lines, per
  [references/wrapper-template.md](references/wrapper-template.md). Frontmatter `description` is
  the dispatch trigger: concrete nouns from that repo, not abstractions. `tools` follow autonomy
  posture (read-only auditors drop Edit/Write).

### Step 5 — Wire procedure (harness as data)

If the program has a harness (profiles + chains + a dispatch command), add what the lane needs:
the skills its repo profile should load, and a **chain** for the session kind it will run most
(ordered `skill:` / `gate:` / `do:` steps). If there is no harness yet, start the minimal one in
[references/harness-shapes.md](references/harness-shapes.md) — one chain file and a dispatcher
skill — only when ≥2 repos share conventions. One repo does not need a bus.

### Step 6 — Land it

One branch + draft PR per repo touched; Conventional Commit titles
(`feat(agents): charter <name>-<lane>`); bodies cross-reference companions and state: the lane,
why it exists, how it was grounded (name the scans), what was verified (skill ids, facts), and
what was deliberately not done. Done-proof: the wrapper shows up as a selectable agent type in a
session from that repo; the roster row renders; the checklist passes.

### Step 7 — Shakedown (the eval)

Offer, never run unprompted: dispatch the new agent on one small, real item from its gap list and
read the result like a reviewer. Did it read its role doc, stay in lane, honor the gates, produce
the five-part answer (workload type · inputs · output contract · failure behavior · autonomy
posture)? Fix the **doc**, not the transcript, where it drifted — same PR.

## Refreshing an existing teammate

Same skill, shorter path: re-scan the lane, diff reality against the doc's gap list and facts,
re-verify skill ids both directions, re-stamp dates, land one draft PR. Roster-wide refresh: one
read-only reviewer across all role docs comparing "Skills I use" against the installed surface,
then apply only verified findings.

## Three standing loops every owner inherits

- **Learnings ledger.** Read your lane's section of `docs/LEARNINGS.md` at session start; append
  a dated, lane-tagged entry at session end (pattern that worked, assumption the data corrected,
  alternative parked with when-to-revisit, process miss). Append, never rewrite; strikethrough +
  pointer when superseded. A team that re-derives its taste each session is N strangers.
- **Capability check at prompt-read.** Before the first action, enumerate the skills and connected
  tools the session actually has and map the charter to them. Before shelling out or saying "I have
  no credentials", check whether a connected tool already does the job.
- **Work in unison.** One owner per lane, but a single-owner session is a starting point, not a
  fence. When a task needs another lane's judgment, spawn that owner as a subagent wearing their
  role or charter them through the steward. Human gates are never delegated away.

## What NOT to do

- Don't install catalog agents wholesale. Don't charter without the lane pinned.
- Don't state a fact you didn't read this session; don't cite a file you didn't open.
- Don't charter a new owner to avoid extending an existing one.
- Don't wire a skill you didn't verify resolves; don't purge one you didn't verify is dead.
- Don't let the wrapper drift from the role doc.
- Don't grow the roster ahead of the backlog.
