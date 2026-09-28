---
name: ca-territory-handoff
description: >-
  Segment a California state agency book by relationship state and turn it into a dated,
  prioritized call list a rep can work on Monday. Use when a rep takes over accounts, a
  departed rep's book needs re-homing, or someone asks which accounts have gone quiet, who
  Kim or Aanya should call first, how to split CDCR, Caltrans or any agency between reps, or
  for a handover, territory launch, account blitz or win-back plan. Use it too for
  analysis-only asks — "which accounts are at risk", "where is our whitespace at CMD", "size
  the winnable pond at CalVet", "which facilities have a Grainger account but never ordered"
  — because a segmentation without dated actions is a spreadsheet nobody works. Bands the
  book into recover, defend, watch, provisioned whitespace and cold start, each with its own
  opening words. Do NOT use to log or price a request or worksheet that has arrived (that is
  /ca-rfq), or to write outreach sequences.
requires: [business-central]
degrades-without: [sales-crm, ca-procurement-intel]
---

# CA territory handoff

This is the front of the pipeline. Prospecting and account work are what generate the
requests that `ca-rfq-intake` logs and the NASPO orders that `naspo-quote` prices, so the
call list this skill produces is not a separate exercise from the quote desk — it is what
feeds it.

A handoff fails in a predictable way: 48 facilities become one alphabetical list with one
deadline and no words to say, and the rep works it by geography. The whole method here is
refusing to do that. Segment by relationship state, rank by dollars actually at risk,
anchor the dates to the state's calendar rather than to a manager's month, and write the
opening sentence for each band.

## What this produces, and where it stops

Output is one dated file at
`Customers/State of CA Agencies/.sales-team/sal/<YYYY-MM-DD>-<agency-or-rep>-handoff.md`
when that synced folder is present (if it is not, say so and return the document in the
conversation), carrying: the banded book, the ranked at-risk list, the dated call list with openings, and
the per-account definition of done.

Stop there. Do not write outreach sequences, do not draft emails, do not send anything.
Sequence design belongs to `sales-outbound-prospecting`, `sales-follow-up-discipline` and
`sales-written-communication` (Sloane, where installed). This mirrors `ca-rfq-intake`
stopping before pricing: the stop is what keeps these skills composable instead of
overlapping.

## 1. Get the book, with the scope filter

The book's scope — body armor (by contract code) and CSU/UC are out of the Kim/Aanya CA
state book — lives in `bbs-foundations` `references/canonical-facts.md`, "CA state book scope". Take the exclusions from there, every run, and do not restate
the codes here or in your output: a copy is a second place to be wrong.

Where the account-synced `ca-state-sales-grounding` is installed, invoke it too for
additional context: the account split, the `AREA = CA-STATE` filter, the salesperson-code
caveats and the SCPRS denominator rule. It is not part of this marketplace; if it is not
installed, say so and ask the rep for the account split rather than assuming it.

Per facility, you need these fields, whatever extract they arrive in. Revenue, rep
attribution, order months and the customer number come from Business Central
(`bc_customer_snapshot`, `bc_query_entity`); if BC is unreachable, stop — there is no book to
band:

| Field | Used for |
|---|---|
| Revenue by fiscal year and by month, in scope | Run rate, the one-time-buy trap |
| Rep attribution and share of that facility's revenue | Finding what a departed rep took |
| Last order month | The silence test |
| The facility's own reorder gap (median months between orders) | The silence test's denominator |
| Grainger account present, and login on file | Provisioned whitespace |
| City, and BC customer number | Routing and record-keeping |

Name the fields, not a file. Extracts get rebuilt; the fields do not.

## 2. Segment into five bands

The bands are relationship states, not size tiers, because the band decides the first
sentence of the call.

| Band | Rule | What it actually is |
|---|---|---|
| **Recover** | Departed rep held ≥50% of the facility's revenue **and** the account is silent beyond its own reorder gap | The real win-back |
| **Defend** | Transacted within its own reorder gap | Expansion. Not recovery |
| **Watch** | Silent beyond its gap but never departed-rep-dominated | A service problem or a one-time buy |
| **Provisioned whitespace** | Grainger account exists, zero lifetime revenue | Free pipeline, setup already done |
| **Cold start** | No account, no history | True cold |

Two rules about those rules:

**The silence test is the account's own reorder gap, never a calendar constant.** An
account that buys twice a year is not quiet at four months; one that buys weekly is in
trouble at six. A fixed 90-day rule flags the first as at-risk and misses the second, which
is exactly backwards.

**Defend is usually the largest band by dollars, and it is the one most often mishandled.**
Opening a healthy account with "I'm taking over, sorry for the disruption" tells a buyer
their supplier relationship is unstable and burns the call on an apology instead of the
reorder. Report the band sizes side by side so whoever reads the handoff can see that the
book is mostly running.

## 3. Find what a departed rep took: attribution × recency

Neither half is sufficient alone. A high attribution share on an account still ordering is
not a loss — the relationship transferred with the order. Silence on an account the departed
rep barely touched is a service problem, not a handover problem. It is the intersection that
identifies the accounts where the relationship walked out the door.

Two things that fall out of the intersection and must be called out by name:

- **Concentration beats the headline.** "37% of the book was held personally" is true and
  useless as an instruction. The list of accounts at ≥50% and silent is the instruction.
