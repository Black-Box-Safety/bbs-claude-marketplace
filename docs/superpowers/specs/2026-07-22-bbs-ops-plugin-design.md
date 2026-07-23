# BBS Ops Plugin — Design

**Date:** 2026-07-22
**Author:** Parker Marshall (with Claude Code)
**Status:** Approved for planning

## Problem

BBS went from nothing to a near-launch, customer-facing storefront in four months. The
knowledge of *how the site is wired* — how a manufacturer price list becomes a database
row becomes a Shopify product becomes a rendered product page — lives in Parker's head and
is scattered across skills in three separate repos plus the global `~/.claude` directory.

Two failure modes are already visible:

1. **Single point of failure.** Only Parker knows the full pipeline. A new hire cannot
   confidently upload a product or fix a broken card without asking him.
2. **Skill drift.** Skills are authored ad hoc in whatever repo/machine is open (two were
   written today on a Mac before this session on the PC). The same capability can diverge
   between machines because there is no single distributable source of truth.

## Goal

One installable Claude Code **plugin** that packages BBS's site-maintenance knowledge —
product intake through rendered product page — as consolidated skills, discrete
responsibility-named agents, and onboarding docs, distributed through a GitHub marketplace
repo so any Black Box team member installs it once and stays current via git. Built to
Anthropic's documented plugin conventions.

## Non-Goals

- Not rewriting any existing skill's *logic* — this is consolidation + packaging, not a
  content rewrite. Skills move in as-is, then get light edits for portability.
- Not building new site features. The plugin documents and operates the site that exists.
- Not migrating the generic third-party reference skills (`shopify`, `shopify-api`,
  `shopify-app-dev`, `shopify-debugging`) — those are public Shopify docs, already available
  as marketplace/global skills, and carry no BBS-specific knowledge. The plugin *references*
  them rather than vendoring copies that would drift.

## Distribution

**GitHub marketplace repo** in the `Black-Box-Safety` org, e.g. `bbs-claude-marketplace`.

```
bbs-claude-marketplace/                      (new GitHub repo)
├── .claude-plugin/
│   └── marketplace.json                ← marketplace manifest (one plugin entry)
├── README.md                           ← install instructions for the team
└── plugins/
    └── bbs-ops/
        ├── .claude-plugin/plugin.json  ← plugin manifest (name, version, description)
        ├── skills/                     ← consolidated BBS skills
        ├── agents/                     ← 6 pipeline-stage agents
        ├── commands/                   ← team-facing slash commands
        └── docs/                       ← the wiring map + runbooks
```

Team onboarding is two commands, documented in the repo README:

```
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace
/plugin install bbs-ops@bbs-claude-marketplace
```

Updates propagate through git — `/plugin marketplace update` pulls new skill/agent
versions. This works across Claude Code CLI, the VSCode extension, and Desktop.

## The Pipeline (what the plugin must make legible)

```
manufacturer price list ─┐
                         ▼
   [1] INTAKE        clean → BBS import template → ETL into Supabase products
                         │
                         ▼
   [2] PRICING       contract discount schedules (MSRP % off by manufacturer),
                     NASPO/NPPGov/Sourcewell eligibility, price modes
                         │
                         ▼
   [3] ENRICHMENT    descriptions, images (Firecrawl scrape → CDN), variant
                     family rollups, QA audit for mismatches/broken images
                         │
                         ▼
   [4] STOREFRONT    Shopify sync → product cards, PDPs, brand pages,
                     collection grids, metafields, compliance chips
                         │
                         ▼
   [5] QUOTE BOT     Direct (LE) + Supply (Grainger) lanes, CA bid forms
                         │
                         ▼
   [6] QA / VISION   cross-stage data quality + business-value review
```

## Agent Roster (discrete responsibilities)

Six agents, each named for the pipeline stage it owns. Existing agents map in; names change
from person-names to responsibility-names so a new hire reads the roster and knows who does
what without tribal knowledge.

