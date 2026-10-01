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
| Federal, primes (Bechtel, USACE, Centerra, UCOR), DoD | **SDVOSB** (VA CVE / SBA VetCert) **and small business** under SBA size standards | UEI `FRK5MJD35GN5` | 05/16/2028 |
| California state agencies | **DVBE** — the OSDS certification carries DVBE only | `2009473` | 12/31/2027 |
| LA County only | LA County DVBE (local credit only) | `10086` | 11/17/2027 |
| City of San Diego only | SLBE (local credit only) | `17BB1659` | — |

### Small-business status is channel-dependent, and the reason matters

This fact has flipped twice. It is written with its reason so it stops flipping.

- **Federally, BBS IS a small business.** SBA size standards for BBS's NAICS codes are far
  higher than California's, and BBS is under them. Federal small-business set-asides and
  SDVOSB set-asides are both live and both claimable. Federal positioning that calls BBS a
  small business is **correct** — do not strip it.
- **For the State of California, BBS is NOT a small business.** BBS **exceeded California's
  SB revenue threshold**. OSDS certification `2009473` carries **DVBE only**. This is a
  size-standard fact that changed over time, not a misreading of the certificate — which is
  why the 2026-09-02 ruling may well have been true when it was made.

So on California solicitations, competitive and informal alike:

- **No 5% Small Business preference (SCM §1204).** BBS is not SB in California and claiming
  the preference on a bid signed under penalty of perjury is a false certification.
- **The DVBE incentive (SCM §1202) still applies** — 1–5% scaled to DVBE participation, on
  every competitive solicitation, informal ones included. BBS remains DVBE-certified and
  still claims it. §1202's note
  that a non-SB DVBE incentive "cannot displace award to a #1 ranked small business" now
  describes BBS's actual position in California.

**Ruling: Parker Marshall, in session, 2026-09-22 — OSDS 2009473 is DVBE only; BBS is not
SB certified in California; BBS remains a small business federally. This supersedes the
2026-09-02 ruling recorded below, which held that the OSDS cert carried both.**

**Bids filed before the threshold were valid when filed.** Past California bids in the
filed-form corpus that claim SB (a certification line reading SB with DVBE, a checked SB
box) were filed while BBS was a California small business and were correct then (Parker,
2026-09-23). They are not errors and are not to be "corrected" in the record. They are
also not precedent: anything that learns from, cites, or defaults from the corpus treats an
SB claim as historical only and takes the current value from `vendor_profile.json`. The
same goes for the "largest small business seller to the State of California" ranking —
earned while BBS was a California small business, so it is stated in the past tense.

Everywhere else in the fleet cites this section rather than restating the reasoning.

Where the **DVBE incentive** does **not** apply either: orders placed against an LPA or
NASPO contract (no evaluation, so no incentive — the contract-lane price passes through at
cost); federal and prime bids (SDVOSB there, never DVBE); and storefront or marketing copy,
where an evaluation incentive is not a customer benefit.

The `bbs-shopify` canonical-facts line "BBS is NOT SB-certified" (2026-07-10) and the
storefront doctrine that carries it are **correct for California** and need no change on
that point. They are, however, written channel-neutrally, and read federally they are
false. **Reword** (recorded as outstanding for Parker by PR #29): name the channel —
"BBS is not a California small business; no SB or DVBE preference language in storefront
copy" — so they cannot be read as denying BBS's federal small-business status. **Applied
to the storefront doctrine 2026-09-22, PR #30** (then in the website plugin's hook file;
since 2026-09-28 the same text, byte for byte, lives in
`plugins/bbs-website/hooks/doctrine/bbs-storefront-doctrine.md`). The `bbs-shopify` line is
in another repo and still outstanding there.

**The two injected doctrine sets carried different problems. Both were RESOLVED
2026-09-22 in PR #30.** The maintainers keep the full record in the marketplace repo; it
does not ship with the plugins and nothing here depends on it. The files named below are where the text lives today; on
2026-09-22 it lived in each plugin's `hooks/` config for the since-retired injection plugin,
and the 2026-09-28 move carried it over unchanged.

