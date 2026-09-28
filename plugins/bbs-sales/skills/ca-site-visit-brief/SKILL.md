---
name: ca-site-visit-brief
description: >-
  Build the document set a rep walks into a California state agency site visit with — a
  long-form call plan for the night before and a one-screen pocket card for the parking lot.
  Use whenever a rep has a meeting, site visit, first call, QBR, check-in or introduction
  booked at any CA state facility, or someone asks to prep for a call, brief a rep, build
  talking points, or work out what to say at CDCR, DSH, CalVet, Caltrans, CHP, Cal Fire or
  any agency site. Use it too for narrower asks — "what should Aanya lead with at Metro",
  "what do we know about this buyer", "why did this site go quiet", "what do I ask them" —
  because a pile of account facts is not a call plan. Produces the facts, the order to say
  them in, the questions, and the explicit list of numbers not to say aloud, keeping what BC
  and the CRM prove apart from public documents, inference and the unknown. Not for
  agency-wide background (ca-agency-primer).
requires: [business-central]
degrades-without: [sales-crm, ca-procurement-intel]
---

# CA site visit brief

A rep walks into a state facility with two problems: not knowing what is true, and not
knowing what to say first. Most account research solves the first and calls it done. This
skill produces both halves, and refuses to ship one without the other.

The output is **two documents, always**:

1. **The call plan** — long form, read the night before. Account state, the money story,
   the people, the run of the call, the confidence ledger.
2. **The pocket card** — one screen, no scrolling, read in the parking lot. Why we're here,
   four prices, five questions, and what not to say.

Shipping only the long one is the common failure. Nobody scrolls past a contact table to
find a price with four minutes to go.

## Where this sits

`ca-territory-handoff` decides **who to call**. This skill prepares **the specific meeting**
that call produced. `ca-rfq-intake` logs what the meeting generates; `naspo-quote` prices it.

Stop at the documents. Do not send outreach, do not build the quote, do not fill compliance
forms. If the visit needs a price sheet as a leave-behind, name it in the leave-behind list
and let `naspo-quote` build it.

## 1. Ground first, every run

Before anything else, take the book's scope from `bbs-foundations` `references/canonical-facts.md`, "CA state book scope": body armor and CSU/UC are out of
the Kim/Aanya CA state book. Do not restate it in your output.

Where the account-synced `ca-state-sales-grounding` is installed, invoke it too for
additional context: the account split, the `AREA = CA-STATE` scope filter, the
salesperson-code caveats, and the SCPRS denominator rule. It is not part of this
marketplace; if it is not installed, say so and ask the rep for the account split rather
than assuming it.

Two house rules that bite specifically here:

- **Cancelled invoices are excluded from revenue.** They double-count. A brief quoting gross
  revenue overstates the account to the rep's face.
- **`bbs_accepted` is not a win source today** — see `bbs-foundations`
  `references/canonical-facts.md`, "What counts as a win". A win is confirmed by a BC quote `acceptedDate`, a converted order, or a quote-log
  Outcome of *won* the rep has confirmed. Without one, the honest statement is
  "we do not know if we won these" — never "we won them".

## 2. Assemble from four sources, and keep them separate

| Source | Gives you | How to mark it |
|---|---|---|
| Business Central (`bc_customer_snapshot`, `bc_query_entity`) | Revenue by FY and month, invoice count, AOV, cadence, AR, top SKUs by spend, vehicle mix | **Hard.** Quote freely, internally and to the customer |
| Sales CRM (`crm_list_records`, `crm_get_record`) — if absent, contacts are "data pending" | Named contacts, titles, phones, emails, request counts, open RFQs and their values | **Hard**, with the caveat that titles are often blank — see §5 |
| The site's own folder | Prior quotes, PO numbers and expiry dates, the agency's own RFQ forms, cert packet, pricing research already done | **Documented.** The strongest material in the brief |
| SCPRS, via the ca-procurement-intel MCP (`market_last_sales`) | Competitor prices, category sizing, who else sells there | **Slice-limited. Never say out loud** — see `references/confidence-ledger.md` |

The folder is where the reason for the visit usually lives. Expiring PO pricing, a cost
comparison someone already built, a quote that never closed — that beats any summary
statistic. Read the site folder before the dashboards.

