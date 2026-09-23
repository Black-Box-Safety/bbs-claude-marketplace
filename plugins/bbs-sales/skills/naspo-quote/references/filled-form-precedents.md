# What BBS has actually written on these forms

Mined from the State of CA Agencies corpus (~440 PDFs, ~300 classified: 113
CalRecycle 74, 72 PD 843, 46 BBS quotes, 24 OBS 1000, 22 Darfur, 14 CV 012,
13 GSPD-05-105, 11 STD 204, 24 POs). Counts below are how many past packets used
each value — treat the majority answer as the house standard and deviate only with
a reason. The exception is certification and preference fields: a California SB claim
in the corpus predates BBS passing the SB revenue threshold and is historical only
(see GSPD-05-105 below); the current value comes from `vendor_profile.json`.

Regenerate with:

```bash
python scripts/mine_precedents.py "<State of CA Agencies>" --out /tmp/mine.json
```

## Signer roster — check this before you sign anything

The corpus shows three signers, split by form, and it is **not** all Parker:

| Signer | Signs | Evidence |
|---|---|---|
| **Griffin Forsyth, VP** | CalRecycle 74 — the routine, high-volume case | Print Name on 53 of ~65 filled CalRecycle 74s |
| **Parker Marshall, Sales Manager** | CalRecycle 74 when he owns the RFQ; Darfur; OBS 1000 | 11 CalRecycle 74s, plus the 08/2026 CDCR packets |
| **Jackson Dalton, President (DV Owner)** | PD 843 (DVBE perjury declaration), CV 012 CUF, STD 204 payee rep, Darfur when he's the certifying official | DVBEowner1 on 58 PD 843s; PrintedName on CV 012; NAME OF AUTHORIZED PAYEE REPRESENTATIVE on 4 STD 204s |

PD 843 is Jackson's alone — it declares disabled-veteran ownership. CV 012 likewise.
STD 204 is signed by Jackson as payee representative, with
`jackson@blackboxsafety.com` as the email, not Parker's.

All three are in `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` under
`authorized_representatives`. Griffin has no email on file — confirm one with the
rep before putting it on a form that asks. Ask who is signing rather than
defaulting to whoever signed last time; the roster above tells you which answers
are plausible.

## Vendor constants as they appear on filed forms

| Value | Canonical | Variants seen (harmless, but prefer canonical) |
|---|---|---|
| Legal name | `Black Box Safety, Inc.` | `Black Box Safety, Inc` (no period) appears on 49 PD 843s |
| Address | `1950 Cordell Ct, Suite 103, El Cajon, CA 92020` | `1950 Cordell Ct. Suite 103 El Cajon, CA 92020`, `1950 Cordell CT Ste 103` |
| Phone | `(619) 499-7943` | `619-499-7943` (STD 204 and most CalRecycle 74s) |
| FEIN | `82-1125133` | `821125133` unpunctuated on STD 204 and some Darfur forms |
| DVBE OSDS ref | `2009473` | — |
| DVBE expiration | `12/31/2027` | — |
| Seller's permit | `103213178` | — |

## PD 843 — DVBE Declaration (72 in corpus)

| Field | Standard value |
|---|---|
| `DVBEname` | `Black Box Safety, Inc.` |
| `DVBErefno` | `2009473` (62 packets) |
| `YNagent` | `/1` — the "not a broker or agent" box (56 packets) |
| `DVBEowner1` | `Jackson Dalton` (58); `Jackson Dalton, President (DV Owner)` also used |
| `DVBEowner1date` | date of signing |
| `PageNo` / `TotalPages` | `1` / `1` |
| `description` | one line naming the goods and total quantity |
| `SCno` | solicitation number, or the BBS quote number when the agency issued none |

Real `description` values: `MSA multi-gas detection instruments, calibration
equipment and accessories; NANUK protective cases` · `Steel wire hamper frames,
R&B Wire Model 669 (40 EA)` · `Climbing and rope-rescue equipment` ·
`Janitorial, sanitation and spill-control supplies` · `MRO supplies and hardware`.

Real `SCno` values show the range of what agencies issue: `RFQ 26-07-010`,
`RQS # CPO 0527-0147`, `WH-015`, `RFQ DS 1161 (Porterville DC)`,
`SQ-104749 DWR 8/26/26`, `Quote 900005`.

## GSPD-05-105 — Bidder Declaration (13 in corpus)

`Check Box3` (no subcontractors), `Check Box5` (not a broker/agent), and
`Check Box8` (51% rental N/A) are `/Yes` on all 7 filled copies — that trio is the
BBS answer, confirmed. `page` = `1`, `of #` = `1`.

`Text1` is usually `DVBE`; `SB, DVBE` and `DVBE, SB` (historical only) appear where
BBS claimed both certifications. One packet used a form revision with a `Certification #` field
instead, filled `DVBE 2009473`.

