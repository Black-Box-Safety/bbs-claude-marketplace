# A primer on the BBS Claude system

For everyone at BBS who works with Claude. Owner: Parker.
As of 2 October 2026. Every capability below points at the file it rests on; status comes
from that skill's `requires:` line (`python3 scripts/check_marketplace.py --requirements`).

---

## 1. The short version

We run Claude inside the tools we already use. It reads our systems of record, follows
BBS playbooks written down once, and hands a person a finished draft: a priced quote, a
filled bid packet, a call list, a reminder email. **A person checks it and a person sends
it.** On Claude Code, managed settings switch sending off for everyone, and Business
Central and Grainger are read-only to Claude.

What it is for: faster RFQ turnaround and less time on lookups and first drafts, with one
source of truth for every fact. That is the aim, not yet a measured result:
`docs/MEASUREMENT.md` holds the measures and has no baseline yet, and none is invented here. What it does not do: decide, send, post, or invent a
number. An unknown value comes back flagged, never guessed.

## 2. What is in the marketplace

The marketplace is one install that gives every teammate the same toolkit. It has three
tiers: BBS plugins (ours), pinned external plugins (forks we control), and the commons
(third-party tools we pin and review). This is the summary; each plugin's own README and
the root `README.md` are where the detail lives.

### BBS plugins

| Plugin | Who it is for | What it does | Start with |
|---|---|---|---|
| **bbs-sales** | Kim, Aanya, Joey, Griffin, Parker | The California state book end to end. Territory: call lists, budget timing, agency and site-visit briefs. Quote desk: RFQ intake, Grainger and NASPO pricing, competitive sourcing, the BBS quote PDF, CA compliance packets, DGS BPO checks. Agents: `supplier-scout` (supplier options from SCPRS, Business Central and the web). | `/ca-rfq`, `/ca-territory-handoff` |
| **bbs-back-office** | Purchasing, AR, accounting | After the win. Where an order stands, which order sits behind a customer PO (`so-search`), what a vendor still owes us (`bbs-po-status`), what a problem order needs (`bbs-order-reconciliation`), and margin after the Grainger rebate (`bbs-rebate-profitability`, not connected yet). Reads Business Central; never posts. | Ask in plain words |
| **bbs-marketing** | Anyone writing outward | One-page sales sheets, campaign email drafts, logo rights checks, prior brochures and decks. Approved wording lives in one claims registry. | `/bbs-one-pager` |
| **bbs-website** | Site maintainers | Price list to live product page: catalog import, contract pricing, variant families, enrichment, storefront pages, quote-bot tuning. | `/bbs-add-product`, `/bbs-new-brand` |
| **bbs-foundations** | Everyone | Shared company facts and certification rules, the doctrine every skill inherits, `/bbs-my-voice` (drafts that sound like you), `/bbs-checkup` (is my machine set up), federal deck copy (`bbs-deck-voice`). | `/bbs-checkup`, `/bbs-my-voice` |
| **bbs-claude-coach** | Everyone, day one | Teaches Claude at BBS in plain language and routes a person to the right playbook. | `/bbs-what-can-i-do` |
| **bbs-tools** | Claude Code only | The `bbs-fill` launcher: the one vetted way Claude runs BBS form and quote scripts, so a crafted command in an inbound PDF cannot run arbitrary code. | (runs underneath) |

### Pinned external plugins (BBS forks)

| Plugin | What it does |
|---|---|
| **claudeforge** | The generic engine behind our `CLAUDE.md` files (size cap, chaining, drift audits). `bbs-foundations` supplies the BBS rules on top. |
| **impeccable** | Design review for anything with a front end: storefront pages, dossiers, internal pages like the team guide. |

### Commons (third-party, pinned and reviewed)

