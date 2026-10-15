---
name: marketing-assets
description: >-
  Decide whether a supplier, customer, co-brand, or certification mark may
  appear on a Black Box Safety piece, using the rights ledger. Use when a
  rep asks to put a logo on a flyer, one-pager, or email. Copies the file
  into the program folder only when the ledger row allows it. Do not use to
  download a logo from the web or to invent permission.
requires: []
---

# Marketing assets

One job: a yes or a no from `references/ASSETS.md`, then a file copy only on a yes.

## Inputs

| Layer | File |
|---|---|
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/ASSETS.md` |
| 4 | The program README, for whether the piece is internal or customer-facing |
| Desk | `brand/assets/logos/` inside `MARKETING/bbs-marketing/` |

If the logo directory is not in the workspace, report the ledger decision and
the filename. Ask the rep to open the marketing desk. Do not fetch a substitute
from the web.

## Decision

Read the row. Apply it in this order:

1. No row. The mark is not used, including a file that is already sitting in
   `brand/assets/logos/`.
2. The row says declined, or the permission cell is `NEEDS CONFIRMATION` or
   `NEEDS WRITTEN CONFIRMATION`. The mark waits. Say which cell blocked it.
3. Internal-only pieces follow the exemption `ASSETS.md` already states. Name
   that exemption in the decision. A customer-facing piece does not get it.
4. A row with a rights basis, an approver, and a date, and none of the wait
   states above, may be copied into the program folder. Copy the file. Do not
   redraw, recolor, crop, or build a new lockup. Grainger lockup rules in
   `references/tracks/mro-procurement.md` still apply when that track is in use.

Customer campus marks are the careful case. Oral approval is not the written
confirmation the ledger asks for on an external piece.

## Output

A short decision in the program folder at `02-copy/output/marks.md` when a
program exists, otherwise in the reply:

```text
asset: <filename>
decision: use | wait | refuse
row: <the rights basis and approver cell, quoted>
file: <program-relative path, or none>
```

One mark per decision. A strip of manufacturer logos is a list of decisions,
each with its own row.
