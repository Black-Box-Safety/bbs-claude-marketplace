# Remove skill-bus; doctrine moves to native plugin hooks — design

**Date:** 2026-09-28
**Ruling:** Parker, in session, 2026-09-28. The third-party plugin `joeymnguyen/skill-bus`
"causes issues and has permeated throughout the entire set up." It is removed from the
marketplace, from managed settings, and from every rep install. The doctrine text it
injected is **kept** and re-homed on Claude Code's native hooks, so a rep sees no change in
what a skill run receives.

## What skill-bus did here

Two plugins each shipped a `hooks/skill-bus.json`:

| File | Inserts | Subscriptions |
|---|---|---|
| `plugins/bbs-foundations/hooks/skill-bus.json` | `bbs-claude-md-doctrine`, `bbs-grounding-doctrine` | 15 |
| `plugins/bbs-website/hooks/skill-bus.json` | `bbs-storefront-doctrine`, `bbs-catalog-doctrine` | 12 |

A subscription is `{insert, on, when: "pre"}` where `on` is a `plugin:skill` pattern with
`*` wildcards (some cross-plugin: `claudeforge*`, `shopify`, `impeccable:*`,
`frontend-design:*`). Skill-bus, once a rep ran `/skill-bus:onboard`, copied these into a
per-machine `~/.claude/skill-bus.json` and injected the insert text before the matching skill
ran. That per-machine copy is why "permeated": the truth lived in three places (the two
repo files, the machine copy) and the onboarding step was a manual prerequisite that
`/bbs-checkup` had to police.

## Design

### One plain file per insert

The four insert texts move **verbatim, byte-for-byte** out of the JSON `text` values into:

```
plugins/bbs-foundations/hooks/doctrine/bbs-claude-md-doctrine.md
plugins/bbs-foundations/hooks/doctrine/bbs-grounding-doctrine.md
plugins/bbs-website/hooks/doctrine/bbs-storefront-doctrine.md
plugins/bbs-website/hooks/doctrine/bbs-catalog-doctrine.md
```

Each file is the decoded string and nothing else — no heading, no trailing newline. The
hook reads the file; nothing re-keys the text. The 2026-09-22 channel-rule wording (PR #30)
is therefore carried unchanged, and the PR proves it with a byte comparison against
`git show origin/main:<skill-bus.json>`.

The `bbs-claude-md-doctrine` text contains a literal `${CLAUDE_PLUGIN_ROOT}` — that is how
it read under skill-bus and it is kept as is. Whether the hook should expand it is a
separate question, deliberately not decided here.

### One subscription table per plugin

`plugins/<plugin>/hooks/doctrine/subscriptions.json`:

```json
{
  "inserts": { "<insert>": { "file": "<insert>.md" } },
  "subscriptions": [ { "insert": "<insert>", "on": "<plugin:skill pattern>" } ]
}
```

The `on` patterns are carried over exactly. `when: "pre"` is dropped: every subscription
was `pre`, and the native event is `PreToolUse`, so the key would be a constant. One
addition, owed from the PR #25 review: `bbs-grounding-doctrine` also fires on
`bbs-claude-coach:*`.

Match semantics: the invoked skill name (the Skill tool's `tool_input.skill`, e.g.
`bbs-sales:naspo-quote`) is tested against every `on` pattern with `*` as a glob wildcard,
case-insensitively. Every insert with at least one matching subscription is injected once,
in table order, joined by a blank line. Skill-bus's `maxMatchesPerSkill` cap is not carried:
the table has at most two inserts per plugin, so it could never bind.

### The native hook — two events, one table

`plugins/<plugin>/hooks/hooks.json` declares the same command under two events:

- **`PreToolUse`, matcher `Skill`** — Claude called the Skill tool; `tool_input.skill` is
  the fully qualified name (`bbs-sales:naspo-quote`).
- **`UserPromptExpansion`, matcher `""`** — the user typed `/name`. A `PreToolUse` hook
  does not fire on that path; this event does (Claude Code hooks reference). It carries
  `command_name`, usually bare (`bbs-checkup`, `command_source: "plugin"`) and sometimes
  prefixed. This is the path skill-bus's `monitorSlashCommands: true` covered — the
  2026-09-02 forge spec turned it on deliberately — so it is carried, not dropped.

The script (`doctrine.ps1`, and `doctrine.py` as its twin — below):

1. reads the hook JSON from stdin (a leading BOM tolerated); on empty or unparseable
   input exits 0 silently;
2. routes on `hook_event_name` (falling back to `tool_name == "Skill"` when absent) and
   takes the name from `tool_input.skill` or `command_name`; returns nothing unless it is
   a non-blank string;
3. returns nothing for `expansion_type: "mcp_prompt"` — an MCP server's prompt named
   like a skill is not a skill. A name with a colon (every tool call; a typed
   `/plugin:name`) is matched against the whole pattern. A bare typed name does not say
   which plugin it came from, and skill-bus's own rule for it (`match_subscriptions_prompt`
   in its dispatcher) is kept verbatim: a bare pattern matches as is; a `plugin:suffix`
   pattern matches the name against its suffix; a `plugin:*` or `plugin:**` pattern is
   skipped, because a bare name cannot claim a whole plugin. So a typed `/bbs-checkup` or
   `/brainstorming` gets nothing, exactly as under skill-bus, and a typed
   `/bbs-claude-md-forge` gets the CLAUDE.md doctrine (via the bare pattern) and not the
   grounding doctrine. Nothing is derived from the plugin's directory name: on an installed
   machine `${CLAUDE_PLUGIN_ROOT}` ends in a version string, not the plugin name;
