# Plugins in this marketplace

- **bbs-ops** (live) — site-maintenance pipeline. `plugins/bbs-ops`.
  Note: its `ca-form-filler` and `obs-form-filler` skills cover the same CA state
  compliance forms as `bbs-sales/naspo-quote`. That overlap should eventually
  consolidate into `bbs-sales`, where the quoting workflow lives — a form field map
  maintained in two places will drift, and whichever copy a rep loads first wins.
  Both stay in place for now; don't move them until the sales plugin has run real
  packets and the field maps are confirmed to match.
- **bbs-sales** (live) — inbound CA state quote desk: the intake SOP that files a
  request into the customer folder tree, plus the NASPO pricing and cert-packet
  workflow. `plugins/bbs-sales`.
- **bbs-foundations** (live, first release) — company-wide AI fundamentals. Ships
  `bbs-claude-md-forge` (BBSClaudeMDForge): the BBS way to write, audit, and repair
  CLAUDE.md files, with a deterministic checker and the canonical facts every repo must
  agree on. `plugins/bbs-foundations`. Spec:
  `docs/superpowers/specs/2026-09-02-bbs-foundations-claude-md-forge-design.md`.
  `bbs-grounding-doctrine` now lives here (its `bbs-ops` copy stays under a "migrates"
  note until the two `bbs-ops` subscriptions are repointed — plan task 9).
  Still planned, each its own spec: the MCP connector roster (ca-procurement-intel,
  Grainger, BBS KIt, Microsoft 365, Shopify, Supabase) with a degrade-gracefully contract,
  and AI-literacy onboarding.
- **claudeforge** (pinned external) — the generic CLAUDE.md engine `bbs-foundations`
  depends on, pinned to the BBS fork `Black-Box-Safety/ClaudeForge` at `dev` so it updates
  through git and never gets hand-copied. Install it for `/sync-claude-md` and the
  link/drift audits; `bbs-claude-md-forge` works without it.
