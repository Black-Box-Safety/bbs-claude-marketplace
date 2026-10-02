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

Those five findings are cleared, and so are the six the independent review then raised in
the consolidation itself — the inverted DWR de-duplication rule, the demoted
"stop parsing before Recently Viewed" instruction, the CUF statement described as a vendor
constant, the dropped Grainger substitution and pack-size rules, the signature reversal
that never reached `ca-form-filler`'s Path B, and two `STD 1000` survivors. The routing
eval was re-run on the fixed harness: 24/24, artifact committed.

Two of the review's findings were **open for Parker** and deliberately not changed — the
SB checkbox on CDCR Packet B, and whether Grainger at-cost is a reversal of the old margin
practice. Both are certification or pricing rulings on binding documents.

- **SB checkbox on CDCR Packet B — RULED 2026-09-22.** Parker ruled in session that OSDS
  2009473 carries DVBE only and BBS is not a California small business, having exceeded the
  state SB revenue threshold. The box is **`/Off`**, which is what `fill_obs_packet.py:138`
  already writes and what `docs/superpowers/specs/2026-09-16-ca-form-filler-packet-profiles-design.md:111`
  specifies. Closed — `/ca-rfq` Gate 1 no longer stops on it. Fact and reasoning:
  `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`,
  "Small-business status is channel-dependent".
