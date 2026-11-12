# Move `bbs-fill` into `bbs-sales`, replace the PATH-name allow rule with a hook, retire `bbs-tools`

Status: **design, revised after Rex's review of 8eff944 (HELD, 2026-11-11).** Nothing here
is built. The work ships as **two PRs** (§5): PR A moves the launcher and adds the hook;
PR B retires `bbs-tools`, and opens only after check 12 passes on a rep machine. PR A
waits for #68 and #84 to be on `main` (§7). Versions live in the plan only.

**RULED 2026-11-11.** Parker, in session: "Yes … to the tools fix as a separate slice",
approving the steward's proposal to move the `bbs-fill` launcher out of `bbs-tools`'
top-level `bin/` into `bbs-sales`, replace the PATH-name allow rule with a vetted-command
PreToolUse hook, and retire `bbs-tools`. Splitting the work into two PRs is sequencing
inside that ruling, not a new one (Rex, review of 8eff944). The register entry in
`docs/STEWARD.md` lands with PR A (plan, task 9).

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
  settings."

There is no documented stable path from one plugin to another plugin's files: the
reference documents `${CLAUDE_PLUGIN_ROOT}` as "Absolute path of the plugin's installed
version", for that plugin only, and says it "changes when the plugin updates". So the
launcher must live in the plugin whose scripts it runs. That plugin is `bbs-sales`, the
only consumer:

