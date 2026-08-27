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
- **bbs-foundations** (planned, separate spec) — company-wide AI fundamentals: MCP connectors
  (ca-procurement-intel, Grainger, BBS KIt, Microsoft 365, Shopify, Supabase), shared company
  knowledge, and AI-literacy onboarding. When built, append another entry to
  `marketplace.json` with `"source": "./plugins/bbs-foundations"`.
