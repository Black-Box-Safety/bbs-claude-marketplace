<p align="center">
  <img src="https://img.shields.io/badge/desk-marketing%20material-051c2c" alt="Marketing material">
  <img src="https://img.shields.io/badge/skills-5-b19800" alt="5 skills">
  <img src="https://img.shields.io/badge/facts-claims%20registry-2dd4bf" alt="Facts from the claims registry">
</p>

# bbs-marketing

The plugin reps use to make marketing material and to find what already exists.
A one-page sales piece, a campaign email, a logo check, a prior brochure or deck.
The claims registry is the wording. The rights ledger is the logo. The SharePoint
folder `MARKETING/bbs-marketing/` is where the finished piece and the image files live.

**Jump to:** [The piece, in order](#the-piece-in-order) · [Commands](#commands) · [The rules that don't bend](#the-rules-that-dont-bend)

## The piece, in order

A piece moves through files a rep can open. Each skill stops so the next file is
a decision, not a surprise.

| # | Step | Skill |
|---|---|---|
| 1 | Who it is for, the one ask, the track, the claims check | `marketing-intake` |
| 2 | The one-page draft, then the MRO page | `sales-one-pager` |
| 3 | One email draft | `campaign-email` |
| 4 | May this logo be used | `marketing-assets` |
| 5 | What we already printed or presented | `deck-precedent` |

A Grainger hot-list landing page stays `grainger-promo-page` in `bbs-sales`.
Federal slide copy stays `bbs-deck-voice` in `bbs-foundations`.

`/bbs-one-pager` runs step 1 and stops.

## Commands

| Command | Does |
|---|---|
| `/bbs-one-pager` | Open a program folder and write the brief. Stops before copy. |

## The rules that don't bend

- Approved wording is `references/CLAIMS.md`. A missing row is `NEEDS CLAIM:`.
- One track per piece. `references/tracks/ROUTING.md` chooses it.
- A logo needs a row in `references/ASSETS.md`. The image stays on the desk.
- One channel on a piece. California wording and federal wording do not share a page.
- The gate is `python tools/brand_check.py` on the rendered HTML. A finding stops the handoff.
- A human sends. Tier B needs a named approval in the program README before render.

## Setup

Install this plugin from the marketplace. Open the marketing desk when the job
needs a logo file or a program folder:

`MARKETING/bbs-marketing/programs/`

Logo files are `MARKETING/bbs-marketing/brand/assets/logos/`. The ledger in this
plugin says which of those files may leave the folder.
