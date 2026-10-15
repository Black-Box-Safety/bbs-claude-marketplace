---
name: sales-one-pager
description: >-
  Draft and render a Black Box Safety one-page sales piece from an intake
  brief: capability one-pager, leave-behind, sell sheet, punchout switch card,
  or line card. Use after marketing-intake, when the brief is on disk. Writes
  copy for the rep to edit, then fills the MRO template and runs the brand
  gate. Do not use for a Grainger hot-list promo page, a federal slide deck,
  or a first draft before the brief exists.
requires:
  - python3
degrades-without:
  - poppler
---

# Sales one-pager

Two stages, and they do not run in one breath. Stage `02-copy` writes a markdown
draft and stops. Stage `03-render` runs only when `02-copy/output/copy.md` is
already on disk from an earlier turn, so the rep has had the file.

## Stage 02-copy

### Inputs

| Layer | File |
|---|---|
| 4 | `01-intake/output/brief.md` in the program folder |
| 3 | The one track file named in the brief. A bridge reads both track files |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/VOICE.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/MESSAGING.md` |
| 3 | `${CLAUDE_PLUGIN_ROOT}/references/COMPLIANCE.md` |

If the brief is missing, run `marketing-intake` and stop. If the brief has a
`NEEDS CLAIM` line, write the copy around a visible `NEEDS CLAIM:` marker and
do not render.

### Process

Follow the brief's ask, including when the ask is not the parity wedge. The UC
Irvine capability README on the desk is the case where "same catalog" was the
wrong hero because the ask was an additional punchout tile.

Every factual sentence is approved wording from `references/CLAIMS.md`, copied
exactly. One channel on the piece. California wording comes from the registry
rows for that channel. Do not also print the federal credential line.

### Output

`02-copy/output/copy.md` with the blocks the template needs: eyebrow, headline,
subhead, section label, up to four grid items, the cost panel, the ask, the
footer contact, the credential line, and the disclaimer when `--scope agency`
applies. Then stop. Tell the rep the path and that render waits until they
leave this file as they want it.

## Stage 03-render

Run this only when the rep comes back after the copy file exists.

### Inputs

| Layer | File |
|---|---|
| 4 | `02-copy/output/copy.md` |
| 4 | The program `README.md` (`track`, `tier`, `approved-by`) |
| 3 | `${CLAUDE_PLUGIN_ROOT}/skills/sales-one-pager/assets/onepager.template.html` |
| 3 | Logo files only after `marketing-assets` has allowed each one |

### Process

1. Tier B with `approved-by: PENDING`, or with no name and date, stops here.
2. `public-safety` and `bridge` do not use this template. It is the MRO letter
   page (navy ground, gold payoff, red action). Say so, leave the copy file,
   and stop. A public-safety or bridge shell is a later template.
3. `mro-procurement` fills every `{{TOKEN}}` from the copy file. A token left
   in the HTML is a failed render. Logo `src` values are files `marketing-assets`
   copied into the program, or omitted. Do not pull a mark from the web.
4. Write `03-render/output/piece.html`.
5. Run the gate on that HTML:

```text
python "${CLAUDE_PLUGIN_ROOT}/tools/brand_check.py" 03-render/output/piece.html --scope mro --scope agency
```

Drop `--scope agency` only when the README says why it does not apply. Paste the
output into `GATE.txt` and into the README. Any finding stops the handoff. Fix
the piece. Do not fix the registry.

6. When the gate passes and `pdftotext` is available, a PDF may be printed from
   the HTML in the browser and then checked the same way on extracted text
   (`pdftotext piece.pdf piece.txt`, then the gate on `piece.txt`). Without
   Poppler, hand off the HTML and say the PDF text check has not run.

## What good looks like

A buyer can read the ask from the headline. The proof is a claim id, not an
adjective. The page looks like the MRO track: navy, rationed gold, red for the
ask. Grainger is a partner in the wording the registry allows. The piece does
not say Grainger ships and Black Box Safety collects.
