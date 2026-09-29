# Measurement — proving the program

Owner: Parker. Cadence: monthly 30-minute review. Storage: one SharePoint list
("BBS AI Metrics") + the Claude admin analytics dashboard. No BI tools.

## Baseline (do this month — the window closes)

Reconstruct pre-Claude time-per-RFQ for 3–5 completed quotes from Outlook timestamps
(RFQ arrival → quote sent). Record each in the SharePoint list with a `baseline=yes` flag.
Without this row, no future claim of time saved is provable.

## Inbound four (capacity)

| Metric | Source | Definition |
|---|---|---|
| Quotes/rep/week | BC salesQuotes by salesperson code | count, documentDate in week |
| Turnaround | desk folders / Outlook | RFQ arrival → packet delivered, hours |
| Win rate by lane | BC (needs v1.1 quote loop) | accepted ÷ sent, NASPO vs competitive SEPARATELY |
| Adoption | Claude admin analytics | active reps this week ÷ reps |

## Outbound four (growth — the point)

| Metric | Source | Definition |
|---|---|---|
| Outbound motions/rep/week | weekly log | promo page, winback batch, or follow-up sweep run |
| Promo pages shipped | vercel/repo | count live, per month |
| Winback conversations | weekly log | drifted-buyer contacts that got a reply |
| Net-new or reactivated buyers | BC | first order on a customer number with 12 months silence |

## Draft quality

| Metric | Source | Definition |
|---|---|---|
| Draft-fix rate | desk `FLAGS.md` | Drafts a review caught before send, and how many of those lines are repeats (`Happened more than once?` = yes). Count only lines that exist. Baseline: [MISSING — NEEDS INPUT]. Do not backfill a number. |

## Rules

- Blended win rate hides the NASPO ruling — always segment by lane.
- Adoption is the leading indicator; if a rep goes quiet 2 weeks, ask them what broke.
- Review inbound AND outbound halves together — capacity without conversion is a fail.
