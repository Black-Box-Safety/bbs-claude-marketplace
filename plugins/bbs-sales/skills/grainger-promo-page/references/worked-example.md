# Worked example: CAL FIRE H2 2026

What actually happened on the build this skill was written from, and what it cost
to find out. The numbers below are real. The project lives at
`programs/2026-08-28-calfire-hotlist-h2/`.

Read this for calibration on how much of the work is verification. Roughly none of
it was design.

## The setup

On 2026-08-24 a Grainger government contract manager loaded negotiated pricing
onto every Black Box Safety CAL FIRE account and sent a priced hot list: 6
categories, 92 line items. CAL FIRE buys these exact categories in volume, mostly
through channels that return no diversity participation. The job was to put the
priced list in front of the buyers already buying the items, routed so the spend
reports.

The finished piece was a landing page with a quote builder, plus three segmented
email campaigns.

## What the data said

**The prime concentration.** CAL FIRE (SCPRS business unit 3540) spent $9.74M
direct with Grainger across 489 distinct buyer names, FY24 to FY26, in the
MRO-prime direct slice. The next prime down was $2.2M. That concentration is the
reason a single-prime hot list was worth a page at all.

**The three segments**, sized 2026-08-28:

| Segment | Definition | Buyers | Spend | Slice |
|---|---|---|---|---|
| A | Buys Grainger direct, no BBS history | 268 | $3,937,250 | MRO-prime direct, since 2025-08-01 |
| B | Buys the categories from other suppliers, no BBS history | 214 | $1,344,038 | SB/DVBE-visible, since 2025-08-01 |
| C | Buys the categories elsewhere, has BBS history | 7 | $215,359 | SB/DVBE-visible, since 2025-08-01 |

Segment C was seven people. It was also the most valuable list in the campaign:
seven warm relationships that had gone quiet, one of them buying $122,252 from
four other suppliers. Those seven got individual emails from a human. The other
482 got a campaign.

Note that A and B come from different corpus slices, so their spend figures cannot
be added. The README labels every row with its slice for exactly that reason.

**Where the discount actually was.** The instinct was a campaign headlined on the
signature wildland gear. The category sizing said the deep discounts sat in
janitorial and fleet consumables. A "deep discounts on fire gear" headline would
have died on contact with any buyer who knew the prices, and every buyer on this
list knows the prices.

## What the pricing check found

The sheet was the authority, and it was still worth checking against the agency's
own Grainger account (887895160, CAL FIRE Headquarters Sacramento, NASPO
ValuePoint CA State Agency schedule, sell rule `at_cost`).

**The account beat the sheet on 14 of 91 priced lines.** The negotiated sheet is
supposed to be the best price, so every one of these was a gap to raise with the
rep:

| Item | Sheet | Account | Difference |
|---|---|---|---|
| 11Z396 McLeod tool | $108.56 | $99.02 | $9.54 |
| 9KE02 shovel/pick combo | $136.63 | $128.51 | $8.12 |
| 25K815 cone cups | $32.49 | $31.38 | $1.11 |
| 9DTE3 hydration reservoir | $40.51 | $39.83 | $0.68 |
| 38W367 C cells | $11.33 | $10.75 | $0.58 |
| 5PE82, 5PE83, 5PE84 leather gloves | $3.30 to $3.39 | $3.07 | up to $0.32 |
| 5LE21, 5LE23 Procell cells | $11.37, $14.46 | $11.27, $14.19 | $0.10, $0.27 |
| 39FD09 poly bottle | $1.59 | $1.46 | $0.13 |
| 24M905 hydration conversion kit | $10.18 | $10.08 | $0.10 |
| 4EY97 safety glasses | $1.69 | $1.61 | $0.08 |
| 56LK29 combo tool handle | $28.39 | $28.38 | $0.01 |

The owner's ruling: print the lower of the two on every line, and tell the rep
about the gap, because "lowest when you quote" is what the rep had promised. If
you skip this check you ship a page that a buyer can beat by opening their own
punchout, which is the worst possible outcome for a page whose entire argument is
that the price does not change.

**The discount figure has two honest values.** Across the 89 lines carrying a list
price, the spend-weighted discount is 41.8% off list. The simple mean of the
per-line percentages is 44.0%. Both are true and they are different numbers.
Neither could print, because there is no registry row for a discount claim. Per
item, list price beside contract price is product data and shipped fine.

## The six errors in the source sheet

Every one of these was found by comparing the sheet's description against the
product API. They are typed by a human under time pressure and they are normal.

| Item | Sheet says | Actually is |
|---|---|---|
| 2VJX9 | Industrial cleaner/degreaser, spray | Wire rope, 250 ft |
| 46T349 | Small engine fuels | 54 gal drum, $1,065.27, backordered |
| 1MPU7 | Metal polish, 8 oz | 19.25 oz |
| 4YPA8 | Trash bags, 45 gal | 55 gal |
| 784K11 | Hygenall ToxOff spray | Temporarily unavailable at least 30 days |
| 9AN11 | Fire shelter, Large | Grainger's own image shows the Regular |

