# Pre-send checklist: what the gate cannot see

`brand_check.py` catches exactly three things: superseded wording, expired claims,
and required wording missing for a scope you named. It reads live text only. That
leaves a large and well-populated space of failures that pass green.

Every check below has a reason beside it. Skipping a check whose reason you have
read is a decision. Skipping one because it looked like process is how two shipped
print pieces ended up carrying a certification the company does not hold.

Run these on the **rendered artifact**, after the gate, before anything reaches a
rep, a customer, or an agency.

## Line-level, by grep

- [ ] **Zero em dashes and zero en dashes**, in the page and in every email file.
      `grep -n "$(printf '\u2014|\u2013')" <file>` (or run the same two
      code points through python if your grep lacks alternation)
      The gate cannot see punctuation. This is the single most reliable AI tell in
      the piece, and this audience proofreads.

- [ ] **No banned words.** Check against the list in `brand/VOICE.md`.
      `grep -niE 'seamless|robust|unlock|elevate|empower|cutting-edge|state-of-the-art|best-in-class|world-class|industry-leading|game-changing|groundbreaking|innovative|one-stop shop|turnkey|streamline|leverage|peace of mind|trusted partner|rest assured|and more!' <file>`
      They read as filler to a procurement officer and as marketing to an officer.
      Neither reader is persuaded by either.

- [ ] **Sentence case in every heading.** Title Case On Every Word is a tell, and
      it is what the previously shipped pieces did.

- [ ] **No exclamation points.** A retail exclamation on a specialist audience
      costs credibility that the specifics were buying you.

## Agency name placement

- [ ] **No agency name in a subject line.** COMPLIANCE 1.2 lists subject lines
      explicitly. A subject naming the agency reads as an official communication
      from that agency, which is the endorsement problem in its most legally
      exposed form.

- [ ] **No agency name in the deployed domain or the project name.** Same rule,
      same reason. Check the Vercel project name as well as the URL, because the
      project name becomes the default domain.

- [ ] **No agency name in a headline, logo lockup, product name, or code name.**
      The agency name appears only as plain body text identifying who the piece
      addresses or who Black Box Safety supplies.

- [ ] **No agency seal, badge, patch, uniform, vehicle, or facility image** in any
      of those positions. This includes lifestyle photography: check the
      background of every photo for a patch or a decal, not just the subject.

## The disclaimer

- [ ] **`agency-disclaimer` present verbatim**, with the agency name filled in:
      "Black Box Safety is an independent supplier. This offer is not sponsored
      by, affiliated with, or endorsed by [agency]."
      The gate checks this only for the scopes you actually passed. If you forgot
      `--scope agency`, the gate is green and the disclaimer is missing. Confirm
      by eye that the scope was named, not just that the run passed.

- [ ] **Not reworded, not shortened, not "offer" swapped for another noun.**
      If the exact wording reads wrong on this piece type, that is a registry
      change with a named owner, made before the build.

- [ ] **Present per channel.** The rules were written for email and were never
      applied to print, which is why both shipped print leave-behinds are missing
      it. Satisfying a rule in one channel does not satisfy it in another.

## Grainger and pass-through framing

- [ ] **Grainger is never the subject of a verb that serves the customer.**
      `grep -niE 'grainger (ships|handles|delivers|fulfills|takes care|does)' <file>`
      Also catch: "we just process the paperwork", "Grainger ships and we
      collect", "pass-through", "we facilitate".
      This is a compliance rule, not a style note. Copy that describes Black Box
      Safety as a conduit describes an arrangement the contract does not permit.
      The correct construction: "Black Box Safety takes the order and delivers,
      backed by Grainger's national distribution network."

- [ ] **"Grainger Authorized Tier 1 Diverse Reseller" only**, in that exact
      registry wording. "an authorized reseller for Grainger", as printed on the
      MRO brochure, is superseded.

- [ ] **The manufacturer logo strip sits under a descriptive label**, such as
      "Brands on this sheet", never under a headline. COMPLIANCE 7.3: a mark
      states what Black Box Safety distributes and may not sit where it reads as
      that manufacturer's recommendation.

## Discounts, prices, and availability

- [ ] **No discount percentage in copy without a registered claim row.**
      Showing list price beside contract price per item is product data and is
      fine. A "save 42%" banner, a headline percentage, or an average-off-list
      figure is a claim and needs a row in `brand/CLAIMS.md`.

- [ ] **Written vendor authorization on file before advertising any discount on
      branded product**, per COMPLIANCE 5.1, recorded in the project README.
      Authorization to quote pricing is not authorization to advertise a
      discount. They are separate permissions and reps routinely conflate them.

- [ ] **No delivery-speed claim the availability API did not literally return.**
      It returns arrival dates. It does not return "next day", "fast", or "quick
      ship". Grep for those words.

- [ ] **No buy-now urgency on a made-to-order or backordered line.**
      `grep -niE 'order now|limited stock|act fast|while supplies last' <file>`
      Long-lead items read "made to order, reserves ship in order received". An
      urgency line into a backorder is the copy most likely to produce an angry
      call.

