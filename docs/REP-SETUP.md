# Rep setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds the VS Code quote desk: same Claude, same skills — plus you can SEE the files
Claude is reading, side by side. Screenshots will be pinned in the Teams sales channel.

Same steps on Windows and Mac. Where they differ, each step says so; on a Mac read Cmd for Ctrl.

## Set up (once)

1. **Run the setup script for your computer** (~5 minutes; safe to rerun). Parker posts both
   in Teams with the workspace file. **Run only the one for your computer** — the other one
   stops with a message and changes nothing.

   | Your computer | How to tell | The script |
   |---|---|---|
   | **Windows PC** | Windows logo (Start) on the taskbar | `bbs-setup.ps1` |
   | **Mac** | Apple logo, top-left of the screen | `bbs-setup.sh` |

   **Windows PC**
   - Open PowerShell (Start → type "PowerShell" → Enter) and `cd` to where you saved the file.
   - Run: `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1` (SAM.gov users, Kim and Griffin, add `-SamGov` to be asked for the shared SAM.gov key; Parker supplies it)
     (add `-DryRun` to preview without installing anything).

   **Mac**
   - Homebrew must be installed once first: follow [brew.sh](https://brew.sh).
   - Open Terminal (Cmd+Space → type "Terminal" → Enter) and `cd` to where you saved the file.
   - Run: `chmod +x bbs-setup.sh && ./bbs-setup.sh` (add `--dry-run` to preview; SAM.gov users add `--sam-gov` to be asked for the shared SAM.gov key).
   - If it says `python3` is missing, run `xcode-select --install`, then run the script again.

   **What it does, either way:** installs the tools Claude uses to read RFQs and build quotes
   and packets (Git, Node, Python — on a Mac, Apple's — Chrome, LibreOffice, the PDF/OCR tools, and the Python and
   Node libraries the form-fill and quote skills import); puts each of them on PATH (`[path]`
   lines); installs Claude Code's `claude` command if you don't have it; and installs **every
   plugin in the BBS marketplace** — one `[ok]` or `[install]` line per plugin.

   **How to read the result:**
   - **Done** is a line saying `Done.` near the bottom.
   - `Not done yet`, or a `[later]` line (Windows): close the PowerShell window, open a new
     one, run the script again. Node and Python finish their libraries from a fresh window.
   - Yellow `WARNING:` lines, `[missing]` lines, or `Finished with … to install by hand` mean
     something failed. A plugin that will not install prints Claude Code's own error under its
     `WARNING:` line — that is the part Parker needs. Copy the whole window and send it to
     Parker; don't try to fix it.
   - Already set up, and `/bbs-checkup` shows a missing plugin or tool? Run the script again.
2. **Install VS Code** — code.visualstudio.com, all defaults.
3. **Install the Claude Code extension** — Extensions sidebar (Ctrl+Shift+X), search
   "Claude Code", install, then sign in with your BBS Claude account (same login as the
   Desktop app).
4. **Open the quote desk** — grab `workspace/bbs-rep.code-workspace` from the marketplace
   repo (Parker posts it in Teams), or run the launcher script for your computer
   (`scripts/install-desktop-launchers.ps1` on Windows, `scripts/install-desktop-launchers.sh`
   on a Mac) so it lands on your Desktop with the other workspaces. First open: replace
   `REPLACE-ON-FIRST-OPEN` with your OneDrive root per `workspace/README.md`, save, reopen.
   Accept the 4 recommended extensions. The file explorer / primary sidebar stays
   on the **left**. If yours is on the right: View → Appearance → Move Primary
   Side Bar Left. Site maintainers open `bbs-web` instead; see
   `workspace/README.md`. Nothing to wire for the BBS doctrine — the plugins' own
   hooks inject it whenever a BBS skill runs.
5. **Restart, then check.** Close every VS Code window and quit the Claude Desktop app
   (Windows: from the tray; Mac: Cmd+Q) so they pick up the new PATH — reopening one window
   is not enough. Then **run `/bbs-checkup`** in a Claude panel. Everything ✅? Done.
   Anything ❌? It prints the exact sentence to send Parker — send it, use the Desktop app
   meanwhile.
6. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## What you just installed, and what each plugin needs

Step 1 installed every plugin, and managed settings keep them on for everyone. You do not
need to install plugins yourself. If you ever have to by hand (the script could not run),
these are the commands — type them in a Claude panel:

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-foundations@bbs-claude-marketplace            # doctrine, CLAUDE.md, reconciliation
/plugin install bbs-claude-coach@bbs-claude-marketplace           # understand / start / extend
/plugin install bbs-sales@bbs-claude-marketplace                  # territory and the quote desk
/plugin install bbs-marketing@bbs-claude-marketplace              # one-pagers, campaign email, logos
/plugin install bbs-back-office@bbs-claude-marketplace            # orders, vendor receipts, margin
/plugin install bbs-website@bbs-claude-marketplace                # the website, price list to page
/plugin install bbs-tools@bbs-claude-marketplace                  # bbs-fill: lets the form scripts run in auto mode
```

That fallback does not install the tools in step 1, so run the script as soon as you can.

New to the toolkit? Run `/bbs-explain-claude` or `/bbs-what-can-i-do` after checkup.

**An install gives you the skills, commands and hooks — and nothing else.** Two things it
does not give you, and they are the two reasons a skill fails on a fresh machine.

**1. Connectors are assigned by Parker, not installed by you.** Run `/mcp` to see which
ones you have. Without them the skills still load, they just have nothing to read.

| Your plugin | Connectors it needs | What breaks without them |
|---|---|---|
| `bbs-foundations` | Microsoft 365 (`bbs-voice-template` only) | the voice template can't sample your Sent Items; everything else works standalone |
| `bbs-sales` | BC MCP, Grainger, Microsoft 365, SCPRS (CA book); Firecrawl optional | Grainger pricing, NASPO quotes and promo pages stop; precedent lookups degrade; intake can't pull from Outlook |
| `bbs-back-office` | **BC MCP**, Grainger, Microsoft 365; CData Connect for `bbs-rebate-profitability` | without BC, nothing to read at all; order reconciliation also needs Grainger and Microsoft 365 |
| `bbs-website` | Supabase, Shopify, Grainger MCP, Firecrawl | catalog and storefront skills can't act |

Missing one? That is the `/bbs-checkup` line you send Parker — it is an admin assignment,
not something you can fix locally.

**2. Four `bbs-sales` skills shell out to software on your PC.** Step 1's bootstrap installs
all of it; this table is here so you can tell *before* you start whether a job will run.
Everything not listed is pure Claude plus connectors.

| Skill | Needs on your machine (all installed by Step 1 on Windows) |
|---|---|
| `ca-form-filler` | `pypdf`, `pymupdf`, `pdftotext` (poppler) |
| `naspo-quote` | `pypdf`, `pymupdf`, `pdftotext` (poppler) |
| `bbs-quote-builder` | Node, the `docx` library, and LibreOffice (`soffice`) for the PDF |
| `grainger-promo-page` | `pdftotext` (poppler) |
| `dgs-bpo-item-check` | nothing — it ships its own 19,390-part lookup |

Most of these check their dependencies before touching a file and print the exact install
command if something is missing — a clear message, never a half-written bid document. Run
`/bbs-checkup` after setup; it verifies these libraries are actually present, so a green
checkup means the document-producing skills will run.

## Daily use

- New RFQ lands in your mailbox (an `_inbox/` folder arrives once Parker's intake flow is
  live): open the workspace, tell Claude what arrived — `/ca-rfq` runs it end to end, asking
  first whether to file it before pricing. You review every number. You send.
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
  Tip: the Claude side panel shows a subset of commands and skills. If a `/command` you
  expect is not offered there, typing `claude` in the integrated terminal gives you all of
  them. Either window works; use whichever you prefer.
- **Cursor** is not part of rep setup; see [`CURSOR-SETUP.md`](CURSOR-SETUP.md) for the maintainer guide.
- **Desktop app**: everything else, or if VS Code is ever broken. Same Claude.

**Files.** In VS Code or the Desktop app's **Code** tab, Claude can read any file you can,
including the synced `Black Box Safety - MASTER` library, without asking. If it ever asks
about reading outside the folder you opened, pick **"Yes, and keep allowing any reads outside
the working directories"**. The answer **"No, and block reads outside the working
directories from now on"** switches those reads off for good, and then Claude cannot open
customer folders; if you picked it, tell Parker. In auto mode it can also change files in
the folder you opened without asking, so check what it changed.
In the Desktop **chat** window, give Claude a file with the paperclip or by dragging it in.

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
