# CA compliance forms — the rules that are the same whoever fills them

Three skills in this plugin fill California compliance forms:

| Skill | Fills |
|---|---|
| `ca-form-filler` (Path A) | The CDCR OBS 4007(B) "Packet-B" — nine sub-forms bound into one PDF |
| `ca-form-filler` | The same sub-forms when an agency sends them as standalone PDFs |
| `naspo-quote` | The packet that goes with a NASPO-routed quote |

Eight of the nine sub-forms are documented below. **This file owns what those forms
mean — who signs them, what stays blank, what disqualifies a bid.** Each skill keeps its
own AcroForm field IDs, because a field ID belongs to a specific PDF: the same STD 204
has different internal names inside a bound packet than as a standalone download, and
pretending otherwise is how a filler writes to the wrong box.

So: **semantics here, field IDs in the skill.** If you are about to write down a signing
rule or a leave-blank rule in a skill, put it here instead.

Vendor facts — address, FEIN, seller's permit, cert numbers, signers — come from
`${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`. Never retype them.

## Who signs what

Conflating these two is the single most common error, and it is not cosmetic: the
ownership lines certify who owns the certified business, and anyone else's signature on
them is a false certification.

| Signer | Lines | Why |
|---|---|---|
| **The signer the rep names** (variable) | OBS 4007(B) and OBS 4007(C) bidder signature, Darfur certification (OBS 1500 / DGS PD 1), CalRecycle 74 certification, OBS 1000 GenAI factsheet | Named by the rep on every run; never defaulted. A signature is applied only as *Delegated signatures* allows. OBS 1000 joined this row 2026-10-01 (Parker: "Yes, rep-signed"). |
| **Jackson Dalton** (fixed) | DGS PD 843 DVBE owner declaration, CV 012, STD 204 authorized payee representative, STD 205 | Tied to who **owns** the certified business — the disabled-veteran owner's declarations. Jackson's image goes on these whoever runs the packet (Parker, 2026-10-01, R3); never anyone else's. |

### Delegated signatures — when a skill applies a signature

Ruled by Parker, in session, 2026-10-01 (R1): counsel has given the team "broad discretion
… to sign for each other on anything under $250,000 and any form that is involved in that
process for quoting." This supersedes the Parker-and-Jackson delegation of 2026-09-16 and
the "any other signer" rule that went with it.

- **"Complete the packet" is the approval.** A BBS employee asking a skill to complete the
  packet authorizes it to sign every line it knows how to sign, for the people relevant to
  that solicitation — the rep-signed lines for the signer the rep names, the owner lines
  for Jackson (Parker, 2026-10-01, R5). There is no second confirmation step.
- **Who: the six delegates** in `vendor_profile.json` `signature_delegation` — Griffin,
  Parker, Joey, Kim, Aanya and Jackson, and no one else. The rep names the signer of the
  rep-signed lines on every run (name, title and email); there is no default, and with no
  signer named the skill stops with `[MISSING — NEEDS INPUT]`. The signer is matched on
  the recorded email or alias **and** the recorded name.
- **The limit:** a delegated signature is applied only when the quote's grand total,
  **including tax**, as on the quote of record (the Business Central sales quote / the SQ
  the rep sends) is **strictly under** `signature_delegation.limit_usd` (Parker,
  2026-10-01, R1b). At or over the limit, or with the total missing or unreadable, no
  delegated signature is applied to any line — owner lines included — and every signature
  line is left blank and flagged `⚑ SIGNATURE REQUIRED`. The total comes from the quote of
  record, never an estimate.
- **What is applied:** the delegate's own PNG of record, read from that person's
  `signature_image` in `vendor_profile.json` (Parker, 2026-10-01, R2) — never typed text,
  never a path from the request, never an image that could differ from the signer. A
  delegate whose `signature_image` is null or whose PNG is missing cannot be signed for;
  the run stops and names the file.
- **Never a customer, an agency or a third party.** The signer's email must be a single
  address on BBS's domain (the domain of `vendor_profile.json` `contact.email`); anything
  else stops the run with nothing written. The domain is checked first. A BBS employee
  who is not one of the six gets print name and title filled and the signature and date
  left blank for a hand signature, flagged `⚑ SIGNATURE REQUIRED`.
