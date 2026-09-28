---
name: bbs-weekly-sales-report
description: >-
  Build Parker Marshall's weekly sales summary of his own, Kim Quezon's and Aanya
  Samarasinghe's week on the California state agency book, written to
  ~/weekly-sales-reports/YYYY-MM-DD_weekly-sales-report.md under that week's Monday. Use
  when Parker says "weekly sales report", "write up the week", "what did the team do this
  week", "I have to fill out the sales form", "pull the numbers for the weekly", or asks for
  quotes, RFQs, orders or bookings over a named week or "last week". Use it too for a
  per-rep question over a week — "how did Aanya do this week", "what did Kim quote", "did we
  submit everything that was due" — because Business Central's salesperson codes cannot
  split Aanya out of a shared bucket and its quote records miss most of the pipeline; the
  Sales CRM is the pipeline. Do NOT use for a month, quarter or fiscal-year-to-date figure;
  those are booked-revenue questions for Business Central directly.
requires: [sales-crm]
degrades-without: [business-central, microsoft-365]
---

# BBS weekly sales report

Parker submits a weekly Microsoft Form summarizing the week for himself, Kim and Aanya.
This skill produces the underlying markdown report he writes the form from.

The form itself is submitted by a human. Produce the file; do not attempt to submit
anything on Parker's behalf.

## Ground the scope first

The book's scope — body armor (by contract code) and CSU/UC are out of the Kim/Aanya CA
state book — lives in `bbs-foundations` `references/canonical-facts.md`, "CA state book
scope". Take the exclusions from there at the start of every run.

Where the account-synced `ca-state-sales-grounding` is installed, invoke it too for
additional context: the Kim/Aanya account split, the `AREA = CA-STATE` scope filter, the
salesperson codes and their caveats, and the source-trust table. Do not restate any of it
here or in the report — it changes, and a second copy is a second place to be wrong. It is
not part of this marketplace; if it is not installed, say so and ask Parker for the account
split rather than assuming it.

## MCP connectors this needs

| Connector | Used for | If it is absent |
|---|---|---|
| Dataverse / Sales CRM (`crm_list_records`, `crm_get_record`, `crm_list_attributes`) | `bbs_rfqs` — the pipeline, per rep | Stop. Say the pipeline section cannot be produced. Do **not** substitute Business Central quote counts for it; that is the specific error this skill exists to prevent. |
| Business Central (`bc_query_entity`, `bc_get_sales_document`, `bc_describe_entity`) | Booked orders and invoices for the week | Report the pipeline half and mark bookings "data pending". |
| Outlook (`outlook_email_search`) | Parker's own outbound activity only | Omit the activity note. Never imply coverage of Kim's or Aanya's mail — there is no delegate access to their mailboxes. |

If a connector needs authorization, say so plainly and stop on that section rather than
estimating around it.

## The four traps

These are the reasons this skill exists rather than a generic weekly-report routine.

**1. The Sales CRM is the pipeline, not Business Central.** Dataverse `bbs_rfqs`, read
through the Sales CRM connector, is live and Kim and Aanya create records in it
themselves. Many quotes never reach BC at all, so a BC quote count understates the week's
pipeline — often badly. Query the CRM for anything about quotes, RFQs, response time or
win rate. Use BC for what BC is authoritative on: posted orders, invoices, booked revenue,
AR. The two answer different questions and neither substitutes for the other.

**2. Business Central salesperson codes cannot produce a per-rep split.** Which codes
exist and what each covers is `ca-state-sales-grounding`'s to say, not this skill's —
read them there, and ask Parker if that skill is not installed. What matters here is the
consequence: Aanya's work does not land under a code of her own, and posted invoices carry
codes from earlier arrangements, so do not assume a clean one-code-per-rep world.
Attribute per rep by the CRM record owner (`_ownerid_value`), or failing that by the
agency-to-rep mapping in the grounding skill. Never by BC salesperson code alone. If a BC
figure genuinely cannot be split, report it as a team baseline and say in the report that
it is one.

**3. Body armor and CSU/UC are excluded — body armor by contract code, never by product
guesswork.** Canon's "CA state book scope" names the codes. Strip them from every figure in
this report; leaving them in inflates whichever rep's agency they landed on.

**4. Aanya owns CRM records directly.** This is the whole reason her week is measurable.
Filter `bbs_rfqs` on `_ownerid_value` for her rather than reaching for the BC team bucket.

## Pulling the week

The week runs Monday to Sunday. The report is filed under the **Monday** date. If Parker
says "last week" on a Tuesday, he means the week that just closed, not the two days so far.

