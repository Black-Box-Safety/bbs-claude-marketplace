---
name: obs-form-filler
description: Fill out the CDCR OBS 4007(B) "RFQ Packet-B" California state compliance forms for Black Box Safety (BBS). Use this skill whenever a BBS rep needs to respond to a CDCR (Department of Corrections and Rehabilitation) informal competitive RFQ — i.e. whenever they upload or mention a blank OBS 4007(B) packet, "Packet B", "OBS 4007", a CDCR RFQ, or ask to fill out the bid forms / compliance packet for a CDCR quote. Also trigger when a rep provides a quote (product, price, quantity) plus a solicitation number and asks to "fill the OBS form", "redo this on the new forms", "complete the bid packet", or "fill out the CDCR forms". The rep supplies the quote line items, the dates, the agency contact info, and their own rep info (name/title/email); this skill merges in BBS's fixed vendor profile, fills all 9 sub-forms, embeds signatures, and produces a submission-ready PDF. Do NOT use for non-CDCR bid packets, NASPO/Grainger-routed quotes, or generic California state forms unrelated to the OBS 4007(B) packet.
---
> **BBS Ops pipeline — stage: Quote bot.** See `site-wiring-map` for how this fits the whole flow.

# OBS 4007(B) Packet-B Filler — Black Box Safety

## What this does

Black Box Safety responds to CDCR informal competitive RFQs by completing a 9-form
"Packet B": OBS 4007(B), Line-Item Cost Worksheet, Bidder Declaration (GSPD-05-105),
Darfur Contracting Act (OBS 1500), CalRecycle 74, GenAI Factsheet (OBS 1000),
DVBE Declarations (DGS PD 843), Supplement Vendor Payee Data Record, and Payee Data
Record (STD 204).

The packet is the same every time except for (a) the quote line items, (b) the dates
and solicitation number, (c) the agency requestor/ship-to info, and (d) which rep is
signing the bidder line. Everything else — BBS's address, FEIN, seller's permit, DVBE
cert, the DVBE owner's signature, the accounting contact — is fixed and lives in the
bundled vendor profile so the rep never re-keys it.

## The model behind the form (read this — it prevents the common mistakes)

Two different people sign this packet, and conflating them is the #1 error:

- **The rep** signs the *bidder* lines: OBS 4007(B) bidder signature, the Darfur
  certification, the CalRecycle 74 certification. The rep is a **variable** — a
  different salesperson may quote and sign each job. Their name/title/email/signature
  come from the rep's input.
- **Jackson Dalton** (DV owner, President) signs the *ownership* lines: DGS PD 843
  (DVBE owner declaration) and STD 204 (authorized payee representative). These are
  tied to who *owns* the certified DVBE, not to who quoted the job, so they are fixed
  regardless of which rep is responding.

Other rules baked into the script, with the reasoning:

- **Agency-side fields stay blank.** Method-of-award detail, SCPRS ref number, PO#,
  and the STD 204 paying-agency block are filled in by the State, not the bidder.
- **CalRecycle 74 is never left blank.** A missing CalRecycle 74 can disqualify the
  bid. BBS resells finished goods and rarely certifies a postconsumer percentage, so
  PCRC defaults to "NA"/"NA". Only override if the rep gives a real percentage.
- **Signature dates** are filled if provided. If the rep wants to wet-sign and date by
  hand, pass an empty string for `signature_date` and the date lines stay blank.
- **Four company-name lines have no fillable field** (OBS 4007(B) Business Name, the
  worksheet Business Name header, CalRecycle 74 Contractor/Company Name, and STD 204
  Section 1 NAME). The script writes those as text annotations at known coordinates —
  the rep doesn't need to do anything.

## Workflow

### 1. Read the inputs
The rep will give you a quote (either pasted as text, or as an uploaded PDF/xlsx) plus
a solicitation number, dates, agency contact, and their own rep info. If a quote file
is uploaded, extract the line items from it (qty, unit, description, part number, unit
price). For Grainger-cart PDFs or DWR/Grainger sources, prefer the relevant existing
BBS extraction skill, then bring the items here.

If the rep doesn't specify a `signature_date`, default it to today's date in `M.D.YY`
format (matching BBS's house style, e.g. `5.28.26`). If they don't give a rep, default
to Parker Marshall, Sales Manager, parker@blackboxsafety.com.

### 2. Build the inputs JSON
Copy `assets/inputs_template.json` and fill it in. Schema:

- `solicitation_number`, `release_date` (MM/DD/YYYY), `due_date` (MM/DD/YYYY)
- `signature_date` (M.D.YY, or "" to hand-date)
- `delivery_days_aro` (default "30")
- `product_summary` — one short line describing the buy; used on OBS 1000, CalRecycle 74,
  and PD 843 description fields
- `shipping_handling` — number, default 0.0 (BBS quotes FOB destination / freight prepaid)
- `rep`: { name, title, email, signature }
- `agency`: { requestor_name, requestor_email, requestor_phone, ship_to_line1/2/3 }
- `calrecycle_pcrc` / `calrecycle_sabrc` — default "NA"
- `line_items`: list of { qty, unit, description, part_number, pcrc, unit_price }.
  `ext_price` is computed (qty x unit_price) unless supplied. Subtotal, S&H, and grand
  total are computed automatically.

### 3. Run the fill script
```bash
python scripts/fill_obs_packet.py <blank_packet.pdf> <inputs.json> <output.pdf>
```
The script fills all AcroForm fields (via the public pdf skill's fill script), then
adds the four company-name text annotations. It requires `pymupdf` — if not installed,
run `pip install pymupdf --break-system-packages -q` first.

### 4. Verify before delivering
Convert the output to images and eyeball the key pages — the form field layout can drift
between packet revisions:
```bash
python /mnt/skills/public/pdf/scripts/convert_pdf_to_images.py <output.pdf> <verify_dir>/
```
Check: OBS 4007(B) front page (page 2), the line-item worksheet (page 12), CalRecycle 74
(page 16), PD 843 (page 21), and STD 204 (page 24). Confirm the rep signed the bidder
lines, Jackson signed the ownership lines, the totals are right, and no company-name
line is blank.

If a field lands in the wrong place, the packet revision may have changed. Re-extract the
field list with `python /mnt/skills/public/pdf/scripts/extract_form_field_info.py
<blank_packet.pdf> fields.json` and reconcile the field IDs in
`scripts/fill_obs_packet.py` (the `add(...)` calls and `LINE_FIELD_IDS`). The annotation
coordinates in `ANNOTATIONS` are tied to the Rev. 08/2025 layout.

### 5. Deliver
Copy the final PDF to the outputs directory and present it. Then give the rep a short
status: which forms were completed, who signed what, and the reminder to add the
signature date by hand at submission if it was left blank.

For a full page-by-page map of what goes where, who signs each form, the four
flat-text annotation coordinates, and the list of irregular field names, see
`references/field_map.md`.

## Field-name caution

The source packet's AcroForm field names are hand-authored and slightly irregular
(e.g. one line-item extended-price field is literally named
`"OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext Price L5"`,
and rows 13/18/23 use a different ext-price naming pattern). `LINE_FIELD_IDS` in the
script encodes these quirks. If the fill script reports an invalid field ID, re-extract
the field list and update the map rather than guessing.
