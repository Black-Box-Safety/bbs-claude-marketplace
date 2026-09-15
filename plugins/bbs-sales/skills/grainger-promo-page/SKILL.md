---
name: grainger-promo-page
description: Build a Black Box Safety product promotion landing page for a California public agency from a Grainger negotiated hot list or price sheet, with live pricing, product photography, a quote builder, SCPRS-sized buyer segments, and the brand compliance gate. Use this skill whenever a Grainger rep sends a priced sheet or hot list for an agency, whenever someone asks for a promo page, contract sheet, product landing page, punchout promo, or campaign page for CAL FIRE, CDCR, DWR, CHP, Caltrans, CalVet, a CSU or UC campus, or any other California agency, and whenever someone says they want to promote Grainger items or a hot list to an agency by email or web. Also use it when asked to price a list of Grainger item numbers for an agency account, or to segment an agency's buyers for a campaign.
---

# Grainger promotion landing page

Turn a Grainger negotiated price sheet into a landing page an agency buyer can actually
order from, plus the buyer segments to send it to.

The pattern this skill encodes: an agency already buys these items, usually direct or from
a competitor. Routing the same items at the same contract price through Black Box Safety
turns that spend into reportable diversity participation. The page's job is to make the
list concrete (real prices, real photos, real availability) and to let a buyer assemble a
quote without typing an email.

## Ground rules that outrank everything else

Read `../../../CLAUDE.md` and `../../../brand/VOICE.md` before writing any copy. The
non-negotiables that bite hardest on this piece type:

- Every fact comes from `brand/CLAIMS.md` in its exact approved wording. If it is not
  registered, write `NEEDS CLAIM: <description>` and stop. Never edit the registry to make
  a piece pass.
- No em dashes or en dashes anywhere. This is the single most reliable AI tell and the gate
  cannot see it, so check with grep.
- Sentence case headings. No exclamation points. No agency name in a subject line, a
  domain, or a headline.
- Grainger is never the subject of a verb that serves the customer. Write "Black Box Safety
  delivers, backed by Grainger's national distribution network," never "Grainger ships."
  This is a compliance rule about not reading as a pass-through, not a style preference.
- The `agency-disclaimer` wording is required verbatim on any piece naming an agency.
- No delivery-speed claim unless the availability API literally returned it. It returns
  arrival dates, not "next day."
- No discount percentage in copy without a registered claim row. Showing list price beside
  contract price per item is product data and is fine; a "save 42%" banner is a claim. If
  you ever do compute a headline discount figure, say which of two honest numbers you used:
  spend-weighted (total contract price over total list price) and the mean of the per-line
  percentages differ, sometimes by two points or more, and printing one without saying which
  invites the reader to assume the other.

## Workflow

### 1. Intake, before you build anything

Write the project README first, at `programs/<YYYY-MM-DD>-<agency>-<campaign>/README.md`,
with `track:` in frontmatter. `references/readme-template.md` has the structure that has
survived a real build. A missing `track:` is a failure, not a default.

Record in it: who asked, which agency, the persona, the single ask, the gate scopes, and
the date price and availability were verified. You will paste the gate output here later.

### 2. Get the pricing straight

The priced sheet is the authority, but verify it rather than trusting it. Two failure modes
have both happened:

- **The sheet has no prices.** A rep may send an item list and a priced version separately.
  Extract with `pdftotext -layout` and grep for `$`. If there are none, ask for the priced file
  before going further.
- **The sheet is not actually the lowest.** Price every item against the agency's own
  Grainger account with `grainger_price` (the `account` parameter is required and per-account
  discounts differ). Compare. On the last build the sheet beat the account on some lines and
  lost on fourteen others. Print the lower of the two and tell the rep about the gap, because
  "lowest when you quote" is usually what the rep promised.

Also check the sheet's footer for a pricing term. An expired or missing term is a blocker to
raise, not a number to invent.

`scripts/price_hotlist.py` does the parse, the batch pricing, the comparison, and writes
`data/hotlist.json`. Run it with `--help` for arguments.

### 3. Sanity check the items

Sheets carry transcription errors. Compare each API description against the sheet
description and flag mismatches for a human: wrong item numbers (a degreaser that prices as
wire rope), wrong pack sizes, items unavailable for 30+ days, and images that show the wrong
variant. Put them in the README under "Data corrections applied." Do not silently correct.

### 4. Size the audience from SCPRS

This is what makes the campaign more than a mailshot. Using the SCPRS warehouse
(`explore_sql`), find the agency's business unit, then build three segments:

| Segment | Definition | Wedge | Corpus slice |
|---|---|---|---|
| A | Buys the prime direct, no BBS history | Same items, same price, now the spend reports | mro_prime_direct |
| B | Buys these categories from other suppliers, no BBS history | Already competed, no solicitation to run | sb_dvbe_visible |
| C | Has BBS history but now buys elsewhere | Warm, individual, references the real relationship | sb_dvbe_visible |

A and B come from different corpus slices and their spend figures cannot be added into one
headline number. That is the easiest way to turn two correct queries into one wrong claim.
Segment C is usually tiny and the most valuable thing on the page. Read
`references/scprs-queries.md` for the queries and the denominator rules. State which corpus
slice every number comes from; the warehouse holds two and they are not the market.

Cross-check against Business Central for open quotes, stale accounts, and anyone currently
escalating a late order. People with a backorder problem get a status email, not a promo.
Put them on a "Do not send" list in the README.

### 5. Build the page

