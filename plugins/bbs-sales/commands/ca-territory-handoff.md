---
description: Segment a California state agency book by relationship state and turn it into a dated, prioritized call list — bands, the ranked at-risk list, and the words to open each call. Stops before any outreach is written.
---

# /ca-territory-handoff

A rep is taking over a book, or a book needs re-homing, or someone wants to know which accounts are at risk. Turn the book into something a rep can work on Monday. Run the `ca-territory-handoff` skill and follow it; the steps below are the shape of the run.

1. **Establish the scope.** An agency, a rep's book, or a departing rep's accounts. Invoke `ca-state-sales-grounding` for the account split, the `AREA = CA-STATE` filter and the body-armor exclusion by contract code. Do not restate any of it in the output — it changes, and a copy in a second place is a second place to be wrong. It is account-synced, not part of this marketplace; if it is not installed, say so and ask the rep for the split and filter rather than assuming them.

2. **Pull the book by facility.** Revenue by fiscal year and by month, rep attribution and share, last order month, the facility's own reorder gap, Grainger account presence, city, BC number. Name the fields, not an extract file; extracts get rebuilt. If a field is unavailable, say data pending rather than estimating it.

3. **Band it.** Recover (departed rep held ≥50% **and** silent beyond the account's own reorder gap), Defend (transacted inside its gap), Watch (silent but never departed-rep-dominated), Provisioned whitespace (Grainger account exists, zero lifetime revenue), Cold start (nothing). The silence test uses each account's own gap, never a calendar constant — an account that buys twice a year is not quiet at four months.

4. **Rank by dollars at risk.** Annualized prior run rate × probability of loss, not lifetime revenue. Flag any account where one month is more than half of lifetime: that is a one-time buy, not a run rate, and a rep who ranks off it forecasts wrong. Label the current month partial — it is incomplete by construction and is not a decline.

5. **Find the zero-threaded accounts.** Any account the departed rep held at 100% that is now silent has no second BBS name at it. List those separately; they are the urgent subset and they set the two-name rule.

6. **Size the pond.** Work `references/pond-sizing.md`. Report takeable, contestable and undercut-able separately, label every SCPRS figure with the slice it covers, and report the adjusted category figure with the exclusion named.

7. **Anchor the dates.** Invoke `ca-budget-timing` for the two-tier deadline, the encumbrance rule and any item that runs on the federal fiscal year. Never restate a deadline from memory. Count working days against the facility count before accepting any "contact everyone by <date>" target, and say plainly when the arithmetic does not work.

8. **Write the dated call list.** Ranked Recover accounts by name first with the band opening from `references/opening-lines.md`, whitespace quote-first, Defend triggered by each account's own reorder gap, cold starts as a standing weekly block. Every account gets a definition of done: a named human, a role, a direct line or email, the next expected need date, and a dated next action.

9. **Report and stop.** Give the rep the bands with their dollar totals, the ranked at-risk list, and the dated call list. Then stop. Do not write an outreach sequence, do not draft an email, do not send anything — sequences belong to the `sales-*` craft skills (Sloane, where installed).

Then hand off as the pipeline continues: any contact that yields a request or a worksheet goes to **`/ca-rfq`** next (its Gate 0 is intake, through `ca-rfq-intake`), a NASPO order or an item-number pricing ask goes to `naspo-quote`, and a segment that wants a promotion goes to `grainger-promo-page`.
