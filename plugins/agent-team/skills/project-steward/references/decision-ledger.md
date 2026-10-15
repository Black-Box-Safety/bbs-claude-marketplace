# Decisions ledger — `docs/pm/DECISIONS.md`

Maintained by the steward. Each entry is a locked decision with its rationale and evidence so the
"why" survives the people and sessions that made it. Reversing one is a deliberate act with its own
entry, not drift. **Newest first.**

## Entry shape
```markdown
## D<nn> — <date> · <one-line title stating the decision, not the topic>

**Decision (<who ruled>, <date>, verbatim where possible; recorded by <steward> <date>).**
<The ruling in plain prose. Numbered where it answers several questions.>

**Why.** <Rationale and the evidence it rests on — file paths, numbers read this run, the brief it answers.>

**What this ruling does and does not move.**
- **Gates:** <none | which, and how>
- **Access:** <none | narrows/widens what>
- **Schema:** <none | what returns as its own decision>
- **Sequencing:** <unchanged | what changed>

**Supersedes / amends:** <D-ids, or none>
```

## The candidates section (top of file)
`## Candidates — recorded by the steward, NOT decided (the principal rules; a candidate binds nothing)`
Each candidate states the question, the proposed clause, the evidence, **what the principal knows
that the record does not**, and the steward's recommendation. A candidate is how you avoid inventing
a ruling while still moving the thinking forward. It becomes a D-entry only when the principal rules.

## Rules
- Record a ruling the same day it is given, verbatim where you can.
- Never write a D-entry for something the principal has not actually said. "He would probably say
  yes" is a candidate.
- A locked decision is cited by id in charters and role docs; it is not re-argued in a PR thread.
- Reversal = a new entry naming the old one, with the evidence that changed.
