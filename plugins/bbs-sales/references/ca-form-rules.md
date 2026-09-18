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
ownership lines certify who owns the certified business, and a rep signing them is a
false certification.

| Signer | Lines | Why |
|---|---|---|
| **The rep** (variable) | Bidder signature, Darfur certification, CalRecycle 74 certification | Whoever quoted the job. Comes from the skill's inputs; `default_rep` in the profile is only a fallback. |
| **Jackson Dalton** (fixed) | DGS PD 843 DVBE owner declaration, STD 204 authorized payee representative | Tied to who **owns** the certified business, not to who quoted. Never varies by rep. |

## The sub-forms

| Form | Rule |
|---|---|
| **STD 204** Payee Data Record | Section 1 NAME is the legal name, not the short name. Section 6 is the paying agency's block — leave it entirely blank. Signed by the owner, not the rep. |
| **DGS PD 843** DVBE declaration | Signed by the DVBE owner. "Name of DVBE" is the **legal name** exactly as `vendor_profile.json` `business_identity.legal_name` gives it (ruled 2026-09-18, matches the filed corpus); never the short name. SCPRS reference number is the State's to fill; leave it. |
| **CalRecycle 74** (SABRC) | **Never leave blank — a missing CalRecycle 74 can disqualify the bid.** BBS resells finished goods and rarely certifies a postconsumer percentage, so PCRC and SABRC default to "NA". Only override with a real percentage the rep supplies. Certified by the rep. |
| **OBS 1000** GenAI factsheet | Answer the "was GenAI used" question; it is about the *product* being sold, not about how the bid was prepared. |
| **GSPD-05-105** Bidder Declaration | BBS bids as the certified business, not through subs or brokers, unless the rep says otherwise for this bid. The "distinct element of work" is the CUF statement, which is **not** in the vendor profile — ask the rep. |
| **STD 205** Payee Data Record Supplement | Accompanies STD 204 when the agency asks for it. Same signer as the STD 204 — the owner, not the rep. Agency block stays blank, exactly as on the STD 204. |
| **OBS 1500** Darfur Contracting Act (CDCR) | The CDCR packet's Darfur form; **DGS PD 1** is the standalone equivalent outside a CDCR packet. Same substance either way: BBS has no business operations in Sudan, so the no-foreign-operations paragraph is the one that applies. Certified by the rep. |
| **DGS PD 1** Darfur Contracting Act (standalone) | As OBS 1500, when the agency sends the DGS form rather than the CDCR one. Do not fill both for the same bid. |

## Fields the State fills — leave them blank

Method-of-award sub-options, SCPRS reference number, PO / RFQ number boxes, and the
entire STD 204 paying-agency block. A bidder filling these in is guessing at the
agency's own record-keeping.

## Certification language

Read the `_meta.notes` in the vendor profile before filling anything and surface any
warning there to the rep. The two that cost money:

- **Claim the SB preference on competitive California solicitations.** OSDS 2009473
  carries both SB and DVBE, so the 5% SB preference (SCM §1204) and the DVBE incentive
  (SCM §1202) both apply — including on informal solicitations. They do not apply to
  LPA/NASPO orders, federal bids, or storefront copy.
- **Federal is SDVOSB, never DVBE.** Different word, different program. Do not let
  federal language reach a state form or the reverse.

## Verify before delivering

Render the filled pages and look at them. These forms clip long values silently, and a
checkbox can hold the right value and still render blank if the packet revision renamed
its checked state — so check the **image**, not the field value. Confirm the SB/DVBE box
is actually ticked, the totals match the quote, the right person signed each line, and no
company-name line came out empty.

---

Owner: bbs-sales. Last verified 2026-09-15.
