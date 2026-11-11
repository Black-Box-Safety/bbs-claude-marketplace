# Plan: move `bbs-fill` into `bbs-sales`, gate it with a hook, retire `bbs-tools`

Spec: `docs/superpowers/specs/2026-11-11-bbs-fill-into-bbs-sales.md`. RULED 2026-11-11
(Parker, in session: "Yes … to the tools fix as a separate slice"). Revised after Rex's
review of 8eff944: the work is **two PRs**.

- **PR A** (tasks 1–11): launcher in `bbs-sales`, the `fill-gate` hook, skills repointed.
  `bbs-tools` and `Bash(bbs-fill *)` stay. **Do not start until #68 and #84 are both merged
  to `main`** (spec §7).
- **PR B** (task 12): retire `bbs-tools`. **Do not open until check 12 passes on a rep
  machine running PR A's `bbs-sales`** (spec §5, step 5).

Each PR is one draft PR from a branch cut from `main` at that time (merge `main` in, never
rebase, if it moves). Nothing merges, leaves draft or is re-pasted without Parker. Run
`python3 scripts/check_marketplace.py` after every task that touches a skill, README or
manifest.

---

## PR A

### Task 1: Copy the launcher (no behaviour change yet)

1. `cp plugins/bbs-tools/bin/bbs-fill plugins/bbs-sales/scripts/bbs-fill`; `git add`; set
   mode `100755` (`git update-index --chmod=+x`). `plugins/bbs-tools/` stays untouched
   until PR B.
2. Add `plugins/bbs-sales/scripts/bbs-fill text eol=lf` to `.gitattributes`.
3. Check: `ALLOWED` in the new file equals `ALLOWED` on `main` byte for byte: #68's and
   #84's entries present, and **`bbs-quote-builder/scripts/build_quote.js` absent** (#68
   retires that skill, Parker 2026-11-11; #84's branch still lists it, so confirm it did not
   come back with whichever merged second). Do not re-add it.

### Task 2: Re-anchor the launcher on its own plugin root (spec §2)

1. Replace the `market=…/../../..` computation with `root=$(cd "$(dirname "$self")/.." && pwd -P)`;
   require `script` = `$root/skills/<one of ALLOWED>` after `real()`; refuse if `$root` is a
   link.
2. Keep `cache=` as `$root/../../..` for the argument check; keep every other block as is.
3. Header: rewrite the STABLE INTERFACE paragraph (spec §2); keep the path-pattern
   paragraph and add the hook sentence.
4. Check: copy `plugins/bbs-tools/tests/test_bbs_fill.py` to
   `plugins/bbs-sales/scripts/tests/test_bbs_fill.py`, port the fixture to
   `<tmp>/cache/<market>/bbs-sales/<ver>/{scripts,skills}`, drop `build_quote.js` from any
   fixture. All ported tests pass. Add and pass: other-version script refused; mode
   `100755`; no CR in the file; the `.gitattributes` rule is present.

### Task 3: The hook, Python half (spec §3.2–3.6)

1. `plugins/bbs-sales/hooks/fill-gate.py`, stdlib only: read stdin JSON → checks 1–6 → print
   the allow JSON or nothing; exit 0 always; any exception → nothing.
2. Lexer: a small state machine over **code points**, written from the spec's grammar, not
   from `shlex`. Unquoted runs ASCII only; no unquoted word-initial `=`; forbidden set = every
   `Cc` code point plus U+2028, U+2029.
3. Path checks per spec §3.5: exact code-point comparison after separator and drive
   normalisation; the link walk **starts at the root itself**.
4. `ALLOWED` from `$CLAUDE_PLUGIN_ROOT/scripts/bbs-fill`: any CR in the file or any entry
   not matching `^"[a-z0-9-]+/scripts/[A-Za-z0-9_.-]+\.(py|js)"$` → no decision for every
   command.
5. Check: `python3 -m py_compile`; the case file (task 5) passes on the Python half.

### Task 4: The hook, PowerShell half

1. `plugins/bbs-sales/hooks/fill-gate.ps1`: same checks, same reason string, ASCII-only
   source, runs on Windows PowerShell 5.1 and pwsh 7 (no `ResolveLinkTarget`, no `?.`, no
   ternary).
