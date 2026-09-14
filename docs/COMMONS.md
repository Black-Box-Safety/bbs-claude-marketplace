# Commons — curated third-party plugins

**What it is.** Generally applicable skills and plugins, made by other people, that a BBS rep is
likely to find genuinely useful. Nothing BBS-specific lives here; that belongs in `bbs-sales`
or `bbs-foundations`. Ruled 2026-09-13.

**The bar.** Quality first, tokens second: a plugin gets in if it works out of the box, is
maintained upstream, and matches a task reps actually do. Context cost is a tiebreaker, not a
veto. Anything that needs a per-machine API key stays out.

**How it ships.** Each item is a pinned external entry in `.claude-plugin/marketplace.json`
under `category: "commons"`, enabled for everyone through managed settings. Pins are release
tags where the upstream cuts them, a commit SHA otherwise. Nothing is copied into this repo.

## Current roster

| Plugin | Pin | Why reps have it | Watch for |
|---|---|---|---|
| `superpowers-chrome` | `v3.0.5` | Drives the rep's own Chrome: product research on distributor and agency sites, logged-in sessions included. Full browser access is a standing ruling; no deny rules touch it | Upstream says beta. Needs Node.js (bootstrap installs it). If a rep hits a crash, log it in FLAGS |
| `caveman` | `v2.6.0` | Opt-in terse mode. Cuts output tokens roughly two-thirds; technical content stays exact. `/caveman lite` is a good default for long sessions | Off by default via managed env (`CAVEMAN_DEFAULT_MODE=off`); never forced on |
| `document-skills` (Anthropic) | commit `34040c9c` | Word, PDF, Excel handling with real scripts: fill and merge PDFs, read tracked changes, build spreadsheets with formulas. RFQ worksheets and bid packets are exactly this | `pptx` excluded on purpose. Skills carry Python scripts; `uv` from the bootstrap covers the runtime |

## Considered, not included (yet)

| Candidate | Reason |
|---|---|
| humanizer / avoid-ai-writing | Already inside `bbs-voice-template` (35 patterns vendored from blader/humanizer) |
| superpowers (full) | Developer workflow; its session hook injects a large mandatory block. Parker-only |
| Playwright MCP | Isolated browser, no logins, ~25 tool schemas per session |
| `pptx`, `internal-comms` | Bundled with unrelated skills or rarely needed; add on request |
| meeting-insights-analyzer, sanitize, csv-data-summarizer | Community skills; useful, unreviewed. Brainstorm after the pilot |
| claude-persona | Marketing tier, burns seat limits; admin only |

## Refresh

Quarterly, with key rotation: check each upstream for a newer tag, read its changelog, bump the
pin, run `claude plugin validate . --strict`, push. If an upstream goes quiet for two quarters,
decide: fork under Black-Box-Safety or drop.

## Propose an addition

One line in the Teams sales channel: what it does, the task it would replace, a link. Parker
tries it a week on live work first. Same bar as above.

*Maintainer: Parker Marshall · Last verified: 2026-09-13*
