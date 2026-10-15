# Quote Spec Schema

The `build_quote.js` script consumes a JSON file with this structure and prints the
Business Central quote layout (reference SQ-104776). It runs offline — it never calls
Business Central — so the BC read-back in SKILL.md step 2 happens first, and the fields
marked **BC** below are copied from it, not typed. Where the rep's source disagrees with
BC, flag it for the rep; don't overwrite either side.

The company block (legal name, street, city/state/zip, phone, certification string) is
not in the spec at all: the script reads it from the plugin's
`references/vendor_profile.json`.

## Fields

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `bcQuote.number` | string | yes | **BC** `number` | The SQ number, e.g. `"SQ-104797"`. Must be `SQ-` plus six digits. Never generated, predicted, or taken from a local series. |
| `bcQuote.customerNumber` | string | yes | **BC** `customerNumber` | The **sell-to** customer number (bill-to can differ). |
| `bcQuote.customerName` | string | yes | **BC** `customerName` | Sell-to name. The script warns if it appears in neither `billTo` nor `shipTo`. |
| `certChannel` | string | yes | rep / channel | `"california"` → `DVBE <osds_ref_number>`; `"federal"` (federal agencies and primes) → `SDVOSB`; `"none"` → no line. No default. For `california` the script checks the profile's `certifications.sb_dvbe.expiration` against `documentDate`: expired (or no expiration on file) → `ERROR:`; within 30 days → `WARNING:`. |
| `documentDate` | string | yes | **BC** `documentDate` | `MM/DD/YYYY` or `YYYY-MM-DD`, e.g. `"09/28/2026"`. |
| `validTo` | string | yes | **BC** `validUntilDate` | |
| `paymentTerms` | string | yes | **BC** `paymentTermsId` → `paymentTerms.displayName` | e.g. `"Net 45"`. No default; if BC has none, ask. |
| `shipmentMethod` | string | yes | **BC** `shipmentMethodId` → `shipmentMethods.displayName` | No default; if BC has none, ask. |
| `solicitation` | string | no | the RFQ | RFQ/solicitation number. Omit to hide the row. |
| `billTo` | string[] | yes | **BC** `billTo*` | Lines of the Bill to Address block. If BC's bill-to address is empty, ask — never a name-only block. |
| `shipTo` | string[] | yes | **BC** `shipTo*` | Lines of the Ship to Address block. Drives tax jurisdiction. |
| `pricing.method` | string | yes, unless every line is Grainger and `graingerAtCost` is true | rep | `"margin"`, `"markup"`, or `"at-cost"`. No default. |
| `pricing.rate` | number | yes for margin/markup | rep | Decimal from 0 to under 1, e.g. `0.20` — so markup is capped under 100%. Ignored for `at-cost`. |
| `pricing.graingerAtCost` | boolean | yes if any line is `source: "grainger"`, unless method is `at-cost` | rep / channel | `true`: Grainger lines at cost. `false`: Grainger lines follow the method. No default. Which applies depends on the channel — canon's "Grainger sell rule, by channel". |
| `taxRate` | number | no | rep, checked against **BC** line `taxPercent` / `totalTaxAmount` | Decimal from 0 to under 0.2, e.g. `0.0725`. Omit or `0` for pre-tax. A string, a percent (`7.25`) or a negative is rejected. |
| `taxBasis` | number | no | rep, checked against **BC** | Amount tax is calculated on, when less than the subtotal. 0 or more, never above the subtotal. Defaults to the subtotal. Given with no tax rate → `WARNING:`. |
| `estimatedPricing` | boolean | no | rep | `true` appends `*` to prices + estimate footnote. |
| `columns.uom` | boolean | no | rep | Adds a UOM column; every line must then carry `uom`. |
| `columns.countryOfOrigin` | boolean | no | rep | Adds a Country of Origin column. Lines without a documented origin print blank and are flagged. |
| `columns.leadTime` | boolean | no | rep | Adds a Lead Time column. |
| `notes` | string[] | no | rep | Free-text lines under the metadata grid. |
| `footerNotes` | string[] | no | rep | Small grey lines under the totals band. |
| `items[]` | array | yes | source doc | Line items, in order. |
| `items[].partNumber` | string | no | source doc | SKU / manufacturer part / Amazon ASIN. Omit → em-dash. |
| `items[].description` | string | yes | source doc | Full product description. |
| `items[].qty` | number | yes | source doc | Positive quantity. |
| `items[].uom` | string | **yes when `columns.uom` is on** | source doc | Unit of measure from the source (`"Pack"`, `"Box"`, `"Each"`). No default — a pack price printed as "Each" is a wrong number, so a missing unit is an `ERROR:`. Ignored when the column is off. |
| `items[].countryOfOrigin` | string | no | documented source only | Rendered only with `columns.countryOfOrigin`. Requires `countryOfOriginSource`. Omit when undocumented — never inferred. |
| `items[].countryOfOriginSource` | string | with `countryOfOrigin` | — | Where the origin is documented, e.g. `"Grainger MCP grainger_search, 09/28/2026"` or `"manufacturer spec sheet rev C"`. Not printed. |
| `items[].leadTime` | string | no | tool result / vendor quote | Rendered only with `columns.leadTime`. Omit → em-dash. Never estimated. |
| `items[].source` | string | no | — | `"grainger"` marks a Grainger line, priced per `pricing.graingerAtCost` (or at cost under `at-cost`). The only accepted value. |
| `items[].unitCost` | number | yes | vendor quote / tool result | **Vendor cost**, 0 or more — discount lines are not supported. For a Grainger line, the Grainger MCP `unitPrice`. |

