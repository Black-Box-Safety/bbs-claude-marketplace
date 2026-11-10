# The review loop — one bounded pass per PR

Applies to every substantive PR from a session or agent. Led by the steward.

**1. LAND.** The author pushes the draft PR with its verification evidence.

**2. STEWARD REVIEW — immediate.** Review against the charter; re-run the repo's own checks
yourself and never trust the body's numbers. Charter compliance, lane fences, standing constraints,
any declared-gaps block. Fails → straight back to the author; no panel spends tokens on a PR that
has not met its own charter.

**3. IMPACT PANEL — independent seats.** From what the diff actually touches (shared tables and
their owners, tool contracts, cross-repo mirrors, vocabularies, gates, exported surfaces), dispatch
each impacted owner for an independent review — in parallel, blind to each other. Each returns
per-item verdicts: CONFIRM / CONFIRM-WITH-AMENDMENT (exact text) / CHALLENGE (with the
alternative), grounded in file:line.
*Proportionality (your call, logged):* full panel for anything touching a shared surface; one seat
for narrow overlap; steward-only solely for docs-only or no-shared-surface diffs, stated explicitly.

**4. SYNTHESIS.** Dedupe; surface genuine conflicts between seats and rule on them explicitly as
yourself — never launder your own ruling as panel consensus; separate pre-merge changes from
follow-ups; post ONE consolidated review, findings ranked, each attributed to its seat. **Every
follow-up gets a carry-forward entry drafted in the synthesis itself** (title · why it matters
later · owner · severity · trigger · evidence). A follow-up with no drafted entry is a pre-merge
change by default.

**5. ADJUDICATION — with the author, as a conversation.**
- Findings are claims, not orders. The author may accept, adapt or rebut each one; a rebuttal must
  be evidence-grounded (file:line, a test, data), never preference or authorship.
- Anchoring is expected and managed: name it when you see it, restate the finding in the author's
  terms, ask for the evidence that would change both minds. Defensiveness is not guilt.
- A CHALLENGE from the impacted surface's owner stands unless rebutted with evidence. Ties after
  evidence go to the **owner of the affected surface**, not the PR author. Irreconcilable or
  doctrine-touching calls go to the principal with both positions stated fairly.
- State your own disagreement plainly; work the best way forward, which may be a third shape.
- Every finding gets a recorded disposition on the PR: `accepted` / `adapted (how)` /
  `rebutted (evidence)` / `deferred (owner + where recorded)`. A finding that vanishes without a
  disposition is a process defect.

**6. RE-VERIFY + MERGE.** The author pushes the agreed changes; you re-run the checks, check each
disposition landed as recorded (including cross-repo mirrors), and merge on the principal's word
or recorded standing delegation. In the same pass, append the recorded follow-ups to the register
through one ledger PR in the home repo (the end-of-session ledger PR is fine) and route them to
owners. The merge is not complete until that ledger PR is open.

## Termination — the loop is bounded
1. **One fix round per PR.** Step 6 is you re-running checks and checking dispositions; it is not a
   second dispatch of the seats.
2. **A second adversarial round has exactly one trigger and is the last one:** a BLOCKING finding
   whose fix **changed the mechanism** rather than patching the instance, so the new mechanism has
   never been reviewed. Send it to the reviewing seat once, and say in the dispatch that this is the
   final round.
3. **Everything found after that is a register entry, not a round** — including findings on the new
   mechanism. The PR merges. The one exception: the specific blocker is still open (the fix does not
   work), which returns to the author as a **defect**, not as a new review. A disposition that did
   not land is likewise a defect return, not a round.
4. **Accepted gaps close the topic.** Once an owner declares a gap, argues it, and pins it with a
   named test, it is a decision; re-litigating it needs new evidence, not a fresh reviewer's opinion.
5. **State the endpoint when you open the loop.** Every panel dispatch names what will end it
   ("panel → one fix → merge") so the author and the principal know the shape before tokens are spent.
The failure this prevents is not bad findings; it is cost and calendar unbounded while quality gains
shrink. The register is where a true-but-not-blocking finding goes instead of another round.
