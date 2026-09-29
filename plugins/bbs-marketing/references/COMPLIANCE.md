# Compliance

These rules bind every published piece in every channel — print, email, landing page, slide, booth graphic. They were
written for email, were never applied to print, and both shipped print leave-behinds are missing the required
independent-supplier disclaimer as a direct result. **A rule here is not satisfied by having satisfied it in another
channel.** Facts come from `references/CLAIMS.md`, worded exactly as its `approved wording` column states: the registry
governs *what a claim says*, this file governs *whether and how* it may be made.

## 0. Scope: internal versus customer-facing

Every rule in this file is written for **customer-facing** pieces — anything that reaches an
agency buyer, a supplier, a partner, or the public. Sections 1 through 9 apply to those in full.

**Internal-only pieces are exempt from the agency-mark and third-party-mark restrictions**
(§1.2 and §7.1). Approved by Parker Marshall, 3 September 2026.

A piece is internal-only when **all** of these hold. Fail any one and it is customer-facing:

1. Its audience is BBS employees and contractors, and no one else.
2. It is not sent to, handed to, shown to, or shared with anyone outside BBS, and it is not
   published, posted, or linked from anywhere a non-employee can reach.
3. It carries no offer, no price a customer could act on, and no call to action aimed outward.
4. It is labelled internal on its face.

Examples that qualify: sales playbooks and territory guides, account handover documents, the
kickoff deck, market and competitive analyses, training material, internal dashboards.

Examples that do not, whatever they are called: anything a rep forwards to a buyer, a
"leave-behind", a landing page, a promotion sheet, a quote packet, a capability statement.

**What stays true even internally.** The exemption is narrow — it lifts the *permission* barrier
on marks, not the honesty rules. On an internal piece you still never state or imply agency
endorsement (§1.1); never redraw, recolor, restyle, or distort any third-party mark (§7.2);
never lock a third-party mark to the BBS wordmark to form a new combined logo (§7.2); and never
present a manufacturer or agency mark as an endorsement of BBS (§7.3). Certification claims
(§2), contract references (§3), and MAP and pricing rules (§5) apply everywhere without change,
because a rep who learns a wrong claim internally repeats it externally.

**The reclassification rule.** The moment an internal piece is sent outside BBS it becomes
customer-facing retroactively, and every restriction applies to it as published. If there is any
prospect a document will be forwarded to a buyer, build it to the customer-facing standard from
the start. When in doubt, it is customer-facing.

## 1. Agency marks and endorsement

1. Never state or imply that an agency, department, or campus sponsors, endorses, approves, or is affiliated with Black
   Box Safety, or that a purchase is official or required.
2. Never put an agency name, seal, badge, patch, uniform, vehicle, or facility image in a headline, logo lockup, product
   name, domain, subject line, or code name. An agency name appears only as plain body text identifying who the piece
   addresses or who BBS supplies. **Internal-only pieces are exempt** — see §0. On an internal piece an agency seal may
   sit in a section header or beside its agency's data, because there is no audience to mislead about endorsement. The
   mark is still never redrawn, recolored, or locked to the BBS wordmark.
3. **CA Vehicle Code § 2262** restricts use of "California Highway Patrol" or "CHP" in connection with a business in any
   manner reasonably construed as implying association with or approval by the CHP. Treat every agency the same by
   default; verify the current statutory text before quoting the statute itself.
4. **The independent-supplier disclaimer is required on print as well as email.** Registered as `agency-disclaimer`,
   presence `required`, scope `agency`, it reads exactly:

   > Black Box Safety is an independent supplier. This offer is not sponsored by, affiliated with, or endorsed by [agency].

   Complete it with the agency's name. Never reword, shorten, or swap "offer" for another noun at build time — if the
   exact wording reads wrong on a piece type, that is a registry change with a named owner.
5. `--scope agency` applies whenever a piece names an agency, carries an agency mark, addresses agency personnel, or is
   handed out at or for that agency — nearly every BBS piece. Run the gate at the track scope *and* `agency` unless the
   project README states why `agency` does not apply.

