<p align="center">
  <img src="https://img.shields.io/badge/desk-CA%20state%20business%2C%20both%20directions-051c2c" alt="California state business, both directions">
  <img src="https://img.shields.io/badge/skills-3-b19800" alt="3 skills">
  <img src="https://img.shields.io/badge/pricing-at%20cost%20on%20CA%20schedules-2dd4bf" alt="At cost on CA schedules">
</p>

# bbs-sales

The plugin for California state business, both directions: the request that comes in, and the
campaign that goes out. A buyer emails an RFQ and this plugin takes it from the inbox to a signed
packet in the buyer's folder. A Grainger rep sends a negotiated price sheet and this plugin turns
it into a landing page an agency buyer can order from, sent to the segment of buyers most likely
to act on it.

Reps lose state quotes on the paperwork more often than on the price. A cert with last quarter's
solicitation number, an unsigned perjury declaration, a duplicate folder that hides the last
quote's precedent: any of those can set the whole bid aside. The plugin makes the boring half
automatic so the rep spends their time on the buyer. The same discipline applies going out: a
promo page that overstates a discount or implies an agency's endorsement is a compliance problem,
not a marketing win, so every page runs through the same brand gate as any printed piece.

**Jump to:** [The three skills](#the-three-skills) · [Setup](#one-time-setup) · [Commands](#commands) · [The rules that don't bend](#the-rules-that-dont-bend) · [Rollout guide](#rollout-guide)

## The three skills

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

## One-time setup

Do these once per machine. Skipping any one of them shows up as a confusing failure halfway through a packet or a page, not as a clear error at the start.

### For `naspo-quote`

**1. Install the PDF libraries.**

```bash
pip install pymupdf pypdf
```

`pymupdf` fills and stamps the forms; `pypdf` reads filled values back out of the archive when the skill mines precedents. No PDF library means no packet.

**2. Create `~/.bbs/vendor_profile.json`.**

This is the single authority for every BBS value that goes on a state form: legal name, address, FEIN, seller's permit, DVBE cert number and expiration, the CUF statement, and Jackson Dalton as the disabled-veteran owner. It lives outside the repo so nobody's certificate numbers end up in git.

Start from the copy already in this marketplace:

```bash
mkdir -p ~/.bbs
cp plugins/bbs-website/skills/obs-form-filler/assets/bbs_vendor_profile.json ~/.bbs/vendor_profile.json
```

Then open it and confirm every value is current. If an RFQ arrives pre-filled with a BBS field that disagrees with this file, the RFQ is wrong: flag it, don't adopt it.

TODO: confirm whether `~/.bbs/vendor_profile.json` needs a `cuf_statement` key beyond what the bbs-website copy carries, and whether the signature paths below should also live in this file rather than being passed per-run.

**3. Point at the signature images.** Both PNGs live in OneDrive, not in this repo:

- Parker: `.../Customers/Bechtel/sentinel/vandenburg-sentinel-rfps/RFP-741986-vlc-tempest-filters/signature/parker-signature.png`
- Jackson: `.../Black Box Safety - MASTER/Jackson Dalton Signature/Copy of JACKSON_SIG.png`

TODO: Griffin Forsyth signs most CalRecycle 74s, but no signature PNG path is recorded. Add his file and its path here.

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
| `/ca-rfq-log` | Log a request you just received: find or create the folder, save the attachments, open `RFQ.md`, update the buyer's quote log. Stops before pricing. |
| `/ca-rfq-quote` | Take a logged RFQ folder through pricing, quote, cert packet, visual verification, and delivery. |

Agent: `supplier-scout` — supplier options for an item BBS has never sourced; dispatched by `bbs-sourcing` step 5c or directly ("find supplier options for MSA 10082709").

Run them in that order. `/ca-rfq-quote` on an unlogged request works, but you lose the deadline record and the buyer history that makes the next quote faster.

`grainger-promo-page` has no slash command yet. Describe the ask ("build a promo page for CAL FIRE from this hot list") and it fires on its own.

## The rules that don't bend

These four come up on every state quote, and each one exists for a reason worth knowing.

**Price at cost on CA state schedules.** On every California state schedule today the sell rule is `at_cost`: the customer price equals BBS cost, no markup. That is not generosity and not a mistake in the data. BBS is paid through the contract rebate, not the margin on the line. A rep or a code path that adds 20% here produces a quote that is both wrong and uncompetitive. Competitive solicitations are the exception: there the price is a bid and margin is the rep's call.

**Price against the buying institution's own Grainger account.** Discount is per account, so the wrong account returns a price that looks completely valid and is completely wrong. The account number is usually in the agency folder name (`CMC - 887895111 - California Men's Colony`); a buyer note inside the folder that names a different account for their site wins, because it came from the buyer.

**No sales tax on the worksheet.** The OBS Line-Item Cost Worksheet prints "Do not include sales tax" on its face. The agency handles tax on its side. Quote `taxRate = 0` and let the totals match the worksheet exactly: a tax line is a mismatch the buyer has to reconcile before they can award.

**DVBE cert 2009473 expires 12/31/2027.** The DVBE certification is what makes BBS worth quoting to a state buyer with a participation goal, and a packet signed against an expired cert is worse than no packet. Check the expiration against the quote due date before signing anything. Expired, or inside 30 days, means stop and tell the rep.

One more that is not a rule but behaves like one: the `Customers/State of CA Agencies/` tree is the training data. Every blank the agency sent and every filled version BBS returned is in there. When history can answer a question (which form revision this agency uses, what BBS wrote in that field last time, whether this buyer accepted a 0% recycled-content answer), read the corpus instead of guessing or asking the rep.

## Hooks (v1.1)

Deterministic guards, PowerShell, shipped with the plugin. They fire on Windows rep machines
without any per-machine setup.

| Hook | When | What it does |
|---|---|---|
| `guard-tree.ps1` | Before Bash / Write / Edit | Denies renames or moves inside `All RFQ's by Agency` (folder names carry account numbers); denies creating a buyer or agency folder whose name near-duplicates a sibling (case, spaces, `(ALL)`, a dropped or added word, two typos); denies overwriting anything under `FILLED/` |
| `desk-context.ps1` | Session start inside a buyer folder | Puts the last rows of `quote-log.md` and the latest `FLAGS.md` entries in front of Claude before the first prompt |

A denial shows up as a permission refusal with a one-line reason Claude relays. Test locally:
`powershell -File plugins/bbs-sales/hooks/tests/run-tests.ps1`.

## Rollout guide

How this gets introduced to the team, and what "working" looks like: <https://claude.ai/code/artifact/6fd0a004-8323-477d-b461-332fb35afd7e>

---

<sub>Part of the Black Box Safety plugin marketplace. Sibling to `bbs-website`, which maintains the website.</sub>