- **Only forms in the quoting process** — the forms in the table below. A form the
  scripts cannot positively identify gets no signature.
- **These lines are sworn.** The signer confirms the certification content — on
  CalRecycle 74, the PCRC and SABRC values — before sending. Claude drafts; a person
  reviews and sends.

## The sub-forms

| Form | Rule |
|---|---|
| **STD 204** Payee Data Record | Section 1 NAME is the legal name, not the short name. Section 6 is the paying agency's block — leave it entirely blank. Signed by the owner, not the rep. |
| **DGS PD 843** DVBE declaration | Signed by the DVBE owner. "Name of DVBE" is the **legal name** exactly as `vendor_profile.json` `business_identity.legal_name` gives it (ruled 2026-09-18, matches the filed corpus; confirmed by Parker 2026-09-28, "do legal name"); never the short name, and never typed as a literal. SCPRS reference number is the State's to fill; leave it. |
| **CalRecycle 74** (SABRC) | **Never leave blank — a missing CalRecycle 74 can disqualify the bid.** BBS resells finished goods and rarely certifies a postconsumer percentage, so PCRC and SABRC default to "NA". Only override with a real percentage the rep supplies. Contractor/Company Name is the legal name (see *Company name*). Signed by the signer the rep names — *Rep-signed lines* above. |
| **OBS 1000** GenAI factsheet | Answer the "was GenAI used" question; it is about the *product* being sold, not about how the bid was prepared. Business Name is the legal name (see *Company name*). Signed by the signer the rep names (ruled 2026-10-01). |
| **GSPD-05-105** Bidder Declaration | BBS bids as the certified business, not through subs or brokers, unless the rep says otherwise for this bid. The "distinct element of work" is the CUF statement, which is **not** in the vendor profile — ask the rep. |
| **STD 205** Payee Data Record Supplement | Accompanies STD 204 when the agency asks for it. Same signer as the STD 204 — the owner, not the rep. Agency block stays blank, exactly as on the STD 204. |
| **OBS 1500** Darfur Contracting Act (CDCR) | The CDCR packet's Darfur form; **DGS PD 1** is the standalone equivalent outside a CDCR packet. Same substance either way: BBS has no business operations in Sudan, so the no-foreign-operations paragraph is the one that applies. Company name is the legal name (see *Company name*). Signed by the signer the rep names — *Rep-signed lines* above. |
| **OBS 4007(C)** Price Request front page (CDCR, Fair and Reasonable / Exempt, e.g. an LPA order) | Bidder block from the vendor profile; DVBE box ticked with the OSDS cert number and expiry, SB and MB **not** ticked (Parker, 2026-10-01) — this identifies the certification and claims no incentive. Signed by the signer the rep names. The solicitation, buyer and ship-to blocks are the agency's: keep whatever the agency entered. |
| **DGS PD 1** Darfur Contracting Act (standalone) | As OBS 1500, when the agency sends the DGS form rather than the CDCR one. Do not fill both for the same bid. |

## Company name

Every company-name line BBS fills takes `vendor_profile.json`
`business_identity.legal_name`, read from the profile and never typed: STD 204 Section 1,
STD 205, DGS PD 843 "Name of DVBE" (above), and — ruled by Parker, in session, 2026-09-28
("Yes, they can match legal name") — CalRecycle 74 Contractor/Company Name, OBS 1000
Business Name and Darfur (OBS 1500) company name. **Open:** the OBS Line-Item Cost
Worksheet "BUSINESS NAME:" header was not covered by that ruling and still takes the short
name.

## Fields the State fills — leave them blank

Method-of-award sub-options, SCPRS reference number, PO / RFQ number boxes, and the
entire STD 204 paying-agency block. A bidder filling these in is guessing at the
agency's own record-keeping.

