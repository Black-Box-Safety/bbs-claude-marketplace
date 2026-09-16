# Steward — how a work session runs

The operating manual for `.claude/agents/steward.md`. Read `AGENTS.md` first.

---

## The loop

```
scope → brief → dispatch worker → worker opens PR
      → steward reviews with a fresh reviewer
      → findings back to the SAME worker → worker tends
      → steward merges
```

Four properties make it worth running:

- **A session ends at a PR, not a merge.** The agent that wrote the change never approves
  it.
- **The reviewer did not write the code.** Parker's standing authorization to merge is
  conditional on exactly this.
- **Findings return to the original worker**, which still holds the context. A fresh
  session re-deriving the change is slower and gets it less right.
- **The steward is woken by the PR**, not by polling. Subscribe to PR activity when the
  worker opens it.

### Commands

```bash
python3 scripts/check_marketplace.py            # every PR, must exit 0
/code-review <PR> high                          # the independent review
cd docs/evals && python3 discriminate.py \      # only if descriptions changed
  --skills skills.json --queries queries-routing.json \
  --runs 5 --workers 4 --anonymize --out /tmp/r.json
```

`--workers 4`, never 10 — the harness throttles and returns spurious `__none__`. A cluster
of `__none__` across unrelated queries is throttling; a real routing defect names the
wrong skill and reproduces in isolation.

---

## Tonight's slices

In dependency order. Each is one session.

### 0 — Land PR #12 *(blocks everything; do this first)*

It carries the consolidation, the model-ID propagation fix, the invariant checker and the
signature-doctrine change. Everything else branches off an unmerged base until it lands.

Outstanding review findings to clear first — all confirmed by reproduction:

| Where | Defect |
|---|---|
| `scripts/check_marketplace.py` | A SKILL.md with no frontmatter makes `yaml.safe_load` return a string; the run aborts with `AttributeError` instead of reporting `no_name` |
| `scripts/check_marketplace.py` | `COUNTER_EXAMPLE` + a ±2-line window: one ordinary "not" silences all three scans |
| `docs/evals/discriminate.py` | stdout drained at process exit is never parsed, so a fast run discards its `tool_use` event and scores `__none__` |
| `.../references/checklist.md` | documents `check_claude_md.py --self-test`, which does not exist |
| `.../skills/dgs-bpo-item-check/SKILL.md` | the Aanya→"the rep" rewrite left "unless she asks" with no antecedent |

**Done:** findings cleared, `check_marketplace.py` exits 0, fresh review is clean, PR
merged, the six verified-dead branches deleted (`v1.1` held back — it reads as a version
marker; ask Parker).

### 1 — FY26/27 BPO list *(operationally urgent)*

`dgs-bpo-item-check` bundles `Final_BPO_Item_List_25-26B.xlsx` and says it covers
"calendar years 2025 and 2026 only." California FY26/27 began 1 July 2026. **A rep
checking today is checking last year's list**, and Aanya's version adds alternates on a
miss plus restricted-item alerts that production does not have.

Needs the FY26/27 list from Aanya's bundle. **Escalate if it is not available** — do not
synthesize a list.

**Done:** current list bundled, alternates-on-miss and restricted-item alerting present,
coverage note accurate.

### 2 — One trigger, end to end

Today `/ca-rfq-log` and `/ca-rfq-quote` each restate their skill's body verbatim, so
command and skill drift. Parker wants one trigger that completes documents and signs.

Build `/ca-rfq` as an orchestration contract — **order and gates only, no restated
steps** — running intake → recognize customer/packet → extract → price → quote → fill and
sign → verify → deliver. Retire the two commands.

**Done:** one command, no duplicated skill bodies, the routing eval still green.

### 3 — Packet profiles in `ca-form-filler`

Generalize Path A from one hard-coded packet to a profile set keyed on **customer
recognition**: `references/packets/{obs-4007b,dsh-general,dsh-atascadero}.md`. Recognition
matches text in the PDF — deterministic, unlike sibling skills competing on descriptions.
This is where Aanya's DSH iterations land: as profiles, not as skills.

**Done:** profile contract documented, OBS migrated to it, a second profile added, adding
a third needs no change to `SKILL.md`.

### 4 — Aanya's bundle

12 skills; 7 she asks to keep callable. Her genuinely personal parts stay personal — her
Excel format, her SQ+10-digit convention. The shared substance folds into the meta skills.
`daily-forms` has a **scheduled task** running off it; moving it breaks a live automation.
`grainger-sourcing-quote-builder` depends on "Kim's skill", so a third person's work is in
scope.

