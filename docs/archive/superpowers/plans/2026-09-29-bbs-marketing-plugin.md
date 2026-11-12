# bbs-marketing plugin — integration plan

> **Status:** Parker said go on 2026-09-29. Phases 1–3 are the plugin in this branch.
> Phase 4 (desk `CLAUDE.md` pointer) waits until this plugin is on `main`, so the desk
> does not lose its rules while the plugin is only on a branch. Phase 5 (`grainger-promo-page`
> move) stays a separate pull request. A session ends at a pull request. The agent that
> wrote the change does not approve it.

**Goal:** Give reps one marketplace plugin, `bbs-marketing`, for marketing material: one-page sales pieces, email drafts, supplier and customer marks, and prior decks and brochures. The plugin lives in `bbs-claude-marketplace` and follows the same plugin shape as `bbs-sales`. The way a piece is made follows Interpretable Context Methodology (ICM), arXiv:2603.16021v2.

**Architecture:** The plugin is the factory. The SharePoint folder is the desk. Skills are stage contracts. A run writes plain files a rep can open and edit before the next stage. `brand_check.py` is the mechanical gate. Facts stay in one registry. Finished programs, priced catalogs, and binary marks stay on the desk.

**Grounding, verified 2026-09-29:**

| Source | What it actually is |
|---|---|
| `MARKETING/bbs-marketing/` | Local git repo on the SharePoint desk. No GitHub remote. Brand registry, rights ledger, `brand_check.py`, and six real program folders. `templates/`, `company/`, and `archive/` are empty. `CLAUDE.md` still says `programs/` holds only a `_TEMPLATE`. |
| `MARKETING/claude-marketing/joey-marketing/` | Joey's `csu-marketing` skill. Its own `CLAUDE.md` says live work moved to `bbs-marketing` and this kit is read-only. Paths inside the skill still point at a retired `claude-csu/` tree. |
| `plugins/bbs-sales/skills/grainger-promo-page/` | The live promo-page skill. A second copy sits in `bbs-marketing/.claude/skills/bbs-grainger-promo-page/`. |
| `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md` § Marketing desk | Already calls for a `bbs-marketing` plugin, a root `CLAUDE.md`, Joey's skill as the seed, and moving `grainger-promo-page` in v1.1. |
| ICM paper, §3.1–3.3 | Five principles and a five-layer folder. Sequential, human-reviewed, repeatable work. Local scripts for the parts that are not judgment. |

## What a rep can do when this ships

| Job | Where they start | What they get |
|---|---|---|
| Make a one-page sales piece | "One-pager for Sonoma State's procurement office." | Intake brief, copy they can edit, print-ready PDF, gate output in the program README |
| Make a leave-behind, sell sheet, punchout card, or line card | Same skill, piece type named in the intake | Same staged folder, track chosen from the request |
| Draft a campaign email | "Email the CAL FIRE buyers who purchase Grainger direct." | A draft in the program folder. A person sends it |
| Use a supplier, campus, or co-brand mark | "Can I put the DeWalt logo on this?" | A yes/no from the rights ledger, and the file copied into the program only when the row allows it |
| Look up an older deck or brochure | "What did we send UC?" | A short precedent note pointing at the file in `MARKETING/`. The file stays where it is |

## ICM, applied to this repo

The paper's claim is that a sequential, human-reviewed workflow does not need a multi-agent framework. Numbered folders and markdown contracts do the orchestration. One agent reads the files for the current stage. A person edits the file before the next stage runs.

Five principles, and where each one lands:

1. **One stage, one job.** Joey's `csu-marketing` skill interviews, gathers logos, picks a layout, writes copy, builds HTML, and reviews the PDF in one pass. Split that into skills that stop. Intake stops when the brief is written. Copy stops when the draft is on disk. Render runs only after the rep has had the draft.
2. **Plain text as the interface.** Intake, copy, and the gate log are markdown. HTML is the render source. PDF is the handoff, produced by a script, and the gate audits extracted text, which the current `CLAUDE.md` already requires.
3. **Layered context loading.** A stage names the files it reads. A one-pager does not load the public-safety track, the promo-page scripts, and every old brochure.
4. **Every output is an edit surface.** The rep edits `01-intake` and `02-copy` in the program folder. The next stage reads whatever they left there.
5. **Configure the factory, not the product.** Voice, claims, tracks, and templates are configured once in the plugin. Each program folder is a new product from that factory.

Five layers, mapped onto the marketplace:

