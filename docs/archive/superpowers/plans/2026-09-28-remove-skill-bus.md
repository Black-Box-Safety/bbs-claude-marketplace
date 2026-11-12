# Remove skill-bus; doctrine moves to native plugin hooks — plan

Spec: `docs/superpowers/specs/2026-09-28-remove-skill-bus.md`. Branch
`claude/remove-skill-bus` off `main` at `6f4ce16`. Ends at a PR, not a merge.

## 1. Extract the doctrine, byte-for-byte

- `git show origin/main:plugins/bbs-foundations/hooks/skill-bus.json` and the website one;
  decode each `inserts.<name>.text` with `json.load` and write it, UTF-8, no trailing
  newline, to `plugins/<plugin>/hooks/doctrine/<name>.md`.
- Write `plugins/<plugin>/hooks/doctrine/subscriptions.json` from the old `subscriptions`
  list: same `insert`, same `on`, drop `when`. Append `{"insert": "bbs-grounding-doctrine",
  "on": "bbs-claude-coach:*"}` to the foundations table (PR #25 follow-up).
- Assert: `open(md,'rb').read() == old_text.encode('utf-8')` for all four. Keep the script
  in the scratchpad; print the result into the PR.

## 2. The hook

- `plugins/bbs-foundations/hooks/doctrine.ps1`, PowerShell 5.1-compatible: read stdin,
  gate on `tool_name == "Skill"`, glob-match `tool_input.skill` against the table, read
  matched files, emit `hookSpecificOutput.additionalContext` with non-ASCII escaped,
  `trap { exit 0 }`, no writes. Copy byte-identical to `plugins/bbs-website/hooks/`.
- `plugins/<plugin>/hooks/hooks.json`: `PreToolUse`, matcher `Skill`, the pwsh-then-
  powershell shell selector from the spec, `timeout: 10`, a `statusMessage`.
- `plugins/<plugin>/hooks/tests/run-tests.ps1` on the `bbs-sales` pattern: the three
  stdin cases from the spec plus empty stdin and a non-Skill tool.
- Run the tests under the scratchpad pwsh 7. Record that 5.1 is unverified.
- `git rm` both `skill-bus.json` files.

## 3. Managed settings

- Remove the marketplace entry and the enabledPlugins line. Two substring replacements in
  `claudeMd`, done with `str.replace` on the parsed JSON value and re-serialised with the
  file's existing indentation and escaping, so nothing else in the file moves. Diff shows
  exactly those hunks; `permissions` untouched.

## 4. Checker

- Replace `check_skill_bus` with `check_doctrine_hooks` (parse, insert resolution, file
  existence, dangling / wrong-plugin targets, hooks.json command paths, ps1 drift).
- Add the `skill_bus_reference` repo-wide scan with counter-example awareness; add
  `uninstall` to `COUNTER_EXAMPLE`; exempt the checker itself and the archive/narrative
  paths already exempted elsewhere.
- Rewrite the three name-keying comments (`load_skills` docstring, `duplicate_skill_name`,
  `name_folder_mismatch`) to cite the doctrine tables.
- Update the module docstring line that names skill-bus.

## 5. Docs sweep

One pass over every live hit from `grep -rli skill-bus`, rewriting to describe the native
hooks: `.claude-plugin/PLUGINS.md`, `.claude/agents/steward.md`,
`.cursor/rules/reviewing-changes.mdc`, `.github/workflows/check-marketplace.yml`,
`.gitignore`, `README.md`, `docs/ADMIN-CLEANUP.md`, `docs/MAINTAINER-GUIDE.md`,
`docs/REP-SETUP.md`, `docs/STEWARD.md`, `plugins/bbs-foundations/{README.md,
commands/bbs-checkup.md, docs/MANAGED-SETTINGS.md, docs/ONBOARDING.md,
skills/bbs-claude-md-forge/references/{bbs-doctrine.md, canonical-facts.md}}`,
`plugins/bbs-website/{.claude-plugin/plugin.json, README.md, agents/storefront-pages.md,
commands/{bbs-onboard.md, bbs-review.md}, docs/ONBOARDING.md,
skills/site-wiring-map/SKILL.md}`. `CLAUDE.md` / `AGENTS.md` do not mention it.

- `/bbs-checkup`: drop skill-bus from check 1; check 9 becomes hooks.json parse + doctrine
  files exist (+ pwsh/powershell resolves).
- `docs/STEWARD.md` "Already open for Parker": resolved entry for the ruling; new open
  item for the per-machine uninstall and the managed-settings re-paste.
- `docs/ADMIN-RUNBOOK.md`: local uninstall steps; `docs/ADMIN-CLEANUP.md`: the
  marketplace line becomes "remove".
- Historical: `docs/superpowers/**`, `docs/SESSION-HANDOFF-2026-09-15.md` untouched.

## 6. Verify, commit, PR

- `python3 scripts/check_marketplace.py` → 0 FAIL; note the WARN count.
- The grep, the JSON parses, the byte assertion, the three hook runs — outputs verbatim
  into the PR body.
- Commit with the session trailer; `git push -u origin claude/remove-skill-bus`; open the
  PR to `main` titled "Remove skill-bus; doctrine moves to native plugin hooks"; remove
  the worktree.

---

Owner: Parker Marshall. Last verified 2026-09-28.
