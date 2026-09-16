---
name: ca-form-filler
description: >-
  Fill any California state compliance form or bid packet for Black Box Safety — the CDCR OBS
  4007(B) "Packet B", and standalone forms including STD 204, STD 205, DGS PD 843, GSPD-05-105
  Bidder Declaration, DGS PD 1 and OBS 1500 Darfur, OBS 1000 GenAI, CalRecycle 74 and CV 012.
  Use whenever a rep uploads blank state forms or a bid packet, mentions any of those form
  numbers, or says "Packet B", "OBS 4007", "the CDCR forms", "the bid packet", "state forms",
  "compliance forms", or "fill out the forms". It merges BBS's canonical vendor profile with
  the solicitation, fills every field it can verify, signs BBS's own lines and flags any
  signer it cannot determine, and reports what it could not fill. Do NOT use to price items (grainger-
  pricing), build the customer quote (bbs-quote-builder), extract line items from a cart PDF
  or screenshot (rfq-item-extract), or run a whole NASPO response end to end (naspo-quote,
  which calls this for the paperwork).
compatibility: claude-code
---

# California compliance forms — Black Box Safety

One skill for every CA form BBS files. Two paths through it:

- **A known packet** — the CDCR OBS 4007(B) 9-form "Packet B" — has an exact, scripted
  fill. Take it whenever the packet matches; it is faster and it validates.
- **Anything else** — standalone forms, or a packet this skill has no profile for — goes
  through the general map-and-fill path.

Both paths share the same vendor facts, the same signing rules, and the same refusal to
guess. Those live in `${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md` — who signs which
lines, what the State fills in, why CalRecycle 74 is never left blank, and which
certification language applies. Put a new signing or leave-blank rule there, not here, so
this skill and `naspo-quote` stay in agreement.

## Critical rules

1. **Never invent data.** A value that is not in the vendor profile and cannot be read out
   of the solicitation is `[MISSING — NEEDS INPUT]` in the output and a line in the gap
   report. These are binding documents; a plausible guess is worse than a blank.
2. **Sign only BBS's own lines, only with BBS's own signatures.** Parker Marshall and
   Jackson Dalton have each delegated authority to sign the forms in this skill's
   profiles, so the packet is produced signed. Apply a signature **only** to the line its
   owner signs (rule 5), and **never** on behalf of a customer, an agency, or any third
   party. A line whose correct signer you cannot determine is
   `⚑ SIGNATURE REQUIRED — <name>, <title>`, not a guess.
3. **The vendor profile is the authority** for every static BBS fact. If the solicitation
   pre-fills a BBS field with something different, flag it — do not accept the correction.
4. **Check the DVBE cert against the due date before filling anything.** Expired, or
   inside 30 days of expiry, is a hard stop.
5. **Two different people sign, and conflating them is the most common error.** The
   quoting **rep** signs bidder lines (OBS 4007(B) bidder signature, Darfur, CalRecycle
   74). **Jackson Dalton**, DV owner and President, signs ownership lines (DGS PD 843,
   STD 204 authorized payee) — those follow who *owns* the certified DVBE, not who quoted
   the job, so they do not change with the rep.
6. **Agency-side fields stay blank** — method of award, SCPRS ref, PO#, and the STD 204
   paying-agency block are the State's to complete.
7. **Verify by looking.** Rasterize the pages that matter and inspect them before
   delivering. A checkbox can hold the right value and still render blank if the packet
   revision renamed its checked state.

## Vendor facts

Read them from the plugin's canonical profile. There is exactly one copy:

```python
import json, os
root = os.environ["CLAUDE_PLUGIN_ROOT"]
vp = json.load(open(f"{root}/references/vendor_profile.json"))

legal_name = vp["business_identity"]["legal_name"]
fein       = vp["business_identity"]["fein"]
cert       = vp["certifications"]["sb_dvbe"]      # ONE cert carrying both SB and DVBE
owner      = next(r for r in vp["authorized_representatives"] if r["role"] == "dvbe_owner")
```

Look signers up **by `role`**, never by list position. Surface anything in `_meta.notes`
before proceeding. Do not copy this file anywhere; earlier revisions of this skill read a
per-machine copy at `~/.bbs/vendor_profile.json`, which is how a cert expiry could go
stale in one place while binding bids went out from another.

Check the cert against the due date immediately:

```python
from datetime import datetime
exp = datetime.strptime(cert["expiration"], "%m/%d/%Y")
due = datetime.strptime(due_date, "%m/%d/%Y")
days = (exp - due).days
if days < 0:
    raise SystemExit(f"STOP — DVBE cert expired {cert['expiration']}, before the {due_date} due date")
if days < 30:
    print(f"WARNING: DVBE cert expires in {days} days ({cert['expiration']}) — flag to the rep")
```

---

# Path A — CDCR OBS 4007(B) "Packet B"

Take this path whenever the packet is the CDCR 9-form Packet B: OBS 4007(B), Line-Item
Cost Worksheet, Bidder Declaration (GSPD-05-105), Darfur (OBS 1500), CalRecycle 74, GenAI
Factsheet (OBS 1000), DVBE Declaration (DGS PD 843), Supplement Vendor Payee Data Record,
and Payee Data Record (STD 204).

The packet is identical every time except the quote line items, the dates and solicitation
number, the agency requestor and ship-to, and which rep signs. Everything else comes from
the vendor profile.

### 1. Collect the inputs

