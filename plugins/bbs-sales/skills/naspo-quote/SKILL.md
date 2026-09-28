---
name: naspo-quote
description: >-
  Run a complete California state agency RFQ response end to end and deliver both halves: live
  Grainger pricing for the requested item numbers, the BBS sales quote PDF, and the filled CA
  compliance packet (OBS Line-Item Cost Worksheet, CalRecycle 74, DGS PD 843, Darfur OBS 1500,
  OBS 1000 GenAI, Bidder Declaration GSPD-05-105). Use whenever a CDCR institution, CalVet
  home, CSU/UC campus, Caltrans district or any State of California agency asks for pricing on
  item numbers, sends blank state certs to complete, or both — even if they never say NASPO,
  and even when the ask looks like only pricing or only paperwork, because on state business
  the two halves ship together. An agency email that asks for a quote is this skill, not an
  intake task: ca-rfq-intake only files a request and opens its folder, and does not price or
  fill anything. Do NOT use for a competitive SB/DVBE bid needing vendor sourcing
  (use bbs-sourcing), or when the rep wants the forms alone with no pricing
  (use ca-form-filler).
requires: [grainger, python3, pypdf, pymupdf]
---

# NASPO quote — CA state agency RFQ

A California state RFQ is one job with two halves: a price that has to come from
the live contract, and a packet of certs that has to be internally consistent
with that price. Reps lose these on the paperwork, not the pricing — a cert with
last quarter's solicitation number or an unsigned perjury declaration gets the
whole quote set aside. This skill keeps both halves in step.

Work in the buyer's folder under
`Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`.
That folder is the document store; Supabase `rep_cockpit` is the tracker.

## 1. Read the buyer folder before asking anything

The RFQ email tells you the items. The folder usually tells you everything else.

- `<Buyer Name>.txt` — Grainger/Proco account number, BC customer ID, ship-to address.
- The attached **Line-Item Cost Worksheet** — its pre-printed header carries the
  solicitation number (e.g. `NASPO: 07-25-51-02.3`). Read it out of the PDF; don't
  ask the rep for a number that's sitting in the attachment.
- Sibling folders from earlier RFQs for the same institution — prior CalRecycle
  answers, prior comment blocks, what the buyer accepted last time.

Extract for each line: Grainger item number, description, quantity, UOM.

## 2. Price against the right account

```
grainger_price(productCodes=["1ZRZ8", ...], account="<institution or account #>")
```

The account is not optional and not interchangeable — discount is per account, so
the wrong one returns a wrong price that looks perfectly valid. Use the account
from the buyer folder; the facility name ("CMC", "Porterville", "KVSP") works.

Read `account.sellRule` in the response. On every CA state schedule today it is
`at_cost`: **the customer price equals BBS cost, no markup.** BBS is paid through
the contract rebate. If a code path or habit makes you apply 20% margin here, the
quote is wrong and uncompetitive.

If you only have a description or manufacturer part number, `grainger_search`
first. For delivery promises, `grainger_availability` with the ship-to ZIP.

Record the values you'll need downstream: `unitPrice`, `contractReferencePrice`,
`discountOffContractReferencePct`, `uom`, `status`, and the account number.

## 3. Build the quote

Use the **bbs-quote-builder** skill. NASPO-specific spec values:

| Field | Value |
|---|---|
| `pricing` | `{"method": "markup", "rate": 0}` — at-cost, no markup |
| `taxRate` | `0` — the worksheet prints "Do not include sales tax" |
| `solicitation` | the number off the worksheet header |
| `shipmentMethod` | `FOB Destination` |
| `unitCost` | the Grainger `unitPrice` |

Quote number comes from the rep — the 900001 series. Check what's already used
(`find "Customers" -iname "*Quote_9000*"`) and propose the next one rather than
assigning silently.

## 4. Fill the compliance packet

Read `references/form-field-maps.md` for the field names on each form — they do
not match the visible captions (`Text1` is the DVBE certification line,
`Check Box8` is the N/A box), and a wrong name writes nothing without erroring.
For a form revision you haven't seen, run:

```bash
python scripts/inspect_form.py "<blank form>.pdf"
```

`python` is the interpreter `scripts/bbs-setup.ps1` installs on Windows (where `python3` is
only the Microsoft Store stub). Mac: type `python3` instead, here and in every command below.

Then write one JSON spec covering every form and run:

```bash
python scripts/fill_ca_forms.py spec.json
```

The script handles text, checkboxes, radio groups, and signature stamping. Its
docstring documents the spec shape.

Standard BBS answers, consistent across every state packet:

| Form | Answer |
|---|---|
| Bidder Declaration GSPD-05-105 | cert = DVBE; subcontractors = No; broker/agent = No; 51% rental = N/A; distinct element of work = the CUF statement |
| DGS PD 843 | DVBE ref 2009473; Section 2 box 1 (**not** a broker or agent); Section 3 blank unless renting equipment; page 1 of 1 |
| Darfur OBS 1500 | Option #1 — no business activities outside the US |
| OBS 1000 GenAI | GenAI utilized = **No**; detail questions and training question stay blank |
| CalRecycle 74 | agency + buyer header from the RFQ, vendor block from the profile, one row per quoted line |

Vendor constants live in `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`
(legal name, FEIN, address,
DVBE cert 2009473 exp. 12/31/2027, Jackson Dalton as DV owner).
Treat it as the authority — if an RFQ pre-fills a BBS field differently, the RFQ
is wrong; flag it rather than adopting it.

The **CUF statement is not a vendor constant and is not in the profile.** It is the
"distinct element of work" on the GSPD-05-105 Bidder Declaration, it is specific to
the bid, and the rep supplies it. Never compose one — a Commercially Useful Function
statement is a certification on a binding bid. Missing, it is `[MISSING — NEEDS
INPUT]`. `references/ca-form-rules.md` is authoritative.

CalRecycle recycled content is the one genuinely per-item judgment, and it is
**not** a constant — it follows what the product is made of. Across ~113 filed
CalRecycle 74s: metal goods are `11A` / 10%, plastics are `6` / 20%, paper and
filing supplies `1G` / 30%, tissue `1A` / 45%, and mixed-material, wood,
chemical, or electronic items are `N/A` / 0%. Read
`references/calrecycle-sabrc-guide.md` before filling those two columns — writing
0% / N/A on a box of nails is wrong, and this form is sworn under penalty of
perjury. Where the material is genuinely unclear and no sibling folder shows a
precedent for that institution, write `[REP TO CONFIRM]` and raise it in the
summary rather than inventing a figure.

## 5. Signatures

`Customers/State of CA Agencies/_README.md` carries standing authorization: Parker
and Jackson each approve their signature being applied to state requests, on the
understanding that the rep has reviewed the items with the buyer. Confirm that
review has happened for this RFQ, then apply:

- **The rep who quoted the job** — CalRecycle 74. Ruled by Parker 2026-09-18, matching
  `${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md`. The corpus shows Griffin on most
  historical packets; that is history, not the rule. Never default it to last time's signer.
- **Parker Marshall, Sales Manager** — Darfur OBS 1500, OBS 1000, and CalRecycle 74 on
  RFQs he quoted himself.
- **Jackson Dalton, President (DV Owner)** — DGS PD 843 and CV 012, the
  disabled-veteran declarations, and STD 204 as payee representative
  (`jackson@blackboxsafety.com`). These are his to sign, not Parker's.
- GSPD-05-105 has no signature block; the signed quote covers its certification.

Ask who quoted the job rather than defaulting to last time's answer.
`references/filled-form-precedents.md` has the split with counts.

Signature images: each signer's PNG location is `signature_image` on that person in
`${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` — Parker under
`default_rep.signature_image`, Jackson under `authorized_representatives.signature_image`
(the `dvbe_owner` entry). Read it from there; never copy a path into this file. Pass it
unchanged in the spec's `signatures` map and set `master_root` to the synced
`Black Box Safety - MASTER` folder; the script joins the `MASTER/` path itself, so never
build an absolute path by hand. `fill_ca_forms.py` checks every signer's image and every
blank form before it opens a PDF, and writes nothing unless every form filled and every
`sign` entry stamped. On a `⚑ SIGNATURE REQUIRED` or `⚑ SIGNATURE NOT APPLIED` stop, fix
the path or field name, or drop that `sign` entry and leave the line unsigned for the
rep. Never work around the stop.

