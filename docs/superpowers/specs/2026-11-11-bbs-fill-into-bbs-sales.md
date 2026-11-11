# Move `bbs-fill` into `bbs-sales`, replace the PATH-name allow rule with a hook, retire `bbs-tools`

Status: **design, for review.** Nothing here is built. Implementation waits for #68 and #84
to be on `main` (§7).

**RULED 2026-11-11.** Parker, in session: "Yes … to the tools fix as a separate slice",
approving the steward's proposal to move the `bbs-fill` launcher out of `bbs-tools`'
top-level `bin/` into `bbs-sales`, replace the PATH-name allow rule with a vetted-command
PreToolUse hook, and retire `bbs-tools`. The register entry in `docs/STEWARD.md` lands with
the implementation PR (plan, task 9); this spec cites the ruling and does not restate the
register.

---

## 1. The problem

claude.ai organization sync skipped `bbs-tools`:

> Plugin contains a top-level bin/ directory ('bin/bbs-fill'). claude.ai-hosted plugins may
> not ship bin/ executables … Declare executable entry points via hooks, commands, or
> mcpServers instead.

The docs read today agree and name the fix:

- *Host a marketplace*, "Distribute through organization settings"
  (`code.claude.com/docs/en/plugins/host-marketplace`): "**Top-level `bin/` directory**:
  claude.ai rejects a plugin that has one and syncs the rest of the marketplace. … Keep
  executables in another directory, such as `scripts/`, and reference them as
  `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` from your hooks or MCP server configs."
- *Plugins reference*, directory table: "claude.ai and Cowork don't install a plugin that
  has this directory, including one you distribute through claude.ai organization
  settings." (`claude.com/docs/plugins/platform-support` redirects into the same pages.)

There is no documented stable path from one plugin to another plugin's files: the
reference documents `${CLAUDE_PLUGIN_ROOT}` as "Absolute path of the plugin's installed
version", for that plugin only, and says it "changes when the plugin updates". So the
launcher must live in the plugin whose scripts it runs. That plugin is `bbs-sales`, the
only consumer:

