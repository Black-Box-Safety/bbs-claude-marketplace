# Plan — move `bbs-fill` into `bbs-sales`, gate it with a hook, retire `bbs-tools`

Spec: `docs/superpowers/specs/2026-11-11-bbs-fill-into-bbs-sales.md`. RULED 2026-11-11
(Parker, in session: "Yes … to the tools fix as a separate slice").

**Do not start until #68 and #84 are both merged to `main`** (spec §7). Branch:
`fix/bbs-fill-into-bbs-sales`, restarted from that `main` (merge, never rebase, if it moves
again). One draft PR. Nothing merges, leaves draft or is re-pasted without Parker.

Each task ends with its own check. Run `python3 scripts/check_marketplace.py` after every
task that touches a skill, README or manifest.

---

### Task 1 — Move the launcher (no behaviour change yet)

1. `git mv plugins/bbs-tools/bin/bbs-fill plugins/bbs-sales/scripts/bbs-fill`; confirm
   `git ls-files -s` shows `100755`.
2. `git mv plugins/bbs-tools/tests/test_bbs_fill.py plugins/bbs-sales/scripts/tests/test_bbs_fill.py`
   (create the folder if #77 has not).
3. Check: `ALLOWED` on the branch equals `ALLOWED` on `main` byte for byte: #68's and #84's
   entries included, and **`bbs-quote-builder/scripts/build_quote.js` absent** (#68 retires
   that skill, Parker 2026-11-11). Do not re-add it. Drop it from any test fixture too.

### Task 2 — Re-anchor the launcher on its own plugin root (spec §2)

1. Replace the `market=…/../../..` computation with `root=$(cd "$(dirname "$self")/.." && pwd -P)`;
   require `script` = `$root/skills/<one of ALLOWED>` after `real()`; refuse if `$root` is a
   link.
2. Keep `cache=` as `$root/../../..` for the argument check; keep every other block as is.
3. Rewrite the header's STABLE INTERFACE paragraph (spec §2); keep the path-pattern
   paragraph and add the hook sentence.
4. Check: port the test fixture to `<tmp>/cache/<market>/bbs-sales/<ver>/{scripts,skills}`;
   all ported tests pass; add and pass: other-version script refused; mode `100755`.

### Task 3 — The hook, Python half (spec §3.2–3.6)

1. `plugins/bbs-sales/hooks/fill-gate.py`, stdlib only: read stdin JSON → checks 1–6 → print
   the allow JSON or nothing; exit 0 always; any exception → nothing.
2. Lexer as a small state machine, written from the spec's grammar, not from `shlex`.
3. `ALLOWED` parsed from `$CLAUDE_PLUGIN_ROOT/scripts/bbs-fill` with the same rule as the
   test.
4. Check: `python3 -m py_compile`; the case file (Task 5) passes on the Python half.

### Task 4 — The hook, PowerShell half

1. `plugins/bbs-sales/hooks/fill-gate.ps1`: same checks, same reason string, ASCII only,
   runs on Windows PowerShell 5.1 and pwsh 7 (no `ResolveLinkTarget`, no `?.`, no ternary).
2. Reparse-point test via `(Get-Item -Force $p).Attributes -band [IO.FileAttributes]::ReparsePoint`.
3. Check: `run-tests.ps1` cases pass under pwsh 7.

### Task 5 — Hook tests and parity (spec §8)

1. `hooks/tests/fill_gate_cases.json`: every row of both spec tables, plus anything found
   while building. Paths are placeholders the runner fills from a temp fake root.
2. `hooks/tests/fill_gate_parity.py`: runs each case through both halves; compares decision
   and reason; `BBS_REQUIRE_PS=1` makes a missing PowerShell a FAIL; prints the allow table
   at the end.
3. Same file: the bash differential check and the fixed-seed fuzz.
4. `run-tests.ps1`: load the same JSON and assert the PowerShell half alone.
5. Mutation check, recorded in the PR: disable the `;` rejection, then the word-0 check,
   then the symlink walk — each must turn at least one case red.

### Task 6 — Wire the hook

1. Add the `PreToolUse` / `Bash` entry to `plugins/bbs-sales/hooks/hooks.json` with the
   `sh` pre-filter and the house interpreter chain (pwsh → powershell → python3 → silent
   `exit 0`), `timeout` 10, no `statusMessage` (it would show on every matching call).
2. Extend `parity.py`'s `check_entry()` pattern (from #84) to run this entry through `sh`
   with stub interpreters: nothing starts for a command without `bbs-fill`; stdin arrives
   intact.
3. Update the `hooks.json` `description` by one sentence.

### Task 7 — Repoint every skill line

1. Replace every `bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/` with
   `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/` in
   `plugins/bbs-sales/**/*.md`, including #68's `bc-quote-entry` and #84's `desk-remember`.
2. Rewrite each "if `bbs-fill` is not found, `bbs-tools` is missing" paragraph (spec §4).
3. `ca-form-filler/references/packets/README.md`: new `ALLOWED` path.
4. Check: the new launcher test "no bare `bbs-fill \"`" passes; the skill-line test finds
   every line and every one is on `ALLOWED`. No `description:` changes, so the routing eval
   is not re-run; say so in the PR.

### Task 8 — Retire `bbs-tools` in the repo (spec §4 table)

1. `marketplace.json`: remove the entry; add `"renames": {"bbs-tools": null}`; run
   `claude plugin validate .` if the CLI is available, else say it was not run.
2. `git rm -r plugins/bbs-tools`.
3. Managed settings JSON and `MANAGED-SETTINGS.md` (new section "Form scripts: a hook, not
   a rule (2026-11-11)"); `bbs-checkup.md` checks 1 and 12; `bbs-sales/README.md`;
   `README.md`; `PLUGINS.md`; `SYSTEM-OVERVIEW.md`; `REP-SETUP.md`; `REGISTRY.md` row.
4. CI: launcher step → `plugins/bbs-sales/scripts/tests/test_bbs_fill.py`; new step
   `fill_gate_parity.py` with `BBS_REQUIRE_PS=1`.
5. Check: `grep -rn "bbs-tools" --exclude-dir=.git .` returns only `marketplace.json`'s
   `renames`, `REGISTRY.md`, `docs/STEWARD.md`, dated specs/plans/assessments, and
   `MANAGED-SETTINGS.md` history sentences. `grep -rn "Bash(bbs-fill"` returns only
   history sentences.

### Task 9 — Record the ruling

`docs/STEWARD.md` register: "**bbs-fill into bbs-sales — RULED 2026-11-11.** Parker, in
session: \"Yes … to the tools fix as a separate slice\"." plus one line of what it approved
and a pointer to the spec. Nothing restated.

### Task 10 — Checker FAIL: not in this slice

Do not edit `scripts/check_marketplace.py`. The FAIL on a top-level `bin/` in any
`plugins/*` (spec §4) is a review-side follow-up (steward, 2026-11-11); leave it out of the
PR body's asks.

### Task 11 — Versions, gates, PR

1. Versions (steward, 2026-11-11): `bbs-sales` **0.16.0** (#77 merged at 0.13.0; #68 holds 0.14.0, #84 holds 0.15.0), `bbs-foundations` **0.5.1**;
   ask the steward for marketplace `metadata.version` if it moves.
2. Full local gate: `check_marketplace.py` exit 0; launcher tests; hook parity with pwsh
   present; `check_claude_md.py "$PWD"` exit 0.
3. Draft PR. **V1 is a merge gate** (steward, 2026-11-11). Body: what a rep will notice ("form scripts run without an Allow click, as
   before; nothing to install"), the ruling, the deploy order (spec §5) as a checklist for
   Parker, merge gates V1–V3 (spec §6) as unchecked boxes **Parker runs before merging**:
   - load the branch's `bbs-sales` with `claude --plugin-dir <checkout>/plugins/bbs-sales`
     (disable the installed `bbs-sales` for that session), auto mode on;
   - V1, V2, V3 as written in the spec.
4. Stop. Rex reviews; findings come back to this worker.

### After merge (Parker, outside the repo) — spec §5

- [ ] Reps restart; one rep runs `/bbs-checkup`, check 12 passes.
- [ ] Then re-paste `bbs-managed-settings.json` (ADMIN-RUNBOOK §1).
- [ ] Re-run organization sync; confirm no `bin/` error.
- [ ] Never re-paste before the new `bbs-sales` is on rep machines.

---

Owner: Parker Marshall. Written 2026-11-11.