## 2. Certification claims

1. Registered wording only, reproduced exactly, and one channel on the piece. A California piece
   prints `dvbe-cert`. A federal or prime piece prints `sdvosb` or `sdvosb-full`. `vosb` is federal
   and unclaimed unless the audience is a VOSB set-aside. UEI `FRK5MJD35GN5` is a federal identifier.
   Do not print a California credential and a federal credential on the same piece.
2. **DVBE is a California state certification** issued by CA DGS. **SDVOSB and VOSB are federal certifications** issued
   by the SBA. Different programs, different governments; neither confers anything on the other.
3. Conflating them is a live error already in the field. Never write "nationally certified DVBE," "federally certified
   DVBE," or any equivalent. Never credit the VA or the CVE for a veteran-owned certification — the SBA certifies, and
   the VA's CVE stopped certifying in January 2023.
4. Never claim a certification confers preference, set-aside eligibility, or an award. State only the mechanism: it lets
   a buying agency's spend count toward a participation goal.
5. Any percentage, dollar, or goal figure attached to a certification needs its own registry row before it prints — the
   3% DVBE goal figure is not yet registered. Rows carry expiries; a piece rendered past one fails the gate, so
   re-verify with the owner rather than re-render.

## 3. Contract and vehicle references

1. Cite only a vehicle BBS is actually on, and only from `references/CLAIMS.md` — never from an existing piece, a vendor
   deck, or a prior PDF. Name the awarding body beside the number: `C-CSUCO-00001768` (CSU Grainger Agreement) ·
   `1-23-84-07` (CA DGS statewide body armor LPA) · `091422-WWG`, `091924-BBS` (Sourcewell) · `7-25-51-02.03` (NASPO
   ValuePoint LPA) · `2018-000207` (OMNIA Partners) · `PS25650` (NPPGov) · `Grainger Authorized Tier 1 Diverse Reseller`
   (Grainger Distributor Alliance).
2. Respect scope: MRO vehicles never appear on a `public-safety` piece, armor vehicles never on an `mro-procurement`
   piece; on a bridge piece each column carries only its own. Never imply a vehicle is exclusive, obligates the agency
   to buy, or is held by BBS alone unless the awarding body's own documentation says so.
3. No federal contract number prints. The GSA number carried in the retail kit has no registry row.

   NEEDS CLAIM: GSA contract 47QSWA23D000Y — awarding schedule, SIN coverage, current status, and the exact rendering
   permitted on a piece.

## 4. Gift and ethics (FPPC)

1. Any discount, promotion, or courtesy offered to public employees must be **modest** and **class-wide** — same terms
   for every member of a defined class (e.g. all sworn officers) — and framed that way in the copy.
2. **Never** extend an individual, enhanced, early, or one-off offer to procurement staff, equipment-unit personnel,
   contract administrators, or anyone who influences a BBS award. A gift-reporting problem for a buyer ends the account,
   not just the campaign.
3. No gifts, meals, tickets, prizes, giveaways, raffles, or sample retention offered to procurement or equipment-unit
   personnel in any piece. A scan-to-enter drawing at a vendor fair is an individual benefit.

## 5. Vendor MAP and pricing

1. Confirm vendor authorization in writing before advertising any discount on branded product, and record the
   confirmation in the project README.
2. Honor MAP: show MSRP and put the discount behind a code or a quoted price where MAP requires it. Never advertise
   below a manufacturer's own published price.
3. Verify price, lead time, and availability the day the piece renders, with the date in the README. Never frame a
   made-to-order or backordered item with buy-now urgency — state the wait plainly.

## 6. CAN-SPAM and consent

1. Every commercial send carries a working unsubscribe link and the physical postal address `1950 Cordell Ct., Ste 103,
   El Cajon, CA 92020`. Honor an unsubscribe company-wide across every list within 10 business days.
2. Subject, preview text, and from-name must not misrepresent sender or content. The sender is Black Box Safety — never
   an agency or a program name that reads as one. Send only to profiles with verified marketing consent; a transactional
   purchase is not consent.
