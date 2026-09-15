# Rep setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds the VS Code quote desk: same Claude, same skills — plus you can SEE the files
Claude is reading, side by side. Screenshots will be pinned in the Teams sales channel.

## Set up (once)

1. **Run the bootstrap** — download `scripts/bbs-setup.ps1` from the marketplace repo (Parker
   posts it in Teams with the workspace file), then in PowerShell:
   `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1`. It installs Git, Node, Chrome,
   and the PDF/OCR/Office command-line tools Claude uses to read RFQs. Two minutes, safe to rerun.
2. **Install VS Code** — code.visualstudio.com, all defaults.
3. **Install the Claude Code extension** — Extensions sidebar (Ctrl+Shift+X), search
   "Claude Code", install, then sign in with your BBS Claude account (same login as the
   Desktop app).
4. **Open the quote desk** — grab `workspace/bbs-rep.code-workspace` from the marketplace
   repo (Parker posts it in Teams). First open: replace `REPLACE-ON-FIRST-OPEN` with your
   OneDrive root per `workspace/README.md`, save, reopen. Accept the 4 recommended
   extensions.
5. **Run `/bbs-onboard`** once — wires the skill-bus doctrine injection so BBS grounding rules
   fire inside the quoting skills. Without it the skills run with no guardrail text.
6. **Run `/bbs-checkup`** in a Claude panel. Everything ✅? Done. Anything ❌? It prints the
   exact sentence to send Parker — send it, use the Desktop app meanwhile.
7. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## What you just installed, and what each plugin needs

Install only the plugin for your desk. Everyone gets `bbs-foundations`.

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-foundations@bbs-claude-marketplace            # everyone
/plugin install bbs-sales@bbs-claude-marketplace                  # sales reps
/plugin install bbs-back-office@bbs-claude-marketplace            # purchasing / accounting
/plugin install bbs-website@bbs-claude-marketplace                # whoever maintains the site
```

**An install gives you the skills, commands and hooks — and nothing else.** Two things it
does not give you, and they are the two reasons a skill fails on a fresh machine.

**1. Connectors are assigned by Parker, not installed by you.** Run `/mcp` to see which
ones you have. Without them the skills still load, they just have nothing to read.

| Your plugin | Connectors it needs | What breaks without them |
|---|---|---|
| `bbs-foundations` | none | nothing — works standalone |
| `bbs-sales` | BC MCP, SCPRS, Microsoft 365, Firecrawl | pricing and precedent lookups degrade; intake can't pull from Outlook |
| `bbs-back-office` | **BC MCP** | all 4 skills have nothing to read at all |
| `bbs-website` | Supabase, Shopify, Grainger MCP, Firecrawl | catalog and storefront skills can't act |

Missing one? That is the `/bbs-checkup` line you send Parker — it is an admin assignment,
not something you can fix locally.

**2. Three `bbs-sales` skills shell out to software on your PC.** Step 1's bootstrap
installs all of it; this table is here so you can tell *before* you start whether a job
will run. Everything not listed is pure Claude plus connectors.

| Skill | Needs on your machine |
|---|---|
| `ca-form-filler` | `pypdf`, `pymupdf`, `pdfplumber`, `pdftotext` (poppler) |
| `bbs-quote-builder` | Node + `npm install docx`, and LibreOffice (`soffice`) for the PDF |
| `grainger-promo-page` | `pdftotext` (poppler) |
| `dgs-bpo-item-check` | nothing — it ships its own 19,390-part lookup |

Each of these checks its dependencies before touching a file and prints the exact install
command, so a missing library is a clear message, never a half-written bid document.

## Daily use

- New RFQ lands in your mailbox (an `_inbox/` folder arrives once Parker's intake flow is
  live): open the workspace, tell Claude what arrived — `ca-rfq-intake` files it and starts
  the record. Then `/ca-rfq-quote` when you're ready to price. You review every number.
  You send.
- Where you'd have asked "what did we quote them last time?" — ask Claude. It reads the
  quote-log and Business Central and cites what it finds.
- Need to find a product or a supplier? Ask Claude to open Chrome and look. It drives your own
  browser, logged in as you. Prices still come from Grainger or a vendor quote, never from a web
  page — Claude knows the rule.
- One outbound motion a week: a promo page, a winback batch, or a follow-up sweep. Log it.
- Claude got something wrong? One line in `FLAGS.md`. That's a catch, not a confession.
- Session hygiene: one RFQ per Claude session — `/clear` before the next one. Side question?
  `/btw` keeps it out of the session. Corrected Claude twice on the same thing? `/clear` and
  restart with a sharper prompt. Multi-day deal? `/rename <agency>-<item>` so
  `claude --resume` finds it tomorrow.

## When to use which window

- **VS Code**: quote work — you want the RFQ, the worksheet, and Claude on one screen.
- **Desktop app**: everything else, or if VS Code is ever broken. Same Claude.

## Want an agency storefront?

Twelve agencies already have their own BBS gear-assistant page (cdcr.blackboxsafety.com
etc.). If your buyer's agency should have one: drop the agency name + what they buy into
the buyer's folder and ping Parker — that's the whole request process today.

## The ground rules

Read and sign the one-page use policy (bbs-foundations → docs/AUP.md). Short version:
approved tools only for company data, every number human-reviewed, you send everything,
log it when Claude gets it wrong, experiment freely otherwise.

## Level up (optional, free)

Anthropic Academy "Claude 101": anthropic.skilljar.com/claude-101. Ask Parker both the
how-do-I and the it's-broken questions for now, with your /bbs-checkup line for the latter
(a deputy champion gets named after the pilot).
