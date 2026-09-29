---
name: marketing-intake
description: >-
  Open a Black Box Safety marketing piece. Interview the rep, pick one track,
  check every needed fact against the claims registry, and write the program
  brief. Use when someone asks for a one-pager, leave-behind, sell sheet,
  flyer, line card, punchout card, brochure, or campaign email and no program
  folder exists yet. Stops when the brief is written. Do not use to write
  copy, render a PDF, price a hot list, or send email.
requires: []
---

# Marketing intake

Layer 2 for the first stage. One job: produce a brief the next stage can trust.
Stop when `01-intake/output/brief.md` exists. Do not write a headline into the piece.

## Inputs

| Layer | File |
|---|---|
| 1 | `${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/AUDIENCES.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/tracks/ROUTING.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/CLAIMS.md` (the rows the piece will need, not the whole file if you can name them) |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/COMPLIANCE.md` section 9, for the tier |

A bridge piece also reads both track files, and only then. An MRO piece does not open
`references/tracks/public-safety.md`.

## Process

1. Ask, from the requester, one or two questions at a time when the answer is not
   already in what they said: who it is for (a persona in `AUDIENCES.md`), the single
   ask, the account, the piece type, where it will be seen, and which facts it needs.
   If the request already answers these, confirm them in the brief instead of re-asking.
2. Pick one track from `ROUTING.md`. The test is who wears or uses the item and which
   vehicle pays, not the catalog category. When the request is genuinely undecided,
   use `mro-procurement` and say so in the README.
3. Check each needed fact against `CLAIMS.md` before any headline. No row means
   `NEEDS CLAIM: <description>` in the brief. That blocks render. It does not block
   writing the brief.
4. Set the tier from `COMPLIANCE.md` section 9. Tier B is any new claim, new named
   reference customer, new agency mark, new certification wording, or a first piece
   for an agency Black Box Safety has not published to. Tier B records
   `approved-by: PENDING` until a person gives a name and a date.
5. Create the program folder on the marketing desk:
   `MARKETING/bbs-marketing/programs/YYYY-MM-DD-short-slug/`.
   If that `programs/` directory is not in the workspace, ask the rep to point at the
   marketing desk. Do not invent a machine path and do not create a folder under
   `Customers/`.

## Outputs

Write these files and then stop.

`README.md` frontmatter and a short why:

```markdown
---
track: mro-procurement
tier: B
approved-by: PENDING
piece-type: capability-one-pager
date: YYYY-MM-DD
---

# <account> <piece type>

## Why this piece exists

<one paragraph from the requester>

## Facts

| Need | Claim id | Status |
|---|---|---|
| <what the piece must be allowed to say> | <id from CLAIMS.md, or NEEDS CLAIM> | ready / blocked |
```

`track:` is one of `mro-procurement`, `public-safety`, `bridge`. A missing `track:` is a
failure. `--scope agency` applies when the piece names an agency, carries an agency mark,
addresses agency personnel, or is handed out for that agency. Say in the README when it
does not apply.

`01-intake/output/brief.md` is the edit surface. Same facts as the README, plus the one
sentence the buyer must remember and the one ask. The rep may edit this file. The next
skill reads whatever they leave there.

`01-intake/CONTEXT.md` is this file's Inputs, Process, and Outputs, so the folder explains
itself.

## Worked example

`MARKETING/bbs-marketing/programs/2026-08-13-uc-irvine-capability-onepager/README.md`
is a brief whose ask rejected the usual parity wedge. Read it when the ask might not be
"same catalog, now it counts." Do not copy its sentences into a new piece. Do not
overwrite that folder.

## Report and stop

Tell the rep the folder path, the track, the tier, and any `NEEDS CLAIM` line. Copy is
`sales-one-pager`. An email is `campaign-email`. A hot-list page is `grainger-promo-page`
in `bbs-sales`.