The first one is the instructive one. A degreaser that prices as 250 feet of wire
rope is a wrong item number, and it would have shipped as a $64.65 degreaser on a
page a buyer would then have tried to order from. The last one is the reason to
look at the images and not only the text: the correct item, the correct price, and
a photograph of the wrong variant.

None were silently corrected. All went in the README under "Data corrections
applied" so the rep could tell the vendor.

## The expired pricing term

The sheet's footer read "Pricing is good until June 30th, 2026." The sheet was
titled H2 2026 and was sent on 2026-08-24. The term, as written, was already past.

This is the single most important finding in the build, because the offer is the
pricing. It could not be paraphrased around, it could not be dropped and left
implicit, and it could not be guessed. It needed one written line from the rep
confirming the real term, and until that arrived every piece downstream was
provisional.

`scripts/price_hotlist.py --report` prints the term line for this reason.

## What blocked the send

The page built, deployed, and passed the gate clean at `--scope mro --scope
agency`. It still could not be sent. The blockers, in the order they matter:

1. **The pricing term was expired as written.** No piece could state a term or an
   expiry until the rep confirmed the real one in writing.
2. **No registry row for a discount claim.** So no percentage anywhere in copy,
   despite 41.8% being real and being the most persuasive number in the file.
3. **No registry row for an availability claim, for CAL FIRE as a named customer,
   or for a general web address.** Each surfaced as a `NEEDS CLAIM` marker in the
   drafts rather than a paraphrase.
4. **The contact email was wrong and the gate could not see it.** The registry
   registers `joey@blackboxsafety.com`, who covers UC, CSU, SDG&E and LADWP. State
   of California accounts are a different rep. Substituting the correct address
   would have passed the gate silently, because the gate checks that registered
   wording is not superseded, not that the right person is printed. It needed a
   new, state-scoped registry row.
5. **A contract number conflict the gate could not see.** `7-25-51-02.03` is the
   registry value and the number CAL FIRE buyers cite themselves.
   `7-18-51-02.18`, printed on the Branding Guide business card, is not registered
   as superseded, so nothing would have flagged it.
6. **No written vendor authorization to advertise a discount on branded product**,
   required by COMPLIANCE 5.1. The rep's email authorized quoting the pricing.
   That is a different permission.
7. **Manufacturer mark rows still `NEEDS CONFIRMATION`** in the assets ledger. The
   marks shipped on a verbal authorization from the owner, recorded in the README
   with a name and a date as the permission of record, with the README stating
   plainly that the ledger still needed updating.
8. **16W483 had no price on the sheet.** One line, and it still had to be either
   priced or omitted rather than quietly dropped.
9. **Two named contacts were escalating late orders** as of 2026-08-27, one on 100
   backordered helmets with no ETA. Both went on a do-not-send list. A promotional
   email into a live backorder escalation costs more than the campaign earns.

## The availability answer, and why it constrained the copy

Fifteen items were checked at quantity 10 into ZIP 95811 on the day of render. The
API returned: "First shipment arrives on Mon. Aug 31, balance on or before Fri.
Oct 30." Three of the fifteen could not fill quantity 10. No Northern California
branch could fill the basket for pickup.

The API returns arrival dates. It never returns the phrase "next day". So no piece
in the campaign claimed next-day delivery, and the README says so explicitly in a
sentence beginning "Therefore", which is what turns a check into a copy
constraint that survives three more drafts.

## The owner decisions

Several defaults in COMPLIANCE.md were overridden by the owner, in session, with
the concern raised and reaffirmed. They are recorded that way in the README so the
distinction between a rule broken and a rule overridden by the person entitled to
override it is legible later:

- The CAL FIRE mark placed on the piece as a hero chip, never locked to the BBS
  wordmark, disclaimer verbatim in the footer.
- The NASPO ValuePoint mark placed as a credential badge with its ledger row still
  unconfirmed.
- SDVOSB wording removed sitewide as federal-only.
- The one-ask rule ruled inapplicable to this landing page specifically: a
  transactional page whose job is quote building is a different piece type from a
  flyer, and it carries the asks the transaction needs. The rule still bound every
  email in the campaign, each of which carried exactly one ask.

## The shape of the effort

Ninety-two parsed lines produced one page. The work was: verify the price twice,
verify the product against its own item number, verify what the agency actually
buys, verify what may legally be said about any of it, and then build. The
building was the short part.

Which is the transferable lesson. If you are three hours in and have a beautiful
page and an unverified sheet, you have a beautiful page that cannot be sent.