**Activity note, from Parker's own mailbox** (`outlook_email_search`) — optional, and his
mailbox only.

**Pipeline, from `bbs_rfqs`** — per rep, using the owner field:

| Field | Gives you |
|---|---|
| `_ownerid_value` | The rep. Kim, Aanya or Parker |
| `bbs_receiveddate`, `bbs_duedate`, `bbs_submitteddate` | What came in, what was due, what went out on time |
| `bbs_quotevalue` / `bbs_quotevalue_base` | Dollar value |
| `bbs_accepted` | **Not a confirmed win.** Report it as "accepted in CRM (unconfirmed)" — see *Wins* below |
| `bbs_orderfinalized` | Supporting signal only; not by itself a win |
| `_bbs_accountid_value`, `_bbs_contactid_value` | Agency and named buyer |
| `statuscode` (In Progress 1, Submitted 100000001), `statecode` (0 Active) | Where it stands |
| `bbs_quotemethod` (0 Business Central, 1 Provision Connect, 2 Customer Documents) | How it was quoted |
| `bbs_lpa` | The leveraged procurement agreement, where flagged |

Three counts carry the week: **received** (`bbs_receiveddate` inside the week),
**submitted** (`bbs_submitteddate` inside the week), and **overdue** (`bbs_duedate`
passed with no `bbs_submitteddate`). The third is the one worth surfacing every time —
it is the only number in the report that names work that did not happen.

**Wins.** What `bbs_accepted` means is not yet ruled (open for Parker in `docs/STEWARD.md`,
*Already open for Parker*; when ruled, the ruling gets one home and this skill points
there). Until then, take the safe reading: `bbs_accepted` is **not** a confirmed win.
Report those records in their own column, "accepted in CRM (unconfirmed)". Count a record
as a **win** only when one of these confirms it — a Business Central quote with an
`acceptedDate`, a quote converted to a sales order, or a quote-log Outcome of *won* — and
the rep has confirmed it. Keep the unconfirmed column out of wins and out of any win rate.

**Bookings, from Business Central** (`bc_query_entity`) — query the `salesOrders` entity
filtered on `documentDate` inside the week, and the `salesInvoices` entity on the same
filter to catch orders booked and shipped inside the week (an order that shipped in full
may already have become an invoice). Count each booking once: match an invoice to its
order where the invoice carries the order number (check with `bc_describe_entity`), and
say in the report if some could not be matched. Do not use the open-orders tool for
bookings: it returns only orders not yet fully shipped, so anything booked and shipped in
the same week disappears. Apply the book's scope as above. On documents,
`shortcutDimension1Code` is CONTRACT and `shortcutDimension2Code` is the CUSTOMER agency
code; AREA is not a shortcut dimension and has to be joined through dimension set lines,
so filtering on dimension 2 for the agency and dimension 1 to exclude the body-armor codes
is the practical scope filter. If you need a field this skill does not name, describe it
with `bc_describe_entity` rather than guessing at it.

## Report structure

Write to `~/weekly-sales-reports/YYYY-MM-DD_weekly-sales-report.md`, Monday date.

```markdown
# Weekly Sales Report — week of [Monday date]

## Summary
[Three or four sentences. What moved, what did not, what needs a decision.]

## Pipeline (Sales CRM, bbs_rfqs, as of [date])
| Rep | RFQs received | Submitted | Overdue | Quoted value | Accepted in CRM (unconfirmed) | Confirmed wins |

## Bookings (Business Central, as of [date])
[Orders and invoices in the week, in scope. Team baseline where it cannot be split — say so.]

## By rep
### Kim Quezon
### Aanya Samarasinghe
### Parker Marshall

## Overdue and at risk
[Every RFQ past due with nothing submitted, with agency, value and days late.]

## Notes and data gaps
[What could not be pulled and why.]
```

## House rules

Every figure gets a source and an "as of" date. An unreachable source produces "data
pending", never an estimate. Fiscal years are California's, July through June. Everything
here is read-only — no writes to BC, Dataverse, QuickBooks or Supabase, and no mail sent
on anyone's behalf. Any procurement figure drawn from the SCPRS warehouse is the
SB/DVBE-visible slice and must say so; it is not the market.

Where a week looks bad, say why before saying who. Explain structural causes — a
territory in transition, a fiscal-year boundary, a one-time buy in the comparison period,
an attribution gap in the codes — before naming any person. A report that skips that step
turns a structural fact into a performance accusation.
