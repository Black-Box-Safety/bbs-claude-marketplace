# Item entry spec

One JSON file per batch, usually one vendor quote. Save it in the customer folder next to
the quote it serves as `BC-import/items-<yyyy-mm-dd>.json`. The check writes
`<spec>.review.md` beside it and the commit appends `<spec>.bc-log.jsonl`.

## Top level

| Field | Required | Meaning |
|---|---|---|
| `vendorNo` | yes, unless every row carries its own | Default BC vendor number (`V#####`) for rows without one |
| `vendorName` | recommended | Name as it reads on the vendor quote; the check stops if BC's name for `vendorNo` does not contain it |
| `preparedBy` | yes | The rep's name; printed on the review sheet |
| `source` | yes | The document the costs came from, with number and date |
| `items` | yes | One object per item, below |

## Per item

| Field | Required | Rule |
|---|---|---|
| `number` | yes | 1-20 ASCII characters, no leading or trailing spaces, unique in the spec and absent from BC. Grainger SKU on Grainger-filled buys |
| `displayName` | yes | 1-100 ASCII characters, starts with the manufacturer. Hyphens and straight quotes only |
| `displayName2` | no | Up to 50 ASCII characters of overflow (accessories included, size notes) |
| `manufacturer` | yes | The brand the description must start with (`Carr Lane`, `Harrington`, `3M`) |
| `baseUoM` | yes | A unit of measure code that exists in BC. `EA` unless the vendor sells a pack, case or box; then the real code (`PK10`, `CS`, `BX`) |
| `costPer` | yes | What one unit of cost buys. Must equal `baseUoM`; convert before you write the spec |
| `unitCost` | yes | Greater than zero, the vendor's price to BBS before freight and tax. Zero only with `includedWith` |
| `costSource` | yes | Where the cost was read, with a number or date: `Carr Lane SQ-122475 10/08/2026`, `Grainger MCP acct 888783805 2026-10-14`, `Star CSP 0052299006 10/07/2026`. Words like verbal, roughly, estimate, approx or phone fail the check |
| `preparedBy` (top level) | yes | Must equal the `--approved-by` name on commit |
| `unitPrice` | no | Sell price when known. Never below cost; equal to cost needs `zeroMarginOk: true`. Leave off for Grainger items priced at quote time |
| `zeroMarginOk` | no | `true` only when the rep accepts selling at cost and has seen that on the sheet |
| `vendorNo` | no | Overrides the top-level vendor for this row (mixed Carr Lane plus Grainger batches) |
| `vendorItemNo` | no | The vendor's own part number when it differs from `number`, up to 50 characters. Lands in Vendor Item No. on the card |
| `includedWith` | no | Another `number` in this spec whose price covers this accessory. Forces cost 0 and price 0 on this row |

Everything the API cannot take from the spec is fixed: type Inventory, posting groups
PRODUCTS and INVENTORY, tax group TAXABLE. Item category, replenishment, costing method and
the warehouse fields stay at BC defaults, which is how every BBS item is set up.

## Example

```json
{
  "vendorNo": "V11469",
  "vendorName": "Geisler",
  "preparedBy": "Parker Marshall",
  "source": "Carr Lane quote SQ-122475 (10/08/2026) for Bechtel PO 833193",
  "items": [
    {
      "number": "CL-10000-SHR-1",
      "displayName": "Carr Lane CL-10000-SHR-1 Swivel Hoist Ring, 1\"-8, 10,000 lb",
      "manufacturer": "Carr Lane",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 288.36,
      "unitPrice": 339.25,
      "vendorItemNo": "CL-10000-SHR-1",
      "costSource": "Carr Lane SQ-122475 10/08/2026"
    },
    {
      "number": "1TAJ3",
      "displayName": "Harrington LB010-10 Lever Chain Hoist, Hook Mount, 2,000 lb, 10 ft Lift",
      "manufacturer": "Harrington",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 598.97,
      "vendorNo": "V10017",
      "costSource": "Star CSP 0052299006 10/07/2026 acct 888783805"
    },
    {
      "number": "CAB-16AWG-AC",
      "displayName": "Cisco AC power cord, 16 AWG",
      "manufacturer": "Cisco",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 0,
      "unitPrice": 0,
      "includedWith": "C1300-8FP-2G"
    }
  ]
}
```

The third row only validates if `C1300-8FP-2G` is also in the spec.

## What the review sheet shows

| # | Item No. | Description | UoM | Vendor | Vendor Item | Cost | Price | GM% | Cost source |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CL-10000-SHR-1 | Carr Lane CL-10000-SHR-1 Swivel Hoist Ring, 1"-8, 10,000 lb | EA | V11469 Geisler | CL-10000-SHR-1 | 288.36 | 339.25 | 15.0 | Carr Lane SQ-122475 10/08/2026 |

The rep reads this table, not the JSON. The approval token at the top of the sheet is the
one the commit command needs, and it changes whenever the spec file changes.
