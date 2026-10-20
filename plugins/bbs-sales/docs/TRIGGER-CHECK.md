# Skill trigger check — bbs-sales territory skills

First run on the territory branch (3 September 2026); re-run against main for 0.4.0 on 28
September 2026 — see the last section.

Adding two skills to a plugin whose existing skills already fire on "a California state agency
thing arrived" carries one real risk: `ca-territory-handoff` stealing RFQ intakes. Both are
"do something structured with a CA agency," and a handoff description that leans on agency
names would start winning conversations that belong to `ca-rfq-intake`. Breaking a working desk
to add a new capability is not a trade worth making, so the descriptions were checked against
realistic rep phrasings before release.

**Date:** 3 September 2026. **Method:** each phrasing read against all five descriptions,
judging which one a reader would pick and whether any second skill is a plausible competitor.

## Should fire `ca-territory-handoff`

| # | Phrasing | Fires | Nearest competitor |
|---|---|---|---|
| 1 | "our CDCR rep left — which of his accounts have actually gone quiet and which are still ordering?" | handoff | none. "gone quiet"/"still ordering" is relationship state, named in the description |
| 2 | "kim's got 48 facilities and 20 working days. what does he call first?" | handoff | none. Prioritization and a dated list |
| 3 | "which CMD facilities have a grainger account set up but have never placed an order with us" | handoff | intake shares "CMD" and "order"; the description names provisioned whitespace verbatim, so handoff wins |
| 4 | "we're splitting caltrans between aanya and kim, how should it break" | handoff | none. Book split |
| 5 | "size the winnable pond at calvet — how much of their spend can we actually get" | handoff | `grainger-promo-page` also does SCPRS segmentation, but for a campaign audience, not book sizing. Handoff names pond sizing explicitly |

## Should fire `ca-budget-timing`

| # | Phrasing | Fires | Nearest competitor |
|---|---|---|---|
| 1 | "if I get the PO signed june 28 but we don't ship till august does the money still count" | budget-timing | none. The encumbrance rule is in the description in those words |
| 2 | "buyer at DSH says she has to spend by end of the fiscal year. is that actually her deadline?" | budget-timing | none. Two-tier deadline |
| 3 | "what did the enacted budget give CAL FIRE this year, and is it one-time" | budget-timing | Nell (an account-synced agent, where installed) overlaps by design — the skill points at her for the live read and says so |
| 4 | "when's the DGS cutoff for a $180k order" | budget-timing | none. Names the DGS cutoff and the SB/DVBE threshold |
| 5 | "is september a bad time to be calling state agencies" | budget-timing | handoff also sequences a quarter; handoff invokes budget-timing for exactly this, so either entry point lands right |

## Should fire `ca-rfq-intake`, not the new skills

| # | Phrasing | Fires | Why the handoff does not win |
|---|---|---|---|
| 1 | "log this CDCR request from Kaycie Koll, worksheet attached" | intake | A specific arrived request with a document. "Log" plus an attachment is intake's language; handoff has no document-arrival trigger |
| 2 | "porterville just emailed asking for pricing on 14 line items, where does this go" | intake | "Where does this go" is folder placement. Handoff produces a call list, not a folder |
| 3 | "start a quote request for CHP, they sent a portal link" | intake | "Start"/"portal link" are named in intake's description |
| 4 | "file this DWR RFQ before I lose the due date" | intake | A deadline on a specific request, not a calendar question. `ca-budget-timing` is about appropriations, not RFQ due dates — no collision |
| 5 | "aanya got a bare item list from a DGS building, what's the first move" | intake | "First move on any state RFQ" is intake's opening line. Brenda is the nearer competitor here (DGS BPO), and that is correct routing, not a skill collision |

## Ambiguous cases resolved deliberately

- **"when's the next caltrans glove reorder window?"** → `ca-territory-handoff`. A reorder gap is
  account behaviour, not an appropriation. Budget timing answers when the agency has money;
  the reorder gap is in the handoff's segmentation fields. Called out here because the phrasing
  reads like a calendar question and is not one.
- **"build a promo page for CAL FIRE off this hot list"** → `grainger-promo-page`. A priced sheet
  plus "promo page" is unambiguous; handoff's segmentation language does not reach it.

## Result

No collision found. The separation that does the work: `ca-rfq-intake` triggers on **a document
that arrived**, `ca-territory-handoff` on **a book to be worked**, and `ca-budget-timing` on **a
date to be defended**. The two overlaps that remain are intentional handoffs rather than
contests — budget-timing to Nell for the live read, and handoff to budget-timing for dates.

Re-run this check whenever a description in this plugin changes.

## Re-run against main — 28 September 2026 (bbs-sales 0.4.0)

The first run predates main's reorganization. On main the desk has ten skills and one command,
`/ca-rfq`, whose Gate 0 is intake; `/ca-rfq-log` and `/ca-rfq-quote` no longer exist, and the
new skills now hand off to `/ca-rfq`. The four skills that arrived after the first run
(`ca-agency-primer`, `ca-site-visit-brief`, `ca-visit-readiness-review`,
`bbs-weekly-sales-report`) were never in it. Same method: each phrasing read against every
description in `bbs-sales` plus `bbs-claude-coach`, whose `/bbs-what-can-i-do` and
`/bbs-start` answer "what can I do" and "how do I start".