| Plugin | What it does |
|---|---|
| **document-skills** | Anthropic's Word, PDF, Excel and PowerPoint playbooks: RFQ worksheets, bid PDFs, workbooks, decks. |
| **superpowers-chrome** | Drives your own Chrome for research on distributor and agency sites. |
| **caveman** | Optional terse-output mode. |

People learn the vocabulary once: a **skill** is a playbook, a **plugin** is a binder of
playbooks, a **connector** is a live window into a system, a **command** is a shortcut
that starts with `/`.

## 3. The four connectors

| Connector | What Claude can do through it | Who has it | Used today by |
|---|---|---|---|
| **Business Central** (`bc_*`) | Read only. Customers, items, sales orders, quotes and invoices, purchase orders and receipts, vendors, ledgers (about 150 entity sets). | Everyone | `bbs-order-reconciliation`, `so-search`, `bbs-po-status`, `bbs-quote-builder`, `naspo-quote`, the territory and site-visit playbooks |
| **Grainger** (`grainger_*`) | Read only. Search, per-account price, availability, part resolution, cross-reference, accounts. | Everyone who quotes | `grainger-pricing`, `naspo-quote`, `bbs-order-reconciliation`, `grainger-promo-page` |
| **Sales CRM** (`crm_*`) | Reads records and attributes. It **can** update a record; no BBS playbook does yet, and managed settings do not pre-approve it, so it asks first. | Everyone | `bbs-weekly-sales-report`; territory, visit and primer playbooks when present |
| **SCPRS / ca-procurement-intel** (`market_*`, `play_*`) | Read only. State purchase history, spend, last sales, and packaged plays (competitor profile, whitespace, contestable market, reorder timing, receptive buyers, fair-and-reasonable reference). | Reps on the CA state book | `ca-site-visit-brief`, `ca-agency-primer`, `ca-territory-handoff`, `supplier-scout`, `grainger-promo-page` |

Two facts that shape every design below:
- **SCPRS is a slice, not the market.** Totals cover the SB/DVBE-visible harvest, never all
  state spend. Every number from it says so.
- **The Business Central connector is interim.** When Microsoft's official connector works
  in Claude Code, tool names change and the read-only claim must be re-checked
  (`MANAGED-SETTINGS.md`).

## 4. How we automate with them

Three tiers, cheapest first. Nothing below sends, posts, signs a customer's line or changes
Business Central.

### Tier 1: running now (one ask, several systems)

| Workflow | Systems it joins | What comes back | Status |
|---|---|---|---|
| RFQ to signed packet (`/ca-rfq`) | Business Central, Grainger, Microsoft 365 | Filed request, priced quote, filled packet, signed within the delegation, every judgment call listed | Ready today |
| Monday call list (`ca-territory-handoff`) | Business Central, Sales CRM, SCPRS | A dated, prioritized list of who to call and why | Ready today |
| Site visit pack (`ca-site-visit-brief`, then `ca-visit-readiness-review`) | Business Central, Sales CRM, SCPRS | Call plan and pocket card, then a pressure test | Ready today |
| Weekly sales report (`bbs-weekly-sales-report`) | Sales CRM, Business Central | Parker's summary of the CA team's week | Ready today |
| Supplier options (`supplier-scout`) | SCPRS, Business Central, the web | Makers, distributors, alternates; prices only from pages opened | Ready today |
| Problem order (`bbs-order-reconciliation`) | Business Central, Grainger, Microsoft 365 | Which record is wrong, every affected PO, who can approve the fix, money owed back | Ready today |
| Order behind a customer PO; vendor still owes us (`so-search`, `bbs-po-status`) | Business Central | Invoices and SO for a PO; received and outstanding from the lines | Ready once this change merges |

### Tier 2: small builds that join what we already have

All **Not built yet.** Each is one new playbook on existing connectors; only item 7 needs a
new system. Ranked by leverage for the least build.

