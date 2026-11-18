# desk-learn probe, 2026-11-16

Spec section 9 probe: payloads built from real CA and Sentinel deal paths and real file content, replayed through
`hooks/desk-learn.py` (and `hooks/desk-learn.sh` for the shell prefilter) with a scratch TMPDIR. OneDrive was only read;
the hook wrote nothing but its own markers and ledger under the scratch temp folder. Seven-digit-or-longer numbers and buyer names in folder
names are masked as `<acct>` and `<buyer>`. Synthetic parts: the edited text (a fake quote-log row, an Edit that sets a Stage line).

## 1. CA RFQ.md, Write of the real file's content (first session, then a second session)

| Deal folder | Stage header on disk | Session 1 | Session 2 (same content) |
|---|---|---|---|
| 10.12.26 | priced | silent | silent |
| ppe naspo 10.28.26 | quote built | silent | silent |
| warehouse 10.28.26 | logged | silent | silent |
| 6 grainger lines naspo 9.15.26 | packet built | silent | silent |
| AED G5 9.8.2026 | logged | silent | silent |
| Chainsaw 11.6.20226 | (no Stage line: legacy/v1) | silent | silent |
| ems 2 estimate 10.28.26 | sourcing | silent | silent |
| HVAC Filters 10.27.2026 | packet built | silent | silent |
| Faucets naspo 11.13.2026 | quote built | silent | silent |
| Commercial Doors 11.11.2026 | sourcing | silent | silent |
| helmet covers 10.16.26 | priced | silent | silent |
| <buyer> | (no Stage line: legacy/v1) | silent | silent |

## 2. CA RFQ.md, Edit that sets the Stage line (synthetic edit text on a real path)

| Deal folder | Edit | Result |
|---|---|---|
| ppe naspo 10.28.26 |  priced ->  sent | reminder: RFQ.md written at stage sent; folder: ppe naspo 10.28.26 |
| ppe naspo 10.28.26 |  sent ->  sent | silent |
| ppe naspo 10.28.26 |  sent ->  outcome | reminder: RFQ.md written at stage outcome; folder: ppe naspo 10.28.26 |

## 3. CA quote-log, FILLED, PO/award and Bash events on real paths

| Case | Result |
|---|---|
| Edit adds a row to CARB - Air Resource Board - <acct>/<buyer>/quote-log.md | reminder: quote-log row added or Outcome set; folder: <buyer> |
| Edit with close-out wording to the same log | silent |
| Edit adds a row to CARB - Air Resource Board - <acct>/<buyer>/quote-log.md | reminder: quote-log row added or Outcome set; folder: <buyer> |
| Edit with close-out wording to the same log | silent |
| Edit adds a row to EMSA - Emergency Medical Services Authority/quote-log.md | reminder: quote-log row added or Outcome set; folder: EMSA - Emergency Medical Services Authority |
| Edit with close-out wording to the same log | silent |
| Bash `>> quote-log.md` with cwd = that buyer folder (relative) | reminder: quote-log row added or Outcome set; folder: <buyer> |
| Bash `tee -a` the same log (absolute) | reminder: quote-log row added or Outcome set; folder: <buyer> |
| Write a new file under a real deal's FILLED folder: Orange Desiccant 10.14.2026 | reminder: new file in FILLED/; folder: Orange Desiccant 10.14.2026 |
| Write a new file under a real deal's FILLED folder: Webcams 11.4.2026 | reminder: new file in FILLED/; folder: Webcams 11.4.2026 |
| bbs-fill command writing into that FILLED folder (path with spaces, parentheses, ampersand) | reminder: new file in FILLED/; folder: Orange Desiccant 10.14.2026 |
| Write of a file named like a PO/award in a real deal folder: `PO#<acct>.pdf` | reminder: PO, award or NOA file written; folder: <buyer> 11.8.22 |
| Write of a file named like a PO/award in a real deal folder: `PO#<acct>.pdf` | reminder: PO, award or NOA file written; folder: <buyer> 11.8.22 |
| Write of a file named like a PO/award in a real deal folder: `<acct>PO.pdf` | reminder: PO, award or NOA file written; folder: Cleaning Supplies 9.7.22 |
| Write of `notes.md` in that deal folder | silent |