| Skill | Scripts on `ALLOWED` today |
|---|---|
| `ca-form-filler` | `fill_obs_packet.py`, `fill_packet_c.py`, `packet_profile.py`, `render_pages.py` |
| `naspo-quote` | `fill_ca_forms.py`, `inspect_form.py` |
| ~~`bbs-quote-builder`~~ | ~~`build_quote.js`~~: **not carried.** #68 deletes the skill and removes the entry (Parker, 2026-11-11, per the steward). The launcher's `.js` → `node` branch stays, unused, so a future vetted `.js` needs no launcher change |
| `sam-gov-opportunities` | `sam_opportunities.py` |
| `usaspending-awards` | `usaspending_awards.py` |
| `bc-item-entry` | `bc_item_entry.py` |
| `bc-quote-entry` (#68) | `bc_quote_entry.py` (R3) |
| `desk-remember` (#84) | `desk_memory.py` (R7, A3) |

## 2. Decision 1: where the launcher goes

**`plugins/bbs-sales/scripts/bbs-fill`**, git mode `100755`, invoked by skills as:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>" <args…>
```

Why the variable is safe to write in a skill: the plugins reference, "Where each variable
resolves", says `${…}` resolves "Anywhere in the Markdown body" of skill content, and "The
variables aren't present in the environment of commands Claude runs through the Bash tool
… write the `${...}` reference in the Markdown body instead, and Claude Code substitutes the
path inline when it loads the content." So the command Claude sends is a literal absolute
path, and the hook (§3) sees that literal path. A command that still contains the text
`${CLAUDE_PLUGIN_ROOT}` would expand to an empty string in the Bash tool and point at
`/scripts/bbs-fill`; the hook refuses any `$` (§3.2), so that never auto-runs.

Every guarantee the launcher gives today is kept, unchanged unless stated:

| Guarantee | Today (`bbs-tools/bin/bbs-fill`) | After |
|---|---|---|
| `ALLOWED` list, by `<skill>/scripts/<file>` | yes | **the list as it stands on `main` after #68 and #84** (§7): their two entries added, `bbs-quote-builder/scripts/build_quote.js` gone. Stays the single home of the list: the hook reads it from the launcher (§3.4), never a copy |
| Where the script may sit | the `bbs-sales` plugin of the **same marketplace cache**, any version folder | **stricter: the launcher's own plugin root**, `<root>/skills/<ALLOWED>`, where `<root>` is `real(dirname(self))/..`. A script from another installed version of `bbs-sales` is refused |
| Symlink / `..` resolution of the script | `real()` | same |
| Version folder may not be a link | yes | becomes "the plugin root may not be a link" |
| Fixed interpreter, `python3 -E` / `python -E` on Git Bash, `node` for `.js` | yes | same |
| No interpreter options; first argument may not start with `-` | yes | same |
| `unset BASH_ENV ENV NODE_OPTIONS PYTHONSTARTUP PYTHONPATH PYTHONHOME` | yes | same |
| Arguments: no dot-folder/dotfile of the home folder, nothing in the plugin cache, no `..`, `--opt=/path` checked, Windows paths normalised | yes | same; "the plugin cache" is still `<root>/../../..` when `<root>` sits at `<cache>/<marketplace>/bbs-sales/<version>` |
| Refuses to run from a forbidden folder | yes | same |
| `set -f`, `#!/bin/bash -p`, exit 64 + `REFUSED` | yes | same |

Header comment changes: the "STABLE INTERFACE: the managed allow rule matches the name
`bbs-fill`" paragraph becomes "the hook in `hooks/fill-gate.*` matches this exact path;
do not move or rename the file". The "why not a path-pattern rule" paragraph stays and
gains the hook sentence (§3.1).

**Known limit, unchanged in kind.** In a repo checkout (`--plugin-dir plugins/bbs-sales`)
`<root>/../../..` is the checkout's parent, so the launcher refuses arguments anywhere under
it. Tests use the fake-cache layout, as today.

## 3. Decision 2: how it runs without a prompt

### 3.1 Why not an allow rule

The obvious replacement, `Bash(*/bbs-sales/*/scripts/bbs-fill *)`, is the rule the
launcher was built to avoid. *Configure permissions*, "Wildcard patterns"
(`code.claude.com/docs/en/permissions`): "A `*` in a Bash rule matches any text, including
spaces". The leading `*` would match `python3 -c '<anything>' /x/bbs-sales/y/scripts/bbs-fill z`,
and the docs warn that "Claude Code matches everything before the first `*` as written, so
those words are what limit the rule": with nothing before the first `*`, nothing limits it.
The absolute path differs per machine and per version, so an exact rule is not possible
either. The launcher's own header records the same reasoning (2026-10-01).

### 3.2 The hook

`plugins/bbs-sales/hooks/fill-gate.py` and `fill-gate.ps1`, a `PreToolUse` entry with
matcher `Bash` in `bbs-sales/hooks/hooks.json`. It returns

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow",
 "permissionDecisionReason":"bbs-fill: vetted script <skill>/scripts/<file>"}}
