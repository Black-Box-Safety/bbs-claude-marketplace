---
name: bbs-po-status
description: >
  Determine the true received, outstanding, and invoiced status of Black Box
  Safety (BBS) purchase orders to vendors in Business Central. Use this skill
  whenever anyone asks what has been received, shipped, billed, or is still
  outstanding on a BBS vendor PO — including "what are we expecting from
  [vendor]", "how much is outstanding on PO-xxxx", "what's still inbound",
  "open vendor liability", "what has [vendor] shipped us", or any request that
  sums or reports PO receipt status. ALWAYS use this skill for PO receipt
  status. NEVER answer from the PO header `fullyReceived` flag — it is
  systematically unreliable. This skill applies to every vendor (Allstar Fire,
  Grainger, LION, Point Blank, etc.), not just one.
requires: [business-central]
---

# BBS Purchase Order Status — Receipt & Outstanding Logic

## Why this skill exists

Business Central's PO **header `fullyReceived` flag is systematically wrong** in
the BBS environment. It frequently reads `true` when **zero** quantity has
actually been received against the PO. Any report, app, or agent that decides
receipt status from `fullyReceived` will materially **understate open vendor
liability** and overstate what has shipped.

Diagnosed example: PO-10009141 (Allstar) showed `fullyReceived: true` on the
header while every line had `receivedQuantity = 0` and there were **no posted
purchase receipts** against it. The goods had not arrived. Relying on the header
flag understated a single AllStar 6-month outstanding analysis by ~$412K
($112K reported vs. $524K actual).

**Rule: the header `fullyReceived` flag is forbidden as a basis for any
received/outstanding determination. Always compute from line-level fields.**

## The correct field model (per PO line)

| Field (UI label) | API field | Meaning |
|---|---|---|
| Quantity | `quantity` | Total on the original PO (shipped + unshipped) |
| Reserved Quantity | (reserved) | Linked to the sales order; reserves these units to a specific SO. For our purposes this **always matches Qty. to Receive**. |
| Qty. to Receive | (= Reserved Qty) | **Outstanding to ship from the vendor** — not yet received |
| Quantity Received | `receivedQuantity` | Actually received against the PO |
| Qty. to Invoice | `invoiceQuantity` | Received but **not yet invoiced** by the vendor |
| Quantity Invoiced | `invoicedQuantity` | Invoiced / billed by the vendor (i.e., shipped to customer and billed) |

Identity that must hold on each line:
```
quantity = receivedQuantity + (Qty. to Receive / outstanding)
receivedQuantity = invoicedQuantity + invoiceQuantity   (received-but-unbilled vs billed)
```

## Definitions used in reporting

- **Received** = `receivedQuantity` (validate against Posted Purchase Invoices / vendor bills)
- **Outstanding to ship** = Qty. to Receive = `quantity − receivedQuantity` (equals Reserved Quantity for SO-reserved lines)
- **Received but not yet billed** = `invoiceQuantity`
- **Billed / shipped to customer** = `invoicedQuantity`
- **Outstanding value** = Σ (Qty. to Receive × `directUnitCost`) across all lines
- **Received value** = Σ (`receivedQuantity` × `directUnitCost`) across all lines

## Required procedure

Every call goes through the Business Central connector's `bc_query_entity` (read-only).
Text filters are case-sensitive; dates are bare `yyyy-mm-dd`.

1. **Identify the PO set and pull every line in the same call.**

   ```
   entitySet: purchaseOrders
   filter:    vendorNumber eq '<V#####>' and orderDate ge <yyyy-mm-dd>   (or number eq 'PO-########')
   select:    id, number, orderDate, vendorNumber, vendorName
   expand:    purchaseOrderLines($select=description,quantity,directUnitCost,receivedQuantity,invoiceQuantity,invoicedQuantity,amountExcludingTax)
   top:       200   (page with skip while has_more)
   ```

   Use the header only for `number`, `orderDate`, `vendorName`, `vendorNumber` and `id`.
   **Do not select or use `fullyReceived` or `status` for receipt determination.** Do NOT skip
   any PO based on the header: every PO in scope is inspected at the line level.
   `purchaseOrderLines` cannot be queried on its own (Business Central requires the parent
   document); it only comes back through `expand` on `purchaseOrders`.
   To resolve a vendor name to its number, query `vendors` with
   `contains(displayName,'<Name as spelled>')`.

2. **Compute per line:**
   - Outstanding qty = `quantity − receivedQuantity`
   - Outstanding value = Outstanding qty × `directUnitCost`
   - Received value = `receivedQuantity` × `directUnitCost`

3. **Validate "received" when the number matters.** Posted receipts:
   `purchaseReceipts` (filter `orderNumber eq 'PO-########'`, expand `purchaseReceiptLines`).
   Posted vendor bills: `purchaseInvoices` (expand `purchaseInvoiceLines`). Physical receipt
   with cost: `itemLedgerEntries` with `entryType eq 'Purchase' and sourceNumber eq '<V#####>'`.
   If no posted receipt or invoice exists, the goods have not been received, whatever any
   header says. Check a field exists with `bc_describe_entity` before filtering on it; a
   filter on a field the entity does not have fails with a 400, not an empty result.

4. **Roll up** received value, outstanding value, and PO total (Σ `amountExcludingTax`).
   Report all three, and say which entity each number came from.

## Data-quality flags to surface every time

- **$0 unit-cost lines** — a real outstanding order with no pricing entered
  (e.g. AllStar PO-10009846: 3 coats + 3 pants at $0). Flag for pricing or void.
- **Comment / spec lines** carry `quantity = 0` and `directUnitCost = 0` — they
  describe sizing or color and must be **excluded** from totals (they are not
  shippable lines).
- **Shipping / freight lines** are real cost lines and **count** toward value.
- Any PO where header `fullyReceived = true` but line `receivedQuantity = 0` —
  note it; it is the exact failure mode this skill guards against.

## Do NOT

- Do **not** use `fullyReceived` (header) for anything receipt-related.
- Do **not** assume "Open" or "Released" status means received.
- Do **not** infer receipt from the presence of a sales order or reservation —
  reservation is a commitment, not a receipt.
- Do **not** sum comment/spec lines into value totals.

## Tools (Business Central connector, read-only)

- `bc_query_entity` on `purchaseOrders` with `expand=purchaseOrderLines`: headers and lines (the lines are the source of truth)
- `bc_query_entity` on `purchaseReceipts` / `purchaseInvoices` (with their line expands): posted receipts and vendor bills, for validation
- `bc_query_entity` on `itemLedgerEntries`: physical receipt ground truth with cost
- `bc_describe_entity`: field names and one sample record, before filtering on an unfamiliar field
