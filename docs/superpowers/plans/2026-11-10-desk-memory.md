# Desk memory — plan

Spec: `docs/superpowers/specs/2026-11-10-desk-memory-design.md`. One slice per session, in
dependency order. Each ends at a draft PR reviewed by Rex.

## Slice 1 — capture one line, see it next session, not next door (this PR)

- `plugins/bbs-sales/hooks/desk-memory.py` and `.ps1`, registered on SessionStart.
- `plugins/bbs-sales/skills/desk-remember/` (`SKILL.md`, `scripts/desk_memory.py`:
  `where`, `add`, `show`).
- Desk template, buyer template, intake skill and plugin README say what `LEARNED.md` is.
- bbs-sales 0.7.0 > 0.9.0 (PRs #75 and #77 each take 0.8.0).

Tests:
`python3 plugins/bbs-sales/skills/desk-remember/scripts/test_desk_memory.py` (writer, refusals,
the save-then-show loop, isolation, format agreement between writer and both hook halves) and
`python3 plugins/bbs-sales/hooks/tests/desk_memory_parity.py` (hook halves agree). Both in CI.

## Slice 2 — reach the session that opens at the desk root; tidy

Depends on PR #75 being on `main` (its PostToolUse first-write path and once-per-session
marker) and on the ruling in spec Open for Parker 3.

- First touch of a buyer folder in a session (first Read, Write or Edit under it) injects that
  buyer's `LEARNED.md` chain, once per buyer per session. Build it into the existing
  PostToolUse hook entry rather than adding a second process per tool call.
- `desk_memory.py retire` (move a replaced line to `LEARNED-archive.md`) and `merge` (fold a
  OneDrive conflict copy back in); the hook says when a conflict copy exists.
- If ruled: `desk_memory.py` on the `bbs-fill` allow list, skill switched to `bbs-fill`.

Tests: parity cases for the PostToolUse path (shown once, not for a sibling, not twice);
writer tests for retire and merge; `test_bbs_fill.py` still green.

## Slice 3 — the monthly roll-up (the recursive half)

- `desk_memory.py digest --root <tree>`: wider-marked notes, statements recurring across
  buyers, `FLAGS.md` rows by skill and bucket with repeats first. Read-only; one page out.
- `desk_memory.py promote`: one line up, lower lines archived with where they went; refuses
  without an approver's name.
- A Parker-facing skill for the review, and `docs/ADMIN-RUNBOOK.md` pointing the monthly
  flag triage at it. REGISTRY standing task gets its tool.

Tests: a synthetic tree with planted repeats; digest finds exactly those; promote leaves one
line above and none below; a second promote of the same line is a no-op.

## Slice 4 — decay

- Hook marks notes older than 12 months (both halves, `BBS_TODAY` pinned in tests, as PR #75
  does). Writer asks for a tidy past 40 entries. Digest lists notes past 18 months.

Tests: parity with a pinned date on both sides of each threshold.

## Slice 5 — templates and the precedent rule

Depends on PR #72 being on `main`.

- `bbs-foundations` forge templates carry the settled-file / landing-file pattern for a
  customer desk; `scaffold_folder_context.py` leaves `LEARNED.md` alone and says so.
- The stay-in-this-buyer's-folder rule goes into the skills that search past packets
  (`naspo-quote` precedent mining), with the "label every row with its folder" clause.
- Score the "remember that ..." routing queries (added in slice 1) on a machine with auth.

Tests: both checkers; `test_mine_precedents.py`; the routing eval on a machine with auth.

## Outside this plan: the NASPO at-cost stop

The refusal table is a floor. The lasting control for a Grainger markup on a California state or
NASPO quote is a deterministic at-cost stop in `bc-quote-entry` (#68) and the same check in
`bbs-quote-builder`. It belongs to those skills, is not part of desk memory, and is not built.
Until it is, do not narrow the markup category in `REFUSE_TABLE`.

## Slice 6 — a second desk, only when one asks

A profile in `DESKS` and a second tree name in the hook pair. Not built until a desk exists
that wants it.
