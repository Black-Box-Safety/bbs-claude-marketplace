# Project README template

Copy this to `programs/<YYYY-MM-DD>-<agency>-<campaign>/README.md` and fill it in
**before** you build anything. The README is not documentation written after the
fact. It is the record that makes the piece shippable: the gate output lives here,
the Tier B signature lives here, and the permission of record for every borrowed
mark lives here.

Each section below carries a short parenthetical saying why it exists. Read those
before deleting a section that looks like bureaucracy. Every one of them is here
because its absence cost something on a real build.

Replace every `<PLACEHOLDER>`. A placeholder left in the file is an unanswered
question, not a formatting slip.

---

```markdown
---
track: <mro-procurement | public-safety | bridge>
tier: <A | B>
approved-by: <Person Name, YYYY-MM-DD | PENDING>
date: <YYYY-MM-DD>
---
```

(Frontmatter. `track:` decides how the piece is dressed and argued and which gate
scopes apply. A missing `track:` is a failure, not a default. `approved-by:` with
no name is not an approval, so "PENDING" is the honest value until someone signs.)

# <Agency> <period> <campaign name>

## Why this piece exists

<Who asked for it and what changed to make now the moment. Name the rep or the
event: a priced sheet arriving, a contract renewal, a vendor fair date. Then the
commercial logic in two or three sentences: what the agency already buys, through
what channel today, and what routing it through Black Box Safety changes.>

(This is the section that stops a campaign being rebuilt from scratch in six
months. It also catches the campaign that has no reason to exist, before the
photography does.)

## Intake

| Field | Answer |
|---|---|
| Requester | <name, role> |
| Agency | <full legal name, plus SCPRS business unit if known> |
| Persona | <which persona in AUDIENCES.md, and the real job titles it maps to here> |
| Piece type | <landing page, HTML email, plain-text rep variant, priced PDF leave-behind> |
| Where it is seen | <email to named buyers, page linked from that email, handed out at X> |
| Single ask | <one action per piece. If the project has several pieces, one line each.> |
| Track | <mro-procurement, public-safety, or bridge> |
| Gate scopes | <--scope mro --scope agency> |

(Intake answered in writing, from the requester, not from assumption. The fact
check happens here: every fact the piece needs gets checked against
`brand/CLAIMS.md` at intake, so an unregistered fact is a blocker you raise on day
one rather than discover at render.)

## Segments

Sized from the SCPRS warehouse, business unit <NNNN>, on <YYYY-MM-DD>.

| Segment | Definition | Buyers | Spend | Slice | Window |
|---|---|---|---|---|---|
| A | Buys the prime direct, no BBS purchase history | <n> | $<n> | <MRO-prime direct> | <date to date> |
| B | Buys these categories from other suppliers, no BBS history | <n> | $<n> | <SB/DVBE-visible> | <since date> |
| C | Buys those categories elsewhere, has BBS history | <n> | $<n> | <SB/DVBE-visible> | <since date> |

Context totals, same date: <agency> <prime>-direct spend <FY range> is $<n> across
<n> buyer names (<slice>). Black Box Safety is <rank/standing> at $<n> across <n>
buyer names, last PO <date>.

Segment C named, highest first: <name $n; name $n; ...>

(Every number carries its corpus slice and its window. The warehouse holds two
deliberate slices of SCPRS and neither is the market or the agency's whole spend.
An unlabelled total is the one number in this file most likely to be repeated in a
meeting, which is exactly why it must not be left ambiguous. Segment C is usually
tiny and is the most valuable list in the campaign, because those are warm
relationships that have gone quiet.)

## Source data

- `data/<source-file>.pdf`: <who sent it, when, what it is authoritative for>.
  <n> line items with prices, <n> categories.
- `data/hotlist_official.csv`: parsed from that PDF.
- <Any unpriced twin or XLSX version, named explicitly as not used for pricing.>

Where the priced sheet and the live account price disagree, the piece prints the
LOWER of the two, per <owner> decision <date> (account price used on <n> of <n>
lines). Confirmed against account <number> (<facility>, <schedule>, sell rule
`<rule>`) on <date>:

| Item | Sheet | Account price | Note |
|---|---|---|---|
| <item> | $<n> | $<n> | <sheet lower / account lower, raise with rep> |

(Naming the unpriced twin matters: the two files look identical in a folder and
pricing off the wrong one is silent. The account-versus-sheet table is what the
rep needs to see, because a cheaper account price means the negotiated sheet has a
gap in it.)

