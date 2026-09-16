# Commons — the curated third-party toolbox

**What it is.** Generally applicable skills and plugins, made by other people, that a BBS
rep is likely to find genuinely useful. Nothing BBS-specific lives here; that belongs in
`bbs-sales` or `bbs-foundations`. Ruled 2026-09-13.

**The bar.** Quality first, tokens second: a plugin gets in if it works out of the box, is
maintained upstream, and matches a task reps actually do. Context cost is a tiebreaker, not
a veto. Anything that needs a per-machine API key stays out.

**How it ships.** Each item is a pinned external entry in `.claude-plugin/marketplace.json`
under `category: "commons"`, enabled for everyone through managed settings. Nothing is
copied into this repo. Where an upstream ships more than reps should receive, the entry
narrows it with a `skills:` filter rather than taking the whole tree.

**Who keeps it true.** `.claude/agents/commons-curator.md`. One agent for one durable
domain, across the whole lifecycle.

---

## The lifecycle

```
evaluate → pin → validate → refresh (on cadence) → retire
```

**Evaluate.** Three hard filters: API key, license, rep-appropriateness. An independent
upstream has to exist — see the `awesome-claude-skills` entry below for why that is not a
formality.

**Pin.** A pin is a fact from a system of record. It is read off the upstream or it is not
written. All three current upstreams tag **annotated**, so the recorded SHA must be the
**peeled commit** (`git rev-list -n1 <tag>`), not the tag object (`git rev-parse <tag>`).
The tag object exists, looks plausible, and is not the code.

**Validate.** `python3 scripts/check_marketplace.py` and, where available,
`claude plugin validate . --strict`.

**Refresh.** On the entry's own cadence, not the calendar's. What gets diffed is what reps
receive: the plugin manifest (**especially `hooks`**), the `skills:` paths the entry
selects together with the skill and command **counts**, and `LICENSE*` / `LICENSING.md`.
The three hard filters are re-applied every refresh, not grandfathered from intake.

**Retire.** The liveness clock is the **last commit on the default branch**, not the last
release — a repo can go six months without a tag and be under daily development. Two
cadence periods of silence raises fork-or-drop. The curator raises it; Parker decides it.

### Release model drives cadence

| Release model | Cadence | Why |
|---|---|---|
| `rolling` (no tags) | monthly | There is no tag to wait for; the signal is commit date. "Check for a newer tag" returns clean forever |
| `tagged` (one train) | quarterly | |
| `multi-train` (interleaved prefixes) | monthly | A release you want can sit between four you must not take, and the trains move at different speeds |

A `tagged` upstream that in practice ships faster than quarterly is treated as
`multi-train`. Evidence: `caveman` shipped `v2.7.0` on 2026-09-14 — **ten days** after the `v2.6.0`
release the pin was taken from, and **one day** after the ruling was last verified.

---

## Current roster

| Plugin | Pin | Release model · cadence | Why reps have it | Watch for |
|---|---|---|---|---|
| `superpowers-chrome` | `v3.0.5` | `tagged`, single `vX.Y.Z` train · quarterly | Drives the rep's own Chrome: product research on distributor and agency sites, logged-in sessions included. Full browser access is a standing ruling; no deny rules touch it | Upstream says beta. Needs Node.js (`bbs-setup.ps1` installs it). If a rep hits a crash, log it in FLAGS |
| `caveman` | `v2.7.0` | `multi-train`, **nine** tag prefixes, authoritative train is bare `vX.Y.Z` · monthly | Opt-in terse mode. Cuts output tokens roughly two-thirds; technical content stays exact. `/caveman lite` is a good default for long sessions | Off by default via managed env (`CAVEMAN_DEFAULT_MODE=off`); never forced on. The entry is narrowed to 2 of the 20 skills in the tree — re-check the count each refresh. Split license, see below |
| `document-skills` (Anthropic) | commit `34040c9c` | `rolling`, **zero tags** · monthly | Word, PDF, Excel and PowerPoint with real scripts: fill and merge PDFs, read tracked changes, build spreadsheets with formulas, assemble decks. RFQ worksheets and bid packets are exactly this | **`pptx` visual QA and PDF conversion go through LibreOffice (`soffice`), which `bbs-setup.ps1` does not install, and behaviour on a rep's Windows box is unverified.** `docx` and `xlsx` reference `soffice` too and have the same gap. `pptx` also assumes `pptxgenjs` is preinstalled; on a rep machine it is an `npm install`. Skills carry Python scripts; `uv` from the bootstrap covers that runtime, and Poppler covers `pdftoppm` |

