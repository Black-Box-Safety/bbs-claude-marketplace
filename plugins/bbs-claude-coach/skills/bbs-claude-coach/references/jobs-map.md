# Jobs map — start from the work in front of you

Everyone gets the whole toolkit. Nothing below is locked to a title. If two rows fit, pick
the closer job and say so.

| The job | First step | Usually lives in | Needs a live connector? |
|---|---|---|---|
| Cold outreach / follow-up email | Ask Claude to draft it; once, run `/bbs-my-voice` so it sounds like you | `bbs-foundations` (voice) | Outlook helps sampling for voice |
| California state RFQ just arrived | Tell Claude what arrived, or `/ca-rfq` (it files first, then prices) | `bbs-sales` | BC, Grainger, M365, SCPRS as assigned |
| Taking over a CA state book / which accounts went quiet / who to call first | Ask for a handoff, or `/ca-territory-handoff` (`ca-territory-handoff`) | `bbs-sales` | **Business Central**; Sales CRM and SCPRS help |
| Prep for a site visit or meeting at a CA state facility | Ask to prep the visit (`ca-site-visit-brief`); agency-wide background is `ca-agency-primer`; review the finished brief with `ca-visit-readiness-review` | `bbs-sales` | **Business Central**; Sales CRM and SCPRS help |
| Weekly sales report for the CA state team | Ask for the weekly sales report (`bbs-weekly-sales-report`) | `bbs-sales` | **Sales CRM**; Business Central and Outlook help |
| When does an agency have money / is June 30 the real deadline? | Ask the timing question (`ca-budget-timing`) | `bbs-sales` | none |
| Price Grainger / NASPO lines | Ask to price the list (Grainger MCP — never memory or the open web) | `bbs-sales` | **Grainger MCP** |
| Fill CA / CDCR compliance packet | Ask after pricing — `ca-form-filler` / packet path | `bbs-sales` | usually local PDF tools from bootstrap |
| Marketing one-pager, campaign email, logo check, a prior brochure or deck | `/bbs-one-pager`, or ask (`sales-one-pager`, `campaign-email`, `marketing-assets`, `deck-precedent`); approved wording is the claims registry; design polish via `impeccable` | `bbs-marketing` | varies |
| Brand page on the storefront | Ask; design polish via `impeccable` | `bbs-website` | **Supabase**, **Shopify** |
| Order / invoice / "what do they owe us?" | Ask about the PO, order, or vendor balance | `bbs-back-office` | **Business Central** |
| Problem order / reconciliation | Ask what the order needs (`bbs-order-reconciliation` lives in `bbs-back-office`) | `bbs-back-office` | **Business Central** |
| AR: what is past due / where we stand with one agency | Ask; Claude reads Business Central (read-only) and says where each number came from. Shopify card payments may still show as unpaid: check before you chase | `bbs-back-office` | **Business Central** |
| AR: past-due reminder email | Ask for the reminder in your Outlook Drafts; once, run `/bbs-my-voice`. You read it and send it | `bbs-foundations` (voice) | **Microsoft 365** (draft only; sending is denied in Claude Code) |
| AR: short payment over a price or quantity | Ask which record is wrong (`bbs-order-reconciliation`); sales decides what goes back to the customer | `bbs-back-office` | **Business Central** |
| Accounting: one question about the books, no export | Ask it in plain words; Claude reads Business Central (read-only) and names the records behind each number | `bbs-back-office` | **Business Central** |
| Accounting: was a promised vendor credit received? | Ask about the PO; `bbs-order-reconciliation` lists credits, free replacements and absorbed freight ("Money owed back to us") | `bbs-back-office` | **Business Central** |
| Accounting: match a statement against an export | Hand over both files; Claude builds the workbook and flags the rows that don't match | commons `document-skills` | none |
| Which order or invoices sit behind a customer PO; what a vendor still owes us | Ask with the PO number or the vendor (`so-search`, `bbs-po-status`); answers come from the lines, never the PO header flag | `bbs-back-office` | **Business Central** |
| Margin after the Grainger rebate | **Not ready yet.** `bbs-rebate-profitability` needs a connector Parker hasn't switched on. Tell Parker if you need it | Parker | n/a |
| Supplier options for an item BBS has never sold | Ask for supplier options; the `supplier-scout` agent searches the web itself and prices only from pages it opened, with link and date. Grainger prices still come from Grainger | `bbs-sales` | none (built-in web search; Firecrawl when assigned) |
| Product research you want to see yourself | Ask Claude to open your real Chrome and look; prices still from a real source | commons `superpowers-chrome` | Chrome/Node from bootstrap |
| What federal solicitations are open for a NAICS code or an agency? | Ask what is open on SAM.gov (`sam-gov-opportunities`); it lists open notices with a set-aside fit column and flags what it cannot tell | `bbs-sales` | **SAM.gov key** in `SAM_GOV_API_KEY` (BBS's one shared key, from Parker; never pasted into a chat) |
| Who won this kind of federal work before / top vendors / BBS's own federal awards | Ask who won (`usaspending-awards`); it reads past contract awards and says what each amount means | `bbs-sales` | none (public API, no key) |
| Channel-partner / federal deck copy | Ask for deck copy in BBS voice (`bbs-deck-voice`) | `bbs-foundations` | document skills for assembly |
| Read or build a PDF / Word / Excel / PPT | Hand the file over or ask to build it | commons `document-skills` | LibreOffice caveat for some PDF paths |
| "Is my machine set up?" | `/bbs-checkup` | `bbs-foundations` | checkup probes the connectors it can |
| "What even is a skill?" | `/bbs-explain-claude` | **this plugin** | none |
| "I want a new shared tool" | See `how-to-extend.md` — tell Parker or propose; do not copy shared skills into `~/.claude/skills/` | Parker / PR | none |

## If they are unsure

Ask one question: **"What are you trying to finish in the next half hour?"** Match the
table. Give **one** first step. Offer a second step only after they finish the first.

## What this map must not do

- Invent a price, cert number, form ID, or signer.
- Say a plugin is "only for sales" or "only for ops" as a hard wall — recommend the fit,
  invite them to use what the job needs.
- Replace the playbooks in `bbs-sales` / `bbs-website` / `bbs-back-office`. Route there.
