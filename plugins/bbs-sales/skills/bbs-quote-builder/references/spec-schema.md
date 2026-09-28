# Quote Spec Schema

The `build_quote.js` script consumes a JSON file with this structure. It runs offline —
it never calls Business Central — so the BC read-back in SKILL.md step 2 happens first and
its result goes into `bcQuote`. The script refuses to build without it.

## Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `bcQuote.number` | string | yes | The Business Central sales quote number this document represents, e.g. `"SQ-104797"`, **as read back from BC**. Must be `SQ-` plus six digits. Never generated, predicted, or taken from a local series. |
| `bcQuote.customerNumber` | string | yes | From the same read-back, e.g. `"C10171"`. |
| `bcQuote.customerName` | string | yes | From the same read-back. Check it is the customer this document is for. |
| `documentDate` | string | yes | Quote date, e.g. `"09/28/2026"`. Prefer the BC quote's `documentDate`. |
| `validTo` | string | yes | Expiration date. Prefer the BC quote's `validUntilDate`. |
| `shipmentMethod` | string | no | Defaults to `"FOB Destination"`. |
| `solicitation` | string | no | RFQ/solicitation number. Omit to hide the row. |
| `billTo` | string[] | yes | Lines of the Bill-to block. Prefer the BC quote's `billTo*` fields. |
| `shipTo` | string[] | yes | Lines of the Ship-to block. Prefer the BC quote's `shipTo*` fields. Drives tax jurisdiction. |
| `pricing.method` | string | yes, unless every line is `source: "grainger"` | `"margin"`, `"markup"`, or `"at-cost"`. No default — the script fails without it. |
| `pricing.rate` | number | yes for margin/markup | Decimal, e.g. `0.20` for 20%. Ignored for `at-cost`. |
| `taxRate` | number | no | Decimal, e.g. `0.0875`. Omit or `0` for a pre-tax quote. |
| `estimatedPricing` | boolean | no | `true` appends `*` to prices + estimate footnote. |
| `columns.leadTime` | boolean | no | `true` adds a Lead Time column (narrows Description). |
| `items[]` | array | yes | Line items, in order. |
| `items[].partNumber` | string | no | SKU / manufacturer part / Amazon ASIN. Omit → em-dash. |
| `items[].description` | string | yes | Full product description. |
| `items[].qty` | number | yes | Quantity. |
| `items[].uom` | string | no | Unit of measure, e.g. `"Pack"`, `"Box"`, `"Each"`. Defaults to `"Each"`. |
| `items[].leadTime` | string | no | Only rendered if `columns.leadTime` is true, e.g. `"1–3 business days"`. Omit → em-dash. From a tool result or a vendor's written quote, never estimated. |
| `items[].source` | string | no | `"grainger"` marks a Grainger line: always at cost, whatever `pricing.method` says. The only accepted value. |
| `items[].unitCost` | number | yes | **Vendor cost.** For a Grainger line, the Grainger MCP `unitPrice`. |

A spec with a top-level `quoteNumber` (the retired local-series field) is rejected with a
message pointing here.

## Pricing math

- Grainger line (`source: "grainger"`): `sell = unitCost` — at cost, always. Why:
  `grainger-pricing` §2 and `bbs-foundations/skills/bbs-claude-md-forge/references/bbs-doctrine.md` #19.
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
  "pricing": { "method": "margin", "rate": 0.20 },
  "taxRate": 0.0875,
  "columns": { "leadTime": true },
  "items": [
    { "partNumber": "B08N3GCLYP", "description": "Envelope Moistener, Pack Of 4", "qty": 4, "uom": "Pack", "unitCost": 12.42, "leadTime": "5–7 business days" },
    { "partNumber": "1ZRZ8", "description": "Walk-through metal detector", "qty": 1, "uom": "Each", "unitCost": 175.36, "source": "grainger", "leadTime": "1–3 business days" }
  ]
}
```

The first line is margin-priced (12.42 ÷ 0.80 = 15.53); the Grainger line prints 175.36
unchanged. `estimatedPricing` stars every price on the document, so set it only when the
costs really are estimates — a Grainger MCP price is not one.
