# Brand Core

Black Box Safety, Inc. goes to market as one brand in two expressions. This file holds only what is true in
both. Every piece inherits everything here; a track file may extend these rules but never contradicts them,
and never restates them. Every factual assertion on a published piece comes from `references/CLAIMS.md`, worded
exactly as its `approved wording` column states. Nothing here overrides that.

## The wordmark

The mark is drawn artwork — `BLACK` / `BOX` / `SAFETY` with the `O` of `BOX` replaced by a hexagonal glyph.
It is not type.

- Never typeset, rebuild, retrace, or substitute a font for the wordmark, and never alter its letterspacing,
  stack proportions, or hex glyph.
- The registered-trademark `®` is part of the mark: never removed, resized independently, or relocated.
- Two configurations are approved: **stacked** (three lines) and **horizontal** (`BLACKBOXSAFETY`). Use
  stacked wherever vertical room allows; horizontal only in shallow bands — footers, letterhead rules,
  signatures.
- Three color renderings are approved: **two-color** (black letterforms, gold `BOX`) on light grounds,
  **all-black** for one-color print, and **reversed white** on dark grounds. Two-color is the default
  wherever substrate and process allow. On a dark ground the mark is reversed white — never two-color on
  navy, never gold letterforms carrying the whole mark.
- Never set the mark on unmodified photography, apply a shadow/outline/glow/gradient to it, or lock it to
  another organization's mark to form a new combined logo. Co-brand lockups are governed per track.

## Clear space and minimum size

- Clear space on all four sides equals the cap height of the `B` in `BLACK` at the size in use. Nothing —
  type, rule, image edge, trim, fold — enters that zone.
- Minimums: stacked, **0.75 in** wide in print and **72 px** on screen; horizontal, **1.25 in** and
  **120 px**. Below these the hex glyph fills in and the `®` vanishes.
- The mark never appears below these sizes. If a placement cannot hold one, drop the mark rather than
  shrink it.

## Approved logo files

Logo artwork lives in `brand/assets/logos/`. Only files in that directory are approved source art — never
art pulled from a website, a deck, an old PDF, or a search result. Filenames are stable and referenced
directly by templates: `bbs-logo-color.png` (stacked, two-color), `bbs-logo-white.png` (horizontal,
reversed), `bbs-logo-stacked-white.png` (stacked, reversed), and `bbs-logo-black.png` (all-black, one-color
print — add when produced). Add a rendering to that set only after approval; never generate a variant at
build time. Third-party marks are not BBS art and carry their own rights — see `references/ASSETS.md`.

## Shared palette

Both expressions inherit these four tokens. A track chooses which one leads; neither adds a color without
adding it here.

| token | hex | print | role |
|---|---|---|---|
| `--black` | `#000000` | PMS Black 6C · CMYK 70-50-25-100 | wordmark letterforms, rules, dense ground |
| `--navy` | `#051C2C` | PMS 296C · CMYK 91-76-55-68 | primary dark ground |
| `--gold` | `#B19800` | PMS 104C · CMYK 33-33-100-4 | the single accent |
| `--gray` | `#B7B7B8` | PMS Cool Gray 4C · CMYK 29-23-23-0 | dividers, secondary rules, muted states |

- Gold is an accent, never a field. It carries one idea per piece — the payoff line, the credential, the
  mark's `BOX` — and never fills a page ground or a body-copy block.
- Gold on navy measures 6.0:1 and is approved for text at any size. Gold on white measures 2.9:1 and
  **fails**: on light grounds gold is permitted only for display type at 24 px / 18 pt and above, rules,
  and graphic elements — never body copy.
- Body copy is white or `--gray` on dark, `--black` or a dark neutral on light. Never gold.
- Tints at 80/60/40/20% are allowed; new hues are not. Never set `--navy` on `--black` or the reverse —
  they read as one color.

## Typography

- **Univers LT Std** is the house typeface of record: Black or Bold for headlines and titles, Roman or
  Light for body. Each track names its own working substitute where a co-brand or display need overrides
  this; the substitute is named in the track file, never chosen per piece.
- One family per piece, varied by weight — never more than two families including a co-brand face. Headline
  case, display face, and condensed treatments are track decisions.
- Body copy is sentence case, left-aligned, never justified. Labels and eyebrows are uppercase bold with
  ~0.1em letter-spacing.
- Minimum body size is 9 pt in print, 14 px on screen. Legal and credential lines never go below 6.5 pt.

## Layout principles

- Every published piece carries, in a consistent place across a family: the wordmark, the credential line
  for that piece's one channel, and a contact block with a person, an address, and an email.
