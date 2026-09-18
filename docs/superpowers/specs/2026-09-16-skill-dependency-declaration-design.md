# Skill Dependency Declaration — Design

**Date:** 2026-09-16
**Author:** Claude Code (worker session), for Parker Marshall
**Status:** Proposed — implements `docs/STEWARD.md` slice 5
**Plan:** `docs/superpowers/plans/2026-09-16-skill-dependency-declaration.md`

## Problem

A rep installs the marketplace and runs a skill. If the skill needs the Grainger MCP and
that connector is not assigned to their account, nothing announces it. The skill either
degrades into a plausible answer with no live pricing behind it, or stops halfway through
a bid. **Nothing in this repo tells a rep, before they install, whether a job will run on
their machine.**

### The evidence that this is not recoverable from prose

Two scans of the same 27 skills for external-system dependencies, differing only in regex
phrasing, disagreed: **20 skills with dependencies on one pass, 25 on the other.** The
whole difference was wording — "Business Central" vs `bc_*`, "Grainger" vs
`grainger_price`. Nothing declares anything, so the answer is recoverable only by reading
prose, inconsistently.

Reading the 27 skills by hand for this spec found three failure modes that make a
prose scan not merely inconsistent but **wrong**:

1. **A brand name is usually not a dependency.** `dgs-bpo-item-check` says "Grainger part
   number" six times and explicitly instructs *"Do not search the web, do not check
   Grainger.com"* — it reads a bundled `.txt`. `rfq-item-extract` parses "Grainger cart"
   PDFs with no Grainger connector at all. `bbs-quote-builder`'s only mention of Business
   Central is its description saying *"Do NOT use this skill to pull existing quote
   records out of Business Central."* A prose scan counts all three as dependencies.

2. **An identifier prefix is not a dependency either.** `bbs-pricelist-import` contains
   `bc_sync_queue` and `bc_vendor_no` — **Supabase table and column names**, not Business
   Central MCP tools. A `bc_*` regex fabricates a Business Central dependency on a skill
   that never touches it.

3. **One name hides three different installs.** "Business Central" is reached three
   mutually exclusive ways in this repo, and no skill uses more than one:

   | Path | Shape | Skills |
   |---|---|---|
   | BBS Business Central MCP | `bc_customer_snapshot`, `bc_query_entity`, … | `bbs-order-reconciliation`, `grainger-promo-page` |
   | `bc-mcp-proxy` | `ListSalesInvoices_PAG30012`, `ListPurchaseOrders_PAG30066`, … | `so-search`, `bbs-po-status` |
   | CData Connect AI | catalog `Dynamics365BusinessCentral1` | `bbs-rebate-profitability` |

   A declaration that flattens these to "Business Central" tells a rep to install the
   wrong thing and is worse than no declaration, because it reads as authoritative.

## Goal

Every skill declares, **in its own frontmatter**, the external systems it needs, and
`scripts/check_marketplace.py` FAILs on a dependency that is used but not declared.

## Non-goals

- **Not** verifying that a declared connector actually exists or is reachable. No agent in
  this repo can reach an MCP connector to confirm a skill really needs it. Declarations are
  read from skill text and are labelled that way (see *Honesty* below).
- **Not** a sibling registry file. Invariant 2 — a fact restated in a second file goes
  stale in one of them. The declaration lives in the frontmatter of the skill it describes.
- **Not** touching any `description:` text. Four descriptions are at 980–1006 of the 1024
  limit; the declaration is a separate key and adds nothing to them.
- **Not** Python package resolution beyond naming the import. `pypdf` and `pymupdf` are
  declared because their absence is the actual failure; pinning versions is out of scope.

## Design

### 1. Two frontmatter keys

```yaml
name: grainger-promo-page
description: >-
  …unchanged…
requires: [grainger, business-central, ca-procurement-intel, python3]
degrades-without: [firecrawl, vercel-cli]
```

- **`requires:`** — the job cannot be completed without it. **Mandatory on every skill**,
  including the five that need nothing, which write `requires: []`. An omitted key is a
  FAIL, so "declares nothing" is a reviewed assertion rather than an oversight. This is
  what actually delivers the slice: completeness comes from the key being mandatory, not
  from the scanner being clever.
- **`degrades-without:`** — optional key; the skill runs and says the live lookup is
  unavailable. This is not invented: `site-wiring-map` already states the contract —
  *"If a connector is not installed, the referencing skill degrades gracefully … it never
  errors the session."* Collapsing optional into required would over-warn a rep away from
  a skill that works fine without it.

**The skill names the system, never the kind.** `grainger` is always an MCP; repeating
`mcp:` in 12 skills would be a fact restated 12 times (invariant 2). The kind lives once,
in the checker's registry, and is printed on demand by `--requirements`.