Enrich the Grainger sourcing/LPA-request skill from real examples in Parker's sent mail to
`customersupport@grainger.com` and to Grainger reps (Monica Flores, Phillip Barrile) — he
authorized that search.

**Done:** each of the 12 is folded, kept personal, or explicitly deferred with a reason.

### 5 — Dependency completeness

Every skill declares the connectors, MCPs and CLI tools it needs, machine-checked, so a
rep can tell before installing whether a job will run on their machine.

**Done:** `check_marketplace.py` fails on an undeclared dependency.

---

## Adding a skill from outside

`awesome-claude-skills` (ComposioHQ) and similar lists are candidate sources, not an
install path.

**Their install guidance is a user-level copy into `~/.config/claude-code/skills/`. Do not
follow it.** That is precisely the pattern that produced this company's 15 shadowed
personal skills, where the maintained marketplace copy loses to a stale local one. Route
every candidate through `docs/COMMONS.md` instead: propose, review, **pin** the upstream,
never vendor it, then `claude plugin validate . --strict`.

Candidates from that list worth a look, none yet reviewed: `brainstorming` (fits the
spec-then-plan discipline), `mercury-mcp` (multi-agent coordination), `postgres`
(read-only SQL for the supplier/catalog work), `kaizen`, `csv-data-summarizer`. Skip
`google-workspace-skills` — BBS is Microsoft 365.

---

## Build discipline

For anything that is a build rather than an edit, write the spec to
`docs/superpowers/specs/` and the plan to `docs/superpowers/plans/` before implementing,
and reference both from the PR. The repo already works this way.

Full `superpowers` is ruled **Parker-only** (`docs/COMMONS.md`) because its session hook
injects a large mandatory block. Steward sessions may use it; never push it to rep
installs.

---

## Yours to change — granted 2026-09-16

Parker has granted the steward authority over **the saved preferences and the settings**.

**The saved preference still carrying the removed signature rule** is the live one. It
says "Never pre-fill signature lines on any compliance form." That rule was removed from
this repo — Parker states it was never BBS practice, and counsel confirmed the delegation
(Parker and Jackson each know the forms their signature is used on and have authorized
signing on their behalf). The preference is now the last place it survives, and it
re-injects into every new session until it changes. Replace it with the rule that actually
governs: **the right signer on the right line** — Parker on bidder and cert lines, Jackson
on the ownership lines (DGS PD 843, STD 204 payee), never a customer's or a third party's,
and never a line whose signer cannot be determined. `plugins/bbs-sales/references/ca-form-rules.md`
is authoritative on the split.

For `settings.json`, the `update-config` skill is the supported path.

**Establish the mechanism before reporting it done.** This is the trap that caught the
personal-skill cutover: we assumed removing a synced skill from disk would retire it,
tested it, and a new session re-synced it byte-identical within seconds. Account-level
saved preferences may not be editable from a Claude Code session at all. If no real
mechanism exists, say so and leave it for Parker in the UI. Never report a preference as
updated without verifying the change persisted.

**Managed settings are not this.** `plugins/bbs-foundations/docs/bbs-managed-settings.json`
is the source and editing it is yours; *deploying* it is an admin paste in the claude.ai
console that only Parker can do.

## Escalate, do not decide

Write it up with evidence and move to the next slice. Do not idle.

- Anything changing a binding document: a signer, a form ID, a certification claim, a
  price rule.
- Anything outside this repo **other than the preferences and settings granted above**:
  the account-synced personal skills, managed-settings deployment, connector assignment.
  **No repo change fixes these.**
- A business ruling — which workflow owns a step, whether a vehicle applies.
- Removing a control. Say it is wrong; do not delete it.

### Already open for Parker

- **Re-paste managed settings** — the model-ID and Grainger changes reach no machine from
  the repo alone.
- **The personal-copy cutover** is account-side, in claude.ai → Settings → Capabilities →
  Skills. Five orphans now contradict what replaced them; `bbs-b2b-pricing` still drives
  the retired punch-out.
- **One routing ruling**: does a fresh "agency emailed asking us to quote" belong to
  `ca-rfq-intake` or `naspo-quote`? Left untuned on purpose — fitting the test before the
  ruling would just be fitting the test.

---

Owner: Parker Marshall. Last verified 2026-09-16.
