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

### The native hook

`plugins/<plugin>/hooks/hooks.json` declares a `PreToolUse` hook with matcher `Skill`
that runs `${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.ps1`. The script:

1. reads the hook JSON from stdin; on empty or unparseable input exits 0 silently;
2. returns nothing unless `tool_name` is `Skill` and `tool_input.skill` is a string;
3. loads `doctrine/subscriptions.json` beside itself, matches, reads each matched insert's
   file as UTF-8 (normalising `\r\n` to `\n` in case of an autocrlf checkout);
4. prints `{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"<text>"}}`
   with every non-ASCII character JSON-escaped, so the output is the same bytes under
   Windows PowerShell 5.1's OEM console encoding and pwsh 7's UTF-8;
5. exits 0 on every path, including its own errors (`trap { exit 0 }`). It never blocks a
   skill and never writes a file. Timeout 10 s.

**Interpreter choice — PowerShell, and why.** The rep bootstrap (`scripts/bbs-setup.ps1`)
installs Git, Node, Chrome, pdftotext, pandoc and `uv`. It does **not** put `python3` on
PATH — `check_marketplace.py` already warns about exactly this (`bootstrap_caveat`) — so a
Python hook would silently do nothing on a stock rep machine. Windows PowerShell 5.1 is on
every Windows machine, which is why `bbs-sales` already ships its two hooks as `.ps1`
(`plugins/bbs-sales/hooks/hooks.json`, "PowerShell, exec form, Windows rep machines").
This follows that precedent.

**Windows and macOS with one script.** Claude Code runs a hook's `command` string through
Git Bash on Windows (the bootstrap installs Git for this reason; `docs/COMMONS.md` records
it) and `sh -c` on macOS. So the command is a small POSIX-shell selector:

```sh
command -v pwsh >/dev/null 2>&1 && exec pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.ps1"; command -v powershell >/dev/null 2>&1 && exec powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/doctrine.ps1"; exit 0
```

pwsh (PowerShell 7) if present on either platform, else Windows PowerShell 5.1, else exit 0
silently. A Mac without `pwsh` (`brew install powershell`) gets no doctrine and no error —
degraded, not broken, and `/bbs-checkup` reports it. The script is written to the
PowerShell 5.1 subset (no `??`, no ternary, no `-AsHashtable`) so both interpreters run the
same file. `${CLAUDE_PLUGIN_ROOT}` is the only path form used.

The same `doctrine.ps1` ships in both plugins because `${CLAUDE_PLUGIN_ROOT}` is per plugin
and one plugin cannot address another's files. Two copies of code is a drift risk, so the
checker FAILs if they differ (`doctrine_hook_drift`) — a fact with a checker.

### What is dropped with no native equivalent

Skill-bus's `settings` block: `maxMatchesPerSkill`, `telemetry` (the
`skill-bus-telemetry.jsonl` file), `observeUnmatched`, `monitorSlashCommands`,
`showConditionSkips`. Native hooks have no telemetry file, so `/bbs-review` can no longer
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
- the two `doctrine.ps1` copies differ.

A new repo-wide scan, `skill_bus_reference`, FAILs on the literal `skill-bus` anywhere
outside `docs/superpowers/` and `docs/SESSION-HANDOFF-*` unless the mention is a
counter-example (a sentence saying it is retired, or telling Parker to uninstall it). The
checker's own copy of the token is exempt, as its other self-referential scans are.
`uninstall` joins the counter-example vocabulary for this reason. The name-keying comments
that cited skill-bus as the reason skills key on `plugin:skill` now cite the doctrine
tables.

### Managed settings

`plugins/bbs-foundations/docs/bbs-managed-settings.json`: `extraKnownMarketplaces` loses
`skill-bus-marketplace`; `enabledPlugins` loses `skill-bus@skill-bus-marketplace`. In
`claudeMd`, exactly two substrings change and nothing else; both before/after strings are
quoted in the PR body. The `permissions` block is byte-identical.

1. `then /skill-bus:onboard so the doctrine injects automatically` → a truthful sentence:
   the doctrine injects automatically through the plugins' own hooks; nothing to run.
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
  nothing for `unrelated`. Windows PowerShell 5.1 is not available in the build
  environment: that path is unverified by the builder and is called out in the PR.

---

Owner: Parker Marshall. Last verified 2026-09-28.
