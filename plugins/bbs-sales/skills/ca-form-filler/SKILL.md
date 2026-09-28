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
  signer it cannot determine, and reports what it could not fill. Do NOT use to price items
  (grainger-pricing), build the customer quote (bbs-quote-builder), extract line items from
  a cart PDF
  or screenshot (rfq-item-extract), or run a whole NASPO response end to end (naspo-quote,
  which calls this for the paperwork).
compatibility: claude-code
requires: [python3, pypdf, pymupdf, poppler]
---

# California compliance forms — Black Box Safety

One skill for every CA form BBS files. Two paths through it:

- **A recognised packet** has a **profile** in `references/packets/` — an exact page map
  and a scripted fill. Take it whenever a profile matches; it is faster and it validates.
- **Anything else** — standalone forms, or a packet no profile recognises — goes through
  the general map-and-fill path.

Which one you are on is decided by text read out of the PDF, not by what the rep called
the file and not by judgement. Run the resolver (Path A step 1) before anything else.

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
   the job, so they do not change with the rep. When the rep's signature may be applied
   and when a rep line is left for them to sign by hand is in `ca-form-rules.md`; Path A's
   script prints a `⚑ SIGNATURE REQUIRED` line for each one it leaves, and the cover
   summary repeats it.
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
cert       = vp["certifications"]["sb_dvbe"]      # key name is historical: carries DVBE only
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

# Path A — a packet with a profile

### 1. Recognise the packet

```bash
SKILL_DIR=<the folder containing this SKILL.md>
python "$SKILL_DIR/scripts/packet_profile.py" --recognize-pdf <blank_packet.pdf>
```

`python` here is the interpreter `scripts/bbs-setup.ps1` installs on Windows, where
`python3` is only the Microsoft Store stub. On a Mac, where only `python3` exists, type
that instead. Every command in this skill follows the same rule.

It reports one of four things, and each is an instruction. It checks the profile set
conforms before it evaluates a single marker, so a malformed profile is a refusal here
and never a quiet `no match`:

- **A profile id** — you are on Path A. The output names the profile file, the fill
  script, the inputs template and the pages to verify. Read that profile before filling:
  it holds the page map, which page carries whose signature line, the irregular field IDs
  and where this packet puts the State's own fields. Who signs and what stays blank are in
  `ca-form-rules.md`, which the profile cites rather than copies.
- **`no match -> Path B`** — no profile recognises this PDF. Go to Path B. This is the
  normal answer for standalone forms and for any packet whose profile has not been built
  yet; it is not an error.
- **`REFUSED`** (exit 1) — **Stop.** Either several profiles matched and none subsumes the
  rest, or a profile does not parse or breaks the recognition contract. Report it; do not
  pick one, and **do not fall back to Path B to get moving**. A packet that matches two
  profiles is one whose markers are wrong, and a profile set with a broken file in it may
  be missing the very profile for the packet in hand — falling through would hand-map a
  packet that has a verified scripted fill, silently. Both are worth knowing before the
  next bid. `packet_profile.py --validate` names the file and line.
- **`ERROR`** (exit 2) — a missing input file, or `pdftotext` absent or failing. A broken
  machine, not a decision about this packet. Fix it and re-run.

`references/packets/README.md` is the profile contract — what a profile file must
contain, how recognition resolves, and what to fill in before a new one goes live. Adding
a packet is one file in that directory; nothing in this SKILL.md names a packet or needs
editing for it.

This step needs nothing installed — `packet_profile.py` is stdlib only and reads the
profile front matter itself, so it never stops a bid to ask for a package. `pdftotext`
is the one external tool, and `bbs-checkup` installs it.

Recognition picks a candidate. It does not authorise the write: the fill script validates
every field ID, its type and its page against the PDF in hand and refuses to write if one
is unknown, so a wrong match produces no packet rather than a wrong one. Both have to
agree.

### 2. Collect the inputs

What varies between two runs of the same packet is the quote line items, the dates and
solicitation number, the agency requestor and ship-to, and which rep signs. Everything
else comes from the vendor profile.

The rep supplies the quote (pasted, or as a PDF/xlsx), the solicitation number, dates,
agency contact, and their own name/title/email. If the items arrive as a Grainger cart
PDF, a screenshot, or a DWR RFQ, run `rfq-item-extract` first and bring the list here.