- One idea per block — the headline states the claim, the body supports it.
- Iconography is line art at a single stroke weight in `--navy`, `--black`, or the track's accent. Never
  mixed weights, filled clip art, or emoji.
- Type crossing photography sits on a solid or scrim panel, never on the raw image.
- Print pieces build full-bleed: 0.125 in bleed, 0.25 in minimum safe margin.
- Nothing ships without a clean `tools/brand_check.py` run at the piece's scope.

## Veteran-owned identity

Veteran ownership is a fact of the company, not decoration. State it once, precisely, as a certification —
never as a slogan, a flag graphic, or a claim of preference.

- Spell it out on first or formal reference as **SBA-certified Service-Disabled Veteran-Owned Small
  Business**; use **SDVOSB** as the short form in credential lines.
- **SBA-certified Veteran-Owned Small Business** is separately held and may be claimed where a VOSB
  set-aside or federal audience makes it relevant.
- Never credit the VA or the CVE for the certification in any wording. The SBA certifies.
- Commercially, these certifications are what let a buying agency's spend count toward a diversity or
  small-business participation goal. State the mechanism; never promise an award or a preference.

NEEDS CLAIM: founder's name, branch of service, and the service-connected injury behind the company story.

NEEDS CLAIM: whether "Keeping you safe on the job" is still the current tagline.

## Credentials and company facts

Reproduce exactly. Do not paraphrase, expand, abbreviate, or reformat.

- California piece: **CA DVBE Cert. 2009473**. That is the only certification line on the piece.
- Federal or prime piece: **SDVOSB** (long form: SBA-certified Service-Disabled Veteran-Owned Small
  Business). **SBA-certified Veteran-Owned Small Business** only where a VOSB audience makes it
  relevant. UEI **FRK5MJD35GN5** belongs on that federal piece.
- A piece prints one of those two credential lines. The gate fails a piece that prints both.
- **1950 Cordell Ct., Ste 103, El Cajon, CA 92020**. The city is **El Cajon**; San Diego is the county.
  Naming the county as the home city is a registered error and fails the build.
- **joey@blackboxsafety.com** — no other address appears on a published piece.
- Legal entity name is **Black Box Safety, Inc.** on first and legal reference, *Black Box Safety*
  thereafter. *BBS* is internal shorthand and never appears customer-facing.
- Contract and cooperative-vehicle numbers are track-scoped and registered in `references/CLAIMS.md`. Take them
  from there, never from an existing piece.

NEEDS CLAIM: outbound phone number for the contact block.

NEEDS CLAIM: web address for the contact block.

## What lives elsewhere

- `references/tracks/` — expression-specific rules: which token leads, display face, photography, voice, buyer,
  wedge, co-brand lockups. Read exactly one track file per piece.
- `references/CLAIMS.md` — the governed registry of approved wording, superseded wording, and expiry. Every fact
  on a piece comes from there.
- `references/ASSETS.md` — third-party mark rights: which logos may be used, in what context, under whose
  permission.

## Data visualization palette

Registered 2026-09-03, approved by Parker Marshall. A narrow, explicit exception to
"new hues are not [allowed]" above, and the only one.

Charts need four series a reader can tell apart. The four brand tokens cannot supply them:
gray `#B7B7B8` falls below the chroma floor and reads as no-data, which leaves gold and navy —
two hues for a four-series problem. These four steps exist **for data marks only**.

| Slot | Light (`#F6F7F9` surface) | Dark (`#0E1116` surface) | Convention in CA state sales |
|---|---|---|---|
| 1 | `#B19800` (brand gold, unchanged) | `#AD9412` | Kim Quezon |
| 2 | `#20629B` | `#4E8CC4` | Aanya Samarasinghe |
| 3 | `#A83B2C` | `#CB6152` | departed rep / at-risk |
| 4 | `#6A5AA8` | `#8E79C6` | shared team / other |

Validated against all six checks (lightness band, chroma floor, CVD separation, normal-vision
floor, contrast) in both modes. Assign in fixed order; never cycle. A ninth series folds into
"Other" or becomes small multiples.

**Bounds of the exception.** These steps are for chart marks only — never page chrome, never
type, never a logo, never a background. Page chrome stays black, navy, gold and gray as above.
Gold at `#B19800` measures 2.66:1 on light paper, below 3:1, so **every gold mark carries a
direct label or a table view**; that relief is required, not optional. Status colors
(good / warning / critical) are reserved, ship with an icon and a label, and are never a series.
