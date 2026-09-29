---
name: deck-precedent
description: >-
  Find an existing Black Box Safety brochure, capability statement, line card,
  or pitch deck and write a short precedent note. Use when a rep asks what we
  already sent a campus, an agency, or a federal buyer. Points at the file on
  the marketing desk. Do not use to write new slide copy or to assemble a
  PowerPoint.
requires: []
---

# Deck precedent

One job: point at a file that already exists. Open it before you describe what
is inside. The index is filenames. A filename is not a summary of the document.

## Inputs

| Layer | File |
|---|---|
| 3 | `${CLAUDE_PLUGIN_ROOT}/skills/deck-precedent/references/precedent-index.md` |
| Desk | The path the index names, if it is in the workspace |

## Process

1. Search the index for the account, the vehicle, or the piece type the rep named.
2. If the workspace can see that path, open it and write what it actually contains.
   If it cannot, give the path and say the file was not opened.
3. Federal or prime slide copy, when the rep wants new words, is `bbs-deck-voice`
   in `bbs-foundations`. This skill does not write that copy and does not build
   a new deck. A California sales-deck template is not in this plugin yet. Say so
   and offer `sales-one-pager` when the need is a one-page piece.

## Output

A precedent note. In a program folder, save it as `01-intake/output/precedent.md`.
Otherwise reply with the same shape:

```text
file: <path from the index>
opened: yes | no
what it is: <only what you read, or "not opened">
use: <what the rep can reuse: structure, or nothing until they open it>
```

Do not quote a contract number, a price, or a cert line from memory of the file.
If you read one, it still has to match `references/CLAIMS.md` before it goes on
a new piece.
