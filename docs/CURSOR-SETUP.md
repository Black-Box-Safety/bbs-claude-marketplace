# Cursor setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds Cursor as a quote-desk window: the same workspace file as VS Code, the same
Claude Code skills and connectors, plus Cursor chat that can see the RFQ folder you
@-mention. Screenshots will be pinned in the Teams sales channel.

On Windows with VS Code instead, use [`docs/REP-SETUP.md`](REP-SETUP.md). The workspace
file is the same either way.

## Set up (once)

1. **Run the bootstrap** — Parker posts the script in Teams with the workspace file.
   - **Mac:** download `scripts/bbs-setup.sh`, then in Terminal:
     `chmod +x bbs-setup.sh && ./bbs-setup.sh`. Needs Homebrew ([brew.sh](https://brew.sh))
     the first time; after that it is two minutes and safe to rerun.
   - **Windows:** `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1`.
   It installs Git, Node, Chrome, LibreOffice, and the PDF/OCR tools used to read RFQs.
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
   Accept the recommended extensions on first open.
5. **Wait for OneDrive** — the agency folders should not show cloud-only placeholders.
   Open the RFQ PDF once so it actually downloads before you ask Claude to read it.
6. **Cursor plugins (not the same as Claude Code connectors)** — Cursor Settings → Plugins.
   Everyone who quotes: **Outlook** and **Teams**, signed in as *you*. Site maintainers
   only: Supabase, Vercel, Firecrawl. Anyone doing UI: Mobbin. Parker assigns the rest
   (see the matrix below). Do not paste API keys or URLs with tokens into
   `~/.cursor/mcp.json`.
7. **User rule, once** — Cursor Settings → Rules → User Rules. Paste the body of
   `.cursor/rules/bbs-invariants.mdc` from this repo (skip the `---` frontmatter). That
   covers you if you ever open a folder that is not the quote desk.
8. **Run `/bbs-onboard`** once in the **Claude Code panel** (not the Cursor Agent panel) —
   wires the skill-bus doctrine so BBS grounding rules fire inside the quoting skills.
9. **Run `/bbs-checkup`** in that same Claude Code panel. Everything ✅? Done. Anything ❌?
   It prints the exact sentence to send Parker — send it, use the Desktop app meanwhile.
10. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## What you just installed, and what each surface needs

Cursor is two tools in one window. Mixing them up is the usual first-week failure.

| Surface | How you open it | What it can see |
|---|---|---|
| **Claude Code panel** | Claude icon / the extension you signed into | Marketplace plugins, `/ca-rfq-quote`, `/bbs-checkup`, claude.ai connectors (Grainger, BC, CRM, M365, SCPRS). Managed settings deny send-class tools. |
| **Cursor Agent chat** | Cmd+L / Agent | The files you @-mention, Cursor plugins (Outlook, Teams, …), project rules. **Does not inherit Claude Code's deny list or connectors.** Pricing still happens in the Claude Code panel. |

Install only the marketplace plugin for your desk. Everyone gets `bbs-foundations`.
Run these in the Claude Code panel:

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-foundations@bbs-claude-marketplace            # everyone
/plugin install bbs-sales@bbs-claude-marketplace                  # sales reps
/plugin install bbs-back-office@bbs-claude-marketplace            # purchasing / accounting
/plugin install bbs-website@bbs-claude-marketplace                # whoever maintains the site
```

**Connectors are assigned by Parker in claude.ai, not installed by you.** In the Claude
Code panel, `/mcp` lists them. Without them the skills still load, they just have nothing
to read. The matrix in [`plugins/bbs-foundations/docs/MANAGED-SETTINGS.md`](../plugins/bbs-foundations/docs/MANAGED-SETTINGS.md)
is the source; short version:

| Your plugin | claude.ai connectors it needs |
|---|---|
| `bbs-foundations` | none |
| `bbs-sales` | BC, Grainger, M365, SCPRS (CA book), Sales CRM |
| `bbs-back-office` | BC |
| `bbs-website` | Supabase, Shopify, Grainger, Firecrawl — **Parker / Griffin only** |

### Cursor plugins — role matrix

These are Cursor Settings → Plugins. They are *not* the claude.ai connectors.

| Cursor plugin | Who | Why |
|---|---|---|
| Outlook | Everyone who quotes | RFQs in **your** inbox. Sign in as yourself. |
| Teams | Everyone who quotes | The sales channel, not a second chat silo |
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
| File today's RFQ and start the record | `/ca-rfq-log` — or "Log this RFQ for [agency]" with the PDF @-mentioned |
| Price it | `/ca-rfq-quote` — or "Price this against CMC" / the buying institution's name |
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

- **Cursor**: quote work on a machine where you want the file tree, Outlook/Teams plugins,
  and Claude Code in one app. Default on Mac.
- **VS Code**: the same workspace file, if that is what your machine already runs. Same
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
`.cursor/rules/bbs-invariants.mdc` onto the desk root, post the workspace + bootstrap in
Teams, and enable Outlook/Teams for each quoting rep's Cursor account.

## Level up (optional, free)

Anthropic Academy "Claude 101": anthropic.skilljar.com/claude-101. Cursor's own 2-minute
tour is enough for @-mentions and Agent vs Chat. Ask Parker both the how-do-I and the
it's-broken questions for now, with your `/bbs-checkup` line for the latter.