The rep supplies the quote (pasted, or as a PDF/xlsx), the solicitation number, dates,
agency contact, and their own name/title/email. If the items arrive as a Grainger cart
PDF, a screenshot, or a DWR RFQ, run `rfq-item-extract` first and bring the list here.

Defaults when unspecified: `signature_date` today in `M.D.YY` (BBS house style, e.g.
`5.28.26`), `delivery_days_aro` 30, `shipping_handling` 0.0 (BBS quotes FOB destination),
CalRecycle PCRC/SABRC "NA", rep `default_rep` from the profile.

### 2. Build the inputs JSON

Copy `assets/inputs_template.json`. Schema: `solicitation_number`, `release_date` and
`due_date` (MM/DD/YYYY), `signature_date` (`M.D.YY`, or `""` to hand-date),
`delivery_days_aro`, `product_summary` (one line, used on OBS 1000, CalRecycle 74 and PD
843), `shipping_handling`, `rep{name,title,email,signature}`,
`agency{requestor_name,requestor_email,requestor_phone,ship_to_line1..3}`,
`calrecycle_pcrc`, `calrecycle_sabrc`, and `line_items[]` of
`{qty, unit, description, part_number, pcrc, unit_price}`. Extended prices, subtotal, S&H
and grand total are computed.

### 3. Fill

```bash
SKILL_DIR=<the folder containing this SKILL.md>
python "$SKILL_DIR/scripts/fill_obs_packet.py" <blank_packet.pdf> <inputs.json> <output.pdf>
```

It fills every AcroForm field, then writes the four company-name lines that have no
fillable field as text annotations at known coordinates. It needs `pypdf` and `pymupdf`,
checks for both before touching the packet, and prints the install command if either is
missing (`pip install pypdf pymupdf --break-system-packages -q`).

**It writes the packet only if every field validates**, so a non-zero exit means there is
no output file rather than a half-filled one. Read any `NOTE:` lines: a checkbox ticked
under a different state name means this revision differs from Rev. 08/2025 and the rest of
the layout deserves a closer look.

### 4. Verify

```bash
python "$SKILL_DIR/scripts/render_pages.py" <output.pdf> <verify_dir>/ 2 12 16 21 24
```

Those are the pages that carry the risk: OBS 4007(B) front (2), line-item worksheet (12),
CalRecycle 74 (16), PD 843 (21), STD 204 (24). Pass no page numbers to render everything.
Confirm, in this order:

1. **The DVBE box on page 2 is actually ticked**, with the PD 843 "not a broker" box (21)
   and the STD 204 entity boxes (24). Check the rendered image, not the field value.
2. Every line item appears and the grand total matches the quote.
3. The rep signed the bidder lines and Jackson the ownership lines.
4. No company-name line is blank.

If a field lands wrong, the packet revision has changed. The script refuses to write when a
field ID is unknown, sits on an unexpected page, or is a checkbox it cannot tick, and names
every offender. To see what the new packet contains:

```bash
python "$SKILL_DIR/scripts/fill_obs_packet.py" --inspect <blank_packet.pdf>
```

Reconcile that against the `add(...)` calls and `LINE_FIELD_IDS` in the script, update
`references/packet-obs-4007b.md`, and re-check the four annotation coordinates — they are
tied to the Rev. 08/2025 layout.

`references/packet-obs-4007b.md` has the page-by-page map, the annotation coordinates, and
the list of irregular field names in this packet. They are irregular: one extended-price
field is literally named `"OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost
Wrksht - Ext Price L5"`, and rows 13/18/23 use a different pattern again. If the script
reports an invalid field ID, re-extract and update the map rather than guessing.

---

# Path B — standalone forms and unknown packets

### 1. See what the PDF actually is

```bash
python3 "$SKILL_DIR/scripts/fill_obs_packet.py" --inspect /path/to/forms.pdf
```

The inspector reads any CA form PDF, not just Packet B — it reports each field's page,
type and checkbox on-states. **No fields listed means a flat scan**; use the coordinate
path in step 3.

Then identify which forms are present:

```bash
pdftotext /path/to/forms.pdf - | grep -n "STD 204\|STD 205\|PD 843\|CV 012\|Darfur\|CalRecycle\|OBS 1000\|GenAI\|GSPD"
```

Match on text, using the detection table in `references/field-maps.md`. Report the forms
you identified to the rep before filling, and flag anything unrecognized.

### 2. Map the fields

`references/field-maps.md` holds the per-form maps — STD 204, DGS PD 843, GSPD-05-105,
DGS PD 1, OBS 1000, CalRecycle 74 — and, first, the list of keys the vendor profile
actually has. Check a key exists before mapping it.

### 3. Fill

**Fillable PDFs** are the preferred path: set the AcroForm values, then validate the same
way Path A does before writing anything.

**Flat or scanned PDFs** fall back to coordinate stamping. Rasterize every page, map the
coordinates visually, then stamp. This is slower and more error-prone, so verify harder.

### 4. Verify

Rasterize and inspect every page you touched. Same rule as Path A: look at the render, not
the field value.

---

# Deliver (both paths)

Write outputs as `BBS_<FormID>_<Agency>_<SolNum>_<YYYYMMDD>.pdf`, then give the rep a
cover summary:

```
# BBS Form Packet — <Agency>

## Fields filled
<form: what was filled, from where>

## Signature requirements
⚑ <form> — <who signs>, <which line>

## Gap report
[MISSING — NEEDS INPUT] <field>: <why it could not be filled>
```

Close with the reminder to hand-date at submission if `signature_date` was left blank.

---

Owner: Parker. Last verified 2026-09-15.
