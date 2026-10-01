# Team rollout explainer: design brief

**For:** Parker Marshall, Sales Manager, who runs the rollout.
**Audience of the finished page:** Berenice and Joyce Newell (purchasing), Summer (accounts
receivable), Bella and Annette Somers (accounting), Emily (body armor administration and
Shopify work).
**Written:** 2026-10-01 by the BBS explainer (`.claude/agents/bbs-explainer.md`).
**Builds next:** `IMPLEMENTATION-PROMPT.md` in this folder. It carries the exact page copy,
the grounding table and the acceptance checks. The copy lives there once, because the
builder needs it verbatim (AGENTS.md invariant 2). This brief holds the reasoning.

Nothing here is a promise of a capability the marketplace does not ship. Every tool named
below was read in this repo, its path is given, and its status comes from its own
`requires:` line (`python3 scripts/check_marketplace.py --requirements`, run 2026-10-01).

---

## 1. What we are making, in one paragraph

One private web page (an Artifact) that each of the six people opens from a link Parker
sends. The link carries their name (`#berenice`, `#summer`, ...), so the page opens on
**their** week first: three or four jobs they already do, written as before and after,
each tagged honestly as *Ready today*, *On Parker's list* or *Not built yet*. Below that
come the shared pieces in this order: what Claude is at BBS (one picture), the guardrails
(one picture), and how to start tomorrow (three steps that hand them to the coach plugin's
`/bbs-what-can-i-do`). The page does not teach Claude in general. It routes into the coach,
which already does that (`plugins/bbs-claude-coach/`).

---

## 2. Audience map

Notation. **Week** is inference, marked as such, drawn from the marketplace skills that
name the work, the storefront team page (`bbs-shopify/theme/templates/page.about.json`,
role lines only) and the `bbs-shopify` planning docs. It has not been confirmed with the
person. **Status** uses three values:

- **Ready today**: the skill or connector exists and its `requires:` are on the standard
  connector list everyone gets (Business Central, Microsoft 365, Grainger, Sales CRM;
  `docs/ADMIN-RUNBOOK.md` §3).
- **On Parker's list**: the skill exists but cannot run for this person today (a retired
  connector, a connector not assigned, a stale data file).
- **Not built yet**: a gap. Listed for the roadmap, never shown as available.

Parker's account-synced skills are **not presented**. Per `HANDOFF.md` they are personal
copies being retired, and they live only in his account. Five of them (`bbs-po-status`,
`so-search`, `bbs-rebate-profitability`, `bbs-pricelist-import`, `dgs-bpo-item-check`)
have a marketplace copy that is the maintained one, and the page names that copy. The
sixth was replaced: `grainger-cart-info` (account skill, not in the marketplace repo) was
merged into `rfq-item-extract`, which is what the page names.

### 2.1 Purchasing: Berenice

