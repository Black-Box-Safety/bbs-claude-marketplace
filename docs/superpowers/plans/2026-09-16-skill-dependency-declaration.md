# Skill Dependency Declaration — Plan

**Date:** 2026-09-16
**Spec:** `docs/superpowers/specs/2026-09-16-skill-dependency-declaration-design.md`
**Slice:** `docs/STEWARD.md` §5 — Dependency completeness
**Branch:** `claude/slice-5-dependency-declaration`

Two halves: **A** every skill declares its external systems, machine-checked; **B** the
checker runs on every pull request instead of when an agent remembers.

---

## A — Declaration

### A1. Registry in `scripts/check_marketplace.py`

`EXTERNAL_SYSTEMS`: `id → {kind, signals, canon, bootstrap}`.

Signals are **enumerated identifiers**, never brand names — see the spec for why
(`bc_sync_queue` is a Supabase column, and a `bc_*` prefix would fabricate a Business
Central dependency).

| id | kind | signal shape |
|---|---|---|
| `business-central` | mcp | the ten real `bc_*` tool names |
| `bc-mcp-proxy` | mcp | `…_PAG#####`, `bc-mcp-proxy:` |
| `cdata-connect` | connector | `CData Connect AI`, `Dynamics365BusinessCentral1` |
| `grainger` | mcp | `grainger_price`, `grainger_search`, … , "Grainger MCP" |
| `supabase` | mcp | `execute_sql`, `apply_migration`, `SUPABASE_SERVICE_KEY`, … |
| `shopify` | mcp | "Shopify MCP", `SHOPIFY_ADMIN_API_TOKEN`, `graphql_query` |
| `microsoft-365` | connector | `outlook_*`, `sharepoint_*`, `teams_*`, "M365 tools" |
| `ca-procurement-intel` | mcp | `explore_sql`, `market_*`, `play_*` |
| `firecrawl` | mcp | "Firecrawl", `FIRECRAWL_KEY` |
| `sirv` | service | "Sirv" |
| `node` / `libreoffice` / `shopify-cli` / `vercel-cli` / `python3` | cli | the invocation |
| `pypdf` / `pymupdf` / `anthropic` | python-package | the import |

Bonds: each system id's `canon` string must appear in `canonical-facts.md`; each cli id's
`bootstrap` names its `bbs-setup.ps1` winget id or `None`.

### A2. Checks

`missing_requires`, `requires_malformed`, `unknown_dependency_id`,
`undeclared_dependency` (FAIL); `dependency_declared_unused`, `cli_not_bootstrapped`
(WARN); `dependency_registry_drift` (FAIL). All FAILs route through
`is_counter_example()` first. `canonical-facts.md` is exempt from the scan — it is the
file the anchors are checked against, so scanning it is circular.

### A3. Scan scope

`SKILL.md` + everything under the skill directory (`references/`, `scripts/`, `assets/`).
`bbs-order-reconciliation`'s real `bc_*` calls live in `references/tool-recipes.md`, so
references cannot be skipped.

### A4. Declare all 27, read from skill text

| plugin | skill | `requires` | `degrades-without` |
|---|---|---|---|
| back-office | `bbs-order-reconciliation` | business-central, grainger, microsoft-365 | |
| back-office | `bbs-po-status` | bc-mcp-proxy | |
| back-office | `bbs-rebate-profitability` | cdata-connect | |
| back-office | `so-search` | bc-mcp-proxy | |
| foundations | `bbs-claude-md-forge` | python3 | anthropic |
| foundations | `bbs-deck-voice` | — | |
| foundations | `bbs-voice-template` | microsoft-365 | |
| sales | `bbs-quote-builder` | node, libreoffice | |
| sales | `bbs-sourcing` | microsoft-365 | firecrawl, ca-procurement-intel, business-central |
| sales | `ca-form-filler` | python3, pypdf, pymupdf | |
| sales | `ca-rfq-intake` | python3 | |
| sales | `dgs-bpo-item-check` | python3 | |
| sales | `grainger-pricing` | grainger | |
| sales | `grainger-promo-page` | grainger, business-central, ca-procurement-intel, python3 | firecrawl, vercel-cli |
| sales | `naspo-quote` | grainger, python3, pypdf, pymupdf | |
| sales | `rfq-item-extract` | — | |
| sales | `vendor-quote-email` | — | |
| website | `bbs-pricelist-import` | supabase | firecrawl |
| website | `brand-page-builder` | supabase, shopify, shopify-cli | firecrawl |
| website | `contract-discount-loader` | supabase | |
| website | `family-rollup` | supabase, shopify | firecrawl |
| website | `image-pipeline` | supabase, sirv | firecrawl, shopify |
| website | `le-lane-tuning` | supabase | |
| website | `price-list-cleaner` | — | |
| website | `product-page` | shopify-cli | shopify |
| website | `site-wiring-map` | — | |
| website | `supply-lane-tuning` | grainger | |

**Four** skills need nothing external — `bbs-deck-voice`, `rfq-item-extract`,
`vendor-quote-email`, `site-wiring-map`. The brief estimated two; the other two are
prose-only mentions (`site-wiring-map` names every connector in the repo and invokes none
of them).

