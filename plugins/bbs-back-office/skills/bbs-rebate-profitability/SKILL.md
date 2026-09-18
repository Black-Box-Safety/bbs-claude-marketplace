---
name: bbs-rebate-profitability
description: "Analyze Black Box Safety's true profitability by applying downstream Grainger rebates based on contract code dimensions from Business Central. Use this skill whenever a user asks about BBS profit, margin, P&L, profitability, rebate income, Grainger rebate, contract code margin, adjusted margin, true margin, NASPO margin, OMNIA margin, or any analysis that requires understanding BBS's actual gross profit after accounting for Grainger rebates. Also trigger when users ask about customer profitability, revenue by contract code, or want to understand which accounts or contract vehicles are most/least profitable. This skill is essential because Business Central's item ledger entries show COGS at Grainger list — the real margin only appears after layering in rebate percentages tied to each invoice's contract code dimension."
requires: [cdata-connect]
---

# BBS Rebate Profitability Analysis

## Why this skill exists

Black Box Safety resells Grainger products to government agencies under cooperative contracts. Grainger pays BBS a downstream rebate based on the contract vehicle used on each sale. Business Central records revenue and COGS at the Grainger catalog price, so the item ledger shows near-zero or zero margin on many accounts. The actual profit comes from the rebate, which is a percentage of COGS returned to BBS after the fact. Without adjusting for rebates, the P&L is misleading — large accounts appear unprofitable when they're actually earning 8-10% margin.

## Rebate structure

