# Field maps — standalone California compliance forms

What goes in each field of the CA forms BBS meets outside a bound packet. For the CDCR
OBS 4007(B) packet, use its profile in `packets/` instead — a field ID belongs to a
specific PDF, and the same STD 204 has different internal names inside a bound packet than
as a standalone download. `packets/README.md` is the profile contract.

Source key: **VP** = `vendor_profile.json` · **RFQ** = extracted from the solicitation ·
**REP** = the rep must supply it · **DERIVED** = computed at runtime ·
**SIGN** = apply that signer's signature (rule 2 — these lines are produced signed) ·
**⚑ SIG** = signer cannot be determined from `ca-form-rules.md`; leave blank and flag it.

## What the vendor profile actually contains

Check a key exists before you map it. Earlier revisions of this file mapped
`dvbe_details.veteran_owner_name`, `rep.full_name`, `cuf_statement`, `broker_or_agent`
and `uses_genai` — **none of those exist** in `vendor_profile.json`, so every form that
depended on them silently produced an empty field. The real shape is:

```
business_identity.{legal_name, fein, ca_sellers_permit, entity_type, founded}
address.{mailing_street, city, state, zip}
contact.{phone, email, website}
certifications.sb_dvbe.{osds_ref_number, expiration, scope, carries}
certifications.local_only[].{name, number, scope}
certifications.federal.{designation, gsa_mas}
authorized_representatives[].{role, name, title, email, phone, signs}   # role, not index
default_rep.{role, name, title, email, signs}
```

Reps are `name`, never `full_name`. Look a signer up **by `role`**, never by list
position — the order of that array is not a contract.

Anything not in that list is REP input or `[MISSING — NEEDS INPUT]`. Never invent it.

## STD 204 — Payee Data Record

| Field | Source | Value |
|---|---|---|
| Legal Name (§1) | VP | `business_identity.legal_name` |
| Mailing address, city/state/zip | VP | `address.*` |
| Email | VP | `contact.email` |
| Entity Type checkbox | VP | `entity_type` is Corporation → "Corporation — All Others" |
| FEIN (§3) | VP | `business_identity.fein` (XX-XXXXXXX) |
| CA Resident (§4) | DERIVED | check "California Resident" |
| Rep name / title / phone / email (§5) | VP | the `dvbe_owner` representative — this is the **authorized payee** line, so Jackson Dalton signs it, not the quoting rep |
| Agency name / address / phone / fax (§6) | RFQ | agency block |
| Signature, date (§5) | SIGN | **Jackson Dalton** — the authorized payee line follows who owns the certified business, matching the §5 rep fields above |

**Field IDs on this form frequently do not match the visual section labels** — the FEIN
field and the §5 rep fields are commonly misnamed in the PDF metadata. Rasterize and look
before trusting a mapping:

```bash
pdftoppm -jpeg -r 150 -f 1 -l 1 /path/to/forms.pdf /tmp/std204_verify
```

## DGS PD 843 — DVBE Declaration

| Field | Source | Value |
|---|---|---|
| DVBE name (§1) | VP | `business_identity.legal_name`. **Ruled by Parker 2026-09-18:** the legal name, `Black Box Safety, Inc.`, on every PD 843. Path A (`fill_obs_packet.py`) writes the same key. The filed corpus agrees (72 PD 843s, see `naspo-quote/references/filled-form-precedents.md`) |
| DVBE ref number (§1) | VP | `certifications.sb_dvbe.osds_ref_number` |
| Solicitation # (§1) | RFQ | solicitation number |
| Not a broker/agent (§2) | DERIVED | check — BBS supplies from stock, see `ca-form-rules.md` |
| DV owner name, phone (§3) | VP | `authorized_representatives[role=dvbe_owner].name` (Jackson Dalton) and `.phone`. **These are in the profile — fill them.** Path A fills them from the same keys; blanking them here is what made one path sign the form and the other render it incomplete |
| DV owner personal address, tax ID (§3) | REP | genuinely **not** in the profile — his personal address and tax ID are deliberately not committed. `[MISSING — NEEDS INPUT]` and flag |
| All signatures and dates | SIGN | **Jackson Dalton** — DVBE owner declaration. A perjury certification, so the signer must be the owner and never the quoting rep |

