# Plan — `/ca-rfq`, one orchestration contract

*Spec: `docs/superpowers/specs/2026-09-16-ca-rfq-orchestration-design.md`. Branch:
`claude/slice-2-ca-rfq-trigger`, off `origin/main`. Slice 2 of `docs/STEWARD.md`.*

---

## Objective

Replace `/ca-rfq-log` and `/ca-rfq-quote` with a single `/ca-rfq` that carries the desk's
running order and its gates, and no skill procedure at all.

## Done condition

- One command replaces two: `plugins/bbs-sales/commands/ca-rfq.md` exists; the other two
  files are deleted.
- **No duplicated skill bodies.** A reviewer diffing `ca-rfq.md` against `ca-rfq-intake`,
  `rfq-item-extract`, `dgs-bpo-item-check`, `grainger-pricing`, `bbs-sourcing`,
  `vendor-quote-email`, `bbs-quote-builder`, `ca-form-filler` and `naspo-quote` finds no
  restated procedure — only order, gates, and pointers.
- Intake is an **explicit, skippable gate**, and the open routing ruling is not pre-empted.
- No skill is modified. No skill `description:` is modified.
- `python3 scripts/check_marketplace.py` exits 0.
- `check_claude_md.py` clean on the repo.
- One PR referencing this plan and the spec.

## Steps

### 1 — Read the contract and the artifacts *(done)*

`AGENTS.md`, `CLAUDE.md`, `docs/STEWARD.md`, both commands, both skills, the plugin README,
`scripts/check_marketplace.py`, `plugins/bbs-sales/references/ca-form-rules.md`,
`plugins/bbs-sales/skills/ca-form-filler/SKILL.md`, and the frontmatter of every other skill
the running order touches.

### 2 — Establish the baseline *(done)*

`python3 scripts/check_marketplace.py` before any edit: **27 skills · 0 FAIL · 4 WARN**,
exit 0. The four WARNs are pre-existing `description_near_limit` notices on
`bbs-order-reconciliation`, `bbs-quote-builder`, `naspo-quote` and `rfq-item-extract`. This
slice touches no description, so the same four must appear afterwards and no more.

### 3 — Verify the drift claim rather than repeating it *(done)*

The slice brief asserted the commands restate their skills *verbatim*. Read side by side,
they paraphrase. Three candidate divergences were drafted from memory and **two were
wrong** on re-reading — `/ca-rfq-quote` does keep the SABRC-guide pointer, and
`ca-rfq-intake` does say not to email the buyer. The four divergences that survived a
line-by-line check are the ones recorded in the spec. Every one was read out of both files.

### 4 — Write `plugins/bbs-sales/commands/ca-rfq.md`

Nine gates: intake (0), recognition (1), extraction (2), eligibility (3), pricing (4),
quote (5), fill and sign (6), visual verification (7), delivery (8). Each names its skill
and states only what must be true to pass. Gates 2 and 3 are explicitly skippable; gate 0
is the ruling-sensitive one.

Constraints held while writing:

- No form ID, signer, cert number, price rule, folder convention or field map appears in
  the file. Referred to `references/ca-form-rules.md` and `references/vendor_profile.json`
  by portable `${CLAUDE_PLUGIN_ROOT}` path.
- No model ID appears; none was needed.
- No step sends. Gate 8 states that the run ends with a person and that the send-class
  tools are denied by managed settings.
- `ca-form-filler`'s two open escalations are named as *existing* and stopping the run.
  They are not resolved, restated or routed around, and their substance is not re-keyed —
  which also means the file carries no path to them, because they are recorded in the
  marketplace repo and a rep's install has no `docs/`.

### 5 — Retire the two commands and repoint every live reference

`git rm` both files, then repoint:

| File | Was | Now |
|---|---|---|
| `README.md` | plugin table lists both | `/ca-rfq` |
| `plugins/bbs-sales/README.md` | two-row command table + "run them in that order" | one row, plus the intake-gate and open-ruling note |
| `workspace/DESK-CLAUDE-template.md` | "`/ca-rfq-log` and `/ca-rfq-quote` invoke them directly" | `/ca-rfq` runs the desk order with intake as an explicit first gate |
| `docs/REP-SETUP.md` | "then `/ca-rfq-quote` when you're ready to price" | `/ca-rfq` end to end, asking first whether to file before pricing |
| `docs/STEWARD.md` | slice 2 says "verbatim" | corrected to "paraphrase", with why the correction strengthens the slice |

**Left alone, deliberately:**

- `docs/superpowers/plans/2026-09-11-rep-workspace-v1.md` and
  `docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md` — dated build records
  inside the checker's own `ARCHIVE_DIRS`. Rewriting a record to match the present is how it
  stops being a record.
- `plugins/bbs-foundations/docs/bbs-managed-settings.json` — out of scope for this session,
  and a repo edit reaches no machine. Added as a clause to the existing "re-paste managed
  settings" item in `docs/STEWARD.md`'s open-for-Parker register instead.

### 6 — Verify

```bash
python3 scripts/check_marketplace.py
python3 plugins/bbs-foundations/skills/bbs-claude-md-forge/scripts/check_claude_md.py "$PWD"
grep -rn "ca-rfq-log\|ca-rfq-quote" --include="*.md" --include="*.json" .
```

**The routing eval is not re-run, because nothing this slice touches can move it.** It
scores skill `description:` fields via `docs/evals/skills.json`; commands are not skills and
do not enter that file. No skill was modified. Re-running it would consume Anthropic auth to
re-measure an input that did not change.

## What this plan does not deliver

- **The open routing ruling is not decided.** Gate 0 case (c) asks the rep and records the
  answer. Either ruling lands afterwards as a one-paragraph replacement.
- **`ca-form-filler`'s two open escalations are not resolved.** The command stops on them.
- **No end-to-end exercise against a real RFQ.** This session has no buyer folder, no
  Grainger account and no blank packet. The command's *structure* is verified — it exists,
  it parses, it restates nothing, the checkers pass — and its *behaviour on a live RFQ is
  unverified by this session.* First real run should be supervised.

## Follow-up, review pass (same PR)

The review of this PR reversed two "left alone" items in step 5 and closed four gaps in the
command itself. Recorded here rather than edited above.

- `scripts/check_marketplace.py` gained `RETIRED_COMMANDS`, so a surviving pointer to a
  retired *command* now FAILs the same way a retired skill does.
- `plugins/bbs-foundations/docs/bbs-managed-settings.json` was corrected in the repo; the
  re-paste escalation stays open on top of it.
- In `commands/ca-rfq.md`: the price-first branch now establishes vehicle and account at
  Gate 1 like every other branch; the state path enters `naspo-quote` once at Gate 4 and
  Gates 5-8 check its output instead of re-invoking it; Gate 6's claim that `naspo-quote`
  calls `ca-form-filler` was false and is gone; Gate 4's price-trace rule is scoped to the
  routes that have a buying account.

---

Owner: Parker Marshall. Last verified 2026-09-16.