### 2. The registry, and what it is bonded to

`scripts/check_marketplace.py` holds one table: `id → (kind, signals, canon anchor)`.

**Signals are enumerated identifiers, never brand names.** `business-central` is detected
by the ten real `bc_*` tool names, not by `bc_*`, which is what would have misread
`bc_sync_queue`. Brand names are deliberately **not** signals — they are the measured
source of the 20-vs-25 disagreement, and a checker built on them inherits the ambiguity it
exists to remove.

Two bonds keep the registry from becoming a third source of truth:

- Every **system** id carries an anchor string that must appear in
  `references/canonical-facts.md` — the "Systems of record" table is the authority for what
  BBS's systems are called. Rename a system in canon without updating the checker and the
  checker FAILs (invariant 3, from the checker's side).
- Every **CLI** id is checked against `scripts/bbs-setup.ps1`, the rep-machine bootstrap.
  A CLI tool a skill needs that the bootstrap does not install is a WARN, because that is
  precisely a job that will not run on a rep's machine.

### 3. Checks added

| Code | Level | Fires when |
|---|---|---|
| `missing_requires` | FAIL | a skill has no `requires:` key |
| `requires_malformed` | FAIL | `requires:`/`degrades-without:` is not a list of strings |
| `unknown_dependency_id` | FAIL | a declared id is not in the registry (typo guard) |
| `undeclared_dependency` | FAIL | a registry signal appears in the skill and the id is in neither key |
| `dependency_declared_unused` | WARN | a declared id has no signal anywhere in the skill |
| `cli_not_bootstrapped` | WARN | a declared CLI id is not installed by `bbs-setup.ps1` |
| `dependency_registry_drift` | FAIL | a registry anchor no longer appears in `canonical-facts.md` |

`undeclared_dependency` is a **floor, not a ceiling.** It proves only what an enumerated
identifier can prove. A skill that says "look it up in Business Central" in prose and never
names a tool is invisible to it — which is the honest position, and why `requires:` is
mandatory rather than inferred.

Over-declaration is a WARN, not a FAIL, on purpose: the safe direction is a rep installing
one connector too many.

### 4. Counter-example awareness

The scan calls the existing `is_counter_example()` before every FAIL, as
`AGENTS.md` requires of any new check. Prose warning about a system is correct content:
`bbs-quote-builder`'s *"Do NOT use this skill to pull … out of Business Central"* must not
be read as a Business Central dependency.

One scoping exemption, for a stated reason rather than by filename convenience:
**`canonical-facts.md` is excluded from the dependency scan because it is the file the
registry's anchors are checked against.** Scanning the registry's own source for undeclared
uses of the registry is circular; it names `shopify theme list` and `execute_sql` as canon,
not as instructions to the skill that happens to host the file.

### 5. Reporting

`python3 scripts/check_marketplace.py --requirements` prints the per-skill table with the
kind resolved — the "can I run this?" view, derived at read time, never stored twice.

## Honesty — what this does not establish

**Unverified by me:** no agent in this session can reach Grainger, Business Central,
Supabase, Shopify, Microsoft 365, the SCPRS warehouse or CData Connect to confirm that a
skill genuinely needs the connector it names. Every declaration in this change is **read
from the skill's own text** — its tool calls, its scripts' imports, its documented
commands. Where the text is ambiguous the spec records the reading taken. A connector that
a skill needs but never mentions is not discoverable this way and is not claimed to be
covered.

## Findings surfaced, not fixed

- **`bbs-quote-builder` requires `soffice` (LibreOffice) to deliver its PDF, and
  `scripts/bbs-setup.ps1` does not install it.** A rep who ran the bootstrap cannot produce
  a quote PDF. Surfaced by `cli_not_bootstrapped`; changing the bootstrap is outside this
  slice.
- `dynamics-crm` appears in canon's Systems of record ("Pipeline / outreach — Dynamics 365
  Sales") but **no skill touches it**. Not added to the registry.
- `.claude-plugin/marketplace.json` pins `claudeforge` at `ref: "dev"` and `impeccable` at
  `ref: "main"` — moving targets on BBS's own forks, so what a rep installs Tuesday is not
  what they installed Monday. **Flagged, not changed**; outside this slice.

## Alternatives rejected

- **A `dependencies.json` registry beside the skills.** Violates invariant 2 directly.
- **Inferring dependencies from prose and skipping the declaration.** This is the thing
  that was measured to disagree with itself by five skills.
- **Putting the requirement in `description:`.** Four descriptions are within 5% of the
  1024 limit; past it the text is truncated through the "do NOT use" clause.
- **A single flat `requires:` with no optional tier.** Would mark seven website and sales
  skills as unusable without Firecrawl, contradicting `site-wiring-map`'s stated
  graceful-degradation contract.
