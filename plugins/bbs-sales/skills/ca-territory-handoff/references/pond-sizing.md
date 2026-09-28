# Sizing the winnable pond

Read this when a handoff run reaches the pond-sizing step. It exists as a reference rather
than in SKILL.md because it is the longest single body of rules and it is only needed once
per run.

## The denominator rule, applied

`ca-state-sales-grounding` states the rule (if it is not installed, the ca-procurement-intel
MCP's own instructions carry the same rule): the SCPRS warehouse holds a deliberate slice of
California procurement, by default the SB/DVBE-visible harvest. It is not all California
procurement.

What that means operationally, every time you print a number from it:

- Label the figure with the slice. **"SB/DVBE-visible slice of the SCPRS harvest, as of
  <date>"** — not "the market," not "the agency's budget," not "state procurement."
- The label travels with the number into the output file and into anything a rep might read
  aloud. A rep who repeats an unadjusted, unlabelled pond figure to a buyer who knows their
  own spend loses credibility permanently, and it is not recoverable in the same fiscal year.
- If you cannot establish which slice a figure came from, it is not usable. Say data pending.

## The three slices, and why they are different numbers

Report them separately. Collapsing them into one "opportunity" figure overstates by a
multiple and gives the rep no idea what to do differently per dollar. The ca-procurement-intel
MCP's `play_contestable_market`, `play_undercut_coop` and `play_category_whitespace` are the
usual starting points; check what each covers with `explain_method` before printing a figure
from it, and if the connector is absent, say pond sizing is data pending.

| Slice | Definition | What the rep does with it |
|---|---|---|
| **Takeable** | In-category spend at this agency that BBS can quote today on an existing vehicle | Call list fuel. This is the real number |
| **Contestable** | In-category spend held by an incumbent BBS could displace, but which needs a solicitation, a new vehicle, or a catalog addition | A campaign, not a call |
| **Undercut-able** | Spend where BBS can quote but the current holder's price is unknown | Verify before promising anything |

Whitespace — a provisioned account with zero revenue — is takeable by definition and is the
cheapest slice in the set. Surface it separately from the dollar totals, because its value
is speed rather than size: pricing is live against that account today.

## Category definition and its distortions

Categories are read from UNSPSC segments — 42 (medical), 46 (defense/safety/security) and 53
(apparel/luggage/personal care) are the segments that carry BBS's catalog.

Segment-level rollups sweep in lines that are nothing to do with the book. The worked
example: a single hearing-aid family under 42211705 can carry tens of millions at a
corrections agency and swamp the category, producing a "takeable" figure that is mostly one
audiology vendor. **Always report the adjusted figure**, name the exclusion and its size, and
keep the unadjusted number visible so the adjustment is auditable rather than a silent edit.

The general rule: before trusting any agency-level category total, list the top vendors and
top UNSPSC lines inside it. A distortion is almost always one vendor and one line, and it is
obvious in thirty seconds if you look.

## Competitor certification discipline

Certification status is the strongest lever in this territory and the easiest to get wrong
in public.

- **State what BBS holds, by channel.** In California, DVBE only — BBS is not a California
  small business. Federally, SDVOSB and small business. Never state it without the channel
  (canonical-facts.md, "Certifications, by jurisdiction"). What that certification means
  under the SB/DVBE Option — including that BBS can only be one of two or more DVBE quotes,
  and cannot win a pool of SB quotes — is in `ca-budget-timing` §1. Do not size a slice on
  the Option without reading it.
- **Never state what a competitor lacks unless it has been verified** in the certification
  registry, with the date of the check recorded. Carry unverified competitor status as an
  open verification item in the output, never as a claim.
- A rep corrected on a certification claim in front of a buyer loses that account.

## Reconciling two sources that disagree

Business Central and the SCPRS corpus will give different sizes for the same agency, and so
will two vintages of the corpus. They are not in conflict; they measure different things.

1. Establish what each source covers before comparing. BC is BBS's own transactions from
   April 2025. SCPRS is a slice of the agency's procurement across all vendors. QuickBooks
   covers the pre-April-2025 history without dimensions.
2. Use BC for what BBS holds, SCPRS for what the agency spends. Never subtract one from the
   other without saying that is what you did and why the difference is meaningful.
3. When two corpus vintages disagree, prefer the newer and report the delta rather than
   silently replacing the figure — a moving pond size is itself information about the agency.
4. If the gap cannot be explained, print both with their sources and flag it. An unexplained
   reconciliation is a finding, not an embarrassment.