- **A 100% share that is now silent is zero-threaded**, not "reduced coverage." There is no
  second name at BBS who has spoken to that buyer. Flag those separately; they are the
  urgent subset and they drive the two-name rule in §7.

Where a departing rep's company-wide numbers exist, do not present them as this book's
numbers. A rep whose total billings fell may have had a healthy book here, and a new rep
shown a collapsing chart in week one draws exactly the wrong conclusion about what she
inherited. Compute the monthly series for this book and say what it actually shows.

## 4. Rank by dollars at risk, not dollars ever

Rank within each band by annualized prior run rate × probability of loss, not by lifetime
revenue. Lifetime rewards history that will not repeat.

**The one-time-buy trap.** Flag any account where a single month is more than half of
lifetime revenue, and label it in the output. An account showing the largest lifetime total
in the book on the strength of one fiscal-year-end purchase is not a run rate, and a rep who
forecasts off it will miss by the size of that month.

**The partial-month trap.** The current month in any extract is incomplete by construction.
Never present it as a decline, and say "partial month, data as of <date>" on the row.

## 5. Size the pond

Read `references/pond-sizing.md` when the run reaches this step. It carries the SCPRS
denominator rule as applied here, the takeable/contestable/undercut-able slices, the UNSPSC
category definition and its known distortions, competitor-certification discipline, and how
to reconcile two sources that disagree about the same agency.

## 6. Anchor the dates

Invoke `ca-budget-timing`. Never restate an encumbrance date, a DGS cutoff or a budget item
from memory — a confidently stated stale date quoted to a buyer with authority is the
failure this whole method exists to prevent.

What the calendar changes here is sequencing, not just phrasing. An agency that carries both
the worst relationship risk and the longest funding runway is the first week's work, and the
reason the rep can give a buyer for calling is a real one. Say the coincidence out loud when
you find it; it is the spine of a launch.

A management date like "contact everyone by end of month" corresponds to nothing at any
agency. Count the working days against the facility count before accepting any such target,
and say plainly when the arithmetic does not work — an impossible plan fails as the rep's
failure rather than the plan's.

## 7. Multi-thread: the two-name rule

State agencies buy at the site. One agency is dozens of buying points, so a headquarters
relationship does not carry an institution.

**An account is not covered until two named humans at it are on record.** That is the
definition of done for the Recover band, not "made contact."

Second names legitimately come from: SCPRS named buyers with their spend and last-PO dates,
the buyer folders and `CLAUDE.md` files under `Customers/State of CA Agencies/`, the Sales
CRM (`bbs_rfqs`, read with `crm_list_records` — if the connector is absent, say the
second-name search is incomplete), and prior RFQ records. **Never invent one.** A name that turns out not to
exist ends the call, and in government sales it ends it publicly.

## 8. Write the words

Read `references/opening-lines.md` when building the call list. It carries one opening per
band, the true things a rep can say with their sourcing, the objection answers, and what to
do with each call outcome.

The call list itself is dated and ordered: the Recover accounts by name in ranked order
first, whitespace quote-first rather than conversation-first, Defend triggered by each
account's own reorder gap rather than by the calendar, and cold starts as a standing weekly
block rather than a deliverable with a date.

## 9. Definition of done, and the scoreboard

Read `references/scoreboard.md`. Per account the bar is: a named human, their role, a direct
line or email, the date of their next expected need, and a dated next action in the record.
Anything short of that is an attempt, not a contact — and a metric with no definition of
done gets reported as met and means nothing.

## 10. Honesty rules

- Every figure carries its source and an as-of date.
- "Data pending" beats an estimate. Always.
- State what BBS holds, never what a competitor lacks, unless the competitor's status has
  been verified. A rep corrected on a certification claim in front of a buyer loses the
  account and does not get it back that fiscal year.
- Label every SCPRS-derived figure with the slice it covers. Not "the market," not the
  agency's budget.

## Where the current research corpus lives

Territory research outputs — market sizing, budget reads, external and competitive intel,
geography — live in `Customers/State of CA Agencies/.sales-team/` and in the working data
folder of the session that produced them, where those are present on this machine — if
they are not, say so. **Read the current corpus; never carry a copy of it in this skill.** Those files are dated evidence with a shelf life measured in months.

Check the `as_of` field (and `warehouse_last_po_observed` where present) before using any
number from them, and print that date next to the figure. If the corpus is older than the
most recent Governor's Budget or the current extract, say so in the output rather than
quietly using it.

## Handing off

This skill ends where the pipeline continues:

- A contact produces a request or a worksheet → **`/ca-rfq`**, whose Gate 0 runs
  `ca-rfq-intake`. Log it before pricing anything.
- A contact produces a NASPO order or asks for pricing on item numbers → **`naspo-quote`**.
- A whole segment wants a promotion, a hot list, or a contract sheet → **`grainger-promo-page`**.
- Sequences, cadences and outreach copy → the `sales-*` craft skills (Sloane, where
  installed).

## Reference files

- `references/pond-sizing.md` — sizing the winnable pond from the SCPRS corpus.
- `references/opening-lines.md` — the band openings, the true things, the objections.
- `references/scoreboard.md` — definition of done, leading indicators, where each is readable.
