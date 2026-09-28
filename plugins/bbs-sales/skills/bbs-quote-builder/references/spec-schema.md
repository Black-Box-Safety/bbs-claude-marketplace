# Quote Spec Schema

The `build_quote.js` script consumes a JSON file with this structure. It runs offline —
it never calls Business Central — so the BC read-back in SKILL.md step 2 happens first and
its result goes into `bcQuote`. The script refuses to build without it.

## Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `bcQuote.number` | string | yes | The Business Central sales quote number this document represents, e.g. `"SQ-104797"`, **as read back from BC**. Must be `SQ-` plus six digits. Never generated, predicted, or taken from a local series. |
| `bcQuote.customerNumber` | string | yes | The **sell-to** customer number from the same read-back, e.g. `"C10171"` (bill-to can differ). |
| `bcQuote.customerName` | string | yes | The sell-to customer name. The script warns if it appears in neither `billTo` nor `shipTo`. |
| `documentDate` | string | yes | Quote date, e.g. `"09/28/2026"`. Prefer the BC quote's `documentDate`. |
| `validTo` | string | yes | Expiration date. Prefer the BC quote's `validUntilDate`. |
| `shipmentMethod` | string | no | Defaults to `"FOB Destination"`. |
| `solicitation` | string | no | RFQ/solicitation number. Omit to hide the row. |
| `billTo` | string[] | yes | Lines of the Bill-to block. Prefer the BC quote's `billTo*` fields. |
| `shipTo` | string[] | yes | Lines of the Ship-to block. Prefer the BC quote's `shipTo*` fields. Drives tax jurisdiction. |
| `pricing.method` | string | yes, unless every line is Grainger and `graingerAtCost` is true | `"margin"`, `"markup"`, or `"at-cost"`. No default — the script fails without it. |
| `pricing.rate` | number | yes for margin/markup | Decimal from 0 to under 1, e.g. `0.20` for 20% — so markup is capped under 100%. Ignored for `at-cost`. |
| `pricing.graingerAtCost` | boolean | yes if any line is `source: "grainger"`, unless method is `at-cost` | `true`: Grainger lines at cost (CA state schedule / cooperative quotes). `false`: Grainger lines follow the method. No default — missing is an error, because at-cost is ruled only for CA state schedules. |
| `taxRate` | number | no | Decimal from 0 to under 0.2, e.g. `0.0875`. Omit or `0` for a pre-tax quote. A string, a percent (`8.75`) or a negative is rejected. Check it against the BC quote's tax (SKILL.md step 2.5). |
| `estimatedPricing` | boolean | no | `true` appends `*` to prices + estimate footnote. |
| `columns.leadTime` | boolean | no | `true` adds a Lead Time column (narrows Description). |
| `items[]` | array | yes | Line items, in order. |
| `items[].partNumber` | string | no | SKU / manufacturer part / Amazon ASIN. Omit → em-dash. |
| `items[].description` | string | yes | Full product description. |
| `items[].qty` | number | yes | Quantity. |
| `items[].uom` | string | no | Unit of measure, e.g. `"Pack"`, `"Box"`, `"Each"`. Defaults to `"Each"`. |
| `items[].leadTime` | string | no | Only rendered if `columns.leadTime` is true, e.g. `"1–3 business days"`. Omit → em-dash. From a tool result or a vendor's written quote, never estimated. |
| `items[].source` | string | no | `"grainger"` marks a Grainger line, priced per `pricing.graingerAtCost` (or at cost under `at-cost`). The only accepted value. |
| `items[].unitCost` | number | yes | **Vendor cost**, 0 or more — discount lines are not supported. For a Grainger line, the Grainger MCP `unitPrice`. |

`documentDate`, `validTo`, `billTo`, `shipTo` and every `items[].description` are checked
before anything is built; a missing one is an `ERROR:` and exit 1, not a blank on the page.

A spec with a top-level `quoteNumber` (the retired local-series field) is rejected with a
message pointing here.

## Pricing math

- Grainger line (`source: "grainger"`): `sell = unitCost` when `graingerAtCost` is true
  or the method is `at-cost`; otherwise priced by the method. At cost is ruled for CA
  state schedules only — the Grainger row of
  `bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md` and
  `bbs-doctrine.md` #17.
- `at-cost`: `sell = unitCost`
- `margin`: `sell = unitCost / (1 - rate)`
- `markup`: `sell = unitCost * (1 + rate)`
- `amount = round(sell * qty)`
- `subtotal = sum(amount)`
- `tax = subtotal * taxRate`
- `total = subtotal + tax`

All money is rounded to the cent at each step.

## Worked example

`SQ-100000` and `C00000` below are placeholders, not real BC records — a real spec carries
what the read-back returned.

```json
{
  "bcQuote": { "number": "SQ-100000", "customerNumber": "C00000", "customerName": "Office of Energy Infrastructure Safety" },
  "documentDate": "09/28/2026",
  "validTo": "10/28/2026",
  "shipmentMethod": "FOB Destination",
  "solicitation": "SCTASK0021599 / RITM0018734",
  "billTo": ["Office of Energy Infrastructure Safety", "CA Natural Resources Agency"],
  "shipTo": ["Office of Energy Infrastructure Safety", "715 P Street, 15th Floor", "Sacramento, CA 95814", "US"],
  "pricing": { "method": "margin", "rate": 0.20, "graingerAtCost": true },
  "taxRate": 0.0875,
  "columns": { "leadTime": true },
  "items": [
    { "partNumber": "B08N3GCLYP", "description": "Envelope Moistener, Pack Of 4", "qty": 4, "uom": "Pack", "unitCost": 12.42, "leadTime": "5–7 business days" },
    { "partNumber": "1ZRZ8", "description": "Walk-through metal detector", "qty": 1, "uom": "Each", "unitCost": 175.36, "source": "grainger", "leadTime": "1–3 business days" }
  ]
}
```

The first line is margin-priced (12.42 ÷ 0.80 = 15.53); the Grainger line prints 175.36
unchanged because `graingerAtCost` is true — right for this CA state agency. With
`graingerAtCost: false` it would be margin-priced too (219.20). `estimatedPricing` stars every price on the document, so set it only when the
costs really are estimates — a Grainger MCP price is not one.