`scripts/build.py` renders `assets/page-template.html` from `data/hotlist.json`. Copy both
into the project's `web/` directory and run it. `price_hotlist.py --out` should point at that
project's `data/` directory, since that is where `build.py` looks for `hotlist.json`.

`build.py` carries five constants from the CAL FIRE build that are NOT agency-neutral and
need editing per campaign: `CAT_ORDER` and `CAT_NOTE` (the category list and their one-line
descriptions, since a different sheet may not use fire tools, PPE, batteries, jan/san, fleet,
misc), `HERO` (the twelve item numbers featured as hero cards, chosen per §5's ranking rule),
`BRAND_LOGOS` (the brand-substring to logo-file map, since a new agency's sheet has different
manufacturers), and the literal agency-name prefix in `build_units()` used to strip the
prefix off Business Central customer names before showing them in the unit picker.

What the template already gives you, so you do not rebuild it:

- Dossier hero with a lifestyle photo collage behind a gradient, contract chips, credential
  badges on white chips
- Manufacturer logo banner under a descriptive label ("Brands on this sheet"), which keeps
  it from reading as an endorsement
- Hero product cards ordered by what the agency actually reorders most, each with photo,
  contract price against list, and an add-to-quote button
- The full sheet as collapsible categories, searchable, with per-row product thumbnails and
  brand chips. Collapsed category headers must not be sticky or they stack on each other.
- A quote builder: add from any row, direct SKU entry with typeahead, unit picker that
  autofills the delivery address, localStorage draft, print-to-PDF on letterhead, mailto
  fallback
- Analytics hooks on the actions that matter commercially

Pull the agency's ship-to addresses from Business Central for the unit picker. Buyers abandon
forms when they have to type an address; a picker that fills it removes that.
`scripts/units_from_bc.py` does the query and writes `data/units.json`.

### 6. Imagery

Product shots come from the Grainger API `pictureUrl` field, re-requested at
`?wid=800&hei=800&fmt=png-alpha` for transparent PNGs rather than the default thumbnail.

Lifestyle photography comes from manufacturer domains via Firecrawl. Prefer in-use shots
over studio. Never use agency photos, and never use a photo showing agency uniforms, patches,
or badges, since that implies endorsement. Verify every download is a real image with `file`
and `sips`, because 403 pages save as valid-looking files.

Manufacturer marks need a row in `brand/assets/ASSETS.md` giving rights holder and permission
of record. Most rows sit `NEEDS CONFIRMATION`. If the owner authorizes use verbally, record
that authorization in the project README with a name and date as the permission of record,
and say plainly that the ledger still needs updating.

### 7. Optimize for how it will actually be opened

These pages get opened from an email, on a phone, and then forwarded to a buyer:

- Open Graph tags and a 1200x630 preview card, or the link renders as a bare URL in Outlook.
  `scripts/make_og.py` renders one with headless Chrome so it uses the real brand typeface.
- Short segment paths (`/a`, `/b`, `/c`) via `vercel.json` rewrites, clean in plain-text
  email, and read by the page to tag analytics events by segment.
- A forward-to-buyer link. In agency procurement the person who wants the item is almost
  never the person who can buy it, so a one-click forward carrying the link, the vehicle
  number, and the disclaimer is the highest-value CTA on the page.
- Favicon, canonical URL, and mobile: 44px touch targets, no horizontal body scroll, the
  quote panel as a bottom sheet.

### 8. Gate, then deploy

Run from the repo root, on the rendered artifact and not the template:

```
python3 tools/brand_check.py <path-to-index.html> --scope mro --scope agency
```

Green is not sufficient. The gate catches superseded wording, expired claims, and missing
required wording. It cannot see an implied endorsement, an unregistered discount claim, a
substituted contact email, an em dash, or anything set as artwork. Check those by eye and
by grep, then paste the gate output into the README.

Deploy with `vercel deploy --prod --yes --scope <team>` from a directory holding
`index.html`, `assets/`, and `vercel.json`. The Vercel MCP deploy tool fails on payloads
over about 100KB, so use the CLI. **The project name must not contain the agency name**,
since a domain is one of the places COMPLIANCE bars an agency name.

Verify on the deployed URL, not locally: check for broken images, confirm the short paths
return 200, and drive the quote builder once.

## References

- `references/readme-template.md` — project README structure with the intake table,
  blockers, do-not-send list, and gate output section
- `references/scprs-queries.md` — SCPRS segment queries and the denominator rules
- `references/compliance-checklist.md` — the pre-send checks the gate cannot perform
- `references/worked-example.md` — the CAL FIRE H2 2026 build, with the real numbers, the
  errors found in the source sheet, and what blocked the send

## What tends to go wrong

**Building before the pricing is settled.** The offer is the pricing. If the term is expired
or the sheet is unpriced, everything downstream is provisional.

**Trusting the sheet's product descriptions.** They are shorthand typed by a human. The API
descriptions are correct and far better for a rendered piece.

**Letting the discount story lead when the data does not support it.** Check where the deep
discounts actually are. On the last build they were in janitorial and fleet consumables, not
the signature wildland gear, and a campaign built on "deep discounts on fire gear" would have
died on contact with a buyer who knew the prices.

**Treating the compliance registry as an obstacle.** It exists because two shipped print
pieces carried a certification the company does not hold. When a fact has no row, the honest
move is to raise it, not to paraphrase around it.

**Printing the wrong contact email and not catching it.** `CLAIMS.md` may register a contact
email scoped to a different set of accounts than the one you are building for. Substituting
the correct rep's address passes the gate silently either way, since the gate only checks
approved and superseded strings, not which account a piece is for. This is invisible to a
careful proofreader who does not know the account map, so check it by hand every time.
