# Session handoff — 2026-09-15

What the marketplace reorganization changed, what each plugin owns, what a person
actually gets when they install one, and what is left.

Written to close out the session that did the work. The next session should be able to
answer "which plugin do I install and what will it do for me" without reading a diff.

---

## 1. What changed

Merged as `bcdde99` (PR #9). Open: PR #10 (this file's companion, the `HANDOFF.md`
rewrite). PR #1 closed as superseded.

**The problem.** Mapped against how a state quote actually moves, the marketplace covered
intake → compliance forms → website. It had no pricing path, no customer quote document,
and nothing after bid submission — while all of that already existed as personal skills on
one laptop. A rep who installed the sales plugin hit a dead end right after logging the RFQ.

**The change.** Plugins are now split by **the desk that owns the work**, not by subject:

- 3 skills moved out of the website plugin into `bbs-sales` (`obs-form-filler`,
  `ca-form-filler`, `bbs-sourcing`).
- 12 skills ported in from the personal set, filling the pricing, quote-document,
  item-extraction and post-award gaps.
- `bbs-back-office` created; `bbs-order-reconciliation` moved into it from
  `bbs-foundations`.
- BBS's vendor facts and the shared CA form rules collapsed into one file each.

**Seven portability defects fixed on the way in** — every ported skill was checked for
paths that only resolve on the author's machine or inside a Claude session. Two of the
seven failed *silently*: `bbs-pricelist-import`'s frontmatter had an unquoted colon, so it
would never have loaded at all, and `grainger-promo-page`'s `name` disagreed with its
folder, which stops skill-bus subscriptions matching.

**One correction worth carrying forward.** A vendor-profile note asserting "BBS is NOT
SB-certified" was wrong and would have cost money: `ca-form-filler` surfaces those notes as
pre-fill warnings, so it would have talked reps out of the 5% Small Business preference on
every competitive state solicitation. OSDS 2009473 carries **both** SB and DVBE. The
lesson: canonical facts come from `bbs-foundations`, never inferred from a neighbouring
doctrine file whose scope you have not checked.

---

## 2. Roles and responsibilities — what each plugin owns

The rule: **a plugin owns a desk, and says what it does not own.** If a skill would make
someone install a plugin whose other skills are irrelevant to their job, it is in the wrong
plugin.

### `bbs-sales` — the California state quote desk
**Owns:** everything from an inbound RFQ to a submitted bid, plus outbound campaigns.
RFQ intake, item extraction, BPO eligibility, pricing, the customer quote document, and the
CDCR/CA compliance packets.
**Does not own:** anything after the bid is won (→ `bbs-back-office`), the website
(→ `bbs-website`), or company-wide doctrine (→ `bbs-foundations`).
**Installed by:** sales reps. 13 skills · 1 agent · 2 commands · 4 hooks.

### `bbs-website` — the storefront pipeline
**Owns:** a manufacturer price list becoming a live product page. Catalog import, contract
pricing, variant families, enrichment, storefront pages, quote-bot lane tuning, and the
skill-bus doctrine that keeps design, cert and pricing rules consistent.
**Does not own:** bid forms or vendor sourcing — those moved to `bbs-sales`.
**Installed by:** whoever maintains the site. 10 skills · 10 agents · 4 commands · 1 hook.

### `bbs-back-office` — after the bid is won
**Owns:** reading the truth out of Business Central. Order status, vendor PO receipts,
problem-order reconciliation, true margin after Grainger rebates.
**Does not own:** anything that writes to BC. These skills report; they never post.
**Installed by:** purchasing, accounting, anyone answering "where is it?". 4 skills.
**The thread holding it together:** every skill exists because BC's surface answer is
wrong — `fullyReceived` is unreliable, item-ledger COGS sits at Grainger list before
rebates, an uninvoiced order isn't where people look, and a reported symptom is the last
link in a chain.

### `bbs-foundations` — company-wide
**Owns:** doctrine every other plugin inherits, the BBS way to write a CLAUDE.md, personal
voice skills, managed settings, the AUP, `/bbs-checkup`.
**Does not own:** any desk's workflow. 2 skills · 3 commands · 1 hook.

### Pinned external plugins
`claudeforge`, `impeccable`, `superpowers-chrome`, `caveman`, and Anthropic's
`document-skills` (docx/pdf/xlsx) are **pinned, not copied**, so they keep receiving
upstream fixes. This is the established mechanism — if someone wants an Anthropic skill in
the marketplace, pin it; never vendor a copy.

---

