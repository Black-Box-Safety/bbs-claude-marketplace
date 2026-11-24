---
description: Run a quote request for any customer that is not a California state agency — federal, a prime, local government, a utility or a commercial account — under one order. Files it, extracts the lines, prices, builds the Business Central quote, and stops at the rep. For a California state request use /ca-rfq.
---

# /rfq

One request, one running order, for a customer outside the California state desk. It is the
same practice `/ca-rfq` runs, without the California state form packet and its
certification wording.

**This file carries order and gates.** Each step names the skill that owns it; invoke that
skill and follow its body. It restates no price rule, certification, signer or form. Those
live in the customer's own `CLAUDE.md`, the channel file above it, and the skills.

**A gate that cannot be met stops the run and goes to the rep.** It is never guessed past.

## Gate 0 — Is this the right command

- **A State of California agency,** or a folder under `State of CA Agencies/` → stop, and run
  `/ca-rfq`. The state rules are different and they bind.
- **Body armor, or a CSU or UC campus** → stop and tell the rep whose book it is. This command
  does not run those.
- **More than a quote is owed** (a proposal, a sources-sought response, a solicitation with
  volumes, or nothing to price yet) → it is a pursuit, not a request. Say so; the notes go in
  the pursuit folder's `PURSUIT.md`. Price only the part that is a priced request.
- **A request under a contract BBS already holds** (a BPA call, a task order) → continue, and
  read that contract folder's `CONTRACT.md` first.
- **A folder inside another quote desk** (Bechtel Sentinel today, or any folder whose own
  `CLAUDE.md` describes its record, quote log or workbook) → that desk's file governs. Follow
  its record and ledger rules at every gate below; where it and this command differ, it wins.

## Gate 1 — The customer, the channel, the folder

1. Name the customer and find its folder under `Customers/`. Search by customer, by buyer and
   by item before creating anything.
2. Read the customer's `CLAUDE.md` and the channel file above it. **The channel decides the
   certification wording, the price rule and the paperwork.** If neither file states the
   channel, ask the rep. Never infer it from the folder name.
3. Find or create the deal folder, named the way that customer's folder already names them.
   Save the request and every attachment as received.

**Gates.** The channel is stated by a file or by the rep. A customer folder with no
`CLAUDE.md` gets the offer the foundations hook describes, and the run continues either way.
No outcome file is created by hand: outside a desk, the Business Central quote is the record.

## Gate 2 — Extract the lines

`rfq-item-extract`, unless the rep handed over a clean list.

**Gate.** The line count carried forward equals the line count the request asks for.
Quantities and units are the buyer's, carried exactly.

## Gate 3 — Open the working workbook, and read the earlier ones

`rfq-workbook`. Create this request's workbook from the extracted lines. It is internal and
it is where every cost, source, price and pricing note is written from here on.

Then precedent: the earlier workbooks in this customer's deal folders (the price, how it was
set, the outcome and the lesson), then Business Central (`bc_customer_snapshot`,
`bc_get_sales_document`). Cite what is found, with its date.

**Gate.** The workbook exists and has one row per line of Gate 2.

## Gate 4 — Price

| The line | Skill |
|---|---|
| Grainger carries it | `grainger-pricing` |
| Competitive, or Grainger does not carry it | `bbs-sourcing` |
| One vendor, one ask | `vendor-quote-email` |

`bbs-sourcing` was written for California state bids. Here, use it to find suppliers and
draft the asks only. Its California procurement methods and DVBE wording do not apply to
this request; certification wording comes from the channel file, never from that skill.

**Gates.**

- Every unit price has a source and a date beside it. No source, no price: `[FLAG: why]`.
- **The Grainger account is the one the customer's `CLAUDE.md` names.** If none is named,
  stop that line and ask the rep; the wrong account returns a wrong price that looks valid.
- **Every cost and every price is in the workbook as it is found,** the cost with its source
  and the price with a note saying how it was set. `rfq-workbook` refuses either without it.
- **Whether a Grainger line may carry markup is decided in one place:** the "Grainger sell
  rule, by channel" table in bbs-foundations' `canonical-facts.md`. Read the row for this
  request's channel and vehicle and apply it as written. Where that table says a channel is
  open, the line is `[FLAG: sell rule for <channel> is open for Parker]` and goes to the rep;
  no rule is inferred from another row. An order on a California schedule is that table's
  California row whoever the buyer is.
- Show cost, sell and margin to the rep; none of the three goes on anything the customer
  sees except the sell price.

## Gate 5 — Build the quote in Business Central

`bc-item-entry` for any item not yet in Business Central, then `bc-quote-entry`. Both act
only after the rep approves the review sheet by name.

**Gates.** `rfq-workbook`'s `show` reports no gaps: every line is priced or marked No bid.
The quote's lines and prices are the workbook's. The quote number is the one Business Central assigned, read back. Customer
number, salesperson and contract code come from the customer's `CLAUDE.md` or from the rep,
never from the California defaults. A person releases, prints and sends from Business
Central.

## Gate 6 — The buyer's paperwork

Use the forms the buyer sent with the request, and only those. Never the California packet.
Fill what a file supports; a certification, a country of origin or a signer that no file
supports is `[FLAG: why]` and goes to the rep.

## Gate 7 — Deliver to the rep, and stop

State what is ready for review, what is still open, and where each file is. Give the rep
the workbook's totals: cost, sell and margin. **The run ends
with a person.** This command has no send step.

**When the outcome is known,** close the workbook: the outcome and, in the rep's words, why
and what to do differently next time.

If the rep says something worth keeping about this customer, and `desk-remember` does not
cover this folder, say so and offer the edit to the customer's `CLAUDE.md` instead.
