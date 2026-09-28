# The pocket card

The document that actually gets read. One screen on a phone, outdoors, minutes before the
meeting. If the rep has to scroll to find a price, it has failed.

## Four blocks, in this order

### 1. Why we're here
One sentence. Then the buyer and the requester, with tap-to-call `tel:` links. Nothing else.

### 2. The prices
Three to five lines. Each tagged by what it is:

| Tag | Means |
|---|---|
| **down** | Price fell. Lead with this one |
| **up** | Rising. Say it yourself, in one sentence |
| **swap** | We're proposing a different item. Bring the sample |
| **flagged** | We cannot win this line today. Be honest, offer to source it another way |

Numbers only. No rationale — that lives in the long brief.

### 3. The questions
Five maximum, ordered by what opens the most. One line each, with at most one line of why.

If the brief has nine questions, the card gets the five that matter and the rest become a
follow-up email. A first meeting spent interviewing the customer about our own record-keeping
reads as an audit.

### 4. Do not say
Explicit, itemized, unhedged. Typically:

- Competitor names or their certifications
- Any SCPRS-derived figure
- Internal gaps stated as customer-facing numbers
- Any other facility's AR or performance
- Anything outside this rep's book

## Also on the card

**In the bag** — the physical list. Printed price sheets with copy counts, product samples
for any swap, the cert packet as a visible stack, business cards, a blank contact sheet.

A spec swap does not sell off a spreadsheet. The warehouse manager approving a substitution
needs to hold both items.

**One verification line** in the footer for anything that must be checked before sending —
a duplicate contact record, an unconfirmed email address.

## Design constraints

Published as an artifact, mobile-first, per `artifact-design`:

- Fluid type via `clamp()`, and `text-size-adjust` set, or iOS inflates the page.
- No fixed minimum widths anywhere. Grids use `minmax` / `auto-fit`.
- Tables restack into labeled field/value pairs under ~700px rather than scrolling sideways.
- Semantic color carries state — down / up / swap / flagged read at a glance, before the
  words are read.
- Both light and dark themes defined at token level.

Test the assumption that matters: can someone find the toilet-tissue price in four seconds
without scrolling? If not, cut something.
