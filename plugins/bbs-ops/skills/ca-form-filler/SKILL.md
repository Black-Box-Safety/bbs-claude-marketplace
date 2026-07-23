---
name: ca-form-filler
description: >
  Use this skill whenever a Black Box Safety sales rep needs to fill out California
  state compliance forms for a bid or RFQ response. Triggers include: any mention
  of "state forms", "bid packet", "compliance forms", "STD 204", "STD 205",
  "DGS PD 843", "CV 012", "DGS PD 1", "OBS 1000", "CalRecycle 74", "form packet",
  "fill out the forms", "bid submission forms", or any upload of a PDF that appears
  to contain blank California state government forms. Also trigger when the rep says
  "I need to respond to this RFQ" alongside a form packet upload. The skill reads
  the vendor profile, extracts RFQ-specific data from the uploaded documents, maps
  all fields across all required forms, fills what can be pre-filled, flags all
  signature lines, and produces filled PDFs ready for rep review and submission.
compatibility: claude-code
---
> **BBS Ops pipeline — stage: Quote bot.** See `site-wiring-map` for how this fits the whole flow.

# California State Compliance Form Filler

## Overview

This skill automates the completion of California state bid compliance forms for
Black Box Safety. It combines static vendor profile data with RFQ-specific data
extracted from uploaded documents to produce a filled form packet.

**Optimized for Claude Code** — persistent filesystem, browser PDF preview,
iterative fix/verify loop without re-uploading source files.

**Inputs:**
- RFQ document (PDF) — for agency info, solicitation number, due date, line items
- Form packet (PDF) — blank CA state forms to be filled

**Output:**
- Filled PDF(s) with all pre-fillable fields completed
- Signature lines clearly flagged with `⚑ SIGNATURE REQUIRED`
- Cover summary (markdown) with fields filled, signature requirements, and gap report

**Vendor profile:** `~/.bbs/vendor_profile.json` (persistent across sessions)
**PDF scripts:** `~/.bbs/pdf_scripts/` (persistent helper scripts — see Setup below)
**Output directory:** `~/bbs_forms/[YYYYMMDD_AgencyShortName]/`

---

## Setup (First Run Only)

On first use, create the persistent directory structure and copy the pdf skill
scripts so they persist across sessions:

```bash
mkdir -p ~/.bbs/pdf_scripts
mkdir -p ~/bbs_forms

# Copy pdf skill scripts to persistent location
cp /mnt/skills/public/pdf/scripts/* ~/.bbs/pdf_scripts/

# Write vendor profile to persistent location
cat > ~/.bbs/vendor_profile.json << 'PROFILE'
PASTE_VENDOR_PROFILE_JSON_HERE
PROFILE
```

The vendor profile JSON is stored in `references/vendor_profile.json` inside
this skill package. Copy its contents into the above command on first run.

Check setup is complete:
```bash
ls ~/.bbs/pdf_scripts/
cat ~/.bbs/vendor_profile.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('Profile OK:', d['business_identity']['legal_name'])"
```

---

## CRITICAL RULES

1. **Never invent data.** If a field value is not in the vendor profile or cannot
   be extracted from the RFQ, mark it `[MISSING — NEEDS INPUT]` in the output
   and list it in the cover summary gap report. Do not guess or approximate.

2. **Never pre-fill signature fields.** Leave all `/Sig` type fields blank.
   Add a text annotation adjacent to each signature line:
   `⚑ SIGNATURE REQUIRED — Parker Marshall, Sales Manager`
   Date of signing is also left blank — completed at submission time.

3. **Vendor profile is the authority for all static BBS data.** Do not accept
   corrections to legal name, FEIN, cert numbers, or other static fields from
   the RFQ document. If the RFQ pre-fills a BBS field incorrectly, flag it.

4. **DVBE cert expiration must be checked** against the RFQ due date before
   filling any form. If expired or within 30 days of expiry, hard stop and flag.

5. **CalRecycle 74 is always RFQ-specific.** No static vendor data applies to
   line items. All recycled content % and SABRC codes must come from the rep.

6. **Always verify output visually.** After filling, rasterize key pages and
   inspect before delivering. Fix and re-run if any field is misplaced.

---

## Step 1 — Load Vendor Profile

