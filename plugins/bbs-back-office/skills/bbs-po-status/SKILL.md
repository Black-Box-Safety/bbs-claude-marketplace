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

1. **Identify the PO set.** Pull PO headers for the vendor / date window via
   `ListPurchaseOrders_PAG30066`. Use these only for `number`, `orderDate`,
   `vendorName`, `vendorNumber`, and `id`. **Ignore `fullyReceived` and `status`
   for receipt determination.** Do NOT skip any PO based on the header flag —
   every PO in scope must be inspected at the line level.

2. **Pull lines for EVERY PO** via `ListPurchaseOrderLines_PAG30067` (parent
   `PurchaseOrder_id` = header `id`). Select:
   `description, quantity, directUnitCost, receivedQuantity, invoiceQuantity, invoicedQuantity, amountExcludingTax`.

3. **Compute per line:**
   - Outstanding qty = `quantity − receivedQuantity`
   - Outstanding value = Outstanding qty × `directUnitCost`
   - Received value = `receivedQuantity` × `directUnitCost`

4. **Validate "received" against Posted Purchase Invoices** (vendor bills) when
   the number matters: `ListPurchaseInvoices_PAG30042` →
   `ListPurchaseInvoiceLines_PAG30047`, and/or confirm posted receipts via
   `ListPurchaseReceipts_PAG30064`. If no posted receipt/invoice exists, the
   goods have not been received regardless of any header flag.

5. **Roll up** received value, outstanding value, and PO total (Σ
   `amountExcludingTax`). Report all three.

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

## Tools (Cloud BBS BC MCP / bc-mcp-proxy)

- `ListPurchaseOrders_PAG30066` — PO headers
- `ListPurchaseOrderLines_PAG30067` — PO lines (the source of truth)
- `ListPurchaseReceipts_PAG30064` / `ListPurchaseReceiptLines_PAG30065` — posted receipts
- `ListPurchaseInvoices_PAG30042` / `ListPurchaseInvoiceLines_PAG30047` — posted vendor bills (validation)
- `ListItemLedgerEntries_PAG30069` — `entryType eq 'Purchase'`, `sourceNumber eq '<vendorNo>'` for physical receipt ground-truth with cost
