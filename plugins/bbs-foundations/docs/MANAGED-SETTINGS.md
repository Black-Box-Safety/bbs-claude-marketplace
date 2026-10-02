# Managed settings — the one config every BBS machine gets

`bbs-managed-settings.json` beside this file is the settings block Parker pushes from the
remote (server-managed) source that populates `~/.claude/remote-settings.json` on every
teammate's machine. That file is a **mirror**: local edits are overwritten on refresh, so
this is the only place to change it. This document says what each block does and why, so
the next person to edit it does not have to reverse-engineer it.

Owner: Parker Marshall. Last verified: 2026-09-18. Company facts in the `claudeMd` block
come from `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`;
when that file changes, change the block.

## What it does, block by block

| Block | Purpose | Why it matters for a small team |
|---|---|---|
| `extraKnownMarketplaces` | Registers **one** BBS marketplace | Two marketplaces named after forks confused install instructions in August. The doctrine that fires when a skill runs ships inside the plugins themselves (`hooks/hooks.json`), so no second marketplace is needed for it |
| `enabledPlugins` | `bbs-foundations`, `bbs-claude-coach`, `bbs-sales`, `bbs-marketing`, `bbs-back-office`, `bbs-website`, `bbs-tools`, `claudeforge`, `impeccable`, plus the commons: `superpowers-chrome`, `caveman`, `document-skills` — all on, for everyone | Nine people. The cost of an unused plugin is a few lines of context; the cost of a rep missing the quote-desk skill is a lost bid. Literacy (`bbs-claude-coach`) and post-award (`bbs-back-office`) are company-wide too. `bbs-website` is advisory, so a rep having it costs nothing. `bbs-marketing` added 2026-10-01: it shipped in #39 without a row here, so neither managed settings nor the bootstrap installed it. The bootstraps install every plugin in `marketplace.json` unless this list sets it `false`. `bbs-tools` (2026-10-01) carries only the `bbs-fill` launcher the allow rule below names |
| _(no `mcpServers`)_ | Grainger, BC, SCPRS, CRM, M365 are all claude.ai connectors (ruled 2026-09-13) | Connectors are assigned in the admin console, never configured per machine. The local `grainger-api` stdio server stays on admin machines only; a `mcpServers` entry here would show red in `/mcp` on every rep machine that lacks it |
| `permissions.allow` | Read-only git/gh and file tools without prompts + the superpowers-chrome browser tool (full browser access is a ruling; prompts per click would defeat it). Since 2026-10-01 (R4): `Bash(bbs-fill *)` — the vetted form and quote scripts, through the `bbs-tools` launcher, which runs only allow-listed scripts; the read-only Grainger MCP and BC MCP Custom API tools; Outlook **draft** creation and editing. Bare `Read` "matches all file reads" (permissions docs, *Match all uses of a tool*; checked 2026-10-02): Claude Code reads any file the person can open without a prompt, the synced MASTER library included, and also `~/.ssh`, browser profiles and other projects. Whether to narrow it is OPEN (`docs/STEWARD.md`, 2026-10-02). **Never** `Bash(python:*)` or a path-pattern rule: a `*` matches anything, so such a rule would let a crafted command run arbitrary Python past auto mode | Fewer prompts on the actions that cannot break anything, and auto mode no longer stops a rep mid-packet (Kim, 2026-10-01) |
| `permissions.ask` | Push, PR create/merge, Vercel deploy, Shopify theme push; Outlook calendar event create/update/delete, which email invites, updates and cancellations to attendees (Parker, 2026-10-01); since 2026-10-02 the Outlook and Teams send-class tools (send, forward, meeting responses, inbox rules, auto-replies, the three Teams sends; also `ask` in the admin console), so Claude can send but every send waits for a person's Allow (Parker, 2026-10-02) | Plan → approve → execute is doctrine; this makes the tool enforce it |
| `permissions.deny` | `rm -rf`, force-push, hard reset, `gh repo delete`, reading `.env` files: `Read(**/.env)` and siblings cover the session folder and below, and since 2026-10-02 `Read(~/**/.env)` and siblings cover the whole home folder (Parker, ruling (c)); a `.env` outside both (elsewhere on `C:\` outside the home folder, or on another drive) is not covered | The irreversible actions and the secret files, plus the send-class tools that stay off: Outlook `send_draft` (its Allow prompt shows only a message id, not the email; Parker, 2026-10-02), SignNow invites and QuickBooks estimate/invoice/payment-link sends. The Outlook and Teams sends are in `permissions.ask` (row above). Deny rules apply in auto mode too, before its classifier, and hold over users' mods. `Read(**/.env)` does not block `.env.example` |
| `env.CAVEMAN_DEFAULT_MODE=off` | Caveman stays off until a rep types `/caveman` | The plugin's own default is `full`; without this every rep session — including customer-email drafting — would start terse |
| `env.CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000` | Plugin and marketplace clones get ten minutes, not the 120 s default | A large plugin overran 120 s on a laptop whose antivirus scans every file. Moved here from the bootstrap's saved copy (2026-10-01) so it lives in one place; the bootstrap still sets it for its own install run |
| `env.CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=1` | A winget- or Homebrew-installed Claude Code updates itself | A native install ignores it. Moved from the Windows bootstrap's saved copy (2026-10-01) |
| `pluginConfigs` → `cc-plugin-sec-default@builtin` → `allowManagedModsOnly: true` | Only the organization's own mods load; a mod a user installs, loads with `--plugin-dir`, or Claude writes mid-session does not (Parker, 2026-10-02) | A user's mod can approve a call an `ask` rule would prompt for, so without this the per-send Allow could be skipped. Plugins' `hooks/hooks.json` hooks (ours) are not mods and keep running. A mod in a plugin from a GitHub marketplace counts as a user's and stops loading; as of 2026-10-02 none of ours or the pinned commons ship one (`impeccable` and `claudeforge` track moving branches, so recheck when they update) |
| `disableBypassPermissionsMode` | Nobody can run `--dangerously-skip-permissions` | For a team that is not native with AI, the permission prompt is the seatbelt |
| `claudeMd` | Company memory injected into **every** session on every machine | The nine rules that hold everywhere, the exact strings, the systems of record, and where the detail lives. Managed-settings-only field, so it cannot be overridden by a repo file. This is the fastest path to "the same answer Parker would give" |
| `companyAnnouncements` | One rotating line at startup | Onboarding by repetition |
| `autoUpdatesChannel: stable` | Skip release-candidate builds | Fewer surprises on machines nobody is debugging |
| `cleanupPeriodDays: 60` | Transcripts kept two months | Long enough to `/resume` a quote thread from last month |

## Before pasting it

1. **Rotate the Grainger gateway key.** The old one was distributed in plaintext to every
   machine and pasted into at least one chat. Issue a new one; put it in
   `~/grainger-api/mcp/.env` on admin machines only (`GRAINGER_GATEWAY_API_KEY=...`). The distributed
   config no longer carries it.
2. **Confirm connector assignments** in the admin console match the matrix below (Grainger,
   BC, SCPRS, CRM, M365). No `mcpServers` block ships; reps get everything as connectors.
3. **Remove `bbs-ops@bbs-claude-marketplace`** from any existing config. The plugin is
   `bbs-website` as of marketplace PR #4. The old id installs nothing.
4. **Check the official Anthropic marketplace still installs** after pushing. This file does
   not set `strictKnownMarketplaces`, so it will; see the hardening note below before you do.

## After pasting it

Each machine: restart Claude Code, then `/plugin marketplace update`, then `/bbs-my-voice`
once (`/bbs-onboard` is the website pipeline tour). The doctrine hooks need no step: they
are active as soon as the plugins load. The test
that matters: a teammate opens a repo they have never seen and runs `/bbs-claude-md audit`
without asking anyone.

## Optional hardening (not in the file — read first)

**`strictKnownMarketplaces`** turns the registered marketplaces into an allowlist: nobody
can add a marketplace that is not on it. Right for a small business, with two caveats that
have bitten people:

- Any allowlist **silently disables the `~/.claude/skills/` auto-load** unless the list also
  contains `{ "source": "skills-dir" }`. Parker has hundreds of local skills there.
- The official Anthropic marketplace (`claude-plugins-official`, source of
  `claude-md-management`) must be on the list or nobody can install from it. Get its exact
  source from `/plugin marketplace list` on a machine that has it; do not guess the repo.

```json
"strictKnownMarketplaces": [
  { "source": "github", "repo": "Black-Box-Safety/*" },
  { "source": "skills-dir" },
  { "...": "the official marketplace's source, copied from /plugin marketplace list" }
]
```

**`allowedMcpServers`** would allowlist MCP servers the same way. Not recommended yet: the
team's Business Central and Microsoft 365 connectors are claude.ai connectors, not
`mcpServers` entries, and a wrong allowlist here blocks a rep's local dev server with no
useful error.

## Connectors — managed in claude.ai, not in this file

`mcpServers` here covers only local stdio servers. The connectors the team reaches through
claude.ai (Claude Code, Desktop, and the web app all share them) are enabled per user or
per organization in **claude.ai → Settings → Connectors**, and that is where the alignment
Parker asked for actually happens. Of the connectors on Parker's account today:

| Connector | Who should have it | Why |
|---|---|---|
| Business Central — BC MCP (Custom API) (read-only: `bc_customer_snapshot`, `bc_find_item`, …) | **Everyone** | Quote of record, AR, open orders. Read-only, so no approval risk. Replaced the retired `bbs-bc-mcp-proxy`. **Interim** until Microsoft's official BC MCP works in Claude Code; tool names change at the swap (grep list in the v1.1 backlog). BC Chat Connector retired 2026-09-13 |
| BBS Sales CRM MCP | **Everyone** | Pipeline of record (ruled 2026-09-13) |
| Microsoft 365 (Outlook, SharePoint, Teams search) | **Everyone** | RFQ intake, bid history in `MASTER/Customers`, sent-mail sampling for `/bbs-my-voice` |
| Grainger (`grainger_search` / `grainger_price` / `grainger_availability`) | **Everyone who quotes** | Per-account pricing is doctrine; this is how they get it without the open web |
| ca-procurement-intel / SCPRS (`explore_sql`, `play_*`) | **Reps on the CA state book** | Competitive intelligence and buyer segments for promo pages |
| Supabase | **Site maintainers only**, read-only where possible | The catalog is the source of truth; a mass UPDATE from a rep's session is the failure mode |
| Shopify admin, Vercel, Firecrawl, Dataverse, QuickBooks, SignNow, Adobe | **Parker / Griffin only** | Admin, deploy, finance, or single-purpose. Not team tools |

The `claudeMd` block already tells every session which system of record answers which
question, so a teammate with the right connectors gets routed correctly without reading this.

**Cursor is a different surface.** claude.ai connectors reach Cursor only through the
Claude Code extension (`/mcp` in that panel). Cursor Settings → MCP / Plugins is a
separate list, and reps do not use Cursor (ruled 2026-09-28): Outlook and Teams are
send-capable and Parker/Griffin only, Mobbin for UI work, Supabase / Vercel / Firecrawl
for site maintainers. Do not put Grainger keys,
SCPRS path tokens, or CRM path tokens in a committed `mcp.json`. The role matrix and
the first-open path live in `docs/CURSOR-SETUP.md`.

## Parker-local skills — already promoted, now waiting to be retired

This section used to list personal skills "worth promoting". **They are promoted.** Every
one of them has a marketplace copy, and that copy is the maintained one.

What is left is the opposite job: retiring the personal copies, 15 of them, which shadow
the marketplace in Parker's own sessions. The 2026-09-15 consolidation made five of them
outright contradictions — `bbs-b2b-pricing` still drives the retired
`b2b.blackboxsafety.com` punch-out, and `obs-form-filler`, `grainger-cart-info`,
`grainger-screenshot` and `dwr-pdf-info` compete with the skills that replaced them.

They are **account-synced**: they live in Parker's claude.ai account, not on disk and not
in this repo, so they can only be removed in claude.ai → Settings → Capabilities → Skills.
`HANDOFF.md` carries the confirmed mechanism, the evidence, and the order.

## Draft-first enforcement (2026-09-11)

Doctrine says "humans send quotes." Since 2026-10-02 (Parker) that means a person approves
every send: the Outlook and Teams send-class tools sit in `permissions.ask`, so Claude can
send an email or Teams message but each one stops for an Allow click. `outlook_send_draft`
stays denied, because its prompt shows only a message id, so the rep would approve an id
rather than the email; Claude sends with `outlook_send_mail`, whose prompt shows recipients,
subject and body, and drafts Claude writes are sent by the rep from Outlook. The SignNow
tools (including the embedded-invite tools, which mint live signing links) and the
QuickBooks sends stay in `permissions.deny`. Ask rules hold in auto mode too; a user's mod
could approve past one, which is why `allowManagedModsOnly` is set. Before 2026-10-02 the
Outlook and Teams tools were denied outright. This was specced as a PreToolUse hook; deny rules
achieve the same guarantee with nothing to install or debug on rep machines. Caveat: the
tool-name prefix derives from the connector's name per account, and a deny on a nonexistent
name is a silent no-op — so deployment verification (ADMIN-RUNBOOK §1) includes asking
Claude to send a test email and expecting an Allow prompt (not a silent send), on the admin
machine AND the pilot rep's. The same caveat holds for the allow rules: a rule on a wrong connector name only
means a prompt, never an unwanted action. If a future connector adds a new send-class tool, add it to the ask or deny list in
the same commit that documents it here. AUP.md is the human-side counterpart, linked from the
`claudeMd` block.

## Empowerment posture (2026-09-11)

Ruling: reps may install skills, author their own, and experiment. The strict lockdown keys
(`strictKnownMarketplaces`, `strictPluginOnlyCustomization`, model restrictions) are
deliberately absent. Guardrails cover irreversible acts and the money path only.

## Commons (2026-09-13)

Three pinned third-party plugins ship to everyone: `superpowers-chrome` (real-Chrome browsing),
`caveman` (opt-in terse mode), and Anthropic's `document-skills` (docx/pdf/xlsx). Curation,
bar, and refresh cadence: `docs/COMMONS.md`. The browser tool is on the allow list on purpose —
reps browse to find products, and the pricing-source rule (no price from the open web) is a
rule about where numbers come from, not a restriction on browsing. Caveman is forced off by default
through the managed `env` block; a rep turns it on per session with `/caveman lite` or
`/caveman full`.

## What is deliberately not here

- **No API keys, tokens, or buying account numbers.** Those live in
  `~/grainger-api/mcp/.env` on admin machines. FEIN, seller's permit and cert numbers live
  in `plugins/bbs-sales/references/vendor_profile.json`, committed deliberately in this
  private repo — not re-keyed into a CLAUDE.md.
- **No hooks.** The plugins carry their own (`bbs-foundations` and `bbs-website` inject
  doctrine, `bbs-sales` guards the quote-desk tree); `bbs-website` ships one template
  validator in `bbs-database`'s repo settings where it belongs.
- **No model pin.** People pick per task; the `claudeMd` block names the three current IDs
  so nobody writes a stale one into a file.
- **No MASTER-specific read rule and no `additionalDirectories`.** Bare `Read` already
  reads the library. Making it a working folder would let edits be auto-accepted across it.
  A `Read(~/**/*Black Box Safety - MASTER/**)` rule was drafted 2026-10-02 and dropped in
  review as redundant (PR #47).
- **Where the send-class ask and deny rules do not reach.** The rules above name connector tools
  as `mcp__claude_ai_<server>__<tool>`, which the docs apply to "connectors Claude Code
  fetches itself": the terminal and the VS Code panel. In the Desktop app's **Code** tab the
  app hands connectors to Claude Code directly, and "no MCP setting or `managed-mcp.json`
  reaches them"; the desktop app "applies the session's ordinary permission rules to those
  tools" (*mcp*, "How connectors reach Claude Code"; *desktop*, enterprise section; checked
  2026-10-02). Server-managed settings do not reach the Desktop **chat** window or
  **Cowork** at all. The admin console's per-tool connector controls have two settings:
  `blocked` (the tool is gone, org-wide, Claude Code included) and `ask` (Claude Code
  prompts on every call, even in auto mode, never offers to remember the answer, and allow
  rules do not skip it) (*mcp*, "Organization controls on connector tools"). So the denied
  tools are also `blocked` in the console, and the Outlook and Teams send tools are set to
  `ask` there as a second control (`docs/ADMIN-RUNBOOK.md` §3; Parker, 2026-10-02). The docs
  say org `ask` does not reach the Desktop app's local sessions and do not say whether
  claude.ai chat honours it, so on the Desktop app whether a send stops for an Allow is
  unverified; ADMIN-RUNBOOK §3 has the test. In the chat window a person gives Claude a file
  with the paperclip or by dragging it in.
- **No `bbs-bc-mcp-proxy`.** Retired 2026-09-02 in favour of the Business Central claude.ai
  connector.
