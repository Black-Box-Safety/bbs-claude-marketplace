# Consolidated findings — all investigations, 2026-09-11

One page unifying the seven investigations run during the rep-workspace design session
(home desktop). Detail lives in the companion docs; this is the unified view.

| # | Investigation | Full report |
|---|---|---|
| 1 | Local Claude config audit (this machine) | summarized here only |
| 2 | Local repo survey (staleness, remotes) | summarized here only |
| 3 | Org/personal GitHub repo survey (9 repos) | summarized here only |
| 4 | Past-session memory search (Jun–Sep 2026) | summarized here only |
| 5 | Folder-migration debrief | `2026-09-11-folder-migration-debrief.md` |
| 6 | Business Central assessment (live tenant) | `2026-09-11-bc-assessment.md` |
| 7 | External research: SMB AI ops + Claude Code team practices | `2026-09-11-research-briefs.md` |

## 1. Local config audit (Parker's home machine)

- **Two leaked keys found:** Firecrawl API key baked into ~20 permission-allowlist entries
  in `~/.claude/settings.local.json`; Grainger gateway key in plaintext in
  `~/.claude/remote-settings.json` (stale macOS-path entry). **Rotate both.**
- Allowlist has 116 entries incl. `Bash(bash *)` (arbitrary execution) and auto-approved
  `apply_migration` / `execute_sql` / `graphql_mutation` — contradicts the
  plan→approve→execute doctrine. Rebuild from scratch; never copy to a rep machine.
- 27 plugins enabled, 21 developer-oriented; 11 marketplaces registered (8 personal GitHub
  repos, 3 with nothing enabled); caveman plugin owns the statusline. A rep needs ~5% of
  this. 3 of 8 global skills are the business assets (bbs-sourcing, ca/obs-form-filler).
- No managed policy exists on any machine; nothing is centrally enforced today.

## 2. Local repo survey

- `bbs-claude-marketplace` was **22 commits behind** origin (now pulled — the three-plugin
  architecture + managed-settings design existed remotely, invisible locally).
- `bbs-quote-bot` is 10 commits ahead of a remote on the **personal** account (pjm3wv),
  not the org. bbs-database/bbs-shopify slightly behind with small uncommitted work.
- No `.mcp.json` anywhere — MCP/connector config is all user-level or claude.ai-side.
- OneDrive `claude-inside-sales-skills/` still holds the June skill bundles — the original
  drift source; delete after marketplace rollout.

## 3. GitHub repo survey (rep-infrastructure attempts, ranked)

- **Tier 1 (deploy from):** `bbs-claude-marketplace` (3 plugins, managed settings,
  actively maintained), `bbs-naspo-quote` (deepest asset: 438 mined PDFs, tested
  form-filler; vendored copy in marketplace must be reconciled), `ca-quote-hub` (best
  CLAUDE.md grounding + rep-ready .code-workspace to harvest; Supabase pipeline parked).
- **Tier 3 (superseded):** `bbs-sales-vault` (workflow depends on a never-written ICM
  stage folder; harvest the tree map, archive), `BBS-ICM-Sales` (unmodified public fork),
  `bbs-agent` (one-commit campaign tool, campaign over).
- `bbs-bc-mcp-proxy` **retired** — replaced by the BC MCP (Custom API) connector.
- `bbs-rfq-automation` (Power Platform) is a live **parallel** effort targeting a Dataverse
  rep app — formally parked as rep destination by the rollout design; invariants retained.
- `bbs-customer-bots` (Gear Assistant, 12 agency tenants) — separate customer-facing
  track; `new-agency-tenant` skill becomes rep-deployable in tiers (v1 request path,
  v1.1 rep-mode PR flow).

## 4. Past-session memory (Jun–Sep 2026)

- Recurring problems across all attempts: bus factor, skill/fact drift across machines and
  14 repos, money safety (at-cost NASPO), compliance-packet risk, intake discipline,
  approval gates, rep-machine plumbing (BC OAuth).
- The bbs-ops handoff (Jul 23) stalled at install (fixed Aug 13); the acceptance test
  result was **never recorded**; source-repo cutover unconfirmed. Managed settings
  (Sep 2) designed, **never pushed**. Pattern: designs finish, deployments stall.
- Two different `ca-rfq-intake` skills exist (ca-quote-hub Supabase version vs marketplace
  folder version) — same name, silent collision.

## 5. Folder-migration debrief (see full doc)

- Migration to `All RFQ's by Agency/…` happened Aug 11–27 on another machine. Convention
  documented; rejected conventions recorded.
- Nine live landmines — duplicate buyer folders (most expensive intake error), the
  `CalTrans` / `Cal Trans (ALL)` duplicate pair, CDCR "copy" trees, **load-bearing
  folder-name typos carrying Grainger account numbers (never rename)**, buyer notes
  overriding folder-name accounts, truncated names, unknown `_Unfiled/` state.
- Naming tension needing a ruling: skill says item-first deal folders; reps use date-first.
- Harvest correction: `agency-tree.md` (8/27) supersedes stale `document-store-map.md` (8/11).

## 6. Business Central assessment (see full doc)

- BC is heavily used (≈10 quotes/day, ≈45–70 orders/day, real purchasing) — better than
  typical 9-person shops. Three open loops: **Claude 9000xx quotes never enter BC**
  (re-typed on win, invisible to precedent search); **quote lifecycle fields unused** (no
  win rate); **dimensions scaffolded 18 months ago, apparently never populated** (NASPO
  at-cost not separable from margin; no rebate audit denominator).
- Shopify cash-application gap: aged "unpaid" invoices were card-paid; real overdue
  government AR is only ~$11k. `bc_list_unpaid_invoices` currently cries wolf.
- Low-hanging fruit adopted into the spec (v1.1/later); firm don't-do list: no AL
  extensions, no ISV add-ons, no Premium, no item renumbering, no catalog sync into BC.

## 7. External research (see full doc)

- **SMB ops:** MIT ~95%-of-pilots-fail finding pins failure on measurement/adoption, not
  models. Adopted: baseline-now, golden-case eval set (FAR 14.407 makes bid pricing errors
  binding), blameless "AI was wrong" log, one-page AUP (shadow-AI antidote), you-as-canary
  change discipline, automate-labor-not-decisions line.
- **Claude Code product:** server-managed settings (hourly refresh, no MDM), hooks as
  *enforced* guardrails vs advisory CLAUDE.md, `strictKnownMarketplaces` /
  `strictPluginOnlyCustomization` / `forceLoginMethod` lockdowns, Routines (scheduled
  cloud agents — the nightly audit needs no server), Team analytics dashboard + spend
  report (free measurement), eval-first skill methodology (no built-in runner — build a
  small harness), marketplace `version`-field semantics (omit for auto-update), Anthropic
  Academy free courses, Cowork as the non-dev desktop surface.

## Cross-cutting conclusions (what the design acted on)

1. **Design was never the bottleneck; deployment and enforcement were.** Managed settings
   push + marketplace auto-update + lockdown keys make consistency structural.
2. **The best assets were invisible or duplicated** (22-commits-behind marketplace, two
   intake skills, three parker-voice copies) → REGISTRY.md + single-source pointer rule.
3. **The compliance/money path needs a regression net** (golden evals + 100% human review
   of numbers + guardrail hook blocking outbound sends).
4. **Measurement is nearly free** (BC data + analytics dashboard + 3-hour baseline) and is
   what proves the program's value.
5. **The folder tree is trustworthy only with its landmines attached** — they ship in the
   desk CLAUDE.md verbatim.
