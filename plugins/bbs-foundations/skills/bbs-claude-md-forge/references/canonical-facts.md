# Canonical facts — the exact strings, and the contradictions they settle

When a CLAUDE.md disagrees with this file, the CLAUDE.md is wrong. When this file is wrong,
fix it here once and tell Parker. Verified against the fleet sweep of 2026-09-02 and the
owner-locked canonical facts in `bbs-shopify` (2026-07-10). Public-record data only; the
FEIN, seller's permit, and buying account numbers live in `~/.bbs/vendor_profile.json`.

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
| California state agencies | **DVBE** (OSDS program name is "SB/DVBE") | `2009473` | 12/31/2027 |
| LA County only | LA County DVBE (local credit only) | `10086` | 11/17/2027 |
| City of San Diego only | SLBE (local credit only) | `17BB1659` | — |

BBS is **not** California SB-certified. Do not write "5% SB preference" or "SB credit."
`ca-quote-hub/CLAUDE.md` still says "5% SB preference + DVBE incentive" — that line is
wrong and should be corrected there. Parker's email signature reads `CA SB/DVBE 2009473`,
which is the program's name and is fine in a signature; it is not a claim of SB status.

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
| Grainger pricing | BBS b2b punch-out (`b2b.blackboxsafety.com`), Grainger MCP | Never the open web |
| Pipeline / outreach | Dynamics 365 Sales | |
| Storefront | Shopify `bbs-supabase-test.myshopify.com`, theme "BBS — Field Manual" | Verify the live theme id with `shopify theme list` before pushing |
| BBS form values (FEIN, permit, certs) | `~/.bbs/vendor_profile.json` | Skills read it; never re-key it |

## People and signatures

| Person | Role | Signs |
|---|---|---|
| Jackson Dalton | President, DV owner | Ownership lines: DGS PD 843, STD 204, CV 012. Always. |
| Griffin Forsyth | Vice President | Federal / Sourcewell contracts; most CalRecycle 74s |
| Parker Marshall | Sales Manager, primary responder | Bidder and cert lines: Darfur, OBS 1000, reps & certs; CalRecycle 74 on his own RFQs |

Never pre-fill a signature line. "No review, no signature."

Quote desk (2026-07): Aanya Samarasinghe (quotes/crossovers), Kim Quezon (door/tactical),
Joyce Newell (POs), Jeff Azar (body armor), Griffin (federal). Accounting: Amy Leath.

## Model IDs

`claude-opus-4-8` · `claude-sonnet-5` · `claude-haiku-4-5`. Anything with a dated suffix
or an older number (`claude-opus-4-5` in `bbs-agent/config.py`) is stale.

## Brand

Navy `#051c2c`, gold `#b19800`, AllStar red `#fa0a0a` (co-branded dashboard only). Fonts
Archivo, JetBrains Mono. Quote SLA 48 hours. CA sales tax ~7.75%, F.O.B. Destination.

## Contradictions the sweep found, and the ruling

| Contradiction | Ruling |
|---|---|
| MRO LPA `7-25-51-02.03` (96 places) vs `-52-` (10 places) | `-51-`. Fix `bbs-agent` |
| "CA SB & DVBE … 5% SB preference" vs "NOT SB-certified" | Not SB-certified. Fix `ca-quote-hub` |
| HQ "San Diego" vs "El Cajon" | El Cajon |
| Theme "BBS — Field Manual" vs "Copy of BBS — Field Manual" id `160937935099` | The id wins; check `shopify theme list` |
| Shopify `--only`: "always" vs "never for new files" | Both true: `--only` for edits, full push when adding files, always from `theme/` |
| Line caps "~120" vs "~200" | 150, hard |
| Same skill, two names (`bbs-price-list-cleaner` / `price-list-cleaner`; two different `ca-rfq-intake`) | One name per behaviour. Two skills with one name is worse than a missing skill: it fails silently with a plausible answer |
| Two things named `bbs-ops`: the org repo `Black-Box-Safety/bbs-ops` and the website plugin | Resolved 2026-09-02: the plugin is now `bbs-website` (install `bbs-website@bbs-claude-marketplace`); `bbs-ops` names only the repo |
| Griffin: "VP" / "Vice President" / "federal signer" / "CalRecycle 74" | Vice President; signs federal, Sourcewell, and most CalRecycle 74s |