| Skill | Scripts on `ALLOWED` after #68 and #84 |
|---|---|
| `ca-form-filler` | `fill_obs_packet.py`, `fill_packet_c.py`, `packet_profile.py`, `render_pages.py` |
| `naspo-quote` | `fill_ca_forms.py`, `inspect_form.py` |
| `sam-gov-opportunities` | `sam_opportunities.py` |
| `usaspending-awards` | `usaspending_awards.py` |
| `bc-item-entry` | `bc_item_entry.py` |
| `bc-quote-entry` (#68) | `bc_quote_entry.py` (R3) |
| `desk-remember` (#84) | `desk_memory.py` (R7, A3) |
| ~~`bbs-quote-builder`~~ | ~~`build_quote.js`~~: **not carried.** #68 deletes the skill and the entry (Parker, 2026-11-11). #84's branch still lists it, so whichever of the two merges second must not re-add it; plan task 1.3 checks. The launcher's `.js` → `node` branch stays, unused |

## 2. Decision 1: where the launcher goes (PR A)

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
`${CLAUDE_PLUGIN_ROOT}` would expand to an empty string and point at `/scripts/bbs-fill`;
the hook refuses any `$` (§3.2), so that never auto-runs.

**Line endings.** `.gitattributes` today gives LF only to `*.sh`, and Git for Windows
defaults to `core.autocrlf=true`, which would check the launcher out as
`#!/bin/bash -p\r` and break it. PR A adds `plugins/bbs-sales/scripts/bbs-fill text eol=lf`.

Every guarantee the launcher gives today is kept, unchanged unless stated:

| Guarantee | Today (`bbs-tools/bin/bbs-fill`) | After |
|---|---|---|
| `ALLOWED` list, by `<skill>/scripts/<file>` | yes | **the list on `main` after #68 and #84** (§1). Stays the single home of the list: the hook reads it from the launcher (§3.5), never a copy |
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

**Known limit, unchanged in kind.** From a repo checkout or a `--plugin-dir` copy,
`<root>/../../..` is two folders above the checkout, so the launcher refuses arguments
anywhere under it. Tests use the fake-cache layout; V1 keeps its test PDFs outside that
folder (§6).

**Not fixed here.** Neither the launcher nor `guard-tree` stops a fill whose output
argument is `…/FILLED/x.pdf`; `guard-tree.py` looks for `rm`/`del`, redirects,
`tee`/`Set-Content` and copies into `FILLED/`, not for a script's output argument. The gap
exists today. Follow-up, separate PR (plan, "Follow-ups"): the launcher refuses output
paths under `FILLED/`.

## 3. Decision 2: how it runs without a prompt (PR A)

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
returns `deny` or `ask`: refusing is the launcher's job.

1. `tool_name` is `Bash`, `tool_input.command` is a string, and
   `tool_input.dangerouslyDisableSandbox` is absent or false.
2. `CLAUDE_PLUGIN_ROOT` is set in the hook's environment (the plugins reference: hook
   commands get `CLAUDE_PLUGIN_ROOT` "Exported to the process").
3. The command is **one simple command** under a deny-by-default lexer that accepts a strict
   subset of word syntax shared by `bash` and `zsh` (the Bash tool runs `zsh` on macOS reps),
   and nothing else. The lexer works on **code points**, never on UTF-16 units: the
   PowerShell twin decodes surrogate pairs with `[char]::ConvertToUtf32`, and a lone
   surrogate rejects the command.
   - Words are separated by runs of U+0020 spaces. Nothing else separates.
   - A word is a concatenation of three kinds of run:
     - **unquoted**: ASCII only, `[A-Za-z0-9_./:,=+@%-]`, and **not starting the word with
       `=`** (zsh's EQUALS expansion turns `=name` into a command path);
     - **single-quoted** `'…'`: any code point except `'` and the forbidden set below;
     - **double-quoted** `"…"`: any code point except `"`, `$`, `` ` ``, `!` and the
       forbidden set, where `\` is allowed only when the next character is none of `$`,
       `` ` ``, `"`, `\` (so `"C:\Users\kim\…"` is literal, as in bash and zsh).
   - Non-ASCII text is accepted **only inside quotes**. That keeps both twins off Unicode
     category tables, which differ between Python and .NET versions, and it is what the
     skills write anyway. Non-BMP letters and macOS NFD file names (combining marks) are
     fine quoted; unquoted they give no decision.
   - The forbidden set, anywhere, quoted or not: every Unicode `Cc` code point (C0 controls
     including newline, CR, tab and NUL; DEL; C1 controls including U+0085) and U+2028,
     U+2029. `Cc` is a fixed range in every Unicode version.
   - **Anything else rejects the whole command**: `;` `&` `|` `<` `>` `(` `)` `{` `}`, `$`
     anywhere, backtick anywhere, unquoted `\`, unquoted `*` `?` `[` `]` `~` `#` `!` `^`,
     an unquoted word-initial `=`, an unterminated quote, an empty command.
   - This rejects compound commands, pipes, background `&`, redirects, subshells, command
     and process substitution, parameter and arithmetic expansion, brace, tilde and EQUALS
     expansion, globs, comments and history expansion, by construction.
4. **Word 0 is the launcher.** After quote removal, word 0, normalised (§3.5), equals
   `<CLAUDE_PLUGIN_ROOT>/scripts/bbs-fill`. Word 0 may be built from several runs
   (`"<root>/scripts/"bbs-fill`): what counts is the word after quote removal, the same
   word the shell executes. A leading `VAR=value` assignment, `env`, `exec`, `command`,
   `bash`, `sh`, `nohup`, `time` or anything else in front fails this.
5. **Word 1 is a vetted script** of this root: normalised, it equals
   `<CLAUDE_PLUGIN_ROOT>/skills/<a>` for some `<a>` on the launcher's `ALLOWED` list.
6. Neither path has a `.` or `..` segment, and **no path component from the root itself
   down to the launcher or the script is a symlink or reparse point**: the walk includes
   the root, matching the launcher's "plugin root may not be a link" (§3.5).

Arguments after word 1 are not inspected: they are data, and the launcher checks them (dot
folders, cache, `..`) before it runs anything. A command the hook allows is therefore a
command the launcher would also have allowed, given the same root.

**Assumption, stated.** No other PreToolUse hook on a rep machine returns `updatedInput`
for Bash. How Claude Code combines one hook's `allow` with another hook's rewritten input
is not documented. `git grep updatedInput plugins` is empty today; the pinned third-party
plugins (commons, `claudeforge`, `impeccable`) are not checked. Plan task 5.4 adds the grep
to the hook tests so a local plugin that starts doing it fails CI.

**Assumption, stated: the rep's shell setup.** The hook sees the command text, not the
rep's shell configuration. A zsh global alias, or an option such as `RC_QUOTES` or
`MAGIC_EQUAL_SUBST`, can change how a word is read. That needs a prior write to the rep's
`~/.zshrc`, and today's `Bash(bbs-fill *)` rule has the same exposure. The differential
test (§8) runs `zsh -f`, which skips the user's startup files, so it checks the default
grammar the hook models.

### 3.3 Precedence: the hook cannot weaken a managed control

*Configure permissions*, "Precedence among rules, hooks, and mods": "PreToolUse hook
decisions don't bypass permission rules. Claude Code evaluates deny and ask rules regardless
of what a PreToolUse hook returns: a matching deny rule blocks the call, and a matching ask
rule still prompts even when the hook returned `"allow"` … including deny rules set in
managed settings." The hooks reference, PreToolUse decision control: "Deny and ask rules
are still evaluated regardless of what the hook returns", and "When multiple PreToolUse
hooks return different decisions, precedence is `deny` > `defer` > `ask` > `allow`."
In plan mode a hook `allow` has no effect on a call that is not read-only (permissions,
"Hook approvals in plan mode").

So:

- **Send controls stay intact.** The Outlook and Teams send-class tools are MCP tools in
  `permissions.ask`; SignNow / QuickBooks sends and `outlook_send_draft` are in
  `permissions.deny`. The hook's matcher is `Bash` only; it never sees those calls.
- **The managed Bash denies and asks stand** (`rm -rf`, `git push --force`,
  `git reset --hard`, `gh pr merge`, `git push`, `gh pr create` …). A single launcher
  invocation cannot contain them anyway (§3.2.3–4).
- **Another hook's `deny` still wins** over our `allow`, by the precedence above.
  (`guard-tree` does not cover fill output into `FILLED/`; see §2, "Not fixed here".)
- **What no hook can approve stays unapprovable**: critical-path `rm`, network-path reads
  (*Permission modes*, "An allow rule or `PreToolUse` hook can't approve these").

### 3.4 `allowManagedHooksOnly`, and which copy of `bbs-sales` loads

**`allowManagedHooksOnly`.** Not set in `bbs-managed-settings.json` today. If Parker sets
it, plugin hooks stop, with one exemption. Hooks reference, "Hook locations": "Your user,
project, local, and plugin hooks are blocked. Hooks from plugins force-enabled in managed
settings `enabledPlugins` are exempt"; settings reference, `allowManagedHooksOnly`: "only
managed hooks run, plus Agent SDK hooks and hooks from plugins your managed settings
force-enable." `bbs-sales` is force-enabled, so `fill-gate` keeps running. For
`MANAGED-SETTINGS.md`: **taking `bbs-sales` out of managed `enabledPlugins` while
`allowManagedHooksOnly` is on turns every form script back into a prompt.**

**Org-synced and managed copies.** The docs settle this. *Plugin loading*, "Name
conflicts": a plugin named in managed `enabledPlugins` has the highest precedence, and a
plugin synced from claude.ai has the lowest: "When an enabled plugin from any other origin
matches its name, Claude Code loads that plugin and reports the synced copy as not loaded."
The org-rollout page says the same: "Claude Code loads one plugin per name. It loads the
copy that managed settings install and reports the synced copy as not loaded." So once PR A
makes `bbs-sales` syncable, `bbs-sales@synced` never loads on a rep machine while managed
settings name `bbs-sales`. If `bbs-sales` ever left managed `enabledPlugins`, the synced
copy would load from `~/.claude/plugins/synced/` with its own hook and its own root; the
launcher's `<root>/../../..` would then be `~/.claude/plugins` or `~/.claude`, both still
forbidden argument locations. Safe either way.

**Why V1 cannot use `--plugin-dir` on the real name.** The same rule 1 says: "A
`--plugin-dir` copy whose manifest name matches the id's name part isn't loaded, and you
see `--plugin-dir copy of "<name>" ignored: plugin is locked by managed settings`". §6
uses a renamed test copy for that reason.

### 3.5 Path comparison and `ALLOWED` parsing, both twins

- Separators: `\` → `/`. Drive forms `C:/x`, `C:\x` and Git Bash `/c/x` compare equal; the
  drive letter is compared case-insensitively, everything else case-sensitively and by exact
  code points (no Unicode normalisation). A case or normalisation mismatch between the root
  and word 0 means "no decision", never a wrong allow. On macOS a case-differing root is
  therefore a prompt; Claude Code substitutes the same string it exports, so this should not
  happen in practice, and a test pins the outcome.
- Duplicate `/` collapse; a trailing `/` on the root is dropped. A root containing spaces or
  non-ASCII is fine: the skills quote the path, and §3.2 accepts any non-forbidden code point
  inside quotes.
- Lexical only: no `realpath` (PowerShell 5.1 has no portable link resolver). Instead the
  hook walks each component **from the root itself** down and refuses if any is a symlink
  (`os.path.islink`) or a reparse point (`[IO.FileAttributes]::ReparsePoint`). A link
  *above* the root (macOS `/var` → `/private/var`) does not matter: both strings come from
  the same Claude Code substitution.
- `ALLOWED` is read from `<root>/scripts/bbs-fill`: the lines between `ALLOWED=(` and the
  next `)`. Each entry must match `^"[a-z0-9-]+/scripts/[A-Za-z0-9_.-]+\.(py|js)"$` exactly.
  **Any CR in the file, or any entry that does not match, means no decision for every
  command**: a damaged list fails to a prompt, loudly, rather than being half-read.

### 3.6 Failure modes, all fail to a prompt

| Situation | Result |
|---|---|
| No `pwsh`, `powershell` or `python3` | No decision: the normal flow prompts. No `systemMessage` (it would fire on every Bash call) |
| Hook times out or crashes, exit ≠ 0 or 2 | Non-blocking error; no decision → prompt |
| Plugin updated mid-session | *Plugin loading*: hook commands "keep using the previous version's path" until `/reload-plugins`. A skill loaded after the update carries the new path; word 0 no longer equals the hook's root → prompt. The old version folder survives 14 days |
| `allowManagedHooksOnly` on and `bbs-sales` not force-enabled | Hook blocked → prompt |
| Launcher has CRLF line endings, or an `ALLOWED` entry is malformed | No decision → prompt (and the launcher itself would fail) |
| Any parse doubt | No decision → prompt |
| Windows: Git Bash cannot execute a `C:\…` word 0 | **Not a prompt: `command not found`, a block.** V3 must prove this does not happen (§6) |

### 3.7 Cost on every Bash call

The entry starts with a `sh` pre-filter, the shape #84 uses for `Read`, so an interpreter
starts only when the command can possibly match:

```sh
IN=$(cat); case "$IN" in *bbs-fill*) ;; *) exit 0 ;; esac; …interpreter chain as guard-tree, piping "$IN"…
```

The pre-filter only ever skips the hook, so a miss costs a prompt, never an allow.

### 3.8 Auto mode: what the docs do not settle

The launcher exists because auto mode stopped Kim mid-packet (2026-10-01), and with Claude
Code v2.1.283 or later auto mode is the built-in starting mode (*Permission modes*), so
every rep is on this path. The hooks reference says `"allow"` "skips the permission
prompt"; *Permission modes* says, of `dontAsk`, that "calls approved by a PreToolUse hook
run too". The auto-mode decision order ("How the classifier evaluates actions") lists
allow, ask and deny **rules** in step 1 and does not mention a hook `"allow"`. And under
"Server-side classifier review" the server reviews actions as part of the model response,
before hooks run; whether a server verdict outranks a hook `allow` is not stated.
**[FLAG: unverified.]** This is merge gate V1 (§6), run on both review paths.

Recorded for `MANAGED-SETTINGS.md`: **form scripts run without a prompt because of
behaviour the docs do not state.** A Claude Code update can bring the prompts back. That
fails safe (a prompt, not an unvetted run), but it fails, and check 12's auto-mode line is
how we would notice.

### 3.9 What a skill does when the call still prompts

The "if `bbs-fill` is not found, `bbs-tools` is missing" paragraphs are replaced with:

> If the launcher answers `REFUSED`, relay its reason to the rep and stop. If an Allow
> prompt appears for a form script, **do not ask the rep to approve it.** Re-issue it once
> as exactly `"<launcher>" "<script>" <args>`, with nothing before or after it. If it
> prompts again, stop, and tell the rep to run `/bbs-checkup` and send the result to
> Parker.

The hook never denies, so a prompt means the command was not the vetted form, and a click
would run whatever it was. Invariant 4: fail loudly on a binding document.

**The rep's No is the control.** In Manual mode the permission prompt reaches the rep first,
and Claude gets control back only after the rep answers, so the instruction above covers
only what happens after that answer (or after an auto-mode denial). Every rep-facing text in
this slice (the PR A body, the check 12 WARN, Parker's note to the team) therefore says,
exactly: "If Claude Code asks you to Allow a `bbs-fill` command, choose **No**, then run `/bbs-checkup` and send the result to Parker."

## 4. Decision 3: what each PR changes

### PR A: launcher, hook, skill repoint (`bbs-tools` stays)

`bbs-tools` stays in `marketplace.json` and in managed settings. Org sync already skips it,
so keeping it costs nothing, and its old launcher keeps serving any session still on old
skills.

| File | Change |
|---|---|
| `plugins/bbs-sales/scripts/bbs-fill` | New: the launcher (§2). `plugins/bbs-tools/bin/bbs-fill` is **left in place, unchanged**, until PR B |
| `.gitattributes` | `plugins/bbs-sales/scripts/bbs-fill text eol=lf` |
| `plugins/bbs-sales/hooks/fill-gate.{py,ps1}`, `hooks/hooks.json` | New hook and its `PreToolUse` entry (§3.2, §3.7); the `hooks.json` description gains one sentence |
| `plugins/bbs-sales/skills/**` (every `bbs-fill` line, including #68's and #84's) | `bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/…"` → `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/…"`; fallback paragraphs → §3.9 wording |
| `plugins/bbs-sales/skills/ca-form-filler/references/packets/README.md` | Path to `ALLOWED` → `plugins/bbs-sales/scripts/bbs-fill` |
| `plugins/bbs-sales/skills/bc-item-entry/{SKILL.md,references/item-rules.md,references/rep-setup.md}` | "the interpreter `bbs-fill` runs" stays; `bbs-tools` mentions go |
| `plugins/bbs-sales/README.md` | `bbs-tools` lines go; Hooks table gains `fill-gate.ps1` / `.py` |
| `plugins/bbs-foundations/commands/bbs-checkup.md` | Check 12 (below) |
| `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` | New section "Form scripts: a hook, not a rule (2026-11-11)": §3.1, §3.3, §3.4 (both paragraphs), §3.8's dependency sentence, and "`Bash(bbs-fill *)` and `bbs-tools` stay until PR B". The `permissions.allow` row points at it |
| `.github/workflows/check-marketplace.yml` | New launcher test path; hook parity with `BBS_REQUIRE_PS=1`; a macOS job for the hook tests (§8) |
| `docs/STEWARD.md` | Register entry for the 2026-11-11 ruling |

**Check 12, new text (PR A).** Find `bbs-sales`' installed root from `/plugin`; run
`"<root>/scripts/bbs-fill"` with no arguments and expect `REFUSED — usage`, exit 64.
Confirm `/permissions` **Ask** lists `outlook_send_mail`. Then **the auto-mode line**:
confirm the session is in auto mode (or say which mode it is in), run
`"<root>/scripts/bbs-fill" "<root>/skills/ca-form-filler/scripts/packet_profile.py" --list`
and report whether it ran without a prompt and without an auto-mode denial. PASS = all
three. WARN names the failed part and then says, exactly: "If Claude Code asks you to Allow a `bbs-fill` command, choose **No**, then run `/bbs-checkup` and send the result to Parker." While `bbs-tools` is still installed (between PR A and PR B), `command -v bbs-fill`
resolving is expected and is not a failure.

### PR B: retire `bbs-tools` (opens only after check 12 passes on a rep machine)

| File | Change |
|---|---|
| `.claude-plugin/marketplace.json` | Remove the `bbs-tools` entry; add top-level `"renames": {"bbs-tools": null}`. Do not set `forceRemoveDeletedPlugins` (§5) |
| `plugins/bbs-tools/` | Deleted |
| `plugins/bbs-foundations/docs/bbs-managed-settings.json` | Remove `"bbs-tools@bbs-claude-marketplace": true` and `"Bash(bbs-fill *)"`. Takes effect on Parker's re-paste |
| `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md` | `enabledPlugins` row drops `bbs-tools`; the R4 sentence in `permissions.allow` becomes a pointer to the PR A section; keep "**Never** `Bash(python:*)` or a path-pattern rule". "Business Central writes" and "Desk memory notes" keep "on the `bbs-fill` allow list" and lose "`Bash(bbs-fill *)`" |
| `plugins/bbs-foundations/commands/bbs-checkup.md` | Check 1 drops `bbs-tools`; check 12 drops the "`bbs-fill` on PATH is expected" sentence |
| `README.md`, `.claude-plugin/PLUGINS.md`, `docs/SYSTEM-OVERVIEW.md`, `docs/REP-SETUP.md` | Remove the `bbs-tools` install line, tree entry and table rows; plugin counts and badges follow |
| `REGISTRY.md` | New row: `bbs-tools` plugin, **archived**, "Retired (RULED 2026-11-11); launcher now `bbs-sales/scripts/bbs-fill`, gated by `fill-gate`" |
| `.github/workflows/check-marketplace.yml` | Old launcher test step removed |

The bootstraps (`scripts/bbs-setup.ps1`, `scripts/bbs-setup.sh`) name no plugin; they
install every `marketplace.json` entry, so removing the entry is enough.

**Checker.** `scripts/check_marketplace.py` belongs to the review side (CLAUDE.md). A FAIL
on a plugin with a top-level `bin/` is a review-side follow-up (steward, 2026-11-11),
outside this slice.

## 5. Order of operations: never prompting, never blocked

| Step | Who | What | Rep state after |
|---|---|---|---|
| 0 | — | #68 and #84 on `main` (§7) | unchanged |
| 1 | worker → Rex | Build PR A; CI green; review | unchanged |
| 2 | **Parker** | **Merge gates V1–V3** (§6) | unchanged |
| 3 | Parker | Merge PR A | unchanged until restart |
| 4 | reps | Restart (`autoUpdate: true`): new `bbs-sales` with launcher and hook; `bbs-tools` and `Bash(bbs-fill *)` untouched | **no prompt** via the hook; any stale session still has the old pair, which still works |
| 5 | Parker / one rep | `/bbs-checkup` passes check 12 on a rep machine, and `/plugin` shows the new `bbs-sales` version there | unchanged |
| 6 | worker → Rex → Parker | Build, review and merge PR B | — |
| 7 | reps | Restart: `bbs-tools` gone from the marketplace | see below |
| 8 | **Parker** | Re-paste managed settings (drops `bbs-tools` from `enabledPlugins`, drops `Bash(bbs-fill *)`); re-run org sync | `bbs-tools` gone; org-sync error gone |

**What steps 7–8 do, from the docs, and what they do not say.** *Host a marketplace*,
"Migrate users with a renames map": for a `null` entry "the old key is dropped from those
scopes [user, project, local] and the user sees `Removed from the "your-marketplace"
marketplace`", and for a plugin still enabled in managed settings "the notice recurs until
an admin updates `enabledPlugins` there". **Whether a managed-enabled plugin removed with
`renames: null` stays loaded is not stated.** [FLAG: unverified.] It does not matter any
more: by step 7 every rep has run the new skills since step 4, and nothing calls bare
`bbs-fill`. (The sentence "Plugins that only managed settings installed stay in place"
belongs to `forceRemoveDeletedPlugins`, a different mechanism this slice does not use; the
earlier draft misquoted it.)

**Tell reps, after PR A (Parker's note to the team):** "If Claude Code asks you to Allow a `bbs-fill` command, choose **No**, then run `/bbs-checkup` and send the result to Parker."

**Tell reps, after PR B (PR B body and Parker's note to the team):** between step 7 and step 8 a
recurring "bbs-tools removed from the marketplace" notice is expected. It is harmless and
stops after Parker re-pastes.

**Never re-paste before step 5.** A rep still on old skills would lose the rule and the
force-enabled `bbs-tools` together: every fill would be `bbs-fill: command not found`.
Until step 8, rollback of either PR is a plain revert.

## 6. Merge gates for PR A (verification on a real machine)

**V1: auto mode, both review paths, the real workload.** On Parker's managed machine:

1. Make a test copy of the PR A branch's `plugins/bbs-sales` whose manifest `name` is
   changed to `bbs-sales-v1`, and start `claude --debug --plugin-dir <copy>`. (A copy named
   `bbs-sales` is not loaded: it is "locked by managed settings", §3.4.)
2. Record the Claude Code version and what `/status` shows for "Auto mode server".
3. Use a **blank test packet**, kept **outside** the copy's grandparent folder (§2, "Known
   limit"). Write every output to a scratch folder and discard it afterwards: a signed
   Packet B from a test run must not end up in a customer folder.
4. In auto mode, run the whole Packet B sequence that stopped Kim, through the copy's
   `bbs-sales-v1:ca-form-filler` skill: profile recognition, fill, render.
5. Run it twice: once with server review as the session has it, once with
   `CLAUDE_CODE_AUTO_MODE_SERVER=0` (*Permission modes*, "Server-side classifier review"),
   both started with `--debug-file <scratch>/v1-<run>.log`.

On **both** runs, for every script call:
- the executed command is `"<the copy's root>/scripts/bbs-fill" "<the copy's root>/skills/…"`;
- the debug log shows fill-gate's reason `bbs-fill: vetted script …` (hooks reference: for
  `"allow"` the reason is "written to the debug log only");
- no prompt and no denial.

**The `CLAUDE_CODE_AUTO_MODE_SERVER=0` run proves the hook skips review.** *Permission
modes*, "Check which model the classifier used": with `--debug-file`, every local classifier
review writes `classifier_request_started` to the log.
- **Positive control first:** in the same session, have Claude run `curl https://example.com`
  and confirm the log gains a `classifier_request_started` line. This proves the log would
  show a review. Per the same section: no permission rule may match `curl`, and if no line
  appears, `/status` must read `Auto mode server: Disabled` and the check is rerun with the
  sandbox off.
- **Pass** only if **no `classifier_request_started` line belongs to any fill call**: there
  is no classifier or server verdict for that call at all, not merely none that denied it.
  A classifier that reviewed and approved a harmless fill is a **fail**: reps would be back
  to auto mode stopping a packet mid-run.

**The server-review run can show less.** There the server reviews inside the model
response, before hooks run, so no log line can show a review skipped. Record each fill
call's outcome; pass is no prompt and no denial across the full sequence. The V1 record
says plainly that this run proves only that, and **Parker accepts that limit** when he
ticks V1.

Fail on either run: stop and report to Parker (§3.8). Nothing has been removed.

**V2: the hook does not over-allow.** In **Manual** mode (`/permissions` mode `default`),
same test copy: ask Claude to run
`"<root>/scripts/bbs-fill" "<root>/skills/ca-form-filler/scripts/packet_profile.py" --list && echo hi`.
Pass: a prompt, and the debug log shows no fill-gate decision for it. Decline the prompt.
No Outlook or Teams send is part of V2: the hook's matcher is `Bash`, so a send tests
nothing here and a mis-click sends real mail.

**V3: Windows.** One Windows rep machine (Git Bash, Windows PowerShell 5.1), same test-copy
method. Record the exact `${CLAUDE_PLUGIN_ROOT}` string Claude Code substitutes (the docs do
not give the slash form). Confirm Git Bash executes `"C:\…\scripts\bbs-fill"` (or whatever
form is substituted) as word 0, and the fill runs without a prompt. If Git Bash cannot run
that form the result is a block, not a prompt (§3.6), and PR A does not merge.

## 7. Sequencing with the open queue

- **#68** (`bc-quote-entry`) adds `bc-quote-entry/scripts/bc_quote_entry.py` (R3) and
  removes `bbs-quote-builder/scripts/build_quote.js`.
- **#84** (desk memory slice 2) adds `desk-remember/scripts/desk_memory.py` (R7, A3) and a
  launcher test; its branch still lists `build_quote.js`.

PR A starts only when both are merged to `main`. It moves the launcher as it stands on
`main` then, with both entries, #84's test, and without `build_quote.js`. If either PR has
been closed instead of merged, its entry is **not** carried. #77 is merged; there is no
`hooks.json` coordination left.

**Versions** are in the plan (task 11) only.

## 8. Tests (PR A)

**Launcher**: `plugins/bbs-sales/scripts/tests/test_bbs_fill.py`, ported from
`plugins/bbs-tools/tests/test_bbs_fill.py`: every existing test kept; the fake cache becomes
`<tmp>/cache/<market>/bbs-sales/<ver>/{scripts/bbs-fill,skills/…}`; the skill-line regex
becomes `"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/bbs-fill" "\$\{CLAUDE_PLUGIN_ROOT\}/skills/([^"<]+)"`.
New: a vetted script from **another version folder** of `bbs-sales` is refused; the launcher
is mode `100755` in git and contains no CR; `.gitattributes` carries the `eol=lf` rule; **no
skill or reference still writes a bare `bbs-fill "`**.

**Hook**: `plugins/bbs-sales/hooks/tests/fill_gate_parity.py` plus cases in
`run-tests.ps1`, one shared case file `hooks/tests/fill_gate_cases.json`
(`{command, env, setup, expect: "allow"|"none", why}`), run through both twins; decision
**and** reason string must agree; `BBS_REQUIRE_PS=1` in CI. Each case builds a fake root
with real files. Cases, at minimum (`<L>` launcher, `<S>` a vetted script, both quoted
unless shown otherwise):

| Must give **no decision** (normal flow) | Why |
|---|---|
| `<L> <S> a; rm -rf x` · `<L> <S> && echo` · `<L> <S> \| tee` · `<L> <S> &` · `<L> <S> \|\| x` | compound / background |
| `<L> <S> > out` · `<L> <S> 2>&1` · `<L> <S> < in` · `<L> <S> <<EOF` | redirects |
| `<L> <S> $(id)` · `` <L> <S> `id` `` · `<L> <S> "$(id)"` · `<L> <S> "$HOME"` · `<L> <S> ${X}` · `<L> <S> <(x)` | substitution, expansion |
| `(<L> <S>)` · `{ <L> <S>; }` · `<L> <S> {a,b}` · `<L> <S> *.pdf` · `<L> <S> ~/x` · `<L> <S> #c` | subshell, groups, brace, glob, tilde, comment |
| `<L> <S> =ls` · `=bash <S>` | zsh EQUALS (unquoted word-initial `=`) |
| `<L> <S> a\nrm x` · `\r` · `\t` · NUL · U+0085 · U+2028 · lone surrogate · unterminated `'` or `"` | forbidden code points, bad quoting |
| `<L> <S> café.pdf` · `<L> <S>` + non-BMP letter, unquoted | non-ASCII unquoted |
| `PYTHONPATH=/x <L> <S>` · `LD_PRELOAD=x <L> <S>` · `BASH_ENV=x <L> <S>` · `env X=1 <L> <S>` · `exec <L> <S>` · `bash <L> <S>` · `command <L> <S>` | env injection, wrappers |
| `"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" <S>` | unexpanded variable |
| `/other/bbs-sales/9.9.9/scripts/bbs-fill <S>` · launcher of another version · `<L>x <S>` | launcher outside this root |
| word 0 differs from the root only in case (macOS) · or only in NFC/NFD form | no normalisation |
| `<L> <root>/skills/ca-form-filler/scripts/test_fill_obs_packet.py` · `<L> /tmp/fill_obs_packet.py` · `<L> <root>/skills/../skills/…` · `<L>` alone · `<L> -c x` | script not vetted, not here, `..`, missing, an option |
| `<L> <S>` with a symlink at: a skill folder on the way · the launcher · `scripts/` · **the root itself** | links at or below root |
| launcher file with CRLF line endings · an `ALLOWED` entry `"../x.py"` or `"ca-form-filler/fill.py"` | damaged list: no decision for every command |
| `dangerouslyDisableSandbox: true` · `tool_name: PowerShell` · no `CLAUDE_PLUGIN_ROOT` · stdin not JSON | outside scope |

| Must **allow** | Note |
|---|---|
| `"<L>" "<S>" in.pdf inputs.json out.pdf` | the skill form |
| `'<L>' '<S>' --inspect 'Packet B (2026).pdf'` | single quotes, spaces in an argument |
| `<L> <S> --validate` (both unquoted, ASCII root) | unquoted |
| `"<root>/scripts/"bbs-fill "<S>"` | word 0 built from quoted and unquoted runs |
| `"<L>" "<S>" "C:\Users\rep\Desktop\out.pdf"` and Windows root forms `C:\…`, `C:/…`, `/c/…` | Windows |
| root containing spaces · root containing non-ASCII (`é`, a non-BMP letter) · `CLAUDE_PLUGIN_ROOT` with a trailing `/` | root shapes, quoted |
| `"<L>" "<S>" "Ca\u0301fe\u0301.pdf"` (NFD) · `"<L>" "<S>" "<non-BMP letter>.pdf"` | non-ASCII inside quotes |
| `"<L>" "<S>" -c "import os"` | arguments are data |
| `"<L>" "<S>" ""` | empty argument |

**Differential check against real shells** (Python test): for every case the hook allows,
run the command in `bash --norc --noprofile` **and** in `zsh -f` (which skips the user's
startup files, §3.2) with word 0 replaced by a stub that prints its
argv NUL-separated (`set -f` in bash, `setopt noglob` in zsh); each shell's argv must equal
the hook's word list. Then a bounded fuzz (fixed seed, a few thousand strings over an
alphabet of quotes, `\`, `$`, `;`, `&`, `|`, `=`, spaces, newline, `*`, ASCII and non-ASCII
letters and the two paths): whenever the hook allows, both shells' argv must equal the
hook's and word 0 must be the launcher. A shell that is not installed is a SKIP locally and
a FAIL in CI.

**Where it runs.** CI is `ubuntu-latest` only today. PR A adds a `macos-latest` job that
runs the hook parity (Python half plus pwsh) and the bash/zsh differential, because macOS
reps run the Bash tool in `zsh` and use NFD file names. Windows is covered by V3 and check
12, not CI.

**`updatedInput` guard.** The hook tests grep `plugins/` for `updatedInput` and fail if any
local plugin returns it for Bash (§3.2, "Assumption").

**What the hook allows**, printed by the parity test as a table at the end of each run
(case, decision, reason), so a reviewer sees the allow set without reading code.

## 9. Not in this slice

- Whether `forceRemoveDeletedPlugins` should be set marketplace-wide.
- Any change to what is on `ALLOWED`.
- The launcher refusing output paths under `FILLED/` (follow-up, §2).
- Cowork / claude.ai Chat behaviour of the form skills: hooks and the Bash tool there are
  not verified by this design; the slice only makes `bbs-sales` installable there.
- The checker FAIL on a top-level `bin/` (review side, §4).

## Docs read 2026-11-11

- Hooks reference: `code.claude.com/docs/en/hooks` ("Hook locations",
  `allowManagedHooksOnly`; PreToolUse decision control and `permissionDecisionReason`;
  precedence; exit-code semantics).
- Configure permissions: `code.claude.com/docs/en/permissions` ("Wildcard patterns";
  "Compound commands"; "Precedence among rules, hooks, and mods"; "Hook approvals in plan
  mode").
- Permission modes: `code.claude.com/docs/en/permission-modes` (starting mode from v2.1.283;
  "How the classifier evaluates actions"; "Server-side classifier review" and
  `CLAUDE_CODE_AUTO_MODE_SERVER`; `dontAsk`; what no hook can approve).
- Settings reference: `code.claude.com/docs/en/settings-reference` (`allowManagedHooksOnly`).
- Plugins reference: `code.claude.com/docs/en/plugins-reference` (directory table, `bin/`;
  "Where each variable resolves").
- Plugin components: `code.claude.com/docs/en/plugins/components` (`bin/`).
- Plugin loading: `code.claude.com/docs/en/plugins/loading` ("Name conflicts"; "Cleanup of
  previous versions"; hooks keep the previous version's path until `/reload-plugins`).
- Org rollout: claude.com plugins org-rollout ("loads one plugin per name"), as quoted in
  Rex's review and matching *Plugin loading* rule 5.
- Host a marketplace: `code.claude.com/docs/en/plugins/host-marketplace` ("Distribute
  through organization settings"; "Migrate users with a renames map"; "Uninstall removed
  plugins from users' machines").
- Marketplace reference: `code.claude.com/docs/en/plugins/marketplace-reference` (`renames`).

---

Owner: Parker Marshall. Written 2026-11-11; revised the same day after Rex's review of
8eff944. For re-review before any build.
