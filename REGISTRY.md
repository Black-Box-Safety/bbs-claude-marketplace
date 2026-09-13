# BBS asset registry

Every BBS repo and AI asset has exactly one status and one home. Update this file in the
same PR/commit as any status change. Statuses: **canon** (build here), **harvest** (take
named value, then archive), **parked** (deliberate pause, revisit condition named),
**archived** (done, read-only), **separate track** (alive, not this program). "archived"
records the ruling; the GitHub click itself is tracked in docs/ADMIN-CLEANUP.md until done.

Last verified: 2026-09-11 (rep-workspace design session).

| Asset | Status | Ruling / where the value went |
|---|---|---|
| `bbs-claude-marketplace` | **canon** | The brain. Plugins, managed settings, specs, this registry |
| `bbs-naspo-quote` (repo) | **canon** | Source repo; cutover pending — Marketplace `bbs-sales/naspo-quote` becomes canonical; repo keeps precedent-mining scripts + gets pointer README |
| `ca-quote-hub` | **harvest** | `.code-workspace` + CLAUDE.md grounding → `workspace/`; Supabase `rep_cockpit` **parked** (revisit if folder tracking misses deadlines); its duplicate `ca-rfq-intake` skill: delete |
| `bbs-sales-vault` | **harvest** | SharePoint tree map superseded by `plugins/bbs-sales/skills/ca-rfq-intake/references/agency-tree.md` (8/27); README tone reused in REP-SETUP; then archive the repo. |
| `parker-voice` (repo) | **harvest** | Consolidate: Worked example inside `plugins/bbs-foundations/skills/bbs-voice-template`; other copies (bbs-customer-bots/docs) get pointers |
| `bbs-bc-mcp-proxy` | **archived** | Retired 2026-09-02, replaced by BC MCP (Custom API) claude.ai connector; archive once nothing references the Vercel endpoint |
| `bbs-customer-bots` | **separate track** | Customer-facing Gear Assistant; `new-agency-tenant` gains rep mode in v1.1 (PR flow) |
| `bbs-rfq-automation` | **parked** | Dataverse app is not the rep destination; ruled invariants live in doctrine |
| `bbs-agent` | **archived** | FY2026 campaign over; one commit |
| `BBS-ICM-Sales` | **archived** | Unmodified public fork; idea absorbed |
| BC MCP (Custom API) connector | **canon** | Interim Business Central access until Microsoft's official BC MCP is usable in Claude Code; swap list in `docs/superpowers/plans/2026-09-13-v1.1-backlog.md` |
| BC Chat Connector | **archived** | Retired 2026-09-13; redundant with BC MCP (Custom API). Remove from admin-console assignments |
| BBS Sales CRM MCP connector | **canon** | Assigned to everyone (ruled 2026-09-13); pipeline of record |
| `bbs-suppliers` | **canon** | Data plane. Supplier leverage layer; v1.1: wire briefs into `bbs-sourcing` references (pointer, not copy) |
| OneDrive `claude-inside-sales-skills/` | **archived** | Delete: Original drift source; superseded by marketplace install |
| `bbs-shopify`, `bbs-database`, `bbs-quote-bot` | **separate track** | Site/catalog ops (bbs-website plugin's world) |

## Standing tasks

| Task | Cadence | Owner |
|---|---|---|
| Quarterly security hygiene: rotate keys, skim permission files, prune marketplaces | Quarterly, 30 min | Parker |
| Registry re-verify (statuses still true?) | Quarterly, with the above | Parker |
| Flag-log triage → skill fixes | Monthly | Parker |
| Metrics review (4 inbound + 4 outbound) | Monthly, 30 min | Parker |
