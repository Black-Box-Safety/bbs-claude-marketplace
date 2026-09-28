# The confidence ledger

Every site visit brief ends with this. It exists so a rep can improvise without stating
something they cannot defend, and so the next person reading the brief knows which numbers
survived scrutiny.

Five tiers. Each figure in the brief belongs to exactly one.

## Hard — Business Central / Sales CRM

Revenue by fiscal year and month, invoice counts, AOV, reorder cadence, AR and ageing,
category mix, top SKUs by spend, contract vehicle mix, open pipeline values, and every
contact name, phone and email.

Always state the as-of date. Always state that cancelled invoices are excluded. Quotable
internally and to the customer without qualification.

## Documented — the site's own folder

Prior quotes and their estimate numbers, PO numbers and their stated expiry, the agency's
own RFQ forms, the cert packet, any pricing comparison already built for this site.

The strongest material in a brief, because it is the customer's own paper. A PO that says
"pricing valid until 6/30" is a fact the buyer cannot dispute and usually has not noticed.

## Slice-limited — SCPRS

Competitor prices, category sizing, "who else sells here", any market-share-shaped number.

**Never say these out loud in a customer meeting.** SCPRS harvests are a visible slice, not
the market. Two failure modes, both bad:

- "We're your #1 supplier" — the buyer either disputes it or resents it.
- "This category is worth $3.1M to you" — you have just told a procurement professional
  their own budget, from partial data.

Mark the harvest scope and date in the ledger. Use them to decide where to aim, never as a
claim.

## Inference — plausible, unverified

State the inference and the reason in the same sentence, and label it. "Consistent with the
FY26 pricing expiring 6/30" is honest. "They stopped buying because pricing expired" is not,
until they say so.

An inference in a brief is a question to ask on the call, not a finding to present.

## Data pending — genuinely missing

Say exactly "data pending". Never estimate, never bracket, never round toward a guess.

The recurring members of this tier:

- **Win/loss on open RFQs.** `bbs_accepted` is not a confirmed win (see `SKILL.md` §1 for
  what confirms one). Without a confirmation, we do not know.
- **Contact titles.** Frequently blank in the CRM.
- **Requester identity** on historical quotes that were addressed to a shared mailbox.
- **Any site with no BC history at all** — a cold start is a cold start, not a small number.

## Wording

In the brief, tier the figures. In the room, the rule collapses to one line the rep can
hold: *say the hard numbers and the customer's own paper; ask about everything else.*