2. Code points via `[char]::ConvertToUtf32` over surrogate pairs; a lone surrogate rejects.
   No `[char]::IsLetter`, no Unicode category tables.
3. Reparse-point test via `(Get-Item -Force $p).Attributes -band [IO.FileAttributes]::ReparsePoint`,
   from the root down.
4. Check: `run-tests.ps1` cases pass under pwsh 7.

### Task 5: Hook tests and parity (spec §8)

1. `hooks/tests/fill_gate_cases.json`: every row of both spec §8 tables, including the
   cases Rex added: zsh `=` (leading and word-initial), non-BMP letters and NFD names
   (quoted → allow, unquoted → none), root differing only in case or normalisation, symlink
   at the root and at the launcher, word 0 built from quoted and unquoted runs, roots with
   spaces, non-ASCII or a trailing `/`, CRLF launcher, malformed `ALLOWED` entry. Paths are
   placeholders the runner fills from a temp fake root.
2. `hooks/tests/fill_gate_parity.py`: runs each case through both halves; compares decision
   and reason; `BBS_REQUIRE_PS=1` makes a missing PowerShell a FAIL; prints the allow table.
3. Same file: the differential check against **bash and zsh** and the fixed-seed fuzz
   (spec §8). `BBS_REQUIRE_SHELLS=1` makes a missing `zsh` a FAIL (set in CI).
4. Same file: the `updatedInput` guard (grep `plugins/`, fail on any Bash hook returning it).
5. `run-tests.ps1`: load the same JSON and assert the PowerShell half alone.
6. Mutation check, recorded in the PR: disable, in turn, the `;` rejection, the word-0
   check, the root-included link walk, the word-initial `=` rejection, and the CR check.
   Each must turn at least one case red.

### Task 6: Wire the hook

1. Add the `PreToolUse` / `Bash` entry to `plugins/bbs-sales/hooks/hooks.json` with the
   `sh` pre-filter and the house interpreter chain (pwsh → powershell → python3 → silent
   `exit 0`), `timeout` 10, no `statusMessage`.
2. Extend `parity.py`'s `check_entry()` (from #84) to run this entry through `sh` with
   stub interpreters: nothing starts for a command without `bbs-fill`; stdin arrives intact.
3. Update the `hooks.json` `description` by one sentence.

### Task 7: Repoint every skill line

1. Replace every `bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/` with
   `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/` in
   `plugins/bbs-sales/**/*.md`, including #68's `bc-quote-entry` and #84's `desk-remember`.
2. Replace each "if `bbs-fill` is not found, `bbs-tools` is missing" paragraph with the
   spec §3.9 wording, verbatim. Never tell the rep to approve a form-script prompt.
3. `ca-form-filler/references/packets/README.md`: new `ALLOWED` path.
4. `bbs-sales/README.md`: drop `bbs-tools` lines; Hooks table gains `fill-gate`.
5. Check: the launcher test "no bare `bbs-fill \"`" passes; the skill-line test finds every
   line and each is on `ALLOWED`. No `description:` changes, so the routing eval is not
   re-run; say so in the PR.

### Task 8: Managed-settings docs and the checkup (no re-paste in PR A)

1. `MANAGED-SETTINGS.md`: new section "Form scripts: a hook, not a rule (2026-11-11)" with
   spec §3.1, §3.3, both §3.4 paragraphs, and §3.8's dependency sentence; say
   `Bash(bbs-fill *)` and `bbs-tools` stay until PR B. The `permissions.allow` row points
   at the section. **`bbs-managed-settings.json` is not edited in PR A.**
2. `bbs-checkup.md` check 12: spec §4 "Check 12, new text", including the auto-mode line.
3. CI: new launcher test path; hook parity with `BBS_REQUIRE_PS=1` and
   `BBS_REQUIRE_SHELLS=1`; a `macos-latest` job running the hook parity and the bash/zsh
   differential. The old `plugins/bbs-tools/tests/test_bbs_fill.py` step stays until PR B.

### Task 9: Record the ruling

