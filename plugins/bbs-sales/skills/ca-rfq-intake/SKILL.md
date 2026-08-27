---
name: ca-rfq-intake
description: Log an inbound California state quote request into the right customer folder and open its run record — the first move on any state RFQ, NASPO or competitive. Use this the moment a request arrives from a CDCR institution, CalVet home, DSH hospital, Caltrans district, CalFire unit, CMD, DWR, or any State of California agency, whether it comes as an email with attachments, a bare item list, a Line-Item Cost Worksheet, or a portal link — and use it before pricing anything, because an RFQ that never got logged is the one that misses its deadline. Also use it when asked to file, log, intake, or "start" a state quote request, or to find where a request should live.
---

# CA state RFQ intake

Logging is the cheap step that makes every later step possible. An RFQ that lands in
an inbox and never lands in a folder has no deadline anyone can see, no history for the
next quote to learn from, and no place for the certs to go. This skill does that first
move and stops — pricing and paperwork come after, in `naspo-quote`.

It runs the same for a NASPO ValuePoint reorder and a competitive solicitation. The
difference shows up at pricing, not at intake.

## 1. Find the folder before creating one

The tree is
`Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`.

Work down it in that order and reuse what exists:

- **Agency** — the folder usually carries the Grainger account in its name
  (`CMC - 887895111 - California Men's Colony`). Check
  `references/agency-tree.md` for the current list before inventing a folder; the
  same agency appears under several names in the wild (Caltrans/Cal Trans, CDCR
  institutions by acronym).
- **Institution or Buyer** — CDCR, CalVet, and DSH nest by institution, then buyer.
  Departments (DWR, CMD, PDC, CDFW) nest straight to buyer. If the buyer is new to
  us, create their folder and a `CLAUDE.md` from `references/buyer-context-template.md`.
- **Deal folder** — `<Item M.D.YY>`, e.g. `metal detectors naspo 8.27.26`. Lowercase
  item description, the vehicle if it's worth flagging, then the date the request
  arrived. This is the house convention for the CA state tree; the
  `yyyymmdd-<customer>-<shortdesc>` slug used elsewhere in the quote desk does not
  apply here.

Creating a second folder for a buyer who already has one is the most common intake
error and the most expensive, because the next quote's precedent search misses it.
Search the tree by buyer name and by item before you create anything.

## 2. Save everything as received

Every attachment, unrenamed: the RFQ or worksheet, blank certs, spec sheets, the
buyer's email itself as text or PDF. Completeness matters more than tidiness — a spec
sheet you skipped is the substitution argument you can't make later.

If the buyer sent only an email body with an item list, save it as
`request-email.txt` in the deal folder. The words they used are evidence about what
they'll accept.

## 3. Open the run record

Create `RFQ.md` in the deal folder from `references/rfq-record-template.md`. Fill what
the documents actually say and flag what they don't — an empty required field is
information, a guessed one is a liability.

The fields that decide everything downstream:

| Field | Where it comes from | Why it matters |
|---|---|---|
| Due date + time + timezone | the RFQ, or the email | The only thing that can't be recovered later |
| Solicitation number | the Line-Item Cost Worksheet header, usually | Goes on every cert; missing means reference the BBS quote number |
| Vehicle | NASPO ValuePoint, DGS BPO, or competitive | Decides whether pricing is at-cost or a bid |
| Grainger account | the agency folder name or the buyer note | Wrong account, wrong price |
| Forms required | the attachment list and any "must return" language | Missing one form can make the bid non-responsive |
| Ship-to | buyer note or the RFQ | Freight, and the tax jurisdiction if tax ever applies |

Read the buyer's `CLAUDE.md` (a folder up) while you fill this in. It carries what we
learned last time: format quirks, whether they accept equivalents, how they've handled
recycled-content answers.

## 4. Classify the request

Two questions, both answerable from the documents:

**Vehicle.** A pre-printed NASPO number on the worksheet, or an agency that buys on
one, means at-cost NASPO pricing and the standard cert packet. No vehicle named, a
"fair and reasonable" form, or language about competing quotes means competitive —
the certs are the same, the pricing is a bid, and margin is the rep's call.

**Sourceable or not.** Line items that map to Grainger item numbers price live.
Anything else needs the supplier bench, which is a different clock — flag it in the
run record on day one, not the day before the deadline.

## 5. Register it and hand off

Add a row to `../quote-log.md` in the buyer folder (create from
`references/buyer-context-template.md` if absent) so the buyer's history stays in one
readable place. The Supabase `rep_cockpit` pipeline in `ca-quote-hub` remains the
tracker of record for deadlines across all buyers; this log is the local, human
version that travels with the documents.

Then say what you found and what's next — vehicle, deadline, line count, forms, and
whether anything needs sourcing. Pricing and the cert packet are the `naspo-quote`
skill's job; hand off, don't start.

## What not to do at intake

Don't price, don't fill forms, and don't email the buyer. Intake exists to make the
request findable and its clock visible. Mixing in the work that follows is how the
deadline field ends up empty.

## Reference files

- `references/agency-tree.md` — the agency and institution folders that exist, with
  Grainger accounts, so you file into the tree rather than beside it.
- `references/rfq-record-template.md` — the `RFQ.md` run record shape.
- `references/buyer-context-template.md` — `CLAUDE.md` and `quote-log.md` for a
  buyer folder, the ICM layer that later quotes read first.
- `scripts/scaffold_folder_context.py` — generate or refresh the `CLAUDE.md` files
  across the whole tree from the buyer notes already on disk.
