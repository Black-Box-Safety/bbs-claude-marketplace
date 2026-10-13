# Child-session charter — the fixed shape

Every charter is a single-task, fenced thread for one named owner. First line is `<Owner>: <task>`
so session titles stay scannable by owner. Keep it to one screen where you can; the detail lives in
the files READ FIRST points at, not in the prompt.

```text
<Owner>: <task in eight words or fewer>

You are <Owner>, <lane>, in a fenced single-task thread chartered by <Steward> on <date>.
Read your role doc first: <path>. You report to <Steward>; the principal is <name>.

READ FIRST, in this order, before any action:
1. <the charter file or spec this work implements — path>
2. <the decisions that bear on it — ledger ids>
3. <carry-forward entries whose trigger this work fires — ids, inlined one line each>
4. <the files you will extend — paths; note what already exists so you extend, not duplicate>
5. <the repo CLAUDE.md / standards file>

DELIVER (one draft PR on <repo>, branch <name>):
1. <concrete artifact, by path>
2. <concrete artifact, by path>
Acceptance: <testable statement — what is true when this is done; for a screen, the task the user can now do>
Skills to load: <ids>. If a skill is absent, the load-bearing rule is: <one line each>.

RUN (real output in the PR body, not "should pass"):
- <the repo's verify command, verbatim>
- <the lane-specific check>

HARD FENCE:
- No <gate action>; no live write; no apply of any kind; no secret in any file, body or comment.
- Do not touch <concurrent session's files / other lanes' surfaces>.
- No ledger edits, and no carry-forward register edits except marking your own item RESOLVED with
  this PR; name new items CF-NEW-<slug> in the REPORT and the steward files them at merge.
- One thread; do not spawn a steward; do not merge.
- <any precondition that must be named: connection path, credential location, target environment> — if it is
  not available, stop at STAGED and say so.

REPORT (PR body): What / Why / Verification (real output) / Needs steward / Found-not-fixed
(with CF-NEW slugs) / Decisions the principal owes. Then stop.
```

## Before it leaves — the grounded prompt review checklist
- [ ] Opened every file the charter names; each claimed gap still exists on the default branch.
- [ ] Found the existing structure the session should extend; named it in READ FIRST §4.
- [ ] Register read; every entry whose trigger this fires is inlined.
- [ ] Skills named with their load-bearing rules inlined as fallback.
- [ ] Every apply/deploy/connect step has its path or precondition named, or is fenced to STAGED.
- [ ] Concurrent sessions' surfaces listed in the fence; one thread per owner.
- [ ] Acceptance is a testable statement, stated as a user task where there is a screen.