- **Grainger at-cost vs the old margin practice — RULED 2026-09-18 and confirmed
  2026-09-28 for California state agencies; primes RULED 2026-09-28; other channels
  OPEN.** Parker, in session, 2026-09-28: "confirmed" (to the at-cost rule; recorded only for
  California state agencies — CA state schedules and the NASPO ValuePoint CA MRO LPA —
  until the open question below is answered), and on primes: "For primes,
  grainger products can be increased. reps should ask for a discount from our grainger
  account manager first." So on a prime (e.g. Bechtel) Grainger lines may be marked up:
  the rep asks BBS's Grainger account manager for a discount first, prices from the
  discounted cost, and applies whatever markup the rep chooses — no figure is set, and
  none is invented. **Still open for Parker:** national and local cooperative contracts,
  direct federal and private. **Ask:** are national cooperative contracts (Sourcewell,
  NPPGov, UC/OMNIA) at cost? A draft of this PR had put "cooperative contracts" in the
  at-cost row, which Parker did not rule; review caught it and it was narrowed.
  The single home is `canonical-facts.md`, "Grainger sell rule, by channel" (the Systems
  of record Grainger row points there); `grainger-pricing` §2 points at it, reminds the rep
  on a prime to request the discount first and offers to write the request (never sends,
  never invents a discount). The quote builder's per-quote `pricing.graingerAtCost` (PR
  #34) follows it: `true` on a California state-schedule / NASPO LPA quote, `false` on a
  prime. PR #34 restates the rule (`spec-schema.md:30`, `:126`, `SKILL.md:142`, "not ruled
  for primes"); it merges after this PR and is to repoint at canon.
  An earlier version of this entry said every live file "agrees" with an unconditional
  at-cost rule; since the prime ruling that is no longer the test. Scoped to California
  state / NASPO and therefore still correct: `naspo-quote`, `ca-rfq-intake`, the
  `bbs-sales` README, `supply-lane-tuning`, `quote-bot`, `bbs-order-reconciliation`
  ("on these accounts"). Stated unconditionally and corrected in PR #36:
  `grainger-pricing` §2 and `bbs-doctrine.md` rule 19 (now a pointer). **Still unconditional, not edited
  here:** the managed `claudeMd` in `bbs-foundations/docs/bbs-managed-settings.json` ("BBS
  sells Grainger at cost") — a managed artifact, so it needs its own PR with a second
  reviewer and then Parker's re-paste. `bbs-quote-builder`'s 20% gross-margin house
  default (`SKILL.md:69-71`) is being changed by a separate worker (PR #34).

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

**Decision 2026-09-28 (still BLOCKED on Aanya).** Parker, in session: "Aanya will
provide." Until she does, `dgs-bpo-item-check` keeps the FY25–26 list, and every answer
opens with the list it checked against plus a `⚠ STALE LIST` line once that fiscal year has
ended (`check_items.py`, `BPO_LIST_*`). The constants are now checked against the bundle:
the script exits 1 unless the named source file is in `assets/`, its name carries the FY
token, the years are consecutive, the dates are that fiscal year, and both asset files
match fingerprints stored beside the constants (`test_check_items.py`). No list is synthesized.

**Done:** current list bundled, alternates-on-miss and restricted-item alerting present,
coverage note accurate.

### 2 — One trigger, end to end *(built; PR #14 in review)*

The now-retired `/ca-rfq-log` and `/ca-rfq-quote` each **paraphrased** their skill's body —
they did not restate it verbatim, as an earlier draft of this slice said. The difference
made the case stronger: a verbatim copy is merely redundant and drift is visible in a diff,
whereas a paraphrase can silently disagree with the skill it paraphrases, and those two
already did. Parker wanted one trigger that completes documents and signs.

`/ca-rfq` is that trigger, built as an orchestration contract — **order and gates only, no
restated steps** — running intake → recognize customer/packet → extract → price → quote →
fill and sign → verify → deliver. Both commands are gone and every live pointer is
repointed, including the `claudeMd` block in `bbs-managed-settings.json`.

**Done:** one command, no duplicated skill bodies, the routing eval still green — not
re-run, because no skill `description:` changed and commands never enter
`docs/evals/skills.json`. `check_marketplace.py` now FAILs on a surviving pointer to a
retired *command*, not only to a retired skill.

**Not done here:** review and merge of PR #14. It edits a managed artifact, so it needs the
second reviewer that rule already requires. The command's behaviour on a live RFQ is
unverified — no session has run it against a real buyer folder.

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

## Escalate, do not decide

Write it up with evidence and move to the next slice. Do not idle.

- Anything changing a binding document: a signer, a form ID, a certification claim, a
  price rule.
- Anything outside this repo: the account-synced personal skills, managed-settings
  deployment, connector assignment. **No repo change fixes these.**
- A business ruling — which workflow owns a step, whether a vehicle applies.
- Removing a control. Say it is wrong; do not delete it.

### Already open for Parker

- **Re-paste managed settings** — the model-ID and Grainger changes reach no machine from
  the repo alone, and neither does the slice-2 command line. The repo copy's `claudeMd`
  block is corrected to `/ca-rfq` (it named the two retired commands), but the correction
  reaches a rep only when Parker re-pastes; until then every session still loads the dead
  names into memory.
- **Edit the saved preference** that still says "Never pre-fill signature lines on any
  compliance form." It re-injects the removed rule into every new session.
- **The personal-copy cutover** is account-side, in claude.ai → Settings → Capabilities →
  Skills. Five orphans now contradict what replaced them; `bbs-b2b-pricing` still drives
  the retired punch-out.
- **The routing ruling — RULED 2026-09-24: file first.** A fresh "agency emailed asking us
  to quote" runs `ca-rfq-intake` before anything is priced. `/ca-rfq` Gate 0 (c) no longer
  asks. `docs/evals/queries-ambiguous.json` `naspo-1` is still `__unscored__`; re-score it
  against `ca-rfq-intake` on the next eval run that has Claude auth.
- **Both injected doctrine sets carried pre-2026-09-22 certification wording —
  RESOLVED 2026-09-22 in PR #30.** Neither was changed by the SB correction (PR #29),
  which was scoped out of them; this was a documented deferral, now closed. (At the time
  the text lived in each plugin's `hooks/skill-bus.json`, a file retired 2026-09-28; since
  then the same text, byte for byte, is in `hooks/doctrine/*.md` — see the next entry. The old file names
  below are kept as the historical record.)
  - `plugins/bbs-foundations/hooks/skill-bus.json` (retired path; now `hooks/doctrine/bbs-claude-md-doctrine.md`)
    — **RESOLVED 2026-09-22, PR #30.** It injected the *affirmative false claim* that the
    5% SB preference (SCM §1204) applies on California competitive solicitations, into
    **every CLAUDE.md-writing skill run**. Now carries the channel split: California DVBE
    only, §1204 never, §1202 still claimed; federal SDVOSB and small business.
  - `plugins/bbs-website/hooks/skill-bus.json` (retired path; now `hooks/doctrine/bbs-storefront-doctrine.md`)
    — **RESOLVED 2026-09-22, PR #30.** Its channel-neutral "BBS is NOT SB-certified" is
    replaced by the reword recorded in canonical facts, which names California. The
    matching `bbs-shopify` canonical-facts line lives in another repo and is still open
    there.

  A PR touching either gets a second reviewer: they reach every skill run without anyone
  installing anything.
- **The third-party injection plugin (`joeymnguyen/skill-bus`) — RULED 2026-09-28: retired.**
  Parker, in session: it "causes issues and has permeated throughout the entire set up."
  It is removed from managed settings, from the checker and from every live doc; the
  doctrine text it injected is **kept**, moved byte for byte into
  `plugins/{bbs-foundations,bbs-website}/hooks/doctrine/*.md`, and re-homed on each
  plugin's own `hooks/hooks.json`: `PreToolUse` on the Skill tool for a tool call and
  `UserPromptExpansion` for a typed slash command (the path `monitorSlashCommands` covered);
  PowerShell, or python3 where there is none; fails open. Same subscriptions, plus
  `bbs-claude-coach:*` on the grounding doctrine (owed from the PR #25 review).
  `check_marketplace.py` FAILs if the name creeps back into a live file. The rest of its
  settings block (telemetry, `maxMatchesPerSkill`, `observeUnmatched`, `showConditionSkips`)
  has no native equivalent and is dropped. Spec and plan for the retired plugin's removal:
  `docs/superpowers/{specs,plans}/2026-09-28-remove-skill-bus.md`.
- **Parker: after the skill-bus removal merges, re-paste managed settings and, on each
  existing machine, `/plugin uninstall skill-bus@skill-bus-marketplace` and remove the
  `skill-bus-marketplace` entry** (`/plugin marketplace remove skill-bus-marketplace`) —
  a repo change cannot do that. Until both are done a machine still runs the retired
  plugin alongside the native hooks and injects the doctrine twice. Steps:
  `docs/ADMIN-RUNBOOK.md` §1a. The Windows PowerShell 5.1 path of the new hook was not
  executable in the build environment (pwsh 7 and python3 were, and agree byte for byte);
  the first Windows rep run of any `bbs-sales:*` skill should be watched for the doctrine
  appearing once.
- **`bbs-deck-voice` claims "Largest small business seller to the State of California"** —
  **RESOLVED 2026-09-23, PR #31.** Parker ruled BBS was a California small business when
  it earned that ranking: keep the claim, make it historical. The four present-tense lines
  are now past tense ("Became the largest…"), following `:28`; nothing else in the claim
  changed and no `description:` was touched. Original entry, kept for history: it said so in
  the present tense — `SKILL.md:25`, `SKILL.md:57`, `references/federal-positioning.md:34`,
  `:57` (`:28` is past tense and reads fine). Since 2026-09-22 BBS is **not** a California
  small business, so this is the same channel-crossing sentence class PR #29 removed,
  pointing the other way. Deliberately **not** changed: it may be a ranking BBS legitimately
  earned while certified, it is deck marketing rather than a sworn certification, and
  rewriting it from this ruling alone would be the "infer a certification from a
  neighbouring file" error the cautionary tale warns against. Parker's call — keep as is,
  qualify with a date, or drop.
- **Past California bids in the filed-form corpus that carried an SB claim — RESOLVED
  2026-09-23, PR #31.** Raised in review of PR #30 and not previously recorded here.
  Parker ruled they were filed while BBS was a California small business and were correct
  when filed: no compliance problem, and the record of what was filed stays as filed. The
  fix is downstream — nothing that learns from the corpus may carry an SB claim into a bid
  made today. `naspo-quote/scripts/mine_precedents.py` now routes values carrying an SB,
  MB or small-business token to `historical_only` instead of the `filled_values`
  precedent table; a generically named checkbox still needs a human check (test:
  `test_mine_precedents.py`); `filled-form-precedents.md`, `naspo-quote` SKILL.md and the
  `bbs-sales` README say certification values come from `vendor_profile.json`, never from
  a past packet. Canon records the pre-threshold validity.
- **`ca-form-rules.md` / `vendor_profile.json` read as excluding informal solicitations
  from the DVBE incentive — RESOLVED 2026-09-23, PR #31.** Raised by both reviewers of
  PR #30 (which fixed the same wording in the foundations hook only). Parker approved
  aligning them with canon: §1204 is never claimed on any California solicitation; §1202 is
  claimed on every California competitive solicitation, informal ones included.
- **Outlook and Teams Cursor plugins for reps — RULED 2026-09-28: reps do not use Cursor.**
  Parker, in session: "Reps do not need to use Cursor; that is a guide down the line."
  Raised in the PR #27 review: `docs/CURSOR-SETUP.md` told every quoting rep to add the
  Outlook and Teams Cursor plugins, both send-capable, while Cursor does not inherit the
  managed deny list. Applied in PR #27: `docs/CURSOR-SETUP.md` is now a maintainer / future
  guide for Parker, not rep onboarding; reps set up with `docs/REP-SETUP.md` (VS Code /
  Claude Code), and every rep-facing Cursor path the PR added is gone. The Outlook and Teams
  Cursor plugins are marked send-capable, Parker/Griffin only — not for rep machines.
  No exception is granted: `.cursor/rules/bbs-invariants.mdc` keeps "Do not add
  send-capable MCP servers" and AGENTS.md is unchanged.
- **Body armor and CSU/UC out of the Kim/Aanya CA state book — RULED 2026-09-28: canon.**
  Parker, in session: "Body armor (BA-CA, BODYARMOR, BA-SRCWL) and CSU/UC are out of the
  Kim/Aanya CA state book." Raised in the PR #27 review, where the line lived only in the
  Cursor rule. Its single home is now "CA state book scope" in
  `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`;
  `.cursor/rules/bbs-invariants.mdc` points at it instead of restating it.
- **Who signs the rep-signed lines (CalRecycle 74, OBS 4007(B) Bidder Signature, Darfur
  OBS 1500) — RULED 2026-09-18: the rep who quoted the job; superseded, RULED 2026-09-28:
  any BBS employee, named by the rep.** Parker, in session, 2026-09-28: "anyone is
  permitted to sign", and, asked whether the rep names the signer: "yes, or whomever the
  rep says, they can sign it with anyone." The rule lives once, in `ca-form-rules.md`,
  "Rep-signed lines": the rep names the signer on every run (no template default; none
  given → `[MISSING — NEEDS INPUT]`); the signer must be a BBS employee (one `@`, BBS's
  domain, checked before the name; otherwise REFUSED, nothing written); a delegate in
  `vendor_profile.json` (Parker, Jackson — counsel, 2026-09-16; matched on the recorded
  email or alias) gets the delegated signature, including on a bid someone else prepared;
  any other signer gets name and title, signature and date blank, `⚑ SIGNATURE REQUIRED`.
  The signature can never differ from the signer (no free-text signature input). The DV-owner
  declarations (DGS PD 843, CV 012, STD 204) stay Jackson's. Path A: `fill_obs_packet.py`
  (`resolve_signer`, a confirmation block every run) and `test_fill_obs_packet.py`. Path B:
  `naspo-quote/scripts/fill_ca_forms.py` refuses a spec with no signer, a non-BBS signer,
  or a delegate's image for a signer whose email/alias is not that delegate's; the image
  is always the delegate's own `signature_image` from the profile (never a spec path);
  every form declares its `form` kind, and only PD843/CV012/STD204/STD205 take the
  dvbe_owner's `dv_owner` stamp (`test_fill_ca_forms.py`). OBS 1000's signer is not
  ruled (`field-maps.md`): no skill stamps it, and the draft line in this PR assigning it
  to Parker was removed — **open for Parker** (superseded 2026-10-01: OBS 1000 is
  rep-signed, and the delegates are the six of R1a — see the 2026-10-01 rulings below).
  Signer data (after PR #37): Parker has his own
  `authorized_representatives` entry, role `sales_manager`, with his alias and the
  `signature_image` moved off `default_rep`; `signature_delegation.delegates` is
  `["sales_manager", "dvbe_owner"]`, resolved to those entries by both loaders. Canon,
  `naspo-quote` §5, `field-maps.md` and the `bbs-sales` README point at the rule.
- **Company name on CalRecycle 74, OBS 1000 and Darfur OBS 1500 — RULED 2026-09-28: legal
  name.** Parker, in session: "Yes, they can match legal name". They take
  `vendor_profile.json` `business_identity.legal_name`, as DGS PD 843 already did; rule in
  `ca-form-rules.md`, "Company name"; `fill_obs_packet.py` writes it and
  `test_fill_obs_packet.py` asserts it. **Open for Parker:** the OBS Line-Item Cost
  Worksheet "BUSINESS NAME:" header was not covered and still takes the short name.
- **DGS PD 843 "Name of DVBE" — RULED 2026-09-18; confirmed RULED 2026-09-28.** Parker,
  in session: "do legal name". The field takes `vendor_profile.json`
  `business_identity.legal_name`, never `short_name`. `fill_obs_packet.py` already wrote
  `legal_name`; `ca-form-rules.md` records the confirmation, and `test_fill_obs_packet.py`
  now asserts the field equals the profile's legal name and follows the profile rather
  than a literal.
- **Quote numbers — RULED 2026-09-28: BC SQ number.** Parker, in session: "use BC SQ
  number". BBS customer quotes carry the Business Central SQ number; the local `900001`
  series is retired. Recorded in canon (Systems of record). `bbs-quote-builder`, which
  still describes the 900001 series, is being changed by a separate worker and is not
  edited by the PR that records this entry.
- **Sequencing the territory work — RULED 2026-09-28 (Parker, in session): land the
  sales-territory work before the weekly rep review build.** Landed by the PR that records
  this entry (`claude/sales-territory-land`), which brings the genuinely new work from
  Parker's branch `sales-territory-0.3.0` onto main — `ca-territory-handoff`,
  `ca-budget-timing`, `ca-agency-primer`, `ca-site-visit-brief`,
  `ca-visit-readiness-review`, `bbs-weekly-sales-report`, `/ca-territory-handoff`, and the
  `sal` and `brenda` agents — and leaves that branch untouched. The weekly rep review is
  built after it, on top of it.
- **What the weekly rep review may read — RULED 2026-09-28 (Parker, in session).** It may
  read a rep's own Sent Items **only when the rep runs it on themselves**. Business facts
  only: counterparty, agency domain, date, subject, attachment names and quote
  attachments. No personal mail, no sentiment, and no timing or volume surveillance
  metrics. Parker's team view covers **his own mailbox only**, and the output says so in
  words — it never implies coverage of anyone else's mail. Applies to the review when it is
  built; `bbs-weekly-sales-report` already reads only Parker's own mailbox. (The list of
  business facts above comes from §3.2 of the weekly-review brief, which Parker approved in
  session; it is the approved brief's wording, not his verbatim words.)
- **Reactive/proactive and new/repeat tags — RULED 2026-09-28 (Parker, in session):
  workbook-only.** They live in the rep review's workbook and nowhere else; **no new Sales
  CRM fields** are created for them.
- **What `bbs_accepted` means — RULED 2026-09-28.** Parker, in session: "I believe [it] is
  in State of CA Agencies and means the quote has converted." Checked live in the
  production CRM the same day: across 2,550 `bbs_rfqs` records created since 2026-01-01,
  `bbs_accepted` is never true, `bbs_orderfinalized` is never true, and no record has
  `bbs_ponumber` set. Home: `canonical-facts.md`, "What counts as a win" — Parker's stated
  intent is "converted" ("I believe"), to be confirmed before anything relies on it; never
  set in practice, so no skill counts a win from it today, and a report says "not recorded
  in CRM", never zero. `bbs-weekly-sales-report` (column "Accepted in CRM (unconfirmed)"),
  `ca-site-visit-brief` (and its `confidence-ledger.md`) and the `ca-territory-handoff`
  scoreboard say only that it is not a win source today and point there; none restates
  its meaning (PR #36 review). Closed. Original entry,
  kept for history: The
  territory work used the Sales CRM field two ways: `ca-site-visit-brief` said it is not a
  win flag, while `bbs-weekly-sales-report` counted it as a win and `ca-territory-handoff`'s
  scoreboard derived win rate from it. Until Parker rules, every skill takes the safe
  reading: `bbs_accepted` is **not** a confirmed win; the weekly report shows it as
  "accepted in CRM (unconfirmed)" and counts a win only on a BC quote `acceptedDate`, a
  converted order, or a quote-log Outcome of *won* confirmed by the rep. **Ask:** rule what
  `bbs_accepted` means. The ruling gets one home (canon or this register), and
  `bbs-weekly-sales-report`, `ca-site-visit-brief` and the handoff scoreboard all point
  there instead of each carrying the reading.
- **Is canon's "Dynamics 365 Sales" the BBS Sales CRM connector? — OPEN (raised in the
  PR #33 review, 2026-09-28).** Canonical facts' Systems of record table names "Pipeline /
  outreach — Dynamics 365 Sales"; the territory skills declare `sales-crm` (the BBS Sales
  CRM connector, Dataverse `bbs_rfqs`), which the checker WARNs as `system_not_in_canon`.
  **Ask:** if they are the same system, say so and the `sales-crm` registry entry in
  `scripts/check_marketplace.py` gets anchored to that canon row, clearing the WARN. If
  not, the Sales CRM needs its own canon row — Parker's call either way, since canon names
  BBS's systems.
- **Where `/ca-rfq` looks for rulings — RULED 2026-09-28: canon.** Parker, in session:
  "Yes" (to repointing it at `canonical-facts.md`). `/ca-rfq` ships to reps in `bbs-sales`
  without this repo's `docs/`, and its Gate 1 "an open ruling stops the run" looked for a
  *Ruled* table in `docs/PRODUCT.md` §9 that never existed. It now reads
  `bbs-foundations` `canonical-facts.md`, "Rulings on binding documents" — a *Ruled* table
  that points at where each rule lives, and an *Open* list — at Gate 0 (c), Gate 1 and
  *What this command deliberately does not do*; the stale "does not decide the open
  routing ruling at Gate 0 (c)" (ruled 2026-09-24) is gone. This register stays the
  maintainers' full record.
- **`docs/PRODUCT.md` is empty on main, and Parker has no content for it — noted
  2026-09-28 (Parker, in session). RESOLVED 2026-09-28: `lead-reviewer` repointed; file
  deleted in PR #36.** The reviewer (`rex`, `.claude/agents/rex.md`; `lead-reviewer` until
  2026-10-01) checks rulings against this register (*Already open
  for Parker*), merge order against *Tonight's slices*, and invariants against `AGENTS.md`.
  With `/ca-rfq` repointed at canon (above) and `README.md`'s two lines repointed at this
  file, nothing referenced it, so it is deleted.
  Original entry, kept for history:
  `.claude/agents/lead-reviewer.md` still tells the reviewer to check PRs against
  `docs/PRODUCT.md` §2 (what a rep should understand), §5 (merge order) and §9 (recorded
  rulings), none of which exist. A reviewer following it either skips those checks or
  holds a PR for a ruling it cannot find. **Recommendation:** repoint lead-reviewer's §9
  and §5 checks at this register (*Already open for Parker*, and *Tonight's slices* for
  merge order) and drop §2 or give it a real home, in its own PR — agent config is outside
  the territory PR's scope, so `lead-reviewer.md` is deliberately unchanged there.

- **The reviewer's GitHub identity — RULED 2026-10-01: COMMENT-style reviews accepted.**
  Parker, in session, asked whether Rex (the reviewer, `.claude/agents/rex.md`, renamed from
  `lead-reviewer` the same day) should get its own GitHub identity: "Accept COMMENT reviews".
  The build session and Rex both post as `pjm3wv`, so GitHub records neither an approval nor
  a "changes requested", and `main`'s branch protection requires no approval (PR #41 merged
  with none). So Rex posts every review as a COMMENT; one whose first line is
  "Request changes — do not merge" holds the PR exactly as a request-changes review would,
  and one whose first line is "Cleared — ready to merge" with the cleared head SHA clears it,
  and a green CI check alone is never a merge signal (`rex.md`, *Decide*). Rejected for now:
  a GitHub App or machine account for Rex plus one required approval on `main` — the
  stronger control, revisit if a merge ever lands without Rex's clearance. If a classifier
  or other safety control blocks a step (it blocked a post-merge `git fetch` in PR #41, and
  on 2026-10-01 blocked the build session from dispatching a reviewer to merge the build
  session's own PR), stop and report it to Parker; do not retry or route around it. ~~Parker
  merges when the session that dispatches Rex is also the PR's author.~~ Superseded
  2026-10-02 (next entry).

- **impeccable: install only the fork's `plugin/` folder, with its hooks off — RULED
  2026-10-01 (Parker, in session: "go with option A").** The entry was a `url` source with
  `"path": "plugin"`, but `url` sources take only `url`/`ref`/`sha`, so Claude Code ignored
  `path`, installed the whole fork and ran its Node install: 639 MB, 16,287 files, and the
  likely reason impeccable failed to install on Kim's Windows machine. It is now
  `git-subdir` (2.2 MB, 58 files). `plugin/` also ships PostToolUse (Edit|Write) and Stop
  hooks whose launcher downloads the engine binary from upstream `pbakaus/impeccable`
  releases on first run, outside the fork pin. The marketplace entry replaces both with
  no-ops, which entry `hooks` do per event; verified with `claude -p` that neither fires
  and nothing is downloaded. `IMPECCABLE_HOOK_DISABLED` was rejected: the binary reads it
  only after the launcher has downloaded it. The skill still runs that same launcher
  (byte-identical, engine 0.1.5) when a rep invokes `/impeccable`, as it did before. The
  `plugin/` build also adds four agents (`impeccable-finish-reviewer`, `-documenter`,
  `-manual-edit-applier`, `-asset-producer`).

- **Grainger on a prime when the account manager grants no discount — OPEN (raised in the
  PR #34 review, 2026-09-28).** Canon's prime row says the rep prices "from that
  discounted cost" and "never invent a discount"; it does not say what the cost is when
  none is granted. The natural reading is the Grainger MCP `unitPrice`, but that is a
  price rule, so no skill writes it until Parker confirms. **Ask:** confirm, and the
  answer goes into canon's "Grainger sell rule, by channel" prime row, not into a skill.
- **Address spelling in `vendor_profile.json` — OPEN (2026-09-28).** The profile holds
  `1950 Cordell CT Ste 103`, which every filled form prints. **Ask:** confirm the spelling
  and case as registered (e.g. with OSDS), so binding forms match the certification record.
- **Bechtel's home in this repo, and the BC write-API scripts — OPEN (2026-09-28).**
  Bechtel is the only customer outside State of CA agencies with the same folder
  structure (Parker, in session); its desk `CLAUDE.md` lives on SharePoint, not here, and
  the scripts that write to Business Central have no declared home. **Ask:** where
  Bechtel's desk context and those scripts are maintained. #35 depends on the answer.
- **The macOS bootstrap installs no pip or npm libraries — RESOLVED 2026-10-01, this
  session's rep-setup PR** (`bbs-setup.sh` now installs pypdf/pymupdf/openpyxl for `python3`,
  `docx`/`pptxgenjs` with NODE_PATH in `~/.zprofile`, links `soffice`, and installs the
  plugins). Original entry:
  `scripts/bbs-setup.ps1` installs `docx` (npm; `bbs-quote-builder` needs it) and the
  Python libraries the form-fill scripts import; `scripts/bbs-setup.sh` installs no npm or pip libraries; its only Python piece is `uv`.
  A Mac rep's first quote or packet run fails on a missing module. **Fix:** mirror the
  Windows npm and pip steps in `bbs-setup.sh`, in its own PR.
- **Carried from the 2026-09-16 session task list, evidence not re-verified — OPEN.**
  (a) Account-synced office skills (`docx`, `pdf`, `xlsx`, `pptx`) in Parker's claude.ai
  account may shadow the pinned `document-skills` copies. (b) Slice 3 closed with a
  second packet profile, but no real second customer packet has been run through it.
  Verify each before acting; the `skills:` filter and `caveman-init` findings are
  recorded in `docs/COMMONS.md`.
- **R1 — delegated signing scope — RULED 2026-10-01.** Parker, in session: "Our team has
  been given broad discretion by counsel to sign for each other on anything under $250,000
  and any form that is involved in that process for quoting." Supersedes the 2026-09-16
  delegation (Parker and Jackson only) for the forms the skills fill. Counsel's written
  authorization is filed physically at BBS; the repo records only its date (2026-10-01, as
  given to Parker in session) and its scope — the six people (R1a), a quote under $250,000
  including tax (R1b), forms in the quoting process — in `vendor_profile.json`
  `signature_delegation`, never as a reference to a file. Rule home: `ca-form-rules.md`,
  "Delegated signatures". Claude still drafts; a person reviews and sends (invariant 5).
- **R1a — the team: six people — RULED 2026-10-01.** Parker, in session: Griffin, Parker,
  Joey, Kim, Aanya and Jackson, and no one else; Joyce Newell, Jeff Azar and Amy Leath are
  **not** delegates. Names, titles and emails were read the same day from BBS's Microsoft
  365 directory and each person's own email signature, never inferred from a name pattern:
  Griffin Forsyth, Vice President, griffin@; Joey Magliato, Account Manager, joey@; Kim
  Quezon, Account Manager, kim@ (the directory still says "Intern"; Parker ruled "Account
  Manager"; Kim is a man — he/him); Aanya Samarasinghe, Account Manager, aanya@; Parker and
  Jackson as already recorded. Home: `vendor_profile.json` `authorized_representatives` and
  `signature_delegation`. **For Parker:** correct Kim's M365 job title.
- **R1b — the $250,000 limit is the quoted price including tax — RULED 2026-10-01.**
  Parker, in session. The measure is the quote's grand total, tax included, as on the quote
  of record (the Business Central sales quote / the SQ the rep sends). A delegated signature
  is applied only when that total is **strictly under $250,000**; at or over it, or when the
  total is missing or unreadable, no delegated signature is applied — the line is left blank
  and flagged. The total comes from the quote of record, never an estimate. Enforced in code
  by the form scripts; the figure lives once, in `vendor_profile.json`
  `signature_delegation`.
- **R2 — signature form: the PNG of record — RULED 2026-10-01.** Parker, in session: the
  **signature image**, which each person provides. Both paths stamp the PNG; the typed-name
  "signature" `fill_obs_packet.py` wrote into the signature fields (verified 2026-10-01 at
  `:207`, `:383`, `:437` — the delegate's name as text, which Kim reported) goes.
  **R2a — where the PNGs live (the session's choice, made 2026-10-01):**
  `MASTER/Signatures/<first>-<last>.png` in the synced `Black Box Safety - MASTER` library,
  e.g. `MASTER/Signatures/kim-quezon.png`, so every machine has them through OneDrive.
  Parker's image sat inside a Bechtel RFP folder and broke once when that folder was renamed
  (2026-09-28); Jackson's was at `MASTER/Jackson Dalton Signature/Copy of JACKSON_SIG.png`.
  **For Parker:** copy both into `MASTER/Signatures/` as `parker-marshall.png` and
  `jackson-dalton.png` before this PR's profile change reaches a rep. Every other
  `signature_image` is `null` until that person's PNG is in place, and the scripts refuse to
  sign as anyone whose image is missing. The PNG spec is in `docs/ADMIN-RUNBOOK.md`.
- **R3 — Jackson's owner declarations stay Jackson's — RULED 2026-10-01.** Parker, in
  session. DGS PD 843, CV 012, STD 204 and STD 205 carry Jackson's image whoever runs the
  packet. The team ruling (R1/R1a) widens who may *run* a packet, not whose declaration those
  lines are. Rule home: `ca-form-rules.md`, "Who signs what".
- **R4 — where control lives: Parker's machine, pushed out — RULED 2026-10-01.** Parker, in
  session: "I want to ensure that I have all the managed settings and things I can control
  from my machine and then be disseminated out all set up." Everything that can be set
  centrally goes in `plugins/bbs-foundations/docs/bbs-managed-settings.json`, which Parker
  pastes in the claude.ai admin console (`docs/ADMIN-RUNBOOK.md` §1). Nothing is merged into
  a rep's own `~/.claude/settings.json`. `/bbs-checkup` stays read-only: it verifies, it
  never writes.
- **R5 — "complete the packet" is the approval to sign — RULED 2026-10-01.** Parker, in
  session: "the bbs employee says 'complete the packet' and there is implicit knowledge that
  that means you can sign everywhere that the skills know to sign for the people that are
  relevant for the solicitation (rep and jackson typically)." No separate per-run
  confirmation step: the request is the authorization, within R1–R3 (the six, under the
  limit, the right signer on each line). Rule home: `ca-form-rules.md`, "Delegated
  signatures".
- **OBS 1000 (GenAI factsheet) is a rep-signed line — RULED 2026-10-01.** Parker, in
  session, asked whether R1's "any form that is involved in that process for quoting" makes
  OBS 1000 rep-signed: "Yes, rep-signed". Closes the open question recorded under *Who signs
  the rep-signed lines* (above). Canon, `bbs-grounding-doctrine.md` and `bbs-doctrine.md` were updated to match on
  2026-10-01 (Parker, in session: "you make the canon and doctrine edits"), after the
  auto-mode classifier had refused the first attempt.
- **OBS 4007(C) front page on an LPA order: DVBE box ticked, cert number given — RULED
  2026-10-01.** Parker, in session: "Tick DVBE + cert #". The box identifies BBS's
  certification (OSDS 2009473) for the agency's DVBE reporting; SB and MB stay unticked, and
  no incentive is claimed — the DVBE incentive is still never claimed on an LPA/NASPO order.
  Certification logic is otherwise unchanged.
- **CDCR Packet C arrives partly filled and must be assembled — RULED 2026-10-01.** Parker,
  in session: "You should aggregate the other forms and be able to handle inbound documents
  that have some of the forms filled out with customer information. That is how it will
  typically work in practice." The 4007(C) profile recognises each bound form by its own
  text, and the fill keeps every value the agency already entered.
- **How auto mode lets the vetted form scripts run — RULED 2026-10-01: the `bbs-tools`
  launcher.** Parker, in session, chose "New bbs-tools launcher" after the Claude Code docs
  were checked the same day: a `*` in a `Bash()` allow rule matches anything, spaces
  included, and an allow rule overrides auto mode's classifier, so a path-pattern rule such
  as `Bash(python *…/fill_obs_packet.py *)` could be satisfied by a crafted command (one
  planted in an inbound agency PDF, say) and run arbitrary Python. Instead the managed
  settings allow exactly `Bash(bbs-fill *)`; `plugins/bbs-tools/bin/bbs-fill` runs only its
  allow-listed scripts, from the same marketplace's installed `bbs-sales`, with a fixed
  interpreter and no interpreter options. Its own plugin because claude.ai and Cowork do not
  install a plugin with a `bin/` folder. Rejected: path-pattern rules (bypassable), and no
  allow rule (Kim's original stop).
- **Kim's `ca-grainger-rfq`, `recalc_excel.ps1` and `PDF_Tools` — OPEN (2026-10-01).** Kim
  named them for the allow list; none exists in this repo. Parker, in session: "Don't know —
  skip". No permission rule is written for a name nobody can verify. **Ask:** find out from
  Kim what each is (an account-synced skill, a local script, a connector) before any rule.
- **Microsoft 365 tools that send without being "send" tools — RULED 2026-10-01.** Raised in
  the PR #44 review. Parker, in session, chose "Deny rules + vacation, ask events": the
  managed settings **deny** `outlook_create_filter` (an inbox rule can auto-forward mail)
  and `outlook_set_vacation` (auto-replies go to everyone who writes), and **ask** before
  `outlook_create_event`, `outlook_update_event` and `outlook_delete_event` (each emails
  invites, updates or cancellations to attendees). Home:
  `plugins/bbs-foundations/docs/bbs-managed-settings.json`; explained in
  `MANAGED-SETTINGS.md`.
- **The team-rollout page covers Sales — RULED 2026-10-01.** Parker, in session: "I want
  sales to be included as well", then chose one shared Sales card for Kim, Aanya, Joey and
  Griffin with four rows (`/ca-rfq` to packet, Grainger and NASPO pricing, visit and account
  prep, weekly report and follow-up drafts); later added a federal deck row for Griffin
  (`bbs-deck-voice`), SAM.gov for Kim and Griffin, and "a way for an agent to internet
  search ... without a window" (shown as the existing `supplier-scout` agent). SAM.gov has
  no skill, so the page shows it as Not built yet. Page: PR #46. Building the SAM.gov skill
  and a general web-research agent is deferred to a separate session (Parker: "we will do
  that separately").
- **Team-rollout page: impeccable's product interview skipped — RULED 2026-10-01.** Parker,
  in session, chose "Build, infer from brief": product context comes from the build prompt
  and `brief.md`; no PRODUCT.md or DESIGN.md is committed.
- **Team-rollout page, signature wording — RULED 2026-10-02.** Parker, in session: "Claude
  can sign it for outside sales, that is the point. They do not need to know about counsel,
  just that claude can sign the packets for them. make it more direct and simpler." Tile 3
  is seen by every reader, so it is scoped to Sales (PR #50 review): "If you're in Sales,
  Claude signs your packets once Parker has your signature on file. It signs each line as
  the right person, and never for a customer. Anything it can't sign comes back flagged.
  Outside Sales, it doesn't sign for you." "Each line as the right person" covers Jackson's
  owner lines (R3, R5); "Outside Sales" keeps the six non-delegates out (R1a).
  The RFQ row says it signs the packet and flags what it can't sign. Page copy only: the
  signing rules themselves stay R1, R1a, R1b, R2 and R5, unchanged. All four Sales readers'
  `signature_image` is null today, so until their PNGs are filed their lines come back
  flagged, which the "once Parker has your signature on file" clause covers.
- **Team-rollout page, Joey Magliato's picker line — OPEN (2026-10-01).** Canon records only
  his title, so "Customer accounts and quotes" is the build session's wording. **Ask:**
  Parker confirms or replaces it (one string in `PEOPLE`).
- **Reading files in Claude Desktop, and where "humans send" holds — RULED 2026-10-02.**
  Parker, in session, asked for a setting "so that users can read files in claude desktop",
  chose "Both" (the Code tab and the chat window) and approved a managed allow rule
  `Read(~/**/*Black Box Safety - MASTER/**)`. Rex's review of PR #47 found the premise wrong:
  the managed settings already allow bare `Read`, which "matches all file reads", so Claude
  Code already reads MASTER, and every other file the person can open, without a prompt.
  The rule was dropped and the docs corrected (PR #47). The chat window and Cowork never
  receive server-managed settings, and in the Desktop app's Code tab the docs say connectors
  arrive directly from the app, where our `mcp__claude_ai_…` deny rules are not documented
  to match and the console's `blocked` control is what applies. Parker then ruled, in
  session: "a keep, b no, c yes, d yes":
  (a) **keep bare `Read`**; (b) **no** `Edit` ask rule on MASTER (the quote desk writes
  packets there); (c) **yes**: the `.env` denies also cover the whole home folder
  (`Read(~/**/.env)`, `.env.local`, `.env.production`, in `bbs-managed-settings.json`);
  (d) **yes**: every connector tool the managed deny list names is also set to `blocked` in
  the claude.ai admin console (`docs/ADMIN-RUNBOOK.md` §3), so "humans send" holds on the
  Desktop app (Code tab and chat); Cowork coverage is unverified. Parker's test send from a
  Desktop Code-tab session was denied the same day ("it is blocked"); what denied it is not
  shown, so (d) stands. `AGENTS.md` invariant 5 ("On Claude Code, managed settings deny the
  send-class tools") is documented only for the terminal and VS Code; it is not edited here
  (Parker's call). A rep who answers "No, and block reads … from now on" to the first-read
  prompt loses reads outside the opened folder until
  `permissions.blockReadsOutsideWorkingDirectories` is removed from their
  `~/.claude/settings.json` and a new session is started (`/add-dir` re-opens one folder at
  a time meanwhile); `/bbs-checkup` does not detect it yet.
- **`so-search` and `bbs-po-status` move onto the Business Central connector — RULED
  2026-10-02.** Parker, in session: "The business central purchase order finding should
  work", then "Yes" to doing the retarget. This overrides the README's earlier "do not
  retarget those two skills onto `bc_*`". Both now use `bc_query_entity` (read-only):
  `salesInvoices` filtered on `customerPurchaseOrderReference` returns `orderNumber`;
  `purchaseOrders` with `expand=purchaseOrderLines` returns line-level received and invoiced
  quantities. Verified live the same day. Two behaviours the skills now state: Business
  Central text search is case-sensitive and `tolower()` returns nothing silently, and
  `purchaseOrderLines` cannot be queried without its parent. `requires:` is
  `business-central` for both; the retired `bc-mcp-proxy` is required by nothing.
  `bbs-rebate-profitability` stays on CData; this ruling does not cover it.
- **Rex merges what it clears, whichever session dispatched it — RULED 2026-10-02.**
  Parker, in session: "enable rex to conduct merges himself going forward for all session".
  This supersedes "Parker merges when the session that dispatches Rex is also the PR's
  author" (2026-10-01 entry above). Rex squash-merges any PR it has cleared on its own
  reading, including one written by the session that dispatched it, as long as Rex did not
  write or push content to that PR (`rex.md`, *Never*). Everything else in `rex.md` *Decide*
  still holds: both checkers at exit 0, a recorded ruling for any binding-document change,
  no removed control, and a "Cleared — ready to merge" COMMENT with the head SHA before the
  merge. The build session still never merges its own PR, and still never edits a PR Rex is
  reviewing. Parker merged PR #50 himself on 2026-10-02, by instruction in session, after
  both reviews' findings were fixed and CI was green.
- **Federal lookups: SAM.gov and USAspending skills — BUILT and RULED 2026-10-02.** Built
  the item Parker deferred on 2026-10-01 (see "The team-rollout page covers Sales" above).
  - **Skills.** `bbs-sales` gained two read-only skills:
    - `sam-gov-opportunities`: open federal notices, through SAM.gov's Get Opportunities API.
    - `usaspending-awards`: past contract awards, top vendors, reported subawards and BBS's
      own history, through the public USAspending search API.
  - **PRs.** Both registry entries (`sam-gov`, `usaspending`) are in the review-side PR
    [Black-Box-Safety/bbs-claude-marketplace#51](https://github.com/Black-Box-Safety/bbs-claude-marketplace/pull/51).
    The skills PR is stacked on it.
  - **Design.** `docs/superpowers/specs/2026-10-02-sam-gov-opportunities-design.md`.

  Parker's rulings, in session, 2026-10-02:
  - **(a) USAspending comes into the marketplace.** "I want it to incorporate and create a
    skill for usaspending API too." The README had said "Not in this marketplace". Cursor's
    `bbs-usaspending` MCP stays as it is.
  - **(b) One SAM.gov account, one shared key.** "It will all link to the same sam.gov
    account, we dont need multiple." Parker supplies the value for each machine's
    `SAM_GOV_API_KEY`. The whole team shares one daily request budget.
  - **(c) Both scripts run without a prompt.** "yes it can run without a call". They are
    added to the `bbs-fill` allow list. They write no file; each makes network GETs to
    SAM.gov, or search POSTs to USAspending.
  - **(d) No Systems of record row.** "no it doesnt need a SOR". SAM.gov and USAspending are
    public data sources. The two `system_not_in_canon` WARNs are therefore expected and
    accepted.
  - **(e) BBS is VOSB.** "yes we are VOSB". This is now in canon's certification table, and
    VA VSA/VSS set-asides read "Eligible".
  - **(f) Federal codes.** Parker attached screenshots of BBS's NAICS, PSC and GSA SIN codes.
    They are now in canon, "Federal codes", as their single home.

  Parker's follow-up rulings, in session, 2026-10-02:
  - **(g) GSA MAS ultimate end date is 2042.** "for GSA use 2042". Canon's vehicle row now
    reads current option period to 11/14/2027 and ultimate end 11/14/2042. This supersedes the
    "No 'ult. 2042'" line. The storefront doctrine's restatement was corrected to match.
  - **(h) SDB is never claimed.** "dont do small disadvantaged business". This holds even
    though the GSA record lists "SBA Certified Small Disadvantaged Business".
  - **(i) The PSC list is complete.** "the PSC list is correct". The flag is removed from
    canon.
  - **(j) The shared key is the entity account's.** "parker@blackboxsafety.com is the
    entity". So it is on the 1,000-requests-a-day tier.
  - **(k) Key expiry.** The current key was issued 2026-10-02, valid 89 days, through
    2026-12-30. Canon, "Federal codes", records the account and the expiry date, never the
    value.
    - **Declined: storing the key in this repo.** Parker asked to "store that to the bbs
      claude marketplace". The key's value was not written to git, because AGENTS.md
      ("Credentials stay out of git — API keys") and invariant 2 put credentials outside the
      repo. It goes in each machine's `SAM_GOV_API_KEY`.
    - **Not done: a live test.** A one-request live test with the key, from the build
      container, was refused by the auto-mode permission classifier. The SAM.gov script is
      still unverified live.
  - **Set-aside size flag (Rex, PR #52 review).** Every SDVOSB, VOSB and small-business fit
    line reads "Eligible" and also carries a flag to confirm BBS is small under that NAICS
    size standard, because all three are small-business programs. This is not a new ruling:
    it is the stricter reading of (e) and of canon. **Ask:** Parker confirms the flag stays.
  - **(l) The key reaches machines through the bootstrap, not the repo.** Parker, in
    session: "Add the api to the GitHub repo so it's accessible through there. I haven't run
    the install yet." The value is not committed (AGENTS.md, credentials). Instead,
    `bbs-setup.ps1` and `bbs-setup.sh` ask for the key with hidden input, never print it, and
    save it as `SAM_GOV_API_KEY`: the user environment on Windows, `~/.zprofile` on a Mac. Enter
    skips. The Mac script refuses anything but letters, digits, `-` and `_`, so a paste cannot
    break out of the profile line.
    - **Opt-in.** Parker, in session: "yes fix 1 and 2". The prompt now runs only with
      `-SamGov` / `--sam-gov`, so people who never use SAM.gov are neither asked nor shown it
      as undone. On Windows, a run with redirected input or `-NonInteractive` skips quietly
      instead of erroring. Rex's PR #56 finding 3, the plain-text key readable by Claude, is
      accepted ("3 is fine").
    - **A GitHub Actions secret would not do this job.** Only workflows can read one; an
      install cannot.
  - **`bbs-tools` 0.2.0.** The two scripts reach installed machines only through the
    version bump, so `bbs-tools` moves to 0.2.0 with the allow-list change.
---

Owner: Parker Marshall. Last verified 2026-10-02.
