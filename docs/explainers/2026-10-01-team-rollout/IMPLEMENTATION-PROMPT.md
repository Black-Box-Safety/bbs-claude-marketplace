# Build prompt: BBS Claude toolkit page for the team rollout

> Parker: paste everything below the line into a fresh Claude Code session opened in the
> `bbs-claude-marketplace` repo. It is self-contained. The reasoning behind it is in
> `brief.md` beside this file; the builder does not need it.
>
> **Built 2026-10-01 (PR #46).** The page went beyond this prompt at Parker's direction in
> session: a shared Sales card (Kim, Aanya, Joey, Griffin), a supplier-scout row, Griffin's
> federal deck row, and SAM.gov under Coming next for Kim and Griffin. The page source
> (`bbs-claude-toolkit.html`) is the current truth; what changed and what is still open is in
> `docs/SESSION-HANDOFF-2026-10-01.md`. Re-running this prompt as written would drop Sales.

---

You are building one private web page (an Artifact) that introduces the BBS Claude
marketplace to six people at Black Box Safety, Inc. who do not use Claude yet. Everything
you need is in this prompt: the audience, the page structure, every word of copy, the facts
each claim rests on (with file paths), the brand rules and the checks you must pass. **Do
not research, do not invent, do not add a capability.** If something here turns out to be
missing or wrong, stop and report (section 9). You are building, not designing from scratch.

## 1. Who it is for, and what it must do

**Readers.** Six people, named exactly as below, never ranked or compared, never given job
titles beyond the role group:

| Slug | Name as shown | Role group | One-line job (picker) |
|---|---|---|---|
| `berenice` | Berenice | Purchasing | Vendor POs and problem orders |
| `joyce` | Joyce Newell | Purchasing | Customer POs on the quote desk |
| `summer` | Summer | Accounts receivable | Invoices and collections |
| `bella` | Bella | Accounting | Books, billing and reconciliation |
| `annette` | Annette Somers | Accounting | Books, billing and reconciliation |
| `emily` | Emily | Body armor and Shopify | Body armor orders and Shopify |

They are good at their jobs, busy, not technical, and right to be skeptical. They fear
breaking something, sending something, or being replaced. One concrete "here is your week,
minus the part you dislike" beats ten features.

**The promise.** Hand Claude the lookups and the first draft. Keep the judgment and the
send button.

**Must do.**
1. A person who opens the page with their hash (`#summer`) or taps their name sees **their
   own section first**, directly under the header, before anything general.
2. Say early and plainly that Claude drafts and a person sends, and that it reads Business
   Central without changing it.
3. Tag every capability honestly: **Ready today**, **On Parker's list** or **Not built
   yet**. Never show a gap as available.
4. End by handing the reader to the coach plugin's `/bbs-what-can-i-do`, which already
   teaches Claude at BBS. The page routes; it is not a second manual.

## 2. Tools and skills to use, in this order

1. `Artifact` with `action: "quickstart"`, `intent: "other"`. If it lists a BBS design
   system, read it and reconcile it with section 5; where they disagree on a brand value,
   section 5 wins (it comes from the repo's canonical facts) and you say so in your report.
2. Load the `artifact-design` skill and follow its page contract (title, theming tokens,
   allowed CDNs, size, layout, icon).
3. Load the `artifact-diagramming` skill before drawing G1 and the G3 flow.
4. Load the `impeccable` skill (from the pinned `impeccable` plugin, `/impeccable`) and use
   it for the design pass and its review before publishing. **If `impeccable` is not in
   your skill list, stop and report.** Do not substitute another design skill silently.
5. Publish with the `Artifact` tool (private by default). Do not share it; give Parker the
   link.

No runtime capabilities are needed (no database, no viewer identity, no storage). Do not
use `localStorage`; the hash carries the selection.

## 3. Page architecture

- **One page**, title `BBS Claude Toolkit`, description "Who does what with Claude at
  Black Box Safety: purchasing, AR, accounting and body armor.", icon `compass`.
- Source file: `docs/explainers/2026-10-01-team-rollout/bbs-claude-toolkit.html`.
  Supporting file: publish `bbs_logo.png` from
  `plugins/bbs-sales/skills/bbs-quote-builder/assets/bbs_logo.png` via `files`
  (`{"bbs_logo.png": "plugins/bbs-sales/skills/bbs-quote-builder/assets/bbs_logo.png"}`).
- **Data-driven cards.** Put people, roles, rows, statuses and "coming next" items in one
  JavaScript object at the top of the script, and render every card from it. Removing
  Joyce must be deleting one entry. The page must render its general sections even if
  scripting fails (server-render the general sections in HTML; cards may be rendered by
  script, with a `<noscript>` line: "Turn on JavaScript to see your own week first.").
- **Order with a person chosen** (by hash or tap):
  1. Header (C1) with the guardrail strap.
  2. Picker, collapsed to "Showing Summer's week first. Change".
  3. That person's section (C2).
  4. G1 What Claude is at BBS (C3).
  5. G3 What it will never do (C4).
  6. G4 Start tomorrow (C5).
  7. Coming next for that person (C6).
  8. "Everyone else's week" as a closed `<details>` holding the other role cards.
  9. Footer (C7).
- **Order with no person chosen:** header, picker (open), G1, G3, G4, then all role cards
  in a closed `<details>` ("See every role"), footer.
- Selecting a name updates the URL hash with `history.replaceState`, re-renders the order
  above, and moves focus to the person's section heading. Hash values are the slugs in
  section 1. An unknown hash falls back to "no person chosen".
- Bella and Annette share one Accounting card. When either is chosen, the heading uses the
  chosen name and the card notes "Shared with Annette Somers" or "Shared with Bella".
- Berenice and Joyce each have their own card under a Purchasing heading. When one is
  chosen, the other's card goes to "Everyone else's week".

## 4. The four graphics

**G1 What Claude is at BBS.** Three columns, left to right: *Where the facts live*
(four system tiles) → *Who does the legwork* (Claude, holding a binder) → *Who decides*
(You). Dashed connectors with a small eye glyph from each system to Claude, labelled
"looks in". The Business Central and Grainger tiles carry a small "read-only" tag; Outlook
and SharePoint do not, because Claude can write drafts and files there. A solid arrow from Claude to You labelled "a draft". An arrow out of
You labelled "you send". "You" is the heaviest node (navy fill, white text, a gold rule).
Claude is mid weight; systems are light. Under the diagram, the five-row legend. At widths
under 720px the columns stack vertically and the connectors point down. All labels are real
text, not text baked into an image. Give the diagram a `<title>`/`<desc>` or an
equivalent text alternative that states the flow in one sentence (C3 gives it).

**G2 Your week (the person card).** Role line, promise line, then three to five
row-matched pairs. Each pair: a job title; left cell "Today" (muted text, small ✕ glyph);
right cell "With Claude" (full weight, small ✓ glyph); a status chip; a "Try saying" line in
JetBrains Mono with a copy button (only on *Ready today* rows); and a `<details>`
"Under the hood" naming the playbook. Rows marked *On Parker's list* sit below the Ready rows,
their right cell starts "Soon:", and they carry the chip's reason instead of a "Try saying"
line. At phone width each pair stacks Today above With Claude. A short status legend sits
once above the first card (C2.0).

**G3 What it will never do.** A four-step horizontal flow (vertical on phones): You ask →
Claude looks → Claude drafts → You check and send. The last step is filled navy
with the only gold accent in the section. Below it, four tiles (icon, bold line, one or two
sentences) and one quieter fifth tile.

**G4 Start tomorrow.** A card with three numbered steps and a decorative progress ring (it
stores nothing). Step 2 is the primary action and carries a copy button for
`/bbs-what-can-i-do`. A footer line and two quiet links follow.

Status chips: text plus icon, never color alone.
- **Ready today**: filled check icon.
- **On Parker's list**: clock or wrench icon, outlined; the reason appears next to it.
- **Not built yet**: lock icon, dashed outline (used only in C6).

## 5. Brand, accessibility, phone and themes

**Brand (from `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`,
"Brand").** Navy `#051c2c`, gold `#b19800`. Fonts Archivo (headings and body) and JetBrains
Mono (commands, placeholders), from Google Fonts. Plain, credentialed, veteran-owned: lots of
white space, thin gold rules, navy blocks for emphasis. No stock photos, no illustrations of
people, no flags, seals, patches or military imagery, no gradients. Do not use AllStar red.

**Logo.** Only `bbs_logo.png` (156 x 177 px, navy and gold on white, no transparency).
Show it at up to 64 px tall in the header, on a white rounded plate with padding, in both
themes. Never recolor, invert, crop, redraw, filter or combine it with another mark; never
build a new lockup. No other logo or mark appears (no Grainger, no DVBE, no agency or
customer marks). Rights rules: `plugins/bbs-marketing/references/ASSETS.md`.

**Voice (from `plugins/bbs-marketing/references/VOICE.md`).** Sentence case headings. No em
dashes or en dashes anywhere on the page. No exclamation marks. None of these words:
seamless, robust, unlock, elevate, empower, cutting-edge, state-of-the-art, best-in-class,
world-class, industry-leading, game-changing, groundbreaking, innovative, transform,
revolutionize, streamline, leverage, synergy, ecosystem, turnkey, solutions, delve, rest
assured, peace of mind, we're excited, we're proud. Use the copy in section 6 exactly; if you
must shorten a line for layout, keep its meaning and tell Parker which line.

**Color tokens.** Define on `:root`, redefine for dark mode under
`@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and again
under `:root[data-theme="dark"]`; give `body` an explicit background. Gold `#b19800` on white
is about 2.9:1, which fails for text: use gold only for rules, icons, focus accents and fills
behind navy or white text where contrast passes. For gold-colored text on a light background,
derive a darker gold token and verify at least 4.5:1. In dark mode use a navy-based background
(navy `#051c2c` or a near-navy) with light text; gold on navy is about 6:1 and may be used for
small accents.

**Accessibility (WCAG 2.2 AA).** Body text at least 4.5:1, large text and UI parts at least
3:1, in both themes. One `h1`; headings in order. The picker is a group of real `<button>`s
with `aria-pressed`, reachable by Tab, with a visible focus ring (at least 2 px, 3:1). Touch
targets at least 44 x 44 px. Copy buttons announce "Copied" via an `aria-live="polite"`
region and fall back to selecting the text if the clipboard API fails. Honor
`prefers-reduced-motion` (no animated transitions). `lang="en"`. Diagrams have text
alternatives. Nothing conveyed by color alone. Body text at least 16 px.

**Phone width.** Works at 360 px wide with a 16 px side gutter and no horizontal scroll:
the picker wraps, G1 and G3 stack vertically, G2 pairs stack, long mono lines wrap
(`overflow-wrap: anywhere`).

## 6. Copy deck (use verbatim)

Placeholders in mono: `____` for an identifier the reader fills in. Never put a real PO,
SO, invoice number, amount, agency, customer, vendor contact, signature or anything from a
mailbox on the page.

### C1. Header and picker

- Eyebrow: `Black Box Safety · Internal`
- H1: `Claude does the lookups. You make the calls.`
- Sub: `A short guide for purchasing, accounts receivable, accounting and body armor. Pick your name to see your week first.`
- Guardrail strap (always visible, under the sub): `Claude drafts. You send. It reads Business Central and never changes it.`
- Picker label: `Who are you?`
- Picker groups and buttons: section 1 table (group heading, then name with its one-line
  job under it).
- Collapsed picker: `Showing {Name}'s week first.` + button `Change`
- No person chosen, above the general sections: `Pick your name above, or read on for the whole picture.`

### C2. Person cards

**C2.0 Status legend** (once, above the first card):
`Ready today: works now.` · `On Parker's list: built, waiting on one fix or switch.` · `Not built yet: tell Parker if you want it.`

Card heading pattern: `{Name}, your week with Claude`. Under it: role group, then the
promise line in larger type.

**Berenice** · Purchasing
Promise: `Less digging through four records to find the one that is wrong.`

1. **A problem order** · Ready today
   - Today: `Someone says the item or size is wrong. You open the PO, the bid sheet, the order sheet and Business Central, then search your email for what was promised.`
   - With Claude: `Give Claude the PO and the line. It lines up what the customer asked for, what we quoted, what the PO says and what shipped, tells you which one is wrong, finds every other PO with the same line, and names who can approve the fix. You decide. The account owner sends.`
   - Try saying: `PO ____ line ____: the customer says the size is wrong. Which record is wrong, and who can approve the fix?`
   - Under the hood: `Playbook: bbs-order-reconciliation, in the back office binder. It reads Business Central, Grainger and your own Outlook. It changes nothing in Business Central or Grainger.`
2. **Money owed back to us** · Ready today
   - Today: `A vendor promised a credit on the phone. Weeks later nobody knows if it landed.`
   - With Claude: `When Claude rebuilds an order's history, it lists the credits promised, free replacements shipped and freight we paid for someone else's mistake, and who owes what. You decide what to chase.`
   - Try saying: `On PO ____, was any vendor credit or free replacement promised, and did it happen?`
   - Under the hood: `Same playbook, its "money owed back to us" step.`
3. **A Grainger cart into the portal** · Ready today
   - Today: `You retype item numbers and quantities from a cart PDF or a screenshot.`
   - With Claude: `Drop in the PDF or screenshot. Claude hands back ITEM#,QTY lines to paste into the Grainger portal. You check the count.`
   - Try saying: `Pull the item numbers and quantities from this Grainger cart.`
   - Under the hood: `Playbook: rfq-item-extract, in the sales binder. It reads only the file you give it.`
4. **What a vendor still owes us** · On Parker's list · reason `Waiting on a Business Central link fix`
   - Today: `The PO can say fully received when nothing has arrived, so you check every line.`
   - With Claude: `Soon: Claude adds up received and outstanding from the lines, never the header flag.`
   - Under the hood: `Playbook: bbs-po-status, in the back office binder.`

Card note (below the rows): `Working a problem order, you can write to Claude in English or Spanish. It answers in the language you write in and keeps PO numbers, part numbers and units like EA or PK exactly as printed.`

**Joyce Newell** · Purchasing
Promise: `Less hunting for the order behind a PO.`

1. **A whole order from its number** · Ready today
   - Today: `You click through Business Central screens to see what is on an order.`
   - With Claude: `Give Claude the sales order or invoice number. It reads the header and every line from Business Central, so you can check them against the customer's PO.`
   - Try saying: `Show me SO-____ with every line.`
   - Under the hood: `The Business Central window, which is read-only.`
2. **A Grainger cart into the portal** · Ready today
   - Today: `You retype item numbers and quantities from a cart PDF or a screenshot.`
   - With Claude: `Drop in the PDF or screenshot. Claude hands back ITEM#,QTY lines to paste into the Grainger portal. You check the count.`
   - Try saying: `Pull the item numbers and quantities from this Grainger cart.`
   - Under the hood: `Playbook: rfq-item-extract, in the sales binder.`
3. **A problem order** · Ready today
   - Today: `A customer says a line is wrong and you go looking through the PO, the quote and the emails.`
   - With Claude: `Claude tells you which record is wrong, which other POs have the same line, and who can approve the fix.`
   - Try saying: `PO ____ line ____ looks wrong. Which record is wrong?`
   - Under the hood: `Playbook: bbs-order-reconciliation, in the back office binder.`
4. **Which order is this customer PO?** · On Parker's list · reason `Waiting on a Business Central link fix`
   - Today: `A PO number arrives and you search for the order behind it, invoiced or not.`
   - With Claude: `Soon: Claude finds the sales order from the customer's PO number, even before it has been invoiced.`
   - Under the hood: `Playbook: so-search, in the back office binder.`
5. **Is this part on the DGS BPO?** · On Parker's list · reason `Waiting on this fiscal year's BPO list`
   - Today: `You look each Grainger part up on the BPO list.`
   - With Claude: `Soon: Claude checks every part against the current list. Today it still holds last fiscal year's list, and it says so on every answer.`
   - Under the hood: `Playbook: dgs-bpo-item-check, in the sales binder.`

**Summer** · Accounts receivable
Promise: `Less looking up the same balances one agency at a time.`

1. **Who owes us** · Ready today
   - Today: `You pull the aging, then open each agency to see what is still open.`
   - With Claude: `Ask what is past due, or where we stand with one agency. Claude reads Business Central and answers with the open invoices, orders and quotes in one place, and says where each number came from. Shopify card payments may still show as unpaid: check before you chase.`
   - Try saying: `Which invoices are past due right now, oldest first?`
   - Under the hood: `The Business Central window, which is read-only: it never posts or changes an invoice.`
2. **The reminder email** · Ready today
   - Today: `You write the same past-due reminder again and again.`
   - With Claude: `Claude writes the reminder into your Outlook Drafts. Run /bbs-my-voice once and it sounds like you. You read it and press send.`
   - Try saying: `Draft a polite past-due reminder for invoice ____ into my Outlook Drafts.`
   - Under the hood: `The Outlook window can create a draft. In Claude Code it cannot send. /bbs-my-voice, in the foundations binder, learns only from your own Sent Items.`
3. **A short payment over a price or quantity** · Ready today
   - Today: `An agency pays less because they say the price is wrong, and you chase sales to find out why.`
   - With Claude: `Claude lines up what we quoted, what the PO says and what shipped, says which one is wrong, and names who at the agency can approve a corrected PO. Sales decides what goes back to the customer.`
   - Try saying: `Invoice ____ was short-paid on line ____. Which record is wrong?`
   - Under the hood: `Playbook: bbs-order-reconciliation, in the back office binder.`
4. **Which invoices sit under a customer PO** · On Parker's list · reason `Waiting on a Business Central link fix`
   - Today: `A payment quotes a PO number and you search for the invoices behind it.`
   - With Claude: `Soon: Claude lists every invoice under that PO and the order it came from.`
   - Under the hood: `Playbook: so-search, in the back office binder.`

**Bella and Annette Somers** · Accounting (one shared card; heading uses the chosen name)
Promise: `Ask Business Central a question in plain words.`

1. **One question, no export** · Ready today
   - Today: `You build a filter or an export to Excel to answer one question.`
   - With Claude: `Ask the question. Claude reads Business Central, read-only, and tells you which records each number came from, so you can check it.`
   - Try saying: `From Business Central, list the purchase invoices posted last month that are still open.`
   - Under the hood: `The Business Central window, which is read-only.`
2. **Money owed back to us** · Ready today
   - Today: `A vendor credit was promised and nobody can tell if it ever landed.`
   - With Claude: `When Claude rebuilds an order's history, it lists the credits promised, free replacements shipped and freight we absorbed, so you know what to chase.`
   - Try saying: `On PO ____, was any vendor credit promised, and did it post?`
   - Under the hood: `Playbook: bbs-order-reconciliation, its "money owed back to us" step.`
3. **A workbook from a pile of files** · Ready today
   - Today: `You copy columns between spreadsheets and statements by hand.`
   - With Claude: `Hand Claude the export and the statement. It builds the workbook and flags the rows that don't match. You check the flags.`
   - Try saying: `Match this vendor statement against this export and flag what doesn't match.`
   - Under the hood: `document-skills, Anthropic's Excel, Word and PDF playbooks, pinned in the toolkit.`
4. **Margin after the Grainger rebate** · On Parker's list · reason `Needs a connection Parker hasn't switched on`
   - Today: `Business Central shows little or no margin on rebate deals, because the rebate isn't in it.`
   - With Claude: `Soon: Claude applies the rebate by contract code and shows margin by account and by contract.`
   - Under the hood: `Playbook: bbs-rebate-profitability, in the back office binder.`
5. **What vendors still owe us** · On Parker's list · reason `Waiting on a Business Central link fix`
   - Today: `The PO can say fully received when nothing has arrived.`
   - With Claude: `Soon: Claude adds up what is still outstanding from the receipt lines.`
   - Under the hood: `Playbook: bbs-po-status, in the back office binder.`

Card note: `Roles overlap. Summer's card covers invoices and collections.` (link to `#summer`)

**Emily** · Body armor and Shopify
Promise: `Fewer retyped replies and order lookups.`

1. **The same question, again** · Ready today
   - Today: `You answer the same sizing, lead-time and order-status emails over and over.`
   - With Claude: `Tell Claude what you want to say. It drafts the reply into your Outlook Drafts, in your voice once you run /bbs-my-voice. You check it and send it.`
   - Try saying: `Draft a reply to this email in my Outlook Drafts. Here's what I want to say: ____`
   - Under the hood: `The Outlook window can create a draft. In Claude Code it cannot send.`
2. **Where is this order?** · Ready today
   - Today: `You look an order up in Business Central screen by screen.`
   - With Claude: `Give Claude the sales order number and it reads the order, every line, from Business Central. Orders still sitting in Shopify are not visible to Claude yet.`
   - Try saying: `Show me SO-____ with every line.`
   - Under the hood: `The Business Central window, which is read-only.`
3. **Wrong size delivered** · Ready today
   - Today: `An officer got the wrong size, and you go back through the order, the PO and the emails.`
   - With Claude: `Claude lines up what was ordered, what the PO says and what shipped, and tells you which one is wrong before anyone reorders.`
   - Try saying: `SO-____: the officer received the wrong size. Which record is wrong?`
   - Under the hood: `Playbook: bbs-order-reconciliation, in the back office binder.`
4. **A Point Blank price sheet** · On Parker's list · reason `Needs one piece of software and the website folder set up`
   - Today: `You key price-list rows into a template by hand.`
   - With Claude: `Soon: hand Claude the sheet. It cleans it into the BBS import template and tells you what it could not match. Loading it into the catalog stays with Parker.`
   - Under the hood: `Playbook: price-list-cleaner, in the website binder.`

### C3. G1 What Claude is at BBS

- Heading: `What Claude is at BBS`
- Sub: `An assistant at your desk. It follows the BBS playbooks, looks through live windows into the systems you already use, and hands you a draft.`
- Column 1 label: `Where the facts live`. Tiles: `Business Central` (`orders, invoices, POs` + tag `read-only`) · `Your Outlook` (`your own mail`) · `SharePoint` (`customer folders`) · `Grainger` (`pricing` + tag `read-only`)
- Column 2 label: `Who does the legwork`. Node: `Claude` (`with the BBS playbooks`)
- Column 3 label: `Who decides`. Node: `You`
- Connector labels: `looks in` · `a draft` · `you send`
- Text alternative: `Claude looks into Business Central and Grainger, which it can only read, and into your Outlook and SharePoint. It follows the BBS playbooks and hands you a draft. You decide and you send.`
- Legend (term · what it is):
  - `Playbook (a skill)` · `The BBS way of doing one job, written down. Claude picks the right one when your request matches. You don't have to name it.`
  - `Binder (a plugin)` · `A set of playbooks for one area, like back office or the website. Yours are already on your computer.`
  - `Window (a connector)` · `A live view into a system you already use. Parker switches these on for each person. Business Central and Grainger are read-only.`
  - `Shortcut (a command)` · `A word you type that starts with a slash, like /bbs-what-can-i-do.`
  - `You` · `You check it, you decide, you send.`
- Footnote: `Skill, plugin and connector are the words you'll see in Claude. Type /bbs-explain-claude for the plain-language version.`

### C4. G3 What it will never do

- Heading: `What it will never do`
- Sub: `In Claude Code, the app your setup installs, these rules are switched on for everyone. They are why it is safe to try things there.`
- Flow steps: `You ask` → `Claude looks` → `Claude drafts` → `You check and send`
- Tile 1: **`In Claude Code, it drafts and never sends.`** `In Claude Code, sending, forwarding and Teams messages are switched off for Claude. It can put a draft in your Outlook Drafts; you press send. The ordinary Claude chat window does not have these switches, so use Claude Code for this work.`
- Tile 2: **`Reads Business Central, never changes it.`** `Business Central and Grainger are read-only for Claude. It cannot post, edit or delete a record.`
- Tile 3: **`The right signer on the right line.`** `Signatures go only on the lines of the people allowed to sign them. Claude never signs for you.`
- Tile 4: **`Your mailbox is yours.`** `Claude reads your mail only when you connect it and ask. It never reads anyone else's. /bbs-my-voice learns from your own Sent Items and stops if the mailbox isn't yours.`
- Tile 5 (quieter): **`Rules built in.`** `No invented numbers: if Claude doesn't know, it flags it. Certification wording follows the channel: DVBE for California state work, SDVOSB for federal.`
- Closing line: `The full one-page policy is the AUP you sign with Parker.`

### C5. G4 Start tomorrow

- Heading: `Start tomorrow`
- Step 1: **`Get set up, once.`** `Run the setup file Parker sends for your computer. If the window ends with anything other than Done, send Parker the whole window. Don't try to fix it.`
- Step 2 (primary): **`Ask what it can do for you.`** `Open Claude Code (in VS Code or the Claude Desktop app, where your setup put it) and type /bbs-what-can-i-do. Tell it what you're working on.` Copy button text: `/bbs-what-can-i-do`
- Step 3: **`Try your first ask.`** `Copy the first "Try saying" line from your card, fill in the blank, and check what comes back.`
- Footer: `Something missing or wrong? Tell Parker in one line: what you asked, what happened. A missing tool is a request, not a dead end.`
- Quiet links (text, not hyperlinks): `/bbs-explain-claude` · `the words, in plain language` and `/bbs-start` · `one first step for whatever is in front of you`

### C6. Coming next (for the chosen person; all are Not built yet)

- Heading: `Coming next`
- Sub: `Not built yet. Tell Parker which one you want first.`
- Berenice: `A list of vendor POs past the date the vendor committed to.` · `One shared place to log vendor problems, so the pattern is on record when you talk to the vendor.` · `Vendor bill, PO and receipt checked against each other.`
- Joyce Newell: `A new customer PO checked against our quote, line by line, before the order is entered.`
- Summer: `A collections run: the aging turned into reminder drafts, agency by agency.` · `A payment advice matched to the invoices it pays.` · `A statement of account or invoice-copy pack for an agency.`
- Bella and Annette Somers: `A month-end close checklist.` · `Vendor statement reconciliation, and vendor bill, PO and receipt checked against each other.`
- Emily: `Shopify lookups: orders, products and size options.` · `One view of an officer's order from Shopify to Business Central to Point Blank.` · `A check that every agency's size options are complete.` · `The agency carrier procedure, brought into the toolkit.`

### C7. Footer

`Owner: Parker Marshall. Questions go to Parker. Built from the BBS Claude marketplace as of 1 October 2026.`

## 7. Grounding table (what each claim rests on)

Every capability on the page maps to one row. Check each path exists before you build
(section 8, check 1). Status comes from the skill's `requires:` line.

| # | Claim on the page | Rests on | Status and why |
|---|---|---|---|
| 1 | Problem order: four records, which is wrong, every affected PO, who authorizes | `plugins/bbs-back-office/skills/bbs-order-reconciliation/SKILL.md` (Phases 0 to 11) | Ready today: `requires: [business-central, grainger, microsoft-365, python3, openpyxl]`, all standard |
| 2 | Money owed back to us | same file, Phase 12, "Money owed back to us" | Ready today |
| 3 | English or Spanish; identifiers kept as printed | same file, "Writing for the person you are helping" | Ready today |
| 4 | Cart PDF or screenshot to `ITEM#,QTY` for the Grainger portal | `plugins/bbs-sales/skills/rfq-item-extract/SKILL.md` | Ready today: `requires: []` |
| 5 | Order or invoice by number, header and lines; past-due invoices; one agency's position | Business Central connector tools `bc_get_sales_document`, `bc_list_unpaid_invoices`, `bc_customer_snapshot`, `bc_query_entity`: `plugins/bbs-back-office/skills/bbs-order-reconciliation/references/tool-recipes.md`; read-only allow list in `plugins/bbs-foundations/docs/bbs-managed-settings.json`; connector row in `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` | Ready today: assigned to everyone (`docs/ADMIN-RUNBOOK.md` §3) |
| 6 | "Says where each number came from" | `README.md`, "What it will not do": "tells you where every number came from" | Ready today |
| 7 | Drafts into your Outlook Drafts; in Claude Code cannot send, forward or message in Teams | `bbs-managed-settings.json` `permissions.allow` (draft tools) and `permissions.deny` (send, send-draft, forward, Teams, meeting responses, SignNow, QuickBooks sends) | Ready today |
| 8 | `/bbs-my-voice` learns from your own Sent Items; stops on someone else's mailbox | `plugins/bbs-foundations/commands/bbs-my-voice.md` steps 1 and 2 | Ready today: `bbs-voice-template` `requires: [microsoft-365]` |
| 9 | Workbooks, PDFs, statements | `document-skills` (pinned commons, `docs/COMMONS.md`); jobs map row in `plugins/bbs-claude-coach/skills/bbs-claude-coach/references/jobs-map.md` | Ready today |
| 10 | Price sheet to the BBS import template; catalog load stays with Parker | `plugins/bbs-website/skills/price-list-cleaner/SKILL.md`; Supabase site-maintainer only per `MANAGED-SETTINGS.md` connector table | On Parker's list: `requires:` includes pandas, which the bootstrap does not install, and the output path assumes the website repo layout |
| 11 | What a vendor still owes us | `plugins/bbs-back-office/skills/bbs-po-status/SKILL.md` | On Parker's list: `requires: [bc-mcp-proxy]`, retired; `README.md` back office "Will not ... retarget" |
| 12 | Which order is this customer PO; invoices under a PO | `plugins/bbs-back-office/skills/so-search/SKILL.md` | On Parker's list: `requires: [bc-mcp-proxy]` |
| 13 | Margin after the Grainger rebate | `plugins/bbs-back-office/skills/bbs-rebate-profitability/SKILL.md` | On Parker's list: `requires: [cdata-connect]`, not assigned |
| 14 | BPO check, last fiscal year's list, says so | `plugins/bbs-sales/skills/dgs-bpo-item-check/SKILL.md`; `docs/STEWARD.md` item "FY26/27 BPO list" | On Parker's list |
| 15 | Business Central and Grainger read-only | Both connectors expose only read tools: Business Central's tool list in `MANAGED-SETTINGS.md`'s connector table, which marks it read-only; Grainger's tools are search, price, availability and resolve-part reads. `README.md` "Write to Business Central" under "What it will not do" | Rule |
| 16 | Signatures only on the lines of people allowed to sign | `plugins/bbs-sales/references/ca-form-rules.md` "Who signs what" and "Rep-signed lines and delegated signatures"; canonical-facts "People and signatures" (none of the six readers is a delegate) | Rule |
| 17 | No invented numbers; unknown is flagged | `plugins/bbs-claude-coach/skills/bbs-claude-coach/references/aup-rails.md` rail 2 | Rule |
| 18 | DVBE for California state, SDVOSB for federal | canonical-facts "Certifications, by jurisdiction" | Rule. The page never says "small business" |
| 19 | Playbook, binder, window, shortcut | `plugins/bbs-claude-coach/skills/bbs-claude-coach/references/glossary.md` (skill = playbook, connector = live link, Parker assigns) | Explanation |
| 20 | `/bbs-what-can-i-do`, `/bbs-start`, `/bbs-explain-claude` | `plugins/bbs-claude-coach/commands/` | Ready today: `requires: []` |
| 21 | Setup file, "Done", send Parker the window | `README.md` "Install", step 1; `docs/REP-SETUP.md` step 1 | Ready today |
| 22 | "A missing tool is a request, not a dead end" | `plugins/bbs-claude-coach/skills/bbs-claude-coach/references/how-to-extend.md` §3 | Explanation |
| 23 | Orders still in Shopify not visible; Shopify lookups not built | `MANAGED-SETTINGS.md` connector table (Shopify admin: Parker and Griffin only) | Gap |

**Never present** Parker's account-synced skills (`grainger-cart-info`, `bbs-b2b-pricing`,
or the personal copies of marketplace skills). They are being retired (`HANDOFF.md`).

## 8. Acceptance checks (run all; report each as PASS or FAIL with evidence)

1. **Paths exist.** `test -f` every path in section 7. Any missing: stop (section 9).
2. **Statuses still true.** Run `python3 scripts/check_marketplace.py --requirements` and
   confirm: `bbs-po-status` and `so-search` still `requires: bc-mcp-proxy`;
   `bbs-rebate-profitability` still `cdata-connect`; `rfq-item-extract` still nothing;
   `bbs-order-reconciliation` unchanged. Any difference means a status on the page may now
   be wrong: stop and report the difference rather than editing the status yourself.
3. **No invented numbers.** In the built HTML's visible text there are no amounts,
   percentages, durations or multiples. `grep -nE '\$[0-9]|[0-9]+ ?%|[0-9]+ ?(hours?|hrs?|minutes?|mins?|x faster)|ROI'`
   returns nothing. Digits allowed only in: the date in C7, step numbers, `ITEM#,QTY`,
   CSS, and the logo file name.
4. **No records, customers or signatures.** `grep -nE 'SO-[0-9]|PO-[0-9]|INVP-|SQ-[0-9]|@blackboxsafety|CDCR|CAL FIRE|Allstar|DSH|signature\.png'`
   returns nothing. No image other than `bbs_logo.png`.
5. **Certification language.** "DVBE" appears once, in C4 tile 5, in the same sentence as
   "SDVOSB", "California" and "federal". `grep -ni 'small business'` returns nothing.
6. **Voice.** No em or en dashes in the HTML (`python3 -c "import sys; t=open(sys.argv[1], encoding='utf-8').read(); print(sum(t.count(c) for c in '\u2013\u2014'))" <file>`
   prints 0). None of the banned words in section 5 (case-insensitive grep). Headings in
   sentence case. No exclamation marks in visible text.
7. **Own section first.** For each slug, load the page with `#slug` (headless browser if one
   is available; otherwise trace the render code and say how you verified) and confirm the
   first section after the header and collapsed picker is that person's card, headed with
   their name. Also confirm an unknown hash and no hash show the picker open.
8. **Honest statuses.** Every row's chip matches section 6; no *On Parker's list* row has a
   "Try saying" line or a copy button; *Not built yet* items appear only in C6.
9. **Phone, themes, accessibility.** At 360 px wide, `document.documentElement.scrollWidth
   <= clientWidth` (or reasoned check). Both themes legible; contrast of body text, chips,
   buttons and focus ring meets section 5 in both themes. Keyboard-only: Tab reaches every
   picker button, copy button and disclosure, with a visible focus ring.
10. **Logo untouched.** `sha256sum` of the source PNG equals the published file; no CSS
    `filter`, `mix-blend-mode` or recolor applied to it.
11. **Impeccable review.** Run the `impeccable` review on the page and fix what it finds
    within these rules; list any finding you chose not to fix and why.
12. **Repo check.** `python3 scripts/check_marketplace.py` exits 0 with your files added.
13. **"Read-only" is never general.** `grep -niE 'read-only|never changes|without changing|changes nothing'`
    on the built HTML: every hit names Business Central or Grainger in the same sentence,
    or is the `read-only` tag inside the Business Central or Grainger tile (the tile names
    its system). Any hit that could be read as covering Outlook, SharePoint, the CRM or
    "connectors" in general is a FAIL: Claude can write drafts, files and CRM records there.
14. **Send claims are scoped.** `grep -niE 'cannot send|never sends?|switched off|can.t send'`
    on the built HTML: every hit names Claude Code in the same sentence. None says
    "everyone" or "always" without it.

## 9. Stop and report (do not guess) when

- `impeccable`, `artifact-design` or `artifact-diagramming` is unavailable.
- The logo file is missing or differs from 156 x 177 px.
- A path in section 7 is missing, or check 2 shows a changed `requires:` line.
- You would need a fact, number, name, title or capability that is not in this prompt.
- A line of copy cannot be laid out at 360 px without changing its meaning.
- Summer's row 1 would publish without its Shopify caveat. Keep the caveat until Parker
  confirms in writing that the 2026-09-11 Gap 4 (Shopify card-paid invoices showing unpaid
  in Business Central) is fixed; only then remove it.

Report what is missing, what you did up to that point, and what you need from Parker.

## 10. When you are done

1. Work on a branch (`docs/team-rollout-explainer`), never `main`. Commit the two files in
   `docs/explainers/2026-10-01-team-rollout/` (`brief.md`, this prompt) and the page source.
   Open a pull request with the acceptance results in its description. **Do not merge it**;
   another agent reviews (AGENTS.md, "Working rules").
2. Publish the page with the `Artifact` tool (private). Do not share it.
3. Report to Parker, briefly: the link; the six hash links (`<link>#berenice` and so on);
   each acceptance check with PASS or FAIL; any copy you shortened; and these open
   questions, unchanged:
   - Include Joyce Newell? (Removing her is one data entry.)
   - Add AR, accounting and Shopify rows to the coach's `jobs-map.md` so
     `/bbs-what-can-i-do` agrees with the page?
   - `/bbs-checkup` check 6 (desk folder) will fail for these six. Make it role-aware, or
     warn them?
   - Confirm each of the six has Business Central, Microsoft 365 and Grainger assigned, and
     the customer folders synced (the problem-order playbook reads them).
   - Is Gap 4 (Shopify card-paid invoices showing unpaid in Business Central,
     `docs/assessments/2026-09-11-bc-assessment.md`) fixed? Until it is, Summer's card keeps
     its "check before you chase" caveat.
   - Has the test send been denied in both VS Code and the Claude Desktop app's Claude Code
     (ADMIN-RUNBOOK §1)? The page says sending is switched off in Claude Code; confirm it
     before sharing the link.
   - The read-only claims rest on today's Business Central connector, which
     `MANAGED-SETTINGS.md` calls interim. When it is swapped for Microsoft's official
     connector, re-check that the new tools are read-only before the page keeps saying so.
