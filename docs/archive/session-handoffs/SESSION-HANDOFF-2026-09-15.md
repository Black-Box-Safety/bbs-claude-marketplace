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

**One correction worth carrying forward.** ~~A vendor-profile note asserting "BBS is NOT
SB-certified" was wrong and would have cost money … OSDS 2009473 carries **both** SB and
DVBE.~~ **Superseded 2026-09-22.** Parker ruled in session that OSDS 2009473 carries
**DVBE only** and BBS is **not** a California small business, having passed the state SB
revenue threshold; BBS remains a small business federally. So the conclusion recorded here
on 2026-09-15 was wrong and has been reversed — see `canonical-facts.md`,
"Small-business status is channel-dependent". The lesson survives intact and is the reason
this entry is kept rather than deleted: canonical facts come from `bbs-foundations`, never
inferred from a neighbouring doctrine file whose scope you have not checked, and a
certification claim is not a fact until it names its channel.

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
**Installed by:** sales reps. 10 skills · 1 agent · 2 commands · 4 hooks.

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
voice skills (including `bbs-deck-voice`, the federal slide-copy voice standard), managed
settings, the AUP, `/bbs-checkup`.
**Does not own:** any desk's workflow. 3 skills · 3 commands · 1 hook.

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
| 7 | Real-packet test of the OBS 4007(B) path (`ca-form-filler` Path A) | Parker | Validated against synthetic stubs only; the Rev. 08/2025 blank packet isn't in the repo. Run `--inspect` on a real one before a rep relies on it. |
| 8 | ~~Canonical model IDs are stale~~ | — | **Fixed 2026-09-15, in two halves.** PR #11 fixed the source: `references/models.json` is now the one list, generated from the API by `refresh_models.py` and read by the checker, which no longer carries its own copy. What that PR did not reach was the propagation: **9 live files still named `claude-opus-4-8` as current**, including `bbs-foundations/hooks/skill-bus.json` (injected into every skill run) and `bbs-managed-settings.json` (the company-wide CLAUDE.md on every machine), so the stale value was still being broadcast from a repo whose canonical file was already correct. Those 9 are fixed here. **Parker must re-paste the managed settings** (`ADMIN-RUNBOOK` §1) for it to reach machines — the repo edit alone changes nothing on a rep's PC. |

---

## 5. For the next session — run it against the practices, not the diff

The work above is merged. What matters now is whether the marketplace holds up as a way of
working for a small team, so the next session should audit it against the practices that
make skills and plugins actually land in a business this size. Each one below is paired
with what this repo already does and the specific gap left.

### A skill is found by its description — measured, then consolidated

The handoff predicted the Grainger cluster would collide: `grainger-cart-info`,
`grainger-screenshot`, `dwr-pdf-info`, `dgs-bpo-item-check`, `bbs-b2b-pricing`. **It did
not.** All five routed 5/5 in every condition. `skill-creator`'s `run_eval.py` could not
have shown that — it registers one description and asks "did it fire?", which cannot say
which sibling won. `docs/evals/discriminate.py` registers every installed description at
once in an isolated project root and records which skill was actually invoked.

Description-only routing started at 18/20. The two real defects were elsewhere:
`naspo-quote` lost 40% of its runs to `ca-rfq-intake`, and `dwr-pdf-info` missed the bare
acronym "DWR". The finding that paid was on deliberately ambiguous queries, where the
baseline silently ran the **wrong** skill — "check these Grainger items" ran pricing 4/5,
"pull the Grainger numbers out of items.pdf" ran the cart skill 3/5. Reciprocal
"...or ask which" clauses turned those into questions.

**Then Parker called the consolidation**, and the overlap that mattered was a different
cut from the predicted one: skills doing **one job through different front doors**.

- `grainger-cart-info` + `grainger-screenshot` + `dwr-pdf-info` → **`rfq-item-extract`**.
  One job — get the items out of what the agency sent — behind three input formats.
- `ca-form-filler` + `obs-form-filler` → **`ca-form-filler`**, with the CDCR OBS 4007(B)
  packet as its scripted Path A and everything else as Path B. They were already
  entangled: `ca-form-filler` called `obs-form-filler`'s inspector.
- `bbs-b2b-pricing` → **`grainger-pricing`**, routed through the Grainger MCP. The MCP
  describes itself as the punch-out's replacement, and it carries two rules the old skill
  never stated: pricing is **per-account** (the wrong account returns a wrong price that
  still looks valid), and BBS **sells Grainger at cost** — `unitPrice` is the customer
  price, never marked up, because BBS is paid through a contract rebate.

`dgs-bpo-item-check` and `grainger-pricing` were left separate: they share an *input* (a
list of part numbers) but answer different questions, and they route 5/5 apart.

bbs-sales went 14 skills → 10. Description-only routing is **24/24**.

**What the merges surfaced, which is the real argument for doing them.** Consolidating
forced the divergent copies into one place, and they disagreed:

- `ca-form-filler` named **two form IDs that do not exist** in the shared rules —
  `GSPD-05-106` (it is GSPD-05-105) and `STD 1000` (it is OBS 1000). Both would have gone
  onto binding bids.
- Its field maps read **seven vendor-profile keys that are not there** —
  `dvbe_details.*`, `rep.full_name`, `cuf_statement`, `broker_or_agent`, `uses_genai` —
  so those fields silently produced nothing.
- It loaded the vendor profile from `~/.bbs/vendor_profile.json`, the per-machine copy the
  single-source rule exists to prevent.
- `bbs-order-reconciliation`'s description was 1,155 characters against a 1,024 limit, so
  it was truncated **exactly through its entire "Do NOT use for" clause**.

None of those were visible while the duplicates sat in separate files.

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
