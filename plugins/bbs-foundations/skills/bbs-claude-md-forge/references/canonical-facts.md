# Canonical facts — the exact strings, and the contradictions they settle

When a CLAUDE.md disagrees with this file, the CLAUDE.md is wrong. When this file is wrong,
fix it here once and tell Parker. Verified against the fleet sweep of 2026-09-02 and the
owner-locked canonical facts in `bbs-shopify` (2026-07-10). Public-record data only; the
FEIN and seller's permit live in `plugins/bbs-sales/references/vendor_profile.json`, committed
deliberately in this private repo (see `.claude-plugin/PLUGINS.md`). Buying account
numbers are never committed.

## Identity

| Fact | Value | Never write |
|---|---|---|
| Legal name | `Black Box Safety, Inc.` (short: Black Box Safety, BBS) | — |
| Headquarters | `1950 Cordell Ct, Suite 103, El Cajon, CA 92020` | "San Diego, CA" as HQ (the live site once said it; El Cajon is locked) |
| Founded | 2017, Jackson Dalton, medically retired Marine Corps veteran | — |
| Main phone | `(619) 499-7943` | — |
| Parker's mobile | `757.472.1616` (signature block only) | — |
| Parker's email | `parker@blackboxsafety.com` (`pmarshall@` is an alias, same mailbox) | — |

## Certifications, by jurisdiction

| Channel | Say | Number | Expires |
|---|---|---|---|
| Federal, primes (Bechtel, USACE, Centerra, UCOR), DoD | **SDVOSB**, VA CVE / SBA VetCert | UEI `FRK5MJD35GN5` | 05/16/2028 |
| California state agencies | **SB/DVBE** — one OSDS certification carrying both | `2009473` | 12/31/2027 |
| LA County only | LA County DVBE (local credit only) | `10086` | 11/17/2027 |
| City of San Diego only | SLBE (local credit only) | `17BB1659` | — |