**Historical only — today `Text1` is `DVBE`.** The `SB, DVBE` / `DVBE, SB` forms were
filed while BBS was a California small business and were correct when filed (Parker,
2026-09-23); they are not a compliance problem and the record above stays as filed.
They are not precedent for a bid made today: BBS has since passed California's SB
revenue threshold and OSDS 2009473 carries DVBE alone (ruled 2026-09-22;
`ca-form-rules.md`, "Certification language"). The same holds for a checked SB or MB
box. `mine_precedents.py` routes a field whose name or value carries an SB, MB or
small-business token to `historical_only`, never to `filled_values`. It cannot see a
generically named checkbox (e.g. `Check Box3`) whose meaning is only on the printed
page, so any SB-looking value in a precedent table still needs a human check.

Real `Product list` (CUF) statements, all one to two lines:

- "Black Box Safety, Inc. will supply all goods listed in this solicitation directly. No subcontractors will be used."
- "BBS is the contracting supplier of record: sourcing, purchase order placement, order management, receiving/inspection, invoicing, and delivery."
- "Black Box Safety, Inc. is the prime and sole supplier; no subcontractors will be used. BBS furnishes all climbing and rope-rescue equipment…"

## Darfur OBS 1500 (22 in corpus) — three revisions in circulation

1. **CDCR OBS 1500 (06/11)** — `CompanyVendor Name Printed`, `Date`,
   `By Authorized Signature`. Option #1.
2. **A revision with initials** — `Initials`,
   `Printed Name and Title of Person Initialing option 1 or 2`,
   `Date of signature`. One packet: `GF` / `Griffin Forsyth, VP`.
3. **An XFA-style revision** — `form1[0].Page1[0].#subform[0].CheckBox1[0]` plus
   `#area[0].TextField[0..2]` and `DateTimeField[0]`.

Run `inspect_form.py` rather than assuming revision 1. Where Option #2 fields
exist and don't apply, past packets wrote `N/A` rather than leaving them blank —
some buyers bounce blanks.

## OBS 1000 GenAI (24 in corpus) — two field-naming revisions

The 10/2025 revision uses bare names (`Business Name`, `City`, `Is GenAI
utilized?`). An earlier one prefixes everything with `OBS 1000 - ` and answers the
GenAI question with a checkbox called
`OBS 1000 - No If no skip to Signature section of this form` = `/On` rather than a
radio group. Both appear in the corpus; detect, don't assume.

Standard answers: GenAI = **No** every time; business block from the vendor
profile; `Contract  Description of Purchase` a one-line statement of the goods.
Where a form has an `LPA Contract  Reference` field, packets wrote `7-25-51-02.03`.

## CV 012 — Commercially Useful Function (14 in corpus)

CalVet/CMD forms send this one and it is **not** in the base CDCR packet. XFA field
names:

| Field | Value |
|---|---|
| `form1[0].#subform[0].DoingBusinessAs[0]` | `Black Box Safety, Inc.` |
| `form1[0].#subform[0].OSDSRefNumber[0]` | `2009473` |
| `form1[0].#subform[0].ExpirationDate[0]` | `12/31/2027` |
| `form1[0].#subform[0].SolicitationNumber[0]` | solicitation or quote number |
| `form1[0].#subform[0].RadioButtonList[0..3]` | `/0` |
| `form1[0].#subform[0].RadioButtonList[4..5]` | `/1` |
| `form1[0].#subform[1].PrintedName[0]` | `Jackson Dalton` |
| `form1[0].#subform[1].Title[0]` | `President` |
| `form1[0].#subform[1].Date[0]` | date of signing |

The `/0 /0 /0 /0 /1 /1` radio pattern is the BBS answer set, consistent across
filed copies. Confirm the question wording on the revision in front of you before
copying it — the pattern is only meaningful against the same question order.

## STD 204 — Payee Data Record (11 in corpus)

Needed when the agency has no payee record for BBS, not on routine reorders.

| Field | Value |
|---|---|
| NAME (must match federal tax return) | `Black Box Safety, Inc.` |
| `corpOthers` | `/On` — Corporation, all others |
| `calRes` | `/On` — California resident |
| FEIN | `821125133` (unpunctuated on this form) |
| Mailing address / city-state-zip | `1950 Cordell Ct, Suite 103` / `El Cajon, CA 92020` |
| Authorized payee representative | `Jackson Dalton`, `President` |
| Telephone / email | `619-499-7943` / `jackson@blackboxsafety.com` |
| Agency block | the ordering agency, e.g. `Department of Water Resources`, `Department of Veterans Affairs (CalVet)` |

Some revisions use short internal names (`nameReq1`, `taxIDNumber`, `certName`,
`certTelephone`, `remAddress1`). Where a separate remittance address is asked for
and none applies, packets wrote `N/A - remittance address same as STD 204`.

## Solicitation number formatting

The same NASPO contract appears three ways in the corpus: `7-25-51-02.03` (8
files, the LPA reference style), `07-25-51-02.03`, and `07-25-51-02.3`. **All
three are accepted** — confirmed by the rep 08/27/2026 — so a packet that mixes
them is not a defect and does not need reworking. Default to whichever rendering
the agency's own worksheet prints, since matching their paperwork reads cleanest,
but don't burn a cycle normalizing forms that are already filled.

## CalVet-specific forms to expect

`CV 031 Request for Quote Worksheet`, `CV 039 Fair and Reasonable`, and a
`VSDS Form` show up in CalVet packets alongside the standard certs. They are not
in the CDCR set — inspect and map them when one arrives.