`price-list-cleaner` was a fifth in my reading and is not: the scanner found *"Use `fitz`
(PyMuPDF) for text extraction"* on line 79, which is an instruction to write extraction
code against a package a rep may not have. It declares `[python3, pymupdf]`.

Readings worth recording, because a reviewer will want to check them:

- `ca-rfq-intake` — "The Supabase `rep_cockpit` pipeline in `ca-quote-hub` remains the
  tracker of record" points at another system's record. The skill writes a local markdown
  log. **Not** a Supabase dependency.
- `ca-form-filler` — SCPRS appears once, in "agency-side fields stay blank — method of
  award, SCPRS ref, PO#". A field left blank is not a dependency.
- `bbs-sourcing` — SCPRS and Business Central are reached only through the `supplier-scout`
  agent, and only when the BBS vendor directory misses. Recorded as `degrades-without`.
- `bbs-claude-md-forge` — `execute_sql` and `shopify theme list` appear in its
  `references/`, quoted as CLAUDE.md content and canon, not invoked.

### A4b. What the scanner caught in the table above

The table is a human reading and the scanner corrected six entries of it, which is the
best available evidence that the FAIL is doing work rather than restating what was already
written:

| Skill | Found | Verdict |
|---|---|---|
| `contract-discount-loader` | `python etl/import_contract_pricing.py` | missed — added `python3` |
| `family-rollup` | `python etl/nonapparel_family_rollup.py` | missed — added `python3` |
| `bbs-pricelist-import` | `python etl/import.py` | missed — added `python3` |
| `le-lane-tuning` | `npm run build` | missed — added `node` |
| `supply-lane-tuning` | `npm test`, `npm run eval:supply` | missed — added `node` |
| `price-list-cleaner` | `PyMuPDF` | missed — not a "needs nothing" skill after all |
| `family-rollup` | declared `shopify`, uncorroborated | **over**-declared: line 48 says the edge function's "Shopify token is server-side — no local token needed". Removed |

Two findings were the scanner being wrong, and both were fixed in the registry rather than
worked around in a skill — brand names are not signals, which the spec argues and three
registry entries had quietly broken:

- `site-wiring-map` was told it needed `firecrawl` and `sirv`, from a map of what the three
  website repos contain ("Firecrawl enrichment", "the Sirv image CDN").
- `rfq-item-extract` was told it needed `grainger`, from a line naming the Grainger MCP
  only to say that `grainger-pricing` is the skill that prices the list.

### A5. `--requirements` reporting mode

Per-skill table with kind resolved, derived at read time.

---

## B — CI gate

`.github/workflows/check-marketplace.yml`, on `pull_request` and `push` to `main`, plus
`workflow_dispatch`.

**Reports, does not block, on this first pass.** Whether it becomes a required check is
Parker's call — a gate that starts out mandatory on a repo that has never had one turns
its first false positive into a merge stoppage, and the fastest way to get a checker
ignored is to have it block something that was fine. It runs `--json`, posts the finding
table to the job summary, and exits 0 regardless. Flipping it to blocking is deleting one
`|| true`; the workflow says so in a comment.

Also runs `check_claude_md.py` over the repo root, which `docs/STEWARD.md` names as the
second verify command.

---

## C — Checker limitations: measured, then acted on

Both claims in the brief were re-measured against this HEAD rather than assumed.

1. **"The counter-example exemption blinds 13% of the form-ID scan (12 of 89 in-scope
   plugin markdown files)."** The 89 reproduces exactly. The 12 does not, on any reading
   tried: **2** unknown-form matches exist repo-wide, both exempted, in **1** file; at file
   granularity 6 of 89 (6.7%) contain an exempted match of any kind. Both exemptions are
   **correct** — `field-maps.md` saying *"Form ID is GSPD-05-105. Earlier revisions of this
   file said GSPD-05-106"* is a counter-example doing its job. **No false negative is
   observable, so nothing is changed here.** Reported rather than fixed.

2. **"`form_id_undocumented` WARN is unreachable for STD/OBS."** Confirmed, and it is
   stronger than stated: the branch is unreachable for **all three** families. `near` is
   `[k for k in known if k.startswith(family)]`, and every family `form_re` can match —
   `GSPD-05`, `STD`, `OBS` — already has a documented member, so `near` is never empty.

   **Not made reachable.** The only way to reach it is to loosen the near-miss test, and
   the near-miss test is what caught the two `STD 1000` survivors of the OBS 1000 fix.
   Loosening a control on a binding document is on the escalate list. Fixed instead: the
   dead branch is replaced by a second FAIL branch with an accurate message, so an
   undocumented form is no longer told it is "a near-miss of STD 204, STD 205" when it is
   not. **Same FAIL coverage, no semantics changed, no dead code.** Whether a real-but-
   undocumented form should be a WARN is a ruling on a binding-document control →
   **Parker's call.**

---

## Order

1. Spec + plan ✔
2. Registry and checks in `check_marketplace.py`
3. Prove the FAIL on a deliberately undeclared dependency **before** declaring anything
4. Declare all 27; checker to 0 FAIL
5. Prove the other three directions (empty declaration, warning prose, all-27-pass)
6. Form-ID message fix
7. CI workflow
8. `check_marketplace.py` exit 0 · `check_claude_md.py` · PR