| Phrasing | Fires | Nearest competitor, and why it loses |
|---|---|---|
| "the agency emailed a worksheet from a buyer Kim just called — what now" | `ca-rfq-intake` / `/ca-rfq` | `ca-territory-handoff`. Its description now says in so many words not to use it for a request or worksheet that has arrived |
| "how do I start on the CDCR book Aanya inherited" | `ca-territory-handoff` | `bbs-claude-coach` ("how do I start"). The coach orients on the toolkit and hands a named job to its skill; "the CDCR book" is a named job. If the coach does fire, its `references/jobs-map.md` has a territory-handoff row that names this skill |
| "what can I do about the accounts that went quiet" | `ca-territory-handoff` | `bbs-claude-coach` ("what can I do"). Same reasoning: the object of the sentence is accounts, not the toolkit |
| "prep Aanya for her Metro visit Thursday" | `ca-site-visit-brief` | `ca-agency-primer`. The primer is agency-wide background; each description now names the other for the boundary |
| "tell me about DSH before I take it on" | `ca-agency-primer` | `ca-site-visit-brief` — no booked meeting, so the primer |
| "read this call plan and tell me what would hurt her in the room" | `ca-visit-readiness-review` | `ca-site-visit-brief`. The brief writes; the review reads a finished one |
| "how did Aanya do this week" | `bbs-weekly-sales-report` | None in this plugin. `bbs-back-office` skills answer from Business Central, which is the trap the report's description names |
| "which BPOs are behind pace" | agent `brenda` | `dgs-bpo-item-check` answers on-list/off-list for a part number only; pace is Brenda's |
| "is this part on the BPO" | `dgs-bpo-item-check` | `brenda`, who now points at it for exactly this |
| "price these Grainger items for CalVet" | `grainger-pricing` / `naspo-quote` | `ca-territory-handoff` names "a Grainger account but never ordered" as whitespace; it prices nothing and has no item-number trigger |

**Result — a desk read, not a measurement.** Each phrasing above was read against the
descriptions by one reader judging which a model would pick; nothing was run, and nothing
here shows how often any skill actually fires. Within that limit: one obvious collision was
fixed — the handoff description gained a "do NOT use" clause for arrived requests — the
primer and the visit brief each name the other, the readiness review names both, and every
new description sits under 960 characters so none of those clauses can be truncated away.
The coach overlap is meant as a routing overlap rather than a contest, and the coach's
`jobs-map.md` now carries rows for territory handoff, visit prep, the weekly report and
budget timing so that it can route there; whether it does in practice is unmeasured. Skill
triggering is not machine-checked; `docs/evals/` needs Claude auth to reproduce, and until
it is run this file is a reasoned expectation, not evidence.

## Adding `bc-item-entry` — 16 October 2026 (bbs-sales 0.7.0)

`bc-item-entry` is the first skill on the desk that writes to Business Central, so the risk
runs the other way from the territory additions: a pricing or quote-building request must
not land on a skill that creates item cards, and an item-creation request must not be
answered by `bbs-quote-builder` building a PDF around numbers BC does not have. Same method
as before: each phrasing read against every description in `bbs-sales` plus `bbs-deck-voice`.

| Phrasing | Fires | Nearest competitor, and why it loses |
|---|---|---|
| "these three SKUs aren't in Business Central yet, add them so I can build the quote" | `bc-item-entry` | `bbs-quote-builder` ("build the quote"). Its description says it does not create or edit records in BC; the item-entry description names "create the items so I can build the quote" verbatim |
| "set up the item cards in BC for this PO" | `bc-item-entry` | none. "item cards" and "BC" appear in no other description |
| "enter these products into Business Central with the vendor and cost from the Grainger pricing" | `bc-item-entry` | `grainger-pricing`. Pricing already happened in the sentence; the verb is "enter", and the item-entry description names Grainger pricing as an input |
| "BC doesn't have an item number for the hoist on this order, create the item" | `bc-item-entry` | `bbs-quote-builder` reads an SQ; it has no verb for creating anything |
| "the items are all in BC now, build the customer quote PDF from SQ-104999" | `bbs-quote-builder` | `bc-item-entry`. Items already exist and the ask is the PDF; the item-entry description excludes building the quote |
| "price these Grainger items on the CMC account, just the prices, nothing in BC" | `grainger-pricing` | `bc-item-entry` names Grainger pricing only as a source for a cost; "nothing in BC" is the boundary both descriptions draw |
| "the vendor isn't in BC, create it from the address on the quote" | none in `bbs-sales` (the rep does it in the BC UI) | `bc-item-entry`, whose description says in so many words that it does not create vendors |

The six phrasings with an expected winner are `item-1` to `item-4`, `item-sib-1` and
`item-sib-2` in `docs/evals/queries-routing.json`. **Result: still a desk read.**
`docs/evals/discriminate.py --runs 5 --workers 4 --anonymize` was attempted on
2026-10-16 and did not run: the `claude` CLI on the machine doing the work had no
authenticated session (see the PR #64 body). The expectation above stands until a run with
Claude auth replaces it.


## Added 20 October 2026: `bbs-daily-rep-summary` beside `bbs-weekly-sales-report`

The two share every noun — Parker, a rep, the CRM, Business Central, "how did she do". The
split is the time window and the mode. Read against both descriptions.

| # | Phrasing | Fires | Why |
|---|---|---|---|
| 1 | "what did Aanya do yesterday" | daily | "yesterday" is named in the daily description; the weekly says "Do NOT use for a week… figure" in the other direction and names a week |
| 2 | "set up the daily rep routine" | daily | verbatim in the daily description |
| 3 | "draft my check-in" / "end of day, what do I tell Parker" | daily, check-in mode | the rep-side phrasings are only in the daily description |
| 4 | "how did Aanya do this week" | weekly | "this week" is a weekly phrasing; the daily description sends a week figure to the weekly report by name |
| 5 | "pull the numbers for the weekly" | weekly | verbatim in the weekly description; no overlap |
| 6 | "what's Aanya's number this quarter" | neither; Business Central directly | both descriptions send a quarter figure to BC |
