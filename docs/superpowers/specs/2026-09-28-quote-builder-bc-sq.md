# bbs-quote-builder: Business Central SQ numbers replace the 900001 series — design

**Date:** 2026-09-28
**Ruling:** Parker, 2026-09-28. BBS customer quotes carry the Business Central `SQ-######`
number. The local 900001 series is retired. (The ruling itself is recorded in canon by a
separate change; this spec does not restate it anywhere a second copy could go stale.)

## Problem

`bbs-quote-builder` on `main` asks the rep for a number "in the 900001 series" and
`naspo-quote` tells the model to scan the Customers folder for `*Quote_9000*` and propose the
next one. Two things are wrong with that now:

1. The series is retired, so every quote it produces carries a number that does not exist in
   the system of record (invariant 1).
2. Any scheme that *predicts* a next number — from a folder listing or from BC — can hand a
   customer a number someone else takes a minute later. That is a plausible wrong number on
   a customer document, the exact failure this repo exists to prevent.

## Prior art: Parker's design on `origin/sales-territory-0.3.0`

That branch already moved the skill to `SQ-######`, but step 2 pulls the highest
`salesQuotes.number`, **increments it**, and prints the prediction, then tells the rep to
"log it in BC" afterwards. That is the prediction failure above, one system over: BC assigns
SQ numbers when a quote record is created, and a predicted number is taken by whichever rep
creates the next record first. **Not copied.**

What *is* taken from it:

