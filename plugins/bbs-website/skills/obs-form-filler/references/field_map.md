# OBS 4007(B) Packet-B — Field & Page Reference

CDCR "Request For Quote (RFQ) Packet – B", OBS 4007(B) Rev. 08/2025. Ships as a
fillable AcroForm PDF (~480 fields) plus four flat (non-fillable) company-name lines.
`scripts/fill_obs_packet.py` handles both. This file is a human-readable map of what
goes where and who signs — read it if a field lands wrong or the packet revision
changes.

## Packet contents (page order, 1-based as the PDF opens)

| Page | Form | What the script fills | Signer |
|------|------|----------------------|--------|
| 1 | Cover sheet | (nothing) | — |
| 2 | OBS 4007(B) front page | Solicitation/dates, BBS address, rep contact, FEIN, seller's permit, DVBE checkbox + cert/exp, manufacturer = No, SB-sub = No, bidder signature | **Rep** |
| 3 | OBS 4007(B) additional details | Delivery ARO days (30), All-or-none = Yes, Freight prepaid = Yes, agency requestor + ship-to | — |
| 4–11 | OBS 4007(B) terms / response list | (nothing — boilerplate) | — |
| 12 | Line-Item Cost Worksheet | Line items (qty/unit/desc/part#/PCRC/unit/ext), subtotal, S&H, grand total | — |
| 13 | Bidder Declaration GSPD-05-105 | Cert = DVBE, subcontractors = No, broker = No, rental = N/A, page 1 of 1 | — |
| 14 | GSPD-05-105 instructions | (nothing) | — |
| 15 | Darfur Contracting Act OBS 1500 | Option 1 (no activities outside US): company name + date + signature | **Rep** |
| 16 | CalRecycle 74 | Company name (annotation), address, phone, item row 1 desc, PCRC = NA, SABRC = NA, cert signature | **Rep** |
| 17 | CalRecycle SABRC code table | (nothing) | — |
| 18–19 | GenAI Factsheet OBS 1000 | Business profile, description of purchase, GenAI = No, signature date | (signature glyph field; date filled) |
| 20 | OBS 1000 instructions | (nothing) | — |
| 21 | DVBE Declarations DGS PD 843 | DVBE name/ref/desc, not-a-broker = Yes, owner print + signature + date | **Jackson Dalton (DV owner)** |
| 22–23 | Supplement Vendor Payee Data Record | Legal name, FEIN, physical + remit-to address, sales contact (rep), accounting contact (Amy Leath), DVBE cert, recipient type = LLC S-Corp / All Others | — |
| 24 | Payee Data Record STD 204 | Name (annotation), address, entity = All Others + FEIN, CA resident, authorized payee rep + signature + date | **Jackson Dalton (owner)** |
| 25 | STD 204 instructions | (nothing) | — |

## The two-signer rule (most important)

- **Rep signs** the bidder/certification lines (OBS 4007(B), Darfur, CalRecycle 74).
  The rep is a variable input — a different salesperson can quote/sign each job.
- **Jackson Dalton signs** the ownership lines (PD 843 DV owner, STD 204 authorized
  payee rep). These are tied to ownership of the certified DVBE, not to who quoted.

## Four flat (non-AcroForm) company-name lines

These have no fillable field and are stamped as text annotations by the script
(`ANNOTATIONS` list, PyMuPDF coordinates, origin top-left, Rev. 08/2025 layout):

| Page (0-based) | Location | Value | x, y |
|----------------|----------|-------|------|
| 1 | OBS 4007(B) Business Name | legal_name | 155, 223 |
| 11 | Worksheet "BUSINESS NAME:" | short_name | 105, 101 |
| 15 | CalRecycle 74 Contractor/Company Name | short_name | 145, 296 |
| 23 | STD 204 Section 1 NAME | legal_name | 22, 97 |

## Irregular AcroForm field names

The source field names are hand-authored and inconsistent. The script's
`LINE_FIELD_IDS` map encodes the quirks. Known oddities:

- Row 1 line field: `"OBS Line-Item Cost Wrksht - Line Itm - L1"` (note the extra " - ")
- Row 2 qty/line use `"Line Itm L2"` / `"Qty L2"` (different casing/spacing vs other rows)
- Row 5 ext-price: `"OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext Price L5"` (duplicated prefix)
- Row 6 ext-price: `"OBS Line-Item Cost Wrksht L6"`
- Rows 13/18/23 ext-price: `"OBS Line-Item Cost Wrksht L13"`, `"...wrksht L18"`, `"...Wrksht L23"`

If the fill script reports an invalid field ID, re-extract with the pdf skill's
`extract_form_field_info.py` and reconcile, rather than guessing.

## Fields intentionally left blank (State fills these)

Method-of-award sub-options on page 3, SCPRS reference number (PD 843), PO# / RFQ#
boxes (CalRecycle 74), and the entire STD 204 Section 6 paying-agency block.
