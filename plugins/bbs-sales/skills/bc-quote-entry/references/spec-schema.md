# Quote entry spec

One JSON file per quote. Save it beside the deal in the customer's folder as
`BC-import/quote-<yyyy-mm-dd>.json`. The check writes `<spec>.review.md` next to it and the
commit appends `<spec>.bc-log.jsonl`. Every line's item number must already exist in
Business Central; this spec never creates or changes an item (`bc-item-entry` does that,
first).

## Top level

| Field | Required | Meaning |
|---|---|---|
| `customerNumber` | yes | The BC customer number (`C#####`, upper-case). Resolved by number, never by name (BC's text search is case-sensitive). The customer must exist and not be blocked |
| `externalDocumentNumber` | yes | 1-35 ASCII characters: the agency's solicitation or RFQ number, or the customer's PO number. The check stops if any sales quote in BC already carries it |
| `contract` | yes | The CONTRACT dimension (shortcut dimension 1): the vehicle Gate 1 of `/ca-rfq` named. One of the codes in `quote-rules.md`; anything else stops. `OPEN` for open market, `NASPO` for the Grainger NASPO schedule |
| `book` | yes | Whose rules apply: `ca-state` (Kim Quezon's and Aanya Samarasinghe's agencies), `body-armor` (Parker's; needs a body-armor CONTRACT), `higher-ed` (CSU and UC, Joey Magliato's), `other` (federal, local, private; outside the state book). Body armor on `ca-state` and CSU/UC on `ca-state` both stop |
| `agency` | yes on `ca-state` and `higher-ed` | The state agency the customer belongs to, by its short name or a common spelling (`CAL FIRE`, `CalFire`, `CDCR`, `DSH`, `Caltrans`, `State Water Board`). It decides the owner: one of Kim's 18 agencies means `KQUEZON`, any other state agency means `AANYA`. The check also reads the customer card's CUSTOMER dimension and stops when it names the other owner |
| `salesperson` | yes | The BC salesperson code of the Account Manager who owns the agency: `KQUEZON` or `AANYA` on a state quote, `JMAGLIATO` or `UNIVERSITY` on higher education. Never `PMARSHALL` on a state quote (Parker holds no accounts there) and never `CA STATE TEAM` on any new quote, even where the customer card still defaults to it: the check stops on both. The read-back gate compares it with the header BC wrote |
| `shipTo` | yes | The delivery point, below. PATCHed onto the header after the POST and gated by read-back before any line is added |
| `costSource` | yes | Where every line's cost was read, with a number or date: the vendor quote number and date, or the Grainger account and date the price was read. The same guess-words that fail `bc-item-entry` fail here |
| `pricingBasis` | yes | How the sell price was reached, in a sentence a rep can defend: margin over cost, freight folded in, the schedule rule (Grainger at cost on NASPO). Printed on the review sheet |
| `lines` | yes | One object per quote line, below. At least one |
| `quoteTotalExclTax` | yes | Sum of `qty x unitPrice` across the lines, to the cent. The check stops if the lines do not add up to it; the commit stops if BC's total differs from it |
| `preparedBy` | yes | The rep's name; printed on the sheet and matched against `--approved-by` on commit |
| `zeroMarginOk` | no | `true` when every line sells at cost by design (the NASPO schedule: the Grainger price is the customer price). Otherwise put it on the lines that need it |
| `deal` | no | One line naming the deal, for the sheet and the log |
| `approvedBy` | no | Free text for the rep's own record. The script does not read it: approval is the `--approve <token> --approved-by "<name>"` pair on the commit. Editing it after the check changes the token like any other edit |

## `shipTo`

Exactly the header fields the sales quote API exposes, nothing else; an unknown key stops
the check because BC would reject or ignore the PATCH. All ASCII.

| Field | Required |
|---|---|
| `shipToName` | yes |
| `shipToContact` | no |
| `shipToAddressLine1` | yes |
| `shipToAddressLine2` | no (may be `""`) |
| `shipToCity` | yes |
| `shipToState` | yes, the two-letter code |
| `shipToPostCode` | yes |
| `shipToCountry` | no; `US` when given |

## Per line

| Field | Required | Rule |
|---|---|---|
| `line` | yes | Positive integer, unique in the spec. Becomes the BC line `sequence` as `line x 10000` |
| `number` | yes | The BC item number, upper-case, as the card has it. Must exist in BC as type Inventory and not be blocked; a missing number stops with "enter it through bc-item-entry" |
| `description` | yes | 1-100 ASCII characters. The line text the customer sees; it overrides the card's description on this quote only (non-persistent) and is where the customer's tag or PO line number goes. Hyphens and straight quotes only |
| `qty` | yes | Greater than zero |
| `uom` | yes | A unit of measure code that exists in BC, usually `EA` |
| `unitCost` | yes | Greater than zero: BBS's cost for one unit from `costSource`. Not written to BC; it is the basis the sheet's GM% and the price gate use. Shown beside the card's cost when the two differ |
| `unitPrice` | yes | Greater than zero, never below `unitCost`. Equal to `unitCost` only with `zeroMarginOk` on the line or the spec. A zero stops: by SOP a zero price means nobody priced the line |
| `zeroMarginOk` | no | `true` when this line sells at cost and the rep has seen that on the sheet |

Everything else on the header is fixed or inherited: `documentDate` is the day of the commit,
`validUntilDate` is never sent (BC computes document date + 60), the CUSTOMER dimension and
the payment terms and shipment method inherit from the customer card, and every line is
`lineType: Item` at the `DROPSHIP` location. Tax is calculated when a person releases the
quote in BC; this spec carries no tax.

## Example

Every value below is synthetic.

```json
{
  "deal": "Example Agency - 30 EA Example Mfr EX-6001 covers - RFQ email 2026-01-02",
  "customerNumber": "C00000",
  "externalDocumentNumber": "RFQ EX-6001 01-02-26",
  "contract": "OPEN",
  "book": "ca-state",
  "agency": "DGS",
  "salesperson": "AANYA",
  "shipTo": {
    "shipToName": "Example Agency Training Center",
    "shipToContact": "Buyer Name",
    "shipToAddressLine1": "100 Example Road",
    "shipToAddressLine2": "",
    "shipToCity": "Sacramento",
    "shipToState": "CA",
    "shipToPostCode": "95814",
    "shipToCountry": "US"
  },
  "costSource": "Example Distributor quote Q-000001 dated 01/02/2026: 30 EA EX-6001 @ 89.50, freight 45.00",
  "pricingBasis": "5.0% over cost with the 45.00 freight folded into the unit price: (89.50 x 1.05 -> 94.00) + (45.00 / 30 = 1.50) = 95.50",
  "lines": [
    {
      "line": 1,
      "number": "EX-6001",
      "description": "Example Mfr EX-6001 Aluminized Helmet Cover - special order, freight incl.",
      "qty": 30,
      "uom": "EA",
      "unitCost": 89.50,
      "unitPrice": 95.50
    }
  ],
  "quoteTotalExclTax": 2865.00,
  "preparedBy": "Rep Name"
}
```

A NASPO spec differs in three places: `"contract": "NASPO"`, every line's `unitPrice` equal
to its `unitCost` (the Grainger price read on the buying institution's own account), and
`"zeroMarginOk": true` at the top level with `pricingBasis` saying so. A CAL FIRE or CDCR
spec differs in one: `"agency": "CAL FIRE"` makes the salesperson `KQUEZON`, and the check
stops on anything else.

## What the review sheet shows

A header table (customer number and BC name, the card's payment terms and shipment method,
external document number, CONTRACT, book and owner (`CA state / CAL FIRE -> Kim Quezon
(KQUEZON)`), salesperson, ship-to, document date, cost source,
pricing basis, who prepared it, the sign-in that would write, where the connection values
came from, the approval token), then one row per line:

| # | Item No. | Description | Qty | UoM | Cost | Price | Ext. price | GM% | Card |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EX-6001 | Example Mfr EX-6001 Aluminized Helmet Cover - special order, freight incl. | 30 | EA | 89.50 | 95.50 | 2,865.00 | 6.3 | cost 89.50, price 0.00 |

and the total excluding tax. The rep reads this sheet, not the JSON. The token is the one
the commit command needs, and it changes whenever the spec file changes.
