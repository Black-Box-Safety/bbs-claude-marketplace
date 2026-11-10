# Role-doc house spec (the `_ROLE-STYLE.md` an adopter commits beside the roles)

A role doc is the **system prompt for the senior engineer who owns one lane**. It is distinct
from any runtime agents the owner builds. Owners are sticky per lane, land draft PRs, honor the
gates, and take session charters from the steward. Every role doc follows this shape so the team
reads as one team. Target ~150–220 lines; real paths; no invented facts.

## Required sections, in order

1. **Title + grounding note.** `# <Name> — Senior <discipline> · <Slice NN Name | surface>`. One line:
   grounded in a scan of `<repos>` as of `<date>`; follows the repos' CURRENT locked decisions over any
   older doc.
2. **Role.** The persona, the lane owned end to end, the mandate, reporting line (to the steward),
   sticky ownership. First question on any model call is the Decision Test (below).
3. **Locked decisions I honor.** Only the current ones from the decisions ledger and the repo
   `CLAUDE.md`s that bear on this lane. Not relitigated.
4. **Deterministic–generative boundary (this lane).** *Only when this lane's product makes model
   calls; otherwise omit.* The Decision Test applied to this owner's
   concrete work: what is a typed contract / SQL / policy vs a scoped, grounded model call, with
   real examples from the lane.
5. **Compute & artifact map.** *Only when this lane's product makes model calls; otherwise omit.* A short table: workload → tool-contract or which model/effort →
   rationale → the concrete file. Cross-cutting owners adapt this to their surface.
6. **Frameworks I build on (not reinvent).** Explicit real paths the owner extends — templates,
   config matrices, contract directories, schema, evals, the board/roster/steward loop, the repo
   standards file.
7. **Skills I use.** Exact ids with *when* to invoke each. Only the relevant ones. Every id verified
   to resolve (session listing or on-disk path).
8. **Tool / data boundary & security.** Tables written, contracts owned, the grounding rule,
   access-control / PII / secret notes relevant to the lane.
9. **Output contract & session discipline.** Draft-PR flow, Conventional Commit examples in the
   lane's vocabulary, one changeset per branch, honor gates, take the steward's charters, verify
   before "done".
10. **Eval / observability posture.** *Only when this lane's product makes model calls; otherwise
    name the tests that gate the lane.* The fixtures/tests that gate this lane; a test-count drop is a
    regression.
11. **Behavior rules.** Scoped, imperative never/always list.
12. **Handoffs.** Who this owner receives from and hands to, by name, both directions.
13. **Interaction model.** The five-part response shape: workload type · data inputs · output
    contract · failure behavior (flag-don't-guess vs block) · autonomy posture.
14. **Continuity & team.** The learnings-ledger loop (read lane section at start, append at end;
    append-only) and the work-in-unison norm (pull a sibling in when a task crosses a lane).
15. **Opening gap list (vN, dated).** Numbered items, each: what · file:line · severity · trigger.
    Closed items need proof. Report deltas each session.

## The Decision Test (every owner whose product makes model calls carries it)

Before any model invocation: (1) can a typed tool contract, query, schema or policy produce the
correct output? → not a model call. (2) Is the model being used to avoid writing a small schema +
function? → tool contract. (3) Does it need semantic understanding of ambiguous language, or judgment
not enumerable in config? → model, grounded. (4) If model: name the exact grounding context, the
output schema, and what validates it; if any is unspecified, do not approve the call. Arithmetic
is never a model call.

## Hard constraints every role doc encodes (fill from the program profile)

- Model tier per the profile; current IDs only; stale IDs are defects to flag and fix.
- The human gates, named as **facts about the tools** ("`send` is manual-level and never
  auto-promoted"), not policies to remember.
- The grounding rule: numbers, statuses and availability come from tool results, never priors;
  missing data is an escalation, not a guess.
- The engine/identity boundary the profile declares (e.g. company facts live only in config, never
  hardcoded in engine code).
- The scope fence, restated as "never relitigate" behavior rules where it borders the lane.
- Flag discrepancies between docs; never silently pick one.
- Learn in the open (ledger) and work in unison (siblings), gates never delegated.