| From the old design | Taken? | Why |
|---|---|---|
| `SQ-######` format check in the script | Yes, made a hard error | a bad number must not reach a document |
| "This skill only reads from BC; it never writes" | Yes | invariant 5 and the BC MCP is read-only anyway |
| Predict next number (`orderby=number desc`, +1) | **No** | see above |
| "Log it in BC after it goes out" | **No**, reversed | the record exists first; the document follows it |
| Optional `Lead Time` column (commit `fbcd2f8`, Parker's WIP) | Yes | fits main's table cleanly |
| At-cost pricing (`passthrough`) | Yes, reshaped | canon says Grainger is at cost; see Pricing |
| BC-print layout (SQ-104776: logo left, centered title, totals band) | **Yes — Parker chose it 2026-09-28** | see Layout |
| `paymentTerms`, `taxBasis`, `notes[]`, `footerNotes[]`, UOM/COO toggles | Yes, with the layout | BC-held facts now come from the read-back; see Layout |

## Design

### Quote number: read back, never generated

The rep creates the sales quote in Business Central (a human creates records), or hands over
an SQ number that already exists. The skill then:

1. Reads it back — `bc_get_sales_document` with the SQ number (it searches quotes), or
   `bc_query_entity` on `salesQuotes` filtered `number eq 'SQ-######'`.
2. Confirms it resolves, and that its customer is the customer this document is for.
3. Takes the header it can use (bill-to / ship-to address, document date, valid-until) from
   that record rather than re-typing it.
4. If the BC quote already carries lines, compares them against the document's lines and
   flags any mismatch in item, quantity or total — it does not silently pick one side.

If there is no SQ number, it does not resolve, or BC is unreachable: stop, and put
`[MISSING — NEEDS INPUT]` in front of the rep. There is no fallback series, no prediction,
and no write to BC, ever.

The script cannot call BC itself (the BC connection is an MCP tool, not an HTTP client the
script owns), so it enforces what it can see: the spec must carry a `bcQuote` block holding
what the read-back returned (`number`, `customerNumber`, `customerName`). The script refuses
to build without it, refuses a number that is not `SQ-` plus six digits, and refuses a spec
that still uses the old top-level `quoteNumber` key, naming the reason. The block is
evidence that step 1 ran; it is not a substitute for running it.

### Pricing

- **Grainger lines are at cost.** Canon: `bbs-foundations/.../bbs-doctrine.md` #19 and the
  Grainger MCP row of `canonical-facts.md`; operative rule in `grainger-pricing` §2. The
  skill points there and does not restate the reasoning.
- New per-line `source: "grainger"`: that line's `unitCost` is the Grainger MCP `unitPrice`
  and prints unchanged whatever `pricing.method` says. Main's margin/markup math can no
  longer touch a Grainger line, which closes the gap `MAINTAINER-GUIDE.md` recorded.
- New `pricing.method: "at-cost"` for a whole quote at cost (the NASPO / state-schedule
  case, which `naspo-quote` today fakes as `markup` at rate 0).
- Main's `margin` / `markup` logic is kept for non-Grainger lines — nothing in canon
  contradicts it (competitive bids carry margin, doctrine #17).
- One change to the defaults: main silently fell back to 20% margin when `pricing` was
  missing. The SKILL.md already says "never assume"; the script now agrees and fails when
  a non-Grainger line exists and `pricing.method` / `pricing.rate` are absent
  (invariant 4).

- Found while verifying: main rounded with `Math.round(x * 100) / 100`, which takes
  12.42 ÷ 0.80 = 15.525 **down** to 15.52 (floating point stores 1552.4999…). A one-cent
  undercount per unit on a binding document. Now rounds half up via a `r2()` helper.

### Lead Time column

`columns.leadTime: true` plus `items[].leadTime` (string, em-dash when absent), ported from
`fbcd2f8`. Main's line table has fixed widths summing to 9160 DXA; the new column takes its
width from Description, as the WIP commit did. Everything else in main's table is
unchanged.

### Layout

**Ruled: Parker, 2026-09-28 — "do the bc print layout".** An earlier revision of this
spec kept main's SQ-104032 letterhead and left the choice to him; he chose the Business
Central print layout from `origin/sales-territory-0.3.0` (reference SQ-104776). Ported:

- Logo top-left, `Quote - SQ-######` centered, company block beneath; Bill to Address /
  Ship to Address; two-column metadata grid; totals band (Subtotal · Tax % · Tax Basis ·
  Tax Amount · Total); real Page X / Y footer field.
- `paymentTerms`, `taxBasis`, `notes[]`, `footerNotes[]`, and the UOM / Country of Origin
  column toggles, alongside the Lead Time column already ported.

Changed on the way in, because the old design typed facts BC already holds or printed
facts without a source:

- **Company block** (legal name, street, city/state/zip, phone) is read from
  `bbs-sales/references/vendor_profile.json`; the old design, and main, had literals. The
  printed address follows the profile's spelling ("1950 Cordell CT Ste 103", ZIP 92020).
- **Certification line**, new: a required `certChannel` — `california` → `DVBE 2009473`,
  `federal` → `SDVOSB`, `none` → no line — strings from the vendor profile, never mixed
  and never SB in California (AGENTS.md, "Certifications follow the channel").
- **Payment terms and shipment method** are required and come from the BC quote
  (`paymentTermsId` → `paymentTerms`, `shipmentMethodId` → `shipmentMethods`). The old
  "FOB Destination" default is gone: a typed default is a fact owned by BC.
- **Country of origin** prints only when documented: each value needs
  `countryOfOriginSource` or the build fails; an undocumented line prints blank and is
  flagged. On a federal or prime document an unsupported origin is a false certification.
- **`taxBasis`** is validated (0 ≤ basis ≤ subtotal).
- Salesperson is not printed by this layout, so it is not read.
- The logo asset is shared with main (identical file); kept.

### Review round (independent review of `be4216a`)

- Script validates `taxRate` (number, 0 ≤ rate < 0.2), `documentDate`, `validTo`, `billTo`,
  `shipTo`, `items[].description`; each missing/bad value is an `ERROR:` and exit 1.
- Customer check is on the BC **sell-to** customer (sell-to and bill-to differ in live BC);
  on the NASPO path it is compared with the buyer file's BC customer ID. The script warns
  when `bcQuote.customerName` is in neither address block. An empty BC bill-to address is
  asked about, never printed as a name-only block.
- Tax is compared with the BC quote's line `taxPercent` / header `totalTaxAmount` and
  flagged on mismatch.
- The unsourced "20% house default" is gone; the rep chooses method and rate.
- The Grainger at-cost guarantee depends on the model tagging `source: "grainger"`; this is
  said plainly, `grainger-pricing` names the tag, and step 9 checks the echoed count.
- `pricing.rate` stays below 1 for markup too (catches `20` typed for `0.20`); negative
  `unitCost` (discount lines) stays rejected and is documented.

### Second review round (from the PR #36 review)

Grainger at cost is ruled only for CA state schedule / cooperative quotes (doctrine #17);
prime/commercial (e.g. Bechtel) is open for Parker. Forcing every Grainger line to cost
would put a plausible wrong number on a commercial quote. So the builder no longer does:
a spec with Grainger lines must state `pricing.graingerAtCost` true/false, or use the
`at-cost` method, or the script exits 1. `naspo-quote` sets it for CA state quotes. The
canon pointer is the Grainger row of `canonical-facts.md` (scoped by PR #36) and doctrine
#17 — the earlier pointer to #19 named the wrong rule. This supersedes the "Grainger lines
are at cost" bullets above.

## Knock-on changes

- `naspo-quote` §3 — number comes from BC per `bbs-quote-builder`; its spec row moves to
  `at-cost` + `source: "grainger"`; `requires:` gains `business-central`.
- `naspo-quote/references/worked-example-cmc-900008.md` — historical; a dated note that the
  numbering it shows is retired.
- `commands/ca-rfq.md` Gate 5 — "the number it proposed" becomes the BC number it read back.
- `docs/evals/skills.json` regenerated from the new description.
- `docs/MAINTAINER-GUIDE.md` — the "still documents markup math" bullet is resolved.
- Left alone: `docs/assessments/*` (dated records), real historical values in
  `filled-form-precedents.md` and the buyer-context example row.

## Out of reach

Parker's account-synced copy of `bbs-quote-builder` in claude.ai still describes the 900001
series. Git cannot reach it; he must update or disable it in claude.ai Settings →
Capabilities → Skills.
