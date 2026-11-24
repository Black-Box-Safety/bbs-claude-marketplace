---
name: rfq-workbook
description: >-
  Create and keep the internal working Excel workbook for one quote request at Black Box
  Safety: one row per line with the offered manufacturer and SKU, the source and an
  alternative, unit cost with where it came from, unit price, margin, and a note saying how
  the sell price was set. Use it when /rfq or /ca-rfq reaches the workbook step, or when a
  rep says "start the working workbook", "open the working sheet for this RFQ", "add the
  vendor's cost to the workbook", "what is still unpriced in the workbook" or "show me the
  margin on this RFQ". Do NOT use it to find suppliers or ask vendors for prices (bbs-sourcing). Do NOT use it to build the customer's quote (bc-quote-entry; the
  Business Central print is the customer document), to look up a price (grainger-pricing,
  bbs-sourcing), or to make anything a customer will see: the workbook holds cost and margin
  and never leaves the building.
requires: [python3, openpyxl]
---

# RFQ working workbook

One workbook per request, in the deal folder, edited in place from the first line to the
outcome. It is where the numbers are worked. It is not the quote: the customer's quote is
built in Business Central, and on a quote desk the outcome stays in the desk's own ledger.

This is the Bechtel Sentinel desk's sourcing workbook, made the same for every customer.
What Sentinel learned is built in: every cost cites its record, a substitute is named as
one, a price says how it was set, and the file closes with the outcome and the lesson so the
next request for that customer starts from it.

**It is internal.** It holds cost, supplier names and margin. Never attach it, paste from it
into a customer email, or copy its notes onto a Business Central quote line.

## Where it lives

In the deal folder, named `INTERNAL - <deal folder name> - working.xlsx`. Where the deal
folder already has an `internal/` subfolder, put it there. One per request; never a second
copy with a date on the end.

## The script

Run it through the plugin's launcher, which needs no Allow click (Parker, 2026-11-24):

```
"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/rfq-workbook/scripts/rfq_workbook.py" create --out "<deal folder>/INTERNAL - <deal folder name> - working.xlsx" --lines-json "<lines file>" --header "Customer=<name>"
"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/rfq-workbook/scripts/rfq_workbook.py" set --file "<workbook>" --line <n> --field "cost=<number>" --field "source_ref=<where it came from>"
"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/rfq-workbook/scripts/rfq_workbook.py" show --file "<workbook>"
```

| Command | Does |
|---|---|
| `create` | Writes the workbook. Refuses if the file exists |
| `set` | Sets fields on one line; adds the line if it is new |
| `show` | Prints every line as JSON with extended cost, extended price and margin computed, a `gaps` list per line, and totals |

Add `--help` after `create` or `set` for the header fields and the line field keys; they are
defined once, in the script. If the script says the file is open in Excel or locked, ask the
rep to close it and run it again. `set` and `show` work only on a workbook this script
made; any other spreadsheet is refused and left unchanged. Do not write the workbook any
other way: a hand-built sheet drifts from the columns every other request uses.

## The steps

1. **Open it once the lines are known.** Build the lines list from the extraction, with the
   buyer's quantities, units and wording carried exactly, and run `create`. Fill the header
   from the request and the customer's `CLAUDE.md`; leave unknown fields empty.
2. **Record each cost as it arrives,** with `set`. A cost is refused without `source_ref`:
   the Grainger account and the read date, the vendor's quote number and date, or a listing
   URL and date. Where there is a second source, record it in the `alt_` fields; an
   alternative cost is refused without `alt_ref`. `create` applies the same refusals to the
   lines it is given.
3. **Name what is offered.** `match` is one of Exact, Equal, Substitute, No bid. A
   substitute carries the offered manufacturer and part number and the difference in `notes`.
4. **Record the price with its reason.** A price is refused without `pricing_notes`. Write
   the rule in plain words: "NASPO at cost", "cost plus 12%, the band this buyer has
   accepted twice", "matched the public price on SCPRS PO 4500764412, read 2026-11-24". Put
   the comparisons themselves on the Comps sheet and the band on the header's margin basis.
   **This skill does not decide a price.** The sell rule belongs to the channel and the
   skills that own pricing; this is where the decision is written down.
5. **Before the quote is built, run `show`.** Every line must be priced or marked No bid, and
   `gaps` must be empty. Give the rep the totals and the lines with gaps. A line with a gap
   does not go on the Business Central quote.
6. **Read it back, do not trust the cells.** `show` recomputes extended cost, extended price
   and margin from quantity, cost and price. A workbook a script wrote has no stored formula
   results until Excel opens it, so reading the formula cells yourself returns blanks.
7. **Close it.** When the outcome is known, fill the header's outcome and "why, and what to do
   differently next time" in the rep's words. On a quote desk, the outcome also goes where
   that desk records it; the workbook line is the lesson, not a second ledger.

## Before pricing the next request

Open the earlier workbooks in this customer's deal folders and read three things from each:
the price and its pricing note, the outcome, and the lesson. That is the precedent the next
price starts from.

## What it never does

- Sets or suggests a certification, a signer or a form.
- Sends, attaches or publishes anything.
- Replaces `RFQ.md` on a quote desk or the Business Central quote anywhere.
