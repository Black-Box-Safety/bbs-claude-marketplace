# Session handoff — 2026-09-28

Closes the steward session of 2026-09-28. The rulings themselves live in
`docs/STEWARD.md` (the register) and in `canonical-facts.md` ("Rulings on binding
documents"). This file records what shipped, what needs a person, and where the next
session starts. It does not restate any ruling.

`main` at close: `a583956`. `check_marketplace.py`: 34 skills · 0 FAIL · 14 WARN.

---

## 1. What merged

Every PR below was reviewed by an agent that did not write it, and CI (`invariants`)
was green on its final head.

| PR | What it does |
|---|---|
| #25 | `bbs-claude-coach` |
| #32 | Third-party doctrine-injection plugin retired; native `PreToolUse` / `UserPromptExpansion` hooks carry the same doctrine |
| #27 | Cursor maintainer guide and workspaces (reps do not use Cursor — a later guide) |
| #33 | Sales-territory skills: territory handoff, budget timing, site visit, weekly report |
| #23 | Rep bootstrap packages |
| #26 | Windows portability fixes |
| #37 | Dead signature-image path fixed; packets are written all or nothing |
| #36 | Parker's 2026-09-28 rulings: rep-named signer, legal name on PD 843 / CalRecycle 74 / OBS 1000 / Darfur, Grainger sell rule by channel, BC SQ numbers, `bbs_accepted` never counted as a win, BPO list names the fiscal year it checked |
| #34 | `bbs-quote-builder`: reads the SQ number from BC, BC print layout, DVBE or SDVOSB by channel, Grainger rule read from canon |

Closed: #24 (superseded by #25).

## 2. Still open

| PR | State | Next |
|---|---|---|
| #35 | Draft — spec for logging local/co-op and federal/prime quotes the way CA state quotes are logged; Bechtel is the only other customer with that folder structure | Parker reads it and rules on its 11 open questions |
| #20 | Draft — pin `andrej-karpathy-skills` (maintainer tier) | Parked; `commons-curator` owns it |

## 3. Needs a person (no repo change does these)

1. **Rollout blocker.** Re-instantiate the State of CA desk `CLAUDE.md` on SharePoint
   from `workspace/DESK-CLAUDE-template.md`. The live copy still carries the California
   small-business wording and the two retired slash commands.
2. Bechtel `sentinel/CLAUDE.md` §5 still routes pricing through the retired
   `b2b.blackboxsafety.com` punch-out (sense 2 in AGENTS.md). Point it at the Grainger MCP.
3. Uninstall the retired injection plugin on Parker's Mac and every rep machine, then
   re-paste managed settings from `main` — `docs/ADMIN-RUNBOOK.md` §1a.
4. Turn off the superseded account-synced skills in claude.ai → Settings → Capabilities →
   Skills: `bbs-b2b-pricing`, `obs-form-filler`, `ca-form-filler`, `grainger-cart-info`,
   `grainger-screenshot`, `dwr-pdf-info`, `dgs-bpo-item-check`, `vendor-quote-email`,
   `bbs-sourcing`, `bbs-po-status`, `so-search`, `bbs-rebate-profitability`,
   `bbs-pricelist-import`, `bbs-quote-builder` (the account copy still numbers quotes in
   the retired local series), and `bbs-deck-voice` unless it was hand-edited.
5. Parker's email signature: "CA DVBE 2009473".
6. Run the bootstrap once on a Windows rep machine and watch the first `bbs-sales:*`
   skill run: the doctrine should appear once, not twice.
7. Delete the merged remote branches — appendix A. The cloud session is not permitted to
   delete refs.

## 4. Open rulings for Parker

Not restated here. The open lists are:

- `canonical-facts.md`, "Rulings on binding documents" → *Open — awaiting Parker*
  (Grainger for co-ops, direct federal and private; OBS 1000 signer; Worksheet business
  name). `/ca-rfq` stops on these.
- `docs/STEWARD.md`, *Already open for Parker* — every entry marked OPEN, including the
  ones added today: Grainger on a prime with no discount, address spelling, Bechtel's home
  and the BC write-API scripts, the macOS bootstrap, Dynamics 365 Sales vs the Sales CRM
  connector, and two items carried from the 2026-09-16 task list. Slice 1 (FY26–27 BPO
  list, from Aanya) and the managed `claudeMd` Grainger line are in the same file.
- `docs/COMMONS.md` — the `skills:` filter limitation and the `caveman-init` pin bypass.
- #35's open questions, in the PR.

## 5. Where the next session starts

1. **Grainger hand-off wording** (small, doc-only): `plugins/bbs-sales/skills/grainger-pricing/SKILL.md`
   ~l.148 hands off prices as "passed through at cost" with no channel. Reword the whole
   sentence to point at canon's "Grainger sell rule, by channel". (The no-discount case on
   a prime waits on Parker — STEWARD register.)