| ICM layer | Question | Home |
|---|---|---|
| 0 | Where am I? | `plugins/bbs-marketing/CLAUDE.md` — identity and where to go next. Short. |
| 1 | Which job? | `plugins/bbs-marketing/CONTEXT.md` — request to skill. |
| 2 | What does this stage read, do, and write? | Each skill's `SKILL.md`. That file is the stage contract. |
| 3 | What rules apply on every run? | `plugins/bbs-marketing/references/` — the brand factory. |
| 4 | What is this run? | `MARKETING/bbs-marketing/programs/YYYY-MM-DD-slug/` on the desk. |

ICM and the marketplace disagree in one place, and the split is deliberate. ICM would put the whole workspace, including stage instructions, in one folder the rep copies around. This repo's rule is that skills ship from git and update on push, and that a fact lives in one file. So Layer 0–3 live in the plugin. Layer 4 lives on the desk, next to the logos and the finished pieces. The skill tells the agent which Layer 3 files to open for this stage. It does not paste those files into the skill.

A program run looks like this:

```text
programs/YYYY-MM-DD-short-slug/
  README.md                      track, tier, approved-by, gate output
  01-intake/CONTEXT.md           copied from the skill's stage contract
  01-intake/output/brief.md      rep edits this
  02-copy/output/copy.md         rep edits this
  03-render/output/piece.html
  03-render/output/piece.pdf
  GATE.txt                       pasted brand_check output
```

The numbering is the pipeline. Skipping a stage means the next stage's inputs are missing, and the skill stops.

## What moves, and what stays

**Into the plugin (the factory).**

- Brand markdown: `core.md`, `CLAIMS.md`, `VOICE.md`, `MESSAGING.md`, `AUDIENCES.md`, `COMPLIANCE.md`, `SOURCES.md`, `tracks/ROUTING.md`, `tracks/mro-procurement.md`, `tracks/public-safety.md`, `assets/ASSETS.md`.
- The gate: `tools/brand_check.py`, `tools/README.md`, `tools/tests/`.
- New skills and one HTML template promoted out of a finished piece.
- `plugin.json`, `README.md`, `CLAUDE.md`, `CONTEXT.md`, one command.

**Stay on the SharePoint desk (the product and the binaries).**

- Every folder under `programs/`. Those hold finished pieces, priced hot lists, catalog JSON, and campaign email drafts. Prices in those files are not re-typed into the plugin.
- `brand/assets/logos/`, `brand/assets/fonts/`, `brand/assets/hero/`. About 3.8 MB. The rights ledger moves; the files stay, because most manufacturer and campus rows are `NEEDS CONFIRMATION` or `NEEDS WRITTEN CONFIRMATION`, and the supplier-logo folder also contains an invoice PDF and a helmets PDF that do not belong in the marketplace.
- `brand/sources/*.pdf`. `SOURCES.md` is the trace table and moves. The PDFs stay with the rest of the marketing archive.
- Sibling marketing material the plugin only points at: `MARKETING/Brochures/`, `MARKETING/Marketing Archive/` (pitch decks and the 2017 email templates), `MARKETING/Brand Style Guide/`, `MARKETING/BBS Logo/`.

**Retire in place, after the plugin is the path reps actually use.**

- `claude-marketing/joey-marketing/` stays read-only. Do not revive its symlink into `~/.claude/skills`.
- The copy of `grainger-promo-page` inside `bbs-marketing/.claude/skills/` is a duplicate of the sales plugin. Delete that copy when the desk `CLAUDE.md` becomes a pointer. Do not keep a third copy.
- `.bak` files, `.claude/settings.local.json`, pytest cache, and Playwright logs do not move.

After cutover, the desk `CLAUDE.md` becomes a pointer: this folder is the run archive and the asset desk; the factory is the plugin. The long rule list lives in the plugin once. The desk file lists the real program folders, which the current `CLAUDE.md` does not.

## Plugin shape

Match `plugins/bbs-sales/`:

```text
plugins/bbs-marketing/
  .claude-plugin/plugin.json
  README.md
  CLAUDE.md
  CONTEXT.md
  references/                  # Layer 3, moved from brand/
    CLAIMS.md
    VOICE.md
    MESSAGING.md
    AUDIENCES.md
    COMPLIANCE.md
    SOURCES.md
    core.md
    ASSETS.md
    tracks/
      ROUTING.md
      mro-procurement.md
      public-safety.md
  tools/
    brand_check.py
    tests/
  skills/
    marketing-intake/SKILL.md
    sales-one-pager/SKILL.md
      references/stage-contracts.md
      assets/onepager.template.html
    campaign-email/SKILL.md
    marketing-assets/SKILL.md
    deck-precedent/SKILL.md
  commands/
    bbs-one-pager.md
```

Register it in `.claude-plugin/marketplace.json` with `source: "./plugins/bbs-marketing"` and `category: "sales"`. Add a row to `.claude-plugin/PLUGINS.md`, the plugin table in the root `README.md`, and `REGISTRY.md`.