4. loads `doctrine/subscriptions.json` beside itself, matches (`*` glob,
   case-insensitive, other metacharacters literal), reads each matched insert's file as
   UTF-8 (BOM stripped, `\r\n` normalised to `\n` in case of an autocrlf checkout);
5. prints `{"hookSpecificOutput":{"hookEventName":"<event>","additionalContext":"<text>"}}`
   in exactly the form Python's `json.dumps(ensure_ascii=True)` emits — every non-ASCII
   character escaped — so the bytes are the same from either script and under Windows
   PowerShell 5.1's OEM console encoding;
6. exits 0 on every path, including its own errors (`trap { exit 0 }` / a bare
   `except`), prints nothing to stderr, never blocks a skill, never writes a file.
   Timeout 10 s.

**Interpreter choice — PowerShell, and why.** The rep bootstrap (`scripts/bbs-setup.ps1`)
installs Git, Node, Chrome, pdftotext, pandoc and `uv`. It does **not** put `python3` on
PATH — `check_marketplace.py` already warns about exactly this (`bootstrap_caveat`) — so a
Python hook would silently do nothing on a stock rep machine. Windows PowerShell 5.1 is on
every Windows machine, which is why `bbs-sales` already ships its two hooks as `.ps1`
(`plugins/bbs-sales/hooks/hooks.json`, "PowerShell, exec form, Windows rep machines").
This follows that precedent.

**Windows and macOS with one command.** Claude Code runs a hook's `command` string through
Git Bash on Windows (the bootstrap installs Git for this reason; `docs/COMMONS.md` records
it) and `sh -c` on macOS. So the command is a small POSIX-shell selector:

```sh
command -v pwsh >/dev/null 2>&1 && exec pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.ps1"; command -v powershell >/dev/null 2>&1 && exec powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.ps1"; command -v python3 >/dev/null 2>&1 && exec python3 "${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.py"; exit 0
```

pwsh (PowerShell 7) if present on either platform, else Windows PowerShell 5.1, else
`python3` running `doctrine.py`, else exit 0 silently. The third arm exists because Parker
is on a Mac: a Mac has `python3` (with the Xcode command-line tools) long before anyone
runs `brew install powershell`, and without that arm it would silently get no doctrine.
`doctrine.py` is stdlib only (`json`, `fnmatch`) and carries the same semantics, including
the `UserPromptExpansion` branch; `hooks/tests/parity.py` runs both interpreters on the
same fixtures and requires byte-identical stdout (it skips the PowerShell half, without
failing, when neither `pwsh` nor `powershell` is on PATH — except under `BBS_REQUIRE_PS=1`,
which the CI workflow sets, so CI proves parity rather than skipping it; GitHub's
`ubuntu-latest` image ships `pwsh`). A machine with none of the
three gets no doctrine and no error — degraded, not broken, and `/bbs-checkup` reports it.
The `.ps1` is written to the PowerShell 5.1 subset (no `??`, no ternary, no
`-AsHashtable`) so both PowerShells run the same file. `${CLAUDE_PLUGIN_ROOT}` is the only
path form used.

A Windows machine that skipped the bootstrap has no Git Bash, and Claude Code then hands
the command string to `powershell.exe`, which cannot parse the `sh` selector: the hook
reports an error on every skill call and the skill still runs. `/bbs-checkup` check 9 names
that case; the fix is the bootstrap.

The same `doctrine.ps1` and `doctrine.py` ship in both plugins because
`${CLAUDE_PLUGIN_ROOT}` is per plugin and one plugin cannot address another's files. Two
copies of code is a drift risk, so the checker FAILs if either pair differs
(`doctrine_hook_drift`) — a fact with a checker.

**No shell fast path.** Skipping the interpreter when stdin cannot match (a `grep -q` for
the plugin's subscription prefixes before the `exec`) would save the interpreter start on
most Skill calls, but the prefixes would then live a second time inside `hooks.json`, and
that is the re-keyed fact this repo exists to avoid. The cost stays: one PowerShell start
per Skill call or typed command, well inside the 10 s timeout.

### What is dropped with no native equivalent

From skill-bus's `settings` block: `maxMatchesPerSkill`, `telemetry` (the
`skill-bus-telemetry.jsonl` file), `observeUnmatched`, `showConditionSkips`.
`monitorSlashCommands` is **not** dropped — `UserPromptExpansion` is its native
equivalent, above. Native hooks have no telemetry file, so `/bbs-review` can no longer
read match/no-match coverage from disk; it now checks coverage by reading the subscription
table against the plugin's skill list. `/skill-bus:onboard` and `skill-bus:list-subs` no
longer exist and no step replaces them: the hook is active the moment the plugin is
installed.

