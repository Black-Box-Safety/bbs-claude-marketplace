<p align="center">
  <img src="https://img.shields.io/badge/desk-CA%20state%20business%2C%20both%20directions-051c2c" alt="California state business, both directions">
  <img src="https://img.shields.io/badge/skills-16-b19800" alt="16 skills">
  <img src="https://img.shields.io/badge/pricing-at%20cost%20on%20CA%20schedules-2dd4bf" alt="At cost on CA schedules">
</p>

# bbs-sales

The plugin for California state business, end to end: the territory work that creates the
demand, the request that comes in, and the campaign that goes out. A buyer emails an RFQ and this plugin takes it from the inbox to a signed
packet in the buyer's folder. A Grainger rep sends a negotiated price sheet and this plugin turns
it into a landing page an agency buyer can order from, sent to the segment of buyers most likely
to act on it.

Reps lose state quotes on the paperwork more often than on the price. A cert with last quarter's
solicitation number, an unsigned perjury declaration, a duplicate folder that hides the last
quote's precedent: any of those can set the whole bid aside. The plugin makes the boring half
automatic so the rep spends their time on the buyer. The same discipline applies going out: a
promo page that overstates a discount or implies an agency's endorsement is a compliance problem,
not a marketing win, so every page runs through the same brand gate as any printed piece.