| Contract code (shortcutDimension1Code) | Rebate rate | Applies to |
|----------------------------------------|------------|------------|
| NASPO | 8% of COGS | California state agencies on the MRO statewide contract (LPA #7-25-52-02.03) |
| OMNIA | 10% of COGS | CSU campuses on the Omnia cooperative contract |
| UCOP | 10% of COGS | UC campuses on the UC Office of the President contract |
| BA-CA | 0% | Body armor — California state contract. Margin is built into unit price, no Grainger rebate. |
| BA-SRCWL | 0% | Body armor — Sourcewell national contract. Margin is built into unit price. |
| BODYARMOR | 0% | Body armor — general/Shopify. Margin in unit price. |
| OPEN | 0% | Open market / no cooperative contract. No rebate. |
| DODIG | 0% | DOD Inspector General. No rebate. |
| ICPT | 0% | Intercompany / pass-through. No rebate. |
| EMRKT | 0% | E-marketplace. No rebate. |
| QB LEGACY | 0% | Legacy QuickBooks data. No rebate. |

Only NASPO, OMNIA, and UCOP earn Grainger rebates. All other contract codes have margin built into the sale price or are non-rebate channels.

## Data sources in Business Central

All queries use catalog `Dynamics365BusinessCentral1` and schema `Black Box Safety` via CData Connect AI.

### Primary tables

1. **salesInvoices** — Invoice headers with contract code dimension and customer info
   - `shortcutDimension1Code` → contract code (NASPO, OMNIA, UCOP, BA-CA, OPEN, etc.)
   - `shortcutDimension2Code` → customer segment (AGNCY, CSU, UC, CHP, DSH, DOD, MUNC, etc.)
   - `customerNumber`, `customerName` → customer identity
   - `postingDate` → date filter
   - `status` → "Paid", "Open", or "Canceled"
   - `totalAmountExcludingTax` → invoice revenue (pre-tax)
   - `number` → invoice number (e.g., INVP-10009810)

2. **itemLedgerEntries** — Item-level cost and revenue actuals
   - `costAmountActual` → COGS (negative for sales, positive for returns)
   - `salesAmountActual` → revenue (positive for sales, negative for returns)
   - `sourceNumber` → customer number
   - `entryType` → filter to "Sale"
   - `postingDate` → date filter
   - `documentNumber` → links to invoice number

3. **customers** — Customer master
   - `number` → customer number
   - `displayName` → full customer name

### Critical: always filter out cancelled invoices

Always include `[status] <> 'Canceled'` when querying salesInvoices. Cancelled invoices remain in BC and will inflate revenue if not excluded. This was a real issue — a single $404K cancelled DSH-Napa invoice distorted an entire month's P&L.

### Cross-table join limitation

The CData Connect AI connector cannot reliably JOIN across BC API tables. Use a proportional allocation approach instead:

1. Query **salesInvoices** for revenue by customer + contract code (filtering out cancelled)
2. Query **itemLedgerEntries** for total COGS by customer (entryType = 'Sale')
3. For each customer, calculate the proportion of revenue on each contract code
4. Allocate the customer's total COGS proportionally across contract codes
5. Apply the rebate rate to the allocated COGS for each contract code

This is necessary because the contract code lives on the invoice header, but the precise line-level COGS lives in the item ledger entries, and we can't join them directly.

## Analysis workflow

### Step 1: Get clean revenue by customer and contract code

```sql
SELECT [customerNumber], [customerName], [shortcutDimension1Code],
       SUM([totalAmountExcludingTax]) AS revenue, COUNT(*) AS invCount
FROM [Dynamics365BusinessCentral1].[Black Box Safety].[salesInvoices]
WHERE [postingDate] >= @startDate AND [postingDate] <= @endDate
  AND [status] <> 'Canceled'
GROUP BY [customerNumber], [customerName], [shortcutDimension1Code]
ORDER BY revenue DESC
```

Use parameterized dates: `@startDate` and `@endDate` with type DATE.

### Step 2: Get COGS by customer from item ledger entries

```sql
SELECT [sourceNumber],
       SUM([salesAmountActual]) AS totalRevenue,
       SUM([costAmountActual]) AS totalCost
FROM [Dynamics365BusinessCentral1].[Black Box Safety].[itemLedgerEntries]
WHERE [postingDate] >= @startDate AND [postingDate] <= @endDate
  AND [entryType] = 'Sale'
GROUP BY [sourceNumber]
ORDER BY totalRevenue DESC
```

Note: costAmountActual is negative for sales (outflow). Use absolute value for calculations.

### Step 3: Allocate COGS and compute adjusted profit

For each customer:
1. Sum their total non-cancelled invoice revenue across all contract codes
2. For each contract code, compute: `proportion = code_revenue / total_customer_revenue`
3. Allocate: `allocated_COGS = abs(total_ILE_cost) × proportion`
4. BC profit: `revenue - allocated_COGS`
5. Rebate: `allocated_COGS × rebate_rate` (only for NASPO/OMNIA/UCOP)
6. Adjusted profit: `BC_profit + rebate`
7. Adjusted margin: `adjusted_profit / revenue × 100`

### Step 4: Present results

Present findings in three views:

1. **Summary metrics** — Total revenue, BC gross profit, estimated rebate income, adjusted gross profit, BC margin %, adjusted margin %, margin lift from rebates
2. **By contract code** — Revenue, profit, and rebate impact rolled up by contract vehicle
3. **By customer** — Sorted by adjusted profit, with contract code, rebate rate, and adjusted margin. Color-code margins: red (<5%), amber (5-15%), green (>15%)

### Output format

Produce an Excel workbook with three tabs when the user wants a downloadable deliverable:
- Tab 1: Detail by customer + contract code (filterable)
- Tab 2: Summary by contract code
- Tab 3: Customer summary (one row per customer, all codes consolidated)

For inline conversation, use the visualizer to render interactive charts with metric cards and a scrollable table.

## Interpretation guidance

When presenting results, provide these insights:

- **NASPO and OMNIA accounts showing 0% BC margin are performing as designed.** The rebate IS the margin. Flag this proactively so users don't misinterpret the raw BC data.
- **Body armor contract codes (BA-CA, BA-SRCWL, BODYARMOR) carry margin in the unit price.** No rebate adjustment needed — the BC profit is the real profit.
- **OPEN contract code lines earn no rebate.** These are the ones worth scrutinizing for pricing improvement.
- **Split-coded customers matter.** A single customer may have invoices on NASPO (earns rebate), BA-CA (margin in price), and OPEN (no rebate). The adjusted P&L must account for this mix.
- **Cancelled invoices can massively distort results.** Always verify they're excluded.

## Edge cases

- If a customer appears in the invoice data but not in item ledger entries, their COGS may not have posted yet. Note this in the output.
- Negative revenue rows indicate credit memos or returns. Include them in the analysis but flag them separately.
- The ILE `salesAmountActual` and invoice `totalAmountExcludingTax` will not perfectly match due to timing, rounding, and credit memos processed separately. Note this discrepancy if it exceeds 5%.
- Shopify orders should be consolidated into a single "Shopify" row for readability since they're individual consumer purchases.