A spec with a top-level `quoteNumber` (the retired local-series field) is rejected. Every
required field is checked before anything is built; a missing or invalid one is an
`ERROR:` and exit 1, not a blank on the page.

## Pricing math

- Grainger line (`source: "grainger"`): `sell = unitCost` when `graingerAtCost` is true
  or the method is `at-cost`; otherwise priced by the method. Which channel is at cost
  is ruled in one place: "Grainger sell rule, by channel" in
  `bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`.
- `at-cost`: `sell = unitCost`
- `margin`: `sell = unitCost / (1 - rate)`
- `markup`: `sell = unitCost * (1 + rate)`
- `amount = round(sell * qty)`
- `subtotal = sum(amount)`
- `tax = (taxBasis ?? subtotal) * taxRate`
- `total = subtotal + tax`

All money is rounded to the cent, half up, at each step.

## Worked example — CA state agency, margin with one Grainger line

`SQ-100000` and `C00000` are placeholders, not real BC records — a real spec carries what
the read-back returned.

```json
{
  "bcQuote": { "number": "SQ-100000", "customerNumber": "C00000", "customerName": "CAL FIRE" },
  "certChannel": "california",
  "documentDate": "09/28/2026",
  "validTo": "10/28/2026",
  "paymentTerms": "Net 45",
  "shipmentMethod": "FOB Destination",
  "solicitation": "RFQ 26-07-010",
  "billTo": ["CAL FIRE", "PO Box 944246", "Sacramento, CA 94244", "US"],
  "shipTo": ["CAL FIRE Shasta-Trinity Unit", "875 Cypress Ave.", "Redding, CA 96001", "US"],
  "pricing": { "method": "margin", "rate": 0.20, "graingerAtCost": true },
  "taxRate": 0.0725,
  "columns": { "leadTime": true },
  "notes": ["Metal detector ships direct from Grainger; envelope moisteners 5–7 business days."],
  "footerNotes": ["Quote valid through date shown. Pricing subject to product availability. Reference quote number on any resulting order."],
  "items": [
    { "partNumber": "B08N3GCLYP", "description": "Envelope Moistener, Pack Of 4", "qty": 4, "unitCost": 12.42, "leadTime": "5–7 business days" },
    { "partNumber": "1ZRZ8", "description": "Walk-through metal detector", "qty": 1, "unitCost": 175.36, "source": "grainger", "leadTime": "1–3 business days" }
  ]
}
```

The first line is margin-priced (12.42 ÷ 0.80 = 15.53); the Grainger line prints 175.36
unchanged because `graingerAtCost` is true — right for a CA state agency. The header
carries `DVBE 2009473` because `certChannel` is `california`.

## Worked example — federal prime, origin disclosed

```json
{
  "bcQuote": { "number": "SQ-100001", "customerNumber": "C00001", "customerName": "Bechtel National, Inc." },
  "certChannel": "federal",
  "documentDate": "09/28/2026",
  "validTo": "10/28/2026",
  "paymentTerms": "Net 60",
  "shipmentMethod": "FOB Destination",
  "solicitation": "RFP 752520",
  "billTo": ["Bechtel National, Inc.", "1450 Washington Avenue", "Vandenberg SFB, CA 93437", "US"],
  "shipTo": ["Bechtel National, Inc.", "1450 Washington Avenue", "Vandenberg SFB, CA 93437", "US"],
  "pricing": { "method": "margin", "rate": 0.15, "graingerAtCost": false },
  "taxRate": 0,
  "columns": { "countryOfOrigin": true, "uom": true },
  "items": [
    { "partNumber": "34D659", "description": "DAYTON Wire-Spool Dispensing Cart, 300 lb", "qty": 1, "uom": "Each", "unitCost": 446.11, "source": "grainger", "countryOfOrigin": "Taiwan", "countryOfOriginSource": "Grainger MCP product record" },
    { "partNumber": "12X312", "description": "Wagon Truck, Flow-Through Metal Deck", "qty": 6, "uom": "Each", "unitCost": 260.00, "source": "grainger" }
  ]
}
```

Here the rep stated `graingerAtCost: false` for this prime — per canon's "Grainger sell
rule, by channel", prime Grainger lines may be marked up once the rep has asked BBS's
Grainger account manager for a discount; `unitCost` is that discounted cost. The second line has no documented
origin: its cell prints blank and the script prints a `[FLAG: …]`.
