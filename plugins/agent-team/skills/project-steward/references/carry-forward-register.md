# Carry-forward register — `docs/pm/carry-forward-register.md`

The durable home for **forward-looking** items: not wrong now, will be wrong later, surfaced by a
review and deliberately deferred. It exists because "deferred" findings otherwise live in a session
doc nobody reopens, and because a status list without rules rots while still feeding a dashboard.

## Rules (the block at the top of the file)
1. **Append-preferred.** Never delete. Resolution is a status change with the date and the PR;
   supersession names what replaced it. The history is the value.
2. **The steward writes it; anyone may propose.** Owners may mark their own items RESOLVED with the
   PR — the one write the steward does not gate, because cheap resolution stops ossification.
3. **Every entry has a trigger, and triggers are checked, not remembered.** At charter review the
   steward reads the register for entries the outgoing charter would fire and inlines them.
4. **Severity earns its place.** `blocking-later` (the program breaks when the trigger fires) ·
   `important` (real rework) · `watch` (know about it). Past ~20 OPEN the register is absorbing
   work that should be scheduled: promote the top items into session tasks.
5. **Not a backlog.** Scheduled work with a phase and owner belongs on the board/plan. This is for
   items with **no other home** — that is the entry test.
6. **Stale-checked every reconcile.** An entry whose evidence line no longer resolves is RESOLVED
   or wrong; both need an edit.
7. **Numbers assigned at merge, never at file time.** Parallel branches cannot allocate from one
   append-only file. A session files `CF-NEW-<slug>` in its PR body; the number is assigned when the
   steward's ledger PR carrying the entry merges in the home repo, and the steward then rewrites the
   placeholder in the originating PR's body and in any merged file that cites it.
8. **Security findings live in their own ledger** — same entry shape as below plus a hard rule that no
   credential value ever appears in it — and are indexed here with a pointer line, never duplicated.

## Entry schema (every field required — an entry without *why it matters later* is not an entry)
```markdown
### CF-<nn> · <title>  —  OPEN | RESOLVED <date, PR> | SUPERSEDED by CF-<mm>
- **What:** <the condition, concretely>
- **Why it matters later:** <the future failure, in one or two sentences>
- **Owner:** <roster name>
- **Severity:** blocking-later | important | watch
- **Trigger:** <the event that makes this urgent — "when X is wired", "when row count passes N">
- **Evidence:** <file:line, PR, query>
- **Filed:** <date, by, from which review/session>
```

## Register health line
Each reconcile appends one line at the top of the open section:
`> **Register health — <date> (<steward>, <context>): <N> OPEN by delta** — <resolved ids (PRs)>; <filed ids>; <promotion note if over ~20>.`
