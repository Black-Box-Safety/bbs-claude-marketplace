# Where things live

Map of the customer document store, written for someone reconciling an order they did not
originally handle.

## Contents

- [The root](#the-root)
- [Finding the project without browsing](#finding-the-project-without-browsing)
- [Inside a mature project folder](#inside-a-mature-project-folder)
- [Reading a per-PO order sheet](#reading-a-per-po-order-sheet)
- [Anatomy of a CA state PO](#anatomy-of-a-ca-state-po)
- [Naming traps](#naming-traps)

---

## The root

```
OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER/Customers/
```

Roughly 250 entries. Top level is mostly organizations, but loose files and one-off PDFs
also sit there — do not assume everything at the top level is a folder.

Agency hierarchies go deeper than expected. An institution is usually not the top level:

```
Customers/CDCR/                          ← department
Customers/CDCR/DRP_/                     ← division (Rehabilitative Programs)
Customers/CDCR/DRP_/PLUMBING 2026/       ← the award
Customers/CDCR/DRP_/carpentry-2026/      ← sibling award, same division
Customers/CDCR/Folsom State Prison/      ← institution, for direct business
```

A given institution therefore appears in two places: under the division award that ships
to it, and under its own folder for business it placed itself. When an order problem
involves a multi-institution award, the division folder is the one that holds the records.

Some agencies exist under several spellings at the top level (`CDCR` and
`CA Dept. of Corrections and Rehabilitation`, `CalTrans` and
`California Department of Transportation District 11`). Search rather than browse.

## Finding the project without browsing

By PO number — the reliable way:

```bash
grep -rl "4500755180" "Black Box Safety - MASTER/Customers" 2>/dev/null
```

By item, when you do not have a PO:

```bash
grep -rl "34-874" "Black Box Safety - MASTER/Customers" 2>/dev/null | head -20
```

`grep -rl` only reaches text files and OCR output, not the inside of .xlsx or .pdf. To
search spreadsheet contents, use the openpyxl walk in the main skill, run from the project
root once you have narrowed down to a project.

When several folders match, the working copy is the one with `_ocr/` and processing
sheets. Ignore matches under `_ARCHIVE-*`, `DO NOT USE*`, `* copy`, and `.zip`.

## Inside a mature project folder

A fully processed award looks roughly like this:

```
PLUMBING 2026/
├── DRP PO's/                    Customer PO PDFs, one per institution
│   └── _ocr/                    <INST>_combined.txt — searchable text
├── 1. Processing Sheets/        <INST>_PO_<number>_Order_Sheet.xlsx
│   ├── Consolidated_Order_List.xlsx    every line, every institution
│   └── QA_Rollup.md
├── 2. Orders/                   vendor-facing order artifacts
├── BC Import/
│   └── SO Lines/                <INST>_SO-lines_<PO>.xlsx — what went into BC
├── Grainger Quote PDFs/         vendor quotes backing the bid
├── Grainger Items/
├── presubmission-work/          what we bid and how we got there
│   ├── Final ... submission.xlsx        the line-item cost worksheet submitted
│   ├── <date> submission breakdown.xlsx per-institution split
│   └── Sourcing/                        the working sourcing files
├── prison-folders/              per-institution copies, often with rep notes
└── scripts/                     the build scripts and a HANDOFF primer
```

Not every project is this complete. Older or smaller ones may be a single spreadsheet and
a PDF. The four records from the main skill still exist somewhere — they are just less
tidily separated.

Note `presubmission-work/` in particular. This is the only place that holds **why** a line
was priced the way it was, and it is where UOM and cross-reference errors are visible.

## Reading a per-PO order sheet

`<INST>_PO_<number>_Order_Sheet.xlsx` typically carries these tabs:

| Tab | What it is good for |
|---|---|
| `Dashboard` | Award date, totals, line count, flagged action items |
| `Order Sheet` | The line-by-line record. Both our internal line # and the PO line # |
| `Vendor Action Lists` | Grouped by vendor — **the Notes column here carries rep comments** |
| `Distec Order Pack` | Special-order items routed through Grainger DISTEC |
| `Other Vendors` | Anything not on Grainger, or pending sub approval |
| `Open Items` | Blockers and functional-equivalent subs, with reasons |
| `Quote vs PO Validation` | Lines whose part number could not be located in the OCR'd PO |

Two columns matter more than the rest when reconciling:

- **`Line #` vs `PO Line #`** — these are different numbers for the same row. The customer
  always means the PO line number. Our sheets and BC often key off the internal one.
  Mixing them up sends you to the wrong item.
- **`Notes`** on `Vendor Action Lists` — free text where the person processing the order
  recorded what they noticed. Short entries like "mismatched UOM", "need to order in
  different UOM", or "shipped in multiples of 12" are often the earliest record that
  someone saw the problem months ago.

`Quote vs PO Validation` flags are frequently just OCR misreads, not real mismatches. Treat
them as a list to spot-check, not as findings.

## Anatomy of a CA state PO

CDCR and most state agencies issue on STD. 65 (first page) and STD. 65A (continuation).
The OCR text preserves the order of the printed fields, so these land in predictable spots.

Page 1 header, in order:

- Number of items, date, **amendment number**, PO number
- Ship-to institution and address; bill-to (Accounts Payable)
- Agency billing code and **purchasing authority number** (e.g. `CDCR-5225`)
- **Leveraged Procurement Agreement number** — the contract, e.g. `7-25-51-02.03`
- A local institution contact with name and extension
- `CONTACT NAME` and `CONTACT E-MAIL ADDRESS` — **the buyer.** This is who amendments go to
- Supplier block (us), payment terms, certification numbers
- Subtotal, tax rate, tax, grand total
- Program / category, fund title, and the object of expenditure code
- `AUTHORIZING NAME` / `AUTHORIZING TITLE` — **the Procurement Official who signed**

Line items then run across the continuation pages in this column order:

```
ITEM NUMBER | QUANTITY | UNIT | UNSPSC | RECYCLED | DESCRIPTION | CATEGORY | UNIT PRICE | EXTENSION
```

OCR splits these across lines, so grep with generous context (`-B8 -A8`) and read the
block rather than a single matched line. The quantity sometimes lands on the line above
the unit.

The `UNIT` column is the field to read first. `EA`, `PAC`, `PK`, `PR`, `CS`, `BX` — and the
description usually repeats the pack count in words ("Pack of 12"). When the unit says
`PAC` and the unit price looks like a single-item price, you have found the problem.

An amended PO carries a non-zero `AMENDMENT NO.` in the header. If you are looking for
whether an amendment ever landed, that field is the check.

## Naming traps

- Misspellings are load-bearing. `Pumbing` is a real folder. Search both spellings.
- Trailing underscores distinguish real folders: `DRP_` vs `DRP- SPRING 2026`.
- `copy` and `.zip` duplicates of the same agency folder are common and usually stale.
- Institution abbreviations are used inconsistently: `CTF` / `Correctional Training
  Facility` / `Soledad` all refer to the same place. So do `SQ` / `San Quentin` and `VSP` /
  `Valley State Prison`. Grainger account names and folder names rarely use the same one.
- Year-suffixed siblings (`carpentry-2026`, `PLUMBING 2026`) are separate awards that share
  sourcing data. When an error is in shared sourcing, check the siblings.
