# Asset Rights Ledger

Image files stay on the marketing desk, under `brand/assets/logos/` in
`MARKETING/bbs-marketing/`. This file is the ledger. The plugin does not ship the images.

Every third-party mark used on a **customer-facing** BBS piece needs a row here. **No row, no
use externally.**

**Internal-only pieces are exempt** from the row requirement per COMPLIANCE §0 (approved by
Parker Marshall, 3 September 2026). They may use any mark in `brand/assets/logos/` or
`bbs-customer-bots/public/brand/logos/`. Rows are still written for those marks so the ledger
stays complete and the mark is ready the day a piece goes external.

`brand-check` will require a row for every logo referenced by a piece once builds run through
`templates/build.py` (Phase 2). Until then this ledger is enforced by review.

## Our own marks

| asset | rights basis | approved by | date | notes |
|---|---|---|---|---|
| bbs-logo-color.png | own mark | Joey | 2026-08-13 | primary, light grounds |
| bbs-logo-white.png | own mark | Joey | 2026-08-13 | horizontal, dark grounds |
| bbs-logo-stacked-white.png | own mark | Joey | 2026-08-13 | stacked, dark grounds |
| *bbs-logo-black.png* | own mark | — | — | **Approved rendering per the Branding Guide but no file exists anywhere.** Produce it or drop it from the approved list |

## Certification and program marks

| asset | mark owner | rights basis | approved by | date | expires | notes |
|---|---|---|---|---|---|---|
| dvbe.png | State of California | certification mark, cert 2009473 | Joey | 2026-08-13 | 2027-06-30 | California DVBE only — not a federal mark |
| cred-dgs.png | CA Dept. of General Services | awarded LPA | NEEDS CONFIRMATION | | | |
| cred-naspo.png | NASPO ValuePoint | awarded LPA 7-25-51-02.03 | NEEDS CONFIRMATION | | | see registry item 6 — a business card prints a different LPA number |
| cred-omnia.png | OMNIA Partners | awarded contract 2018-000207 | NEEDS CONFIRMATION | | | |
| omnia-white.png | OMNIA Partners | awarded contract 2018-000207 | NEEDS CONFIRMATION | | | |

## Grainger Distributor Alliance marks

Grainger co-branding carries its own approval chain, separate from any customer-facing review.
Usage rules live in `references/tracks/mro-procurement.md`.

| asset | mark owner | rights basis | approved by | date | expires | notes |
|---|---|---|---|---|---|---|
| grainger.png | W.W. Grainger, Inc. | Distributor Alliance program | Joey | 2026-08-13 | 2027-06-30 | wordmark alone. Never on a red field, never redrawn, recolored, rotated, or cropped |
| ga-black-red.jpg | W.W. Grainger, Inc. | Distributor Alliance program | Joey | 2026-08-13 | 2027-06-30 | official lockup, light grounds. Carries Grainger's tagline as artwork, so it never sits in a block with the BBS campus kicker |
| ga-white-red.png | W.W. Grainger, Inc. | Distributor Alliance program | Joey | 2026-08-13 | 2027-06-30 | official lockup, dark grounds. Same tagline constraint as above |
| cobrand-lockup.png | W.W. Grainger, Inc. / BBS | Distributor Alliance program | Joey | 2026-08-13 | 2027-06-30 | the official co-brand lockup. Approved artifact only. Never build a new BBS/Grainger lockup |
| alliance-seal.png | W.W. Grainger, Inc. | Distributor Alliance program | Joey | 2026-08-13 | 2027-06-30 | footer legal strip and bottom-right of hero. Sits as a separate mark with clear space, never locked to the BBS wordmark |

## Customer marks — highest priority

These are **already printed on distributed pieces** on the strength of an oral approval recorded
only in a prose sentence in the old kit's CLAUDE.md. Written permission should be obtained and
recorded here.