**When the packet arrives partly filled** — the usual case (Parker, 2026-10-01) — every
value the agency already entered is kept. A skill never overwrites a pre-filled field; if
the agency pre-filled a BBS field (name, address, FEIN, cert) with something that differs
from the vendor profile, the run stops and names it, and the rep decides whether to
replace it (the vendor profile is the authority, but the decision is the rep's, per field).

## Certification language

Read the `_meta.notes` in the vendor profile before filling anything and surface any
warning there to the rep. The two that cost money:

- **Never claim the SB preference on a California solicitation.** OSDS 2009473 carries
  **DVBE only** — BBS passed California's SB revenue threshold and is not a California
  small business, so the 5% SB preference (SCM §1204) is **never** claimed on any
  California solicitation. A California form is signed under penalty of perjury;
  claiming a preference BBS does not hold is a false certification. The **DVBE incentive
  (SCM §1202) does still apply** and is claimed on every California competitive
  solicitation, informal ones included — never on LPA/NASPO orders, federal bids, or
  storefront copy. Source: `bbs-foundations` `canonical-facts.md`, "Small-business status
  is channel-dependent".
- **OBS 4007(C) on an LPA order:** tick DVBE and give the cert number; that identifies
  the certification for the agency's DVBE reporting and is not a claim of the §1202
  incentive, which is still never claimed on an LPA/NASPO order (Parker, 2026-10-01).
- **Federal is SDVOSB, never DVBE.** Different word, different program. Do not let
  federal language reach a state form or the reverse. Note that federally BBS **is** a
  small business under SBA size standards — that is a federal fact and has no bearing on
  a California form.

## Machine-readable form table

The form scripts read this block; it is not a second copy of the rules above, it is how
the code finds them. `markers` are strings read out of the actual blank forms (CDCR OBS
4007(C) Rev. 03/2025 uploaded by Parker 2026-10-01; DGS STD 204 Rev. 03/2021, DGS PD 843
Rev. 9/2019, GSPD-05-105, CalRecycle 74 Rev. 01/23, SCO STD 205, CDCR OBS 1000 Rev. 10/2025 and OBS
1500 (06/11), downloaded from dgs.ca.gov, calrecycle.ca.gov and cdcr.ca.gov the same day;
CDCR Supplement Vendor Payee Data Record, Rev. 05/1/2021, from the text of a live Packet C).
A page is that form when every marker appears, and no `none` string appears, in the
first 400 non-whitespace characters of its text, compared without whitespace and without
case. `line` is whose signature the form carries: `rep` (the signer the rep names),
`dv_owner` (Jackson), or `null` (no signature applied). A page that matches no form, or
more than one, gets no signature.

<!-- bbs-form-table:begin -->
```json
{
  "OBS4007C":     {"markers": ["OBS 4007 (C)"],                    "none": [],              "line": "rep"},
  "OBS4007B":     {"markers": ["OBS 4007 (B)"],                    "none": [],              "line": "rep"},
  "Darfur":       {"markers": ["OBS 1500", "DARFUR CONTRACTING ACT"], "none": [],           "line": "rep"},
  "CalRecycle74": {"markers": ["CalRecycle 74", "Postconsu"],      "none": [],              "line": "rep"},
  "OBS1000":      {"markers": ["GENAI REPORTING AND FACTSHEET", "OBS 1000"], "none": [],    "line": "rep"},
  "PD843":        {"markers": ["DISABLED VETERAN BUSINESS ENTERPRISE DECLARATIONS", "PD 843"], "none": [], "line": "dv_owner"},
  "STD204":       {"markers": ["PAYEE DATA RECORD", "STD 204"],    "none": ["SUPPLEMENT"],  "line": "dv_owner"},
  "STD205":       {"markers": ["PAYEE DATA RECORD SUPPLEMENT", "STATE CONTROLLERS OFFICE"], "none": [], "line": "dv_owner"},
  "Supplement":   {"markers": ["SUPPLEMENT VENDOR PAYEE DATA RECORD"], "none": [],          "line": null},
  "GSPD05105":    {"markers": ["BIDDER DECLARATION"],              "none": [],              "line": null}
}
```
<!-- bbs-form-table:end -->

CV 012 is an owner line too, but its blank could not be read for markers (2026-10-01), so
it has no row. A standalone CV 012 keeps the kind its fill spec declares, as before; a CV
012 page inside a bound packet is not recognised and gets no signature. Add its row from
the real PDF, never from memory.

## Verify before delivering

Render the filled pages and look at them. These forms clip long values silently, and a
checkbox can hold the right value and still render blank if the packet revision renamed
its checked state — so check the **image**, not the field value. Confirm the DVBE box
is ticked and the SB box is **not**, the totals match the quote, the right person signed each line, and no
company-name line came out empty.

---

Owner: bbs-sales. Last verified 2026-10-01.
