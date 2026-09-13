# Admin machine cleanup — one-time checklist (home + work desktops)

Findings from the 2026-09-11 audit (docs/assessments/2026-09-11-consolidated-findings.md).
Execute deliberately, one block at a time. Nothing here touches rep machines.

## Secrets (do first, both machines)

- [ ] Rotate Firecrawl API key; update `~/.claude.json` mcpServers env with the new one
- [ ] Rotate Grainger gateway key; new value only in `~/grainger-api/mcp/.env` (admin machines
      only — reps use the Grainger claude.ai connector)
- [ ] Remove the stale local `businesscentral` MCP server entry from `~/.claude.json` (fails
      with "MCP Configuration not found"; superseded by the BC MCP connector)
- [ ] Admin console: unassign the retired BC Chat Connector from everyone
- [ ] Delete `~/.claude/remote-settings.json` stale `bbs-grainger` entry (macOS path + old key)
- [ ] Rebuild `~/.claude/settings.local.json` from empty: remove all 116 entries (they
      include the old Firecrawl key ~20 times, `Bash(bash *)`, and auto-approved
      apply_migration/execute_sql/graphql_mutation). Re-approve prompts as they recur —
      a week of prompts beats a standing contradiction of your own guardrails
- [ ] Delete `~/.claude.json.backup` (51 KB, stale, may hold old keys)

## Marketplaces (11 → keep 5)

- [ ] Keep: claude-plugins-official, bbs-claude-marketplace (register it here — this
      machine never had it), superpowers-marketplace, skill-bus-marketplace (if the
      doctrine-injection stays in use), caveman (ruled in 2026-09-13; becomes a
      `bbs-commons` pin in v1.1, then this direct registration goes)
- [ ] Remove: ecc, n8n-mcp-skills, alation-plugins (already disabled), ui-ux-pro-max-skill,
      impeccable (external — comes via bbs marketplace pin), humanizer, buildwithclaude
- [ ] `bbs-shopify/.claude/settings.json` registers a 12th (secondsky/claude-skills) —
      review, likely remove

## Plugins and skills

- [ ] Caveman: keep (ruled 2026-09-13) — but remove its statusline from settings.json
      before any config is copied anywhere, and delete the stray `.caveman-active.*` /
      `.caveman-mode-log.jsonl` home-dir files
- [ ] Global skills: bbs-sourcing / ca-form-filler / obs-form-filler → replace with 3-line
      pointers to the marketplace copies (single-source rule; do AFTER the marketplace
      install is verified on this machine)
- [ ] Delete OneDrive `claude-inside-sales-skills/` (drift source; superseded)

## Repos

- [ ] Push or reconcile `bbs-quote-bot` (10 commits ahead, remote is personal acct — move
      remote to Black-Box-Safety org or document why not)
- [ ] Commit or discard: bbs-database untracked migration 017; bbs-shopify modified manifests
- [ ] Archive on GitHub: bbs-agent, BBS-ICM-Sales, bbs-sales-vault (after tree-map harvest
      confirmed unneeded — REGISTRY says superseded), bbs-bc-mcp-proxy (after reference check)
