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
| **The signer the rep names** (variable) | OBS 4007(B) bidder signature, Darfur certification (OBS 1500 / DGS PD 1), CalRecycle 74 certification | Any BBS employee — see *Rep-signed lines* below. Named by the rep on every run; never defaulted. |
| **Jackson Dalton** (fixed) | DGS PD 843 DVBE owner declaration, CV 012, STD 204 authorized payee representative | Tied to who **owns** the certified business — these are the disabled-veteran owner's declarations. Never varies by rep, and the 2026-09-28 signer ruling (below) does not touch them. |

### Rep-signed lines — who may sign, and when a skill may apply the signature

Ruled by Parker, in session, 2026-09-28: **any BBS employee may sign** ("anyone is
permitted to sign"; "whomever the rep says, they can sign it with anyone"); **the rep
names the signer.** This covers every rep-signed line: the OBS 4007(B) bidder signature,
Darfur (OBS 1500 or DGS PD 1) and CalRecycle 74. It supersedes "the rep who quoted the
job" (2026-09-18).

- **The rep names the signer on every run** — name, title and email. There is no default;
  with no signer named the skill stops with `[MISSING — NEEDS INPUT]`.
- **Never a customer, an agency or a third party.** The signer's email must be a single
  address on BBS's domain (the domain of `vendor_profile.json` `contact.email`); anything
  else stops the run with nothing written. The domain is checked first.
- **These lines are sworn.** The signer confirms the certification content — on
  CalRecycle 74, the PCRC and SABRC values — before sending.
- **A skill applies a signature only for a signature delegate** listed in
  `vendor_profile.json` `signature_delegation`, matched on the recorded email or a recorded
  alias together with the recorded name — including when the rep names a delegate to sign
  a bid someone else prepared. What is applied is the delegate's own signature of record,
  never free text that could differ from the signer.
- **Any other signer:** print name and title are filled; signature and date are left blank
  for a hand signature and flagged `⚑ SIGNATURE REQUIRED`. A delegate's signature is never
  applied to a line signed by someone else.

## The sub-forms

| Form | Rule |
|---|---|
| **STD 204** Payee Data Record | Section 1 NAME is the legal name, not the short name. Section 6 is the paying agency's block — leave it entirely blank. Signed by the owner, not the rep. |
| **DGS PD 843** DVBE declaration | Signed by the DVBE owner. "Name of DVBE" is the **legal name** exactly as `vendor_profile.json` `business_identity.legal_name` gives it (ruled 2026-09-18, matches the filed corpus; confirmed by Parker 2026-09-28, "do legal name"); never the short name, and never typed as a literal. SCPRS reference number is the State's to fill; leave it. |
| **CalRecycle 74** (SABRC) | **Never leave blank — a missing CalRecycle 74 can disqualify the bid.** BBS resells finished goods and rarely certifies a postconsumer percentage, so PCRC and SABRC default to "NA". Only override with a real percentage the rep supplies. Contractor/Company Name is the legal name (see *Company name*). Signed by the signer the rep names — *Rep-signed lines* above. |
| **OBS 1000** GenAI factsheet | Answer the "was GenAI used" question; it is about the *product* being sold, not about how the bid was prepared. Business Name is the legal name (see *Company name*). |
| **GSPD-05-105** Bidder Declaration | BBS bids as the certified business, not through subs or brokers, unless the rep says otherwise for this bid. The "distinct element of work" is the CUF statement, which is **not** in the vendor profile — ask the rep. |
| **STD 205** Payee Data Record Supplement | Accompanies STD 204 when the agency asks for it. Same signer as the STD 204 — the owner, not the rep. Agency block stays blank, exactly as on the STD 204. |
| **OBS 1500** Darfur Contracting Act (CDCR) | The CDCR packet's Darfur form; **DGS PD 1** is the standalone equivalent outside a CDCR packet. Same substance either way: BBS has no business operations in Sudan, so the no-foreign-operations paragraph is the one that applies. Company name is the legal name (see *Company name*). Signed by the signer the rep names — *Rep-signed lines* above. |
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
- **Federal is SDVOSB, never DVBE.** Different word, different program. Do not let
  federal language reach a state form or the reverse. Note that federally BBS **is** a
  small business under SBA size standards — that is a federal fact and has no bearing on
  a California form.

## Verify before delivering

Render the filled pages and look at them. These forms clip long values silently, and a
checkbox can hold the right value and still render blank if the packet revision renamed
its checked state — so check the **image**, not the field value. Confirm the DVBE box
is ticked and the SB box is **not**, the totals match the quote, the right person signed each line, and no
company-name line came out empty.

---

Owner: bbs-sales. Last verified 2026-09-28.
