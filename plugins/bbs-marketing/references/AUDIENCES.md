# Audiences

Who Black Box Safety sells to, and what each buyer needs to hear. Read before choosing a track in
`tracks/ROUTING.md` and before writing copy. This file decides the argument; every factual assertion
on a published piece still comes from `references/CLAIMS.md` in its exact approved wording. Distilled
from the 06/2020 buyer-persona and target-market decks in `sources/` — see "What we retired."

## Target market

California public agencies that spend against already-competed vehicles and carry supplier
diversity goals. A good-fit account already buys through a vehicle BBS can ride and has a diversity
goal it is not hitting; vehicle access matters more than agency size.

- **CSU and UC campuses** — facilities, EH&S, campus police, central procurement
- **Municipal utilities** — water, power, wastewater districts
- **Cities and counties** — public works, fleet, parks, general services
- **State departments** — the largest pool, and where DVBE participation is scored and reported
- **Law enforcement** — state, county, municipal, and campus agencies
- **Health systems** — public hospital districts and campus health services

How the money moves, and why the personas split the way they do: an end user sends a spec to a
contracting office, which picks a vendor from an approved list and awards through a p-card, a
sole-source set-aside to a diverse supplier, the rule of two, or an open solicitation. **The person
who wants the item and the person who can buy it are almost never the same person.** Most pieces
have to reach both.

## Personas

**Requisitioner** — `mro-procurement`
- Accountable for getting today's order placed, nothing else. Says no when it looks like a new
  login, form, or phone call. Moved by: same punchout, same cart, one different vendor tile.
- **Do this:** lead with the click, never the policy. One instruction, one QR, one screenshot of the
  tile to select. Do not explain DVBE to this person — they did not ask and it reads as extra work.
  Punchout switch card is the native format.

**Procurement officer** — `mro-procurement`
- Accountable for a defensible award and the agency's diversity participation goal. Says no when
  the file would be thin under audit, when a price premium appears, or when the supplier reads as a
  pass-through instead of a supplier.
- Moved by: a contract number they can paste into the file, an already-competed vehicle, reportable
  spend, no premium. `C-CSUCO-00001768`, `7-25-51-02.03`, `2018-000207`, `091422-WWG`,
  `CA DVBE Cert. 2009473`.
- **Do this:** compliance is the hero — vehicle table and credential line above the fold. Obey the
  partnership rule absolutely; pass-through language loses this buyer faster than anything else.
- *NEEDS CLAIM: the mandated DVBE participation goal figure. The wedge turns on it and it still
  cannot be printed.*

**Facilities manager** — `mro-procurement`
- Accountable for uptime and a budget that does not move. Says no when switching implies delivery
  risk, or when "who do I call when it's wrong" is unclear.
- Moved by: same catalog, same price, same delivery, a named human who answers. The
  four-green-checks-against-one-change block was built for them.
- **Do this:** lead with nothing changes. Spend the space on continuity, not savings — they do not
  keep the savings. Put a name and a direct contact on the piece.

**Equipment unit / quartermaster** — `public-safety`
- Accountable for fit, certification, issue records, stock, and the paperwork behind every item
  that goes out the door. Says no when sizing coverage is vague, lead times are optimistic, or
  warranty handling is unstated. This buyer has been burned by a backorder and remembers it.
- Moved by: spec grids, fit coverage, honest lead times, one reorder path, pricing that needs no
  re-competing. `1-23-84-07`, `091924-BBS`, `PS25650`.
- **Do this:** specs, not benefits. Say the model, the level, the fit, the lead time. Never send
  urgency copy into a backorder — long-lead items read "made to order, reserves ship in order
  received."
- *NEEDS CLAIM: NIJ certification wording for armor, plates, and carriers. This persona's single
  most important proof point has no registry row.*

**Chief / command staff** — `public-safety`
- Accountable for officer safety, budget defensibility, audit exposure. Says no when the buy cannot
  be shown to have been competed, or when the vendor is unknown to peer agencies.
- Moved by: one paragraph, the contract vehicle, named agencies already supplied.
- **Do this:** one page, contract numbers, no procurement theory. Resist explaining DVBE mechanics —
  that argument belongs to the other track, and here it makes BBS sound like a broker rather than an
  equipment supplier.
- *NEEDS CLAIM: named agency precedent usable in published copy. Peer proof is the strongest move
  available to this persona and there is no registered wording for it.*