2. **macOS bootstrap**: mirror the Windows npm and pip steps — STEWARD register.
3. **Weekly rep review** (`wip/ca-weekly-rep-review`): scrub the fixture to synthetic
   identities (keep dollar values and dates — they are the test expectations), apply the
   fit-check brief edits, then build in two stages. Its limits are three STEWARD entries,
   read before building: "Sequencing the territory work", "What the weekly rep review may
   read", and "Reactive/proactive and new/repeat tags".
4. Re-score `docs/evals/queries-ambiguous.json` `naspo-1` against `ca-rfq-intake` on the
   next eval run that has Claude auth.

## 6. Lessons worth carrying

- **A restated rule goes stale in the copy nobody is looking at.** After #36 moved the
  Grainger rule into canon, three restatements in #34 and one in
  `docs/MAINTAINER-GUIDE.md` still said primes were unruled. The reviewer caught the last
  one. When a rule moves, grep the whole repo for its old wording, not just the files the
  PR touches.
- **Over-broad wording is a ruling nobody made.** "Cooperative contracts at cost" slipped
  in for "CA state schedules at cost". Narrow a ruling to exactly what was said.
- **A signature image must be tied to its delegate, not to a label in the spec** — #36
  review round 2 found two paths that stamped a delegate's image on a line the spec
  merely labelled.

---

## Appendix A — delete merged remote branches