```python
import json
from pathlib import Path

profile_path = Path.home() / ".bbs" / "vendor_profile.json"
with open(profile_path) as f:
    vp = json.load(f)

# Convenience accessors
legal_name  = vp["business_identity"]["legal_name"]
fein        = vp["business_identity"]["fein"]
address     = f"{vp['address']['mailing_street']}, {vp['address']['city']}, {vp['address']['state']} {vp['address']['zip']}"
phone       = vp["contact"]["phone"]
email       = vp["contact"]["email"]
rep         = vp["authorized_representatives"][0]
dvbe_cert   = vp["certifications"]["dvbe"]["osds_ref_number"]
dvbe_exp    = vp["certifications"]["dvbe"]["expiration"]  # MM/DD/YYYY
sellers_permit = vp["business_identity"]["ca_sellers_permit"]
```

Check `_meta.notes` and surface any warnings before proceeding.

---

## Step 2 — Extract RFQ Data

```bash
# Quick text check first
pdftotext -f 1 -l 2 /path/to/rfq.pdf - | head -60
```

```python
import pdfplumber

rfq_data = {
    "solicitation_number": None,
    "agency_name": None,
    "agency_address": None,
    "agency_phone": None,
    "agency_fax": None,
    "agency_email": None,
    "quote_due_date": None,
    "date_of_request": None,
    "description_of_purchase": None,
    "line_items": []
}

with pdfplumber.open("/path/to/rfq.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        # Parse fields from text using string search
        # Look for: RFQ #, solicitation number, agency name, due date, contact info
```

**DVBE expiration check** — run immediately after loading rfq_data:

```python
from datetime import datetime

dvbe_exp_date = datetime.strptime(dvbe_exp, "%m/%d/%Y")
due_date = datetime.strptime(rfq_data["quote_due_date"], "%m/%d/%Y") if rfq_data["quote_due_date"] else datetime.today()
days_to_exp = (dvbe_exp_date - due_date).days

if days_to_exp < 0:
    raise SystemExit("⛔ DVBE CERT EXPIRED — do not proceed. Cert expired on " + dvbe_exp)
elif days_to_exp < 30:
    print(f"⚠️  WARNING: DVBE cert expires in {days_to_exp} days ({dvbe_exp}). Flag to rep.")
```

---

## Step 3 — Identify Forms and Check Fields

```bash
# Check if form packet has fillable fields
python3 ~/.bbs/pdf_scripts/check_fillable_fields.py /path/to/forms.pdf
```

```bash
# If fillable — extract all field IDs with page numbers and coordinates
python3 ~/.bbs/pdf_scripts/extract_form_field_info.py /path/to/forms.pdf /tmp/fields.json
```

```bash
# Extract text structure to identify which forms are present and on which pages
pdftotext /path/to/forms.pdf - | grep -n "STD 204\|STD 205\|PD 843\|CV 012\|Darfur\|CalRecycle\|OBS 1000\|GenAI\|GSPD"
```

**Canonical form detection:**

| Form ID       | Key Text to Match                              |
|---------------|------------------------------------------------|
| STD 204       | "PAYEE DATA RECORD" / "STD 204"               |
| STD 205       | "PAYEE DATA SUPPLEMENT" / "STD 205"           |
| DGS PD 843    | "DISABLED VETERAN BUSINESS ENTERPRISE" / "843"|
| GSPD-05-105   | "BIDDER DECLARATION" / "GSPD-05-105"          |
| DGS PD 1      | "DARFUR" / "PD 1"                             |
| OBS 1000      | "GENERATIVE AI" / "OBS 1000"                  |
| CalRecycle 74 | "CALRECYCLE" / "RECYCLED CONTENT" / "SABRC"   |
| CV 012        | "COMMERCIALLY USEFUL FUNCTION" / "CV 012"     |

Report identified forms to rep before filling. Flag any unrecognized forms.

---

## Step 4 — Field Mapping Reference

Source key: **VP** = vendor_profile | **RFQ** = rfq_data | **DERIVED** = runtime | **⚑ SIG** = leave blank

### STD 204 — Payee Data Record
| Field | Source | Value |
|-------|--------|-------|
| Legal Name (Section 1) | VP | `legal_name` |
| Mailing Address | VP | `address` |
| City / State / Zip | VP | parsed from `address` |
| Email | VP | `email` |
| Entity Type checkbox | VP | S-Corp → check "Corporation — All Others" |
| FEIN (Section 3) | VP | `fein` (format: XX-XXXXXXX) |
| CA Resident (Section 4) | VP | Check "California Resident" |
| Rep Name (Section 5) | VP | `rep.full_name` |
| Rep Title (Section 5) | VP | `rep.title` |
| Rep Phone (Section 5) | VP | `phone` |
| Rep Email (Section 5) | VP | `email` |
| Agency Name (Section 6) | RFQ | `rfq_data.agency_name` |
| Agency Address (Section 6) | RFQ | `rfq_data.agency_address` |
| Agency Phone/Fax (Section 6) | RFQ | `rfq_data.agency_phone` / `agency_fax` |
| Signature (Section 5) | ⚑ SIG | Leave blank |
| Date (Section 5) | ⚑ SIG | Leave blank |