| File | What it carried | Status |
|---|---|---|
| `plugins/bbs-foundations/hooks/doctrine/bbs-claude-md-doctrine.md` | The **affirmative false claim**: "OSDS SB/DVBE 2009473 for California state, where the 5% SB preference (SCM §1204) … apply on competitive solicitations incl. informal." Injected into **every CLAUDE.md-writing skill run** | **RESOLVED 2026-09-22, PR #30** — now the channel split above |
| `plugins/bbs-website/hooks/doctrine/bbs-storefront-doctrine.md` | "BBS is NOT SB-certified — never claim 'SB credit'." Correct for California, but channel-neutral | **RESOLVED 2026-09-22, PR #30** — reworded as above |

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
| Grainger pricing | **Grainger MCP** — per buying account. The `b2b.blackboxsafety.com` punch-out it replaced is retired | Never the open web; never from memory. Whether a Grainger line is sold at cost depends on the channel — "Grainger sell rule, by channel" below is the one home |
| Pipeline / outreach | Dynamics 365 Sales | |
| Storefront | Shopify `bbs-supabase-test.myshopify.com`, theme "BBS — Field Manual" | Verify the live theme id with `shopify theme list` before pushing |
| BBS form values (FEIN, permit, certs) | `plugins/bbs-sales/references/vendor_profile.json` | Skills resolve it as `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` and never re-key it |

### Grainger sell rule, by channel

The single home for whether a Grainger line may carry markup. Skills point here.

| Channel | Rule | Ruling |
|---|---|---|
| California state agencies — CA state schedules, including the NASPO ValuePoint CA MRO Statewide LPA (number in *Contract vehicles*, above) | **At cost.** The Grainger MCP's `unitPrice` is BBS's cost *and* the customer price, never marked up; BBS is paid through the contract rebate | Parker, ruled 2026-09-18; "confirmed" in session 2026-09-28 |
| Prime contractors (e.g. Bechtel) | **Grainger lines may be marked up.** Before pricing, the rep asks BBS's Grainger account manager for a discount on the items, prices from that discounted cost, then applies whatever markup the rep chooses. No markup figure is set — never invent one — and never invent a discount | Parker, in session, 2026-09-28: "For primes, grainger products can be increased. reps should ask for a discount from our grainger account manager first." |
| National and local cooperative contracts (Sourcewell, NPPGov, UC/OMNIA, local co-ops), direct federal, private | **Open for Parker.** Do not infer a rule from the rows above; ask the rep | — |

Where a quote spec records which rule applied (the quote builder's per-quote
`pricing.graingerAtCost`), it is `true` on a California state-schedule / NASPO LPA quote
and `false` on a prime quote. On an open channel it is not set by inference.

**Customer quote numbers are the Business Central SQ number** (Parker, in session,
2026-09-28: "use BC SQ number"). The local `900001` series is retired.

### What counts as a win

- **A win is confirmed by Business Central** — a sales quote with an `acceptedDate`, or a
  quote converted to a sales order — **or by a quote-log Outcome of *won* that the rep has
  confirmed.** Nothing else is a win.
- **`bbs_accepted` on a Sales CRM `bbs_rfqs` record: Parker's stated intent is
  "converted" ("I believe").** Parker, in session, 2026-09-28: "I believe [it] is in State
  of CA Agencies and means the quote has converted" — his own hedge, kept. Confirm the
  meaning before relying on it.
- **In practice it has never been set.** Checked live in the production CRM on 2026-09-28:
  across 2,550 `bbs_rfqs` records created since 2026-01-01, `bbs_accepted` is never true,
  `bbs_orderfinalized` is never true, and no record has `bbs_ponumber` set.
- **So no skill counts a win from it today**, and a report that would show it says
  "not recorded in CRM" — never zero, which would read as "we won nothing". When reps start
  setting it, confirm with Parker what `true` means and re-check the field before relying
  on it, then change this section, not the skills that point here.

## People and signatures

