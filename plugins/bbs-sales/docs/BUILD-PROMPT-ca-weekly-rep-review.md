# Build prompt — `ca-weekly-rep-review` (bbs-sales)

**How to use this file.** Open Claude Code in `~/bbs-claude-marketplace` and say:
"Read `plugins/bbs-sales/docs/BUILD-PROMPT-ca-weekly-rep-review.md` and build what it
describes. Use the skill-creator skill." Everything below is the brief for that session.

Written 2026-09-28 by Parker Marshall with Claude, from a hand-run reconciliation of the week of
21 September 2026 across email, Business Central, the Sales CRM and the quote folders. That run
is the worked example this skill must reproduce. Its output is at
`Customers/State of CA Agencies/Weekly Summaries/2026-09-21 Weekly Quote Report - CA State.xlsx`.

---

## 0. Who you are while you build this

You are building this as a **sales manager whose job is to grow reps who are new to their
book** — not a manager who audits activity. Aanya Samarasinghe has never held a sales role.
Kim Quezon has never carried a book this size. Both inherited accounts a departed rep let
drift. Growth sales, for them, means turning buyers they are new to into buyers who call them
first: a second named contact, a recorded reorder rhythm, the adjacent category, the facility
down the road in the same department. Answering inbound RFQs is the floor, not the job.

So the skill you are building is a coach's tool. It shows a rep their own week back to them,
more completely than they could assemble it themselves, and then helps them decide what to do
with the next one. If a rep reads its output and feels watched, the build failed, even if every
number is right.

## 1. The job, in one paragraph

Every Monday, for one rep (or the whole CA state team), reconstruct the week that just closed
from four sources — the rep's own email, Business Central, the Sales CRM, and the quote
folders — and summarize it in four parts: **customers** touched, **volume** (count and dollars),
**type** (vehicle, reactive vs proactive, new vs repeat buyer), and **outstanding work**. Then
turn that into the agenda for Parker's Monday meeting with Kim and Aanya: what each rep must
handle reactively this week, and the three to five proactive growth moves they will make, each
with a named buyer, a reason, the opening words, and a definition of done.

## 2. Read these before writing anything

In the repo:

- `plugins/bbs-sales/skills/bbs-weekly-sales-report/SKILL.md` — the existing manager-side
  weekly report. The new skill must not duplicate it; see section 9.
- `plugins/bbs-sales/skills/ca-territory-handoff/` — especially `references/scoreboard.md`
  (definition of done, leading indicators, where each is readable) and
  `references/opening-lines.md`.
- `plugins/bbs-sales/skills/ca-budget-timing/SKILL.md` — for any date the plan depends on.
- `plugins/bbs-sales/skills/ca-rfq-intake/SKILL.md` and `naspo-quote/SKILL.md` — folder layout,
  `quote-log.md` format, what a BBS quote looks like.
- `plugins/bbs-sales/agents/sal.md` — the "reps are new to this" constraint, stated well.
- `plugins/bbs-sales/docs/TRIGGER-CHECK.md` — the collision-check method you will repeat.

Outside the repo (OneDrive, `Customers/State of CA Agencies/`):

- `CLAUDE.md` at the desk root — money rules, landmines, "Outcome is not optional".
- `.sales-team/README.md` — the six agents and where their work lands.
- `.sales-team/sal/kim-intro-ladder/` — `account-tracker.md`, `call-log.md`,
  `the-moments-and-the-words.md`, `week-one.md`.
- `.sales-team/sal/aanya-territory-guide/` — `CLAUDE.md`, `CONTEXT.md`,
  `scoreboard/90-day-measures.md`, `scoreboard/CONTEXT.md`, `05-follow-up/references/cadence.md`.
- `.sales-team/sloane/intro-30-day/scorecard.md` and `quote-triage-kim.md` — the live campaign
  (16 Sep – 14 Oct 2026) and what each rep is judged on during it.
- `Weekly Summaries/2026-09-21 Weekly Quote Report - CA State.xlsx` — the worked example.