3. **Duty email addresses at an agency domain are verification intel, not send targets.** Use them to confirm employment
   and route the relationship; send marketing to a personal address. Where no personal address exists, a duty address
   may receive only the driest informational variant, with the reason in the README.

## 7. Third-party marks

1. Every non-BBS mark — agency, campus, cooperative, distributor, manufacturer — used on a **customer-facing** piece
   requires a row in `references/ASSETS.md` giving rights holder, permitted context, permission of record, and lockup
   constraints. **No row, no use.** `ASSETS.md` now exists; a mark without a row still does not ship externally.
   **Internal-only pieces are exempt from the row requirement** (see §0) — they may use any mark in
   `brand/assets/logos/` or `bbs-customer-bots/public/brand/logos/`. Rows should still be written for those marks so the
   ledger stays complete and the mark is ready when a piece goes external.
2. Use only approved source art from `brand/assets/logos/`; never pull a mark from a website, deck, old PDF, or search
   result, and never redraw, recolor, or restyle one. Never lock a third-party mark to the BBS wordmark to form a new
   combined logo — co-brand lockups are approved artifacts, governed per track, and are Tier B.
3. Marks are not endorsements. A manufacturer logo strip states what BBS distributes; it may not sit under a headline
   that reads as that manufacturer's recommendation.

## 8. Required footer elements by piece type

"Disclaimer" means the exact `agency-disclaimer` wording, required whenever `--scope agency` applies.

| Element | Print leave-behind | Sell sheet | Email | Landing page |
|---|---|---|---|---|
| BBS wordmark, approved rendering | required | required | required | required |
| Legal entity name `Black Box Safety, Inc.` | required | required | required | required |
| Credential line (registry wording) | required | required | required | required |
| Contact block — person, address, email | required | required | required | required |
| Physical address, full | required | required | required | required |
| Independent-supplier disclaimer | required | required | required | required |
| Vehicle numbers with awarding body | required | required | as used | as used |
| Third-party mark attribution per `ASSETS.md` | as used | as used | as used | as used |
| Unsubscribe link | n/a | n/a | required | n/a |
| Consent/preferences link | n/a | n/a | required | as used |
| Price/availability verification date | as used | as used | as used | as used |

Legal and credential lines never set below 6.5 pt; body never below 9 pt print / 14 px screen. Footers are live text —
anything set as artwork is invisible to the gate.

NEEDS CLAIM: public phone number for the contact block — two appear in sources, neither registered, so none prints.

NEEDS CLAIM: web address for the contact block.

## 9. Two-tier approval

**Tier A — the rep ships it, no human gate.** All five must hold: every fact is an existing `references/CLAIMS.md` row,
unexpired and in scope; every mark has a row in `references/ASSETS.md`; every named reference customer is already
cleared and named on a shipped piece; the piece is assembled from existing blocks and an existing template, with no new
layout and no new lockup; and `brand-check` is green at every applicable scope.

**Tier B — named sign-off recorded in the project README before render.** Triggered by any one of: a new claim · a new
named reference customer · a new agency mark or co-brand lockup · new certification wording · any piece for an agency
BBS has not published to before. Record it as `approved-by:` with a person's name and the date. "Approved" with no name
is not an approval. Sign-off is per piece and does not carry to the next one.

## 10. The blocking gate

No PDF renders and no preview link goes to anyone — rep, customer, or agency — until `brand_check.py` passes clean at
every applicable scope and its output is pasted into the project README.

```
python3 tools/brand_check.py <rendered-piece> --scope <track> --scope agency
```

- Audit the rendered artifact, not the source template. For a PDF run `pdftotext` first. A bridge piece is audited at
  `--scope mro --scope public-safety --scope agency`. A missing `track:` in the README is a failure, not a default.
- Green is not a substitute for §§1–9. The gate reads wording; it cannot see an implied endorsement, an ungoverned
  discount, an unlicensed mark, or a missing signature.
- Never edit `CLAIMS.md` to make a failing piece pass. Registry changes are Tier B, made deliberately and before the
  build.