| Agent | Owns | Absorbs / based on |
|-------|------|--------------------|
| `catalog-intake` | Price-list cleaning, import template mapping, ETL into the products DB | `bbs-price-list-cleaner`; part of `database-troubleshooter` |
| `pricing-contracts` | Contract discount schedules, manufacturer eligibility, price modes | `bbs-contract-discount-loader` |
| `product-enrichment` | Descriptions, image pipeline, variant family rollups | `product-enrichment-auditor`, `bbs-family-rollup` |
| `storefront-pages` | Shopify product cards, PDPs, brand pages, collections, metafields | `bbs-product-page`, `brand-page-builder` skills |
| `quote-bot` | Direct + Supply lanes, tuning, CA/CDCR bid forms | `scout`, `quincy`, `response-tuner` (folded into one lane-aware agent) |
| `data-qa` | Cross-stage data-quality audits, broken-image/mismatch hunts, missing-product triage | `database-troubleshooter`, `product-enrichment-auditor` |
| `cross-sell` | Related-products / "Customers Also Bought" strip on cards + PDPs; adjacency-driven basket growth | NEW — Phase A pgvector embedding similarity, Phase B co-order/co-quote data |

`vera` (business-vision reviewer) is retained as a **7th, cross-cutting** agent —
`business-review` — because outcome review is orthogonal to the pipeline stages, not one of
them.

### Advisory / continuous-improvement agents (the "living plugin" engine)

Two expert-persona reviewers sit above the pipeline. They do not own a stage; they review the
whole system and write what they learn back into the plugin so it improves like the site does.
Both are adapted from Parker's Senior AI Architect and Senior Technical PM system prompts —
**re-grounded from the unrelated "Project Parker" repos (`state-sourcing-agent`,
`ca-procurement-intel`, `rfq-staging-app`) onto this project's actual stack**, and with stale
model IDs corrected to the current set (`claude-opus-4-8`, `claude-sonnet-5`,
`claude-haiku-4-5`). Finalized into `plugins/bbs-ops/agents/{arthur,tom,cross-sell}.md`.

| Agent | Role | Owns |
|-------|------|------|
| `arthur` (Arthur the Architect) | AI-integration architect | The deterministic/generative boundary, tool/API-route contracts, model routing + escalation, grounding, prompt-cache discipline, Supabase/RLS + proxy security, cross-repo architecture. Reviews designs against real production behavior. |
| `tom` (Tom the Tech) | Delivery, quality & onboarding lead | Scoping, testable acceptance criteria, prompt/knowledge governance, evals + observability, production-readiness, and translating AI concepts for a team that is not native with AI. |

**Continuous-improvement loop.** A `/bbs-review` command dispatches Arthur + Tom against
recent changes in whichever repo is in scope. Each writes findings *back into the plugin* —
updating `site-wiring-map`, a skill, or an agent — so knowledge compounds instead of dying in
a chat log. Arthur takes architecture findings; Tom takes delivery/quality/onboarding; each
hands the other what isn't theirs. This is what makes the plugin "living": every review pass
leaves the docs and skills sharper than it found them.

> **Decision (locked 2026-07-22):** rename the person-named quote-bot agents
> (scout/quincy/response-tuner) into responsibility names for legibility. Arthur, Tom,
> `cross-sell`, and `business-review` keep their names — they are personas/roles by design,
> not pipeline stages.

## Skill Consolidation Map

Skills move into `plugins/bbs-ops/skills/`, grouped by stage. Each keeps its `SKILL.md`
contract; the only edits are (a) removing hardcoded absolute paths like `~/bbs-database` in
favor of repo-detection, and (b) adding a one-line "part of BBS Ops pipeline stage N" header
so the reader always knows where they are.

| Stage | Skills (source repo) |
|-------|----------------------|
| Intake | `price-list-cleaner` (bbs-database) |
| Pricing | `contract-discount-loader` (bbs-database) |
| Enrichment | `family-rollup` (bbs-database, unmerged branch), `image-pipeline` (NEW — currently empty `image-optimization`/`sirv-*` placeholders in bbs-shopify) |
| Storefront | `product-page`, `brand-page-builder` (bbs-shopify) |
| Quote bot | `le-lane-tuning`, `supply-lane-tuning` (bbs-quote-bot); `ca-form-filler`, `obs-form-filler`, `bbs-sourcing` (global `~/.claude`) |
| Cross-cutting | `site-wiring-map` (NEW — the single "how it all connects" reference) |

Referenced but **not vendored** (pointer only): `shopify`, `shopify-api`, `shopify-app-dev`,
`shopify-debugging`.

