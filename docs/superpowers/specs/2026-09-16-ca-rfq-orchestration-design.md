# Spec — `/ca-rfq` as one orchestration contract

*Written 2026-09-16, before implementation. Plan:
`docs/superpowers/plans/2026-09-16-ca-rfq-orchestration.md`. Slice 2 of `docs/STEWARD.md`.*

---

## The problem

`plugins/bbs-sales/commands/ca-rfq-log.md` and `ca-rfq-quote.md` each **paraphrase the body
of the skill they invoke.** `/ca-rfq-log` restates `ca-rfq-intake`'s five steps as seven;
`/ca-rfq-quote` restates `naspo-quote`'s seven steps as seven shorter ones.

`docs/STEWARD.md` slice 2 describes this as restating the skill's body *verbatim*. It is
not verbatim, and the difference matters in the direction that makes the slice more urgent,
not less. **A verbatim copy is merely redundant; a paraphrase can disagree.** A reader
diffing a verbatim copy sees drift immediately. A paraphrase drifts silently, and the
command and the skill can end up giving two different instructions without either looking
wrong on its own.

They already do disagree, in ways nobody wrote down. Each row below was read out of both
files rather than assumed:

| Fact | The skill says | The command says |
|---|---|---|
| Which lines the DV owner signs | `naspo-quote` §5 puts the DVBE declaration, the disabled-veteran declaration form, **and** the payee data record on Jackson, and notes the Bidder Declaration has no signature block at all | `/ca-rfq-quote` step 5 shortens Jackson's lines to "the disabled-veteran declarations" and drops the rest |
| The CUF statement | `naspo-quote` §4 spends a paragraph on it — not a vendor constant, never compose one, `[MISSING — NEEDS INPUT]` when absent, because it is a certification on a binding bid | `/ca-rfq-quote` does not mention it anywhere |
| Where the buyer's account number lives | `naspo-quote` §1 reads `<Buyer Name>.txt` for the account number, the BC customer ID and the ship-to | `/ca-rfq-quote` step 1 reads "the buyer's `CLAUDE.md`" — a different file |
| The sell rule | `naspo-quote` §2 says read `account.sellRule` out of the pricing response | `/ca-rfq-quote` step 2 asserts the answer instead of reading it: "at cost on state schedules, no markup" |

None of those is a crash. Each is a second, slightly different instruction on a path whose
output is a binding document. That is invariant 2 (**truth lives in one place**) broken in
the least visible way available.

## What replaces them

**One command, `/ca-rfq`, that carries order and gates and no procedure.** Each step names
the skill that owns it. A reviewer should be able to diff the command against every skill it
names and find no restated step — that is the acceptance test, not a style preference.

The distinction the file has to hold:

- **Order** — which step comes after which, and which steps are skippable.
- **A gate** — a condition that must hold before the run moves on, and what happens when it
  does not. Gates are orchestration-level facts: they belong to the *sequence*, not to any
  one skill, so they are not duplicated when they are written here.
- **Procedure** — how a step is actually done. Never here. Always the skill's.

## The constraint that shaped Gate 0

`docs/STEWARD.md` records an **open routing ruling**: does a fresh *"the agency emailed
asking us to quote these…"* belong to `ca-rfq-intake` or to `naspo-quote`? It is left
untuned in `docs/evals/queries-ambiguous.json` (`naspo-1`, `expect: __unscored__`) on
purpose, because fitting the test before the ruling is just fitting the test.

A `/ca-rfq` that **begins unconditionally at intake answers that ruling by construction** —
it ships the intake-first reading as behaviour, and the ruling becomes a formality about
wording. So intake is built as an **explicit, skippable first gate** with three stated
cases:

| Case | Condition | Behaviour |
|---|---|---|
| (a) | a deal folder and run record already exist | skip intake, enter at recognition |
| (b) | unlogged, and the rep asked to file/log/start it | run `ca-rfq-intake`, then continue |
| (c) | unlogged, and the rep asked for a price, quote or packet | **the open ruling.** Ask the rep which order they want, record the answer, continue either way |

Case (c) is the whole point. Asking is not a decision — it is this repo's own escalation
doctrine applied to a business ruling, and it is honourable under **either** ruling without
a rebuild: when Parker rules, case (c) collapses into (a) or (b) and one paragraph is
replaced. Nothing else in the file moves. In the meantime the answers reps actually give
accumulate in the run records, which is evidence Parker can rule *with* rather than
against.

The alternative — pick a provisional default and disclaim it — was rejected. A disclaimed
default is still a default; it is the ruling, shipped, with a note attached.

## What this command must not do

- **Not change any skill.** `plugins/bbs-sales/skills/` is out of scope. In particular no
  skill `description:` changes, because a description change is what forces a routing-eval
  re-run. Commands do not enter `docs/evals/skills.json`, so the routing eval is not
  affected by this slice and is not re-run.
- **Not resolve, restate, or route around `ca-form-filler`'s two open escalations.** The
  command stops and reports when a run reaches one.
- **Not carry a fact that belongs to a system of record.** No form ID, no signer, no cert
  number, no price rule, no folder convention. Those live in
  `plugins/bbs-sales/references/ca-form-rules.md`,
  `plugins/bbs-sales/references/vendor_profile.json`, and the skills.
- **Not design a step that sends.** Delivery ends with the rep. Managed settings deny the
  send-class tools, and the command must not imply otherwise.

## Retiring two commands

A pointer to a retired command is a dangling instruction a rep will follow — the defect
class `scripts/check_marketplace.py` exists to catch for skills. Every live pointer to
`/ca-rfq-log` and `/ca-rfq-quote` is repointed at `/ca-rfq`.

Two categories are deliberately left alone:

- **Dated build records** under `docs/superpowers/` — the checker's own `ARCHIVE_DIRS` treats
  that tree as history, and rewriting history to match the present is how a record stops
  being a record.
- **`plugins/bbs-foundations/docs/bbs-managed-settings.json`** — out of scope for this
  session, and a repo edit reaches no machine anyway. Escalated, not silently fixed.

`check_marketplace.py` has no command-retirement check — its `RETIRED_SKILLS` map covers
skills only. Adding `/ca-rfq-log` and `/ca-rfq-quote` to a command equivalent is a
review-side change to a file this session must not touch; it is raised for the reviewer
rather than made here.

---

Owner: Parker Marshall. Last verified 2026-09-16.