`plugin.json` follows `bbs-sales`: `name`, `description`, `version`, `author.name` = `Black Box Safety, Inc.`, `keywords`, `skills: "./skills/"`.

Skill rules the checker already enforces:

- Folder name matches frontmatter `name:`.
- Quote a `description:` that contains a colon, or use `>-`.
- Keep each description under 1024 characters, and put the "do not use" clause where truncation cannot eat it.
- Resolve plugin files as `${CLAUDE_PLUGIN_ROOT}/...`. No `/Users/...` path and no `~/.bbs/` copy of the claims registry.
- A README skill-count badge must equal the number of `SKILL.md` files. Start at 5.

`python3 scripts/check_marketplace.py` must exit 0. The root README badge currently says three BBS plugins; `marketplace.json` already lists four local plugins (`bbs-website`, `bbs-sales`, `bbs-back-office`, `bbs-foundations`). Adding this plugin makes five local plugins plus the five pinned externals. Update that badge in the same PR. The checker warns if a plugin directory is missing from `marketplace.json`; it does not check the root plugin-count badge, so the PR review has to.

## Skills

Generalize Joey's workflow off Joey-the-person and off the CSU/Grainger-only kit. The interview, the wedge, the partnership framing, and the HTML-to-PDF build are the parts worth keeping. The contract numbers in `joey-marketing`'s knowledge file are not. Those sentences already disagree with the "one registry" rule, because `brand/CLAIMS.md` is the wording source.

Merge on the job. A one-pager and a promo page both end up as a page a buyer sees, and they stay separate skills: one is a print piece from approved claims, the other is a priced hot-list landing page.

### `marketing-intake`

Fires when someone asks for a piece and no program folder exists yet.

Reads: `CONTEXT.md`, `references/AUDIENCES.md`, `references/tracks/ROUTING.md`, the claims index in `references/CLAIMS.md`.

Does: asks who it is for, the single ask, the account, the piece type, where it will be seen, and which facts it needs. Picks one track (`mro-procurement`, `public-safety`, or `bridge`). Checks each fact against `CLAIMS.md` before any headline exists. Writes the program folder and `01-intake/output/brief.md`. Sets tier A or tier B from `COMPLIANCE.md` §9.

Stops. Does not write copy. A missing claim is `NEEDS CLAIM: <description>` in the brief.

### `sales-one-pager`

Fires when the brief exists and the piece type is a capability one-pager, leave-behind, sell sheet, punchout switch card, or line card.

Reads: the brief (Layer 4), one track file, `VOICE.md`, `MESSAGING.md`, `COMPLIANCE.md`, and the block notes in the skill. A bridge piece reads both track files. It does not load the other track "just in case."

Does, as separate stage files:

1. Draft `02-copy/output/copy.md` from the brief. Stop for the rep.
2. After the copy file is in place, fill `assets/onepager.template.html` and render HTML, then PDF.
3. Run `brand_check.py` on the extracted text. Paste the output into `GATE.txt` and the README. A finding stops the handoff.

Seed the template from `programs/2026-08-13-uc-irvine-capability-onepager/` for the one-page shape, and from `joey-marketing`'s brochure template only for blocks that piece does not already have (stat band, comparison, QR). The UC Irvine README is the worked example of a brief that changed the argument: the ask was an additional punchout tile, so the parity wedge was the wrong hero. The skill's stage contract should say to follow the brief's ask, including when the ask is not "same catalog, now it counts."

`approved-by:` with a name and a date is required before render on tier B. A pending approval is a stop.

### `campaign-email`

Fires for an outbound email: win-back, switch, or internal announcement.

Reads: the brief, `VOICE.md`, and one template in the skill. The CAL FIRE H2 segment emails stay on the desk as the worked example the skill points at.

Writes one draft. Does not send. Outlook coverage is the mailbox signed into the machine.

### `marketing-assets`

Fires when a piece needs a logo.

Reads: `references/ASSETS.md` and the logo directory on the desk.

Writes: a one-line rights decision, and a copy of the file into the program folder when the row allows the use. No row means the mark is not used. `NEEDS CONFIRMATION` means the mark waits. Customer marks on an external piece need the written-confirmation state the ledger already names. The UC Irvine decline recorded in the ledger stays a decline.

The skill resolves the desk relative to the workspace the rep has open. It does not hardcode a OneDrive path.

### `deck-precedent`

Fires when someone asks what we have already made: a brochure, a capability statement, a pitch deck, a line card.

Reads: a short index the skill ships (path, date, audience, track) covering `MARKETING/Brochures/` and the pitch decks in `MARKETING/Marketing Archive/`. The index is a pointer list. Opening a deck is a desk read.