| Person | Role | Signs |
|---|---|---|
| Jackson Dalton | President, DV owner | Ownership lines: DGS PD 843, STD 204, CV 012. Always. |
| Griffin Forsyth | Vice President | Federal / Sourcewell contracts. Signed most historical CalRecycle 74s — history, not the rule (below) |
| Parker Marshall | Sales Manager, primary responder | Rep-signed lines when the rep names him as signer: OBS 4007(B) bidder, Darfur, CalRecycle 74. (OBS 1000's signer is not ruled — see *Open* below) |

**Who signs the rep-signed lines (OBS 4007(B) bidder, Darfur, CalRecycle 74)** was ruled by
Parker in session, 2026-09-28. The rule — who may sign, and when a skill may apply a
signature — lives once, in `plugins/bbs-sales/references/ca-form-rules.md`, "Rep-signed
lines". The DV-owner declarations above stay Jackson's.

Signatures are applied by the form skills: Parker and Jackson have each delegated
authority for the forms those skills fill, confirmed with counsel 2026-09-16. The rule
is **whose signature goes on which line** (above) — never a third party's, never a
customer's. Signature images are credentials: they live outside git, like the Grainger
`.env`, and are referenced at run time. Sending stays human: the managed settings deny
the send-class tools.

Quote desk (2026-07): Aanya Samarasinghe (quotes/crossovers), Kim Quezon (door/tactical),
Joyce Newell (POs), Jeff Azar (body armor), Griffin (federal). Accounting: Amy Leath.

## Rulings on binding documents — what `/ca-rfq` checks

`/ca-rfq` (bbs-sales) stops on an open ruling. This is where it looks, because this file
ships to reps and the marketplace repo's `docs/` does not. Each row names a question and
where its answer lives; the answer itself is not restated here. This section is complete
for a run: do not look for another file. The maintainers keep the history in the
marketplace repo, which does not ship to rep machines.

**Ruled**

| Question | Ruled | The rule lives in |
|---|---|---|
| Fresh "please quote" request: file or price first | 2026-09-24 | `/ca-rfq` Gate 0 (c) |
| CDCR Packet B SB checkbox | 2026-09-22 | "Small-business status is channel-dependent", above |
| DGS PD 843 "Name of DVBE" | 2026-09-18, confirmed 2026-09-28 | `ca-form-rules.md`, DGS PD 843 row |
| Company name on CalRecycle 74, OBS 1000, Darfur OBS 1500 | 2026-09-28 | `ca-form-rules.md`, "Company name" |
| Who signs the rep-signed lines (OBS 4007(B) bidder, Darfur, CalRecycle 74) | 2026-09-28 | `ca-form-rules.md`, "Rep-signed lines" |
| Grainger sell rule — California state schedules (incl. the NASPO LPA); primes | 2026-09-18 / 2026-09-28 | "Grainger sell rule, by channel", above |
| Customer quote number | 2026-09-28 | Systems of record, above |

**Open — awaiting Parker**

- Grainger sell rule for national and local cooperative contracts (Sourcewell, NPPGov,
  UC/OMNIA, local co-ops), direct federal and private buyers — including whether national
  cooperative contracts are at cost. A run that needs it stops and tells the rep.
- Who signs OBS 1000 (GenAI factsheet). `ca-form-rules.md` assigns no signer, so a skill
  fills the date, leaves the signature blank and flags it.
- The OBS Line-Item Cost Worksheet "BUSINESS NAME:" header. The 2026-09-28 legal-name
  ruling did not cover it; it keeps the short name `fill_obs_packet.py` writes today until
  Parker rules, and does not stop a run.

## CA state book scope

Body armor (contract codes `BA-CA`, `BODYARMOR`, `BA-SRCWL`) and CSU/UC are **out** of the
Kim/Aanya CA state book. Ruling: Parker, in session, 2026-09-28.

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
| "CA SB & DVBE … 5% SB preference" (`ca-quote-hub`, signature block) vs "NOT SB-certified" (`bbs-shopify` canonical facts, storefront doctrine) | ~~2026-09-02: SB/DVBE is correct, claim the §1204 preference; fix the `bbs-shopify` line~~ — **superseded 2026-09-22.** Parker ruled in session that OSDS 2009473 is **DVBE only** and BBS is **not** SB in California, having passed the state SB revenue threshold. So: no §1204 preference on CA bids; §1202 DVBE incentive unchanged; the `bbs-shopify` line was right about California and stays. BBS *is* small business federally — see "Small-business status is channel-dependent" above, which is the home of this fact |
| HQ "San Diego" vs "El Cajon" | El Cajon |
| Theme "BBS — Field Manual" vs "Copy of BBS — Field Manual" id `160937935099` | The id wins; check `shopify theme list` |
| Shopify `--only`: "always" vs "never for new files" | Both true: `--only` for edits, full push when adding files, always from `theme/` |
| Line caps "~120" vs "~200" | 150, hard |
| Same skill, two names (`bbs-price-list-cleaner` / `price-list-cleaner`; two different `ca-rfq-intake`) | One name per behaviour. Two skills with one name is worse than a missing skill: it fails silently with a plausible answer |
| Two things named `bbs-ops`: the org repo `Black-Box-Safety/bbs-ops` and the website plugin | Resolved 2026-09-02: the plugin is now `bbs-website` (install `bbs-website@bbs-claude-marketplace`); `bbs-ops` names only the repo |
| Griffin: "VP" / "Vice President" / "federal signer" / "CalRecycle 74" | Vice President; signs federal and Sourcewell. He signed most historical CalRecycle 74s — history, not the rule; who signs it now is in "People and signatures" |
