<!--
One slice per PR. Base is `main` unless this PR is stacked; if it is stacked, name the PR
under it and retarget to `main` the moment that one merges.
Rules this template points at, not restates: AGENTS.md (invariants), docs/MAINTAINER-GUIDE.md
§3 (review questions) and §4 "Branches and versions".
-->

## What

<!-- The change, in plain words. Name each plugin touched. -->

## Why

<!-- The problem, or the ruling. A ruling cites who and when (e.g. "Parker, in session,
2026-10-16") and is recorded in the rulings register in docs/STEWARD.md. -->

## Versions

| Plugin | From | To |
|---|---|---|
| | | |

<!-- Every plugin whose files this PR changes gets a version bump in its own
`.claude-plugin/plugin.json`, or installed machines never receive the change. Before
picking a number, check the open PRs for one that already claims it. Write "none" when
only repo files (docs/, scripts/, .github/) changed. -->

## Checked

- [ ] `python3 scripts/check_marketplace.py` exits 0 (WARNs triaged)
- [ ] `claude plugin validate .` passes
- [ ] Hook parity, if a `.ps1`/`.py` pair changed (both halves run, not one)
- [ ] Routing eval re-run, if any skill `description:` changed
- [ ] No binding fact (price, cert, form ID, signer, contract number) typed from memory

## Not checked

<!-- What you could not run here, and why. "Nothing" is a claim; make it only if true. -->