| asset | mark owner | rights basis | approved by | date | expires | notes |
|---|---|---|---|---|---|---|
| csu-fresno.png | California State University, Fresno | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | on a distributed piece |
| csu-la.png | California State University, Los Angeles | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | |
| csu-longbeach.png | California State University, Long Beach | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | |
| csu-sanmarcos.png | California State University, San Marcos | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | |
| csu-slo.png | California Polytechnic State University, San Luis Obispo | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | |
| ladwp-logo.png | Los Angeles Dept. of Water and Power | oral approval, Joey | **NEEDS WRITTEN CONFIRMATION** | | | on a distributed piece |
| *UC Irvine marks* | The Regents of the University of California | none | **DECLINED 2026-08-13** | | | Three files were downloaded from UCI's brand site for the capability one-pager: `ucirvine-blue.png`, `ucirvine-monogram.png`, `ucirvine-endorsement.svg`. Not used and not copied into this library. Downloading from a brand site is not permission, and the endorsement lockup is UC's unit-lockup format, so placing it on a vendor piece is the endorsement read `COMPLIANCE.md` §1.1 bars outright. Joey's call, 2026-08-13. UC Irvine appears as body text and in the `agency-disclaimer` instead |

Note the compliance interaction: using a customer's mark alongside the required
independent-supplier disclaimer is what keeps the piece from reading as an endorsement. See
`references/COMPLIANCE.md`.

## Manufacturer marks

Used to show catalog breadth. Resale relationship is not automatically a trademark licence —
confirm before use on a published piece.

| asset | mark owner | rights basis | approved by | date | notes |
|---|---|---|---|---|---|
| brand-3m.png | 3M | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-dewalt.png | Stanley Black & Decker | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-diversey.png | Diversey | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-gojo.png | GOJO Industries | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-gp.png | Georgia-Pacific | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-honeywell.png | Honeywell | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-kimberly.png | Kimberly-Clark | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-milwaukee.png | Techtronic Industries | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-rubbermaid.png | Newell Brands | manufacturer, resale | NEEDS CONFIRMATION | | |
| brand-sanitaire.png | Bissell | manufacturer, resale | NEEDS CONFIRMATION | | |

## Fonts

| asset | licence | notes |
|---|---|---|
| Roboto-400.woff2 | Apache 2.0 | Grainger's typeface — the MRO track's face |
| BarlowCondensed-500/600/700.woff2 | SIL OFL | display face |
| SourceSans3-400.woff2 | SIL OFL | fallback body face |

**Gap:** only Roboto **400** is present. The MRO track's heading rules call for 500/700/900.
Those weights must be added before a Grainger co-brand piece can build correctly.

## Photography

| asset | source | rights basis | notes |
|---|---|---|---|
| hero-electrician.jpg | unknown | **NEEDS CONFIRMATION** | provenance not recorded in the old kit; confirm licence before reuse |

The 1,265-file `MARKETING/Photos/` library is referenced, not copied. Any image promoted from it
into a published piece needs a row here first.

## California agency marks

Rights basis for every row below is **nominative fair use**: the mark identifies the agency BBS
supplies or analyses, and is never presented as endorsement. Cleared for **internal-only** use
per COMPLIANCE §0 — including section headers, which §1.2 bars on customer-facing pieces.
External use of any of these needs its own review and a permitted-context note.

Source art: `bbs-customer-bots/public/brand/logos/agencies/`. Never redrawn, recolored, or
locked to the BBS wordmark.

| asset | mark owner | rights basis | internal use | external use | approved by | date |
|---|---|---|---|---|---|---|
| cdcr | CA Dept. of Corrections and Rehabilitation | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| calfire | CAL FIRE | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| caltrans | CA Dept. of Transportation | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| calvet | CA Dept. of Veterans Affairs | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| cdfw | CA Dept. of Fish and Wildlife | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| dsh | CA Dept. of State Hospitals | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| dwr | CA Dept. of Water Resources | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| cmd | California Military Department | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| ccc | California Conservation Corps | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| dds | CA Dept. of Developmental Services | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| ladwp | Los Angeles Dept. of Water and Power | nominative fair use | cleared | needs review | Parker | 2026-09-03 |
| csu-* (5 campuses) | California State University | nominative fair use | cleared | needs review | Parker | 2026-09-03 |

**CHP carries a statutory restriction.** CA Vehicle Code § 2262 restricts use of "California
Highway Patrol" or "CHP" in connection with a business in any manner reasonably construed as
implying association or approval. No CHP seal is held and none should be sought. CHP renders as
a typographic chip on every piece, internal included. Cal OES and DGS have no seal on disk and
render the same way.