**Jump to:** [The desk, end to end](#the-desk-end-to-end) · [The territory, before the RFQ](#the-territory-before-the-rfq) · [Setup](#one-time-setup) · [Commands](#commands) · [The rules that don't bend](#the-rules-that-dont-bend) · [Rollout guide](#rollout-guide)

## The desk, end to end

A state quote moves through the same seven steps every time. Each one has a skill, and
the handoffs are what the plugin is really for — the rep should never be the integration
between two of these.

| # | Step | Skill |
|---|---|---|
| 1 | An RFQ arrives and the clock starts | `ca-rfq-intake` |
| 2 | Get the items out of whatever they sent | `rfq-item-extract` — one skill for a DWR RFQ PDF, a saved Grainger cart PDF, or a screenshot of a cart or table |
| 3 | Can we even sell it on this vehicle? | `dgs-bpo-item-check` — is the Grainger part on the active DGS BPO |
| 4 | Price it | `grainger-pricing` (the authorized path — the Grainger MCP) · `bbs-sourcing` (competitive bids needing real vendor outreach, dispatching `supplier-scout` for items BBS has never sourced) · `vendor-quote-email` (one vendor, one ask) |
| 5 | Build the customer's quote | `bbs-quote-builder` — Business Central quote layout, numbered with the BC SQ number, as a PDF |
| 6 | Fill the compliance packet | `ca-form-filler` — every CA form, with the CDCR OBS 4007(B) Packet-B as its scripted path · `naspo-quote` runs a whole NASPO response and calls it for the paperwork |
| 7 | Go find the next one | `grainger-promo-page` (outbound campaign). Federal deck copy is `bbs-deck-voice`, in `bbs-foundations` |

Step 4 is the one to get right. `grainger-pricing` is the authorized path for Grainger
pricing at BBS — prefer it over anything found on the open web, because the open-web
price is not the price BBS's account actually pays.

`bbs-deck-voice` is the exception to this plugin's California framing: it writes
**federal** pursuit copy, where BBS is SDVOSB and never DVBE, and where BBS **is** a small
business under SBA size standards. Do not use it for a CA agency deck, and do not let its
certification language leak into a state bid. On California competitive solicitations the
discipline is different in both halves — OSDS 2009473 carries **DVBE only**, so claim the
DVBE incentive (SCM §1202) and **never** the 5% SB preference (SCM §1204): BBS passed
California's SB revenue threshold and is not a California small business.

An order that has already been taken is not this plugin's work. A wrong item, a short
shipment, a price discrepancy on the PO — those go to `bbs-back-office`.

### The three the plugin was built around

The work splits into inbound and outbound.

| Skill | Fires when | Stops at |
|---|---|---|
| `ca-rfq-intake` | A request arrives from any State of CA agency: CDCR institution, CalVet home, DSH hospital, Caltrans district, CalFire unit, DWR, CMD. Email with attachments, bare item list, worksheet, portal link, all the same. | The RFQ is logged and the clock is visible. No pricing. |
| `naspo-quote` | A logged RFQ needs a price and a packet, or a buyer sends blank state certs to complete. | Signed packet delivered into the buyer's folder, with a summary of every judgment call. |
| `grainger-promo-page` | A Grainger rep sends a priced sheet or hot list for an agency, or someone asks for a promo page, contract sheet, product landing page, punchout promo, or campaign page for a CA agency, or asks to price a list of Grainger item numbers or segment an agency's buyers for a campaign. | A deployed, gated landing page with live pricing and a working quote builder, plus the SCPRS buyer segments to send it to. |

**`ca-rfq-intake`** finds or creates the folder under `Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`, saves every attachment as received, opens an `RFQ.md` run record, and adds a row to the buyer's `quote-log.md`. It deliberately stops before pricing. The point of intake is that the deadline becomes something anyone can see; mixing pricing into it is how the due-date field ends up empty.

Creating a second folder for a buyer who already has one is the expensive mistake, because the next quote's precedent search misses it. Search by buyer name and by item before creating anything.

**`naspo-quote`** reads the buyer folder, pulls live Grainger pricing on the institution's account, builds the quote PDF, and fills and signs the compliance packet: OBS Line-Item Cost Worksheet, CalRecycle 74, DGS PD 843, Darfur OBS 1500, OBS 1000 GenAI, and Bidder Declaration GSPD-05-105. It renders every page and looks at it before delivering, because these forms clip long values silently.

**`grainger-promo-page`** runs the other direction. An agency already buys a given list of items, usually direct or from a competitor. Routing the same items at the same contract price through Black Box Safety turns that spend into reportable DVBE participation, and the skill's job is to make that concrete: real prices, real photos, real availability, and a quote builder a buyer can use without typing an email. The pricing-verification step matters because the sheet a rep sends is not always actually the lowest price: the skill checks every line against the agency's own Grainger account and prints whichever number is lower, because "lowest when you quote" is usually what the rep promised the buyer. SCPRS segmentation is what makes this more than a mailshot: instead of one blast, the skill sizes three buyer segments from the SCPRS warehouse (buys the prime direct, buys the category elsewhere, has BBS history but drifted) so the page goes to the people it can actually move, each with the wedge that fits their situation. And nothing ships before the brand compliance gate runs on the rendered page, same as any other piece, because an implied endorsement or an unregistered discount claim is a compliance problem the gate can catch just as easily on a webpage as on a PDF. The CAL FIRE H2 2026 build is the reference example: it was built once against a real agency hot list, and the errors it turned up (unpriced lines, a sheet that lost to the account price on more than a dozen lines, mismatched item descriptions) are written up in the skill's own worked example rather than repeated here.

Both `ca-rfq-intake` and `naspo-quote` fire on their own when the conversation matches an inbound request; `grainger-promo-page` fires the same way when the conversation matches an outbound campaign build. You do not have to name any of them.

## The territory, before the RFQ

Sales drives requests. A rep works a book, a buyer at a facility gets a call, and the call
produces an RFQ or a NASPO order — which is what the desk above exists to process. These six
skills are the front of that pipeline. None of them writes outreach, prices anything or sends
anything; each stops at a document a rep works from.

| Skill | Job | Stops at |
|---|---|---|
| `ca-territory-handoff` | Band a book by relationship state (recover, defend, watch, provisioned whitespace, cold start), rank by dollars at risk, size the pond, and write the dated call list with the opening words per band | The call list. A request it produces goes to `/ca-rfq` |
| `ca-budget-timing` | When an agency has money, by when it must encumber it, and which deadline governs a deal | The dated answer, with its source. The other territory skills call it for every date they print |
| `ca-agency-primer` | A multi-site department as a system: what each site does, how each buys, where BBS stands, public and internal figures kept visibly apart | The internal primer |
| `ca-site-visit-brief` | One booked meeting: the long call plan for the night before and the one-screen pocket card for the parking lot | The two documents |
| `ca-visit-readiness-review` | Pressure-test a finished brief from the side of the person who has to say it in the room | An ordered list of changes, applied back to the brief |
| `bbs-weekly-sales-report` | Parker's weekly summary of his, Kim's and Aanya's week — pipeline from the Sales CRM, bookings from Business Central | The markdown report he writes the weekly form from. A human submits the form |

What each one needs installed is in its own `requires:` and `degrades-without:`; run
`python3 scripts/check_marketplace.py --requirements` for the table. Several of them lean on
account-synced skills and agents that are not in this marketplace (`ca-state-sales-grounding`,
the `sales-*` craft skills, and personal agents such as Callie and Nell) and on the synced
`Customers/State of CA Agencies/.sales-team/` folder. Each says so when one is missing rather
than working around it.

On certifications the territory skills follow the same channel rule as the desk: in
California BBS is **DVBE only** and not a California small business; federally it is SDVOSB
and a small business. They point at `bbs-foundations` `canonical-facts.md` rather than
restating the ruling.

`docs/TRIGGER-CHECK.md` is a desk read of these descriptions against the desk's existing
skills — one reader's judgement of which skill each phrasing should reach, aimed at a
territory question not stealing an RFQ intake. It is not a measurement of triggering; that
needs `docs/evals/` with Claude auth, and has not been run for these skills.

## One-time setup

Do these once per machine. Skipping any one of them shows up as a confusing failure halfway through a packet or a page, not as a clear error at the start.

### For `naspo-quote`

**1. Install the PDF libraries.**

```bash
pip install pymupdf pypdf
```

`pymupdf` fills and stamps the forms; `pypdf` reads filled values back out of the archive when the skill mines precedents. No PDF library means no packet.

**2. Nothing to create — the vendor profile ships with the plugin.**

`plugins/bbs-sales/references/vendor_profile.json` is the single authority for every BBS value that goes on a state form: legal name, address, FEIN, seller's permit, DVBE cert number and expiration, and Jackson Dalton as the disabled-veteran owner. Skills resolve it as `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`, wherever the plugin was installed.

Earlier revisions told you to copy it to `~/.bbs/vendor_profile.json` first. Do not — that second copy is exactly how a cert expiry goes stale in one place while binding bids go out from another. FEIN and seller's permit are committed here deliberately: this repo is BBS-specific and private (see `.claude-plugin/PLUGINS.md`). Buying account numbers and API keys are never committed.

If an RFQ arrives pre-filled with a BBS field that disagrees with this file, the RFQ is wrong: flag it, don't adopt it.

TODO: the CUF statement (the "distinct element of work" on GSPD-05-105) is **not** in the profile — `ca-form-filler` currently asks the rep for it. Decide whether it belongs in the profile.

**3. Check the signature images are synced.** Both PNGs live in OneDrive, not in this repo. Where each one lives is recorded once, as `signature_image` on that person in `references/vendor_profile.json` — look there, not here. Make sure both files are on this device ("Always keep on this device"); The paths start `MASTER/`, meaning your synced `Black Box Safety - MASTER` folder; `fill_ca_forms.py` joins them onto the spec's `master_root`. It stops with the signer's name and the path if a signature file is missing, empty, or not a PNG, and writes nothing rather than a packet that looks signed.

Who signs the rep-signed lines (CalRecycle 74, Darfur, the OBS 4007(B) bidder line), and when a skill may apply a signature, is in `references/ca-form-rules.md`, "Rep-signed lines" (ruled 2026-09-28). Recording another person's signature image needs them added to `vendor_profile.json` `signature_delegation` first, which is Parker's call.

**4. Make sure OneDrive is actually synced.** This skill reads and writes the `Customers/State of CA Agencies/` tree on disk. A folder that is online-only looks empty to Claude, so a precedent search comes back with nothing and the answer is a guess instead of a lookup. Right-click the `State of CA Agencies` folder and choose "Always keep on this device."

### For `grainger-promo-page`

This skill does not touch the PDF stack or `vendor_profile.json` above: it has its own requirements, listed once here rather than assumed:

- **Grainger MCP access**, for `grainger_price` (per-account pricing) and product data. Pricing every line against the agency's own account, not just the sheet, is the whole point of the pricing-verification step.
- **SCPRS access** (`explore_sql`), to size the buyer segments. Without it the skill can build the page but not the audience.
- **A Business Central connection**, to pull the agency's ship-to addresses for the unit picker. `scripts/units_from_bc.py` turns a `bc_query_entity` result into `data/units.json`.
- **Chrome installed locally**, for `scripts/make_og.py` to render the 1200x630 Open Graph preview card in the real brand typeface. Without a preview card the link renders as a bare URL in Outlook.
- **The Vercel CLI**, for deploy: `vercel deploy --prod --yes --scope <team>`. The Vercel MCP deploy tool fails on payloads over about 100KB, which a page with product photography routinely exceeds, so use the CLI.

## Commands

| Command | Does |
|---|---|
| `/ca-rfq` | The whole desk order under one contract: intake gate, recognition, extraction, eligibility, pricing, quote, packet and signature, visual verification, delivery. It carries order and gates only — every step runs the skill that owns it, so the command cannot drift away from the skills it invokes. |
| `/ca-territory-handoff` | Segment a book and turn it into a dated, prioritized call list. Runs `ca-territory-handoff`; stops before any outreach is written. |

Agents:

- `supplier-scout` — supplier options for an item BBS has never sourced; dispatched by `bbs-sourcing` step 5c or directly ("find supplier options for MSA 10082709").
- `sal` — territory launch and account expansion: tiered launches, displacement and win-back campaigns, multi-threading, and reviewing rep-facing playbooks for whether a rep could execute them.
- `brenda` — DGS blanket purchase orders end to end: intake, the consolidated BPO tracker, pace against expiry, and the follow-ups that get a facility to spend before its BPO lapses.

Agents shipped in a plugin ignore `hooks`, `mcpServers` and `permissionMode`; none of these three sets them.

Intake is an **explicit first gate**, not an unconditional first step: an already-logged RFQ enters at recognition, and an unlogged one that arrives as a request to price puts the order to the rep rather than assuming it. Whether a fresh "the agency emailed asking us to quote these" is filed first or priced first is an open ruling for Parker, and the command is built so either answer lands without a rebuild.

`grainger-promo-page` has no slash command yet. Describe the ask ("build a promo page for CAL FIRE from this hot list") and it fires on its own.

## The rules that don't bend

These four come up on every state quote, and each one exists for a reason worth knowing.

**Price at cost on CA state schedules.** On every California state schedule today the sell rule is `at_cost`: the customer price equals BBS cost, no markup. That is not generosity and not a mistake in the data. BBS is paid through the contract rebate, not the margin on the line. A rep or a code path that adds 20% here produces a quote that is both wrong and uncompetitive. Competitive solicitations are the exception: there the price is a bid and margin is the rep's call.

**Price against the buying institution's own Grainger account.** Discount is per account, so the wrong account returns a price that looks completely valid and is completely wrong. The account number is usually in the agency folder name (`CMC - 887895111 - California Men's Colony`); a buyer note inside the folder that names a different account for their site wins, because it came from the buyer.

**No sales tax on the worksheet.** The OBS Line-Item Cost Worksheet prints "Do not include sales tax" on its face. The agency handles tax on its side. Quote `taxRate = 0` and let the totals match the worksheet exactly: a tax line is a mismatch the buyer has to reconcile before they can award.

**DVBE cert 2009473 expires 12/31/2027.** The DVBE certification is what makes BBS worth quoting to a state buyer with a participation goal, and a packet signed against an expired cert is worse than no packet. Check the expiration against the quote due date before signing anything. Expired, or inside 30 days, means stop and tell the rep.

One more that is not a rule but behaves like one: the `Customers/State of CA Agencies/` tree is the training data. Every blank the agency sent and every filled version BBS returned is in there. When history can answer a question (which form revision this agency uses, what BBS wrote in that field last time, whether this buyer accepted a 0% recycled-content answer), read the corpus instead of guessing or asking the rep. Certification fields are the exception: take them from `vendor_profile.json`, never from a past packet (why: `bbs-foundations` `canonical-facts.md`, "Small-business status is channel-dependent").

## Hooks (v1.1)

Deterministic guards, PowerShell, shipped with the plugin. They fire on Windows rep machines
without any per-machine setup.

| Hook | When | What it does |
|---|---|---|
| `guard-tree.ps1` | Before Bash / PowerShell / Write / Edit | Denies renames or moves inside `All RFQ's by Agency` (folder names carry account numbers); denies creating a buyer or agency folder whose name near-duplicates a sibling (case, spaces, `(ALL)`, a dropped or added word, two typos); denies overwriting anything under `FILLED/`, including a shell delete or a redirect into a submitted packet (reading one stays allowed) |
| `desk-context.ps1` | Session start inside a buyer folder | Puts the last rows of `quote-log.md` and the latest `FLAGS.md` entries in front of Claude before the first prompt |

A denial shows up as a permission refusal with a one-line reason Claude relays. Test locally:
`powershell -File plugins/bbs-sales/hooks/tests/run-tests.ps1`.

## Rollout guide

How this gets introduced to the team, and what "working" looks like: <https://claude.ai/code/artifact/6fd0a004-8323-477d-b461-332fb35afd7e>

---

<sub>Part of the Black Box Safety plugin marketplace. Sibling to `bbs-website`, which maintains the website.</sub>