## The Keystone: `site-wiring-map` skill + docs

The one artifact that directly answers "ensure they understand how the website is wired."
A top-level skill whose body is a narrated map of the whole system: which repo holds what,
where product data lives (Supabase schema summary), how sync runs, where the storefront
theme reads metafields, where the quote bot proxies Claude, and — critically — for each
common task, *which skill and which agent to reach for*. It is the plugin's front door and
what a new hire reads first.

Paired with `commands/`:
- `/bbs-onboard` — walks a new team member through the pipeline and the roster.
- `/bbs-add-product` — routes an "upload a product" request through intake → pricing →
  enrichment → storefront, invoking the right skill at each step.
- `/bbs-new-brand` — new-manufacturer flow (import + contract eligibility + brand page).

## Skill-Bus Enforcement Layer (docs teach, the bus enforces)

The plugin's "guides users" promise has two halves. Docs (`site-wiring-map`, the skills)
*teach*. The **skill-bus** *enforces* — it auto-injects BBS doctrine as context whenever
anyone triggers a relevant skill, so a team member who never read a doc still gets the rules.

This is already proven in-repo: `bbs-shopify/.claude/skill-bus.json` runs a
`bbs-storefront-doctrine` insert (BBS design tokens, cert/claim doctrine, MAP-not-contract
pricing, RFQ page-flow) subscribed `pre` to `impeccable:*`, `shopify`, `shopify-plugin:*`,
`liquid-skills:*`, `frontend-design:*`. Telemetry (`skill-bus-telemetry.jsonl`) shows it
firing on real sessions.

Two defects the current setup has, which the plugin fixes:

1. **It's repo-local to `bbs-shopify`.** Database and quote-bot work get no doctrine. The
   plugin ships the inserts so they travel with install and cover all three stages.
2. **Coverage gaps.** Telemetry shows `bbs-product-page → no_match` (2026-07-22): the
   storefront doctrine does *not* inject when the team's own product-page skill runs. The
   plugin's subscriptions must include the plugin's own skill names.

**Three doctrine inserts, subscribed by pipeline stage:**

| Insert | Injects | Subscribed (pre) to |
|--------|---------|---------------------|
| `bbs-storefront-doctrine` (exists, moves into plugin) | design tokens, cert/claim rules, MAP-not-contract pricing, RFQ flow | `shopify`, `shopify-plugin:*`, `liquid-skills:*`, `frontend-design:*`, `impeccable:*`, **`bbs-ops:product-page`, `bbs-ops:brand-page-builder`, `bbs-ops:cross-sell`** |
| `bbs-catalog-doctrine` (NEW) | import-template rules, contract-eligibility/`is_restricted`, regen-don't-hand-edit | `bbs-ops:price-list-cleaner`, `bbs-ops:contract-discount-loader`, `bbs-ops:family-rollup` |
| `bbs-grounding-doctrine` (NEW) | Arthur's grounding rule, current model IDs, cache-the-prefix, forms-at-session-end | `bbs-ops:le-lane-tuning`, `bbs-ops:supply-lane-tuning` |

`/bbs-onboard` runs `skill-bus:onboard` to wire these subscriptions at install time. Arthur +
Tom's `/bbs-review` reads `skill-bus-telemetry.jsonl` to catch new `no_match` gaps and patch
coverage — closing the loop that makes the plugin "living."

## Reference Skills — Link, Don't Vendor

Several already-installed official plugins cover generic capability the pipeline uses. The
plugin **points at them** (names its dependencies in docs + the wiring map) rather than
copying, so they update on their own and never drift. This is Arthur's no-drift rule.

| Installed skill/plugin | Used by | For |
|------------------------|---------|-----|
| `shopify-plugin:shopify-custom-data` | `cross-sell`, `storefront-pages` | metafields/metaobjects — `bbs.similar_products`, `brand.*` |
| `liquid-skills:*` (standards, a11y, themes) | `storefront-pages`, `cross-sell` | Liquid authoring incl. `product-similar.liquid` |
| `impeccable`, `frontend-design` | `storefront-pages` | UI polish + design review |
| `firecrawl` | `product-enrichment` | enrichment scraping (already in use) |
| `windsor-ai` | `cross-sell`, `business-review` | analytics connectors — cross-sell lift / attach-rate |
| `pr-review-toolkit` | Tom's readiness gate | code review before ship |
| `superpowers` (brainstorming, writing-plans, TDD, verification) | all | the process spine |

