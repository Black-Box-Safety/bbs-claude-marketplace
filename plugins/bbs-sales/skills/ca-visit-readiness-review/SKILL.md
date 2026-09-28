---
name: ca-visit-readiness-review
description: >-
  Pressure-test a finished California state agency call plan, account brief or leave-behind
  before a rep walks in with it, from the point of view of the person who has to say it in
  the room. Use whenever a visit brief, call plan, pocket card, talking points or
  customer-facing leave-behind has been drafted and someone asks to review it, sanity-check
  it, or get a second opinion — and when the brief is finished and nobody asked, because an
  unreviewed prep document is the one that puts an inferred job title or a slice-limited
  market figure in front of a procurement officer. It checks five things — what a rep would
  add, what would hurt them in the room, whether the product story is right, which catalog
  gaps need verifying, and whether it works on a phone ten minutes before the meeting.
  Do NOT use to write the brief itself (ca-site-visit-brief) or for agency background
  (ca-agency-primer).
requires: []
degrades-without: [business-central, sales-crm]
---

# CA visit readiness review

A call plan written from the data and a call plan written by someone who has stood in a
procurement office are different documents. This skill is the second read.

It runs **after** `ca-site-visit-brief` has produced something, and before the rep leaves.
It does not write the brief — it returns an ordered list of what to change, and the changes
get applied back to the source document.

## Ground first

Take the book's scope from `bbs-foundations` `references/canonical-facts.md`, "CA state book scope" — body armor and CSU/UC are out of the Kim/Aanya CA
state book. A reviewer working from stale account assumptions produces confident wrong
corrections, which is worse than no review.

Where the account-synced `ca-state-sales-grounding` is installed, invoke it too for
additional context. It is not part of this marketplace; if it is not installed, say so and
ask the rep for the account split rather than assuming it.

Read the whole brief, and read the underlying folder and account data too — Business Central
(`bc_customer_snapshot`) and the Sales CRM (`crm_list_records`) where connected. A review that
only reads the brief can only catch tone, not fact.

## The five questions

### 1. What would you add before walking in?

Concrete additions only: a category angle nobody covered, a contract-vehicle play, a
competitive risk, a question worth asking on site, a leave-behind, a physical object to
bring.

The highest-yield version of this question: **what does this site buy from someone else
that BBS demonstrably delivers at a sister site?** That comparison is invisible from a
single-site brief and is usually the strongest thing available in the room.

### 2. What is in there that would hurt them?

Look for, specifically:

- **Slice-limited figures stated as fact.** SCPRS sizing, share claims.
- **Internal gaps presented as customer-facing numbers.** Quoted value with unknown outcomes
  is not revenue and must not be said like it is.
- **Another facility's AR, or another rep's book.**
- **Phrasings that read badly over a shoulder.** Anything implying we hoped they would not
  notice something.
- **A number that invites the answer you do not want.** Characterizing a lull as a collapse
  is the standard example.
- **Inferred facts on customer-facing pages.** A job title guessed from buying patterns; an
  email address that has a known duplicate record.
- **Question volume.** Nine questions about our own record-keeping is an audit, not a first
  meeting.

### 3. Is the product story right?

Check the order of the conversation, not just its content. Does it lead with the reason for
the visit? Is the increase said honestly and in one breath? Is the buying mechanism sold
before the catalog? And is there an opening that is not the category they already buy?

### 4. Which catalog gaps need checking?

Where the account spends money BBS should be able to quote and currently cannot, name it and
say what would close it — a cost source, a line card, a distributor relationship, a vehicle.

Mark each as **verify**, not as a miss, unless line-card coverage has actually been checked.
"We cannot source this" and "nobody has checked whether we can source this" are different
findings and only one of them is usually true.

### 5. Does it work on a phone?

The honest answer for most long briefs is no, and the fix is not to shorten the brief — it
is to derive a pocket card from it and keep both. See
`../ca-site-visit-brief/references/pocket-card.md`.

## Output

An ordered list of changes, most consequential first, each naming the specific line or
section. Separate the three kinds:

- **Factual errors** — fix before anything else, especially on customer-facing pages.
- **Additions** — what is missing.
- **Cuts and rephrasings** — what should not be said, and how to say it instead.

Then apply them to the source document and republish. A review that stays in chat while the
rep carries the old version has accomplished nothing.

## Stop rules

- Do not invent contacts, figures or products that are not in the source data.
- Do not soften a factual error into a suggestion. A wrong job title on a leave-behind is a
  defect, not a preference.
- Do not add scope the rep did not ask for. The review serves this visit.
