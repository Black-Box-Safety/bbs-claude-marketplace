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
| `permissions.ask` | Push, PR create/merge, Vercel deploy, Shopify theme push; Outlook calendar event create/update/delete, which email invites, updates and cancellations to attendees (Parker, 2026-10-01) | Plan → approve → execute is doctrine; this makes the tool enforce it |
| `permissions.deny` | `rm -rf`, force-push, hard reset, `gh repo delete`, reading `.env` files: `Read(**/.env)` and siblings cover the session folder and below, and since 2026-10-02 `Read(~/**/.env)` and siblings cover the whole home folder (Parker, ruling (c)); a `.env` outside both (elsewhere on `C:\` outside the home folder, or on another drive) is not covered | The irreversible actions and the secret files + send-class tools (draft-first): Outlook send/forward, meeting responses, inbox rules (a rule can auto-forward mail) and auto-replies (Parker, 2026-10-01), Teams messages, SignNow invites, QuickBooks estimate/invoice/payment-link sends. Since 2026-10-02 (Parker, connector access): every QuickBooks `qbo_payroll_*` tool, and Vercel's purchase tools (`buy_*`, `create_or_transfer_domain`) and `delete_project`, for everyone. Deny rules apply in auto mode too, before its classifier. `Read(**/.env)` does not block `.env.example` |
| `env.CAVEMAN_DEFAULT_MODE=off` | Caveman stays off until a rep types `/caveman` | The plugin's own default is `full`; without this every rep session — including customer-email drafting — would start terse |
| `env.CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000` | Plugin and marketplace clones get ten minutes, not the 120 s default | A large plugin overran 120 s on a laptop whose antivirus scans every file. Moved here from the bootstrap's saved copy (2026-10-01) so it lives in one place; the bootstrap still sets it for its own install run |
| `env.CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=1` | A winget- or Homebrew-installed Claude Code updates itself | A native install ignores it. Moved from the Windows bootstrap's saved copy (2026-10-01) |
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
Parker asked for actually happens.

**Everyone reads every connector; writing to a shared space is by request** (Parker, in
session, 2026-10-02; `docs/STEWARD.md`, "Connector access"). The team is small, so no
information is walled off by role. What is held back is the ability to *change* a space the
whole company relies on: the catalog, the storefront, the site, the books, the pipeline,
SharePoint, signing. A person who needs to write to one asks Parker, and Parker grants it to
that person. Two things are blocked for everyone, admins included: QuickBooks payroll, and
Vercel purchases and project deletion (managed `permissions.deny` plus the console `blocked`
control, `docs/ADMIN-RUNBOOK.md` §3). A person's own Outlook drafts and own calendar are not
shared spaces: drafts stay allowed, invites stay `ask`.

Of the connectors on Parker's account today:

| Connector | Read | Write to the shared space | Why |
|---|---|---|---|
| Business Central — BC MCP (Custom API) (read-only: `bc_customer_snapshot`, `bc_find_item`, …) | **Everyone** | None: the connector has no write tools | Quote of record, AR, open orders. **Interim** until Microsoft's official BC MCP works in Claude Code; tool names change at the swap (grep list in the v1.1 backlog), and the new tools must be re-checked for writes. BC Chat Connector retired 2026-09-13 |
| Grainger (`grainger_search` / `grainger_price` / `grainger_availability`) | **Everyone** | None: read tools only | Per-account pricing is doctrine; this is how it is read without the open web |
| ca-procurement-intel / SCPRS (`explore_sql`, `play_*`) | **Everyone** | By request | Competitive intelligence and buyer segments |
| Microsoft 365 (Outlook, SharePoint, Teams search) | **Everyone** | Own Outlook drafts: everyone. SharePoint writes: by request, through the person's SharePoint permissions | It signs in as the person (it reads their own mailbox), so SharePoint's own permissions decide who can write. Send, forward and Teams messages stay denied |
| BBS Sales CRM MCP | **Everyone** | By request | Pipeline of record (ruled 2026-09-13). It exposes `crm_update_record`; see "Enforcing write by request" |
| Supabase | **Everyone**, through a read-only connection | By request | The catalog is the source of truth; a mass UPDATE from a quote session is the failure mode |
| Shopify admin, Vercel, Firecrawl, Dataverse, SignNow, Adobe | **Everyone** | By request | Storefront, site, crawl, data, signing and design. Vercel purchases and project deletion are blocked for everyone |
| QuickBooks | **Everyone**, payroll excluded | By request | The books. Every `qbo_payroll_*` tool is denied and blocked for everyone, admins included: payroll is personnel data |

### Enforcing write by request

Managed settings and the console `blocked` control are **org-wide**: they cannot give one
person write access and withhold it from another. So the per-person switch lives in one of
two places, and which one depends on how the connector signs in.

1. **The connector signs in as the person.** That system's own permissions decide, and
   Parker grants write there (a SharePoint site permission, a staff role). Microsoft 365
   works this way.
2. **The connector signs in with one shared credential.** Everyone assigned to it can do
   whatever that credential can. Read for everyone then needs a **read-only connection**
   (a read-only key, role or mode) assigned to everyone, with the write-capable connection
   assigned only to the people approved for write. Until a connector's read-only path is
   confirmed, its write-capable connection goes only to approved writers and its read for
   everyone waits.

Which way each connector signs in is not recorded in this repo. **Parker confirms it per
connector** (Supabase, Shopify admin, Vercel, Sales CRM, SCPRS, QuickBooks, SignNow,
Dataverse, Adobe, Firecrawl) before assigning it to everyone. The Sales CRM is already on
everyone's account and exposes `crm_update_record`; no skill in this repo writes to the CRM.

The ruling covers claude.ai connectors. **Cursor plugins are unchanged**: Outlook and Teams
there are send-capable with no org-wide deny, so they stay off rep machines
(`AGENTS.md` invariant 5, `docs/CURSOR-SETUP.md`).

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

Doctrine says "humans send quotes." The `permissions.deny` block now enforces it: the
send-class M365/SignNow tools are denied (including SignNow's embedded-invite tools, which
mint live signing links), so Claude drafts email and packets but cannot transmit them — the
rep sends from Outlook/SignNow as always. This was specced as a PreToolUse hook; deny rules
achieve the same guarantee with nothing to install or debug on rep machines. Caveat: the
tool-name prefix derives from the connector's name per account, and a deny on a nonexistent
name is a silent no-op — so deployment verification (ADMIN-RUNBOOK §1) includes asking
Claude to send a test email and expecting a denial, on the admin machine AND the pilot
rep's. The same caveat holds for the allow rules: a rule on a wrong connector name only
means a prompt, never an unwanted action. If a future connector adds a new send-class tool, add it to the deny list in the
same commit that documents it here. AUP.md is the human-side counterpart, linked from the
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
- **Where the send-class denies do not reach.** The deny rules above name connector tools
  as `mcp__claude_ai_<server>__<tool>`, which the docs apply to "connectors Claude Code
  fetches itself": the terminal and the VS Code panel. In the Desktop app's **Code** tab the
  app hands connectors to Claude Code directly, and "no MCP setting or `managed-mcp.json`
  reaches them"; the documented control there is the claude.ai admin console's per-tool
  connector controls (`blocked`) (*mcp*, "How connectors reach Claude Code"; *desktop*,
  enterprise section; checked 2026-10-02). Server-managed settings do not reach the Desktop
  **chat** window or **Cowork** at all. So on the Desktop app (Code tab and chat) and in
  Cowork, "humans send" rests on the console's `blocked` control, which the docs say the
  desktop app and claude.ai chat apply (Cowork unverified). Ruled 2026-10-02 (d): every
  connector tool this file's `permissions.deny` names is also set to `blocked` in the
  console (`docs/ADMIN-RUNBOOK.md` §3). Parker's test send from a Desktop Code-tab session
  was denied the same day; what denied it is not shown, so the console setting stays. In the
  chat window a person gives Claude a file with the paperclip or by dragging it in.
- **No `bbs-bc-mcp-proxy`.** Retired 2026-09-02 in favour of the Business Central claude.ai
  connector.
