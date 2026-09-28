---
name: ca-budget-timing
description: >-
  Translate the California budget and procurement calendar into sales timing — when an
  agency has money, when it must encumber it, and which deadline governs a specific deal.
  Use whenever anyone asks when to call an agency, whether money lapses on 30 June, what an
  encumbrance deadline is, whether a deal can still land this fiscal year, when the DGS
  cutoff falls, what the enacted budget gave an agency such as CHP, CAL FIRE, State
  Hospitals or Caltrans, whether an augmentation is one-time or ongoing, or how to sequence
  a quarter's selling. Use it before promising a buyer any date: 30 June does not govern
  everything (deals above delegated authority go through DGS around 1 April), California's
  fiscal year does not govern federally funded items, and a lapsing appropriation needs a
  signed PO by the deadline, not a delivery. Not for an RFQ's own due date, which belongs to
  that request's run record.
requires: []
degrades-without: []
---

# CA budget and procurement timing

Urgency in this territory is structural. It comes from the fiscal year, from encumbrance
deadlines on one-time appropriations, and from contract expiries — never from anything a rep
manufactures. Getting the dates right is what makes a rep useful to a public buyer; getting
them wrong loses deals quietly, months later, with no feedback.

This skill answers three questions: does the agency have money, by when must they commit it,
and which deadline governs this particular deal.

## 1. The two-tier deadline — quote both, never one

There is no single California deadline, and treating 30 June as universal is the mistake
that costs the most.

| Path | Practical cutoff | Applies when |
|---|---|---|
| **Through DGS** | **~1 April** of the fiscal year, for non-IT goods | The deal is above the agency's delegated purchasing authority |
| **SB/DVBE Option**, run by the agency itself | **30 June** | $5,000.01–$249,999.99, two certified quotes, no advertising (State Contracting Manual Vol. 2 §1200) |

A rep who knows both can place a large deal in March and a small one in late June. A rep who
knows only "June 30" loses the large one in April and never learns why — the deal simply
does not come back.

The ~1 April date follows a DGS bulletin pattern rather than a statute, so it moves. **Verify
the current fiscal year's bulletin before quoting the date to a buyer**, and say which
bulletin you checked.

## 2. Encumbrance means a signed purchase order, not a delivery

Gov. Code §16304; SAM §8325. An appropriation is encumbered when the agency has a signed
purchase order against it by the deadline. Delivery can follow. Disbursement then runs two
further years before the balance reverts — four years for federal funds.

Two consequences worth carrying verbatim:

- **A deal in late June is not dead.** You can honestly tell a buyer that an August delivery
  is fine against June money, provided the PO is signed.
- **This is a trust-building conversation, not a trick.** Most buyers know it; the ones who
  do not are relieved to hear it, and it is checkable. A rep who gets this right is treated
  as someone who understands the buyer's constraints, which is the whole relationship.

## 3. The fixed statewide calendar

These dates do not move, and each changes what a rep says.

| Date | What it is | What it changes |
|---|---|---|
| **~10 January** | Governor's Budget (Cal. Const. Art. IV §12(a)) | Everything said about next fiscal year before this is speculation. The budget corpus gets reissued after it |
| **~14 May** | May Revision (Gov. Code §13308(e)) | Augmentations and cuts firm up. Re-check any item you quoted in the spring |
| **15 June** | Constitutional deadline for passage | The enacted budget becomes citable |
| **30 June** | Encumbrance deadline for lapsing appropriations; end of FY | The SB/DVBE Option cutoff |
| **1 July** | New fiscal year begins | Money is fresh |

**The best selling window is the first half of the fiscal year** — money is new, encumbrance
deadlines are distant, buyers are planning. Say this out loud to a new rep, because the
instinct is to assume all the pressure is in June, and that instinct wastes the good months.

See `references/calendar.md` for how to read the current corpus's encumbrance table against
these dates.

## 4. How to answer "does this agency have money"

Read the current budget corpus. Cite the **item number**, the amount, the fiscal year, and
whether it is one-time or ongoing. Never estimate an appropriation, and never infer one from
an agency's size or activity.

Three things to check before answering:

- **One-time versus ongoing.** A one-time augmentation is a window with a closing date; an
  ongoing baseline increase is a different sales conversation entirely.
- **Contingent appropriations are not spendable** until the authorizing legislation passes.
  Say so explicitly rather than counting them.
- **Cuts and closures cut both ways.** A facility scheduled to close is not a forecastable
  account, and a rep should be told before they build a pipeline on it.

If the corpus does not cover the agency, say data pending. An invented budget figure quoted
to a buyer who administers that budget ends the relationship.

`references/sourcing.md` says where the enacted budget, LAO reports and DGS bulletins live
and how to cite one so a rep can defend a date.

## 5. Multi-year items and non-California deadlines

Check the item, not the calendar. Some appropriations run on a different clock, and they are
the ones with the longest runway.

The worked example (from the corpus that surfaced it — confirm the current item before
repeating it): the California Military Department's facilities maintenance and repair item
is **federal money encumberable to 30 September** — the federal fiscal year, not
California's. An agency whose funding runs to 30 September is available in a quarter when
everyone else is closed, which is a real reason for a buyer to take a call and a real reason
to sequence that agency first.

The general rule this proves: **the deadline is a property of the appropriation, not of the
agency and not of the state.** Two items at the same agency can lapse on different dates.

## 6. Freshness is part of the answer

The budget corpus lives in `Customers/State of CA Agencies/.sales-team/` and in the working
data folder of the session that produced it, where those are present on this machine. If
they are not, say so and answer from the primary sources in `references/sourcing.md`. It is reissued after the ~10 January Governor's
Budget, and its own text says so.

Do not carry a copy of it. **Check its `as_of` before using any figure, and say the date out
loud to the rep** — "as of the enacted Budget Act of <year>, corpus dated <date>." A
confidently stated stale encumbrance date is worse than no answer, because the rep repeats it
to a buyer with authority and the correction comes from the buyer.

If the corpus predates the most recent Governor's Budget or May Revision, say that before
answering, and treat every FY-forward figure in it as speculative.

## Where this fits

Budget timing is what dates the call list. `ca-territory-handoff` invokes this skill for
every date it prints; nobody should be restating a deadline from memory in a handoff, a
quote, or a promo page.

For the live read on what the Legislature actually funded or cut at a specific agency — the
enacted budget, LAO analysis, augmentations by agency — ask **Nell**, the CA state budget
analyst, where that account-synced agent is installed. She reads lao.ca.gov/budget and the
enacted budget directly; without her, read those two sources yourself and cite them. This
skill carries the method and the calendar; Nell carries the current answer.

## Reference files

- `references/calendar.md` — the statutory dates that do not move, and how to read the
  current corpus's encumbrance table. Pointer to the live corpus, not a copy.
- `references/sourcing.md` — where the enacted budget, LAO reports and DGS bulletins live,
  and how to cite one so a rep can defend a date to a buyer.