| # | Workflow | Joins | Output a person acts on | Gate |
|---|---|---|---|---|
| 1 | **Quote outcome write-back.** Today every RFQ sits in the CRM as "Submitted". Read Business Central quotes and orders, match them to CRM records, and propose Won or Lost per record. | Business Central, Sales CRM | A list of proposed updates; the rep approves each write | Parker rules what "Won" means (`canonical-facts.md` already says `bbs_accepted` is not a win) and whether CRM writes get pre-approval |
| 2 | **Reorder outreach.** SCPRS reorder timing, filtered to agencies that bought from us in Business Central, owner from the CRM | SCPRS, Business Central, Sales CRM | A weekly list per rep plus outreach drafts in Outlook Drafts | None beyond the build |
| 3 | **Quote follow-up.** Business Central quotes sent but not accepted, nearing their valid-until date, owner from the CRM | Business Central, Sales CRM, Microsoft 365 | Follow-up drafts in each owner's Drafts | None beyond the build |
| 4 | **Collections run.** Past-due invoices by agency, turned into reminder drafts | Business Central, Microsoft 365 | One draft per agency in Summer's Drafts | Gap 4 (Shopify card payments showing unpaid) must be fixed or flagged on every draft |
| 5 | **Open vendor liability digest.** `bbs-po-status` across every open PO | Business Central | A weekly table of outstanding value by vendor, with the header-flag failures called out | None beyond the build |
| 6 | **Bid price check.** For a competitive bid, SCPRS fair-and-reasonable reference beside our Grainger account price | SCPRS, Grainger | A one-page price position before the rep sets margin | Price rules stay in canon; the page only reports |
| 7 | **SAM.gov opportunities** (federal) | New: the SAM.gov public API | Open solicitations by NAICS code or agency for Kim and Griffin | Key in each person's environment, never git |

### Tier 3: on a schedule

Claude Code can run a saved prompt on a schedule (a Routine) and leave the result for a
person. The natural candidates are Tier 1 and Tier 2 items that already run weekly: the
Monday call list, the weekly sales report, reorder outreach, the vendor liability digest.
Before any of these is scheduled, Parker confirms three things for the scheduled
environment: the connectors it may use, that the send-class denies apply there too, and
where the output lands (a SharePoint folder or Drafts, never an outbound message).

## 5. What we will not automate

- **Sending.** Every email, Teams message and bid stays a person's click.
- **Writing to Business Central.** Read-only by design; posting stays in Business Central's own screens.
- **Signing a customer's or third party's line**, or any line whose signer is unclear.
- **Numbers without a source.** A price, stock level, spend figure, cert or form ID comes from a tool result or a named file, or it is flagged.
- **A second copy of a fact.** One home per fact; playbooks point at it.

## 6. How we keep it safe

| Risk | Control |
|---|---|
| A plausible wrong number on a binding document | Invariants in `AGENTS.md`; values from systems of record only; `check_marketplace.py` on every PR; review by an agent that did not write the change |
| Something gets sent that should not | Managed settings deny send-class tools on Claude Code; drafts only |
| The interim Business Central connector is swapped | Re-verify read-only and tool names at the swap; the skills name `bc_*` tools in one place each |
| SCPRS read as the whole market | Every SCPRS figure states its slice |
| CRM writes go wrong at scale | No playbook writes today; Tier 2 item 1 proposes per record and asks before each write |
| A scheduled run acts without a person | Routines produce files and drafts only; Parker approves each before it is turned on |

## 7. Where to start

1. **Open Claude Code and type `/bbs-what-can-i-do`.** Tell it what you are working on; it
   points you at the right playbook.
2. **Ask in plain words.** You do not need to name a skill or a connector. Claude picks the
   playbook that matches.
3. **Check what comes back, then you send.** Every result says where its numbers came from.
4. **Want one of the Tier 2 items, or something missing?** Tell Parker in one line what you
   asked and what you needed. A missing tool is a request, not a dead end.

---

Owner: Parker Marshall. Last verified 2026-10-02.
