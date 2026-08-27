---
description: Log an inbound California state quote request into the customer folder tree — find or create the folder, save the attachments, open the RFQ record, update the buyer's quote log. Stops before pricing.
---

# /ca-rfq-log

A request just came in from a state buyer. Get it filed and get its clock visible. Run the `ca-rfq-intake` skill and follow it; the steps below are the shape of the run.

1. **Read the request.** Whatever the rep has — the email, the attachments, a bare item list, a portal link. Pull out the buyer, the institution, the items, and anything that names a deadline. If the rep pasted only a summary, ask for the original before filing anything, because the worksheet header carries the solicitation number and the email carries the due date.

2. **Find the folder before creating one.** The tree is `Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`. Check `references/agency-tree.md`, then search the tree by buyer name and by item. Reuse the agency and buyer folders that exist; the same agency shows up under several spellings. Only the deal folder should be new. A duplicate buyer folder hides the last quote's precedent from the next one, which is why this step comes before any writing.

3. **Save the attachments as received.** Every one, unrenamed: the RFQ or worksheet, the blank certs, the spec sheets, the buyer's email itself. If they sent only an email body with an item list, save it as `request-email.txt`. Completeness beats tidiness — the spec sheet you skipped is the substitution argument you can't make later.

4. **Open the run record.** Create `RFQ.md` in the deal folder from `references/rfq-record-template.md`. Fill what the documents actually say. A field the documents don't answer gets `[FLAG: why]`, never a guess. Get the due date, solicitation number, vehicle, Grainger account, required forms, and ship-to right — those six decide everything downstream. Read the buyer's `CLAUDE.md` one folder up while you fill it in.

5. **Classify it.** Vehicle: a pre-printed NASPO number means at-cost pricing and the standard cert packet; no vehicle named, or "fair and reasonable" language, means competitive and the price is a bid. Sourcing: lines that map to Grainger item numbers price live, anything else needs the supplier bench and a longer clock. Flag that on day one, not the day before the deadline.

6. **Register it.** Add a row to `../quote-log.md` in the buyer folder, creating it from `references/buyer-context-template.md` if it isn't there.

7. **Report and stop.** Tell the rep what you found: vehicle, deadline, line count, forms required, and anything that needs sourcing. Then stop. Do not price, do not fill forms, do not draft an email to the buyer. Pricing and the cert packet are `/ca-rfq-quote`'s job — hand off, don't start.
