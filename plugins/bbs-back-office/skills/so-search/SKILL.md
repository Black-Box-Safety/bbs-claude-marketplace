---
name: so-search
description: Looks up a Black Box Safety Sales Order (SO) by customer PO number using the BBS Business Central MCP. Searches Posted Sales Invoices by customerPurchaseOrderReference. Returns a summary of all invoices tied to that PO and their associated SO number. If no invoices are found (PO not yet invoiced), prompts Aanya for agency name, approximate dollar value, and date range, then searches open Sales Orders and returns the best match with a BC deep link. Trigger immediately whenever Aanya types "SOSearch [PO#]", "/SOSearch [PO#]", "SO search [PO#]", "look up PO [PO#]", "find SO for PO [PO#]", or any similar request to locate a Sales Order by a customer PO number. Always use this skill for that request — never attempt to search BC manually without it.
---

# SOSearch Skill

Looks up a BBS Sales Order by customer PO number via the BC MCP. Searches `ListSalesInvoices` by `customerPurchaseOrderReference` and returns the linked SO and invoice summary. If nothing is found (not yet invoiced), prompts for agency name, dollar value, and date range, then searches open Sales Orders and returns the best match with a BC deep link.

## Trigger

Aanya invokes this with:
- `SOSearch [PO#]`
- `/SOSearch [PO#]`
- `SO search [PO#]`
- `find SO for PO [PO#]`
- `look up PO [PO#]`
- Any request to locate a Sales Order using a customer PO number

The PO number is always the argument following the command. Extract it exactly as given — preserve dashes, leading zeros, and any other formatting (e.g. `4440-0000061136`, `1701-0000005128`).

## Steps

### 1. Load the BC MCP tool

Call `tool_search` with query `"ListSalesInvoices customerPurchaseOrderReference"` to load the `bc-mcp-proxy:ListSalesInvoices_PAG30012` tool. Do this silently — do not narrate it to Aanya.

### 2. Search by PO number

Call `bc-mcp-proxy:ListSalesInvoices_PAG30012` with:

```
filter: customerPurchaseOrderReference eq '[PO#]'
select: number, customerName, customerPurchaseOrderReference, orderNumber, invoiceDate, totalAmountIncludingTax, status, remainingAmount
```

Use `eq` (exact match), not `contains`, since PO numbers are always exact.

### 3a. Results found — format the response

If one or more invoices are returned, output:

---

**SO Found:** [`[orderNumber]`](https://businesscentral.dynamics.com/fea7ae2d-abd8-495f-8001-60dab26c261f/Production?company=Black%20Box%20Safety&page=42&filter='No.'%20IS%20'[orderNumber]')
**Customer:** `[customerName]`
**PO #:** `[customerPurchaseOrderReference]`

The SO Found line must be a clickable markdown hyperlink. Construct it by substituting the actual `orderNumber` value (e.g. `SO-10010115`) into both the display text and the filter parameter of the URL. The URL template is:
`https://businesscental.dynamics.com/fea7ae2d-abd8-495f-8001-60dab26c261f/Production?company=Black%20Box%20Safety&page=42&filter='No.'%20IS%20'[orderNumber]'`

| Invoice # | Invoice Date | Amount | Status |
|---|---|---|---|
| INVP-XXXXXXX | MM/DD/YYYY | $X,XXX.XX | Paid / Open / Canceled |
| ... | | | |

**Total Invoiced:** $X,XXX.XX *(sum of all non-canceled invoice amounts)*

---

Rules:
- If multiple invoices share the same `orderNumber` (common — one SO ships in multiple invoices), group them under that single SO.
- If invoices reference *different* `orderNumber` values (rare — same PO used across multiple SOs), display each SO as a separate group.
- Format `invoiceDate` as MM/DD/YYYY.
- Format dollar amounts with commas and two decimal places.
- Include all statuses (Paid, Open, Canceled) in the table — don't filter any out.
- Do NOT sum Canceled invoices into the Total Invoiced figure.

### 3b. No results — collect criteria and search Sales Orders

If the API returns an empty `value` array, respond with:

> **PO has not been invoiced. Please provide additional search criteria.**

Then ask Aanya for all three of the following in a single message:
1. **Agency name** (e.g. "DSH Metro", "Mule Creek", "ARB")
2. **Approximate dollar value** (e.g. "~$28k", "$15,000")
3. **Rough month or month range the SO was created** (e.g. "June 2026", "May–June 2026")

Once Aanya provides all three, proceed to **Step 4**.

---

### Step 4. Search Sales Orders by agency + amount + date

**4a. Load the Sales Orders tool**

Call `tool_search` with query `"List_SalesOrders_PAG30028 number customerName orderDate totalAmountExcludingTax"` to load `bc-mcp-proxy:List_SalesOrders_PAG30028`. Do this silently.

**4b. Build the filter**

- Agency: use `contains(tolower(customerName),'[lowercase keyword]')` — use the shortest reliable keyword (e.g. "metro", "mule creek", "atascadero")
- Date range: convert the month/range to `orderDate ge YYYY-MM-01 and orderDate le YYYY-MM-30` (use last day of the final month)
- Amount: set `totalAmountExcludingTax ge [lower bound]` where lower bound = stated amount × 0.7 (to allow for ~30% variance either direction)

Select fields: `number, customerName, orderDate, totalAmountExcludingTax, totalAmountIncludingTax, status, externalDocumentNumber`

**4c. Rank and present results**

Sort results by closeness to the stated dollar value. Present the **single best match** first:

---

**Best match:**
**SO:** [SO-XXXXXXX](https://businesscentral.dynamics.com/fea7ae2d-abd8-495f-8001-60dab26c261f/Production?company=Black%20Box%20Safety&page=42&filter='No.'%20IS%20'[SO#]')
**Customer:** [customerName]
**Order Date:** MM/DD/YYYY
**Pre-tax Total:** $XX,XXX.XX
**Customer PO:** [externalDocumentNumber or "—"]

---

Then say: *"If that is not the correct Sales Order, please review the following:"* and list up to **2 additional options** in the same format — only if you judge them to be plausible alternatives (similar amount or same agency in the date window). Do not pad with obviously wrong results.

If only one result exists, skip the additional options entirely.

**Deep link URL template:**
`https://businesscentral.dynamics.com/fea7ae2d-abd8-495f-8001-60dab26c261f/Production?company=Black%20Box%20Safety&page=42&filter='No.'%20IS%20'[SO#]'`

## Error handling

- If the BC MCP tool call fails or throws an error, tell Aanya: "BC MCP returned an error — you may need to reconnect the connector and try again."
- If the PO number was not clearly provided, ask: "Please provide the PO number you'd like to search."
- Never fabricate SO numbers or invoice data.