On California **competitive solicitations, informal included**, BBS is entitled to both the
**5% Small Business preference** (SCM §1204, "Small Business Preference and Competitive
Solicitations") and the **DVBE incentive** (SCM §1202, 1–5% scaled to DVBE participation).
They are evaluation mechanisms, and they are separate: §1202 notes a non-SB DVBE incentive
"cannot displace award to a #1 ranked small business," which is why holding both matters.
§1204 verbatim: the preference "applies for competitive solicitations regardless of the
solicitation format (e.g., RFQ, IFB, RFP) or dollar value with few exceptions," is "for
evaluation purposes only and does not change the actual bids," and is capped at $50,000 per
bid (combined preferences 15% or $100,000, whichever is less). Gov. Code §14838.5(a),
§14838(b)(2), §14838(g); 2 CCR §1896.8. Confirmed by Parker Marshall, 2026-09-02.

Where they do **not** apply: orders placed against an LPA or NASPO contract (no evaluation,
so no preference — the contract-lane price passes through at cost); federal and prime bids
(SDVOSB only); and storefront or marketing copy, where a preference is not a customer
benefit. That last point is what the `bbs-shopify` canonical-facts line "BBS is NOT SB-
certified" (2026-07-10) was protecting, but as written it contradicts this row and the
storefront skill-bus doctrine still carries it. **Outstanding for Parker:** reword that line
to "no SB or DVBE preference language in storefront copy" so the two files agree.

## Contract vehicles (canonical count: 8)

| Vehicle | Number | Notes |
|---|---|---|
| NASPO ValuePoint CA MRO Statewide LPA | `7-25-51-02.03` | Grainger-fulfilled. **Not** `7-25-52-02.03` (a typo that spread to `bbs-agent`), not legacy `7-18-51-02.18` |
| CA Body Armor LPA | `1-23-84-07` | Point Blank, sole-source |
| Sourcewell Body Armor | `091924-BBS` | |
| GSA MAS | `47QSWA23D000Y` | 11/15/2022–11/14/2027. No "ult. 2042" |
| NPPGov | `PS25650` | LE; BBS is the awarded vendor |
| UC / OMNIA | `2018-000207` | |
| CSU | — | |
| DOE Grainger | — | |

CMAS is **not** a BBS vehicle. A manufacturer's own GSA schedule does not authorize BBS
to fulfill unless BBS is a named reseller.

## Systems of record

| Data | System of record | Everything else is a mirror |
|---|---|---|
| Quotes, orders, invoices, AR, spend | **Business Central** (company "Black Box Safety", tenant `fea7ae2d-…`) | Never answer PO receipt from the `fullyReceived` header flag |
| Catalog: products, specs, contract prices | **Supabase** `oaqkueputgaweojcpaim` | Shopify renders it; the quote bot reads a frozen snapshot |
| Procurement intelligence (SCPRS) | Supabase `jsrcrprxoxlnphhcpnbu` via ca-procurement-intel MCP | |
| Revenue dashboard | Supabase `hkogytbgmaucjjaeqrgd` | |
| Customer documents (RFQs, POs, packets) | **SharePoint** `Black Box Safety - MASTER/Customers/…` | Repos hold pointers and lessons, not the documents |
| Grainger pricing | **Grainger MCP** — per buying account. The `b2b.blackboxsafety.com` punch-out it replaced is retired | Never the open web; never from memory |
| Pipeline / outreach | Dynamics 365 Sales | |
| Storefront | Shopify `bbs-supabase-test.myshopify.com`, theme "BBS — Field Manual" | Verify the live theme id with `shopify theme list` before pushing |
| BBS form values (FEIN, permit, certs) | `plugins/bbs-sales/references/vendor_profile.json` | Skills resolve it as `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` and never re-key it |

## People and signatures

| Person | Role | Signs |
|---|---|---|
| Jackson Dalton | President, DV owner | Ownership lines: DGS PD 843, STD 204, CV 012. Always. |
| Griffin Forsyth | Vice President | Federal / Sourcewell contracts; most CalRecycle 74s |
| Parker Marshall | Sales Manager, primary responder | Bidder and cert lines: Darfur, OBS 1000, reps & certs; CalRecycle 74 on his own RFQs |

Signatures are applied by the form skills: Parker and Jackson have each delegated
authority for the forms those skills fill, confirmed with counsel 2026-09-16. The rule
is **whose signature goes on which line** (above) — never a third party's, never a
customer's. Signature images are credentials: they live outside git, like the Grainger
`.env`, and are referenced at run time. Sending stays human: the managed settings deny
the send-class tools.

Quote desk (2026-07): Aanya Samarasinghe (quotes/crossovers), Kim Quezon (door/tactical),
Joyce Newell (POs), Jeff Azar (body armor), Griffin (federal). Accounting: Amy Leath.

## Model IDs

`claude-opus-5` · `claude-sonnet-5` · `claude-haiku-4-5`. Anything with a dated suffix or
an older number (`claude-opus-4-8`, `claude-opus-4-5` in `bbs-agent/config.py`) is stale.

**This list is generated — do not hand-edit it here.** `references/models.json` is the
source: `check_claude_md.py` reads it, and `scripts/refresh_models.py` rewrites it from the
Anthropic Models API (weekly, via `.github/workflows/refresh-models.yml`, which opens a PR
when the list moves). When the workflow changes `models.json`, update this line to match.

That split exists because this fact went stale in two places at once: the list said
`claude-opus-4-8` and the checker enforced it, so the checker passed the superseded ID and
told authors to write it. **When a canonical fact has a checker, the checker is part of the
fact** — which is why the checker now has no copy of its own.

## Brand

Navy `#051c2c`, gold `#b19800`, AllStar red `#fa0a0a` (co-branded dashboard only). Fonts
Archivo, JetBrains Mono. Quote SLA 48 hours. CA sales tax ~7.75%, F.O.B. Destination.

## Terms that mean two things

| Term | The two senses | Which one you mean |
|---|---|---|
| **punchout / punch-out** | (1) The standard procurement pattern: an agency's eProcurement system links out to a supplier's e-commerce catalog and the cart returns to the buyer's system. (2) BBS's own retired Grainger pricing path at `b2b.blackboxsafety.com`. | Sense (1) is live and correct — `grainger-promo-page` uses it, and agencies punch out to Grainger every day. Sense (2) is **retired**: BBS gets Grainger prices from the Grainger MCP (`grainger-pricing`). Never "fix" sense (1) into the MCP wording. |

## Contradictions the sweep found, and the ruling

| Contradiction | Ruling |
|---|---|
| MRO LPA `7-25-51-02.03` (96 places) vs `-52-` (10 places) | `-51-`. Fix `bbs-agent` |
| "CA SB & DVBE … 5% SB preference" (`ca-quote-hub`, signature block) vs "NOT SB-certified" (`bbs-shopify` canonical facts, storefront doctrine) | **SB/DVBE is correct.** 5% SB preference (§1204) + DVBE incentive (§1202) on competitive solicitations incl. informal; never on LPA orders, federal bids, or storefront copy. Fix the `bbs-shopify` line and the storefront doctrine, not `ca-quote-hub`. Ruling reversed 2026-09-02 on Parker's confirmation; the earlier ruling was mine and was wrong |
| HQ "San Diego" vs "El Cajon" | El Cajon |
| Theme "BBS — Field Manual" vs "Copy of BBS — Field Manual" id `160937935099` | The id wins; check `shopify theme list` |
| Shopify `--only`: "always" vs "never for new files" | Both true: `--only` for edits, full push when adding files, always from `theme/` |
| Line caps "~120" vs "~200" | 150, hard |
| Same skill, two names (`bbs-price-list-cleaner` / `price-list-cleaner`; two different `ca-rfq-intake`) | One name per behaviour. Two skills with one name is worse than a missing skill: it fails silently with a plausible answer |
| Two things named `bbs-ops`: the org repo `Black-Box-Safety/bbs-ops` and the website plugin | Resolved 2026-09-02: the plugin is now `bbs-website` (install `bbs-website@bbs-claude-marketplace`); `bbs-ops` names only the repo |
| Griffin: "VP" / "Vice President" / "federal signer" / "CalRecycle 74" | Vice President; signs federal, Sourcewell, and most CalRecycle 74s |