Defaults when unspecified: `signature_date` today in `M.D.YY` (BBS house style, e.g.
`5.28.26`), `delivery_days_aro` 30, `shipping_handling` 0.0 (BBS quotes FOB destination),
CalRecycle PCRC/SABRC "NA", rep `default_rep` from the profile.

### 3. Build the inputs JSON

Copy the `inputs_template` the resolver named. For the CDCR OBS 4007(B) packet that is
`assets/inputs_template.json`, whose schema is `solicitation_number`, `release_date` and
`due_date` (MM/DD/YYYY), `signature_date` (`M.D.YY`, or `""` to hand-date),
`delivery_days_aro`, `product_summary` (one line, used on OBS 1000, CalRecycle 74 and PD
843), `shipping_handling`, `rep{name,title,email,signature}`,
`agency{requestor_name,requestor_email,requestor_phone,ship_to_line1..3}`,
`calrecycle_pcrc`, `calrecycle_sabrc`, and `line_items[]` of
`{qty, unit, description, part_number, pcrc, unit_price}`. Extended prices, subtotal, S&H
and grand total are computed.

### 4. Fill

Run the `script` the resolver named — **that path, not a remembered one**:

```bash
python "$SKILL_DIR/<the resolver's script>" <blank_packet.pdf> <inputs.json> <output.pdf>
```

For the CDCR OBS 4007(B) packet the resolver names `scripts/fill_obs_packet.py`. That is
the worked example, not the command for every packet.

It fills every AcroForm field, then writes the company-name lines that have no fillable
field as text annotations at the coordinates in the profile. It needs `pypdf` and
`pymupdf`, checks for both before touching the packet, and prints the install command if
either is missing (`python -m pip install pypdf pymupdf`).

**It writes the packet only if every field validates**, so a non-zero exit means there is
no output file rather than a half-filled one. Read any `NOTE:` lines: a checkbox ticked
under a different state name means this revision differs from the one the profile was
built against, and the rest of the layout deserves a closer look.

### 5. Verify

Render **the pages this profile lists under `verify_pages`** — the resolver printed them
— and look at them:

```bash
python "$SKILL_DIR/<the resolver's verify_script>" <output.pdf> <verify_dir>/ <verify_pages>
```

Every packet puts its risk on different pages, so take the numbers from the resolver
output and never from a command you have run before. For the CDCR OBS 4007(B) packet they
are `2 12 16 21 24` — front page (2), line-item worksheet (12), CalRecycle 74 (16), PD 843
(21), STD 204 (24) — which is what that example looks like, not a default. Pass no page
numbers to render everything; when a profile lists none, do that. Then confirm, in this
order, reading the profile's page table for where each lands in *this* packet:

1. **The DVBE certification box is actually ticked and the SB and MB boxes are not**, with the PD 843 "not a broker"
   box and the STD 204 entity boxes. Check the rendered image, not the field value.
2. Every line item appears and the grand total matches the quote.
3. The rep signed the bidder lines and Jackson the ownership lines — the profile's Signer
   column says which page is which, and `ca-form-rules.md` says who.
4. No company-name line is blank.

### When a field lands wrong

The packet revision has changed. The script refuses to write when a field ID is unknown,
sits on an unexpected page, or is a checkbox it cannot tick, and names every offender. To
see what the new packet contains:

```bash
python "$SKILL_DIR/scripts/fill_obs_packet.py" --inspect <blank_packet.pdf>
```

Reconcile that against the `add(...)` calls and `LINE_FIELD_IDS` in the script, update the
profile — its page map, its `revision`, its annotation coordinates and its recognition
markers, which are all tied to one revision — and re-run
`python "$SKILL_DIR/scripts/packet_profile.py" --validate`.

Expect the field names to be irregular: in the OBS packet one extended-price field is
literally named `"OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext
Price L5"`, and rows 13/18/23 use a different pattern again. The profile lists the known
oddities. If the script reports an invalid field ID, re-extract and update the profile
rather than guessing.

---

# Path B — standalone forms and unknown packets

You are here because Path A step 1 reported no match. That is the normal answer for a
standalone form, and the correct answer for a packet nobody has mapped yet.

### 1. See what the PDF actually is

```bash
python "$SKILL_DIR/scripts/fill_obs_packet.py" --inspect /path/to/forms.pdf
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

### 5. If this packet comes back

A bound packet filled by hand here twice is a packet that wants a profile. Write one:
`references/packets/README.md` is the contract, and the map you just built by inspecting
the PDF is most of the content. Nothing in this file needs editing to add it.

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

Owner: Parker. Last verified 2026-09-16.
