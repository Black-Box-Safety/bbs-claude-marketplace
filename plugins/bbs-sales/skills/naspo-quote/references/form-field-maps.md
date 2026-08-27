# CA state form field maps

Field names verified against the blank forms CDCR sends with NASPO RFQs. If an
agency sends a different revision, re-run `scripts/inspect_form.py` — names drift
between form revisions, and a wrong name fails silently (the field just stays empty).

Contents:
- [OBS RFQ Line-Item Cost Worksheet (07-2024)](#obs-rfq-line-item-cost-worksheet-07-2024)
- [CalRecycle 74 (01-2023)](#calrecycle-74-01-2023)
- [DGS PD 843 DVBE Declarations (09-2019)](#dgs-pd-843-dvbe-declarations-09-2019)
- [Darfur Contracting Act OBS 1500 (06-2011)](#darfur-contracting-act-obs-1500-06-2011)
- [OBS 1000 GenAI Reporting (10-2025)](#obs-1000-genai-reporting-10-2025)
- [Bidder Declaration GSPD-05-105 (08/09)](#bidder-declaration-gspd-05-105-0809)
- [STD 204 Payee Data Record](#std-204-payee-data-record)
- [CV 012 Commercially Useful Function](#cv-012-commercially-useful-function)
- [Other forms seen in the corpus](#other-forms-seen-in-the-corpus)

---

## OBS RFQ Line-Item Cost Worksheet (07-2024)

Every field is prefixed `OBS Line-Item Cost Wrksht - `. 23 line rows.

| Purpose | Field |
|---|---|
| Solicitation | `…Solicitation#` |
| Vendor | `…BUSINESS NAME` |
| Row 1 (note the inconsistent naming) | `…Line Itm - L1`, `…QTY L1`, `…Unit L1`, `…Descriptions L1`, `…Itm/Part# L1`, `…PCRC L1`, `…Unit Price L1`, `…Ext Price L1` |
| Row 2 | `…Line Itm L2`, `…Qty L2`, `…Unit L2`, `…Descriptions L2`, `…Itm/Part# L2`, `…PCRC L2`, `…Unit Price L2`, `…Ext Price L2` |
| Rows 3-23 | `…Line Itm# L{n}`, `…QTY L{n}`, `…Unit L{n}`, `…Description L{n}` (singular!), `…Itm/Part# L{n}`, `…PCRC L{n}`, `…Unit Price L{n}`, `…Ext Price L{n}` |
| Totals | `…Subtotal`, `…S&H`, `…Grand Total` |
| Comments | `…Comment Text` |

Row 1, row 2, and rows 3-23 each use different naming for the same columns
(`Line Itm - L1` / `Line Itm L2` / `Line Itm# L3`; `Descriptions` vs `Description`).
Generate row field names from a table rather than a loop, or you will write into
nothing on rows 2+. Row 5's extended-price field is also misnamed in the PDF:
`OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext Price L5`.

The description column clips around 55 characters at 8pt — set `fontsize` ~6.5 or
abbreviate. The form itself prints "Do not include sales tax."

## CalRecycle 74 (01-2023)

| Purpose | Field |
|---|---|
| Agency block | `State Agency`, `Purchasing Agent`, `PO`, `Phone`, `Email` |
| Vendor block | `ContractorCompany Name`, `Address`, `Phone_2` |
| Row n (1-6) | `Purchase Order  RFQ  RFP  IFB  Cal Card Order Row{n}` (two spaces after "Order"), `Item Row{n}`, `Product or Services DescriptionRow{n}`, `1Percent Postconsumer Recycled Content MaterialRow{n}`, `2SABRC Product Category CodeRow{n}`, `SABRC compliant{n}` (checkbox) |
| Sign-off | `Print Name`, `Signature` (text field — stamp the image), `Title`, `Date` |

`Meets SABRC` is unchecked on every filed copy in the corpus — fill the percentage
and code columns and leave it alone unless a buyer asks. For which code and
percentage to use, see `calrecycle-sabrc-guide.md`; the answer follows the
product's material, not a fixed default.

## DGS PD 843 DVBE Declarations (09-2019)

| Purpose | Field |
|---|---|
| Section 1 | `DVBEname`, `DVBErefno`, `description`, `SCno`, `SCPRS Reference Number` (state use — leave blank) |
| Section 2 radio | `YNagent` — widget 0 (top, y≈215) = "DVBE is **not** a broker or agent", export `1`; widget 1 (y≈250) = "is a broker", export `0` |
| Owner 1 | `DVBEowner1`, `DVBEowner1signature` (/Sig), `DVBEowner1date` |
| Owner 2 | `DVBEowner2`, `DVBEowner2signature`, `DVBEowner2date` |
| Section 3 (rental only) | `OwnBusiness`, `OwnEquipment`, `DVBEowner3*`, `Principal*` |
| Manager | `DVBEmgr`, `DVBEmgrSignature`, `DVBEmanagerDate` |
| Footer | `PageNo`, `TotalPages` |

Section 3 applies only when renting equipment — leave the whole block blank for a
goods purchase. `description` and `SCno` clip around 45 characters.

## Darfur Contracting Act OBS 1500 (06-2011)

Option #1 (no business activities outside the US) is BBS's answer.

| Purpose | Field |
|---|---|
| Header | `BidAgreement Number OR Request for Quote Number` (narrow — bare number only) |
| Option 1 | `CompanyVendor Name Printed`, `Date`, `By Authorized Signature` (text field — stamp) |
| Option 2 / 3 | `*_2` / `*_3` variants — leave blank |

The Option 1 signature box prints its caption inside the box, so stamp with
`dx: 150, dy: 4` to land right of the caption.

## OBS 1000 GenAI Reporting (10-2025)

| Purpose | Field |
|---|---|
| Page 1 header | `Solicitation / Contract`, `Number Bidder ID/ Vendor ID (opitional)` [sic], `Business Name`, `Business Telephone Number`, `Business Address`, `City`, `State`, `Zip Code` |
| Description | `Contract  Description of Purchase` (two spaces) |
| GenAI radio | `Is GenAI utilized?` — widget 0 = Yes (`Yes`), widget 1 = No (`No`) |
| Pages 2-3 | GenAI detail questions 1-5, `Will training be provided?` — all blank when GenAI = No |
| Sign-off (p2) | `Signature` (/Sig — stamp), `Date` |

## Bidder Declaration GSPD-05-105 (08/09)

Checkbox names give no hint of meaning; this is the mapping:

| Field | Meaning | BBS answer |
|---|---|---|
| `Solicitaion #` [sic] | header | bare solicitation number (narrow) |
| `Text1` | 1a certification line | `DVBE` (clips past ~14 chars) |
| `Check Box1` | 1a "None" | off |
| `Check Box2` / `Check Box3` | 1b subcontractors Yes / **No** | check Box3 |
| `Product list` | 1b distinct element of work | CUF statement, ~2 lines |
| `Check Box4` / `Check Box5` | 1c-1 broker or agent Yes / **No** | check Box5 |
| `Check Box6` / `Check Box7` / `Check Box8` | 1c-2 51% rental Yes / No / **N/A** | check Box8 |
| `page`, `of #` | footer | `1`, `1` |
| Rows `Name, phone, fax*` etc. | subcontractor table | blank |

No signature widget — the form's certification reads "By signing the bid
response," so the signed quote covers it.

## STD 204 Payee Data Record

Only needed for a first-time payee relationship, not routine NASPO reorders.
Field IDs are misaligned with the visible sections on some revisions — run
`inspect_form.py --render` and confirm positions before filling.

Names seen on filed copies: `NAME (This is required...)`, `MAILING ADDRESS
(number, street, apt. or suite no.) (See instructions on Page 2)`, `CITY STATE ZIP
CODE`, `Federal Employer Identification Number (FEIN)`, `corpOthers` (Corporation —
all others), `calRes` (California resident), `NAME OF AUTHORIZED PAYEE
REPRESENTATIVE`, `TITLE`, `TELEPHONE include area code`, `EMAIL ADDRESS`,
`STATE AGENCYDEPARTMENT OFFICE`, `UNITSECTION`, `DATE`. A shorter-named revision
uses `nameReq1`, `taxIDNumber`, `certName`, `certTelephone`, `remAddress1`.

## CV 012 Commercially Useful Function

CalVet and CMD send this one; it is not in the CDCR set. XFA-style names:

| Purpose | Field |
|---|---|
| DBA | `form1[0].#subform[0].DoingBusinessAs[0]` |
| OSDS ref | `form1[0].#subform[0].OSDSRefNumber[0]` |
| Cert expiration | `form1[0].#subform[0].ExpirationDate[0]` |
| Solicitation | `form1[0].#subform[0].SolicitationNumber[0]` |
| CUF questions | `form1[0].#subform[0].RadioButtonList[0..5]` — BBS answers `/0 /0 /0 /0 /1 /1` |
| Sign-off | `form1[0].#subform[1].PrintedName[0]`, `…Title[0]`, `…Date[0]` |

Verify the question order on the revision in hand before copying the radio
pattern — the pattern only means anything against the same questions.

## Other forms seen in the corpus

- **CV 031 Request for Quote Worksheet**, **CV 039 Fair and Reasonable**, and a
  **VSDS Form** arrive with CalVet packets. Not yet mapped — run `inspect_form.py`
  when one lands and add it here.
- **Darfur OBS 1500** and **OBS 1000** each circulate in more than one revision
  with different field names; see `filled-form-precedents.md`.
