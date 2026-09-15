---
name: obs-form-filler
description: Fill out the CDCR OBS 4007(B) "RFQ Packet-B" California state compliance forms for Black Box Safety (BBS). Use this skill whenever a BBS rep needs to respond to a CDCR (Department of Corrections and Rehabilitation) informal competitive RFQ — i.e. whenever they upload or mention a blank OBS 4007(B) packet, "Packet B", "OBS 4007", a CDCR RFQ, or ask to fill out the bid forms / compliance packet for a CDCR quote. Also trigger when a rep provides a quote (product, price, quantity) plus a solicitation number and asks to "fill the OBS form", "redo this on the new forms", "complete the bid packet", or "fill out the CDCR forms". The rep supplies the quote line items, the dates, the agency contact info, and their own rep info (name/title/email); this skill merges in BBS's fixed vendor profile, fills all 9 sub-forms, embeds signatures, and produces a submission-ready PDF. Do NOT use for non-CDCR bid packets, NASPO/Grainger-routed quotes, or generic California state forms unrelated to the OBS 4007(B) packet.
---

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
plugin's canonical vendor profile at `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`,
so the rep never re-keys it. `ca-form-filler` reads that same file: BBS's vendor facts are
written down once, in one place, and a cert expiry cannot go stale in one copy while bids
go out from another. Do not add a second copy here.

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
Run it by its full path — `SKILL_DIR` is the folder holding this SKILL.md, which
is wherever the plugin got installed, not the directory you happen to be in:
```bash
SKILL_DIR=<the folder containing this SKILL.md>
python "$SKILL_DIR/scripts/fill_obs_packet.py" <blank_packet.pdf> <inputs.json> <output.pdf>
```
The script fills all AcroForm fields, then adds the four company-name text
annotations. It needs `pypdf` and `pymupdf`, checks for both before it touches
the packet, and prints the install command if either is missing
(`pip install pypdf pymupdf --break-system-packages -q`). Nothing else is
required: it is self-contained, so it runs the same on a rep's machine as it
does in a Claude session.

It writes the packet only if every field validates, so a non-zero exit means no
output file — never a half-filled one. Read any `NOTE:` lines it prints: a note
that a checkbox was checked under a different state name means this packet
revision differs from Rev. 08/2025, and the rest of the layout deserves a
closer look.

### 4. Verify before delivering
Render the key pages and eyeball them — the form field layout can drift between
packet revisions:
```bash
python "$SKILL_DIR/scripts/render_pages.py" <output.pdf> <verify_dir>/ 2 12 16 21 24
```
Those are the pages that matter: OBS 4007(B) front page (page 2), the line-item
worksheet (page 12), CalRecycle 74 (page 16), PD 843 (page 21), and STD 204
(page 24). Pass no page numbers to render the whole packet.

Confirm, in this order:

1. **The DVBE box on page 2 is actually ticked**, along with the PD 843 "not a
   broker" box (page 21) and the STD 204 entity boxes (page 24). Check the
   rendered image, not the field values — a box can hold the right value and
   still render blank if the packet revision renamed its checked state.
2. Every line item appears and the grand total matches the quote.
3. The rep signed the bidder lines and Jackson signed the ownership lines.
4. No company-name line is blank.

If a field lands in the wrong place, the packet revision has probably changed. The
script refuses to write a packet when a field ID is unknown, sits on an unexpected
page, or is a checkbox it cannot tick, and names every offender. To see what the new
packet actually contains — each field's page, type and checkbox on-states:

```bash
python "$SKILL_DIR/scripts/fill_obs_packet.py" --inspect <blank_packet.pdf>
```

Reconcile that against the field IDs in `scripts/fill_obs_packet.py` (the `add(...)`
calls and `LINE_FIELD_IDS`), and update `references/field_map.md` to match. The
annotation coordinates in `ANNOTATIONS` are tied to the Rev. 08/2025 layout, so
re-check those four company-name lines too.

### 5. Deliver
Copy the final PDF to the outputs directory and present it. Then give the rep a short
status: which forms were completed, who signed what, and the reminder to add the
signature date by hand at submission if it was left blank.

For a full page-by-page map of what goes where, the four flat-text annotation
coordinates, and the list of irregular field names in *this* packet, see
`references/field_map.md`.

For the rules that are the same whoever fills a CA form — who signs which lines, what
the State fills in, why CalRecycle 74 is never left blank, and the certification
language that decides whether BBS claims the 5% SB preference — see
`${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md`. That file is shared with
`ca-form-filler` and `naspo-quote`; put a new signing or leave-blank rule there, not
here, so all three skills stay in agreement.

## Field-name caution

The source packet's AcroForm field names are hand-authored and slightly irregular
(e.g. one line-item extended-price field is literally named
`"OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext Price L5"`,
and rows 13/18/23 use a different ext-price naming pattern). `LINE_FIELD_IDS` in the
script encodes these quirks. If the fill script reports an invalid field ID, re-extract
the field list and update the map rather than guessing.
