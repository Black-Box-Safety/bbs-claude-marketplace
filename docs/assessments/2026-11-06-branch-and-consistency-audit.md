# Branch and consistency audit — 2026-11-06

Steward assessment of `Black-Box-Safety/bbs-claude-marketplace`: branches, open PRs, and
whether the marketplace follows Anthropic's marketplace and plugin guidance. Read-only
except for the PR that carries this file. Every close, delete, merge and settings change
below is **Parker's call**; this file recommends, it does not act.

> **Update, 2026-11-06, after PR #79 opened.** Parker closed #67. Deleting the eight
> merged branches in §1 was refused from the steward session (the session's git proxy
> allows pushes only to its own branch); delete them in the GitHub UI. Rows below are as
> first audited.

## Bottom line

`main` is healthy: `check_marketplace.py` 0 FAIL, `claude plugin validate .` passes. The
risk is in the queue: 11 open PRs, of which **two pairs duplicate each other, three claim
the same `bbs-sales 0.8.0`, one is orphaned on a merged base, and one is five weeks stale
with conflicts.** Eight merged branches were never deleted. `main` is not protected.

## 1. Branches with no open PR (9)

| Branch | State | Recommendation |
|---|---|---|
| `bc-item-entry` | merged as #64 | Delete **after** #67 is closed (it is #67's base) |
| `claude/daily-sales-summary-prompt-rpx0to` | merged as #69 | Delete |
| `claude/magical-brahmagupta-nrh3f9-mac-hooks` | merged as #61 | Delete |
| `claude/magical-brahmagupta-nrh3f9-mac-hooks-followup` | merged as #62 | Delete |
| `claude/magical-brahmagupta-nrh3f9-version-bumps` | merged as #60 | Delete |
| `feat/agent-team-plugin` | merged as #63 | Delete |
| `fix/bbs-tools-0.2.1-version-bump` | merged as #70 | Delete |
| `fix/claudeforge-2.1.1` | merged as #65 | Delete |
| `wip/ca-weekly-rep-review` | 1 commit, 2026-09-28, 41 behind `main`. Its own commit message says it holds **real data, "scrub before merge"** | **Delete now.** The weekly report shipped as `bbs-weekly-sales-report`; the branch's only remaining effect is real customer data sitting in GitHub. Contents were not opened for this audit |

## 2. Open PRs (11)

| PR | Branch | Finding | Recommendation |
|---|---|---|---|
| #67 | `docs/bc-quote-best-practice` | Based on `bc-item-entry`, which merged as #64. Both of its commits are already inside #68 | **Close as superseded by #68** |
| #68 | `bc-quote-entry` | Clean against `main`. Claims `bbs-sales 0.8.0`. Conflicts with #75. Changes `bbs-tools/bin/bbs-fill` and `bbs-foundations` (`canonical-facts.md`, `MANAGED-SETTINGS.md`) **with no bbs-tools or bbs-foundations bump**, so the `bc_quote_entry.py` allow-list entry would not reach installed machines (the #70 failure) | Add both bumps, then review and merge first of the three 0.8.0 PRs |
| #75 | `feat/buyer-outcome-loop` | Draft. Claims `bbs-sales 0.8.0`. Conflicts with #68 and #77 (`hooks.json`, `parity.py`) | After #68 merges, merge `main` into the branch; take `0.9.0` |
| #77 | `rfq-record-v2` | Draft. Claims `bbs-sales 0.8.0`. PowerShell twin never executed | After #75 merges, merge `main` into the branch; take the next minor; CI's `pwsh` parity step must run green |
| #71 | `commons/taste-skill` | Pins taste-skill **and** makes both bootstraps skip `maintainer` entries (Parker, option (a), 2026-10-28) | Keep one of #71/#78 — see below |
| #78 | `feat/commons-taste-skill` | Pins the same taste-skill v2.1.5, **without** the bootstrap skip. Conflicts with #71 | Without #71's bootstrap change, `bbs-setup.*` installs every catalog entry, so #78 alone ships a maintainer-tier tool to rep machines. **Parker: pick one.** Recommended: keep #71, fold #78's wording fixes into it, close #78 |
| #73 | `claude/magical-hypatia-ebi8ye` | Creates `bbs-sourcing/references/email-templates.md` (187 lines) and a voice-template signature step. **No version bump** on bbs-sales or bbs-foundations | Two PRs create the same file differently; conflict with #74 |
| #74 | `claude/confident-hamilton-pxqaxy` | Creates the same file (300 lines, placeholder shells) plus a house email format. Bumps bbs-sales 0.7.1 and bbs-foundations 0.3.1 | **Parker: pick one file.** Recommended: #74 (it carries the bumps and the 2026-10-30 format ruling); move #73's signature-template work onto it, or cut #73 down to only that on a new branch from `main` |
| #72 | `feat/forge-customer-folder-claude-md` | Draft. Clean. bbs-foundations 0.4.0 | Collides with #74's 0.3.1 only in order; whichever merges second merges `main` in and re-bumps |
| #76 | `fix/forge-checker-path-segment` | Draft, one-file checker fix, clean. Touches `check_claude_md.py` with **no bbs-foundations bump**, so reps keep the false FAILs | Add the patch bump, mark ready, review |
| #53 | `claude/upbeat-shannon-6tlvbb` | 2026-10-02, 13 behind, **conflicts with `main`** (managed settings changed in #55/#58 since) | Parker: still wanted? If yes, merge `main` into it and resolve; if the connector-access ruling already landed elsewhere, close |

