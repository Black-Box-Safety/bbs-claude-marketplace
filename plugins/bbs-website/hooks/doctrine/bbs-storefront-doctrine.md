BBS STOREFRONT — DESIGN, CERT & PAGE-FLOW DOCTRINE
(Injected so this skill's output stays consistent with the rest of the Black Box Safety "BBS — Field Manual" Shopify theme. Match the existing site; introduce no new design system or off-brand palette.)

WHO/VOICE: BBS is a serious tactical/safety/PPE/government-procurement reseller. Voice = expert advisor: earnest, technical, mission-driven, credentials-first. SDVOSB + California DVBE; HQ El Cajon, CA; founded 2017. Audience = government/agency procurement (federal, CA state/edu, local/co-op), LE/first-responders, industrial/MRO.

CERT & CLAIM DOCTRINE (hard — never violate):
- No invented or unverified claims. If a fact isn't confirmed in-repo (bbs-suppliers per-manufacturer _brief.md, docs/brand canonical facts), don't assert it.
- No cross-jurisdiction cert credit: San Diego SLBE 17BB1659 and LA County DVBE 10086 are LOCAL only; statewide credit = OSDS DVBE 2009473. BBS is not a California small business; no SB or DVBE preference language in storefront copy. (Reason: BBS exceeded California's SB revenue threshold — bbs-foundations canonical-facts.md, "Small-business status is channel-dependent".)
- A manufacturer's own GSA/contract vehicle does NOT authorize BBS to fulfill unless BBS is a named reseller (respect each _brief.md "landmines").
- Pricing: Shopify price = MAP/MSRP list, NOT contract price (real contract price lives in Supabase). Label store prices "List price / contract pricing on quote" — never "GSA Net / Contract Net".
- Canonical quote SLA = 48 hours. Contract vehicles = 8 (7 verified + NPPGov PS25650, BBS = awarded vendor). GSA MAS = 47QSWA23D000Y (period 2022-2027; no "ult. 2042").

DESIGN TOKENS (use existing, add none): --navy #051c2c, --gold #b19800, --gold-ink (dark gold, PAPER surfaces only), --paper, --black, --gray-2, --line*. Fonts: --display (uppercase headings), --mono (tracked micro-labels), --body. Focus ring: --gold on dark grounds, --gold-ink on paper (WCAG 2.2 non-text >=3:1; body text >=4.5:1).

PAGE-FLOW CONVENTIONS (match other pages): section wrapper <section class="section paper|..."><div class="container">; a .num mono eyebrow (e.g. "/RFQ"); uppercase display H2; mono tracked micro-labels; brand/partner logos on WHITE chips (filter:none), never inverted; TEXT-DENSITY DISCIPLINE — tight, logo/credential-forward, not walls of text (push detail to dedicated pages); ONE primary CTA per surface; images via asset_img_url with explicit width/height + loading=lazy; wide tables inside overflow-x:auto.

RFQ PATTERN: quotes submit through Shopify native {% form 'contact' %} (see theme/sections/rfq-request.liquid) -> store email. The cart ("RFQ Cart") must SUBMIT AN RFQ (package line items + RFQ notes into a contact submission, return the 48-hr confirmation) and must NEVER dead-end at a paid checkout showing list prices.

IMPECCABLE: apply the AI-slop bans; reuse the tokens/components above; the change must read as part of this same site.