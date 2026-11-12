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
| `enabledPlugins` | `bbs-foundations`, `bbs-claude-coach`, `bbs-sales`, `bbs-marketing`, `bbs-back-office`, `bbs-website`, `bbs-tools`, `agent-team`, `claudeforge`, `impeccable`, plus the commons: `superpowers-chrome`, `caveman`, `document-skills` — all on, for everyone | Nine people. The cost of an unused plugin is a few lines of context; the cost of a rep missing the quote-desk skill is a lost bid. Literacy (`bbs-claude-coach`) and post-award (`bbs-back-office`) are company-wide too. `bbs-website` is advisory, so a rep having it costs nothing. `bbs-marketing` added 2026-10-01: it shipped in #39 without a row here, so neither managed settings nor the bootstrap installed it. The bootstraps install every plugin in `marketplace.json` unless this list sets it `false` or its entry carries the `maintainer` keyword (maintainer-tier, Parker installs by hand: `docs/COMMONS.md`, Parker 2026-10-28; `taste-skill` is the first). `bbs-tools` (2026-10-01) carries only the `bbs-fill` launcher the allow rule below names. `agent-team` (2026-10-13, Parker in session): company-neutral roster and steward skills, on for everyone so any program can use them |
| _(no `mcpServers`)_ | Grainger, BC, SCPRS, CRM, M365 are all claude.ai connectors (ruled 2026-09-13) | Connectors are assigned in the admin console, never configured per machine. The local `grainger-api` stdio server stays on admin machines only; a `mcpServers` entry here would show red in `/mcp` on every rep machine that lacks it |
| `permissions.allow` | Read-only git/gh and file tools without prompts + the superpowers-chrome browser tool (full browser access is a ruling; prompts per click would defeat it). Since 2026-10-01 (R4): `Bash(bbs-fill *)` — the vetted form and quote scripts, through the `bbs-tools` launcher, which runs only allow-listed scripts (since 2026-10-16 that list includes the Business Central item-entry script; the rep's named sign-off on its review sheet is the gate, see "Business Central writes" below; since 2026-11-10 it includes the desk-memory writer, see "Desk memory notes" below); the read-only Grainger MCP and BC MCP Custom API tools; Outlook **draft** creation and editing. Since 2026-10-13 (Parker in session, with `agent-team`): the steward's session tools — `Agent` (subagents), and the cloud session tools `create_session`, `send_message`, `get_session`, `list_sessions`, `list_events`, `get_event`, `set_session_title`, `set_session_tags`, `subscribe_pr_activity`, `unsubscribe_pr_activity` under the `mcp__claude-code-remote__` prefix — so a `project-steward` session can launch child sessions, read their transcripts, and be woken by PR events without a prompt per step. An allow rule cannot be scoped to one skill, so these apply to every session on the machine; Rex's review of PR #63 flagged that and Parker ruled it stands (2026-10-13, `docs/STEWARD.md`): these tools cannot send, order, or write to a system of record. The irreversible or loop-capable ones went to `ask` instead: `interrupt_session`, `send_later` (it wraps `create_trigger`, so each firing could schedule the next), `list_triggers`, `delete_trigger` (deletes every session the routine started). `create_trigger` and `archive_session` stay on the default prompt. The prefix is the one observed in a claude.ai cloud session on 2026-10-13; confirm it in `/permissions` on a rep machine after the first paste, and fix it here if a desktop session names the server differently. Bare `Read` "matches all file reads" (permissions docs, *Match all uses of a tool*; checked 2026-10-02): Claude Code reads any file the person can open without a prompt, the synced MASTER library included, and also `~/.ssh`, browser profiles and other projects. Whether to narrow it is OPEN (`docs/STEWARD.md`, 2026-10-02). **Never** `Bash(python:*)` or a path-pattern rule: a `*` matches anything, so such a rule would let a crafted command run arbitrary Python past auto mode | Fewer prompts on the actions that cannot break anything, and auto mode no longer stops a rep mid-packet (Kim, 2026-10-01) |
| `permissions.ask` | Since 2026-10-13 the steward's interrupt, one-shot check-in and routine-delete session tools (see allow). Push, PR create (PR merge moved to `deny` 2026-11-10, R1), Vercel deploy; since 2026-11-11 Vercel purchases and domain transfers (`buy_*` and `create_or_transfer_domain` under the `mcp__claude_ai_Vercel__` and `mcp__Vercel__` prefixes, and `buy_domain` and `create_or_transfer_domain` under any prefix; R9 amendment, see "Vercel purchases ask first" below), and the eight Microsoft 365 sends under any prefix (see "Microsoft 365 sends" below); Shopify theme push; Outlook calendar event create/update/delete, which email invites, updates and cancellations to attendees (Parker, 2026-10-01); since 2026-10-02 the Outlook and Teams send-class tools (send, forward, meeting responses, inbox rules, auto-replies, the three Teams sends; also `ask` in the admin console), so Claude can send but every send waits for a person's Allow (Parker, 2026-10-02) | Plan → approve → execute is doctrine; this makes the tool enforce it |
| `permissions.deny` | `rm -rf`, force-push, hard reset, `gh repo delete`, reading `.env` files: `Read(**/.env)` and siblings cover the session folder and below, and since 2026-10-02 `Read(~/**/.env)` and siblings cover the whole home folder (Parker, ruling (c)); a `.env` outside both (elsewhere on `C:\` outside the home folder, or on another drive) is not covered | The irreversible actions and the secret files, plus the send-class tools that stay off: Outlook `send_draft` (its Allow prompt shows only a message id, not the email; Parker, 2026-10-02), SignNow invites and QuickBooks estimate/invoice/payment-link sends. Since 2026-11-10 (R1), the GitHub merge and auto-merge tools and `gh pr merge`: agents never merge, Parker clicks Merge in the GitHub UI (see "Agents never merge" below). Since 2026-10-02 (Parker, connector access; kept by R9, 2026-11-10): every QuickBooks `qbo_payroll_*` tool, for everyone, admins included. Since 2026-11-11, `mcp__*__` globs back up the payroll and send denies, because a connector's tool prefix differs by surface (see "Payroll and send denies: which names are verified" below). 68 deny entries in all. The Outlook and Teams sends are in `permissions.ask` (row above). Deny rules apply in auto mode too, before its classifier, and hold over users' mods. `Read(**/.env)` does not block `.env.example` |
| `env.CAVEMAN_DEFAULT_MODE=off` | Caveman stays off until a rep types `/caveman` | The plugin's own default is `full`; without this every rep session — including customer-email drafting — would start terse |
| `env.CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000` | Plugin and marketplace clones get ten minutes, not the 120 s default | A large plugin overran 120 s on a laptop whose antivirus scans every file. Moved here from the bootstrap's saved copy (2026-10-01) so it lives in one place; the bootstrap still sets it for its own install run |
| `env.CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=1` | A winget- or Homebrew-installed Claude Code updates itself | A native install ignores it. Moved from the Windows bootstrap's saved copy (2026-10-01) |
| `pluginConfigs` → `cc-plugin-sec-default@builtin` → `allowManagedModsOnly: true` | Only the organization's own mods load; a mod a user installs, loads with `--plugin-dir`, or Claude writes mid-session does not (Parker, 2026-10-02) | A user's mod can approve a call an `ask` rule would prompt for, so without this the per-send Allow could be skipped. Plugins' `hooks/hooks.json` hooks (ours) are not mods and keep running. A mod in a plugin from a GitHub marketplace counts as a user's and stops loading; as of 2026-10-02 none of ours or the pinned commons ship one (`impeccable` and `claudeforge` track moving branches, so recheck when they update) |
| `channelsEnabled: true` | Channels are allowed for the organization (managed-only key) | It was set in the console's live copy (v12) and missing here, so pasting this file would have turned channels off (Parker, 2026-10-02) |
| `disableBypassPermissionsMode` | Nobody can run `--dangerously-skip-permissions` | For a team that is not native with AI, the permission prompt is the seatbelt |
| `claudeMd` | Company memory injected into **every** session on every machine | The eleven rules that hold everywhere (the Business Central write boundary added 2026-11-10, R2; customer-folder CLAUDE.md upkeep, ask first, R6), the exact strings, the systems of record, and where the detail lives. Managed-settings-only field, so it cannot be overridden by a repo file. This is the fastest path to "the same answer Parker would give" |
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
SharePoint. A person who needs to write to one asks Parker, and Parker grants it to that
person. **Signing is not on that list**: who signs which line is R1 and R1a, recorded in
`plugins/bbs-sales/references/ca-form-rules.md`, "Delegated signatures", and no connector
grant changes it. QuickBooks payroll is blocked for everyone, admins included (managed
`permissions.deny` plus the console `blocked` control, `docs/ADMIN-RUNBOOK.md` §3). Vercel
and Supabase are not blocked: R9 (Parker, in session, 2026-11-10) took out the purchase,
project-deletion and billing denies the 2026-10-02 ruling had added. R9 amendment, Parker, 2026-11-11: Vercel purchases and domain transfers ask first; still allowed. Supabase
stays fully allowed. A person's own Outlook drafts and own calendar are not
shared spaces: drafts stay allowed, invites stay `ask`.

Of the connectors on Parker's account today:

| Connector | Read | Write to the shared space | Why |
|---|---|---|---|
| Business Central — BC MCP (Custom API) (read-only: `bc_customer_snapshot`, `bc_find_item`, …) | **Everyone** | None: the connector has no write tools | Quote of record, AR, open orders. **Interim** until Microsoft's official BC MCP works in Claude Code; tool names change at the swap (grep list in the v1.1 backlog), and the new tools must be re-checked for writes. BC Chat Connector retired 2026-09-13 |
| Grainger (`grainger_search` / `grainger_price` / `grainger_availability`) | **Everyone** | None: read tools only | Per-account pricing is doctrine; this is how it is read without the open web |
| ca-procurement-intel / SCPRS (`explore_sql`, `play_*`) | **Everyone** | By request | Competitive intelligence and buyer segments |
| Microsoft 365 (Outlook, SharePoint, Teams search) | **Everyone** | Own Outlook drafts: everyone. SharePoint writes: by request, through the person's SharePoint permissions | It signs in as the person (it reads their own mailbox), so SharePoint's own permissions decide who can write. Send, forward and Teams messages wait for a person's Allow on every send (`permissions.ask`); `send_draft` stays denied |
| BBS Sales CRM MCP | **Everyone** | By request | Pipeline of record (ruled 2026-09-13). It exposes `crm_update_record`; see "Enforcing write by request" |
| Supabase | **Everyone**, through a read-only connection | By request | The catalog is the source of truth; a mass UPDATE from a quote session is the failure mode. Creating a project or branch and restoring a paused project are not denied (R9); whether they prompt first is open with Parker |
| Shopify admin, Vercel, Firecrawl, Dataverse, Adobe | **Everyone** | By request | Storefront, site, crawl, data and design. Vercel purchases and domain transfers ask first; still allowed (R9 amendment, Parker, 2026-11-11). Project deletion is not denied (R9) |
| SignNow | **Everyone**, once Parker confirms its remaining tools cannot place a signature | **Not by request.** Who signs is R1 and R1a (`ca-form-rules.md`, "Delegated signatures"); the send and invite tools stay denied | Signing is a binding-document rule, not a shared-space write |
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

## Business Central writes: the review sheet is the gate (2026-10-16, superseding 2026-10-15)

Ruling (Parker, in session, 2026-10-16): `bc_item_entry.py`, the one script in the
marketplace that writes to Business Central (`bbs-sales` / `bc-item-entry`), is **on** the
`bbs-fill` `ALLOWED` list, so `check`, `commit`, `whoami` and `logout` run under
`Bash(bbs-fill *)` without an Allow prompt. Parker's words: "I do not want to have to
approve the line items. I just want the rep to have to review the planned entered text."
The gate is the skill's own: the check writes a review sheet showing every field BC will
receive, the rep reads it and approves it by name in the chat, and the commit carries that
name and the sheet's token. That named sign-off is also what the organization instructions
require for any Business Central write, and it is not removable here. The 2026-10-15
ruling that kept the script off the list, so that every run also waited for a click, is
superseded; its reasoning (a write to a system of record deserves a second control) was
answered by the sheet, not by the click. Taking the script back off the list is a reversal
and needs Parker, in a reviewed PR.

**Quote creation, and the line in company memory (2026-11-10, R2).** Parker, in session,
2026-11-10, adopting R2, then "Add bc quote entry to managed settings". `bc-quote-entry`
(#68) may create a sales quote, its ship-to and its lines in Business Central; it never
releases, sends, converts or posts, and it runs only after the rep approves the review
sheet by name. The `claudeMd` block now carries one rule naming the whole BC write
boundary (items, Vendor No. on items, sales quotes and their lines; the PM
Claude/BC-Write-API scripts and the `bc-item-entry` and `bc-quote-entry` skills; named
approval in the chat; never release, send, convert or post). Before this the company memory named no
BC write rule, only the systems-of-record line. Detail stays here, not in `claudeMd`:
`bc_quote_entry.py` **is** on the `bbs-fill` allow list under R3 (Parker, 2026-11-10), which
allowed it only once its check stops every NASPO line whose price is not exactly its cost.
That gate exists in #68 (`validate_spec`, tested in `test_bc_quote_entry.py`, `NaspoAtCost`);
removing or weakening it takes the script off the list in the same PR. Like `bc_item_entry.py`
above, its `check` writes a review sheet with every header field and line Business Central will
receive, and its `commit` carries the rep's name and the sheet's token. A proof read-back of the
quote printout stays mandatory (R5). The organization instruction in the claude.ai admin console is a separate place,
which also covers claude.ai chats, and needs the same `bc-quote-entry` edit by hand;
re-pasting this file does not change it.

## Payroll and send denies: which names are verified (2026-11-11)

A deny on a name that does not exist blocks nothing and reports nothing. The same
connector tool shows up under different prefixes on different surfaces: a claude.ai cloud
session named QuickBooks `mcp__Intuit_QuickBooks__` (Rex's review session, 2026-11-11),
another cloud session named it by a server id (`mcp__0af04a37-…__`, 2026-11-10), and
Claude Code on a desktop is documented to use `mcp__claude_ai_<server>__<tool>`. So
`permissions.deny` carries the named rules and a glob for each tool:

| Rule | Covers | Name status |
|---|---|---|
| 27 × `mcp__claude_ai_Intuit_QuickBooks__qbo_payroll_<tool>` | Claude Code fetching the QuickBooks connector itself (terminal, VS Code, Desktop Code tab) | **Tool parts verified**: all 27 match a cloud session's QuickBooks tool list, 2026-11-10. **Prefix inferred** from the documented `mcp__claude_ai_<server>__<tool>` form; not observed on a rep machine |
| `mcp__claude_ai_Intuit_QuickBooks__qbo_payroll_*` | The same, plus payroll tools Intuit adds later | Trailing-`*` form documented (`mcp__github__get_*`); prefix inferred as above |
| `mcp__Intuit_QuickBooks__qbo_payroll_*` | A claude.ai cloud session | **Verified** prefix: seen in a cloud session's tool list, 2026-11-11 |
| `mcp__*__qbo_payroll_*` | Any server, whatever its prefix, including a server id | Deny rules accept a glob in the tool-name position that must match the full name (permissions docs, *Tool name wildcards*, checked 2026-11-11). **Two `*` in one rule is not stated in the docs**, so the two single-`*` rules above stay as the documented cover |
| `mcp__claude_ai_Microsoft_365__outlook_send_draft`, the four `mcp__claude_ai_SignNow__…` sends, the four `mcp__claude_ai_Intuit_QuickBooks__qbo_sales_send_…` sends | Claude Code fetching the connector itself | **Inferred** prefix (documented form); tool parts verified for Outlook and QuickBooks in a cloud session's tool list, 2026-11-10. No SignNow connector was in that session |
| `mcp__*__outlook_send_draft`, `mcp__*__send_invite`, `mcp__*__send_invite_reminder`, `mcp__*__create_embedded_invite`, `mcp__*__create_embedded_sending`, `mcp__*__qbo_sales_send_estimate`, `mcp__*__qbo_sales_send_invoice`, `mcp__*__qbo_sales_send_invoice_reminder`, `mcp__*__qbo_sales_send_payment_link` | Any server | One `*`, the same documented shape as `mcp__*__merge_pull_request` below. The SignNow globs carry generic tool names, so they would also deny a same-named tool on another server; none is connected today |

None of these globs matches the eight Outlook and Teams sends that stay in
`permissions.ask` (`outlook_send_mail`, `outlook_forward_mail`, `outlook_respond_to_event`,
`outlook_create_filter`, `outlook_set_vacation` and the three Teams sends). A match check
against the cloud session's tool names, every `ask` entry and the `claude_ai` and
`Intuit_QuickBooks` forms of each tool found none (2026-11-11, PR #53). Deny beats ask, so a
glob that caught one would turn a send people may Allow into one nobody can make.

The payroll denies hold only where managed settings reach. The ADMIN-RUNBOOK §1 live-fire
runs a payroll read on Parker's machine **and** in a cloud session; both must be refused.

## Vercel purchases ask first (2026-11-11, R9 amendment)

R9 amendment, Parker, 2026-11-11: Vercel purchases and domain transfers ask first; still allowed. Parker, in session: "Yes, ask before Vercel purchases." The Vercel
connector's tool list in a claude.ai cloud session on 2026-11-11 had two tools that buy or
move something: `buy_domain` and `create_or_transfer_domain`. The 2026-10-02 list also
had `buy_addon`, `buy_credits`, `buy_credits_endpoint`, `buy_domains`, `buy_pro` and
`buy_single_domain`; they were not in the 2026-11-11 list, and the `buy_*` glob covers them
if they return. The reads (`get_purchase_quote`, `get_domain_price`, `get_order`) and
`accept_project_transfer_request` (a project, not a domain) are not included.
`permissions.ask` carries:

| Rule | Name status |
|---|---|
| `mcp__claude_ai_Vercel__buy_*`, `mcp__claude_ai_Vercel__create_or_transfer_domain` | **Inferred** prefix from the documented `mcp__claude_ai_<server>__<tool>` form; tool parts verified in a cloud session's list, 2026-11-11 |
| `mcp__Vercel__buy_*`, `mcp__Vercel__create_or_transfer_domain` | **Verified**: a claude.ai cloud session listed `mcp__Vercel__buy_domain` and `mcp__Vercel__create_or_transfer_domain`, 2026-11-11 |
| `mcp__*__buy_domain`, `mcp__*__create_or_transfer_domain` | Any prefix, including a server id (another cloud session listed Vercel as `mcp__274876ca-…__`, 2026-11-10). One `*`, the documented shape |

The `buy_*` globs are scoped to the Vercel server, never `mcp__*__buy_*`, which could
catch another connector's purchase tool. The two any-prefix rules name the exact tool, so
they reach only a tool of that name. No deny rule matches any of these names (deny would
win and turn a purchase into a refusal), and nothing matches a Supabase tool: Supabase stays
fully allowed. Set the same two tools to `ask` in the admin console too (ADMIN-RUNBOOK §3).

## Microsoft 365 sends: ask on every prefix (2026-11-11)

The eight Outlook and Teams send tools in `permissions.ask` were named under
`mcp__claude_ai_Microsoft_365__` only, so a session that named the server differently got
no prompt. A cloud session listed them as `mcp__Microsoft_365__…` on 2026-11-11 and as a
server id on 2026-11-10. `permissions.ask` now also carries one-`*` rules for the same eight
tools: `mcp__*__outlook_send_mail`, `mcp__*__outlook_forward_mail`,
`mcp__*__outlook_respond_to_event`, `mcp__*__outlook_create_filter`,
`mcp__*__outlook_set_vacation`, `mcp__*__teams_send_chat_message`,
`mcp__*__teams_send_channel_message` and `mcp__*__teams_reply_channel_message`. Each names
one exact tool and catches nothing else, and no deny rule catches any of them
(match check, PR #53, 2026-11-11). 33 ask entries in all.

## Agents never merge (2026-11-10, R1)

Ruling (Parker, in session, 2026-11-10, adopting the steward's R1; `docs/STEWARD.md`,
*Already open for Parker*): agents never merge a pull request. Rex reviews and posts
"Cleared — awaiting Parker's merge approval"; Parker clicks Merge in the GitHub UI. Every
agent posts as Parker's own GitHub account, so no agent can prove Parker approved a merge,
and a sentence in an agent file is a request, not a control. So `permissions.deny` carries:

| Rule | Covers | Name status |
|---|---|---|
| `mcp__github__merge_pull_request`, `mcp__github__enable_pr_auto_merge` | The GitHub MCP server as a claude.ai cloud session names it | **Verified**: both appear under these names in a cloud session's tool list, 2026-11-10 |
| `mcp__claude_ai_GitHub__merge_pull_request`, `mcp__claude_ai_GitHub__enable_pr_auto_merge` | A claude.ai GitHub connector that Claude Code fetches itself (terminal, VS Code) | **Inferred** from the documented `mcp__claude_ai_<server>__<tool>` form and the connector's display name "GitHub"; not observed on a rep machine |
| `mcp__plugin_github_github__merge_pull_request`, `mcp__plugin_github_github__enable_pr_auto_merge` | A `github` plugin bundling a server keyed `github` | **Inferred** from the documented `mcp__plugin_<plugin>_<server>__<tool>` form; no BBS machine is known to have such a plugin |
| `mcp__*__merge_pull_request`, `mcp__*__enable_pr_auto_merge` | Any server, whatever its prefix | Documented: deny rules accept a glob in the tool-name position that must match the full name (permissions docs, *Tool name wildcards*, checked 2026-11-10). This is the catch-all for a prefix guessed wrong above |
| `Bash(gh pr merge:*)` | The `gh` CLI, including `gh pr merge --auto` | Moved from `ask` to `deny`: an `ask` would let an agent put a merge in front of Parker as one more Allow click |

A deny on a name that does not exist is a silent no-op, which is why the glob is there.
After the re-paste, confirm in `/permissions` on Parker's machine that the GitHub tools
are listed as denied, and in one cloud session that asking Claude to merge a test PR is
refused rather than prompted.

**What it does not cover.** `gh api` (a `PUT .../pulls/<n>/merge` call), `git push` to
`main`, and any GitHub tool on a surface managed settings do not reach (the Desktop
**chat** window and Cowork; see "What is deliberately not here"). `git push` stays in
`ask`; branch protection on `main` (a required PR and the `invariants` check) is the
control there. Nor does it cover the GitHub MCP tools that write commits straight to a
branch: `push_files`, `create_or_update_file`, and `update_pull_request_branch`. Pointed at
`main`, those are stopped only by branch protection on `main` with admin bypass **off**
(agents act as Parker's own account, an admin, so with bypass on they would pass); that
setting is the backstop for every path in this paragraph. Taking a PR out of draft (`gh pr ready`, `update_pull_request`) is not a
merge and is not denied here; `AGENTS.md` and the agent files still forbid it.

**Where it reaches.** Server-managed settings from the admin console reach Anthropic-hosted
cloud sessions (web, mobile, and cloud sessions started from Desktop), except Claude Tag
sessions; a device-deployed `managed-settings.json` does not reach them (*settings*,
"Settings in cloud sessions"; *model-config*, "Surface coverage"; checked 2026-11-10).
Nothing reaches any machine until Parker re-pastes this file in the admin console.

## Desk memory notes: no Allow click to save one (2026-11-10, R7 A3)

Ruling (Parker, in session, 2026-11-10, R7, A3 as recommended): `desk_memory.py`
(`bbs-sales` / `desk-remember`) is **on** the `bbs-fill` `ALLOWED` list, so `where`, `add`,
`show`, `retire` and `merge` run under `Bash(bbs-fill *)` without an Allow prompt. Before
this a rep saw one permission prompt per note, which is the step that keeps a
non-technical team from saying "remember that" at all. What the script can do bounds the
risk: it writes one dated, attributed line into a `LEARNED.md` inside the rep's own
quote-desk folder (or moves one line to `LEARNED-archive.md`, or folds a OneDrive conflict
copy back in); it refuses prices, discounts, markups, stock and lead times, contact details,
certification and preference claims, account and contract numbers, credentials, and anything
that reads as an approval or an instruction to skip a review, from one table the hooks also
apply on read; it refuses agency- and desk-level notes, which are Parker's (R7, A2); and it
cannot send, price, sign or write to a system of record. Running it through `bbs-fill` also
picks `python` on Windows and `python3` on a Mac, which the skill's bare `python3` line did not.
Taking the script back off the list is a reversal and needs Parker, in a reviewed PR.

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
  doctrine, `bbs-foundations` also reminds a session in a customer folder to offer to create or fix
  that customer's `CLAUDE.md` (asks first, R6), outside the CA quote desk, `bbs-sales` guards the quote-desk tree); `bbs-website` ships one template
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
