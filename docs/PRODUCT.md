# The BBS Claude toolkit — product plan

**A living document.** It says what we are building for the people who work here, what is
true today, what we are folding in next, and how the toolkit grows. Update it in the same
PR as the change it describes. Facts point at their source; nothing is re-keyed here.

Owner: Parker Marshall. Last verified 2026-09-18.

---

## 1. What this is, in one paragraph

Black Box Safety is nine people selling safety and tactical equipment to public agencies.
Most of the day is not selling. It is the labor between "an RFQ arrived" and "a compliant
quote went out," and the labor after the win: chasing a PO, reconciling an order, answering
"what do they owe us." The toolkit moves that labor to Claude and leaves people with the
two decisions that need judgment: what to promise a buyer, and what to send. It is not a
control system. It is a set of tools a person reaches for because the job goes faster with
them than without.

**The test of every change:** a teammate says "that saved me an hour," not "now I have to
do this extra step."

---

## 2. Design principles

These decide what gets built and how. When a proposal violates one, the proposal changes.

1. **Remove a step; never add one.** If a skill needs the rep to learn a command, fill a
   form, or remember a rule, the skill is not finished. The rep says what arrived. Claude
   does the rest and shows its work.
2. **One question, at most.** A tool that interrogates the user gets abandoned. Ask the
   single thing that changes the outcome, then proceed.
3. **Two rails, and everything else is yours.** Humans send. Numbers come from a real
   source or get flagged. Above those two rails, experiment freely. The rails are
   protection for the person, not restriction of them. Full policy:
   `plugins/bbs-foundations/docs/AUP.md`.
4. **Truth lives in one place.** Prices from Grainger or Business Central. Company facts
   from `bbs-foundations` canonical facts. Form values from the vendor profile. A fact
   copied into a second file goes stale in one of them, on a binding document.
5. **Show where every number came from.** A quote a rep cannot trace is a quote they will
   not trust, and they will go back to doing it by hand.
6. **Organize by the job in front of you, not by title.** The same person quotes an agency
   at noon and builds a one-pager at night. Everyone gets the whole toolkit.
7. **Nothing installs by hand.** Content updates through the marketplace. Policy updates
   through managed settings. A rep never copies a file between machines.

---

## 3. The product, in three layers

