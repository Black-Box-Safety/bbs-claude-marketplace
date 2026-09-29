---
name: campaign-email
description: >-
  Draft one Black Box Safety outbound campaign email from an intake brief.
  Use for a switch note, a win-back, or an internal announcement about a
  marketing piece. Writes a draft in the program folder. Do not use to send
  mail, to request a vendor price, or to write a one-pager.
requires: []
---

# Campaign email

One draft. A person sends it from their own mailbox. This skill does not call
a mail tool.

## Inputs

| Layer | File |
|---|---|
| 4 | `01-intake/output/brief.md`. If it is missing, run `marketing-intake` and stop |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/VOICE.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/CLAIMS.md` for every factual sentence |
| 3 | The template below |

The worked examples on the desk are
`MARKETING/bbs-marketing/programs/2026-08-28-calfire-hotlist-h2/email/`.
Read one to see the shape of a segment note. Re-check every sentence against
`CLAIMS.md` before reusing a line. A worked example can be stale. Do not copy
a price, a buyer count, or a contact address out of it.

## Process

Fill this shape. One ask. Sentence case in the subject. When the message names
an agency, the agency-disclaimer wording from the registry goes in the body
verbatim, and the brief's scope includes `agency`.

```text
Subject: {{one ask}}

{{greeting}}

{{who Black Box Safety is, approved wording only}}

{{the one change for this reader}}

{{the ask, one action}}

{{agency disclaimer when an agency is named}}

{{signature block from a claims row. If the sender's email has no row, write NEEDS CLAIM and stop before calling the draft ready}}
```

Partnership wording comes from the registry. The piece says Black Box Safety
delivers, with Grainger's network behind that delivery, in whatever approved
sentence the registry has. It does not say Grainger handles it.

## Output

`02-copy/output/email.md` in the program folder, with the segment named in the
first lines if there is one. Tell the rep it is a draft. Do not send it.
