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

## Invoke the grounding first

Run `ca-state-sales-grounding` at the start of every run. It carries the Kim/Aanya
account split, the `AREA = CA-STATE` scope filter, the body-armor and higher-education
exclusions, the salesperson-code caveats and the source-trust table. Do not restate any
of it here or in the report — it changes, and a second copy is a second place to be wrong.
`ca-state-sales-grounding` is account-synced, not part of this marketplace: if it is not
installed, say so and ask the rep for the account split and scope filter rather than
assuming them.

## MCP connectors this needs

| Connector | Used for | If it is absent |
|---|---|---|
| Dataverse / Sales CRM (`crm_list_records`, `crm_get_record`, `crm_list_attributes`) | `bbs_rfqs` — the pipeline, per rep | Stop. Say the pipeline section cannot be produced. Do **not** substitute Business Central quote counts for it; that is the specific error this skill exists to prevent. |
| Business Central (`bc_query_entity`, `bc_list_open_sales_orders`, `bc_get_sales_document`) | Booked orders and invoices for the week | Report the pipeline half and mark bookings "data pending". |
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

**2. Business Central salesperson codes cannot produce a per-rep split.** `KQUEZON` is
Kim. `CA STATE TEAM` is a shared Parker-plus-Aanya bucket. `PMARSHALL` exists but is
unused, and **Aanya has no personal salesperson code at all**. Posted invoices also carry
codes that predate this arrangement entirely — `AKROTINSKY`, `UNIVERSITY`, `HOUSE`,
`JEFF`, `CARLOS`, the `BA-*` body-armor codes, and blanks — so do not assume a two-code
world. Attribute per rep by the CRM record owner (`_ownerid_value`), or failing that by
the agency-to-rep mapping in the grounding skill (ask Parker for it if that skill is not
installed). Never by BC salesperson code alone. If a
BC figure genuinely cannot be split, report it as a team baseline and say in the report
that it is one.

**3. Body armor is excluded, by contract code and never by product guesswork.** The
grounding skill names the codes. Strip them from every figure in this report; they are
Parker's separate book and leaving them in inflates whichever rep's agency they landed on.

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
| `bbs_accepted`, `bbs_orderfinalized` | Wins |
| `_bbs_accountid_value`, `_bbs_contactid_value` | Agency and named buyer |
| `statuscode` (In Progress 1, Submitted 100000001), `statecode` (0 Active) | Where it stands |
| `bbs_quotemethod` (0 Business Central, 1 Provision Connect, 2 Customer Documents) | How it was quoted |
| `bbs_lpa` | The leveraged procurement agreement, where flagged |

Three counts carry the week: **received** (`bbs_receiveddate` inside the week),
**submitted** (`bbs_submitteddate` inside the week), and **overdue** (`bbs_duedate`
passed with no `bbs_submitteddate`). The third is the one worth surfacing every time —
it is the only number in the report that names work that did not happen.

**Bookings, from Business Central** (`bc_list_open_sales_orders`, `bc_query_entity`) — sales
orders and posted invoices with their document
date inside the week, under the grounding skill's scope filter. On documents,
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
| Rep | RFQs received | Submitted | Overdue | Quoted value |

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

Where a week looks bad, say why before saying who. The FY26-27 revenue drop on this book
is a departed rep's collapsed territory, not Kim or Aanya underperforming, and a report
that omits that turns a structural fact into a performance accusation.