| Layer | What it is | Where it lives | State |
|---|---|---|---|
| **Rails** | Send-class tools denied, company memory injected, plugins enabled for everyone | Managed settings, pushed from the Claude console. Template: `plugins/bbs-foundations/docs/bbs-managed-settings.json` | Live. Two gaps: `bbs-back-office` is not in the enabled list, and the saved preference about signature lines still contradicts current doctrine. Both are console-side fixes. |
| **Job plugins** | The work itself: quote desk, post-award, storefront, company doctrine | `plugins/bbs-sales`, `bbs-back-office`, `bbs-website`, `bbs-foundations` | Sales spine built across three open PRs (#14, #15, #16). Not yet merged. Not yet run end to end by a rep. |
| **Literacy and self-service** | Understand the tools, start any job, extend the toolkit | `bbs-claude-coach` plugin (PR #25), `/bbs-my-voice`, the AUP | Drafted. Needs rework before merge (section 5). |

Underneath all three: `scripts/check_marketplace.py`, which catches the failures that never
throw at runtime, and a review split where Claude builds and a reviewer that did not write
the change decides. A build session ends at a PR, never a merge. The merge decision belongs
to `.claude/agents/lead-reviewer.md`, which squash-merges what passes and posts critiques
on what does not. Cursor's review stance in `.cursor/rules/` is the second opinion.

---

## 4. The experience we are building toward

Five moments. Each one is a job a teammate has today. For each: what they say, what
happens, what they review. This section is the acceptance test in plain language.

### A state RFQ arrives

**They say:** "Mule Creek just sent this," and drop in the email or PDF.
**What happens:** `/ca-rfq` files it in the right customer folder, checks for a duplicate,
pulls the items out of whatever format arrived, checks BPO eligibility, prices Grainger
lines against the institution's own account and routes the rest to vendor sourcing, builds
the quote on letterhead, fills and signs the compliance packet on the lines BBS owns, and
stops.
**They review:** every number with its source in the cover summary, then send.

### A price check

**They say:** "What does Grainger charge CDCR for these?" and paste part numbers.
**What happens:** the Grainger MCP is queried against that buying account. Never the open
web, never memory, never the retired punch-out.
**They review:** the account it priced against. The wrong account returns a wrong price
that still looks valid.

### A post-award question

**They say:** "What has LION shipped us on that PO?" or "What does Caltrans still owe?"
**What happens:** Business Central is read. The answer names the documents it came from.
**They review:** nothing to send. They act on it.

### Marketing material

**They say:** "One-pager for the Sourcewell armor contract, for a sheriff's office."
**What happens:** the design and document skills build it in the BBS voice, with
certification language matched to the channel.
**They review:** claims and numbers before it leaves.

### "What can I even do here?"

**They say:** exactly that, or `/bbs-what-can-i-do`.
**What happens:** the coach reads the plugins actually installed and answers by job, not
by title, with one first step.
**They review:** nothing. They try it.

If a moment above needs more than one question from Claude, or a step the rep has to
remember, it is not done.

---

## 5. What we are integrating now, and in what order

Synthesis of the September work: three Claude slices that finish the sales spine, and
eight Cursor PRs that harden setup, review, and literacy. Merged together in a scratch
worktree on 2026-09-18: the slices merge clean; the coach plugin fails two of the checkers
the slices add. Order matters.

### Step 0. Account-side, today, 30 minutes. Only Parker can do these.

Aanya's install audit of 2026-09-16 found that `bbs-sales` failed to load on a clean
install (a redundant `hooks` key in its manifest) and `document-skills` would not clone (a
commit SHA in a field that takes a branch). Both reproduced on Claude Code 2.1.277 and
both are fixed in the PR that carries this document. The items below are what the same
audit left for the console and the org.

- Delete the five orphaned personal skills in claude.ai settings. They still load first in
  Parker's sessions and one of them drives the retired pricing path. `HANDOFF.md` has the
  mechanism and the list.
- Add `bbs-back-office` to the enabled plugins and re-paste managed settings. Reps under
  managed policy have no post-award plugin today.
- Edit the saved preference that still re-injects the old signature rule.
- Retire the local `bbs-grainger` stdio server on rep machines. Two Grainger servers with
  different tool sets means the account-resolution step can silently fail and a rep prices
  against the wrong account.

### Step 1. Land the spine.

| Order | PR | What it gives a rep | Condition |
|---|---|---|---|
| 1 | #16 dependency declaration | Before installing, knows whether a job will run on their machine | Cursor reviews it. It changes the review-side checker, so the build side cannot be its reviewer. |
| 2 | #14 `/ca-rfq` | One trigger for the whole state RFQ, no procedure to remember | Touches managed settings, so a second reviewer. |
| 3 | #15 packet profiles | New customer packets become profiles, not new skills to pick between | DSH profiles stay stubs until Aanya's material arrives. |
| 4 | #21 CI gate, blocking | Nothing that fails the checker reaches a machine | Take the blocking posture. Add the CLAUDE.md checker as a second step. Drop #16's report-only workflow. |
| 5 | #19, #22, #17, #26 | Review stance for Cursor, guided commons intake, cloud env, Windows portability | Rebase #26 after #15. |

### Step 2. Make setup true.

PR #23 found that a rep who ran the bootstrap had no Python, no PDF libraries, no `docx`,
and no LibreOffice. The first packet would have failed mid-bid with a green checkup. Run
the revised script once on a fresh Windows machine, then merge. Never ship an unrun
installer to people who cannot debug it.

### Step 3. Ship literacy, reworked.

PR #25 (coach) and PR #24 (TOOLKIT.md) are the right thesis. Fold #24 into #25 and fix four
things before merge:

- Replace every reference to the two retired commands with `/ca-rfq`.
- Add `requires: []` to the coach skill. #16 makes the key mandatory.
- Remove the re-keyed certification number from the rails reference. Point at canonical
  facts instead.
- Give the job map one home. A rep's install carries no `docs/` folder, so the plugin is
  the home and the repo-root TOOLKIT.md becomes a pointer.

Then re-paste managed settings with the coach enabled and announce three commands in
Teams. Close #20 (developer guidance for a non-technical fleet) and #24 (folded).

### Step 4. Prove it.

One rep who is not Parker runs one real RFQ through `/ca-rfq`, unaided, on their own
machine. Result recorded in `docs/acceptance/`. Until this row exists, nothing in Step 1
counts as shipped.

---

## 6. Adoption: how people come to want it

Tools for non-technical teams fail on the first bad experience, not on missing features.
The adoption plan is a sequence of small guaranteed wins.

**Launch one job at a time.** Not "here is the toolkit." Instead: "This week, try asking
Claude what a vendor still owes us." One moment from section 4, demonstrated live in
fifteen minutes, then everyone tries it on a real case that day. Next week, the next
moment. Order: post-award questions first (read-only, zero risk, immediate answer), then
price checks, then the full RFQ.

**A champion who is not the admin.** Aanya already built twelve personal skills. She runs
the acceptance test and gives the first show-and-tell. Peer proof beats admin instruction.

**Celebrate the catch.** A `FLAGS.md` entry is the system working. Read the best catch of
the month aloud. A team that is afraid to log errors stops using the tool that surfaces
them.

**"What shipped" monthly.** One Teams post: three things the toolkit does now that it did
not last month, each traced to a rep's request. People push a tool they can see
responding to them.

**Never a dead end.** Every failure message names the fix or the person. `/bbs-checkup`
prints the exact sentence to send Parker. A skill missing a library says what to install.
A skill missing a connector says it is an admin assignment, not the rep's problem.

**Measure adoption as the leading indicator.** `docs/MEASUREMENT.md` owns the numbers. If a
rep goes quiet for two weeks, ask what broke. Do not wait for the monthly review.

---

## 7. How it grows: the loop

```
rep hits a gap → one line in FLAGS.md or Teams
  → weekly triage into a slice (docs/STEWARD.md)
  → build session opens a PR
  → Cursor reviews with .cursor/rules; CI blocks on the checker
  → merge; every machine updates itself
  → /bbs-what-can-i-do reflects it without anyone editing a guide
```

**Requests are the product backlog.** A request is one line: what you wanted, what
happened. That is enough. Turning it into a spec is the steward's job, not the rep's.

**The personal sandbox.** A teammate may build a **new** skill of their own with
`skill-creator`, in their own skills folder, for their own workflow. That is encouraged.
Two things stay out of the sandbox: a personal **copy** of a shared BBS skill (it goes stale
and silently disagrees with the company copy), and anything that invents a price or sends.
When a personal skill helps someone else, it is proposed and lands in the marketplace by PR.

**Voice is personal by design.** `/bbs-my-voice` builds a skill from a rep's own sent mail.
It stays on their machine and is never committed. This is the one intentional exception to
"content lives in the marketplace."

---

## 8. Roadmap

Ordered by leverage for a small team. Each becomes a slice in `docs/STEWARD.md` when it
starts.

| Horizon | Item | Why it matters |
|---|---|---|
| **Now** | Steps 0 through 4 above | Nothing else compounds until the spine is proven on a rep's machine |
| **Now** | FY26/27 BPO list in `dgs-bpo-item-check` | Reps checking eligibility today are checking last year's list. Waiting on Aanya's file. Never synthesize it. |
| **Next** | Aanya's bundle: fold the shared substance, keep the personal parts personal | Seven skills she wants callable; one has a scheduled task on it |
| **Next** | DSH packet profiles, from real packets | Second and third profile prove the profile design |
| **Next** | Prospecting skill: SCPRS play to target list to outreach draft in the rep's voice to a Dynamics note | Every plugin today is inbound. This is the first outbound motion, and the growth half of `MEASUREMENT.md` has nothing feeding it yet |
| **Later** | Won/Lost capture when `/ca-rfq` delivers | Closes the CRM outcome gap. Needs a ruling on whether Claude may write to Dynamics |
| **Now** | `AGENTS.md` at the desk root, stamped beside `CLAUDE.md` | Cursor is allowed in the desk (ruled 2026-09-18) and its Agent reads AGENTS.md, not CLAUDE.md. Today it sees none of the desk landmines |
| **Later** | Body armor quote lane (Sourcewell, CA armor contract) | Second desk, same pattern as the state RFQ |

---

## 9. Rulings

Rulings on binding documents. Only the owner decides; the toolkit flags and waits. A
ruling is recorded here with its date and applied where the repo carries it.

### Ruled

| Date | Ruling | Applied |
|---|---|---|
| 2026-09-18 | **CDCR Packet B Small Business checkbox stays off.** BBS no longer claims SB. | `fill_obs_packet.py` already writes off. **Scope confirmation needed** before the sweep: 30+ files, the managed company memory, the README badge, the AUP and canonical facts all say "SB/DVBE 2009473" and claim the 5% SB preference, and canonical facts records Parker's 2026-09-02 ruling the other way. The sweep is its own slice once Parker confirms: "OSDS 2009473 is DVBE only; BBS claims no SB preference on any California solicitation." |
| 2026-09-18 | **DGS PD 843 "Name of DVBE" is the legal name**, `Black Box Safety, Inc.` | `fill_obs_packet.py` and `field-maps.md` |
| 2026-09-18 | **CalRecycle 74 is certified by the rep who quoted the job.** Griffin's historical share is history, not the rule. | `naspo-quote/SKILL.md` §5; `ca-form-rules.md` already said so |
| 2026-09-18 | **Grainger at cost** is the standing pricing rule. | Already in the managed company memory and `grainger-pricing` |
| 2026-09-18 | **Cursor may open the quote desk.** Reps who prefer Cursor use it with the Claude Code extension. | REP-SETUP. Cursor's own Agent still does not read the desk `CLAUDE.md`, so the desk `AGENTS.md` item in the roadmap moves up to Now. |

### Open

- **Routing, in plain terms.** A rep pastes an agency email asking for a quote. Should
  Claude **file it first** (create the customer folder and run record, check precedent,
  then price) or **price it first** and file afterward? This is about which skill fires
  first, not about which person handles it. Recommended: file first, always. It is how
  duplicate buyer folders and lost precedent are prevented. If confirmed, `/ca-rfq` Gate 0
  loses its one question.
- Whether Claude may write to Dynamics 365 (Won/Lost capture).

---

## 10. Change log

| Date | Change |
|---|---|
| 2026-09-18 | Ruled: Cursor may open the quote desk. Desk `AGENTS.md` moved to Now. |
| 2026-09-18 | Added the `lead-reviewer` agent: independent review, squash-merge or posted critiques, never its own PR. |
| 2026-09-18 | Four rulings recorded and applied (SB checkbox, PD 843 name, CalRecycle signer, Grainger at cost); routing question restated in plain terms. Step 0 trimmed: Aanya has write access, the Grainger key is Parker's to handle outside the plan. |
| 2026-09-18 | Folded in Aanya's install audit: the two manifest blockers (fixed in the same PR), four contributor and console actions added to Step 0, the Cursor ruling and desk AGENTS.md added. |
| 2026-09-18 | Created. Synthesizes the 2026-09-15 reorganization, the three steward slices (#14, #15, #16), and the eight Cursor PRs (#17, #19 to #26). Merge order from a scratch-worktree merge of all eleven. |