**Individual officer** — `public-safety`, plus `--scope agency` when an agency is named
- Accountable for their own kit, on their own money or an allowance. Says no when the price is not
  real, the item is not in stock, or the copy performs at them. This reader proofreads and spots
  tactical cosplay instantly.
- Moved by: "we supply your department's gear," plain specs, real availability, officer pricing.
- **Do this:** product, price, lead time, nothing else. No warrior framing, no thin-line imagery, no
  exclamation points, and never the phrase "End of Watch." The `agency-disclaimer` wording is
  required verbatim on any piece that names an agency.

## The officer-retail segment

The B2G to retail motion. Winning an agency contract to supply issued equipment also creates
something the contract does not capture: a cohort of individual officers who know the brand, have
handled the product, and buy personal gear with their own money. The agency sale is the
introduction; the retail sale is the annuity.

1. **The agency contract is never leveraged in the pitch.** No enhanced or individual offer to
   procurement or equipment-unit personnel, and no gear, samples, or pricing to the person who
   decides the award. FPPC ethics, not a preference.
2. **Discounts stay class-wide** — "officer pricing," open to all officers, behind a code.
3. **Segment by product, then behavior.** The live segments are built from the agency program
   bundle's product IDs, which makes them a clean proxy for officers at an agency we supply.
4. **One split dimension per send.** Recent buyers get kit-completion tone while the gear mindset is
   hot; dormant buyers need news, not coupons; repeat customers get a plain signed note.
5. **Verified-sworn signal is intel, not a send list.** An official agency address confirms who
   someone is; send to their personal address. And CAN-SPAM applies — these are transactional
   customers, not subscribers, so only the consented segment is sendable, with unsubscribe link and
   physical address in every send.

### Segment snapshot — dated, not standing fact

Live registry: `../claude-marketing/shopify-retail-upsell/segments/SEGMENTS.md`. Its counts were
**captured 2026-08-10** and read into this file **2026-08-13**. Order of magnitude at that capture:
roughly 1,500 total buyers in the agency carrier program, about 1,380 marketing-consented and
sendable, about 430 having purchased in the prior 90 days, about 113 repeat customers.

**Treat all of those as expired.** Membership rolls forward on relative recency windows and totals
drift weekly. Re-query `customerSegmentMembers(segmentId: ..., first: 1) { totalCount }` and stamp
the date before any campaign decision or forecast. Never quote a segment count in published copy.

*NEEDS CLAIM: naming a specific agency as a department BBS supplies, for published copy. The segment
registry names one internally; that is an operational record, not registered wording, and the
agency-disclaimer requirement applies the moment a name appears.*

## What we retired, and one source warning

The 06/2020 decks were built for a different company. Not carried forward:

- **"Jarad, Diversity Manager"** — a single composite persona with gender, income band, Myers-Briggs
  and DISC scores. BBS does not sell to one person; it sells to a requisitioner who wants the item
  and a contracting officer who can buy it, and demographic profiling bears on neither. What
  survived is the objection intel underneath: *"they shouldn't have to buy from a disabled veteran
  just because they are a disabled veteran."* That is why every piece leads with the vehicle and
  price parity, and lets the certification close rather than open.
- **The Minnesota footprint** — hot spots split California/Minnesota and a trade-show list that is
  majority Minnesota and national. Today's market is California public agencies.
- **Private-sector accounts** — "large private corporations," telecom and utilities as commercial
  buyers. Both tracks now address public agencies.
- **Training as a revenue line**, the 2020 revenue and margin table, pre/post-COVID payment terms,
  the 2019–2021 site-visit goals, the named competitor, and PPE market sizing from 2015–2016
  forecasts running to 2024. Internal, stale, or expired.
- **"Call our sales team, we will answer 24/7."** Unregistered service claim. Do not print it.

Surviving intact: the government buyer's journey and its four award paths, and the observation that
agencies generally cannot buy through consumer marketplaces but do hold Grainger contracts at local,
state, and federal level. That second point is the foundation the MRO wedge stands on.

**Source warning — the retail kit.** `claude-marketing/shopify-retail-upsell/` contains ungoverned
and superseded material. Do not carry forward the GSA contract number that appears there (a federal
vehicle with no registry row and its own claim rules), its rendering of the DVBE certification, or
the contact address in its footers — both are registered as superseded in `references/CLAIMS.md`, which
carries the approved wording. Take segment structure and campaign mechanics from that kit; take no
facts from it.
