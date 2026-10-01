# Rep setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds the VS Code quote desk: same Claude, same skills — plus you can SEE the files
Claude is reading, side by side. Screenshots will be pinned in the Teams sales channel.

On a Mac the steps are the same, with Cmd for Ctrl; step 1 uses `scripts/bbs-setup.sh`.

## Set up (once)

1. **Run the bootstrap** (~2 minutes, safe to rerun). Download `scripts/bbs-setup.ps1` from
   the marketplace repo (Parker posts it in Teams with the workspace file), then:
   - Open PowerShell (Start → type "PowerShell" → Enter) and `cd` to where you saved the file.
   - Run: `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1` (preview first with
     `-DryRun` if you like). Already set up and `/bbs-checkup` shows a missing plugin or tool?
     Run it again — it is safe to rerun and fixes both.
   - It installs Git, Node, Python, Chrome, LibreOffice, the PDF/OCR tools Claude uses to read
     RFQs, and the Python and Node libraries the form-fill and quote skills build documents with.
     It puts every one of those tools on PATH (`[path]` lines — LibreOffice, Tesseract and Git's
     bash never do it themselves), installs Claude Code's `claude` command if you don't have it,
     and installs every BBS plugin (`[ok]` or `[install]` per plugin).
   - **Done** looks like a line saying `Done.` near the bottom. If instead it says
     `Not done yet`, or any line above says `[later]`: close this PowerShell window, open a
     new one, run the script again, then reopen VS Code. Node and Python only finish their
     extra libraries from a fresh window.
   - Yellow `WARNING:` lines, `[missing]` lines, or `Finished with … to install by hand`, mean
     something failed. A plugin that will not install prints Claude Code's own error under its
     `WARNING:` line — that is the part Parker needs.
   - If anything turns red or yellow, copy the whole window and send it to Parker; don't try
     to fix it.
   - Mac: `scripts/bbs-setup.sh` (needs Homebrew; `--dry-run` to preview). It does the same
     job — tools, Python and Node libraries, `soffice` on PATH, every plugin. If it says
     `python3` is missing, run `xcode-select --install` first, then rerun it.
2. **Install VS Code** — code.visualstudio.com, all defaults.
3. **Install the Claude Code extension** — Extensions sidebar (Ctrl+Shift+X), search
   "Claude Code", install, then sign in with your BBS Claude account (same login as the
   Desktop app).
4. **Open the quote desk** — grab `workspace/bbs-rep.code-workspace` from the marketplace
   repo (Parker posts it in Teams), or run `scripts/install-desktop-launchers.ps1` so it
   lands on your Desktop with the other workspaces. First open: replace
   `REPLACE-ON-FIRST-OPEN` with your OneDrive root per `workspace/README.md`, save, reopen.
   Accept the 4 recommended extensions. The file explorer / primary sidebar stays
   on the **left**. If yours is on the right: View → Appearance → Move Primary
   Side Bar Left. Site maintainers open `bbs-web` instead; see
   `workspace/README.md`. Nothing to wire for the BBS doctrine — the plugins' own
   hooks inject it whenever a BBS skill runs.
5. **Close every VS Code window** (and quit the Claude Desktop app from the tray) so they
   pick up the new PATH — reopening one window is not enough. Then **run `/bbs-checkup`** in
   a Claude panel. Everything ✅? Done. Anything ❌? It prints the
   exact sentence to send Parker — send it, use the Desktop app meanwhile.
6. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## What you just installed, and what each plugin needs

Install the plugins you need. Everyone gets `bbs-foundations` and `bbs-claude-coach`.

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-foundations@bbs-claude-marketplace            # everyone
/plugin install bbs-claude-coach@bbs-claude-marketplace           # everyone — understand / start / extend
/plugin install bbs-sales@bbs-claude-marketplace                  # sales / quoting work
/plugin install bbs-back-office@bbs-claude-marketplace            # purchasing / accounting
/plugin install bbs-website@bbs-claude-marketplace                # whoever maintains the site
```

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
