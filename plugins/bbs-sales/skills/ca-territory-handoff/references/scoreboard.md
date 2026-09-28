# Definition of done, and the scoreboard

Read this at the end of a handoff run. It is the part most likely to need updating, because
it depends on which systems are currently readable.

## Definition of done, per account

A contact is complete when the record carries all five:

1. A named human.
2. Their role at the facility.
3. A direct line or email that has been used, not just found.
4. The date of their next expected need.
5. A dated next action.

Anything less is an attempt. This matters more than it sounds: a metric with no definition
of done is unfalsifiable, so it gets reported as met and means nothing, and the first thing
a new rep learns is that the numbers are decorative.

**Per band, the bar rises:**

| Band | Done means |
|---|---|
| Recover | The five above, **plus a second named human at the account**. A 100%-attributed account that went silent was single-threaded; one name is how it happened |
| Defend | The five above, plus the account's reorder gap recorded so the next call is triggered rather than scheduled |
| Provisioned whitespace | A quote delivered, not a conversation held |
| Watch | The reason for the silence, named. Service issue, one-time buy, or budget — these lead to three different next actions |
| Cold start | The five above. Nothing more is expected on a first pass |

## Leading indicators, weekly

Accounts contacted (by the definition above), response rate, meetings booked, quotes out.
Revenue is a monthly number, not a weekly one.

## Where each indicator is actually readable

This is the part that breaks quietly, so state it explicitly in every handoff:

| Indicator | Read it from | Caveat |
|---|---|---|
| Response time, quotes out | **Dataverse `bbs_rfqs`** (the Sales CRM, via `crm_list_records`) | The pipeline system of record. Reps own records directly, and it carries received / due / submitted dates, so these are genuinely measurable here and are not measurable in BC. Production org only |
| Win rate | Confirmed wins only — a BC quote `acceptedDate`, a quote converted to an order, or a quote-log Outcome of *won*, confirmed by the rep | `bbs_accepted` in the CRM means the quote converted, but canon records that it has never been set (`bbs-foundations` `references/canonical-facts.md`, "What counts as a win"). Report it as "not recorded in CRM", never as zero, and never derive a win rate from it |
| Revenue | **Business Central** | Salesperson codes are stamped by whoever keyed the document, so a rep's own code can credit them with a tiny fraction of the book they actually carry. Check whose code is on the documents before reporting a rep's revenue, and say what the code covers |
| Pipeline | Not Supabase `rep_cockpit` | Stale. Do not point a rep at it |

**If a rep's salesperson code is not stamped on their documents, their BC number is not
their book.** Say so in the handoff rather than reporting the number. Handing someone a
target against a scoreboard they cannot open is how you produce a rep who stops believing
targets. Where the fix is an ops change — stamping the code going forward — the handoff
should say it is happening and what the rep uses in the meantime.

## Ramp

State it honestly and in the output. A book that took a departing rep years does not
transfer in a month.

- Month 1: contact and requalification.
- Months 2–4: quotes, and whichever funding window the calendar says is open.
- Months 5+: anything large enough to clear DGS, which needs the earlier of the two
  deadlines (see `ca-budget-timing`).

Judging a launch on first-month revenue teaches the rep to chase the small reorder instead
of the largest at-risk account, which is precisely the wrong lesson in week one. Say that
where whoever sets the target will read it.