**Critical note on STD 204 field IDs:** The fillable field IDs on this form
frequently do NOT match visual section labels. After extracting field info,
**always rasterize the page and visually confirm coordinate positions** before
mapping field IDs to values. The FEIN field and Section 5 rep fields are
commonly misnamed in the PDF metadata.

```bash
# Rasterize page 1 at 150 DPI to confirm field positions
pdftoppm -jpeg -r 150 -f 1 -l 1 /path/to/forms.pdf /tmp/std204_verify
# Then open /tmp/std204_verify-1.jpg to inspect
```

### DGS PD 843 — DVBE Declaration
| Field | Source | Value |
|-------|--------|-------|
| DVBE Name (Section 1) | VP | `legal_name` |
| DVBE Ref Number (Section 1) | VP | `dvbe_cert` |
| Solicitation # (Section 1) | RFQ | `rfq_data.solicitation_number` |
| Not broker/agent checkbox (Section 2) | VP | Check (broker_or_agent = false) |
| DV Owner Name (Section 3) | VP | `dvbe_details.veteran_owner_name` |
| DV Owner Address (Section 3) | VP | `dvbe_details.veteran_owner_address` |
| DV Owner Phone (Section 3) | VP | `dvbe_details.veteran_owner_phone` |
| DV Owner Tax ID (Section 3) | VP | `dvbe_details.veteran_owner_tax_id` |
| All signatures | ⚑ SIG | Leave blank — perjury certification |
| All dates | ⚑ SIG | Leave blank |

### GSPD-05-105 — Bidder Declaration
| Field | Source | Value |
|-------|--------|-------|
| Certification(s) | VP | "DVBE" |
| Certification # | VP | `dvbe_cert` |
| Subcontractors used | VP | Check "No" |
| Broker or agent (1c-1) | VP | Check "No" |
| Equipment rental 51% (1c-2) | VP | Check "N/A" |
| Distinct element of work | VP | `cuf_statement` (abbreviated) |
| Solicitation # | RFQ | `rfq_data.solicitation_number` |
| Page # | DERIVED | "1 of 1" |

### DGS PD 1 — Darfur Act Certification
| Field | Source | Value |
|-------|--------|-------|
| Company Name | VP | `legal_name` |
| FEIN | VP | `fein` |
| Paragraph 1 initials | VP | `rep.full_name` initials (darfur = no foreign ops) |
| Printed Name + Title | VP | `rep.full_name`, `rep.title` |
| County and State | DERIVED | "San Diego County, California" |
| Signature | ⚑ SIG | Leave blank |
| Date | ⚑ SIG | Leave blank |

### OBS 1000 — GenAI Disclosure
| Field | Source | Value |
|-------|--------|-------|
| Company Name | VP | `legal_name` |
| Address | VP | `address` |
| Phone | VP | `phone` |
| Solicitation # | RFQ | `rfq_data.solicitation_number` |
| Contract Description | RFQ | `rfq_data.description_of_purchase` |
| Uses GenAI? | VP | Check "No" (uses_genai = false) |
| All conditional fields | VP | Skip — uses_genai = false |
| Rep Name | VP | `rep.full_name` |
| Signature | ⚑ SIG | Leave blank |
| Date | ⚑ SIG | Leave blank |

### CalRecycle 74 — Recycled Content Certification
| Field | Source | Value |
|-------|--------|-------|
| Contractor/Company Name | VP | `legal_name` |
| Address | VP | `address` |
| Phone | VP | `phone` |
| RFQ # | RFQ | `rfq_data.solicitation_number` |
| Item # / Description | RFQ | From `rfq_data.line_items` |
| Postconsumer Recycled % | REP | `[MISSING — REP TO CONFIRM]` |
| SABRC Category Code | REP | `[MISSING — REP TO CONFIRM]` |
| Print Name | VP | `rep.full_name` |
| Title | VP | `rep.title` |
| Signature | ⚑ SIG | Perjury cert — leave blank, flag prominently |
| Date | ⚑ SIG | Leave blank |

---

## Step 5 — Fill the Forms

### 5A — Fillable PDFs (preferred path)

```bash
# Validate field values before filling
python3 ~/.bbs/pdf_scripts/check_bounding_boxes.py /tmp/field_values.json
```

```bash
# Fill using the skill script
python3 ~/.bbs/pdf_scripts/fill_fillable_fields.py \
    /path/to/forms.pdf \
    /tmp/field_values.json \
    ~/bbs_forms/[output_dir]/[FormID]_filled.pdf
```