If the rep hasn't reviewed the items, fill everything and leave the signature
lines blank with a note — an unsigned packet is fixable in a minute; a wrongly
sworn cert is not.

Check the DVBE cert expiration against the quote due date before signing anything.
Expired, or inside 30 days, means stop and tell the rep.

## 6. Verify by looking

These forms clip overflowing text silently and radio groups can render with two
options filled. Render every page and actually look at it:

```bash
python -c "import fitz, os, tempfile; [p.get_pixmap(dpi=110).save(os.path.join(tempfile.gettempdir(), f'v{i}.png')) for i,p in enumerate(fitz.open('filled.pdf'))]"
```

Check: no clipped values, one radio selected per group, signatures on the line
rather than on the caption, totals matching the quote, solicitation number
identical on every form. Fix and re-render — don't deliver a packet you haven't
seen rendered.

## 7. Deliver

Write everything to `~/bbs_forms/YYYYMMDD_<Institution>_<Item>/` and copy it into
the buyer's RFQ folder (a `FILLED/` subfolder keeps blanks and completed apart).

Name files `BBS_<FormID>_<Institution>_<Solicitation>_<YYYYMMDD>.pdf` and the
quote `<Institution>_Quote_<number>.pdf`.

Write `cover_summary.md` alongside them:

```markdown
# BBS Form Packet — <Agency>, <Institution> (<Buyer>)
**Solicitation:** ... - **BBS Quote:** ... — $X (pre-tax) - **Generated:** ...
**Account:** Grainger ... , track ...

## Pricing
<table: item, part, qty, unit, extended — plus the discount basis and sell rule>

## Forms filled
<table: form, what was filled>

## Signatures
<who signed what, and on what authorization>

## Notes / gap report
<judgment calls the rep should confirm, and anything left blank and why>
```

Then hand the rep the file list and call out, in the response itself, any
judgment call you made on their behalf — CalRecycle values, a shortened
description, a substituted item. Those are the things that come back to bite.

## The folder is the training data

`Customers/State of CA Agencies/` holds every prior packet — blanks the agency
sent and the filled versions BBS returned. When a question comes up that history
can answer (which revision this agency uses, what BBS wrote in this field last
time, whether this buyer accepted 0% on a similar item), read the corpus rather
than guessing or asking. Non-NASPO RFQs in there count: the pricing differs, the
certs are identical, so they are precedent for the forms even when they are not
precedent for the price. One exception: certification and preference fields. Never
copy a certification value from the corpus; take it from
`${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`. Why some past packets differ:
`bbs-foundations` `canonical-facts.md`, "Small-business status is channel-dependent".

To refresh the precedent tables after a batch of new RFQs:

```bash
python scripts/mine_precedents.py "<path to State of CA Agencies>" --out /tmp/mine.json
```

It classifies every PDF, pulls the filled AcroForm values, and reports
solicitation numbers, account numbers, and anything it couldn't classify — that
last list is where new form types show up. Filed values whose field name or value
carries an SB, MB or small-business token go to `historical_only`, not the precedent
table; a generically named checkbox cannot be detected and needs a human check.

## Reference files

- `references/form-field-maps.md` — field names, radio export values, and the
  clipping limits for each form. Read before writing a fill spec.
- `references/filled-form-precedents.md` — what BBS has actually written on each
  form, with counts, plus the signer roster and the form revisions in circulation.
  Read before deciding a value or a signer.
- `references/calrecycle-sabrc-guide.md` — material → SABRC code and postconsumer
  percentage. Read before filling those two columns.
- `references/agency-registry.md` — Grainger account per institution, contract
  vehicles, where the buyer notes live.
- `references/worked-example-cmc-900008.md` — a complete run end to end, including
  the six things that needed a second pass.