Skills: `ca-state-sales-grounding` (invoke at the start of every run, and never restate it),
`skill-creator`, and the sales craft skills listed in section 7.

**The reps already have scoreboards.** Aanya's 90-day measures and the intro-30-day scorecard
define what they are held to: live conversations (~12 a week), two named contacts per top
account, reorder rhythms recorded, quotes submitted on or before due, and zero blank
next-action dates. The weekly review reports against those. Do not invent a new metric set.
If you think one is missing, propose it to Parker in the build summary instead.

## 3. Helpful, not invasive — the design rules

These are requirements, not tone guidance.

1. **The rep runs it on themselves.** Mailbox connectors are per-user and there is no delegate
   access to Kim's or Aanya's mail. The email section exists only when the rep runs the skill in
   their own session. When Parker runs the team view, the email half covers his own mailbox
   only, and the report says so in one line: "Email evidence covers Parker's mailbox only."
   Never imply coverage you do not have.
2. **Business mail only.** Read Sent Items and customer threads for business facts:
   counterparty, agency domain, date, subject, attachment names, and quote attachments. Never
   quote personal mail, never summarize internal conversation about colleagues, never score
   tone or sentiment, and never report when someone was online, how fast they replied by hour,
   or how many emails they sent. Those are surveillance metrics and they teach the wrong thing.
3. **"Here is what the systems show — tell me what I missed."** Every rep-facing section ends
   with a confirm/correct prompt. The rep's corrections win over the systems, and the skill
   records them.
4. **Found-but-not-logged is offered as help, never as a gotcha.** When email shows a request
   with no CRM record or folder, the skill writes: "This came in on 9/23 and isn't in the CRM
   yet — want me to draft the record and the folder?" It then drafts; it does not file.
5. **Wins first.** The rep-facing review opens with what went well, specifically: a first
   quote to a new buyer, a same-day turnaround, a large quote, a likely win.
6. **No rep-vs-rep ranking in anything a rep reads.** The team rollup is Parker's, and even
   there the existing rule holds: say why before who. A bad-looking week on this book is usually
   a departed rep's collapsed territory, not the person in the chair.
7. **Drafts only.** Proposed `quote-log.md` rows, `call-log.md` rows, `account-tracker.md`
   next-action dates and CRM entries are written as drafts for the rep to accept. Nothing is
   written to Business Central or Dataverse, ever. Nothing is sent.
8. **Activity is the measure in the first ninety days.** Revenue and win rate are Quinn's,
   monthly. The weekly review does not grade a new rep on week-three revenue.

## 4. What the review reports

For one rep, one week (Monday–Sunday, filed under the Monday date).

