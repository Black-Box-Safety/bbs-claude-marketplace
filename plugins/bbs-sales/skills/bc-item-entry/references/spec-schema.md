# Item entry spec

One JSON file per batch, usually one vendor quote. Save it in the customer folder next to
the quote it serves as `BC-import/items-<yyyy-mm-dd>.json`. The check writes
`<spec>.review.md` beside it and the commit appends `<spec>.bc-log.jsonl`.

## Top level

| Field | Required | Meaning |
|---|---|---|
| `vendorNo` | yes, unless every row carries its own | Default BC vendor number (`V#####`, upper-case) for rows without one |
| `vendorName` | yes, whenever `vendorNo` is set | Name as it reads on the vendor quote; the check stops if BC's name for `vendorNo` does not contain it |
| `preparedBy` | yes | The rep's name; printed on the review sheet and matched against `--approved-by` on commit |
| `source` | yes | The document the costs came from, with number and date |
| `items` | yes | One object per item, below |

## Per item

| Field | Required | Rule |
|---|---|---|
| `number` | yes | 1-20 ASCII characters, upper-case (BC stores Code fields upper-case), no leading or trailing spaces, unique in the spec and absent from BC. Grainger SKU on Grainger-filled buys |
| `displayName` | yes | 1-100 ASCII characters, starts with the manufacturer. Hyphens and straight quotes only |
| `displayName2` | no | Up to 50 ASCII characters of overflow (accessories included, size notes) |
| `manufacturer` | yes | The brand the description must start with (`Carr Lane`, `Harrington`, `3M`) |
| `baseUoM` | yes | A unit of measure code that exists in BC. `EA` unless the vendor sells a pack, case or box; then the real code (`PK10`, `CS`, `BX`) |
| `costPer` | yes | What one unit of cost buys. Must equal `baseUoM`; convert before you write the spec |
| `unitCost` | yes | Greater than zero, the vendor's price to BBS before freight and tax. Zero only with `includedWith` |
| `costSource` | yes | Where the cost was read, with a number or date: `<Vendor> quote <number> <date>`, `Grainger MCP acct <buying account> <date>`, `<Distributor> CSP <quote number> <date>`. Any stem of verbal, estimate, approx, roughly, guess, ballpark, phone or "from memory" fails the check, and so does a source with no number or date in it |
| `unitPrice` | no | Sell price when known. Never below cost; equal to cost needs `zeroMarginOk: true`. Leave off for Grainger items priced at quote time |
| `zeroMarginOk` | no | `true` only when the rep accepts selling at cost and has seen that on the sheet |
| `vendorNo` | no | Overrides the top-level vendor for this row (a mixed batch: one vendor's parts plus a Grainger hoist). Upper-case |
| `vendorName` | yes, when the row overrides `vendorNo` | The name for that vendor as it reads on its quote; every distinct vendor in the spec is name-checked against BC. A vendor number with no name anywhere in the spec is an error |
| `vendorItemNo` | no | The vendor's own part number when it differs from `number`, up to 50 characters. Lands in Vendor Item No. on the card |
| `includedWith` | no | Another `number` in this spec whose price covers this accessory. Forces cost 0 and price 0 on this row |

Everything the API cannot take from the spec is fixed: type Inventory, posting groups
PRODUCTS and INVENTORY, tax group TAXABLE. Item category, replenishment, costing method and
the warehouse fields stay at BC defaults, which is how every BBS item is set up.

## Example

Every value below is synthetic. Vendor numbers are resolved by name through the BC
connector when the spec is written (`V#####` stands for whatever BC answers); the account
in a Grainger cost source is the buying institution's own account, read from its folder
name or the buyer's note, never copied from an example.

```json
{
  "vendorNo": "V#####",
  "vendorName": "Example Distributor",
  "preparedBy": "Rep Name",
  "source": "Example Distributor quote Q-000001 (01/02/2026) for Customer PO 000000",
  "items": [
    {
      "number": "EX-1000-A",
      "displayName": "Example Mfr EX-1000-A Swivel Hoist Ring, 1\"-8, 10,000 lb",
      "manufacturer": "Example Mfr",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 100.00,
      "unitPrice": 125.00,
      "vendorItemNo": "EX-1000-A",
      "costSource": "Example Distributor quote Q-000001 01/02/2026"
    },
    {
      "number": "1ABC2",
      "displayName": "Example Mfr LB-010 Lever Chain Hoist, 2,000 lb, 10 ft Lift",
      "manufacturer": "Example Mfr",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 500.00,
      "vendorNo": "V#####",
      "vendorName": "Grainger",
      "costSource": "Grainger MCP acct <buying account> 2026-01-02"
    },
    {
      "number": "EX-CORD-AC",
      "displayName": "Example Mfr AC power cord, 16 AWG",
      "manufacturer": "Example Mfr",
      "baseUoM": "EA",
      "costPer": "EA",
      "unitCost": 0,
      "unitPrice": 0,
      "includedWith": "EX-SWITCH-8P"
    }
  ]
}
```

The second row overrides the vendor, so it carries its own `vendorName`. The third row only
validates if `EX-SWITCH-8P` is also in the spec.

## What the review sheet shows

| # | Item No. | Description | UoM | Vendor | Vendor Item | Cost | Price | GM% | Cost source |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EX-1000-A | Example Mfr EX-1000-A Swivel Hoist Ring, 1"-8, 10,000 lb | EA | V##### Example Distributor | EX-1000-A | 100.00 | 125.00 | 20.0 | Example Distributor quote Q-000001 01/02/2026 |

Above the table the sheet names who prepared it, the source document, the sign-in the
commit would write under (delegated as the rep, or app-only with a flag), where the
connection values came from, and the approval token. The rep reads this sheet, not the
JSON. The token is the one the commit command needs, and it changes whenever the spec file
changes.