## GSPD-05-105 — Bidder Declaration

Form ID is **GSPD-05-105**. Earlier revisions of this file said GSPD-05-106, which is
not a form BBS files.

| Field | Source | Value |
|---|---|---|
| Certification(s) | VP | `"DVBE"` — the OSDS cert carries DVBE only. Never write "SB" or "SB, DVBE" here; BBS is not a California small business (`ca-form-rules.md`, "Certification language") |
| Certification # | VP | `certifications.sb_dvbe.osds_ref_number` |
| Subcontractors used | DERIVED | "No" |
| Broker or agent (1c-1) | DERIVED | "No" |
| Equipment rental 51% (1c-2) | DERIVED | "N/A" |
| Distinct element of work | REP | the CUF statement. **Not in the vendor profile** — ask the rep |
| Solicitation # | RFQ | solicitation number |
| Page # | DERIVED | "1 of 1" |

## DGS PD 1 — Darfur Contracting Act Certification

| Field | Source | Value |
|---|---|---|
| Company name | VP | `business_identity.legal_name` |
| FEIN | VP | `business_identity.fein` |
| Paragraph 1 initials | REP | the signing rep's initials — BBS has no foreign operations |
| Printed name + title | REP | the signing rep (`default_rep` only as a fallback) |
| County and State | DERIVED | "San Diego County, California" |
| Signature, date | SIGN | **The rep** who quoted the job — Darfur is a bidder certification (`ca-form-rules.md`: DGS PD 1 is the standalone OBS 1500) |

## OBS 1000 — GenAI Disclosure

Form ID is **OBS 1000**. Earlier revisions of this file said STD 1000.

| Field | Source | Value |
|---|---|---|
| Company name | VP | `business_identity.legal_name` |
| Address, phone | VP | `address.*`, `contact.phone` |
| Solicitation # | RFQ | solicitation number |
| Contract description | RFQ | description of purchase |
| Uses GenAI? | DERIVED | "No" — BBS resells finished goods; the products contain no GenAI |
| Conditional GenAI fields | — | skip, they depend on "Yes" |
| Rep name | REP | the signing rep |
| Signature, date | ⚑ SIG | **Signer not determined.** `ca-form-rules.md` assigns no signer for OBS 1000, and Path A's OBS profile fills the date only. Fill the date, leave the signature, flag `⚑ SIGNATURE REQUIRED`. Do not infer one from the neighbouring forms |

## CalRecycle 74 — Recycled Content Certification

Never left blank — a missing CalRecycle 74 can disqualify the bid. See `ca-form-rules.md`.

| Field | Source | Value |
|---|---|---|
| Contractor/company name | VP | `business_identity.legal_name` |
| Address, phone | VP | `address.*`, `contact.phone` |
| RFQ # | RFQ | solicitation number |
| Item # / description | RFQ | from the line items |
| Postconsumer recycled % | REP | BBS resells finished goods and rarely certifies a percentage; "NA" is the normal answer. Only a real percentage from the rep overrides it |
| SABRC category code | REP | as above |
| Print name, title | REP | the signing rep |
| Signature, date | SIGN | **The rep** who quoted the job — CalRecycle 74 is a bidder certification. It is a perjury certification, so the rep signs it personally and never on another's behalf |

## Form detection

`pdftotext` the packet and match on the text, not the filename:

| Form ID | Key text |
|---|---|
| STD 204 | "PAYEE DATA RECORD" / "STD 204" |
| STD 205 | "PAYEE DATA SUPPLEMENT" / "STD 205" |
| DGS PD 843 | "DISABLED VETERAN BUSINESS ENTERPRISE" / "843" |
| GSPD-05-105 | "BIDDER DECLARATION" / "GSPD-05-105" |
| DGS PD 1 | "DARFUR" / "PD 1" |
| OBS 1000 | "GENERATIVE AI" / "OBS 1000" |
| OBS 1500 | "DARFUR" in a CDCR packet |
| CalRecycle 74 | "CALRECYCLE" / "RECYCLED CONTENT" / "SABRC" |
| CV 012 | "COMMERCIALLY USEFUL FUNCTION" / "CV 012" |

---

Owner: Parker. Last verified 2026-09-16.