```

**only** when every condition below holds. Otherwise it prints nothing and exits 0, which
leaves the call to the normal permission flow exactly as if the hook were absent. It never
returns `deny` or `ask`: refusing is the launcher's job, and the guard hook's.

1. `tool_name` is `Bash`, `tool_input.command` is a string, and
   `tool_input.dangerouslyDisableSandbox` is absent or false.
2. `CLAUDE_PLUGIN_ROOT` is set in the hook's environment (the plugins reference: hook
   commands get `CLAUDE_PLUGIN_ROOT` "Exported to the process").
3. The command is **one simple command** under a deny-by-default lexer that accepts a strict
   subset of POSIX `sh` word syntax and nothing else:
   - Words are separated by single spaces or runs of spaces. Nothing else separates.
   - A word is a concatenation of: unquoted runs of `[A-Za-z0-9_./:,=+@%-]` and non-ASCII
     letters; single-quoted runs (`'…'`, any character but `'` and control characters);
     double-quoted runs (`"…"`, any character but `"`, `$`, `` ` ``, `!` and control
     characters, where `\` is allowed only when the next character is none of
     `$`, `` ` ``, `"`, `\` — so a Windows path `"C:\Users\kim\…"` is literal, as in bash).
   - **Anything else rejects the whole command**: `;` `&` `|` `<` `>` `(` `)` `{` `}`, `$`
     anywhere, backtick anywhere, unquoted `\`, `*` `?` `[` `]` `~` `#` `!` `^` unquoted,
     any control character (newline, CR, tab, NUL, C1) or U+2028/U+2029 anywhere, an
     unterminated quote, an empty command.
   - This rejects compound commands, pipes, background `&`, redirects (`>`, `2>&1`, `<<`),
     subshells, command and process substitution, parameter and arithmetic expansion,
     brace and tilde expansion, globs, comments and history expansion — by construction,
     not by a list of known attacks.
4. **Word 0 is the launcher.** After quote removal, word 0, normalised (§3.5), equals
   `<CLAUDE_PLUGIN_ROOT>/scripts/bbs-fill`. A leading `VAR=value` assignment, `env`,
   `exec`, `command`, `bash`, `sh`, `nohup`, `time` or anything else in front fails this.
5. **Word 1 is a vetted script** of this root: normalised, it equals
   `<CLAUDE_PLUGIN_ROOT>/skills/<a>` for some `<a>` on the launcher's `ALLOWED` list.
6. Neither path has a `.` or `..` segment, and no path component from the root down to the
   launcher or the script is a symlink or reparse point (§3.5).

Arguments after word 1 are not inspected: they are data, and the launcher checks them (dot
folders, cache, `..`) before it runs anything. A command the hook allows is therefore a
command the launcher would also have allowed, given the same root.

### 3.3 Precedence: the hook cannot weaken a managed control

*Configure permissions*, "Precedence among rules, hooks, and mods": "PreToolUse hook
decisions don't bypass permission rules. Claude Code evaluates deny and ask rules regardless
of what a PreToolUse hook returns: a matching deny rule blocks the call, and a matching ask
rule still prompts even when the hook returned `"allow"` … including deny rules set in
managed settings." The hooks reference, PreToolUse decision control, repeats it: "Deny and
ask rules are still evaluated regardless of what the hook returns", and "When multiple
PreToolUse hooks return different decisions, precedence is `deny` > `defer` > `ask` >
`allow`."

So:

- **Send controls stay intact.** The Outlook and Teams send-class tools are MCP tools in
  `permissions.ask`, SignNow / QuickBooks sends and `outlook_send_draft` in
  `permissions.deny`. The hook's matcher is `Bash` only; it never sees those calls, and
  even a Bash call that matched an ask or deny rule would still be asked or denied.
- **The managed Bash denies and asks stand** (`rm -rf`, `git push --force`,
  `git reset --hard`, `gh pr merge`, `git push`, `gh pr create` …). A single launcher
  invocation cannot contain them anyway (§3.2.3–4).
- **`guard-tree` still wins.** It is a PreToolUse hook on `Bash` too; if it denies (a write
  into `FILLED/`), `deny` beats our `allow`.
- **What no hook can approve stays unapprovable**: critical-path `rm`, network-path reads
  (*Permission modes*, "An allow rule or `PreToolUse` hook can't approve these").

### 3.4 `allowManagedHooksOnly`

Not set in `bbs-managed-settings.json` today. If Parker sets it, plugin hooks stop, with
one exemption. Hooks reference, "Hook locations": "Your user, project, local, and plugin
hooks are blocked. Hooks from plugins force-enabled in managed settings `enabledPlugins` are
exempt"; settings reference, `allowManagedHooksOnly`: "only managed hooks run, plus Agent SDK
hooks and hooks from plugins your managed settings force-enable." `bbs-sales` is
force-enabled (`"bbs-sales@bbs-claude-marketplace": true`), so `fill-gate` keeps running.
Consequence recorded for `MANAGED-SETTINGS.md`: **taking `bbs-sales` out of managed
`enabledPlugins` while `allowManagedHooksOnly` is on silently turns every form script back
into a prompt.** Fail-safe (a prompt, not an unguarded run), but worth one line.

### 3.5 Path comparison, both twins

- Separators: `\` → `/`. Drive forms `C:/x`, `C:\x` and Git Bash `/c/x` compare equal;
  the drive letter is compared case-insensitively, the rest case-sensitively (a case
  mismatch means "no decision", never a wrong allow).
- Duplicate `/` collapse; a trailing `/` on the root is dropped.
- Lexical only: no `realpath` (PowerShell 5.1 has no portable link resolver). Instead the
  hook walks each component from the root down and refuses if any is a symlink
  (`os.path.islink`) or a reparse point (`[IO.FileAttributes]::ReparsePoint`). The root
  itself may sit under a link (macOS `/var` → `/private/var`); that does not matter
  because both strings come from the same Claude Code substitution.
- `ALLOWED` is parsed from `<root>/scripts/bbs-fill`: the lines between `ALLOWED=(` and the
  next `)`, one quoted entry per line, the exact rule `test_bbs_fill.py` already uses.
  Unparseable → no decision.

### 3.6 Failure modes, all fail to a prompt

| Situation | Result |
|---|---|
| No `pwsh`, `powershell` or `python3` | No decision: the normal flow prompts. No `systemMessage` (it would fire on every Bash call) |
| Hook times out or crashes, exit ≠ 0 or 2 | Non-blocking error; no decision → prompt |
| Plugin updated mid-session | Loading reference: "hook commands … keep using the previous version's path" until `/reload-plugins`. A skill loaded after the update carries the new path; word 0 no longer equals the hook's root → prompt. The old version folder survives 14 days ("removes that directory in a background cleanup 14 days later"), so nothing breaks |
| `allowManagedHooksOnly` on and `bbs-sales` not force-enabled | Hook blocked → prompt |
| Any parse doubt | No decision → prompt |

### 3.7 Cost on every Bash call

The entry starts with a `sh` pre-filter, the same shape #84 uses for `Read`, so an
interpreter starts only when the command can possibly match:

```sh
IN=$(cat); case "$IN" in *bbs-fill*) ;; *) exit 0 ;; esac; …interpreter chain as guard-tree, piping "$IN"…
```

The pre-filter only ever skips the hook, so a miss costs a prompt, never an allow.

### 3.8 Auto mode — the one thing the docs do not settle

The launcher exists because auto mode stopped Kim mid-packet (2026-10-01). The hooks
reference says `"allow"` "skips the permission prompt"; *Permission modes* says, of
`dontAsk`, that "calls approved by a PreToolUse hook run too". The auto-mode decision order
("How the classifier evaluates actions") lists allow, ask and deny **rules** in step 1 and
does not mention a hook `"allow"`. **I found no sentence saying a hook `"allow"` skips the
auto-mode classifier.** [FLAG: unverified — must be proven on a real machine in auto mode
before merge.] This is merge gate V1 (§6), confirmed by the steward 2026-11-11: Parker runs one real fill in auto mode from the branch before the implementation PR merges; if it fails, the slice stops and goes back to
Parker, and nothing has been removed yet.

## 4. Decision 3: retiring `bbs-tools`

In the implementation PR:

| File | Change |
|---|---|
| `.claude-plugin/marketplace.json` | Remove the `bbs-tools` entry; add top-level `"renames": {"bbs-tools": null}` (*Host a marketplace*, "Migrate users with a renames map": "Map each former name to its current name, or to `null` when the plugin is gone"; "Treat `renames` as append-only history"). **Do not** set `forceRemoveDeletedPlugins`: it changes uninstall behaviour for every plugin in the marketplace and is its own decision |
| `plugins/bbs-tools/` | Deleted. `test_bbs_fill.py` moves (§8) |
| `plugins/bbs-foundations/docs/bbs-managed-settings.json` | Remove `"bbs-tools@bbs-claude-marketplace": true` and `"Bash(bbs-fill *)"`. Takes effect only on Parker's re-paste, which is step 5 of §5 |
| `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` | `enabledPlugins` row drops `bbs-tools`; `permissions.allow` row: the R4 sentence becomes "the vetted form and quote scripts run through `bbs-sales/scripts/bbs-fill`, approved by `bbs-sales`' `fill-gate` hook (RULED 2026-11-11), not by a rule"; keep "**Never** `Bash(python:*)` or a path-pattern rule". New section "Form scripts: a hook, not a rule (2026-11-11)": §3.1, §3.3, §3.4's consequence, §3.8's gate. The "Business Central writes" and #84's "Desk memory notes" sections keep "on the `bbs-fill` allow list" (still true) and lose "`Bash(bbs-fill *)`" |
| `plugins/bbs-foundations/commands/bbs-checkup.md` | Check 1's list drops `bbs-tools`. Check 12 becomes: find `bbs-sales`' installed root, run `"<root>/scripts/bbs-fill"` with no arguments → `REFUSED — usage`, exit 64; confirm `/permissions` **Ask** lists `outlook_send_mail`; and, in a session, that one vetted no-op (`packet_profile.py --list`) ran without a prompt. WARN text no longer says "bbs-tools not installed" |
| `plugins/bbs-sales/skills/**` (every `bbs-fill` line above, plus #68 and #84's) | `bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/…"` → `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/…"`. The "if `bbs-fill` is not found, `bbs-tools` is missing" paragraphs become "if the launcher answers `REFUSED`, relay it; if the call stops for an Allow, say the form gate did not approve it and let the rep decide" |
| `plugins/bbs-sales/skills/ca-form-filler/references/packets/README.md` | Path to `ALLOWED` → `plugins/bbs-sales/scripts/bbs-fill` |
| `plugins/bbs-sales/skills/bc-item-entry/{SKILL.md,references/item-rules.md,references/rep-setup.md}` | "the interpreter `bbs-fill` runs" stays; any `bbs-tools` mention goes |
| `plugins/bbs-sales/README.md` | `bbs-tools` lines go; Hooks table gains `fill-gate.ps1` / `.py` |
| `plugins/bbs-sales/hooks/hooks.json` | New `PreToolUse` entry (§3.2, §3.7); description gains one sentence |
| `README.md`, `.claude-plugin/PLUGINS.md`, `docs/SYSTEM-OVERVIEW.md`, `docs/REP-SETUP.md` | Remove the `bbs-tools` install line, tree entry and table rows; plugin counts and README badges follow |
| `REGISTRY.md` | New row: `bbs-tools` plugin — **archived** — "Retired 2026-11-11 (RULED); launcher now `bbs-sales/scripts/bbs-fill`, gated by `fill-gate`" |
| `.github/workflows/check-marketplace.yml` | Launcher step points at the new test path; new step runs the hook tests with `BBS_REQUIRE_PS=1` |
| `docs/STEWARD.md` | Register entry for the 2026-11-11 ruling |

The bootstraps (`scripts/bbs-setup.ps1`, `scripts/bbs-setup.sh`) name no plugin: they
install every `marketplace.json` entry, so removing the entry is enough.

**Checker.** `scripts/check_marketplace.py` belongs to the review side (CLAUDE.md). This
slice does not edit it. A FAIL on a plugin with a top-level `bin/` directory, so this
failure is caught in CI rather than by org sync, is a review-side follow-up (steward,
2026-11-11), outside this slice.

## 5. Order of operations: never prompting, never blocked

Two facts drive the order:

- An old `bbs-sales` calls bare `bbs-fill`, which exists only while `bbs-tools` is enabled
  and runs unprompted only while `Bash(bbs-fill *)` is in managed settings.
- A new `bbs-sales` calls `<root>/scripts/bbs-fill`, which the old rule never matches
  (the command does not start with `bbs-fill`), so it relies on the hook alone.

| Step | Who | What | Rep state after |
|---|---|---|---|
| 0 | — | #68 and #84 on `main` (§7) | unchanged |
| 1 | worker → Rex | Build on the branch; CI green; review | unchanged |
| 2 | **Parker** | **Merge gate V1–V3** on his machine, plugin loaded from the branch (plan, task 11) | unchanged |
| 3 | Parker | Merge | unchanged until restart |
| 4 | reps | Restart Claude Code (`autoUpdate: true`): new `bbs-sales` with launcher + hook; `bbs-tools` reported "Removed from the … marketplace" but still loaded, because managed settings force-enable it ("Plugins that only managed settings installed stay in place"). The leftover rule and the leftover `bin/bbs-fill` are harmless | **no prompt** (hook); a stale session still has the old pair |
| 5 | **Parker** | `/bbs-checkup` on one rep machine passes check 12; **then** re-paste managed settings (drops `bbs-tools` from `enabledPlugins`, drops `Bash(bbs-fill *)`) and re-run org sync | no prompt; `bbs-tools` unloaded; org-sync error gone |

**Never the reverse.** Re-pasting before step 4 reaches a rep would take away the rule
**and** the force-enabled `bbs-tools` from a rep still on the old skills: every fill is a
`bbs-fill: command not found` (blocked), or a prompt where a bootstrap-installed copy
survives. Rollback before step 5 is a plain revert of the PR: managed settings are
untouched, so the old pair resumes.

## 6. Merge gates (verification on a real machine)

- **V1 — auto mode.** Auto mode on; ask for a packet profile listing
  (`packet_profile.py --list`) and one real fill on a test PDF. Pass: no prompt and no
  classifier denial. Fail: stop; report to Parker (§3.8). Nothing has been removed.
- **V2 — the hook does not over-allow.** In the same session, ask Claude to run
  `"<root>/scripts/bbs-fill" "<root>/skills/…/fill_obs_packet.py" x && echo hi`.
  Pass: a prompt. Then a Teams or Outlook send to Parker himself: Pass: an Allow prompt.
- **V3 — Windows.** One Windows rep machine (Git Bash, Windows PowerShell 5.1): the same
  fill runs without a prompt. Not provable in CI.

## 7. Sequencing with the open queue

- **#68** (`bc-quote-entry`) adds `bc-quote-entry/scripts/bc_quote_entry.py` to `ALLOWED`
  (R3) and bumps `bbs-tools` to 0.2.2.
- **#84** (desk memory slice 2) adds `desk-remember/scripts/desk_memory.py` (R7, A3), bumps
  `bbs-tools` to 0.2.3, and adds a launcher test (15/15).

Implementation starts only when both are merged to `main`. It then moves the launcher as it
stands on `main` at that moment, with both entries and #84's test, and repoints both skills'
lines. If either has been closed instead of merged, its entry is **not** carried (a script
goes on the list only by its own ruling and reviewed PR). #77 also edits
`bbs-sales/hooks/hooks.json`; whichever lands second merges `main` in, keeping both entries.

Versions (allocated by the steward, 2026-11-11): **`bbs-sales` 0.14.0, `bbs-foundations` 0.5.1.**

#68 also retires `bbs-quote-builder` and drops `build_quote.js` from `ALLOWED`
(Parker, 2026-11-11). The implementation takes `ALLOWED` from `main` as #68 left it and does
**not** re-add that entry.

## 8. Tests

**Launcher** — `plugins/bbs-sales/scripts/tests/test_bbs_fill.py`, ported from
`plugins/bbs-tools/tests/test_bbs_fill.py`: every existing test kept; the fake cache becomes
`<tmp>/cache/<market>/bbs-sales/<ver>/{scripts/bbs-fill,skills/…}`; the skill-line regex
becomes `"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/bbs-fill" "\$\{CLAUDE_PLUGIN_ROOT\}/skills/([^"<]+)"`.
New: a vetted script from **another version folder** of `bbs-sales` is refused; the launcher
file is mode `100755` in git; **no skill or reference still writes a bare `bbs-fill "`**;
no plugin in `plugins/` has a top-level `bin/`.

**Hook** — `plugins/bbs-sales/hooks/tests/fill_gate_parity.py` plus cases in
`run-tests.ps1`, one shared case file `hooks/tests/fill_gate_cases.json`
(`{command, env, expect: "allow"|"none", why}`), run through both twins; decision **and**
reason string must agree; `BBS_REQUIRE_PS=1` in CI. Each case builds a fake root with real
files. Cases, at minimum:

| Must give **no decision** (normal flow) | Why |
|---|---|
| `<L> <S> a; rm -rf x` · `<L> <S> && echo` · `<L> <S> \| tee` · `<L> <S> &` · `<L> <S> \|\| x` | compound / background |
| `<L> <S> > out` · `<L> <S> 2>&1` · `<L> <S> < in` · `<L> <S> <<EOF` | redirects |
| `<L> <S> $(id)` · `` <L> <S> `id` `` · `<L> <S> "$(id)"` · `<L> <S> "$HOME"` · `<L> <S> ${X}` · `<L> <S> <(x)` | substitution, expansion |
| `(<L> <S>)` · `{ <L> <S>; }` · `<L> <S> {a,b}` · `<L> <S> *.pdf` · `<L> <S> ~/x` · `<L> <S> #c` | subshell, groups, brace, glob, tilde, comment |
| `<L> <S> a\nrm x` · `\r` · `\t` · NUL · U+2028 · unterminated `'` or `"` | control characters, bad quoting |
| `PYTHONPATH=/x <L> <S>` · `LD_PRELOAD=x <L> <S>` · `BASH_ENV=x <L> <S>` · `env X=1 <L> <S>` · `exec <L> <S>` · `bash <L> <S>` · `command <L> <S>` | env injection, wrappers |
| `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" <S>` | unexpanded variable (would be `/scripts/bbs-fill`) |
| `/other/bbs-sales/9.9.9/scripts/bbs-fill <S>` · launcher of another version · `<L>x <S>` | launcher outside this root |
| `<L> <root>/skills/ca-form-filler/scripts/test_fill_obs_packet.py` · `<L> /tmp/fill_obs_packet.py` · `<L> <root>/skills/../skills/…` · `<L>` alone · `<L> -c x` | script not vetted, not here, `..`, missing, an option |
| `<L> <S>` where a skill folder on the way is a symlink | link below root |
| `dangerouslyDisableSandbox: true` · `tool_name: PowerShell` · no `CLAUDE_PLUGIN_ROOT` · stdin not JSON | outside scope |

| Must **allow** | Note |
|---|---|
| `"<L>" "<S>" in.pdf inputs.json out.pdf` | the skill form |
| `'<L>' '<S>' --inspect 'Packet B (2026).pdf'` | single quotes, spaces in an argument |
| `<L> <S> --validate` | unquoted |
| `"<L>" "<S>" "C:\Users\rep\Desktop\out.pdf"` and the Windows root forms `C:\…`, `C:/…`, `/c/…` | Windows |
| `"<L>" "<S>" -c "import os"` | arguments are data; the launcher passes them to the script, never to the interpreter |
| `"<L>" "<S>" ""` | empty argument |

**Differential check against real bash** (Python test, Linux and macOS CI): for every case
the hook allows, run the command in `bash` with word 0 replaced by a stub that prints its
argv NUL-separated, under `set -f`; the argv must equal the hook's own word list. Then a
bounded fuzz (fixed seed, a few thousand strings over an alphabet of quotes, `\`, `$`, `;`,
`&`, `|`, spaces, newline, `*`, letters and the two paths): whenever the hook allows, bash's
argv must equal the hook's and word 0 must be the launcher. This is what "real shell
tokenising" means here: the hook implements a subset, and the test proves bash agrees on
every string the hook accepts.

**What the hook allows**, printed by the parity test as a table at the end of each run
(case, decision, reason), so a reviewer sees the allow set without reading code.

## 9. Not in this slice

- Whether `forceRemoveDeletedPlugins` should be set marketplace-wide.
- Any change to what is on `ALLOWED`.
- Cowork / claude.ai Chat behaviour of the form skills: hooks and the Bash tool there are
  not verified by this design; the slice only makes `bbs-sales` installable there.
- The checker change (a review-side follow-up, §4).

## Docs read 2026-11-11

- Hooks reference — `code.claude.com/docs/en/hooks` ("Hook locations",
  `allowManagedHooksOnly` bullets; PreToolUse decision control; precedence
  `deny` > `defer` > `ask` > `allow`; exit-code semantics).
- Configure permissions — `code.claude.com/docs/en/permissions` ("Wildcard patterns";
  "Compound commands"; "Precedence among rules, hooks, and mods").
- Permission modes — `code.claude.com/docs/en/permission-modes` ("How the classifier
  evaluates actions"; `dontAsk`; what no hook can approve).
- Settings reference — `code.claude.com/docs/en/settings-reference` (`allowManagedHooksOnly`).
- Plugins reference — `code.claude.com/docs/en/plugins-reference` (directory table, `bin/`;
  "Where each variable resolves").
- Plugin components — `code.claude.com/docs/en/plugins/components` (`bin/`).
- Plugin loading — `code.claude.com/docs/en/plugins/loading` ("Cleanup of previous
  versions"; hooks keep the previous version's path until `/reload-plugins`).
- Host a marketplace — `code.claude.com/docs/en/plugins/host-marketplace` ("Distribute
  through organization settings", top-level `bin/`; "Migrate users with a renames map";
  "Uninstall removed plugins").
- Marketplace reference — `code.claude.com/docs/en/plugins/marketplace-reference`
  (`renames`).

---

Owner: Parker Marshall. Written 2026-11-11 for review by Rex before any build.
