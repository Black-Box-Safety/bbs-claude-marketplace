# Wrapper template — `<repo>/.claude/agents/<name>-<lane>.md`

The wrapper makes the teammate selectable from a repo. It is a **pointer**; the role doc is the
single source of truth. Duplicating role-doc content here guarantees drift.

```markdown
---
name: <name>-<lane>
description: Use this agent for <the lane, in this repo's concrete terms — name actual routes,
  tables, directories>. Trigger on <the situations that should dispatch it>.
model: <tier from the program profile; must match the roster row>
tools: Read, Edit, Write, Glob, Grep, Bash   # read-only owners drop Edit/Write
---

Full role spec: `<path to the role doc>` — read it first. It is authoritative; this file is only
a pointer so the agent is selectable from this repo.

<Two or three load-bearing constraints, one line each — the ones that prevent damage if the spec
goes unread. E.g. "This repo is the SOLE migration writer for the shared DB." · "Read-only:
evidence and findings, never fix PRs." · "Token-only color, no hardcoded hex.">
Reports to <steward name>. Sticky to this <slice|surface> across sessions. Lands draft PRs per this
repo's standards — branch, verify, review, Conventional Commit titles.
```

## Rules
- `description` is the dispatch trigger: concrete nouns the orchestrator can pattern-match.
- `tools` follow autonomy posture; never grant more than the role doc allows.
- The closing block matches sibling wrappers verbatim (adapt slice/surface and read-only variant).
- One wrapper per repo the teammate edits. Read-only repos get none.
- Done-proof: the agent appears as a selectable type in a session from that repo.
