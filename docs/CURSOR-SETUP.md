# Cursor setup — maintainer guide (future)

**Reps: this is not your setup.** Reps set up with [`docs/REP-SETUP.md`](REP-SETUP.md)
(VS Code / Claude Code). This Cursor guide is for Parker and for future use, and is not
part of rep onboarding (Parker, ruled 2026-09-28).

It adds Cursor as a second window beside the Claude Code Desktop app: the same workspace
file as VS Code, the same Claude Code skills and connectors, plus Cursor chat that can see
the folder you @-mention. Everything in the Desktop app keeps working.

## Set up (once)

1. **Run the bootstrap** — Parker posts the script in Teams with the workspace file.
   - **Mac:** download `scripts/bbs-setup.sh`, then in Terminal:
     `chmod +x bbs-setup.sh && ./bbs-setup.sh`. Needs Homebrew ([brew.sh](https://brew.sh))
     the first time; after that it is two minutes and safe to rerun. It does **not**
     install PowerShell: the BBS doctrine hook runs on the `python3` that ships with the
     Xcode command-line tools (Homebrew installs those), so nothing more is needed.
     `brew install powershell` is optional.
   - **Windows:** `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1`.
   Run only the one for your computer. Either one installs Git, Node, Chrome, LibreOffice,
   the PDF/OCR tools used to read RFQs, and the Python and Node libraries the document skills
   import, then puts each on PATH and installs every plugin in the BBS marketplace.
2. **Install Cursor** — [cursor.com](https://cursor.com), all defaults. Sign in with the
   BBS Google/Microsoft account Parker named for you (not a personal Gmail).
3. **Install the Claude Code extension** — Extensions sidebar (Mac: Cmd+Shift+X, Windows:
   Ctrl+Shift+X), search "Claude Code", install, then sign in with your BBS Claude account
   (same login as the Desktop app). **Pricing, BC, and slash commands live here**, not in
   Cursor's own MCP list.
4. **Open the workspace for your job** — in the Claude Code panel run `/bbs-workspaces`.
   It finds the BBS folders already on this computer and puts a logo'd launcher on the
   Desktop. Or grab a file from `workspace/` and replace the `REPLACE-*` token(s) per
   `workspace/README.md`.
   - Quoting: Quote Desk
   - Site / catalog / bots: Web
   - Admin: Admin
   Accept the recommended extensions on first open. The file explorer / primary
   sidebar stays on the **left** in every BBS workspace and in User settings. If
   yours is on the right, View → Appearance → Move Primary Side Bar Left.
5. **Wait for OneDrive** — the agency folders should not show cloud-only placeholders.
   Open the RFQ PDF once so it actually downloads before you ask Claude to read it.
6. **Cursor plugins (not the same as Claude Code connectors)** — Cursor Settings → Plugins.
   **Outlook and Teams are send-capable: Parker/Griffin only, not for rep machines.**
   Cursor has no org-wide deny, so humans-send would rest on instructions alone. Site
   maintainers: Supabase, Vercel, Firecrawl. Anyone doing UI: Mobbin. See the matrix
   below. Do not paste API keys or URLs with tokens into `~/.cursor/mcp.json`.
7. **User rule, once** — Cursor Settings → Rules → User Rules. Paste the body of
   `.cursor/rules/bbs-invariants.mdc` from this repo (skip the `---` frontmatter). That
   covers you if you ever open a folder that is not the quote desk.
8. **Run `/bbs-checkup`** in the **Claude Code panel** (not the Cursor Agent panel).
   Everything ✅? Done. Anything ❌? It prints the exact sentence to send Parker — send it,
   use the Desktop app meanwhile. Nothing to wire for the BBS doctrine: the plugins' own
   hooks inject it whenever a BBS skill runs, and check 9 confirms they are live.
9. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## What you just installed, and what each surface needs

Cursor is two tools in one window. Mixing them up is the usual first-week failure.

| Surface | How you open it | What it can see |
|---|---|---|
| **Claude Code panel** | Claude icon / the extension you signed into | Marketplace plugins, `/ca-rfq`, `/bbs-checkup`, claude.ai connectors (Grainger, BC, CRM, M365, SCPRS). Managed settings put Outlook and Teams sends behind an Allow prompt and deny the other send tools. |
| **Cursor Agent chat** | Cmd+L / Agent | The files you @-mention, Cursor plugins (Outlook, Teams, …), project rules. **Does not inherit Claude Code's managed settings or connectors.** Pricing still happens in the Claude Code panel. |

Install the plugins you need. Everyone gets `bbs-foundations` and `bbs-claude-coach`.
Run these in the Claude Code panel:

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-foundations@bbs-claude-marketplace            # everyone
/plugin install bbs-claude-coach@bbs-claude-marketplace           # everyone — understand / start / extend
/plugin install bbs-sales@bbs-claude-marketplace                  # sales reps
/plugin install bbs-marketing@bbs-claude-marketplace              # one-pagers, campaign email, logos
/plugin install bbs-back-office@bbs-claude-marketplace            # purchasing / accounting
/plugin install bbs-website@bbs-claude-marketplace                # whoever maintains the site
```

**Connectors are assigned by Parker in claude.ai, not installed by you.** In the Claude
Code panel, `/mcp` lists them. Without them the skills still load, they just have nothing
to read. Who is assigned which connector is ruled in
[`plugins/bbs-foundations/docs/MANAGED-SETTINGS.md`](../plugins/bbs-foundations/docs/MANAGED-SETTINGS.md);
what each skill needs is `python3 scripts/check_marketplace.py --requirements`. Short version:

| Your plugin | claude.ai connectors it needs |
|---|---|
| `bbs-foundations` | M365 (`bbs-voice-template` only) |
| `bbs-claude-coach` | none |
| `bbs-sales` | BC, Grainger, M365, SCPRS (CA book); Firecrawl optional |
| `bbs-back-office` | BC, Grainger, M365; CData Connect for `bbs-rebate-profitability` |
| `bbs-website` | Supabase, Shopify, Grainger, Firecrawl — **Parker / Griffin only** |

Everyone is also assigned the BBS Sales CRM MCP (pipeline of record); no skill requires it.

### Cursor plugins — role matrix

These are Cursor Settings → Plugins. They are *not* the claude.ai connectors.

| Cursor plugin | Who | Why |
|---|---|---|
| Outlook | **Parker / Griffin only** — send-capable; not for rep machines | RFQs in **your** inbox. Sign in as yourself. Cursor has no org-wide deny, so humans-send would rest on instructions alone |
| Teams | **Parker / Griffin only** — send-capable; not for rep machines | The sales channel. Same reason as Outlook |
| Mobbin | Anyone doing UI on the site | Real-app design references |
| Firecrawl | Site maintainers / Parker | Crawl; needs its own login |
| Supabase | Site maintainers / Parker | Catalog. A mass UPDATE from a quote session is the failure mode |
| Vercel | Site maintainers / Parker | Deploy |

Parker-local only (do not add these on a rep machine): local Grainger stdio, SCPRS or CRM
URLs that contain a path token, any `~/.cursor/mcp.json` copied from someone else.

## What to type (cheat sheet)

Slash commands work in the **Claude Code panel**. Plain English works in both; @-mentions
are a Cursor Agent habit.

| You want | Type |
|---|---|
| New RFQ, end to end | `/ca-rfq` with the PDF @-mentioned — it asks first whether to file it, then prices, quotes, and fills the packet |
| Just file it, or just price it | "Log this RFQ for [agency]" / "Price this against CMC" (or the buying institution's name) — `/ca-rfq` carries either as a gate |
| Last time we quoted this buyer | "What did we quote this buyer last? Check quote-log and BC." |
| Grainger cost on NASPO | "Price these Grainger parts against [institution]'s own account." |
| Packet | "Fill the CA packet for this quote. Flag anything you cannot source." |
| Claude got it wrong | One line in that folder's `FLAGS.md` |
| Machine feels off | `/bbs-checkup` in the Claude Code panel |

**@-mention the small thing, not the whole tree.** @ the buyer folder, the RFQ PDF, and
`quote-log.md`. @ `FILLED/` when you need a precedent packet. Do not @ `State of CA
Agencies` — that dumps thousands of files into context and the model starts guessing.

**Models.** Leave Cursor on Auto for quote-desk chat. Use Sonnet in Claude Code for
ordinary RFQs; Opus only when the packet or the agency situation is actually hard. Do not
pin a model in the workspace.

**Never type** "send this to the buyer", "place the order", or "write this invoice to BC".
You send from Outlook, as always.

## Daily use

Same habits as [`REP-SETUP.md`](REP-SETUP.md): one RFQ per Claude Code session (`/clear`
before the next), `/btw` for a side question, `/rename <agency>-<item>` on a multi-day
deal. New RFQ in your mailbox → open the workspace → tell Claude what arrived → review
every number → you send.

PDF and Excel open in tabs (that is why those two extensions exist). Word wrap is on so
`quote-log.md` is readable. Format-on-save is off so a customer worksheet is not rewritten
out from under you.

## When to use which window

- **Cursor**: Parker's machine, when you want the file tree, Cursor plugins, and Claude
  Code in one app. Not a rep window.
- **VS Code**: the rep default, Mac and Windows — the same workspace file and the same
  Claude Code extension. [`REP-SETUP.md`](REP-SETUP.md).
- **Desktop app**: everything that is not folder work, or if Cursor/VS Code is broken.
  Same Claude, same connectors.

## The ground rules

Read and sign the one-page use policy (bbs-foundations → docs/AUP.md). Short version:
approved tools only for company data, every number human-reviewed, you send everything,
log it when Claude gets it wrong, experiment freely otherwise.

## What else makes a non-technical user fast (shipped vs later)

Built into this repo on purpose:

- The workspace file (autosave, wrap, no format-on-save, FILLED stays searchable, git UI
  off so OneDrive does not look like a broken repo).
- The BBS invariants Cursor rule (always on in this repo; stamped onto the desk folder by
  Parker; paste once as a User Rule).
- Mac bootstrap including LibreOffice, matching the Windows script.
- This cheat sheet, the plugin matrix, and `/bbs-checkup` still as the "tell Parker"
  sentence.

Deliberately **not** in git (Parker-local or a later pass):

- Anyone's `~/.cursor/mcp.json`. Path tokens and Grainger keys do not belong in a repo.
- A Cursor equivalent of Claude Code managed settings (org-wide deny). Until that exists,
  the invariants rule plus "do not add send-capable MCP servers" is the control.
- Screenshot-in-chat training beyond "open the PDF in a tab, then @ it".
- Pinning Opus. Cost without a quality gain on a gloves RFQ.
- Extra extensions (Word preview, CSV rainbow, linters). PDF + Excel cover the RFQs we
  actually get; LibreOffice covers export.

Parker still does the clicks a repo cannot: assign claude.ai connectors, stamp
`.cursor/rules/bbs-invariants.mdc` onto the desk root, and post the workspace + bootstrap
in Teams. Outlook/Teams Cursor plugins go on Parker's and Griffin's Cursor only.

## Level up (optional, free)

Anthropic Academy "Claude 101": anthropic.skilljar.com/claude-101. Cursor's own 2-minute
tour is enough for @-mentions and Agent vs Chat. Ask Parker both the how-do-I and the
it's-broken questions for now, with your `/bbs-checkup` line for the latter.
