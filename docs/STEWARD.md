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
- **Grainger at-cost vs the old margin practice — RULED 2026-09-18; confirmed RULED
  2026-09-28.** Grainger at cost is the standing pricing rule. Parker, in session,
  2026-09-28: "confirmed". It was said to be recorded in `docs/PRODUCT.md` §9, which is
  empty; its home is now `canonical-facts.md`, Systems of record, the Grainger row
  (`unitPrice` from the Grainger MCP is the customer price, never marked up), and
  `grainger-pricing` points there. Live files checked for markup/margin language on
  Grainger or NASPO: `grainger-pricing`, `naspo-quote`, `ca-rfq-intake`, the `bbs-sales`
  README, `bbs-doctrine.md`, the managed `claudeMd`, `supply-lane-tuning`, `quote-bot` and
  `bbs-order-reconciliation` all agree. **One does not:** `bbs-quote-builder` states a 20%
  gross-margin house default with no Grainger exception (`SKILL.md:69-71`). It is being
  changed by a separate worker and was deliberately not edited here; `grainger-pricing`
  already tells a rep not to let that math touch a Grainger line.

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

**Blocked on Aanya — RULED 2026-09-28.** Parker, in session: "Aanya will provide." Until
she does, `dgs-bpo-item-check` keeps the FY25–26 list, and every answer now opens with the
list it checked against plus a `⚠ STALE LIST` line once that fiscal year has ended
(`check_items.py`, `BPO_LIST_*`). No list is synthesized.

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
- **Who certifies the CalRecycle 74 — RULED 2026-09-18: the rep who quoted the job;
  superseded, RULED 2026-09-28: any BBS employee preparing the bid.** Parker, in session:
  "anyone is permitted to sign". The two authorities that disagreed — canon's People table
  ("Griffin … most CalRecycle 74s"; "Parker … CalRecycle 74 on his own RFQs") and
  `ca-form-rules.md` ("Certified by the rep") — now say the same thing, and the rule lives
  once, in `ca-form-rules.md`'s CalRecycle 74 row: any BBS employee preparing the bid signs
  as BBS's representative, never a customer, agency or third party; the rep confirms the
  certification content; a skill applies the signature only for a delegate in
  `vendor_profile.json` `signature_delegation` (Parker, Jackson — counsel, 2026-09-16) and
  otherwise leaves signature and date blank and flags `⚑ SIGNATURE REQUIRED`; never
  Parker's or Jackson's signature on another rep's form. `fill_obs_packet.py` implements it
  (`calrecycle74_signer`), refuses a non-BBS signer, and `test_fill_obs_packet.py` executes
  it. Canon, `naspo-quote` §5, `field-maps.md` and the `bbs-sales` README point at it.
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
  `bbs_ponumber` set. Home: `canonical-facts.md`, "What counts as a win" — intended
  meaning converted; never set in practice, so no skill counts a win from it today, and a
  report says "not recorded in CRM", never zero. `bbs-weekly-sales-report`,
  `ca-site-visit-brief` (and its `confidence-ledger.md`) and the `ca-territory-handoff`
  scoreboard now point there instead of saying "not yet ruled". Closed. Original entry,
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
- **`docs/PRODUCT.md` is empty on main, and Parker has no content for it — noted
  2026-09-28 (Parker, in session). RESOLVED 2026-09-28: `lead-reviewer` repointed.** It
  now checks rulings against this register (*Already open for Parker*), merge order
  against *Tonight's slices*, and invariants against `AGENTS.md`; the §2 pointer is dropped
  and its question kept in words. `docs/PRODUCT.md` is **not** deleted: `README.md` (two
  lines) and `plugins/bbs-sales/commands/ca-rfq.md` (Gate 0 (c), Gate 1, and *What this
  command deliberately does not do*) still point at it. `/ca-rfq` Gate 1's "an open ruling
  stops the run" looks for a *Ruled* table in §9 that does not exist — **open for Parker**:
  where `/ca-rfq`, which ships to reps without this repo's `docs/`, should look for rulings.
  Original entry, kept for history:
  `.claude/agents/lead-reviewer.md` still tells the reviewer to check PRs against
  `docs/PRODUCT.md` §2 (what a rep should understand), §5 (merge order) and §9 (recorded
  rulings), none of which exist. A reviewer following it either skips those checks or
  holds a PR for a ruling it cannot find. **Recommendation:** repoint lead-reviewer's §9
  and §5 checks at this register (*Already open for Parker*, and *Tonight's slices* for
  merge order) and drop §2 or give it a real home, in its own PR — agent config is outside
  the territory PR's scope, so `lead-reviewer.md` is deliberately unchanged there.

---

Owner: Parker Marshall. Last verified 2026-09-28.