- [ ] **MAP honored.** Where a manufacturer requires it, show MSRP and put the
      discount behind a quoted price. Never advertise below a manufacturer's own
      published price.

- [ ] **Price, lead time, and availability verified the day the piece renders**,
      with the date in the README.

## FPPC gift rules

- [ ] **Any discount or courtesy is modest and class-wide**, framed that way in
      the copy: same terms for every member of a defined class. A class-wide offer
      that is not described as class-wide reads as an individual one.

- [ ] **No individual, enhanced, early, or one-off offer to anyone who influences
      an award**: procurement staff, equipment-unit personnel, contract
      administrators. A gift-reporting problem for a buyer ends the account, not
      just the campaign.

- [ ] **No gifts, meals, tickets, prizes, giveaways, raffles, or sample
      retention** offered to procurement or equipment-unit personnel anywhere in
      the piece. A scan-to-enter drawing at a vendor fair is an individual
      benefit, however it is framed.

## Third-party marks

- [ ] **Every non-BBS mark has a row in `brand/assets/ASSETS.md`** giving rights
      holder, permitted context, permission of record, and lockup constraints.
      No row, no use. This includes marks already sitting in
      `brand/assets/logos/`, and it includes manufacturer marks pulled off the
      Grainger product feed.

- [ ] **Most rows currently read `NEEDS CONFIRMATION`.** If a mark ships on a
      verbal authorization, that authorization is recorded in the project README
      with a name and a date as the permission of record, and the README says
      plainly that the ledger still needs updating.

- [ ] **Source art from `brand/assets/logos/` only.** Never pulled from a website,
      a deck, an old PDF, or a search result. Never redrawn, recolored, or
      restyled.

- [ ] **No third-party mark locked to the BBS wordmark.** A co-brand lockup is an
      approved artifact, governed per track, and is Tier B.

- [ ] **Lifestyle photography from manufacturer domains only**, verified as a real
      image with `file` and `sips`. A 403 page saves as a file with a plausible
      name and size, and it will silently render as a broken image on the
      deployed URL.

## Contact block and footer

- [ ] **The contact email matches its registry row.** `contact-email` registers
      `joey@blackboxsafety.com`. If the piece needs a different rep, that is a new
      registry row, not a substitution at build time.
      **The gate cannot catch this.** It checks that registered wording is not
      superseded; it does not know that the address printed is the wrong one for
      this account. This has to be read by a human every time.

- [ ] **Footer carries every required element for this channel.** From
      COMPLIANCE §8, for a landing page: BBS wordmark in approved rendering, legal
      entity name `Black Box Safety, Inc.`, credential line in registry wording,
      contact block with person and address and email, full physical address, the
      independent-supplier disclaimer, vehicle numbers with awarding body as used,
      third-party mark attribution as used, consent link as used.
      For an email, add: working unsubscribe link, and consent or preferences
      link, both required.

- [ ] **Footer is live text.** Legal and credential lines never below 6.5 pt
      print or 14 px screen. Anything set as artwork is invisible to the gate and
      is also invisible to a screen reader.

## Anything set as artwork

- [ ] **Read every contract number, credential, and disclaimer set as artwork by
      eye, character by character.** Badge lockups and logo lettering are images.
      The gate reads none of them. The body armor number on page 2 of the tactical
      brochure is a digit transposition that survived because it was artwork.

- [ ] **Check for a vehicle number conflict.** A number that appears on an old
      business card but is not registered as superseded will not be flagged. Where
      the registry and an existing piece disagree, the registry wins and the
      conflict goes in the README as a pending decision.

## Email specifics

- [ ] **Working unsubscribe link, honored company-wide within 10 business days**,
      and the physical postal address `1950 Cordell Ct., Ste 103, El Cajon, CA
      92020`. CAN-SPAM, and both are required on every commercial send.

- [ ] **Subject, preview text, and from-name do not misrepresent sender or
      content.** The sender is Black Box Safety, never an agency or a program name
      that reads as one.

- [ ] **Duty addresses at an agency domain are verification intel, not send
      targets.** Use them to confirm employment and route the relationship. Send
      marketing to a personal address. Where no personal address exists, a duty
      address may receive only the driest informational variant, with the reason
      written in the README.

- [ ] **Send only to profiles with verified marketing consent.** A transactional
      purchase is not consent.

- [ ] **One ask per email.** The one-ask rule can be ruled inapplicable to a
      transactional landing page by the owner, and was on the CAL FIRE build. It
      still binds every email in the campaign.

- [ ] **Cross-check the send list against the do-not-send list** in the README:
      anyone currently escalating a late order gets a status email, not a
      promotion.

## Last two

- [ ] **Gate output pasted into the project README**, not summarised.

- [ ] **Verified on the deployed URL, not locally.** Broken images, short paths
      returning 200, and the quote builder driven once end to end. Local rendering
      hides absolute-path and rewrite failures, which is precisely the class of
      bug an emailed link shows the customer first.