### Provenance

Every pin, with how it was established. Method for all three: `git ls-remote` / `git clone`
through the agent proxy. **The GitHub MCP cannot see third-party repos here and
`api.github.com` returns 403 over the proxy — an access error is not evidence a repo is
missing.**

| Entry | Verified | Tag object | Peeled commit | Upstream date |
|---|---|---|---|---|
| `superpowers-chrome` `v3.0.5` | 2026-09-16, agent | `9048f78163ff3c1f1300a856b8890ab02c92d9f0` | `782358eb8d3b99e3cc1321354b9233f660fdac7a` | 2026-08-07 — newest tag *and* branch tip |
| `caveman` `v2.7.0` | 2026-09-16, agent | `e6c5e68b0064758b8106b83df41cf3829dde3216` | `8b0c1d3699b8d83e87fe4605b378da20c41555e0` | 2026-09-14 |
| `document-skills` `34040c9c` | 2026-09-16, agent | — (no tags in repo) | `34040c9c568585f6929bedeaad110ad08f079624` | 2026-09-10 — is exactly current HEAD |

### Why `caveman` moved to v2.7.0

Not because it is newer. v2.7.0 rewrites both hook commands to prepend

```
HOOK_ROOT=$(printf %s "${CLAUDE_PLUGIN_ROOT}" | sed 's|^/\([a-zA-Z]\)/|\1:/|')
```

which converts an MSYS/Git-Bash `/c/...` path back into `C:/...` before invoking `node`.
v2.6.0 invokes `node` against the unconverted path. **BBS reps are on Windows** and their
Bash tool runs through Git Bash, which is why `bbs-setup.ps1` installs `Git.Git`. This is a
fix for our platform.

### The `caveman` license split

Recorded here, not changed — this was already true at v2.6.0 and went unrecorded at intake.
`LICENSING.md` puts `engine/`, `proxy/`, `rewriter/`, `browse/`, `mcp/` and `shrink/` under
**BSL-1.1** (also the `mem/` Go core and `shared/platform/`); `skills/` and the SDK, CLI and
contract packages stay **MIT**.

The BSL Additional Use Grant permits internal evaluation, local development, CI, and
self-hosted use for your own first-party traffic including production. **BBS reps running
caveman locally are inside that grant.** The boundary it draws is offering the licensed work
to third parties as a hosted, managed or embedded service — which BBS does not do. BSL
versions convert to Apache-2.0 on the earlier of 2030-06-21 or four years from that
version's first BSL distribution.

The reason this matters beyond bookkeeping: `proxy/` is a hosted, token-gated lane that grew
between quarterly checks. That is why the API-key and license filters are re-applied at every
refresh instead of being treated as settled at intake.

---

## Considered, not included