`docs/STEWARD.md` register: "**bbs-fill into bbs-sales — RULED 2026-11-11.** Parker, in
session: \"Yes … to the tools fix as a separate slice\"." Add one line on what it approved,
one on the two-PR split (sequencing, Rex's review of 8eff944), and a pointer to the spec.
Nothing restated.

### Task 10: Checker FAIL, not in this slice

Do not edit `scripts/check_marketplace.py`. The FAIL on a top-level `bin/` in any
`plugins/*` is a review-side follow-up (steward, 2026-11-11).

### Task 11: Versions, gates, PR A

1. Versions (steward, 2026-11-11): `bbs-sales` **0.16.0** (#77 merged at 0.13.0; #68 holds
   0.14.0, #84 holds 0.15.0), `bbs-foundations` **0.5.3** (#72 holds 0.5.0, #68 0.5.1, #84
   0.5.2). Ask the steward about marketplace `metadata.version` if it moves. This plan is
   the one place the numbers live; the spec points here.
2. Full local gate: `check_marketplace.py` exit 0; launcher tests; hook parity with pwsh
   and zsh present; `check_claude_md.py "$PWD"` exit 0.
3. Draft PR A. In the body:
   - what a rep will notice: form scripts still run without an Allow click; nothing to
     install; if one ever prompts, Claude stops and points them to `/bbs-checkup` instead of
     asking them to approve it;
   - the ruling; the two-PR split; spec §5 as Parker's checklist;
   - **merge gates V1–V3 (spec §6) as unchecked boxes Parker runs before merging.** V1 uses
     a test copy renamed `bbs-sales-v1`, loaded with `claude --debug --plugin-dir`, runs the
     full Packet B sequence in auto mode twice (server review as is, then
     `CLAUDE_CODE_AUTO_MODE_SERVER=0`), and passes only if the debug log shows fill-gate's
     allow reason and the new launcher form for every call. V2 runs in Manual mode with no
     Outlook or Teams send. V3 records the Windows root string and that Git Bash runs it.
4. Stop. Rex reviews; findings come back to this worker.

### After PR A merges (Parker, outside the repo)

- [ ] Reps restart. One rep runs `/bbs-checkup`; check 12 passes, auto-mode line included,
      and `/plugin` shows `bbs-sales` 0.16.0 on that machine.
- [ ] Only then does the steward dispatch PR B.

## PR B

### Task 12: Retire `bbs-tools` (spec §4, "PR B")

1. Branch from `main` after PR A has merged **and** check 12 has passed on a rep machine.
2. `marketplace.json`: remove the entry; add `"renames": {"bbs-tools": null}`. Do not set
   `forceRemoveDeletedPlugins`. Run `claude plugin validate .` if the CLI is available; else
   say it was not run.
3. `git rm -r plugins/bbs-tools`.
4. `bbs-managed-settings.json`: drop `bbs-tools@…` from `enabledPlugins` and
   `Bash(bbs-fill *)` from `permissions.allow`. `MANAGED-SETTINGS.md`, `bbs-checkup.md`,
   `README.md`, `PLUGINS.md`, `SYSTEM-OVERVIEW.md`, `REP-SETUP.md`, `REGISTRY.md` per the
   spec §4 PR B table. CI: drop the old launcher test step.
5. Check: `grep -rn "bbs-tools" --exclude-dir=.git .` returns only `marketplace.json`'s
   `renames`, `REGISTRY.md`, `docs/STEWARD.md`, dated specs, plans and assessments, and
   `MANAGED-SETTINGS.md` history sentences. `grep -rn "Bash(bbs-fill"` returns only history
   sentences.
6. Versions: the steward allocates them at build time.
7. Draft PR B. Body: the re-paste order (spec §5, steps 7–8), and the rep notice: a recurring
   "bbs-tools removed from the marketplace" message is expected until Parker re-pastes, and
   it is harmless.

### After PR B merges (Parker, outside the repo)

- [ ] Reps restart.
- [ ] Re-paste `bbs-managed-settings.json` (ADMIN-RUNBOOK §1). Never before PR A's
      `bbs-sales` is confirmed on rep machines.
- [ ] Re-run organization sync; confirm no `bin/` error.

## Follow-ups (separate PRs, not this slice)

- The launcher refuses output paths under `FILLED/` (spec §2, "Not fixed here"). Today
  neither `guard-tree` nor the launcher stops a fill that writes into a submitted packet.
- Review side: checker FAIL on a top-level `bin/` in any plugin.

---

Owner: Parker Marshall. Written 2026-11-11; revised the same day after Rex's review of
8eff944.
