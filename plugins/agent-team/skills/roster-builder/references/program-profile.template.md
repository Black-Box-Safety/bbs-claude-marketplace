# Program profile — `docs/pm/PROGRAM-PROFILE.md`

The one file that carries every program-specific noun the `roster-builder` and `project-steward`
skills need. The skills hold the principles; this file holds the names. Fill every slot; where a
slot is genuinely empty, write `none` rather than leaving it blank, so a reader knows it was
considered.

```markdown
# Program profile

## Program home repo
- **Repo:** `<the one repo that holds this profile, the ledgers, the roster, handoffs and charters>`
- **Program docs path inside it:** `docs/pm/` (every `docs/pm/…` path in the two skills means this repo)

## Principal
- **Name / handle:** <the human who decides; the steward reports to them>
- **How they review:** <e.g. "merges from a business brief, not a diff" | "reads the diff">
- **Decisions only they make (never invented by an agent):** <list — e.g. live sends, production writes, destructive git, schema applies, scope reorderings>

## Steward authority
- **Merge delegated to the steward:** yes | no  (if yes: only after the review loop, with the repo's checks re-run and real output shown)
- **Standing exclusions even when delegated:** any PR that crosses a gate, changes access or settings, applies schema, or carries a secret; destructive git; overturning a merge
- **Repos the steward session must have attached:** all of the above — a steward that cannot see a repo reports `unknown` for it, never a guess

## Repos (one line each: name · what it owns · what must never appear in it)
- `<repo-a>` · <e.g. the web app; owns all DB migrations> · <e.g. no tenant/customer names>
- `<repo-b>` · <e.g. the agent runtime, evals, program docs> · <…>
- `<repo-c>` · <e.g. the control plane: registry, runbooks> · <…>

## Human gates (actions code must never take on its own; name the tool or write that each one guards)
- **Gate 1 — <name>:** <e.g. sending anything to an outside party> · lifted only by: the principal's recorded ruling, on <named evidence: eval pass-rate, captured outcomes>, one autonomy rung at a time (manual → approve-each → approve-sample → auto)
- **Gate 2 — <name>:** <e.g. deleting or overwriting customer records> · lifted only by: <…>
- **Gate 3 — <name>:** <e.g. publishing to a public channel> · lifted only by: <…>
- *Lifted is not crossed.* Code never decides to skip a gate; a ruling moves the rung.

## Model tiers (current IDs only — the retired-ID list is a lint, not a memory; if the
## program already keeps a generated model list, point at that file here instead of re-keying IDs)
- Steward / hardest long-horizon seat: `<id>`
- Every other teammate: `<id>`
- Retired IDs that must not appear anywhere: `<id>`, `<id>`

## Where things live
- Roster table: `<repo>/<path>/ROSTER.md`
- Role docs: `<repo>/<path>/roles/`
- Role-doc house spec: `<repo>/<path>/roles/_ROLE-STYLE.md`
- Decisions ledger: `<repo>/docs/pm/DECISIONS.md`
- Carry-forward register: `<repo>/docs/pm/carry-forward-register.md`
- Security ledger (findings with no credential values, ever): `<repo>/docs/pm/security-ledger.md` or `none`
- Learnings ledger: `<repo>/docs/LEARNINGS.md`
- Status board (if any): `<repo>/<path>`
- Harness (profiles/chains/dispatch), if any: `<repo-or-path>`

## The one metric
- **What success is, in one number read from the data store:** <e.g. "X shipped per week">
- **Where it is read:** <table/query/report>

## Sequencing the principal has locked (do not reorder without them)
- <e.g. A → B → C>

## Scope fence (never relitigate; restate in every charter that borders them)
- <e.g. "no mobile app"; "<domain> permanently out of scope">

## Repo standards digest
- Branch → draft PR → review → squash-merge → delete branch; never commit to the default branch.
- Conventional Commit titles. Docs update in the same PR as the change.
- No secrets in any repo. <other hard rules>
```