### 4a. Customers
- Every agency, facility and named buyer the rep quoted or corresponded with.
- **New vs repeat buyer:** first BBS quote to this buyer in 12 months (check the buyer
  folder's `quote-log.md`, filled packets and BC quote history) is a **new buyer** and is the
  headline growth number.
- Coverage against the rep's account tracker: which top accounts now have two names, which
  still have one.

### 4b. Volume
- Quotes completed, pre-tax dollars, average, largest.
- Response time: CRM received → submitted, and on-time against due.
- A separate one-line "other work" count for anything outside the state book (federal, primes,
  private). It is still the rep's effort and gets acknowledged, but it stays out of state
  figures.

### 4c. Type
- **Vehicle:** NASPO / MRO LPA 7-25-51-02.03 (sells at cost), open market or Fair & Reasonable,
  SB/DVBE Option, DGS BPO, other. Read it off the quote; if the quote does not state it, say
  "not recorded" rather than inferring it.
- **Reactive vs proactive:** reactive = answered an inbound request. Proactive = the rep started
  it: a call-log conversation, a campaign touch, an outbound email to a buyer with no open
  request, a quote that came from a reorder-timing call. The proactive share is the second
  headline growth number.
- **What the quote leaves open:** for each quote, did it produce a second name, a recorded
  reorder rhythm, or a next need? A quote that did none of those is a door that was not walked
  through.

### 4d. Outstanding work
- Open requests with due dates, past due flagged first.
- Quotes out awaiting decision, with the follow-up touch due this week under the rep's cadence
  (Day 1 recap, Day 3 deliver, Day 7 new information, Day 14 status, Day 21 closing question,
  then a decision — from `05-follow-up/references/cadence.md`).
- Outcomes to record (won / lost / no answer), including likely wins found in BC.
- Data fixes, as drafts with an owner.

### 4e. The growth lens — what the coach adds
For each rep, three to five **proactive plays** for the coming week, no more. Each one has:
account and facility, a named buyer (or "find the name" as the step), **why now** (reorder
timing, a budget window from `ca-budget-timing`, whitespace, a second name missing, a quote that
opened a door), the **moment** and opening words from `the-moments-and-the-words.md` or the
handoff's `opening-lines.md`, a time block, and a definition of done from
`ca-territory-handoff/references/scoreboard.md`.

Sources for plays, in order of trust: the rep's own tracker and call log; last week's quotes
(every quote is a reason to call back); BC order history for reorder gaps; the SCPRS tools
(`play_reorder_timing`, `play_receptive_buyers`, `play_category_whitespace`,
`play_buyer_profile`, `play_goal_gap_targets`) — and any SCPRS figure carries its slice label,
never "the market".

## 5. The Monday meeting pack

One agenda for Parker, Kim and Aanya. About 45 minutes, per-rep blocks of about 15.

1. **Wins and what worked** (2 min per rep) — specific, from 4a–4c.
2. **Last week against your scoreboard** (3 min) — their own measures, with the trend from prior
   weeks' rows (`output/weekly-numbers.md` for Aanya; add the equivalent for Kim if absent).
3. **Reactive this week** (4 min) — due dates in order, follow-up touches due, POs to confirm,
   past-due decisions.
4. **Proactive this week** (5 min) — the three to five plays from 4e. The rep picks; the coach
   does not assign all five.
5. **One thing to practise** (1 min) — one learning measure from the 90-day list, tied to a real
   call this week (explain the SB/DVBE Option; use the encumbrance rule on a buyer who thinks
   they are out of time).
6. **Blockers and asks for Parker** — including every "Parker tick" item in Kim's tracker.
7. **Commitments** — each one becomes a dated next action in the rep's tracker, drafted for the
   rep to accept after the meeting.

Add a **capacity check**: working days × protected calling mornings against due quotes plus
planned calls. If the arithmetic does not work, say so before the meeting rather than letting a
rep commit to a week that cannot happen. Add **three open coaching questions** per rep for
Parker to ask ("What did Etcheverry say about the next field-season order?"), not interrogation
questions ("Why wasn't this logged?").

## 6. Evidence and reconciliation — what the week of 21 September taught

Put this in `references/four-source-reconciliation.md`. It is the part of the skill that took a
day to learn by hand, and every item below was a real miss in that run.

**No single source is complete.** The hand run found 34 state quotes. The CRM alone showed 28 and
misattributed some; the folders alone showed 30 and counted one vendor quote as ours; BC alone
missed most of them and showed $0 on several; email alone found three requests nobody had
logged. Reconcile all four, every time, and say which source each row rests on.

### Sales CRM (Dataverse `bbs_rfqs`, production org)
- Owner is `_ownerid_value`. `bbs_accountidname` is not selectable — select
  `_bbs_accountid_value` and read its `@OData.Community.Display.V1.FormattedValue`.
- `createdon` is UTC. Convert to Pacific before deciding which week a record belongs to.
- Failure modes seen: records missing entirely (DAPO CCU SQ-104896; DSH Coalinga SQ-104968; CHP
  Avon kits; PDC phone booths); a submitted date earlier than the record's creation
  (RFQ-005224); marked submitted when the quote had not been sent (RFQ-005238, Cal Fire
  Redding); not marked submitted when it had been built (RFQ-005231, DSH Metro beds,
  $95,829); round-number estimates instead of the quote total (Kim's rows, e.g. RJD $20,000 vs
  the quote's $17,426.18); $1 placeholder records; the CRM owner is not always the person who
  did the work.
- `bbs_accepted` is false on nearly every record, so win rate is not measurable from it yet.
  Capturing outcomes is a habit the review should build, not a number it can report.

### Business Central (`salesQuotes`)
- Filter on `documentDate`. The field is `salesperson`, not `salespersonCode`.
- Salesperson codes cannot split Aanya out (see `bbs-weekly-sales-report`, trap 2).
- Many quote headers show $0 where the folder PDF carries the value (SQ-104967, -104982,
  -104992, -104993, -105002). Use the PDF.
- Quotes converted to orders drop out of `salesQuotes`.
- **Status `Accepted` can reveal a win on an older quote.** SQ-105001 (SWRCB, $1,844.84,
  Accepted 9/25) matched the pre-tax value of a 9/4 quote whose outcome was never logged. Match
  by agency and pre-tax value, then ask the rep to confirm.
- Some quotes exist only in BC with no folder files (PVSP SQ-104979, SATF SQ-104978, CHP
  Monterey SQ-104983, CHP Bosch SQ-104958). Count them, tag them medium confidence, and offer
  to save the PDF to the buyer folder.
- SQ numbers printed on Claude-built PDFs are not always BC numbers (CHP_Quote_104585 does not
  match BC SQ-104585, an EMSA $0 draft). Expect mismatches; do not "correct" them silently.

### Quote folders (`All RFQ's by Agency/<Agency>/<Institution>/<Buyer>/<Item M.D.YYYY>/`)
- Select files by birth time or modified time inside the week. Folder names carry the request
  date; file names sometimes carry the due date ("RFQ Due 9-23.pdf").
- **Recognise a BBS quote:** `Q 16xxx.pdf` from `b2b.blackboxsafety.com` (Kim's and Aanya's
  portal quotes); `SQ-######` PDFs; `<Agency>_Quote_*.pdf`; priced Line Item Cost Worksheets
  and bid sheets; `inputs.json` behind an OBS form fill.
- **Do not count inbound vendor quotes:** Grainger special-order quotes (`2065xxxxxx`,
  "Redbook Qte"), `S-QUO…`, `QUO…`, `Quotation_QO…`, WAXIE, LN Curtis. The CHP EMT folder held
  only a Grainger quote to us, and the first draft of the hand run counted it by mistake.
- The b2b portal PDFs use obfuscated fonts, so text extraction returns garbage. Render the
  page to an image (PyMuPDF) and read the totals and the contract-number line from it.
- One row per request. Revisions count once (SQ-104966 → SQ-104980; V2; rev1). Identical
  quotes under two numbers count once (16179 = 16187, both $10,078.27).
- `quote-log.md` was filled for 2 of 34 quotes that week and missing from 17 of the buyer
  folders involved. The review drafts the missing rows; it does not assume the log is
  complete.
- Watch for copies filed under the wrong institution (Coalinga quotes sitting in an Atascadero
  folder).

### Email (the rep's own Sent Items)
- Search Sent Items by date window, 25 per page, and read every page (the hand run had 121).
- Bodies are large HTML and often spill to a file. Strip tags and read the text; do not
  pull whole threads into context.
- `.ca.gov` recipients are customer touches. Forwards to a rep ("please save to folder") are
  handoffs. Replies such as "received and working on this" mark a new request.
- **Open quote attachments and read their document date.** CHP_Quote_104585 and 104586 were
  attached on 9/21 but dated 8/7: August quotes re-sent for confirmation, $170K that must not
  be counted as new.
- Email is where untracked work shows up: the CHP Avon kits, PDC phone booths, and SATF N95
  budgetary pricing were in nobody's CRM or folder.

### Counting and value rules
- Count a quote when a BBS quote was built inside the week, one row per request.
- Value is the **pre-tax subtotal**. Priority: quote PDF > BC quote total > bid-form inputs >
  CRM estimate. Tag each row High / Medium / Low accordingly and show the split on the summary.
- Attribute to the person who did the work; if the CRM owner differs, note it.
- Scope comes from `ca-state-sales-grounding` (CA state; not body armor, CSU/UC, local,
  federal or primes).
- Anything unknown is `[FLAG: why]`, never a plausible value.

## 7. Borrowed from the sales craft skills

Invoke these by name while building. Take only what is listed; each was checked against state
procurement and several carry commercial habits that would get a rep ignored or in trouble.

| Borrow | From | How it lands in this skill |
|---|---|---|
| "Visibility is respected, not assumed" — sections the runner cannot see are named, never guessed. Three or four questions tied to specific deals, plus wins to acknowledge and where the rep likely needs help | `sales:rep-context` | The confirm/correct prompts, the email-coverage line, the coaching questions in section 5 |
| Section order: Closed (won / lost) → Moved → New → Activity → Monday lookahead. Never show a zero when the source was unavailable. Keep a week-over-week archive; never assume won | `sales:weekly-wrap` | Order of the rep review; the dated `Weekly Summaries/` subfolders are the archive |
| A quiet week is the success case. Report what crossed a threshold, in "act today" and "this week" blocks. Open the full thread before calling something "waiting" | `sales:deal-signals` | Outstanding-work section. Thresholds for this book: request with no reply from BBS in 1 business day; next step unchanged 14+ days |
| Flags: stale 14+ days, slipping (past due or moved twice), blank next step, single-threaded, quote past its valid-until date | `sales:pipeline-review`, Quinn | Quote-out flags. Skip its "3x coverage" and quota framing: award-based RFQ flow needs BBS's own hit rate, which does not exist yet |
| Every open item has a next step, and "I'll follow up" is not one. Track deal source (inbound / outbound / referral). "Smaller, accurate pipeline > large, inaccurate pipeline" | `sales-pipeline-management` | Reactive vs proactive tagging (4c); no-blank-next-action check |
| Whitespace only with at least one piece of evidence; one best play per account; a parking lot for ideas with no evidence yet. Grid = product family × facility × contract vehicle | `sales:expansion-whitespace` | How `references/growth-plays.md` generates plays |
| Start 90 days out: "the renewal you start 90 days out is a process; the one you notice two weeks out is a discount". Aim it at reorder windows, recurring programs, LPA end dates and fiscal Q4 | `sales:renewal-radar` | The "why now" for reorder-timing plays, with dates from `ca-budget-timing` |
| New vs existing buyer; net new contacts added; new vs expansion revenue. "Where else does this problem exist?" "Who else deals with this?" | `sales-deal-upselling`, `sales-analytics-tracking` | New-buyer headline (4a); the second-name question on every quote |
| "Track for decisions, not data." "Reps won't track what's painful." Hygiene targets: next step on >90% of open items; loss reason recorded 100% of the time | `sales-analytics-tracking` | Keep the rep's logging small; draft rows for them. Outcome is not optional (desk `CLAUDE.md`) |
| State-bid loss reasons: price, non-responsive packet, cancelled / no award, lost to another SB/DVBE firm, no-bid. "Price was too high" often masks something else. "Should we have been in this deal?" | `sales-deal-review-win-loss` | Outcome capture in 4d |
| Meeting norms: rep presents, manager coaches; actions, not interrogation; end with specific commitments; blame vs learn | `sales-deal-review-win-loss` | Section 5 runs this way |
| "Schedule proactive work first." A protected prospecting block. Friday review, Monday plan, 1-3-5 prioritisation | `sales-time-management` | The capacity check and the time block on each play. The reps' guides already set three calling mornings and a 2-hour cold block |
| Leading indicators in weeks 1–4, pipeline in weeks 4–12, revenue from week 12; scorecard at weeks 4 / 8 / 12. "Focus beats volume." Replicate a win at the next facility in the same department | `sales-territory-account-launch` | Ramp honesty in every review; the "same department, next facility" play |
| Disqualification matters as much as qualification; "better to lose early than lose late". Rebuild qualification as bid / no-bid: sourceable, vehicle fit, DVBE lever, incumbent, due date feasible | `sales-qualifying-leads` | A one-line bid / no-bid note on any open request that looks unwinnable, so the rep can decline on purpose (it is one of Aanya's learning measures) |
| Diagnose before prescribing; 70/30 listening; "walk me through how decisions like this get made"; "have you bought something similar before?" | `sales-discovery` | Opening questions on proactive plays to units with no open solicitation |
| Accountability is specific ("six quotes out by Friday, response inside 24 hours, reviewed Monday"). "Kim and Aanya should never be surprised by their own numbers" | Callie | Commitments at the end of the meeting |

**Do not import:**

- Manufactured urgency, breakup emails ("should I close your file?"), the "negative reverse",
  invented deadlines.
- Discounting of any kind: volume, term, bundle, "lock in pricing", "creative financing",
  "other budget pools". NASPO sells at cost, and unrequested scope can make a bid
  non-responsive.
- Negotiation or closing stages, Commit / Best Case forecasts, stage-probability weighting, 3x
  coverage and dial quotas as targets.
- Chasing a buyer during an open formal solicitation. Contact is often restricted to the
  formal Q&A, so check the solicitation before any follow-up touch is suggested.
- Calling the procurement officer a "gatekeeper", or going around them. They control the PO and
  the process.
- Executive dinners, gifts or swag. State ethics limits apply.
- "Remove after five touches with no response." State buyers go silent until award; silence
  moves an account to long-term nurture, it does not end it.
- "Don't check email first thing." RFQ due dates will not wait.
- Unsourced benchmarks (the 80% / 44% follow-up statistics, "60% selling time").
- Posting an individual rep's numbers to a team channel. Reading a rep's chat without her
  opting in.
- Any write to the CRM or BC, including creating opportunity records.

## 8. Files to create and change

Create:

- `plugins/bbs-sales/skills/ca-weekly-rep-review/SKILL.md` — under ~250 lines; push detail
  into references.
- `references/four-source-reconciliation.md` — section 6.
- `references/rep-review-template.md` — the rep-facing review, written to the rep in the second
  person, wins first, confirm/correct prompts, drafts section at the end.
- `references/monday-meeting-template.md` — section 5.
- `references/growth-plays.md` — how to generate and rank the three to five plays, with the
  sources in trust order and the definition of done for each.
- `scripts/build_weekly_workbook.py` — the team workbook (Summary, Quotes, Open Requests, Data
  Flags, Method) from a JSON of reconciled rows. Model it on the 2026-09-21 workbook: formulas
  for every total, Arial, pre-tax values, a confidence column, a tie-out check between the agency
  table and the scorecard.
- `plugins/bbs-sales/commands/ca-monday-plan.md` — runs the review for one rep or the team and
  builds the meeting pack.

Outputs land in `Customers/State of CA Agencies/Weekly Summaries/<Monday YYYY-MM-DD>/`:
`<rep>-week-in-review.md` per rep, `monday-meeting.md`, and the team workbook. Ask Parker
before moving the existing 2026-09-21 workbook into a dated subfolder.

Change:

- `plugin.json` and `.claude-plugin/marketplace.json`: version 0.5.0 → 0.6.0, add the skill to
  the description, keywords `weekly-review`, `coaching`, `monday-meeting`, `one-on-one`.
- `plugins/bbs-sales/README.md`: add the skill and the command. The skill-count badge already
  says 5 while the plugin ships far more; fix it.
- `bbs-weekly-sales-report/SKILL.md`: point its trap 1 at
  `ca-weekly-rep-review/references/four-source-reconciliation.md`. The hand run showed the CRM
  also misses and misdates work, so "the CRM is the pipeline" needs "and reconcile it".

Flag, do not fix without Parker's OK (outside this repo):

- `~/.claude/agents/quinn.md` line 22 states the scope filter as `AREA = CA-STATE` minus the
  body-armor codes only. It is missing `minus CUSTOMER in (CSU, UC)`, the clause that stopped
  Joey Magliato's $2.67M of FY25-26 university revenue landing in Aanya's number. The weekly
  review leans on Quinn for monthly numbers, so this needs fixing first.

## 9. Triggers and collisions

The two weekly skills answer different questions:

| Skill | Question | Reader |
|---|---|---|
| `bbs-weekly-sales-report` | What does Parker put on the Microsoft Form? | Parker |
| `ca-weekly-rep-review` | What did I do last week, and what do I do this week? | The rep, then the Monday meeting |

Write the new description around **the rep's own week plus the plan for the next**: "review my
week", "what did I do last week", "prep my Monday", "Monday meeting with Kim and Aanya", "plan
my week", "weekly one-on-one", "what should I work on this week", "what's outstanding for me".
Narrow `bbs-weekly-sales-report` to the form and the manager recap. Then add a section to
`docs/TRIGGER-CHECK.md`: five should-fire phrasings for each weekly skill, the nearest
competitors (`ca-territory-handoff` for "who should I call", Callie and Quinn for scorecards),
and how each ambiguous case resolves.

## 10. Test against the known week

Use the skill-creator eval loop. The week of 21 September 2026 is the fixture. The reconciled
rows, the open-request list, the data flags and the exclusions are all in
`docs/fixtures/week-2026-09-21/build_weekly_example.py`, which is the script that produced the
worked-example workbook. Use it as the starting point for `scripts/build_weekly_workbook.py`:
lift the styling and formulas, move the hard-coded rows into a JSON input. The skill must reach
these answers:

| Check | Expected |
|---|---|
| State quotes, team | 34, $327,748.90 pre-tax |
| Kim | 25 quotes, $163,024.71 |
| Aanya | 9 quotes, $164,724.19 |
| Parker, state | 0 completed. His CHP re-sends and the unsent Redding quote are open work |
| CHP_Quote_104585 / 104586 | Not counted: August quotes re-sent |
| CHP EMT folder | Not counted: Grainger quote to BBS, listed as open work |
| DSH Coalinga 16179 / 16187 | Counted once |
| DSH Metro beds SQ-104998 | Counted, and flagged as not marked submitted in the CRM |
| CalVet VHC Fresno | Flagged past due (RFQ due 9/23, CRM RFQ-005173 open) |
| SQ-105001 | Surfaced as a likely win on TaMara Skondras's 9/4 quote |
| CHP Avon kits, PDC phone booths | Surfaced as requests with no CRM record, with a drafted record offered |

Also run one **rep-mode** test as Aanya would see it and read it as she would: does it open with
her wins, does it avoid comparing her to Kim, does every "you didn't" come with "want me to draft
it?", and could she walk into Monday knowing her three plays?

## 11. Guardrails that carry over

- Everything in the desk `CLAUDE.md`: never invent a price, contact, date or cert fact; Claude
  drafts and a human sends; cert language follows the channel (OSDS SB/DVBE 2009473 for state).
- Read-only against BC, Dataverse, QuickBooks and Supabase.
- SCPRS figures always carry their slice label.
- Never state that a competitor lacks a certification.
- No manufactured urgency. Urgency at a state agency is the fiscal calendar, encumbrance and
  reorder timing, and it comes from `ca-budget-timing`.
- Stop at the review and the meeting pack. Outreach copy is Sloane's, territory banding is
  `ca-territory-handoff`'s, pricing is `naspo-quote`'s. Hand off by name.

## 12. Done means

- The skill reproduces the section 10 table on the fixture week.
- A rep-mode run reads as help to the person it describes.
- The trigger check is updated and shows no collision with `bbs-weekly-sales-report`.
- Version bumped, README updated, nothing committed until Parker has read the diff.