| Candidate | Reason |
|---|---|
| humanizer / avoid-ai-writing | Already inside `bbs-voice-template` (35 patterns vendored from blader/humanizer) |
| superpowers (full) | Developer workflow; its session hook injects a large mandatory block. **Parker-only.** Ruling re-verified 2026-09-16: at `v6.3.0` the `SessionStart` hook is declared in `hooks/hooks.json` and **not** in `plugin.json`, so a check of the manifest alone would wrongly report it gone |
| `brainstorming` | Ships inside the same `superpowers` tree, so it inherits that hook and that ruling. Parker-only, confirmed still correct |
| Playwright MCP | Isolated browser, no logins, ~25 tool schemas per session |
| `internal-comms` | Free to add and correctly licensed, but it teaches **Anthropic's** internal comms formats, not BBS's. If the need is real it belongs in `bbs-foundations` carrying BBS formats, not pinned from outside |
| `csv-data-summarizer` | Upstream `coffeefuelbump/csv-data-summarizer-claude-skill`, HEAD `9b3affd270f85aaf1c8a7a457f510034d5736cde`, **last commit 2025-10-16 — eleven months stale.** Fails the maintenance bar, and `xlsx` already covers the need |
| `postgres` | Reps do not write SQL, the Supabase MCP is already configured for the catalog work, and the host repo is 24 skills of which roughly 9 are Google-stack — BBS is Microsoft 365 |
| `kaizen` | Developer-aimed by its own frontmatter, and 204 `SKILL.md` files is a selection surface, not a toolbox |
| `meeting-insights-analyzer` | No independent upstream — it is a directory inside an aggregator list. Pin unverified, and there is nothing maintained to pin |
| claude-persona | Marketing tier, burns seat limits; admin only |
| `google-workspace-skills` | BBS is Microsoft 365 |

### `ComposioHQ/awesome-claude-skills` — evaluated in full, zero additions

Parker supplied it. HEAD `be2a406907dbc61b73e6827ded415c96139d13a2`, last commit 2026-07-24.
It yielded **nothing installable**, and the reason is structural rather than about taste, so
it is written down here to save the next evaluation.

- **Its headline entries are directories vendored into the awesome-list repo itself** —
  `./meeting-insights-analyzer/`, `./invoice-organizer/`, `./lead-research-assistant/` and
  roughly eleven more. The only pinnable upstream is therefore a marketing aggregator that
  did not write the code and does not maintain it. Pinning that violates "pin the real
  home or pin neither."
- **It also vendors stale copies** of `brand-guidelines`, `canvas-design`, `mcp-builder`,
  `skill-creator`, `theme-factory` and `document-skills` — every one of which has a real,
  maintained home in `anthropics/skills`, which this marketplace already pins.
- **The rest fail a hard filter**: API key (`connect` / Composio's own funnel,
  `deep-research`, `imagen`, `jules`, `langsmith-fetch`), Google or otherwise wrong stack,
  or developer-aimed.

An aggregator list is a candidate source, not an install path. **Its install guidance is a
user-level copy into a personal skills directory. Do not follow it** — that is exactly the
pattern that produced this company's shadowed personal skills, where the maintained
marketplace copy loses to a stale local one.

---

## Refresh procedure

Run by `commons-curator`, per entry, on that entry's cadence.

```bash
# 1. newest release on the authoritative train — filter to the train, then sort -V
git ls-remote --tags --refs <url> | sed 's|.*refs/tags/||' \
  | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1

# 2. peel it. rev-parse gives the tag object; rev-list -n1 gives the code
git rev-list -n1 <tag>

# 3. liveness: last commit on the default branch, not the last release
git log -1 --format=%cI origin/HEAD
```

Then diff the manifest (especially `hooks`), the selected `skills:` paths, the skill and
command counts, and the license files. Re-apply the three hard filters. Bump the pin only
with a reason that names what changed for a BBS rep. Update the provenance row. Run the
validation. Open a PR; an agent that did not write it reviews it.

A refresh that changes nothing is a successful refresh. Record "checked, current" with the
date and move on.

## Propose an addition

One line in the Teams sales channel: what it does, the task it would replace, a link.
Parker tries it a week on live work first. Same bar as above, and the candidate must have
an independent, maintained upstream to pin.

---

*Maintainer: Parker Marshall · Curator agent: `.claude/agents/commons-curator.md` · Last
verified: 2026-09-16*
