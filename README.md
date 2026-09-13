<p align="center">
  <img src="https://img.shields.io/badge/scope-catalog%20→%20storefront%20→%20quote%20bot-051c2c" alt="Covers the full product pipeline">
  <img src="https://img.shields.io/badge/install-one%20plugin-b19800" alt="One plugin">
  <img src="https://img.shields.io/badge/works%20in-Claude%20Code%20CLI%20·%20VS%20Code%20·%20Desktop-6E56CF" alt="Works in Claude Code CLI, VS Code, and Desktop">
</p>

# BBS Website

This marketplace ships more than one plugin. This README covers **bbs-website**, the one that
maintains the website: everything from a manufacturer's price list to a live product page,
packaged as one Claude Code plugin. The marketplace also ships **bbs-sales**, the California
state sales desk (inbound RFQ intake and quoting, plus outbound Grainger promo pages); see the
plugins table below and [its own README](plugins/bbs-sales/README.md) for that one.

bbs-website covers three repos that together make one storefront: the product **database**, the
**Shopify** store, and the customer-facing **quote bot**. Install it once and Claude knows how
BBS does each job, the same way every time. No one person has to hold it all in their head.

**Jump to:** [Plugins in this marketplace](#plugins-in-this-marketplace) · [See it work](#see-it-work) · [Use it](#using-it-team-start-here) · [Set it up](#setting-it-up-admins) · [What you can do](#what-you-can-do) · [What's inside](#whats-inside) · [Limits](#what-it-wont-do) · [Docs](#documentation) · [Technical details](#for-developers)

## Plugins in this marketplace

| Plugin | Covers | README |
|---|---|---|
| `bbs-website` | Maintaining the website: price list to product page, across the database, Shopify, and the quote bot. | This file |
| `bbs-sales` | California state sales: inbound RFQ intake and quoting, and outbound Grainger promo page campaigns. | [plugins/bbs-sales/README.md](plugins/bbs-sales/README.md) |
| `bbs-foundations` | What the whole company stands on: how to write a CLAUDE.md the BBS way (`bbs-claude-md-forge`), the doctrine every skill inherits, and the canonical facts every repo must agree on. | [plugins/bbs-foundations/README.md](plugins/bbs-foundations/README.md) |
| `claudeforge` | Pinned external dependency of `bbs-foundations`: the generic CLAUDE.md engine (150-line cap, `@path` chaining, `/sync-claude-md`). BBS fork, updates through git. | [Black-Box-Safety/ClaudeForge](https://github.com/Black-Box-Safety/ClaudeForge) |
| `impeccable` | Pinned external design skill: `/impeccable polish`, `audit`, `critique`, `typeset`, `layout` plus a deterministic anti-pattern detector for any HTML/UI we ship to customers. Downloads its engine binary to `~/.impeccable/bin/` on first run. BBS fork, sync from upstream to update. | [Black-Box-Safety/impeccable](https://github.com/Black-Box-Safety/impeccable) |

The rest of this README is about `bbs-website` specifically.

## See it work

> **You:** We just got a price list from Avon Protection. Get it into the store.
>
> **Claude:** Cleaning the list into the BBS import template (17 SKUs), loading it into the products database, and checking Avon's contract eligibility (they're on NPPGov PS25650, so contract pricing applies). Enriching descriptions and images, then building the Avon brand page in the Field Manual style like the other 24. Last step: a "Customers Also Bought" strip so the new gear surfaces next to related items.

One request walks the whole pipeline. Each step is owned by an agent that knows the BBS way of doing it, and the rules (pricing, certifications, design) apply automatically whether or not you've read them.

## Using it (team, start here)

Once it's installed, there's nothing to configure:

1. Open the repo in Claude Code (CLI, the VS Code extension, or Desktop).
2. Run **`/bbs-onboard`**. It walks you through the pipeline and the agent roster.
3. It points you at **`site-wiring-map`**, the single "how it all connects" reference.
4. Try a real task: *"Add a product,"* *"Build a brand page for Streamlight,"* or *"Why is the Supply lane showing too many options?"*

You should be able to upload one product and see it render as a card and PDP without asking anyone. The [onboarding guide](plugins/bbs-website/docs/ONBOARDING.md) has more.

## Setting it up (admins)

One person adds the marketplace once; the whole team installs from it and stays current through git.

```bash
# add the marketplace (one time)
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace

# install the plugin
/plugin install bbs-website@bbs-claude-marketplace

# wire the guardrails and learn the layout
/bbs-onboard
```

Updating later is `/plugin marketplace update`: new skill and agent versions arrive through git, so nobody copies files between machines and nothing drifts.

## The rep quote desk

Sales reps: your entire setup is `docs/REP-SETUP.md` (~20 min). The VS Code workspace is
`workspace/bbs-rep.code-workspace`; verify any machine with `/bbs-checkup`.

Admins: `docs/ADMIN-RUNBOOK.md` (deploy + operate), `docs/MEASUREMENT.md` (the 8 numbers),
`docs/ADMIN-CLEANUP.md` (one-time hygiene), `REGISTRY.md` (what's canon vs archived).
Design: `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md`.

## What you can do

- **Load a new price list**: *"Clean this Damascus price sheet and import it."*
- **Apply a contract**: *"Load the new Sourcewell discounts by manufacturer."*
- **Onboard a manufacturer**: *"Add a brand page for Avon, like the others."*
- **Fix the storefront**: *"This product card is missing its logo and shows the wrong price mode."*
- **Tune the quote bot**: *"The Direct lane isn't recommending the right brands."*
- **Merchandise**: *"Add a Customers-Also-Bought strip to the PDPs."*
- **Audit quality**: *"Find products with broken images or descriptions that don't match."*

## What's inside

| | |
|---|---|
| Pipeline stages | **7**: intake, pricing, enrichment, storefront, quote bot, data-QA, cross-sell |
| Agents | **10**: one owner per stage, plus Arthur (architecture), Tom (delivery), business-review |
| Skills | Price-list cleaning, contract pricing, variant families, product pages, brand pages, image pipeline, lane tuning, CA/CDCR bid forms, and `site-wiring-map` |
| Commands | `/bbs-onboard` · `/bbs-add-product` · `/bbs-new-brand` · `/bbs-review` |
| Guardrails | Skill-bus doctrine that auto-applies BBS design, cert, and pricing rules (grounding rules come from `bbs-foundations`) |
| Repos covered | `bbs-database` · `bbs-shopify` · `bbs-quote-bot` |

```mermaid
flowchart LR
  A["Price list"] --> B["1 · Intake<br/>clean + import"]
  B --> C["2 · Pricing<br/>contracts + eligibility"]
  C --> D["3 · Enrichment<br/>copy · images · families"]
  D --> E["4 · Storefront<br/>cards · PDPs · brand pages"]
  E --> F["5 · Quote bot<br/>lanes + bid forms"]
  D --> G["6 · Data-QA"]
  E --> H["7 · Cross-sell"]
```

## What it won't do

It doesn't replace the three repos or run the site: it's how you *maintain* them. The quote bot it tunes is advisory: it searches, recommends, quotes, and generates forms, but it never places orders or writes to Business Central on its own. And it's honest by design: the bot states only facts from the database and knowledge files, never invented prices or stock. Sanity-check any number before it goes to a customer, same as any tool.

## Documentation

| Guide | Who it's for |
|---|---|
| [ONBOARDING](plugins/bbs-website/docs/ONBOARDING.md) | Anyone new to maintaining the site |
| [site-wiring-map](plugins/bbs-website/skills/site-wiring-map/SKILL.md) | The "how it all connects" reference |
| [CONTRIBUTING](plugins/bbs-website/docs/CONTRIBUTING.md) | Changing or adding a skill/agent |
| [plugins/bbs-website](plugins/bbs-website/README.md) | The plugin's own detailed README |

## For developers

<details>
<summary>How it's built, the layout, and the quick start</summary>

### Layout

```
bbs-claude-marketplace/
├── .claude-plugin/marketplace.json   # marketplace manifest, lists every plugin
├── README.md                         # this file
└── plugins/
    ├── bbs-website/
    │   ├── .claude-plugin/plugin.json
    │   ├── skills/                   # one folder per skill, each with SKILL.md
    │   ├── agents/                   # one file per agent
    │   ├── commands/                 # /bbs-onboard, /bbs-add-product, …
    │   └── docs/                     # onboarding + contributor guides
    └── bbs-sales/                    # same shape: plugin.json + skills/, no agents/commands yet
```

### How the pieces fit

- **Skills** teach the BBS way of each task; **agents** own a pipeline stage and route work to the right skill; **commands** are thin orchestration over both.
- **Two data planes, one product truth**: the Supabase products database (`bbs-database`) is the source, Shopify renders it, and the quote bot advises over a frozen snapshot plus live search. A database change reaches the storefront only after sync, and the bot only after a `gen-*.mjs` regen is committed.
- **Docs teach, the skill-bus enforces**: three doctrine inserts (storefront design/cert/pricing and catalog rules from `bbs-website`; quote-bot grounding from `bbs-foundations`) auto-inject as context whenever a relevant skill runs, so the rules hold even for someone who hasn't read them. `/bbs-review` reads `skill-bus-telemetry.jsonl` to catch coverage gaps.
- **Reviewers keep it living**: Arthur (architecture) and Tom (delivery/quality) review recent changes and write findings back into the skills, so the plugin sharpens like the site does.
- **Reference skills are linked, not copied**: generic Shopify/Liquid skills update on their own and never drift.

### Quick start (contributor)

```bash
git clone https://github.com/Black-Box-Safety/bbs-claude-marketplace
cd bbs-claude-marketplace
# add it as a local marketplace to test before pushing
/plugin marketplace add ./
/plugin install bbs-website@bbs-claude-marketplace
/bbs-review        # run Arthur + Tom against your changes before shipping
```

**Model IDs (current only):** `claude-opus-4-8` · `claude-sonnet-5` · `claude-haiku-4-5`. Anything referencing a dated or older suffix is stale. Fix it.

</details>

---

<sub>Maintained by the Black Box Safety team, DVBE/SDVOSB government distributor, El Cajon, CA. No single point of failure by design. Design & plans in `docs/superpowers/`.</sub>