## 4. Sentinel RFP CLAUDE.md files, Write of each real file's content

| RFP folder | First line of the status block | Result |
|---|---|---|
| rfp-825025-pig-spill-control | `> **Status` | reminder: RFP status banner edited; folder: rfp-825025-pig-spill-control |
| rfp-826618-m724-esh-items | `> **Status` | reminder: RFP status banner edited; folder: rfp-826618-m724-esh-items |
| rfp-829985-m724-come-alongs | none | silent |
| rfp-834999-m724-cip-tools-ii | bare `**Status` | reminder: RFP status banner edited; folder: rfp-834999-m724-cip-tools-ii |
| rfp-842942- | bare `**Status` | reminder: RFP status banner edited; folder: rfp-842942- |
| rfp-850332-harnesses | bare `**Status` | reminder: RFP status banner edited; folder: rfp-850332-harnesses |
| rfp-26305-AYSS-00003-vlc-general-signs | `> **Status` | reminder: RFP status banner edited; folder: rfp-26305-AYSS-00003-vlc-general-signs |
| rfp-752578-winches-hoists | `> **Status` | reminder: RFP status banner edited; folder: rfp-752578-winches-hoists |
| rfp-752587-material-handling | `> **Status` | reminder: RFP status banner edited; folder: rfp-752587-material-handling |
| rfp-752887-fire extinguishers | none | silent |
| rfp-817007-vsfb-plumbing-fixtures | `> **Status` | reminder: RFP status banner edited; folder: rfp-817007-vsfb-plumbing-fixtures |

11 RFP CLAUDE.md files: 9 fire, of which 3 have a bare `**Status` line; 2 have no status line and stay silent.

## 5. Sentinel other paths

| Case | Result |
|---|---|
| Site-level CLAUDE.md edit with a status line | silent |
| Edit adding a row (a real row's text) to learning/quote-log.md | reminder: Sentinel quote-log appended; folder: learning |
| Edit adding a row to a quote-log.md that is not learning/quote-log.md | silent |
| Write of a PO-named file in an RFP folder | reminder: PO, award or NOA file written; folder: outbound |
| document-control/CLAUDE.md (not a site/RFP folder) | silent |

## 6. Nothing near a desk, and the shell entry

| Case | Result |
|---|---|
| PO-named file outside both desks | silent |
| a repo file | silent |
| desk-learn.sh with a real quote-log path (real python3) | reminder: quote-log row added or Outcome set; folder: <buyer> |
| desk-learn.sh, Bash `ls` with cwd inside the CA tree | silent |

## Findings

- The banner pattern change matters: 3 of the 11 real Sentinel RFP CLAUDE.md files carry a bare `**Status` line and would have been missed by the `> **Status` pattern.
- Two RFP CLAUDE.md files (rfp-829985, rfp-752887) have no status line at all, so a banner edit there is silent. A Write of a whole CLAUDE.md fires if any line of it starts with `**Status`, edited or not; once per RFP per session.
- None of the sampled real RFQ.md files is at sent or outcome (stages seen: logged, sourcing, priced, quote built, packet built), so a real Write of their content is silent; a sent or outcome move is rare in the sample and the Edit rows in section 2 cover it. Two real RFQ.md files have no Stage line (v1/legacy) and stay silent.
- Real folder names carry parentheses, ampersands, dots and spaces; none broke path matching. Real PO files are named like `PO#<acct>.pdf` and `<acct>PO.pdf`; both match.
- The outcome close-out wording (`per BC`) keeps a quote-log batch quiet on every real log tried; a hand edit with a plain outcome still reminds.

Everything the hook wrote, all under the scratch temp folder: 63 files (markers, stage files, ledgers); no ledger line holds a folder name.

