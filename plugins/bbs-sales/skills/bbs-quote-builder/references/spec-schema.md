# Quote Spec Schema

The `build_quote.js` script consumes a JSON file with this structure.

## Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `quoteNumber` | string | yes | BBS 900001-series number, e.g. `"900003"`. Prompt the rep. |
| `documentDate` | string | yes | Quote date, e.g. `"06/04/2026"`. |
| `validTo` | string | yes | Expiration date, e.g. `"07/31/2026"`. |
| `shipmentMethod` | string | no | Defaults to `"FOB Destination"`. |
| `solicitation` | string | no | RFQ/solicitation number. Omit to hide the row. |
| `billTo` | string[] | yes | Lines of the Bill-to block. |
| `shipTo` | string[] | yes | Lines of the Ship-to block. Drives tax jurisdiction. |
| `pricing.method` | string | yes | `"margin"` or `"markup"`. |
| `pricing.rate` | number | yes | Decimal, e.g. `0.20` for 20%. |
| `taxRate` | number | no | Decimal, e.g. `0.0875`. Omit or `0` for a pre-tax quote. |
| `estimatedPricing` | boolean | no | `true` appends `*` to prices + estimate footnote. |
| `items[]` | array | yes | Line items, in order. |
| `items[].partNumber` | string | no | SKU / manufacturer part / Amazon ASIN. Omit → em-dash. |
| `items[].description` | string | yes | Full product description. |
| `items[].qty` | number | yes | Quantity. |
| `items[].uom` | string | no | Unit of measure, e.g. `"Pack"`, `"Box"`, `"Each"`. Defaults to `"Each"`. |
| `items[].unitCost` | number | yes | **Vendor cost** — the script applies markup/margin to get the sell price. |

## Pricing math

- `margin`: `sell = unitCost / (1 - rate)`
- `markup`: `sell = unitCost * (1 + rate)`
- `amount = round(sell * qty)`
- `subtotal = sum(amount)`
- `tax = subtotal * taxRate`
- `total = subtotal + tax`

All money is rounded to the cent at each step.

## Worked example

```json
{
  "quoteNumber": "900003",
  "documentDate": "06/04/2026",
  "validTo": "07/31/2026",
  "shipmentMethod": "FOB Destination",
  "solicitation": "SCTASK0021599 / RITM0018734",
  "billTo": ["Office of Energy Infrastructure Safety", "CA Natural Resources Agency"],
  "shipTo": ["Office of Energy Infrastructure Safety", "715 P Street, 15th Floor", "Sacramento, CA 95814", "US"],
  "pricing": { "method": "margin", "rate": 0.20 },
  "taxRate": 0.0875,
  "estimatedPricing": true,
  "items": [
    { "partNumber": "B08N3GCLYP", "description": "Envelope Moistener, Pack Of 4", "qty": 4, "uom": "Pack", "unitCost": 12.42 },
    { "partNumber": "9828588", "description": "Office Depot Brand Retractable Ballpoint Pens, Black, Pack Of 50", "qty": 8, "uom": "Pack", "unitCost": 16.99 }
  ]
}
```

In this example each price renders with a trailing `*` and the estimate footnote
appears, because `estimatedPricing` is `true`. Drop that flag (or set it false)
once real vendor costs replace the estimates.