## 3. What you actually get when you install

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace   # once
/plugin install bbs-sales@bbs-claude-marketplace                  # sales reps
/plugin install bbs-website@bbs-claude-marketplace                # site maintenance
/plugin install bbs-back-office@bbs-claude-marketplace            # purchasing / accounting
/plugin install bbs-foundations@bbs-claude-marketplace            # everyone
```

**A plugin install gives you the skills, agents, commands and hooks — and nothing else.**
Two things it does not give you, and both are why a skill fails on a fresh machine:

### Connectors are separate, and some skills are inert without them

| Plugin | Needs | Without it |
|---|---|---|
| `bbs-back-office` | **BC MCP (Business Central)** | All 4 skills have nothing to read |
| `bbs-sales` | BC MCP, SCPRS, Microsoft 365, Firecrawl | Pricing and precedent steps degrade; intake can't fetch from Outlook |
| `bbs-website` | Supabase, Shopify, Grainger MCP, Firecrawl | Catalog and storefront skills can't act |
| `bbs-foundations` | none | Works standalone |

Connector assignment is an admin step — `docs/ADMIN-RUNBOOK.md` §3.

### Some skills shell out to local tooling

Only in `bbs-sales`; everything else is pure Claude + connectors.

| Skill | Needs on the machine |
|---|---|
| `obs-form-filler` | `pypdf`, `pymupdf` (`pip install pypdf pymupdf`) |
| `ca-form-filler` | `pypdf`, `pymupdf`, `pdfplumber`, `pdftotext` (poppler) |
| `bbs-quote-builder` | Node + `npm install docx`, and `soffice` (LibreOffice) for PDF |
| `grainger-promo-page` | `pdftotext` (poppler) |
| `dgs-bpo-item-check` | nothing — ships its own 19,390-part lookup |

`scripts/bbs-setup.ps1` bootstraps most of this on Windows. Each skill checks its
dependencies before touching a file and prints the install command, so a missing library is
a clear message rather than a half-written document.

---

## 4. Open items

| # | Item | Owner | Notes |
|---|---|---|---|
| 1 | **Personal-copy cutover — 15 skills exist twice** | Parker | **Mechanics now confirmed (2026-09-15), and it is not a repo task.** The 15 copies are *account-synced*: removing one from disk did not retire it — a new session re-synced it byte-identical within seconds, and the skill stayed available throughout. It must be removed in Parker's claude.ai account (Settings → Capabilities → Skills). Also confirmed: **there is nothing to merge.** 9 of 15 are byte-identical to the marketplace; the other 6 differ only by being *worse* — `/mnt/skills/...` and `/Users/parkermarshall/...` paths, an unquoted `description:` with a colon, and a `PASTE_VENDOR_PROFILE_JSON_HERE` step. The marketplace copy is canonical in every case, so the cutover is a delete, not a merge. |
| 2 | PR #10 — `HANDOFF.md` rewrite | — | Open, ready |
| 3 | Acceptance gate never recorded | Parker | `docs/acceptance/` — a non-Parker rep completing real work unaided |
| 4 | `bbs-sourcing` references files that exist nowhere | `/bbs-review` | Verified open |
| 5 | `image-pipeline` is a documented stub | `/bbs-review` | Verified open |
| 6 | `family-rollup` depends on an unmerged `bbs-database` branch | — | **Unverified** — lives in that repo |
| 7 | Real-packet test of `obs-form-filler` | Parker | Validated against synthetic stubs only; the Rev. 08/2025 blank packet isn't in the repo. Run `--inspect` on a real one before a rep relies on it. |
| 8 | ~~Canonical model IDs are stale~~ | — | **Fixed 2026-09-15.** Blast radius was 11 live files, not the 2 recorded here — including `bbs-foundations/hooks/skill-bus.json` (injected into every skill run) and `bbs-managed-settings.json` (the company-wide CLAUDE.md on every machine). `CURRENT_MODELS` now lives once in `check_claude_md.py`, and `--self-test` fails if `canonical-facts.md` disagrees. **Parker must re-paste the managed settings** for the fix to reach machines. |

---

## 5. For the next session — run it against the practices, not the diff

The work above is merged. What matters now is whether the marketplace holds up as a way of
working for a small team, so the next session should audit it against the practices that
make skills and plugins actually land in a business this size. Each one below is paired
with what this repo already does and the specific gap left.

### A skill is found by its description, and 30 skills now compete

This is the main quality lever and the least tested thing here. A skill's name and
description are all Claude sees until it triggers, so overlapping descriptions mean the
wrong skill wins — silently, and differently each time.

`bbs-sales` alone has 14 skills, and one cluster is visibly close: `grainger-cart-info`
(cart PDF), `grainger-screenshot` (screenshot of a cart), `dwr-pdf-info` (DWR RFQ PDF),
`dgs-bpo-item-check` ("check these Grainger part numbers") and `bbs-b2b-pricing` ("price
these Grainger items"). A rep who pastes a list of Grainger numbers could plausibly land on
any of three.

**Measured 2026-09-15, and the hypothesis above was wrong.** `skill-creator`'s
`run_eval.py` registers one description at a time and asks "did it fire?", which cannot
answer "which sibling won". A discrimination harness was built instead
(`docs/evals/`): it registers all 13 `bbs-sales` descriptions at once in an isolated
project root and records which one the model actually invokes, 5 runs per query.

| Condition | Baseline | After |
|---|---|---|
| Real-world (name + description) | 20/20 | 20/20 |
| Description alone (names anonymized) | **18/20** | **20/20** |

The Grainger cluster this section predicted would collide never did — cart PDF,
screenshot, DWR PDF, BPO check and punch-out pricing each routed 5/5 in both conditions.
The two real failures were elsewhere: `naspo-quote` lost 40% of its runs to
`ca-rfq-intake`, and `dwr-pdf-info` missed the bare acronym "DWR" (its description led
with the spelled-out agency name). Both now route 100%.

The more valuable finding came from deliberately ambiguous queries. Baseline, "can you
check these Grainger items?" silently ran the **punch-out pricing** skill in 4 of 5 runs,
and "pull the Grainger numbers out of items.pdf" silently ran the **cart** skill in 3 of
5 — a wrong skill, no error. After adding reciprocal "if the rep means eligibility or
price, ask which" clauses, all four ambiguous queries now ask instead of guessing, 5/5.
That is the binding-document rule applied to routing.

Also found and fixed: `bbs-order-reconciliation`'s description was 1,155 characters
against a 1,024 hard limit, so it was **truncated exactly through its entire "Do NOT use
for" clause** — the skill had no negative boundary at selection time at all.

### One source of truth, and nothing invented

Already the repo's strongest habit: vendor facts live in one file both form skills read,
the quote bot states only facts from tool results, `[FLAG: why]` over a guess.

**Gap:** item 8 above. Model IDs are stale in `canonical-facts.md` *and* in the checker
that enforces them, so the wrong value propagates automatically. When a canonical fact has
a checker, the checker is part of the fact — update both or neither. Worth a standing
recheck of every canonical fact with an external source: model IDs, cert numbers and
expiries, LPA numbers, contract vehicles.

### Humans send anything binding

Already enforced rather than documented — managed settings deny the send-class tools,
so quotes and bids are draft-first by construction. Keep it that way; it is the single
control that makes the rest safe to move fast on.

**Extend it:** the same reasoning says a skill should refuse rather than guess on a binding
document. `fill_obs_packet.py` now does this (it will not write a packet with a checkbox it
cannot verify, or a quote too long for the worksheet). Ask whether the other
document-producing skills — `bbs-quote-builder` especially — fail as loudly.

### Distribute, never copy

Already right for external plugins: `document-skills`, `impeccable` and the rest are
pinned, so they keep getting upstream fixes. Vendoring them would have forked them.

**Gap:** item 1. Fifteen skills still exist as personal copies that shadow the marketplace.
Until that is cut over, the marketplace is not actually the distribution mechanism for the
person who owns it, and "no single point of failure by design" is not yet true.

### Measure, or it is a vibe

`MEASUREMENT.md` defines the metrics. `docs/acceptance/` exists precisely because the July
gate was never recorded.

**Gap:** items 3 and 7 — no baseline and no acceptance run. The cheapest real signal: one
non-Parker rep completing one real RFQ end to end, unaided, with what stuck written down.
That single run will say more about the desk split in §2 than any amount of review.

### Least privilege, per desk

Connector assignment is per person and per plugin (`ADMIN-RUNBOOK` §3). A back-office
person needs BC and nothing else; sales needs more. Worth confirming nobody was granted the
full set for convenience — the plugin split makes the minimum obvious for the first time.

### Start where the volume is

The desk split is a bet that CA state quoting is the highest-volume repeated workflow. That
bet is testable: if the sales desk is where the time goes, its skills should show the most
use, and the skills nobody triggers are candidates for removal rather than maintenance.

---

---

Owner: Parker. Last verified 2026-09-15.