Run from a local clone with push rights. Each delete is leased on the SHA the branch
had when its PR closed, so a branch that has moved since is refused, not lost. A
"skipped" line means the push failed for any reason, a moved branch or an auth error —
read git's message above it. Kept on purpose: `main`, the open PRs' branches (#35, #20,
and this handoff's `claude/session-handoff-2026-09-28` until it merges),
`feat/bbs-sales-plugin`, `sales-territory-0.3.0`, `v1.1`, `wip/ca-weekly-rep-review`.
`claude/festive-einstein-249j3j` moved after #28 closed, to #28's squash commit on
`main`, so deleting it loses nothing; it is left out only because its lease SHA changed.

```bash
set -u
git push origin --force-with-lease=refs/heads/claude/fix-signature-path:e62ee07428bf0247f8cf8743b8d8431ee083f037 --delete claude/fix-signature-path || echo "skipped claude/fix-signature-path"   # PR #37
git push origin --force-with-lease=refs/heads/claude/rulings-2026-09-28:806f0f8afcee1dc172e732d316cc28cded4843f8 --delete claude/rulings-2026-09-28 || echo "skipped claude/rulings-2026-09-28"   # PR #36
git push origin --force-with-lease=refs/heads/claude/quote-builder-bc-sq:c7fd1a07c07541267d0e98fe6f80078b2210b33f --delete claude/quote-builder-bc-sq || echo "skipped claude/quote-builder-bc-sq"   # PR #34
git push origin --force-with-lease=refs/heads/claude/sales-territory-land:c779713ec6448b3a131ffed306c5564acb1b9bc0 --delete claude/sales-territory-land || echo "skipped claude/sales-territory-land"   # PR #33
git push origin --force-with-lease=refs/heads/claude/remove-skill-bus:081beaeaea9bd929e1a960d4873333d23cc5d707 --delete claude/remove-skill-bus || echo "skipped claude/remove-skill-bus"   # PR #32
git push origin --force-with-lease=refs/heads/claude/sb-downstream-cleanup:27dd23c6caada9d217d857733ea2000edd0811d9 --delete claude/sb-downstream-cleanup || echo "skipped claude/sb-downstream-cleanup"   # PR #31
git push origin --force-with-lease=refs/heads/claude/skill-bus-sb-correction:1ebc1fe4ba4bc4d9d80dbe959f73f2040757d3db --delete claude/skill-bus-sb-correction || echo "skipped claude/skill-bus-sb-correction"   # PR #30
git push origin --force-with-lease=refs/heads/claude/sb-certification-correction:cff99b7b2b920f20b5a079beef15263c17d4aad9 --delete claude/sb-certification-correction || echo "skipped claude/sb-certification-correction"   # PR #29
git push origin --force-with-lease=refs/heads/feat/cursor-rep-environment:80fc0e9d88927b255307aab8bfa8ecd7d6b37a3e --delete feat/cursor-rep-environment || echo "skipped feat/cursor-rep-environment"   # PR #27
git push origin --force-with-lease=refs/heads/cursor/skill-portability-fixes-cdf4:e9d821da0f421924a01dcd501eeaa378ff69061d --delete cursor/skill-portability-fixes-cdf4 || echo "skipped cursor/skill-portability-fixes-cdf4"   # PR #26
git push origin --force-with-lease=refs/heads/cursor/bbs-claude-coach-25a0:2f83d2f0266deb0d0a1ebec0f3271e84ff7bf82f --delete cursor/bbs-claude-coach-25a0 || echo "skipped cursor/bbs-claude-coach-25a0"   # PR #25
git push origin --force-with-lease=refs/heads/cursor/toolkit-framework-doc-cdf4:b66e18b81877018c24d6fc74f082f349eb00921e --delete cursor/toolkit-framework-doc-cdf4 || echo "skipped cursor/toolkit-framework-doc-cdf4"   # PR #24
git push origin --force-with-lease=refs/heads/cursor/bootstrap-doc-tools-cdf4:a02114d16f1360f391a0fbe30b298a887d00f661 --delete cursor/bootstrap-doc-tools-cdf4 || echo "skipped cursor/bootstrap-doc-tools-cdf4"   # PR #23
git push origin --force-with-lease=refs/heads/cursor/bbs-commons-add-cmd-cdf4:4cbd53f66305b8b707942781b7e23048a0b8c189 --delete cursor/bbs-commons-add-cmd-cdf4 || echo "skipped cursor/bbs-commons-add-cmd-cdf4"   # PR #22
git push origin --force-with-lease=refs/heads/cursor/ci-marketplace-gate-cdf4:4f35601fc37ae15b11e8b56d1ecea899d67a60bd --delete cursor/ci-marketplace-gate-cdf4 || echo "skipped cursor/ci-marketplace-gate-cdf4"   # PR #21
git push origin --force-with-lease=refs/heads/cursor/cursor-review-rules-cdf4:1ea474acc6b10364059b6f040601beab467508d8 --delete cursor/cursor-review-rules-cdf4 || echo "skipped cursor/cursor-review-rules-cdf4"   # PR #19
git push origin --force-with-lease=refs/heads/cursor/set-up-cloud-agent-environment-0805:815fecbddadd6b3caaa2f180332969525078080d --delete cursor/set-up-cloud-agent-environment-0805 || echo "skipped cursor/set-up-cloud-agent-environment-0805"   # PR #17
git push origin --force-with-lease=refs/heads/claude/slice-5-dependency-declaration:3b3a880f3f8cd7f5f69c5d6a2c062afcd2d8d731 --delete claude/slice-5-dependency-declaration || echo "skipped claude/slice-5-dependency-declaration"   # PR #16
git push origin --force-with-lease=refs/heads/claude/slice-3-packet-profiles:41267d0362ce1b2df7d7af878422fb808dc29f7c --delete claude/slice-3-packet-profiles || echo "skipped claude/slice-3-packet-profiles"   # PR #15
git push origin --force-with-lease=refs/heads/claude/slice-2-ca-rfq-trigger:ffba6404aea91907b1051336b3c01a03d820adab --delete claude/slice-2-ca-rfq-trigger || echo "skipped claude/slice-2-ca-rfq-trigger"   # PR #14
git push origin --force-with-lease=refs/heads/claude/commons-toolbox:921ecb642f8d244bd8593001d45277045a0fa5e2 --delete claude/commons-toolbox || echo "skipped claude/commons-toolbox"   # PR #13
git push origin --force-with-lease=refs/heads/claude/trigger-precision-and-canonical-facts:17d2a59ca499adf18531a1422a49ee5fedd90822 --delete claude/trigger-precision-and-canonical-facts || echo "skipped claude/trigger-precision-and-canonical-facts"   # PR #12
git push origin --force-with-lease=refs/heads/claude/model-ids-auto-refresh:df4bc55a6da483c66b0538382ccbd8d85dd7ccc2 --delete claude/model-ids-auto-refresh || echo "skipped claude/model-ids-auto-refresh"   # PR #11
git push origin --force-with-lease=refs/heads/claude/handoff-cleanup:f2f83f1c8ea92f3752c414b3a650f865d9704605 --delete claude/handoff-cleanup || echo "skipped claude/handoff-cleanup"   # PR #10
git push origin --force-with-lease=refs/heads/claude/bbs-marketplace-reorg-by-desk:b958b36bb624cbb70280ce99e9d653bcfe3cf7ca --delete claude/bbs-marketplace-reorg-by-desk || echo "skipped claude/bbs-marketplace-reorg-by-desk"   # PR #9
git push origin --force-with-lease=refs/heads/feat/rename-bbs-ops-plugin-to-bbs-website:4cdc1e7d3debba0e1862ff95209a4888a00e2064 --delete feat/rename-bbs-ops-plugin-to-bbs-website || echo "skipped feat/rename-bbs-ops-plugin-to-bbs-website"   # PR #4
git push origin --force-with-lease=refs/heads/claude/bbs-obs-form-filler-marketplace-nstm6u:cfa1ee257eecf3aefe9a9eca6e1e40ccdd2005ca --delete claude/bbs-obs-form-filler-marketplace-nstm6u || echo "skipped claude/bbs-obs-form-filler-marketplace-nstm6u"   # PR #1
git remote prune origin
```

---

Owner: Parker Marshall. Written by the steward session, 2026-09-28.
