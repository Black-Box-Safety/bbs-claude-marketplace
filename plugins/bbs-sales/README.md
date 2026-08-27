<p align="center">
  <img src="https://img.shields.io/badge/desk-inbound%20state%20RFQ-051c2c" alt="Inbound state RFQ desk">
  <img src="https://img.shields.io/badge/skills-2-b19800" alt="2 skills">
  <img src="https://img.shields.io/badge/pricing-at%20cost%20on%20CA%20schedules-2dd4bf" alt="At cost on CA schedules">
</p>

# bbs-sales

The inbound quote desk for California state business. A buyer emails a request, and this plugin takes it from the inbox to a signed, responsive packet in the buyer's folder — logged first, priced on the right account, certs filled to match.

Reps lose state quotes on the paperwork more often than on the price. A cert with last quarter's solicitation number, an unsigned perjury declaration, a duplicate folder that hides the last quote's precedent — any of those can set the whole bid aside. The plugin makes the boring half automatic so the rep spends their time on the buyer.

**Jump to:** [The two skills](#the-two-skills) · [Setup](#one-time-setup) · [Commands](#commands) · [The rules that don't bend](#the-rules-that-dont-bend) · [Rollout guide](#rollout-guide)

## The two skills

The work splits at a clean seam: get it filed, then get it quoted.

| Skill | Fires when | Stops at |
|---|---|---|
| `ca-rfq-intake` | A request arrives from any State of CA agency — CDCR institution, CalVet home, DSH hospital, Caltrans district, CalFire unit, DWR, CMD. Email with attachments, bare item list, worksheet, portal link, all the same. | The RFQ is logged and the clock is visible. No pricing. |
| `naspo-quote` | A logged RFQ needs a price and a packet, or a buyer sends blank state certs to complete. | Signed packet delivered into the buyer's folder, with a summary of every judgment call. |

**`ca-rfq-intake`** finds or creates the folder under `Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`, saves every attachment as received, opens an `RFQ.md` run record, and adds a row to the buyer's `quote-log.md`. It deliberately stops before pricing. The point of intake is that the deadline becomes something anyone can see; mixing pricing into it is how the due-date field ends up empty.

Creating a second folder for a buyer who already has one is the expensive mistake, because the next quote's precedent search misses it. Search by buyer name and by item before creating anything.

**`naspo-quote`** reads the buyer folder, pulls live Grainger pricing on the institution's account, builds the quote PDF, and fills and signs the compliance packet: OBS Line-Item Cost Worksheet, CalRecycle 74, DGS PD 843, Darfur OBS 1500, OBS 1000 GenAI, and Bidder Declaration GSPD-05-105. It renders every page and looks at it before delivering, because these forms clip long values silently.

Both skills fire on their own when the conversation matches. You do not have to name them.

## One-time setup

Do these once per machine. Skipping any one of them shows up as a confusing failure halfway through a packet, not as a clear error at the start.

**1. Install the PDF libraries.**

```bash
pip install pymupdf pypdf
```

`pymupdf` fills and stamps the forms; `pypdf` reads filled values back out of the archive when the skill mines precedents. No PDF library means no packet.

**2. Create `~/.bbs/vendor_profile.json`.**

This is the single authority for every BBS value that goes on a state form — legal name, address, FEIN, seller's permit, DVBE cert number and expiration, the CUF statement, and Jackson Dalton as the disabled-veteran owner. It lives outside the repo so nobody's certificate numbers end up in git.

Start from the copy already in this marketplace:

```bash
mkdir -p ~/.bbs
cp plugins/bbs-ops/skills/obs-form-filler/assets/bbs_vendor_profile.json ~/.bbs/vendor_profile.json
```

Then open it and confirm every value is current. If an RFQ arrives pre-filled with a BBS field that disagrees with this file, the RFQ is wrong — flag it, don't adopt it.

TODO: confirm whether `~/.bbs/vendor_profile.json` needs a `cuf_statement` key beyond what the bbs-ops copy carries, and whether the signature paths below should also live in this file rather than being passed per-run.

**3. Point at the signature images.** Both PNGs live in OneDrive, not in this repo:

- Parker — `.../Customers/Bechtel/sentinel/vandenburg-sentinel-rfps/RFP-741986-vlc-tempest-filters/signature/parker-signature.png`
- Jackson — `.../Black Box Safety - MASTER/Jackson Dalton Signature/Copy of JACKSON_SIG.png`

TODO: Griffin Forsyth signs most CalRecycle 74s, but no signature PNG path is recorded. Add his file and its path here.

**4. Make sure OneDrive is actually synced.** The whole plugin reads and writes the `Customers/State of CA Agencies/` tree on disk. A folder that is online-only looks empty to Claude, so a precedent search comes back with nothing and the answer is a guess instead of a lookup. Right-click the `State of CA Agencies` folder and choose "Always keep on this device."

## Commands

| Command | Does |
|---|---|
| `/ca-rfq-log` | Log a request you just received: find or create the folder, save the attachments, open `RFQ.md`, update the buyer's quote log. Stops before pricing. |
| `/ca-rfq-quote` | Take a logged RFQ folder through pricing, quote, cert packet, visual verification, and delivery. |

Run them in that order. `/ca-rfq-quote` on an unlogged request works, but you lose the deadline record and the buyer history that makes the next quote faster.

## The rules that don't bend

These four come up on every state quote, and each one exists for a reason worth knowing.

**Price at cost on CA state schedules.** On every California state schedule today the sell rule is `at_cost`: the customer price equals BBS cost, no markup. That is not generosity and not a mistake in the data. BBS is paid through the contract rebate, not the margin on the line. A rep or a code path that adds 20% here produces a quote that is both wrong and uncompetitive. Competitive solicitations are the exception — there the price is a bid and margin is the rep's call.

**Price against the buying institution's own Grainger account.** Discount is per account, so the wrong account returns a price that looks completely valid and is completely wrong. The account number is usually in the agency folder name (`CMC - 887895111 - California Men's Colony`); a buyer note inside the folder that names a different account for their site wins, because it came from the buyer.

**No sales tax on the worksheet.** The OBS Line-Item Cost Worksheet prints "Do not include sales tax" on its face. The agency handles tax on its side. Quote `taxRate = 0` and let the totals match the worksheet exactly — a tax line is a mismatch the buyer has to reconcile before they can award.

**DVBE cert 2009473 expires 12/31/2027.** The DVBE certification is what makes BBS worth quoting to a state buyer with a participation goal, and a packet signed against an expired cert is worse than no packet. Check the expiration against the quote due date before signing anything. Expired, or inside 30 days, means stop and tell the rep.

One more that is not a rule but behaves like one: the `Customers/State of CA Agencies/` tree is the training data. Every blank the agency sent and every filled version BBS returned is in there. When history can answer a question — which form revision this agency uses, what BBS wrote in that field last time, whether this buyer accepted a 0% recycled-content answer — read the corpus instead of guessing or asking the rep.

## Rollout guide

How this gets introduced to the team, and what "working" looks like: <https://claude.ai/code/artifact/6fd0a004-8323-477d-b461-332fb35afd7e>

---

<sub>Part of the Black Box Safety plugin marketplace. Sibling to `bbs-ops`, which maintains the website.</sub>
