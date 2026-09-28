---
name: ca-agency-primer
description: >-
  Build the background briefing that lets a rep understand a California state agency as a
  system rather than one facility — what the department does, how its sites differ, where
  the money is, and where Black Box Safety stands at each location. Use when a rep is taking
  on an agency or preparing for a first meeting inside a multi-site department, or asks what
  an agency is, what its facilities do, how many sites it has, why one site buys differently
  from another, or where the whitespace is across CDCR, DSH, CalVet, Caltrans, Cal Fire, CHP
  or DGS. Use it too for narrower asks — "tell me about Patton", "why is this agency so
  small for us", "which facility should we be at" — because a single-site answer inside a
  multi-site department usually hides the real finding. Keeps public agency facts, internal
  BC and CRM figures and SCPRS slices visibly separate, and says "data pending" where BBS
  has no history. Not for one booked meeting (ca-site-visit-brief).
requires: [business-central]
degrades-without: [sales-crm, ca-procurement-intel]
---

# CA agency primer

A rep who knows one facility will sell to one facility. The account is the department.

This skill produces the standing background document for a whole agency: what it is, what
each site does, how each one buys, and where BBS actually stands. It is the companion to
`ca-site-visit-brief` — the primer is read once when taking on the agency and refreshed
quarterly; the visit brief is written per meeting.

## Where this sits

`ca-territory-handoff` splits and prioritizes a book. This skill explains **one agency in
that book** deeply enough that a rep can talk about the department in front of any of its
sites. `ca-budget-timing` covers when the money lands; this covers what the organization is.

Stop at the document. No outreach, no quotes, no campaign.

## 1. Ground first

Take the book's scope from `bbs-foundations` `references/canonical-facts.md`, "CA state book scope" every run — body armor and CSU/UC are out of the
Kim/Aanya CA state book. Cancelled invoices stay excluded. Do not restate either in the
output.

Where the account-synced `ca-state-sales-grounding` is installed, invoke it too for
additional context — account split, scope filter, SCPRS rules. It is not part of this
marketplace; if it is not installed, say so and ask the rep for the account split rather
than assuming it.

## 2. Research the agency as a public institution

State agencies publish more about themselves than almost any private customer. Use their own
documents, not third-party summaries:

| Want | Where it usually is |
|---|---|
| Mission, program structure, facility list | The department's own site |
| Per-facility population, capacity, headcount, program mix | The department's budget estimate or May Revision document |
| Enacted funding, year-over-year change, position counts | Governor's Budget by item number; the LAO's spending plan write-up |
| Recent program or capacity changes | Budget change proposals, capital outlay lines |

The budget estimate documents are the high-value source. They carry per-site operational
detail that marketing pages do not, and they are the agency's own numbers.

What to capture per site: what the facility actually does, who it serves, its size, and
anything structural that shapes buying — a population that is growing, a new unit coming
online, an aging physical plant, a security posture that dictates who is allowed on site.

## 3. Pull the internal picture per site

From Business Central (`bc_customer_snapshot`, `bc_query_entity`) and the Sales CRM
(`crm_list_records`), per facility — if the CRM connector is absent, mark contacts and
pipeline "data pending" and carry on: revenue by fiscal year, YTD, invoice count,
AOV, reorder cadence and current state, dominant contract vehicle, top categories, open
pipeline, AR, and the named contacts with their request counts.

Where SCPRS sizing helps, it comes from the ca-procurement-intel MCP (`market_spend_summary`)
and is its own source class (§4).

Then do the thing that makes this document worth writing: **put the two side by side**. A
1,300-patient facility doing $40K while a same-sized sibling does $1.2M is the finding. It is
invisible from either source alone.

## 4. Mark every figure with its source class

Four classes, and the document must make them visually distinct — not just footnoted:

- **Public** — from the agency's own budget or program documents. Safe to reference with a
  customer. Cite the document and its date.
- **Hard internal** — BC and CRM, with the as-of date. Internal use; individual facts about
  the customer's own orders are fine to discuss with them.
- **SCPRS-derived** — slice-limited. Never stated to a customer as market fact.
- **Data pending** — say it exactly. A site with no BC history is a cold start, not a zero.

Never blend classes in a sentence. "They have 1,300 patients and we do $40K there" is two
classes and must read as two.

## 5. Write the per-site sections

Each site gets: what it is (public), what BBS sees (internal), and one line on why it matters
commercially. Look specifically for:

- **How each site buys differently.** Contract vehicle mix varies enormously within one
  department. One site punching out on a cooperative contract and another submitting the
  agency's own RFQ forms need different quoting behavior, and a rep who treats them alike
  will lose the second one.
- **Paperwork conventions per site.** Whether quotes are addressed to a named requester or a
  shared mailbox, whether solicitation numbers encode a department or requester, whether one
  desk routes everything. These determine whether the account's history is legible at all.
- **Population or capacity trends.** Growth on a residential campus converts directly into
  consumables. A site above its stated capacity is a different sales conversation from one
  running under.

## 6. Close with the reads

The document ends with what the pattern says, not a restatement:

- Which sites are lapsed against **their own** cadence, not a calendar month.
- Where the whitespace is, measured as share against a comparable sibling site.
- Which categories BBS proves it can deliver at one site and does not sell at another.
- What is genuinely unknown, named as such.

Then a short ordered action list — who to call, in what order, and what to establish.

## 7. Publish and file

Publish as an artifact per `artifact-design`, mobile-correct. **Mark it internal at the top.**
The primer contains other facilities' AR, whitespace gaps and slice-limited sizing — none of
it belongs in front of the customer, and the header should say so.

File the source at
`Customers/State of CA Agencies/.sales-team/callie/<agency>-primer.md` when that synced folder
is present, and refresh it rather than writing a second one. If it is not present, say so and
leave the published artifact as the copy of record.

## Stop rules

- Do not estimate for a site with no history. "Data pending."
- Do not present SCPRS sizing as the agency's budget or the market.
- Do not let a public figure and an internal figure share a sentence without both labeled.
- Do not put a headquarters revenue target in the document when BBS has never sold there —
  HQ is usually an influence target, not a quota target, and saying so is the useful finding.