Writes: a precedent note in the program folder, or in chat when there is no active program. Federal slide copy is `bbs-deck-voice` in `bbs-foundations`. This skill does not write SDVOSB deck copy and does not assemble a new PowerPoint. A CA sales-deck builder is a later skill, after a template exists that has passed the gate.

### Command

`/bbs-one-pager` runs `marketing-intake` and tells the rep the brief is waiting. It does not continue into copy.

### `grainger-promo-page`, later

The 2026-09-11 design already places this move in v1.1. Leave the skill in `bbs-sales` for the first PR. `CONTEXT.md` routes "promo page", "hot list", and "campaign page" to `bbs-sales:grainger-promo-page` by name. A follow-up PR moves the skill, updates the sales README badge (the checker will fail if the badge is left at 10), and leaves a sentence in the sales README pointing at the new home. Promo pages stay a different job from one-pagers.

## Rules that ride along

These are already true in the marketplace. The plugin points at them. It does not re-key them.

- Unknown price, stock, lead time, cert, or contract fact is `[FLAG: why]` or `NEEDS CLAIM:`. `CLAIMS.md` is the only approved wording for a marketing piece. `plugins/bbs-sales/references/vendor_profile.json` remains the only source for values that go on a state form. If a marketing claim and the vendor profile disagree, flag it. Do not pick a winner inside a skill.
- Certification language follows the channel. A California piece uses the DVBE wording in `CLAIMS.md`. A federal or prime piece uses SDVOSB, via `bbs-deck-voice`. One piece carries one channel. `SB/DVBE` is superseded wording.
- CSU, UC, and body armor are in this plugin because that is Joey's marketing work. They stay out of the Kim/Aanya quote book. This plugin does not create buyer folders under `Customers/State of CA Agencies/` and does not run `ca-rfq-intake`.
- One track per piece. `ROUTING.md` is the test. Public-safety equipment sold on an MRO vehicle is an `mro-procurement` piece.
- No third-party mark without a ledger row. No implied agency endorsement. When a piece names an agency, the agency-disclaimer wording and `--scope agency` apply.
- Humans send. Tier A is the rep shipping a piece assembled from existing blocks, existing claims, and a green gate. Tier B is a named person and a date in the README before render.
- Draft only. Do not add a send-capable tool to this plugin.

## Build order

Each phase is its own branch and its own PR.

**Phase 1 — skeleton and factory.** Create the plugin directory, `plugin.json`, README, Layer 0 and Layer 1 files. Move the brand markdown and `brand_check.py` with tests. Fix internal links from `brand/` to `references/`. Register the plugin. Run the checker and the brand-check tests. The desk copies stay until Phase 4 so in-flight programs do not break. This phase ships no skills yet; the README badge stays off until skills exist, or the badge says 0 and the checker is taught that 0 is honest. Prefer landing Phase 1 and Phase 2 in one PR if the diff is still reviewable, so the plugin is not an empty shell on `main`.

**Phase 2 — intake and one-pager.** Add `marketing-intake` and `sales-one-pager`, the template, and `/bbs-one-pager`. Prove it by rebuilding the UC Irvine capability one-pager from its README into a new program folder and showing the gate output. Do not overwrite the 2026-08-13 piece.

**Phase 3 — assets, email, precedents.** Add the three lookup-and-draft skills and the brochure/deck index. Confirm a `NEEDS CONFIRMATION` manufacturer mark is refused, and a BBS-owned mark is copied.

**Phase 4 — desk pointer.** Replace the long desk `CLAUDE.md` with a pointer. Update `START-HERE.md` so a rep opens the marketplace plugin, not a OneDrive-only skill. Remove the duplicate promo-page skill from the desk. Leave `joey-marketing` read-only with its "this kit has moved" banner.

**Phase 5 — move `grainger-promo-page`.** Separate PR. Sales badge, sales README, marketplace description, and any skill-bus subscription move together.

## Acceptance

- `python3 scripts/check_marketplace.py` exits 0.
- `brand_check.py` tests pass from the plugin path.
- A cold session given "one-pager for a campus procurement office" creates a program folder, writes a brief, and stops.
- Given an approved brief, the one-pager skill writes copy, waits, then renders, and refuses to hand off on a red gate.
- A request for a campus logo with `NEEDS WRITTEN CONFIRMATION` does not place that file on the piece.
- No price, cert number, or contract number is introduced in a skill file. Wording is read from `references/CLAIMS.md`.
- Descriptions load (quoted colons, under 1024 characters, folder name matches `name:`).

## Out of scope for this plan

Sending email, deploying a promo page, writing Business Central, renaming customer folders, building a new PowerPoint generator, confirming the open rows in the rights ledger, and copying priced `hotlist.json` or `catalog.json` into git.
