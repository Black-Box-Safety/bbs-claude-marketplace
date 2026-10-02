# Session handoff — 2026-10-01 (team-rollout page)

Closes the session that built the team-rollout page. Rulings and open asks live in
`docs/STEWARD.md` (the register, entries dated 2026-10-01 under *Already open for Parker*).
This file records what shipped, what needs a person, and where the next session starts.

---

## 1. What shipped (PR #46)

| Change | Where |
|---|---|
| The BBS Claude Toolkit page: one data-driven page. Opening it with a person's name in the address (`#summer`) or tapping a name puts that person's week first. Honest status chips, verbatim copy from the build prompt | `docs/explainers/2026-10-01-team-rollout/bbs-claude-toolkit.html`, published privately as an Artifact (link with Parker) |
| Sales added beyond the prompt: one shared card for Kim, Aanya, Joey and Griffin; supplier-scout row; Griffin's federal deck row; SAM.gov as Coming next for Kim and Griffin | same file; register entry "The team-rollout page covers Sales" |
| Two citation fixes from the PR #45 review (G3 hierarchy line; grounding row 15 rests on read-only tools, not the allow list) | `brief.md`, `IMPLEMENTATION-PROMPT.md` |
| Coach jobs map: AR and accounting rows; supplier options split from Chrome research | `plugins/bbs-claude-coach/skills/bbs-claude-coach/references/jobs-map.md` |
| Cloud-session note for installing `impeccable`, and where explainer pages live | `CLAUDE.md` |

Acceptance results for all 14 checks are in the PR description and its two update comments.

## 2. How the page is built (for whoever edits it next)

- **Everything person-specific is in two objects at the top of the script.** `PEOPLE` holds
  each person's slug, name, group, picker line and card. `CARDS` holds each card's rows,
  statuses, note and Coming next items. Removing a person means deleting one `PEOPLE` entry.
  A shared card lists its people in `sharedBy`.
- **A row or Coming next item can carry `for: [slugs]`.** It then shows only on those
  people's view, and in the all-roles view it carries a "For …" tag. Griffin's deck row and
  the SAM.gov item use it.
- **Statuses:**
  - `ready` means Ready today.
  - `list` means On Parker's list; the row carries its `reason`, with no "Try saying" line
    and no copy button.
  - Coming next items are always Not built yet.
  - Every status comes from the playbook's `requires:` line (`python3 scripts/check_marketplace.py --requirements`).
- **Text checks.** The prompt's acceptance greps (§8) run against the source file:
  - The file must not contain `transform` or a `$` followed by a digit; both trip the
    voice and number greps.
  - Every sentence that says read-only, never sends or cannot send must name Business
    Central, Grainger or Claude Code on the same line.
- **Preview locally:** wrap the file in a minimal `<html><body>`, put `bbs_logo.png` beside it
  and load it in Playwright (Chromium is at `/opt/pw-browsers`). Republish with the Artifact
  tool from the same file path to keep the URL.

## 3. Needs Parker (no repo change does these)

1. **PR #46 is merged.** The signature wording was simplified afterwards at Parker's direction
   (register: "Team-rollout page, signature wording — RULED 2026-10-02").
2. **File signature PNGs for Kim, Aanya, Joey and Griffin.** The page tells them Claude signs
   their sales packets once Parker has their signature on file; until then every one of their
   lines comes back flagged (`vendor_profile.json`, `signature_image` is null for all four).
3. **Confirm or replace Joey's picker line** ("Customer accounts and quotes").
4. **Share the page** from its Share menu when ready; the build session cannot share it.
5. The build prompt's open questions, still unanswered:
   - Include Joyce Newell?
   - `/bbs-checkup` check 6 (desk folder) fails for the non-quote-desk readers; make it role-aware or warn them.
   - Confirm each reader has Business Central, Microsoft 365 and Grainger assigned, and the customer folders synced.
   - Is Gap 4 (Shopify card-paid invoices showing unpaid) fixed? Until it is, Summer's caveat stays.
   - Has the test send been denied in both VS Code and the Desktop app's Claude Code (ADMIN-RUNBOOK §1)?
   - When the interim Business Central connector is swapped for Microsoft's, re-check that it is read-only.

## 4. Where the next session starts

Deferred by Parker ("we will do that separately"):

1. **A SAM.gov opportunities skill** for Kim and Griffin. It is a narrow, read-only lookup of
   open solicitations by NAICS code or agency through the official Get Opportunities API. The
   key goes in `SAM_GOV_API_KEY` in each person's environment, never in git (`README.md`
   connector table already says this; it also says not to add a 150-tool government bundle).
   - Declare it in the skill's `requires:`.
   - Register the system in `check_marketplace.py`. That is review-side, so it goes in its
     own PR.
   - When it ships, move the SAM.gov item from Coming next to a Ready row on the Sales card.
2. **A general web-research agent.** `supplier-scout` only researches suppliers for one line
   item. A general agent on built-in `WebSearch`/`WebFetch` (no connector) for an agency, a
   competitor or a regulation needs the same rule: a number counts only from a page it
   fetched, with URL and date.
   - Write, Edit and Bash disallowed, like `supplier-scout`.
   - Add a jobs-map row and a page row when it ships.
3. **Shopify rows in the coach jobs map** (Emily's work). Shopify admin is Parker and Griffin
   only, so most of it is Not built yet; route rather than promise.
4. **`impeccable` v4.4.0 is available.** The pin is v4.3.1; updating it is `commons-curator`'s
   job, not a side effect of design work.

## 5. Notes for the agent doing that work

- **`impeccable` is not installed in a fresh cloud container.** `CLAUDE.md`, "Design work in a
  cloud session", has the five commands.
- **Its static `detect` reports false low-contrast hits on a two-theme page.** Measured in a
  real browser, the page's lowest text contrast is 6.4:1 (light) and 7.68:1 (dark).
- **Rex (`.claude/agents/rex.md`) reviews and merges, but only when dispatched from a session that did not write the PR;** the build session never merges.
- **Run both checkers before pushing:** `scripts/check_marketplace.py` and `plugins/bbs-foundations/skills/bbs-claude-md-forge/scripts/check_claude_md.py "$PWD"`. CI runs both, and the second reads any `claude-…` token in a CLAUDE.md (a `.claude-plugin/` path included) as a model ID.
- **Record in-session rulings in the same PR.** Rex checks rulings against the register in
  `docs/STEWARD.md`, so a ruling a PR relies on goes into the register in that PR.

---

Owner: Parker Marshall. Last verified 2026-10-02.