### Checker

`check_skill_bus` is replaced by `check_doctrine_hooks`, which walks every
`plugins/*/hooks/doctrine/subscriptions.json` and FAILs when:

- the file does not parse, or a subscription names an insert the table does not define;
- an insert's `file` is missing on disk, or is empty;
- a non-wildcard `plugin:skill` target naming a local plugin resolves to no skill or
  command in that plugin (`doctrine_sub_dangling`), or to a skill that lives in another
  plugin (`doctrine_sub_wrong_plugin`) — the old dangling / wrong-plugin checks, carried;
- the plugin's `hooks/hooks.json` does not parse, or a `command` / `args` path under
  `${CLAUDE_PLUGIN_ROOT}` does not exist in the plugin (`hook_script_missing`);
- the two `doctrine.ps1` copies differ, or the two `doctrine.py` copies differ.

A new repo-wide scan, `retired_plugin_ref`, FAILs on the literal `skill-bus` anywhere
outside `docs/superpowers/` and `docs/SESSION-HANDOFF-*` unless the mention is a
counter-example. For this scan the qualifier must be **in the same sentence** as the name
(split on `.`, `!`, `?`), not merely within the usual 200-character proximity: "Never guess
a price. Then run /skill-bus:onboard to finish." is an instruction to run it and FAILs.
The checker assembles the token from parts so it is not its own hit. `uninstall` and
`retire` join the counter-example vocabulary for this reason. The name-keying comments
that cited skill-bus as the reason skills key on `plugin:skill` now cite the doctrine
tables.

### Managed settings

`plugins/bbs-foundations/docs/bbs-managed-settings.json`: `extraKnownMarketplaces` loses
`skill-bus-marketplace`; `enabledPlugins` loses `skill-bus@skill-bus-marketplace`. In
`claudeMd`, exactly three substrings change and nothing else; the before/after strings are
quoted in the PR body. The `permissions` block is byte-identical.

1. `then /skill-bus:onboard so the doctrine injects automatically` → a truthful sentence:
   the doctrine injects automatically through the plugins' own hooks; nothing to run. The
   comma before it becomes a full stop (review nit: the first draft left a comma splice).
2. `The DVBE incentive (SCM 1202) still applies, on competitive solicitations only, never
   on` → `... applies on every competitive solicitation, informal ones included, never on`
   — Parker's 2026-09-22/23 ruling, already in canonical-facts.md and PR #30/#31; this
   string was the last propagation site not updated.

### Docs

Every live mention rewritten to describe the native hooks; `/bbs-checkup` check 9 verifies
the two `hooks.json` files parse and the four doctrine files exist instead of looking for
`~/.claude/skill-bus.json`; check 1 no longer lists skill-bus as a plugin. `docs/STEWARD.md`
records the ruling as resolved and opens the one thing a repo change cannot do; the admin
runbook gets the per-machine uninstall steps. `docs/superpowers/` and
`docs/SESSION-HANDOFF-2026-09-15.md` stay as history and are not edited.

## Not in scope

Any skill `description:`, `models.json`, `vendor_profile.json`, `ca-form-rules.md`,
`fill_obs_packet.py`, other plugins' `marketplace.json` entries. Expanding
`${CLAUDE_PLUGIN_ROOT}` inside the injected text. The `bbs-shopify` repo's own
canonical-facts line, still open there.

## Verification

- `python3 scripts/check_marketplace.py` → 0 FAIL.
- `grep -rli skill-bus` outside `.git`, `docs/superpowers`, `SESSION-HANDOFF` → only
  counter-example mentions the checker accepts, listed in the PR.
- Every `hooks.json`, `subscriptions.json` and `bbs-managed-settings.json` parses.
- Each doctrine `.md` is byte-identical to the corresponding `text` value in
  `origin/main:<skill-bus.json>` — asserted by a script, result printed in the PR.
- `doctrine.ps1` run under pwsh 7 with a fake stdin returns the grounding doctrine for
  `bbs-sales:naspo-quote`, the storefront doctrine for `bbs-website:product-page`, and
  nothing for `unrelated`; `hooks/tests/run-tests.ps1` covers every subscription and both
  typed-command forms; `hooks/tests/parity.py` covers the edge cases (combined inserts,
  case, metacharacters in the name, missing or odd `tool_input`, BOM on stdin and on a
  doctrine file, CRLF doctrine file, missing table, empty stderr) through both
  interpreters and requires identical bytes. Windows PowerShell 5.1 is not available in
  the build environment: that path is unverified by the builder and is called out in the
  PR.

---

Owner: Parker Marshall. Last verified 2026-09-28.