SCPRS comes through the ca-procurement-intel MCP (`market_last_sales`,
`play_competitor_profile`). If that connector is absent, the slice-limited tier is simply
empty; say so in the ledger.

## 3. Find the reason for the visit

Every good call plan has one sentence at the top answering "why are we here this week
rather than any other week". Look for, in order:

1. **Expiring paper.** A PO that states pricing valid only through a date. FY boundaries are
   the single most common reason a state account goes quiet.
2. **A capacity or program change.** New beds, a new facility, a new unit activated, a
   budget augmentation. `ca-budget-timing` covers the money side.
3. **A silence that breaks the site's own cadence.** Measure against that facility's median
   gap, never a calendar month. See the spiky-series warning in §5.
4. **An open item nobody closed.** A large submitted RFQ with no recorded outcome.

If none of these exist, say so, and frame the visit as a relationship call rather than
inventing urgency.

## 4. Write the run of the call

Order matters more than content. The pattern that works:

1. **The reason for the visit**, with the good news first if there is any. A price that went
   down is the best possible opening sentence.
2. **The honest item.** Anything going up, any line where we are exposed. Say it before they
   find it, and say it as one sentence, not as a contradiction spread across three bullets.
3. **The mechanism that makes it easy.** How the agency can buy without going to bid —
   typically Grainger Sourcing under the LPA (`bbs_lpa = S`) [FLAG: confirm with Parker
   that off-catalog Sourcing orders need no bid — see `references/opening-moves.md`; until
   then, describe only what this site has already done]. Do not introduce a contract
   vehicle the site has no history on; adding a vehicle to a working punch-out account
   solves a problem they do not have.
4. **The expansion ask**, tied to something physical they are doing.
5. **The mechanical ask** — who else should be on the punch-out, who should quotes be
   addressed to.

`references/opening-moves.md` carries the phrasings and the traps.

## 5. Three data problems that recur, and what to do

**Blank titles.** The CRM leaves `jobtitle` empty constantly. Never infer a title onto a
document the customer will see — "Warehouse Manager" guessed from buying patterns becomes a
printed error in their hands. Write "title data pending".

**Duplicate and truncated contact records.** Near-duplicate identities (`Eman` / `man.`,
`John Thompson` / `Keith Thomson`) are common. Before any leave-behind is addressed, verify
the email against a second source, and flag the duplicate in the brief.

**Spiky monthly revenue.** State facilities buy in bursts. Before calling a two-month lull a
collapse, compute the site's median non-zero month. Characterizing a normal gap as a loss
invites the buyer to agree that they moved the business. Ask what is queued instead.

## 6. Build the confidence ledger

Every brief ends with a ledger sorting every figure in it into tiers: hard, documented,
slice-limited, inference, and genuinely missing. `references/confidence-ledger.md` has the
tier definitions and the wording. This is not decoration — it is what lets a rep improvise
safely, and it is where "data pending" gets said instead of a guess.

## 7. Build the pocket card

Derive it from the brief; never write it independently. Four blocks, one screen:

- **Why we're here** — one line, plus the buyer and requester with tap-to-call numbers.
- **The prices** — three to five, each tagged down / up / swap / flagged. Numbers only.
- **The questions** — five at most, ordered by what opens the most.
- **Do not say** — the explicit list. Slice-limited figures, competitor claims, internal
  gaps, any other site's AR, and anything outside this rep's book.

`references/pocket-card.md` has the structure and the design constraints.

## 8. Publish

Both documents publish as artifacts, built per `artifact-design`. Mobile correctness is not
optional here — the card is read on a phone, outdoors, in a hurry. Fluid type, no fixed
minimum widths, tables that restack rather than scroll sideways.

Write the source files to
`Customers/State of CA Agencies/.sales-team/reese/<YYYY-MM-DD>-<site>-visit.md` alongside
publishing, when that synced folder is present, so the next visit starts from the last one.
If it is not present, say so; the published artifacts are then the copy of record.

## Stop rules

- Never state a SCPRS-derived figure to a customer. Sizing is internal posture.
- Never claim a win without the confirmation canon requires (`bbs-foundations` `references/canonical-facts.md`, "What counts as a win").
- Never put another facility's AR, or another rep's book, in a document going to a site.
- Never let a competitor's certifications into the room. Check whether ours is actually a
  differentiator against the specific competitors on the account before leaning on it.