- **Week (inference).** Places and tracks vendor POs; checks what a vendor has actually
  shipped against what is outstanding; works problem orders (wrong item or size, short
  shipment, a price or unit-of-measure discrepancy on a customer PO line); chases vendor
  credits; works out who at an agency can approve an amendment. Grounds:
  `plugins/bbs-back-office/skills/bbs-order-reconciliation/SKILL.md` names her ("Berenice's
  most common dead end", Phase 10) and is written for purchasing; `bbs-po-status` describes
  the vendor-receipt work.
- **Repetitive parts.** Opening four records (what the customer asked for, what we quoted,
  what the PO says, what shipped) to find which one is wrong; searching email for what was
  already promised; adding up receipt lines by hand because the PO header flag lies;
  retyping item numbers into the Grainger portal.
- **System of record.** Business Central (POs, receipts, sales orders); SharePoint
  `MASTER/Customers/...` (customer PO PDFs, processing sheets); Outlook.
- **Tools that remove a step.**

  | Job | Tool | Path | Status |
  |---|---|---|---|
  | Problem order: which record is wrong, every affected PO, who can authorize the fix | `bbs-order-reconciliation` | `plugins/bbs-back-office/skills/bbs-order-reconciliation/SKILL.md` | Ready today (needs Business Central, Grainger, Microsoft 365, and the customer folders synced) |
  | Money owed back to us: credits promised, free replacements, freight we absorbed | Same skill, Phase 12 "Money owed back to us" | same | Ready today |
  | Ask in English or Spanish; identifiers kept exactly as printed | Same skill, "Writing for the person you are helping" | same | Ready today |
  | Items out of a Grainger cart PDF or screenshot as `ITEM#,QTY` for the portal | `rfq-item-extract` | `plugins/bbs-sales/skills/rfq-item-extract/SKILL.md` | Ready today (`requires: []`) |
  | What a vendor still owes us, from the receipt lines, never the header flag | `bbs-po-status` | `plugins/bbs-back-office/skills/bbs-po-status/SKILL.md` | On Parker's list: `requires: [bc-mcp-proxy]`, a retired connection; the README forbids quietly retargeting it |

- **Before → after, in their words.**
  - Before: "Someone says the gloves are wrong and I open the PO, the bid sheet, the order
    sheet and Business Central, then dig through email to see what was promised."
    After: "I give Claude the PO and the line. It tells me which record is wrong, every PO
    with the same line, and who can approve the fix. I decide what happens next."
  - Before: "I retype item numbers and quantities from a cart PDF." After: "I drop in the
    PDF and paste back the list it gives me. I check the count."
- **Honest gaps (roadmap).**
  1. `bbs-po-status` needs moving off the retired Business Central link (Parker's call; the
     back-office README names it a gap on purpose).
  2. No late-PO or expediting view: "which vendor POs are past the date the vendor
     committed to". Not built.
  3. The vendor performance line the reconciliation skill asks for (vendor, failure,
     order, date, cost) has no shared place to land, so it stays an anecdote. Not built.
  4. No vendor bill against PO against receipt check (three-way match). Not built.
  5. Purchasing has no set-up path of its own: `docs/REP-SETUP.md` assumes the quote desk
     workspace, and `/bbs-checkup` check 6 looks for the RFQ desk folder (see §2.6).

### 2.2 Purchasing: Joyce Newell (Parker: "maybe")

- **Week (inference).** Handles POs on the quote desk today (Parker's words; also
  `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`,
  "Quote desk (2026-07): Joyce Newell (POs)"). Likely: a customer PO arrives, she finds
  the quote and sales order behind it, checks items against the DGS BPO, gets Grainger
  items into the portal. She is **not** a signature delegate (canonical-facts, "People and
  signatures"), so the page never suggests she signs anything.
- **Repetitive parts.** Finding the sales order behind a customer PO number; retyping
  cart items; checking part numbers against the BPO list.
- **System of record.** Business Central; SharePoint customer folders; Outlook.
- **Tools.**

  | Job | Tool | Path | Status |
  |---|---|---|---|
  | Show a sales order or invoice, header and every line, from its number | Business Central connector (`bc_get_sales_document`) | `plugins/bbs-back-office/skills/bbs-order-reconciliation/references/tool-recipes.md` | Ready today |
  | Cart PDF or screenshot to `ITEM#,QTY` | `rfq-item-extract` | `plugins/bbs-sales/skills/rfq-item-extract/SKILL.md` | Ready today |
  | Problem order | `bbs-order-reconciliation` | as above | Ready today |
  | Which sales order is this customer PO, even before it is invoiced | `so-search` | `plugins/bbs-back-office/skills/so-search/SKILL.md` | On Parker's list: `requires: [bc-mcp-proxy]` |
  | Is this Grainger part on the DGS BPO | `dgs-bpo-item-check` | `plugins/bbs-sales/skills/dgs-bpo-item-check/SKILL.md` | On Parker's list: bundles the FY25-26 list and warns it is stale; FY26/27 list is waiting on Aanya (`docs/STEWARD.md`, item 1) |

- **Before → after.** Before: "A PO comes in and I search Business Central screens for
  the order behind it." After: "I give Claude the order number and get the whole order
  back, every line, to check against the PO."
- **Gaps.** 1. `so-search` on the retired link. 2. BPO list for FY26/27. 3. No "customer
  PO arrived: compare it to the quote line by line before order entry" check. Not built
  (the BC assessment's Gap 1, `docs/assessments/2026-09-11-bc-assessment.md`).
  4. Same set-up gap as §2.6. 5. Her inclusion is Parker's call; the page treats her as a
  one-line data entry that can be removed.

### 2.3 Accounts receivable: Summer

- **Week (inference).** Invoicing and collections for government buyers (storefront team
  page role line). Likely: reading the aging, chasing past-due agency invoices, answering
  "did you get our payment" and "send me a copy of the invoice", matching remittances that
  quote a PO number to invoices, handling short-pays that come from a price or quantity
  dispute.
- **Repetitive parts.** Looking up open invoices one agency at a time; writing the same
  reminder email; tracing a short-pay back through sales to find out why.
- **System of record.** Business Central (invoices, AR); Outlook.
- **Tools.**

  | Job | Tool | Path | Status |
  |---|---|---|---|
  | Who owes us, what is past due; where we stand with one agency | Business Central connector (`bc_list_unpaid_invoices`, `bc_customer_snapshot`) | `plugins/bbs-back-office/skills/bbs-order-reconciliation/references/tool-recipes.md`; connector row "Quote of record, AR, open orders" in `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` | Ready today (read-only) |
  | Reminder email drafted into her own Outlook Drafts | Microsoft 365 connector, draft tools allowed, send denied | `plugins/bbs-foundations/docs/bbs-managed-settings.json` (allow and deny lists) | Ready today |
  | Drafts that sound like her | `/bbs-my-voice` | `plugins/bbs-foundations/commands/bbs-my-voice.md` | Ready today |
  | A short-pay caused by a price or quantity dispute | `bbs-order-reconciliation` (names "purchasing or AR") | as above | Ready today |
  | Which invoices sit under a customer PO | `so-search` | `plugins/bbs-back-office/skills/so-search/SKILL.md` | On Parker's list |

- **Before → after.** Before: "I pull the aging, then open each agency to see what is
  still open." After: "I ask Claude what is past due, or where we stand with one agency,
  and get the open invoices, orders and quotes in one answer." Before: "I write the same
  reminder again." After: "Claude puts a draft in my Outlook Drafts that sounds like me.
  I read it and send it."
- **Gaps.** 1. No collections playbook (aging to a tiered set of reminder drafts per
  agency, with history). Not built. 2. No remittance matching (payment advice to
  invoices). Not built. 3. `so-search` on the retired link. 4. Shopify card-paid orders
  showing as unpaid in Business Central made the unpaid-invoice list noisy as of the
  2026-09-11 assessment (`docs/assessments/2026-09-11-bc-assessment.md`, Gap 4). Confirm
  whether that is fixed before Summer relies on the list. 5. No statement-of-account or
  invoice-copy pack. Not built.

### 2.4 Accounting: Bella and Annette Somers

Parker groups Annette under Accounting (Jackson's announcement titled her Accounts
Receivable Specialist, joined 2026-09-30). The page uses Parker's grouping and shows no
titles. The coach's rule that nothing is locked to a desk
(`plugins/bbs-claude-coach/skills/bbs-claude-coach/references/jobs-map.md`) lets her use
Summer's card too, and the page links to it.

- **Week (inference).** Billing and reconciliation (team page role line for Bella).
  Likely: vendor bills against POs, month-end, credits and returns, margin questions,
  Grainger rebate tracking.
- **Repetitive parts.** Building a filter or an export to answer one question; copying
  columns between spreadsheets; reconstructing an order's history to find a missing
  credit.
- **System of record.** Business Central.
- **Tools.**

  | Job | Tool | Path | Status |
  |---|---|---|---|
  | Ask Business Central a question in plain words, read-only, with sources named | Business Central connector (`bc_query_entity` and the rest; about 150 entity sets incl. GL entries, vendors, purchase invoices) | `plugins/bbs-back-office/skills/bbs-order-reconciliation/references/tool-recipes.md`; README "tells you where every number came from" | Ready today |
  | Money owed back to us | `bbs-order-reconciliation`, Phase 12 | as above | Ready today |
  | Build or read a workbook, PDF or statement | `document-skills` (pinned commons) | `docs/COMMONS.md`; jobs map row "Read or build a PDF / Word / Excel / PPT" | Ready today |
  | Margin after the Grainger rebate, by contract code | `bbs-rebate-profitability` | `plugins/bbs-back-office/skills/bbs-rebate-profitability/SKILL.md` | On Parker's list: `requires: [cdata-connect]`, not on anyone's connector list; README forbids retargeting it quietly |
  | Open vendor liability | `bbs-po-status` | as above | On Parker's list |

- **Before → after.** Before: "I export to Excel to answer one question." After: "I ask
  the question and Claude reads Business Central and tells me where each number came
  from." Before: "A vendor credit was promised and I can't tell if it ever landed."
  After: "When Claude rebuilds an order's history it lists every credit promised,
  replacement shipped and freight we absorbed, so I know what to chase."
- **Gaps.** 1. Rebate margin needs a connector decision. 2. No month-end close checklist
  playbook. Not built. 3. No vendor statement reconciliation or three-way match. Not
  built. 4. The BC assessment found contract and customer dimensions "apparently never
  populated" (Gap 3), while `bbs-rebate-profitability` depends on the contract-code
  dimension. Confirm before anyone trusts a rebate figure. 5. Shopify cash application
  (same as §2.3 gap 4).

### 2.5 Body armor administration and Shopify: Emily

- **Week (inference).** Coordinates body-armor orders and fittings so officers get the
  right fit on contract (team page role line). From `bbs-shopify` planning docs
  (background only): owns production product options for the agency carrier programs
  (sizes, placards), supplies lead times and sizing guides, answers agency coordinators,
  works with Point Blank. Officer orders flow from Shopify into Business Central sales
  orders.
- **Repetitive parts.** Answering the same sizing, lead-time and order-status questions;
  looking up an order; untangling a wrong-size delivery; keying price-list rows.
- **System of record.** Shopify (production store), Business Central, Outlook.
- **Tools.**

  | Job | Tool | Path | Status |
  |---|---|---|---|
  | Replies to coordinators drafted into her Outlook Drafts, in her voice | Microsoft 365 connector + `/bbs-my-voice` | `plugins/bbs-foundations/commands/bbs-my-voice.md`; `bbs-managed-settings.json` | Ready today |
  | Look up an order that reached Business Central (header and lines) or what is still open for an agency | Business Central connector | `.../references/tool-recipes.md` | Ready today |
  | Wrong size, shortage or lost shipment on an armor order | `bbs-order-reconciliation` | as above | Ready today |
  | A Point Blank price sheet cleaned into the BBS import template | `price-list-cleaner` | `plugins/bbs-website/skills/price-list-cleaner/SKILL.md` | On Parker's list (`requires: [python3, pymupdf, pandas]`; pandas is not in the bootstrap, and the output path `templates/2026-{slug}.csv` assumes the website repo layout). Loading into the catalog needs Supabase, which is site-maintainer only, so that step stays with Parker |
  | A body-armor email or one-page piece in the public-safety voice | `campaign-email`, `sales-one-pager` | `plugins/bbs-marketing/skills/`; voice rules `plugins/bbs-marketing/references/VOICE.md` | Ready today |

- **Before → after.** Before: "I answer the same sizing and lead-time email over and
  over." After: "Claude drafts the reply in my Drafts, in my voice, from what I tell it. I
  check it and send it." Before: "An officer got the wrong size and I go back through the
  order, the PO and the emails." After: "Claude lines up what was ordered, what the PO
  says and what shipped, and tells me which one is wrong."
- **Gaps.** 1. No Shopify connection for her: the connector matrix keeps Shopify admin to
  Parker and Griffin (`MANAGED-SETTINGS.md`, connector table). 2. The website plugin
  works the dev store (`bbs-supabase-test`, theme "BBS — Field Manual") while the live
  store she works in is a different store and theme (`bbs-shopify/README.md`;
  `bbs-shopify/docs/plans/2026-09-25-bc-order-integration.md`, finding 1). Its storefront
  skills do not apply to her store yet. 3. The agency-carrier procedure
  (`carter-carrier-builder`) lives in the `bbs-shopify` repo on a branch, not in the
  marketplace. 4. No officer-order status view joining Shopify order, Business Central
  sales order and Point Blank PO. Not built. 5. No product-options audit (for example,
  a size missing from an agency's options, which the 2026-09-15 plan logged as a live
  defect). Not built.

### 2.6 Shared rollout gaps (every role)

1. **Set-up is written for the quote desk.** `docs/REP-SETUP.md` opens the quote-desk
   VS Code workspace; `/bbs-checkup` (`plugins/bbs-foundations/commands/bbs-checkup.md`)
   check 6 expects the `All RFQ's by Agency` folder and a desk `CLAUDE.md`, and check 11
   reports signature images for the six delegates. For these six people check 6 will FAIL.
   Either add a role-aware note to the checkup or tell them in advance. The page does not
   send them to `/bbs-checkup` for that reason.
2. **The feedback path names the sales channel.** `TOOLKIT.md` and `how-to-extend.md` say
   "the Teams sales channel". The page says "tell Parker in one line" and names no channel.
3. **The coach's jobs map has no AR, accounting or Shopify rows**
   (`.../references/jobs-map.md`). `/bbs-what-can-i-do` will route them to the generic
   "Order / invoice" row. Adding three rows there is the cheapest improvement this rollout
   can make, and it keeps the page and the coach from disagreeing.
4. **The reconciliation skill reads the customer folders from disk.** Phase 1 searches
   `Black Box Safety - MASTER/Customers`. Confirm each person has that library synced.
5. **Connector assignment.** Confirm each of the six has Business Central, Microsoft 365
   and Grainger assigned (`docs/ADMIN-RUNBOOK.md` §3 says everyone does).

---

## 3. The core narrative and the metaphor

**Narrative, in three beats.**

1. *Your week, minus the lookups.* Lead with their own task, not with Claude. Each person
   sees three or four things they already do and what changes.
2. *What it is.* One picture: an assistant at your desk who follows the BBS playbooks and
   looks through live windows into the systems you already use, then hands you a
   draft.
3. *What it will never do.* In Claude Code, drafts and never sends; reads Business Central, never changes it;
   never reads anyone's mail but your own, and only when you ask.

Then a three-step start that ends in the coach plugin.

**The metaphor: an assistant at your desk, with the BBS playbooks and a window onto
each system.**

| Term people will hear | In the picture | One line on the page |
|---|---|---|
| Claude | An assistant at your desk | Does the lookups and the first draft |
| Skill | A playbook | The BBS way of doing one job, written down. Claude picks the right one when your request matches |
| Plugin | A binder | A set of playbooks for one area. Yours are already on your computer |
| Connector | A window | A live view into a system you already use. Parker switches these on per person. Business Central and Grainger are read-only; Outlook, SharePoint and the CRM are not (Claude can write drafts, files and CRM records), so "read-only" is never said of connectors in general |
| Command | A shortcut | A word you type that starts with `/`, like `/bbs-what-can-i-do` |
| You | The person who decides | You check it, you decide, you send |

**Why this one.**

- It is Anthropic's own frame, adapted. Anthropic describes building a skill as "putting
  together an onboarding guide for a new hire" (engineering blog) and skills as
  "specialized training manuals" (Skills explained); its plugin lesson says "a plugin is a
  packaged set of skills built around a job" and "the expertise travels with the install,
  not the person". Playbook and binder are those ideas in BBS words.
- It builds on the coach instead of competing. The coach glossary already says a skill is
  "a playbook Claude follows" and a connector is "a live link to a real system"
  (`plugins/bbs-claude-coach/skills/bbs-claude-coach/references/glossary.md`). The page
  keeps "playbook" and turns "live link" into "window". An earlier draft said "read-only
  window"; Rex's review of PR #45 caught that only Business Central and Grainger are
  read-only, so the read-only tag sits on those two tiles alone.
- It answers the split Anthropic draws: "MCP connects Claude to data; Skills teach Claude
  what to do with that data." Window and playbook are exactly those two halves.
- There is house precedent. Parker's own plain-English guide in `bbs-shopify`
  (`docs/guide-for-parker.md`) explains git with a recipe binder. Binders already land
  here.
- **"Assistant", not "new hire" or "digital employee".** The audience's fear is
  replacement. An assistant works for you; a new hire competes with you. The picture
  always ends with the person.

**Rejected.** "USB-C port for AI" (the MCP docs): it explains a standard, which is a
developer's concern, and says nothing about access or safety. "Apps on a phone"
(practitioner blogs): implies people install things themselves and that skills act on
their own. "Digital employee": feeds the fear we most need to remove.

---

## 4. Guardrails framing

Said early (a one-line strap in the page header) and then in full (G3). Four promises,
each grounded:

1. **Claude drafts. You send.** In Claude Code, Outlook send, send-draft and forward, Teams messages,
   meeting responses, SignNow invites and QuickBooks sends are denied for everyone in
   managed settings. Those settings do not reach the ordinary claude.ai chat, where the
   same connectors are live, so the page scopes the claim to Claude Code (`plugins/bbs-foundations/docs/bbs-managed-settings.json`,
   `permissions.deny`). Drafting into your own Outlook Drafts is allowed.
2. **It reads, it does not change.** The Business Central connector is read-only; every
   Business Central and Grainger tool on the allow list is a read
   (`bbs-managed-settings.json`, `permissions.allow`; `MANAGED-SETTINGS.md` connector
   table). "Will not ... write to Business Central" (`README.md`, "What it will not do").
3. **The right signer on the right line.** Signatures belong to the six people counsel's
   authorization covers, on the lines each may sign
   (`plugins/bbs-sales/references/ca-form-rules.md`, "Who signs what" and "Rep-signed lines and delegated signatures";
   canonical-facts "People and signatures"). None of the six readers is a delegate, so the
   page states the rule without names: "Claude never signs for you and never puts anyone's
   signature on a line that isn't theirs."
4. **Your mailbox is yours.** The Microsoft 365 connector works as the person signed in.
   `/bbs-my-voice` reads only your own Sent Items and stops if the mailbox is someone
   else's (`plugins/bbs-foundations/commands/bbs-my-voice.md`, step 1). Nobody's mail is
   read unless they run it themselves.

Plus the rail the coach already teaches, said once: **never an invented number**. Unknown
values come back flagged (`plugins/bbs-claude-coach/skills/bbs-claude-coach/references/aup-rails.md`).

**Tone.** Protection, not control (the coach's own stance, `aup-rails.md`, "Tone when
coaching"). The rails are why it is safe to try things.

**Certification language** appears once, inside the "built in" tile, channel named both
ways: "DVBE wording for California state work, SDVOSB for federal." The page never says
"small business" (canonical-facts, "Small-business status is channel-dependent").

---

## 5. The visual set

### 5.0 Page architecture: one page, a person picker, a link per person

**Choice.** One Artifact page. A person picker at the top (six names grouped under four
role headings). Each person has a hash link (`#berenice`, `#joyce`, `#summer`, `#bella`,
`#annette`, `#emily`). Opening a link, or tapping a name, puts that person's section
directly under the header, before anything general.

**Why not per-role pages.** The "what is this", guardrails and start sections would exist
four times and drift (invariant 2). One URL is also one thing for Parker to update. Roles
overlap (the coach's rule) and a single page lets Annette see Summer's card with one tap.
Hash links give each person the "my own section first" experience per-role pages would.

**Order when a person is chosen.** Header strap → their section (G2) → G1 → G3 → G4 →
"Coming next" (their gaps) → other people (collapsed). With no name chosen: header → picker
→ G1 → G3 → G4.

### G1. What this is

- **Purpose.** Give everyone one picture and five words they keep.
- **Layout.** Three columns, left to right: *Where the facts live* (Business Central,
  Outlook, SharePoint, Grainger) → *Who does the legwork* (Claude, holding a binder of
  playbooks) → *Who decides* (you). Dashed lines with an eye glyph from the systems to
  Claude, labelled "looks in"; a "read-only" tag on the Business Central and Grainger tiles
  only. One solid arrow from Claude to you labelled "a
  draft". One arrow out of you labelled "you send". Below, a five-row legend (the table in
  §3). At phone width the three columns stack top to bottom and the arrows turn downward.
- **Hierarchy.** "You" is the heaviest node (navy fill, gold rule). Claude is mid weight.
  Systems are light. The eye reads to the right and ends on the person.
- **Data shown.** System names only. No numbers, no records, no customers.
- **References.** Anthropic, Skills explained (the data vs. know-how split); Mobbin:
  Runner "Context in, action out" (apps around the job, review before anything goes out);
  Retool authenticate screen (person, check, system in one line).
- **Why this form.** A left-to-right flow carries a sequence and an ending; a hub-and-spoke
  diagram would put Claude in the middle, which is the wrong emphasis. A comparison table
  (Anthropic's five-way table) is too much vocabulary for this audience: subagents,
  projects and prompts are left out on purpose.
- **Copy.** `IMPLEMENTATION-PROMPT.md`, copy deck §C3.

### G2. Your week, before and after (one component, four role instances)

- **Purpose.** The reason anyone keeps reading: their own Tuesday minus the part they
  dislike.
- **Layout.** A card per person (Berenice and Joyce share the Purchasing heading with one
  card each; Bella and Annette share one Accounting card that names both). Inside: a
  role line, a one-sentence promise, then three to four **row-matched pairs**: left
  "Today" (muted, with a small ✕ glyph), right "With Claude" (full weight, ✓ glyph). Each
  pair has a status chip and a "Try saying" line with a copy button holding the exact
  sentence. A disclosure "Under the hood" names the playbook for the curious. At phone
  width each pair stacks Today over With Claude.
- **Hierarchy.** Person's name and role first; promise line; *Ready today* rows above
  *On Parker's list* rows. *Not built yet* rows never appear here; they go to "Coming
  next".
- **Data shown.** Tasks and the systems they touch. Placeholders (`PO ____`, `SO-____`)
  where an identifier would go. No vendor or agency names, no amounts.
- **References.** Mobbin: Ploy "today / on Ploy" row-matched table; V7 before (muted, ✕)
  vs after (bright, ✓); Anthropic Claude for Small Business "prompt card" (the exact
  sentence to type, then what you get).
- **Why this form.** Row-matching makes each change legible on its own; two free-floating
  lists make the reader do the matching. Avoids the Descript and Titan pattern of
  before/after time numbers: we have none we can stand behind.
- **Copy.** Copy deck §C2.

### G3. The guardrails

- **Purpose.** Remove the fear of breaking, sending or snooping, early and plainly.
- **Layout.** Top: a four-step horizontal flow, "You ask → Claude looks →
  Claude drafts → You check and send", with the last step visually owned by the person
  (filled node, the only gold accent). Below: four tiles, each icon + bold line + one
  sentence: In Claude Code, drafts and never sends · Reads Business Central, never changes it · Right signer, right line · Your
  mailbox is yours. A fifth tile, quieter: "Rules are built in" (never an invented number;
  certification wording by channel).
- **Hierarchy.** The flow's final step and tile 1's heading, "In Claude Code, it drafts and never sends.", carry the weight.
- **Data shown.** None.
- **References.** Mobbin: Runner "Review before anything goes out" (numbered status list,
  last step human); Discord authorize screen ("cannot read your messages or send messages
  as you", the cannot line with a lock); WhatsApp Meta AI intro ("Personal messages stay
  private", icon + bold + one sentence); Meta AI "You're in control". Anthropic Claude for
  Small Business, "You stay in charge".
- **Why this form.** A flow shows *where* the human sits; tiles answer the four specific
  fears one at a time. A paragraph of policy (the AUP) is correct but nobody new reads it;
  the page links to it rather than restating it.
- **Copy.** Copy deck §C4.

### G4. Start tomorrow

- **Purpose.** One concrete next step, and a hand-off to the coach.
- **Layout.** A three-item checklist card with a progress ring (purely visual; nothing is
  stored). 1. Get set up once. 2. Type `/bbs-what-can-i-do`. 3. Try the first sentence from
  your card. A footer line: "Something missing? Tell Parker in one line." Below it, a quiet
  link row: `/bbs-explain-claude` for the words, `/bbs-start` for one first step.
- **Hierarchy.** Step 2 is the primary action. Each step has one verb.
- **References.** Mobbin: Google Workspace "You're on your way" (progress, one action per
  step); Remote Recruit checklist (locked rows for steps not available yet); Vanta starter
  guide (dependent steps marked).
- **Why this form.** A checklist with three items is finishable in one sitting; a tour or
  video is not. It ends inside the coach, so the page does not become a second manual.
- **Copy.** Copy deck §C5.

### "Coming next" (not a graphic)

A short list of the person's *Not built yet* and *On Parker's list* items in plain words,
with "Tell Parker which one you want first." Pattern: Remote's locked checklist rows.
Honest gaps build trust with a skeptical reader; hiding them would cost it the first time
they hit one.

---

## 6. Research notes

### Anthropic

| Source | What it says | Borrow | Avoid |
|---|---|---|---|
| [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | "Building a skill for an agent is like putting together an onboarding guide for a new hire." Progressive disclosure: name, then body, then files | The onboarding/playbook frame | The three-level loading diagram: plumbing |
| [Agent Skills overview (docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) | Skills "organized like an onboarding guide you'd create for a new team member"; "Claude uses it automatically when relevant" | "You don't call it; Claude notices the job" (matches the coach glossary) | File-structure detail |
| [Skills explained](https://claude.com/blog/skills-explained) | Skills as "specialized training manuals"; "MCP connects Claude to data; Skills teach Claude what to do with that data"; a five-way comparison table | The data vs. know-how split (window vs. playbook) | The five-way table: too many terms for this audience |
| [Introducing Agent Skills](https://claude.com/blog/skills) | "Claude will only access a skill when it's relevant"; `skill-creator` builds a skill by interview | Reassurance that skills stay out of the way | Developer install paths |
| [Customize Cowork with plugins](https://claude.com/blog/cowork-plugins) | Plugins "turn Claude into a specialist for your role, team, and company"; bundle skills, connectors, commands | "Specialist for your role" supports a per-role page | Product-specific surfaces (Cowork) we are not rolling out |
| [Claude Academy: Plugins, encode your team's expertise](https://academy.claude.com/courses/introduction-to-claude-cowork/plugins-cowork-as-a-specialist) | "A plugin is a packaged set of skills built around a job"; "the expertise travels with the install, not the person"; "the output is still yours to review" | Binder = built around a job; the review line | The interactive mock plugin explorer: too much for six readers |
| [Use plugins in Claude (Help Center)](https://support.claude.com/en/articles/13837440-use-plugins-in-claude) | Plugins bundle skills, connectors and sub-agents "so you get a ready-to-go setup from your first conversation" | "Already installed for you" | Install steps (Parker handles them) |
| [Claude for Small Business](https://claude.com/solutions/small-business) | "You stay in charge. Claude drafts and prepares. You decide what goes out." Prompt card → connectors → outcome; "nothing sends or pays without your OK, and Claude only sees what your accounts allow" | The prompt card; "you stay in charge"; "only sees what your accounts allow" | Customer quotes with hours saved and dollars recovered: we have no grounded numbers |
| [Using Claude for your small business (Academy)](https://academy.claude.com/tutorials/using-claude-for-your-small-business) | Per example: the prompt, what Claude does at each step, what you have when done; "The big decisions stay with you"; "Your existing permissions hold" | Ask → steps → result rhythm for G2 rows | Month-close and payroll examples we do not ship |
| [What is MCP](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro) | "Think of MCP like a USB-C port for AI applications" | Nothing for this audience | The USB-C metaphor (see §3) |
| [How Anthropic teams use Claude Code (PDF)](https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf) | Finance staff wrote plain-text descriptions of their workflows; teams held sessions demonstrating their workflows to each other | Show-and-tell sessions; "describe how you do the job" as the path to a new playbook (the coach's `how-to-extend.md` §4 already says this) | Engineering examples |

### Practitioners and companies

| Source | What they lead with | Borrow | Avoid |
|---|---|---|---|
| [Zapier HR-led AI transformation work kit](https://zapier.com/playbooks/hr-automation) | Open-sourced internal playbooks; HR practitioners building their own tools; keeping people in the loop | Publish the playbooks openly; let the function own its tools | Their adoption percentage: it is theirs, not ours |
| [CBTS: rolling out Claude for Enterprise to all employees](https://www.cbts.com/insights-blog/how-to-roll-out-claude-for-enterprise-to-all-employees-and-get-73x-roi) | ROI multiples and hours-per-week claims | Pilot before company-wide | **Counter-example.** Leading with big multiples is what a skeptical, numbers-literate accounting team discounts on sight |
| [Raj Sanghvi, "Your non-technical team just became dangerous" (LinkedIn, excerpt only; page blocked scraping)](https://www.linkedin.com/pulse/your-non-technical-team-just-became-dangerous-heres-how-raj-sanghvi-zyumc) | "We introduced one tool at a time, let teams find their own use cases, and built internal playbooks based on what actually worked" | One first ask per person; grow from what they use | Hype headline |
| House precedent: `bbs-shopify/docs/guide-for-parker.md` (background, not presented) | Explains git with a kitchen analogy and a recipe binder | Binder language already lands with Parker | Nothing |

### Mobbin references (references, not assets)

| Screen | What makes it legible | Used for |
|---|---|---|
| [Remote: "How will you be using Remote?"](https://mobbin.com/screens/4f05f284-0935-41e2-9149-63d4234369c4) | Each choice is a job in the user's words ("I want to..."), not a title | Person picker labels |
| [Ghost: "What describes you best?"](https://mobbin.com/screens/c5cc238d-2bdf-486d-856e-78fdb09599f0) | Three cards, icon + label + one line, one selected state | Picker card anatomy |
| [Coda: "What's your role?"](https://mobbin.com/screens/7d618f25-89e0-4d74-a687-3311bece87cd) | A short vertical list, low reading load | Picker at phone width |
| [Ploy: today vs. with Ploy](https://mobbin.com/sites/sections/9138eef2-4217-4b65-bdac-b9f7909c6d40) | Row-matched pairs, bold claim + one-line detail per cell | G2 rows |
| [V7: before / with V7](https://mobbin.com/sites/sections/17e4b22d-7c8d-45ff-a87c-47b61b089da6) | Before is muted with ✕, after is bright with ✓ | G2 contrast between columns |
| [Runner: "Review before anything goes out"](https://mobbin.com/sites/sections/2a7bf924-dcef-490b-ae4d-f9ed8bbec018) | Numbered steps with states; the last step belongs to the person | G3 flow; G1 ending |
| [Discord: app authorization](https://mobbin.com/screens/609af9f2-c7b5-43cc-b420-97d2e94f7b51) | A plain "cannot" line with a lock icon under the "can" list | G3 tiles |
| [WhatsApp: Meta AI intro](https://mobbin.com/screens/0a61868a-a9dc-4018-b482-cbdc121d9389) | "Personal messages stay private": icon, bold line, one sentence | G3 mailbox tile |
| [Meta AI: enable screen](https://mobbin.com/screens/16d21c24-a888-4344-b561-338efbcc16f4) | "You're in control" as its own row | G3 tone |
| [Retool: authenticate](https://mobbin.com/screens/755ec605-6047-4529-9335-874d28d0cb7e) | Person → check → system, one line | G1 connector line |
| [Zaro: how it works](https://mobbin.com/sites/sections/f8bee0ad-f336-483c-8cfd-3964bda07b0a) | Four numbered cards, verb-first titles | G4 step titles |
| [Google Workspace: "You're on your way"](https://mobbin.com/screens/05a829a2-525b-4a6e-911a-f4d5e2e5b9ce) | Progress bar, one action button per step, "mark as done" | G4 checklist |
| [Remote: Recruit checklist](https://mobbin.com/screens/2c3856d6-86aa-4ccb-a189-96c96364342d) | Locked rows for steps not available yet | "Coming next" rows |
| [Vanta: starter guide](https://mobbin.com/screens/d6c8a960-3253-4ca4-b4aa-06e902fa0e4e) | Dependent steps shown with a lock and a count | Status chips for *On Parker's list* |

Avoid from Mobbin: [Descript results](https://mobbin.com/sites/sections/02baf104-3af7-400c-8cb5-19660df2763c)
and [Titan Intake](https://mobbin.com/sites/sections/67b9a79c-2487-4ce2-96cb-0231ea6c8976)
(hours and minutes before/after, which we cannot ground); gradient-heavy pickers (Lovable)
that fight the BBS navy and gold.

---

## 7. Open questions for Parker

1. Joyce Newell: include her card? The prompt includes her and makes removal a one-line
   change.
2. Shopify card-paid orders still showing unpaid in Business Central: fixed since
   2026-09-11? Until confirmed, Summer's card carries "Shopify card payments may still
   show as unpaid: check before you chase", and the build prompt stops before removing it.
3. Will you add AR, accounting and Shopify rows to the coach's `jobs-map.md` before the
   page goes out, so `/bbs-what-can-i-do` agrees with it?
4. A role-aware `/bbs-checkup` (skip the desk folder and signature checks for non-desk
   roles), or tell people check 6 will fail?
5. Which gap first? The cheapest high-value one is moving `so-search` and `bbs-po-status`
   to the current Business Central connector: it unlocks rows for Berenice, Joyce, Summer
   and accounting at once. That is your decision; the README says not to do it quietly.