## Blockers

1. **<Blocker in bold.>** <What is wrong, what would fix it, who owns the fix.>
2. <...>

(Written as a numbered list so they can be referred to by number in a message to
the owner. A blocker recorded here is a blocker someone can close. A blocker held
in someone's head becomes a shipped error.)

## Vendor authorization

<Which marks and imagery, authorized by whom, how, on what date, on what basis.
State plainly whether this is written authorization or a verbal authorization
recorded here as the permission of record.>

Written vendor authorization for advertising a discount on branded product,
required by `COMPLIANCE.md` §5.1, <is on file, dated X | is NOT yet on file>.
<Note the difference between authorization to quote pricing and written
confirmation to advertise a discount percentage. They are not the same permission.>

`brand/assets/ASSETS.md` <carries these rows as NEEDS CONFIRMATION and should be
updated deliberately rather than left contradicting this file>.

(No row in ASSETS.md, no use, including marks already sitting in the logo folder.
When a mark ships on a verbal approval, this paragraph is the only record that the
approval happened, and the only thing that will be found if it is ever questioned.)

## Price, lead time and availability verification

- Prices verified <date> against <source> dated <date>.
- Availability checked <date> via <method>, <n> items at qty <n> into ZIP <n>.
  The API returns arrival dates and never returns the phrase "next day". Result:
  "<verbatim message>". <n> of <n> could not fill the quantity. <Branch pickup
  result.>
- Therefore <what the pieces may and may not claim about delivery>.

(COMPLIANCE §5.3 requires the verification date. The "therefore" line is the point
of the section: it converts a check into a copy constraint, so nobody writes
"ships next day" three drafts later.)

## Data corrections applied

Errors found in the source sheet, checked against <the product API> on <date>:

| Item | Sheet says | Actually is |
|---|---|---|
| <item> | <sheet description> | <real product, or real pack size, or real status> |

(Sheets are shorthand typed by a human and they carry transcription errors. These
are recorded rather than silently corrected so the rep can tell the vendor, and so
the next person does not "fix" the correction back to the sheet's version.)

## Do not send

<Named contacts excluded from the campaign, with the reason and the date.>

- <Name, unit. PO <n>, <what is late>, <status>.>

(Someone escalating a backorder gets a status email, not a promotion. This list is
cross-checked against Business Central for open quotes, stale accounts and live
escalations before any send. It is the cheapest goodwill protection in the file.)

## Timing

<Anything dated that changes the CTA or the route: a portal going live, a fiscal
year boundary, a contract renewal, a fair date.>

(A CTA that says "reply for a quote" can be made wrong by a portal launch two days
after the send. Writing the date here forces the recheck.)

## Approval

Tier <A | B>. Triggered by: <new claims, a named reference agency, a new mark or
lockup, new certification wording, or first publication to this agency>.

`approved-by:` <Person Name, YYYY-MM-DD | PENDING>

(Tier B needs a person's name and a date before render. Sign-off is per piece and
does not carry to the next one.)

## Owner decisions, <YYYY-MM-DD>

<Owner name> confirmed in session, overriding the defaults in COMPLIANCE.md where
noted:

- <Decision, what it overrides, and whether the concern was raised and reaffirmed.>

(This section is the difference between a rule that was broken and a rule that was
overridden by the person entitled to override it. Record the override, what it
departs from, and that the concern was actually put to them.)

## Gate

Run <date> on the rendered artifact:

```
$ python3 tools/brand_check.py <path-to-rendered-piece> --scope <track> --scope agency
<pasted output>
exit=<n>
```

Manual checks the gate cannot do, also passed <date>: <zero em or en dashes in the
rendered page and every email file; no agency name in any subject line; the
manufacturer logo strip under a descriptive label rather than a headline; contact
email matches the registry row>.

<Note which files are source rather than rendered sends, and that the gate must be
re-run on final merged bodies before any send.>

(The gate output is pasted, not summarised. Green is not sufficient: see
`references/compliance-checklist.md` for what it structurally cannot see.)

## Deployed

Production: <URL> (project `<name>`, no agency name in the domain per
COMPLIANCE 1.2). Deployed <date>.

<What the deployed page includes, and anything verified on the deployed URL rather
than locally: images loading, short paths returning 200, the quote builder driven
once end to end.>

(Verification happens on the deployed URL. Local rendering hides broken absolute
image paths and rewrite rules, which is exactly the class of bug an emailed link
exposes to the customer first.)
