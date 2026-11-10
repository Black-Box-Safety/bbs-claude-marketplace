# Procedure as data — a chain file and a dispatcher (start only when ≥2 repos share conventions)

The smallest version is one TOML file and one ~20-line skill. No script required.

## `chains.toml` — the order of operations for a kind of session
Skill ids below are illustrative; substitute the skills you actually have installed.
```toml
# steps: "skill: <id>" (invoke before continuing) · "check: <cmd>" (run; continue only if green) · "do: <convention>"
[chains.feature]
repo = "<repo>"
description = "Build or change an app feature"
steps = [
  "skill: <planning skill id>",
  "skill: <plan-writing skill id>",
  "skill: <test-first skill id>",
  "check: <repo verify command>",
  "skill: <review skill id>",
  "do: update docs in the SAME PR",
  "do: draft PR (Conventional Commit title)",
]

[chains.session-close]
repo = "any"
steps = [
  "skill: <verify-before-done skill id>",
  "do: append the learnings-ledger entry for your lane",
  "do: write the handoff if work continues next session",
]
```

## The dispatcher skill (`roster-dispatch`)
"Confirm which repo you are in. Pick the chain from the task (table of task → chain). Read that chain in
`chains.toml` and walk the steps in order: INVOKE a `skill:` step before continuing; RUN a `check:` and
continue only if green; DO a `do:` step. Never substitute a skill because it is close enough; never
skip a check and claim done. Write only the repo you are in. After the last step, walk `session-close`."

## Rules that keep it honest
- Every skill a chain names must resolve on every machine: installed from a pinned marketplace
  entry, or a skill the program's own plugin ships. Never copy a third-party skill into the
  repo; a vendored copy stops receiving upstream fixes.
- A tool counts as adopted only when it has been chartered and piloted on one contract; a name in a
  TOML is not a decision. Anything unused 30+ days is marked UNUSED or deleted.
- The repo's own `CLAUDE.md` wins over the chain file if they disagree; fix the chain in the same PR.

## If you later build a harness repo
When several repos consume the same chains, move `chains.toml` to its own repo with one profile per
consumer and a drift check that CI runs; build it when drift actually bites, not before.