**Distribution consolidation:** BBS skills also exist as `.skill` packages in
`OneDrive/claude-inside-sales-skills` (bbs-sourcing, ca-form-filler, obs-form-filler) and as
copies in global `~/.claude/skills`. The plugin becomes the single source; onboarding
documents removing the duplicate global/OneDrive copies so there is one truth per skill.

## Sibling Plugin: `bbs-foundations` (separate spec)

`bbs-ops` is the **site-maintenance** plugin. A second, broader plugin — `bbs-foundations` —
is planned separately: the company's **AI fundamentals** for a team that is not native with
AI. It carries the MCP connectors the team uses (ca-procurement-intel, Grainger, BBS KIt,
Microsoft 365, Shopify, Supabase), foundational skills, shared company knowledge, and
how-to-work-with-Claude onboarding. It gets its own brainstorm → spec → plan cycle.

Boundary between the two:
- **`bbs-ops`** — how to *change the website* (the pipeline, its skills and agents). No MCPs
  bundled; it *references* MCPs that `bbs-foundations` provides.
- **`bbs-foundations`** — what the *whole company* stands on: MCPs, company knowledge, AI
  literacy. The ca-procurement-intel MCP lives here, not in `bbs-ops`.

Both ship from **one marketplace repo** (`Black-Box-Safety/bbs-claude-marketplace`), so the team
adds one marketplace and installs either or both. The `pjm3wv/ca-procurement-intel-bbs` fork
was used only to read that project's README format for these docs — its code is **not**
pulled into either plugin.

## Migration Strategy

1. **Copy, don't cut, first.** Build the plugin repo with copies so nothing breaks while we
   validate. Original repo-local skills keep working during transition.
2. **Validate** by installing the plugin locally and running each command/agent against a
   real task (upload a test product, build a test brand page).
3. **Cut over.** Once validated, replace the originals in each repo with a short pointer
   (`This skill now lives in the bbs-ops plugin — install it via ...`) so there is exactly
   one source of truth and drift stops.
4. Global skills (`ca-form-filler`, etc.) stay installed globally *and* ship in the plugin;
   resolve the duplication by removing the global copies for anyone who installs the plugin
   (documented in onboarding).

## Anthropic Best Practices Applied

- **Plugin + marketplace manifests** per the documented schema (`.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`).
- **Skills**: one responsibility each, description-driven auto-discovery, progressive
  disclosure (heavy reference material in `references/`, not the main body).
- **Agents**: discrete single responsibility, description written for correct routing, minimal
  tool grants (DB agents get SQL + read tools only, not write-everything).
- **Commands**: thin orchestration that delegates to skills/agents rather than duplicating
  their logic.
- **Version pinning** via plugin.json `version`; changelog in the repo.

## Success Criteria

1. A Black Box team member who has never touched the codebase can install the plugin and,
   guided only by `/bbs-onboard` and `site-wiring-map`, correctly upload one new product and
   see it render as a card + PDP — without asking Parker.
2. Every current BBS-specific skill is reachable from the single plugin; no capability is lost.
3. Each pipeline stage has exactly one owning agent, the two advisory reviewers (Arthur, Tom)
   plus `business-review` and `cross-sell` are present, and the roster tables in the docs
   match the shipped agents.
4. After cutover, each source repo's former skill location contains only a pointer to the
   plugin (no divergent copies), and the duplicate global/OneDrive skill copies are removed.
5. Skill-bus doctrine inserts ship in the plugin and fire on the plugin's own skills — a
   `no_match` for a `bbs-ops:*` skill in `skill-bus-telemetry.jsonl` is a coverage bug
   `/bbs-review` must catch and close.

## Open Questions for Spec Review

1. Agent naming — responsibility-named (default) vs. keep person-names (scout/quincy/vera)?
2. Should `image-pipeline` be authored now (the sirv/image dirs are empty), or stubbed as a
   documented TODO until the CDN workflow is settled?
3. Repo name — `bbs-claude-marketplace` vs. something shorter (`bbs-ops`)?