**Suggested merge order:** #67 close → #76 → #68 → #74 (or #73) → #72 → #71 (or #78) →
#75 → #77 → #53 (or close). Each later PR merges `main` into its branch and re-bumps after
the one before it. Never rebase a pushed branch: landing it needs a force-push, which
managed settings deny.

## 3. Marketplace consistency against Anthropic's guidance

Sources: <https://code.claude.com/docs/en/plugins/host-marketplace.md> and
<https://code.claude.com/docs/en/plugins/marketplace-reference.md>, read 2026-11-06;
`claude plugin validate` 2.1.319 run on this checkout.

| Finding | Evidence | Status |
|---|---|---|
| Entry display fields override `plugin.json`, and seven of eight had drifted | `bbs-foundations` entry still advertised order reconciliation, which moved to `bbs-back-office`; `bbs-sales` entry carried keyword `sb-dvbe` (BBS is not a California small business) and omitted the federal lookups | **Fixed in this PR**: relative-path entries carry only `name`, `source`, `category`; `plugin.json` is the one source |
| Changed plugins are not always bumped | #60 and #70 were bump-only follow-ups; #73 and #76 are open without bumps | Rule added to MAINTAINER-GUIDE §4 and the new PR template. A mechanical check (plugin dir changed ⇒ version changed) belongs to the review side's `check_marketplace.py` |
| `claude plugin validate` was not in CI | — | **Added in this PR**, pinned to 2.1.319, blocking on errors |
| `plugins/bbs-marketing/CLAUDE.md` is never loaded | Validator: "CLAUDE.md at the plugin root is not loaded as project context". Its rules ("NEEDS CLAIM", "does not send email") therefore reach no rep session unless a skill reads the file | **Open.** bbs-marketing owner: have `marketing-intake` read it explicitly (as it already reads `CONTEXT.md`), or move the rules into the skills |
| `bbs-claude-coach` name "reads as one of Anthropic's own" | Validator warning | Leave. Renaming breaks every install; the warning does not block |
| `bbs-tools` ships a top-level `bin/` | Docs: claude.ai **organization sync** rejects a plugin with a top-level `bin/` | No action while distribution is managed settings + git. If Parker moves to Organization settings → Plugins, this plugin will not sync |
| No `LICENSE`, no icons | Validator directory-profile checks | Not applicable: these gate submission to Anthropic's public directory, not a private marketplace |
| `version` set only in `plugin.json` for local plugins; externals pinned by `ref`/`sha` | Matches the docs | Correct as is |
| No `renames` map | None needed yet | Rule added: any removal or rename appends one |

## 4. Repository settings (Parker, GitHub UI)

1. **Protect `main`** (Settings → Branches): require a PR, require the `invariants`
   status check, block force-push. `list_branches` reports `main` unprotected today,
   although AGENTS.md assumes it is.
2. **Automatically delete head branches** (Settings → General). Removes the eight-branch
   backlog from ever recurring.
3. Do **not** add a CODEOWNERS file with a single owner who also authors every PR: GitHub
   does not let an author approve their own PR, so "require code owner review" would
   block every merge. Rex's COMMENT-review flow is the review gate.

## 5. Deferred on purpose

- **`docs/STEWARD.md` is 860 lines** and mixes the operating loop, slice plans from
  September ("Tonight's slices", PR #12) and the rulings register. Splitting it now would
  conflict with five open PRs that edit it. Split once the queue in §2 drains: the loop
  stays in STEWARD.md, rulings move to `docs/RULINGS.md`, finished slices are deleted.
- Three `docs/SESSION-HANDOFF-*.md` files and a root `HANDOFF.md` overlap. Fold into one
  handoff once the personal-copy cutover in `HANDOFF.md` is done.

---

Owner: Parker Marshall. Prepared by the steward session, 2026-11-06.