**field_values.json format:**
```json
[
  {
    "field_id": "exact_id_from_extract_form_field_info",
    "description": "human readable label",
    "page": 1,
    "value": "the value to fill"
  }
]
```

### 5B — Flat/Scanned PDFs (fallback)

```bash
# Extract structure for coordinate-based placement
python3 ~/.bbs/pdf_scripts/extract_form_structure.py /path/to/forms.pdf /tmp/structure.json

# Rasterize all pages for visual coordinate mapping
pdftoppm -jpeg -r 150 /path/to/forms.pdf /tmp/form_pages
```

Then use `fill_pdf_form_with_annotations.py` with image or PDF coordinates.
See `/mnt/skills/public/pdf/FORMS.md` for full coordinate mapping workflow.

### 5C — Verify Every Output

After filling each form, **always** rasterize and inspect before delivery:

```bash
pdftoppm -jpeg -r 150 -f 1 -l 2 ~/bbs_forms/[output]/filled.pdf /tmp/verify
# Inspect /tmp/verify-1.jpg, /tmp/verify-2.jpg
```

If any field is misplaced: adjust coordinates or field ID mapping, re-fill, re-verify.
Do not deliver until visual inspection confirms correct placement.

### Output naming convention:
```
~/bbs_forms/YYYYMMDD_[AgencyShortName]/
  BBS_STD204_[Agency]_[SolNum]_[YYYYMMDD].pdf
  BBS_PD843_[Agency]_[SolNum]_[YYYYMMDD].pdf
  BBS_GSPD05105_[Agency]_[SolNum]_[YYYYMMDD].pdf
  BBS_Darfur_[Agency]_[SolNum]_[YYYYMMDD].pdf
  BBS_CalRecycle74_[Agency]_[SolNum]_[YYYYMMDD].pdf
  BBS_OBS1000_[Agency]_[SolNum]_[YYYYMMDD].pdf
  cover_summary.md
```

---

## Step 6 — Generate Cover Summary

Write `cover_summary.md` to the output directory:

```markdown
# BBS Form Packet — [Agency Name]
**RFQ/Solicitation:** [number or MISSING]
**Due Date:** [date]
**Generated:** [today]

## A — Fields Filled
| Form | Field | Value | Source |
|------|-------|-------|--------|
| STD 204 | Legal Name | Black Box Safety, Inc. | VP |
...

## B — Signature Requirements
⚑ All forms require wet signature from Parker Marshall, Sales Manager.
Date of signing to be completed at time of submission.
Forms requiring signature: [list]

⚑ PERJURY CERTIFICATIONS (sign only after verifying content):
- CalRecycle 74 — verify all recycled content % and SABRC codes before signing
- DGS PD 843 — perjury certification for DVBE declarations

## C — Gap Report
[List any MISSING fields with form name, field name, and what rep needs to provide]
[If none: "No missing fields — packet is complete pending signatures."]
```

---

## Step 7 — Deliver

```bash
# Open output directory for rep to access files
ls -la ~/bbs_forms/[output_dir]/

# Open filled PDFs in browser for final visual review
open ~/bbs_forms/[output_dir]/*.pdf   # macOS
xdg-open ~/bbs_forms/[output_dir]/   # Linux
```

Print the cover summary to chat. Explicitly call out:
- Any DVBE cert expiration warnings
- CalRecycle 74 perjury certification reminder
- All gap report items requiring rep input

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| STD 204 field IDs misaligned to visual sections | Always rasterize page 1 and verify before filling; adjust field_id mapping |
| Form not in canonical list | Flag to rep; do not fill; ask for guidance |
| DVBE cert expired or within 30 days | Hard stop before any filling |
| RFQ solicitation number not found | Flag in gap report; ask rep to provide; use `[MISSING]` as placeholder |
| Form packet is flat/scanned PDF | Use coordinate-based annotation approach (Step 5B) |
| Agency includes non-standard forms | Flag as unrecognized; ask rep to confirm requirements |
| Rep uploads forms only, no RFQ | Ask for RFQ or collect solicitation data manually before proceeding |
| Multiple authorized signers | Ask rep which signer before filling |
| CalRecycle 74 — no line items provided | Fill company header; mark all item rows `[MISSING — REP TO PROVIDE]` |
| DGS PD 843 DVBE owner fields null | Halt on PD 843 only; fill remaining forms; list missing fields |
| Font not found warning during fill | Non-blocking; proceed — output will use default font substitution |
| Field value truncated in small box | Abbreviate to fit; note full value in cover summary |
