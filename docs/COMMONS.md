# Commons — the curated third-party toolbox

**What it is.** Generally applicable skills and plugins, made by other people, that a BBS
rep is likely to find genuinely useful. Nothing BBS-specific lives here; that belongs in
`bbs-sales` or `bbs-foundations`. Ruled 2026-09-13 — **on the understanding that entries could be
narrowed, which turned out not to be true.** See "Open for Parker."

**The bar.** Quality first, tokens second: a plugin gets in if it works out of the box, is
maintained upstream, and matches a task reps actually do. Context cost is a tiebreaker, not
a veto. Anything that needs a per-machine API key stays out.

**How it ships.** Each item is a pinned external entry in `.claude-plugin/marketplace.json`
under `category: "commons"`, enabled for everyone through managed settings, except
maintainer-tier entries (below), which are pinned but not enabled and not installed by the
bootstraps. Nothing is copied into this repo.

**A commons entry is all-or-nothing.** Read "`skills:` does not filter" below before
assuming otherwise. Because there is no working way to take part of a tree, **the unit of
decision is the whole upstream.** Where the unwanted half is *noise* — developer skills
competing for selection — that is a cost to weigh, and a tree can still be worth taking.
Where the unwanted half is *dangerous* — a command that executes code from outside the pin,
a hook that touches every session — it is a rejection, or an accepted risk named as one.
`caveman` is the second kind, which is why its row below is long.

**Who keeps it true.** `.claude/agents/commons-curator.md`. One agent for one durable
domain, across the whole lifecycle.

---

## Known platform limitation — `skills:` does not filter

A `skills:` list on a marketplace entry is **additive, not restrictive**. It adds paths to
the scan; it does not narrow it. The plugin's whole `skills/` directory registers either
way.

**Established here, not assumed.** Three fixture plugins, each with three inert skills, in
an isolated `CLAUDE_CONFIG_DIR` on **Claude Code 2.1.273**: one declaring `skills:` on the
marketplace entry, one declaring it in `plugin.json`, one control declaring nothing. A live
session was asked to list every fixture skill it could see. All nine came back, in all
three configurations. The installed bundle agrees: `getPluginSkills` loads the default
`skillsPath` **and then appends** the entry's `skillsPaths`.

**What this costs us, today:**

- **`caveman` reps receive all 20 skills**, not the 2 the entry names — plus 6 command
  files and 3 `cavecrew-*` agents, which a `skills:` list never covered in the first place.
- **The `document-skills` filter has never worked either.** Reps have been receiving all 19
  skills in `anthropics/skills` — `academy-guide`, `slack-gif-creator`, `frontend-design`
  and `webapp-testing` among them. The line "pptx deliberately excluded" was already false
  before this revision touched it.
- **Adding `./skills/pptx` is therefore a runtime no-op.** Reps already have `pptx` from
  that pin. It is kept because the *documentation* defect it fixes is real:
  `bbs-deck-voice`'s description ends "use the pptx skill for assembly," and the manifest
  claimed to withhold it. **It changes no rep's capability.**

**Mechanisms tried, none of which restricts the listing:**

| Mechanism | Result on 2.1.273 |
|---|---|
| `skills:` on the marketplace entry | No effect. Additive |
| `skills:` in the plugin's own `plugin.json` | No effect. Additive |
| `skillOverrides: {"<name>": "off"}` in user, project, or local settings | **Did not reproduce.** The key is in the settings schema (`on` / `name-only` / `user-invocable-only` / `off`, described as a per-skill *listing* override) and is managed-settings-mergeable, but neither the bare nor the `plugin:skill` key form removed a fixture skill from a session's listing |
| `permissions.deny: ["Skill(<plugin>:<skill>)"]` | **Blocks execution, confirmed.** The denied skill returns `Skill execution blocked by permission rules`; an undenied sibling in the same tree still runs. The wildcard `Skill(<plugin>:*)` blocks the whole tree the same way. It does **not** remove the skill from the listing, so the context cost stays and the model still selects it and then fails. A risk control, not a noise control |

**So: the `skills:` lists in `marketplace.json` record intent and nothing more.** They are
kept because they are harmless, they say what BBS decided, and they become correct if the
loader ever changes. They are not a control. Nothing in this file may describe them as one.

**There is exactly one control that works today**, and it is a blunt one: a
`permissions.deny` entry of the form `Skill(<plugin>:<skill>)`, or `Skill(<plugin>:*)` for a
whole tree, in managed settings. It stops the skill *running*. It buys back no context and
removes no selection noise — the model still sees the skill, picks it, and then fails. Use
it where a skill is a hazard, not where it is merely surplus.

**It does not reach commands.** A command is not a skill, so `Skill(…)` cannot touch
`caveman-init`; `grep -aoF 'SlashCommand(' ` on the installed binary returns zero
occurrences, against seven for `Skill(`. The only reachable lever for a command is a
Bash-level deny on what the command tells Claude to run.

`skillOverrides` remains the only candidate that would cut the listing itself, and it did
not reproduce. Both live in **managed settings** — Parker's, not this repo's.

---

## The lifecycle

```
evaluate → pin → validate → refresh (on cadence) → retire
```

**Evaluate.** Three hard filters: API key, license, rep-appropriateness. An independent
upstream has to exist — see the `awesome-claude-skills` entry below for why that is not a
formality. And because selection does not work, judge the **whole tree**.

**Pin.** A pin is a fact from a system of record. It is read off the upstream or it is not
written. `caveman` and `superpowers-chrome` both tag **annotated**, so the recorded SHA
must be the **peeled commit**, not the tag object — the tag object exists, looks plausible,
and is not the code. (`anthropics/skills` has no tags at all, so the question does not
arise there; its pin is a commit SHA by necessity.)

**Validate.** `python3 scripts/check_marketplace.py` and `claude plugin validate . --strict`.

**Refresh.** On the entry's own cadence, not the calendar's. What gets diffed is what reps
receive: the plugin manifest (**especially `hooks`**), the tree's skill, command and agent
**counts**, and `LICENSE*` / `LICENSING.md`. The three hard filters are re-applied every
refresh, not grandfathered from intake.

**Retire.** The liveness clock is the **last commit on the default branch**, not the last
release — a repo can go six months without a tag and be under daily development. Two
cadence periods of silence raises fork-or-drop. The curator raises it; Parker decides it.

### Release model drives cadence

| Release model | Cadence | Why |
|---|---|---|
| `rolling` (no tags) | monthly | There is no tag to wait for; the signal is commit date. "Check for a newer tag" returns clean forever |
| `tagged` (one train) | quarterly | |
| `multi-train` (interleaved prefixes) | monthly | A release you want can sit between four you must not take, and the trains move at different speeds |

A `tagged` upstream that in practice ships faster than quarterly is treated as
`multi-train`. Evidence: `caveman` shipped `v2.7.0` on 2026-09-14 — ten days after the
`v2.6.0` release the pin was taken from, and one day after the ruling was last verified.

### Pins are tag refs, and tags move

`caveman` and `superpowers-chrome` are pinned to `v2.7.0` and `v3.0.5` — **mutable refs.**
A force-moved upstream tag silently changes what every rep gets, and the recorded peeled
commit below would no longer describe the code. Until the pins are commit SHAs, **every
refresh re-checks that the tag still peels to the recorded commit** (step 2 of the
procedure). Moving the pins to SHAs outright costs the readability of a version number and
is Parker's call; the re-check is the interim control.

---

## Current roster

| Plugin | Pin | Release model · cadence | Why reps have it | Watch for |
|---|---|---|---|---|
| `superpowers-chrome` | `v3.0.5` | `tagged`, single `vX.Y.Z` train · quarterly | Drives the rep's own Chrome: product research on distributor and agency sites, logged-in sessions included. Full browser access is a standing ruling; no deny rules touch it | Upstream says beta. Needs Node.js (`bbs-setup.ps1` / `bbs-setup.sh` install it). Pin is a mutable tag ref. If a rep hits a crash, log it in FLAGS |
| `caveman` | `v2.7.0` | `multi-train`, nine tag prefixes, authoritative train is bare `vX.Y.Z` · monthly | Opt-in terse mode. Cuts output tokens roughly two-thirds; technical content stays exact. `/caveman lite` is a good default for long sessions | Off by default via managed env (`CAVEMAN_DEFAULT_MODE=off`); never forced on. **Reps receive the whole tree** (measured on Claude Code 2.1.273 on Linux; the loader is not platform-specific, but it was not re-measured on Windows) — 20 skills, 6 command files, 3 `cavecrew-*` agents — because `skills:` does not filter. **`caveman-init` (`.md` and `.toml`) runs `curl … raw.githubusercontent.com/JuliusBrussee/caveman/main/src/tools/caveman-init.js \| node -`: download-and-execute from upstream `main`, bypassing the pin entirely and writing rule files into the rep's current repo.** Pre-existing at v2.6.0. Commands ship regardless of any `skills:` list. `caveman-help` advertises `/caveman-compress`, for which no command file exists. Split license, see below. Pin is a mutable tag ref |
| `document-skills` (Anthropic) | commit `34040c9c` | `rolling`, zero tags · monthly | Word, PDF, Excel and PowerPoint with real scripts: fill and merge PDFs, read tracked changes, build spreadsheets with formulas, assemble decks. RFQ worksheets and bid packets are exactly this | **`pptx` visual QA and PDF conversion go through LibreOffice (`soffice`), now installed by both bootstraps; behaviour on a rep's Windows box is still unverified.** `docx` and `xlsx` reference `soffice` too. `pptx` also assumes `pptxgenjs` is preinstalled; on a rep machine it is an `npm install`. **Reps receive all 19 skills in the tree**, not the 4 named — the filter has never worked (measured on Claude Code 2.1.273 on Linux; not re-measured on Windows). `uv` from the bootstrap covers the Python runtime; Poppler covers `pdftoppm` |

### Provenance

Every pin, with how it was established. Method for all three: `git ls-remote` / `git clone`
through the agent proxy. **The GitHub MCP cannot see third-party repos here and
`api.github.com` returns 403 over the proxy — an access error is not evidence a repo is
missing.**

| Entry | Verified | Tag object | Peeled commit | Upstream date |
|---|---|---|---|---|
| `superpowers-chrome` `v3.0.5` | 2026-09-16, agent | `9048f78163ff3c1f1300a856b8890ab02c92d9f0` | `782358eb8d3b99e3cc1321354b9233f660fdac7a` | 2026-08-07 — newest tag *and* branch tip |
| `caveman` `v2.7.0` | 2026-09-16, agent | `e6c5e68b0064758b8106b83df41cf3829dde3216` | `8b0c1d3699b8d83e87fe4605b378da20c41555e0` | 2026-09-14 |
| `document-skills` `34040c9c` | 2026-09-16, agent | — (no tags in repo) | `34040c9c568585f6929bedeaad110ad08f079624` | 2026-09-10 — is exactly current HEAD |

### Why `caveman` moved to v2.7.0 — and how big the move actually is

The reason for taking it is a Windows fix. v2.7.0 rewrites both hook commands to prepend

```
HOOK_ROOT=$(printf %s "${CLAUDE_PLUGIN_ROOT}" | sed 's|^/\([a-zA-Z]\)/|\1:/|')
```

which converts an MSYS/Git-Bash `/c/...` path back into `C:/...` before invoking `node`.
v2.6.0 invokes `node` against the unconverted path. **BBS reps are on Windows** and their
Bash tool runs through Git Bash, which is why `bbs-setup.ps1` installs `Git.Git`.

**The bump is not two lines.** `v2.6.0..v2.7.0` is **438 files changed, +42,604 / −6,024**.
Inside `src/hooks/` alone it is 12 files, +555 / −415. By `--numstat`, so these are real
insertions and deletions rather than `--stat`'s total-changed: `caveman-activate.js`
**+18/−60**, `caveman-mode-tracker.js` **+62/−9**, a **new `caveman-config.js` (+101/−0)
that both hooks now depend on**, `caveman-stats.js` **+139/−286**, `caveman-parse.js`
+80/−5, the statusline scripts, the install/uninstall scripts, and `checksums.sha256`. **The hook
runtime changed, not just the command strings that invoke it.** The two strings are quoted
above because they are the visible part; they are not the size of the change.

**Open risk, unresolved.** caveman's `plugin.json` declares no `shell` for its hooks, while
`obra/superpowers` sets `"shell": "bash"` explicitly. v2.7.0's command is now **shell
syntax** (`HOOK_ROOT=$(...); node ...`) where v2.6.0's was a bare `node` invocation. If
hooks are not run through a POSIX shell on a rep's Windows box, the fix does not apply and
**the hook breaks outright** — a worse outcome than the bug it fixes. Nobody on this side
has a Windows machine to test it. This is the highest-blast-radius item in the tier: it
runs at `SessionStart` and `UserPromptSubmit` on every machine with the plugin enabled.

### The `caveman` license split

Recorded here, not changed. `LICENSING.md` puts `engine/`, `proxy/`, `rewriter/`, `browse/`,
`mcp/` and `shrink/` under **BSL-1.1** (also the `mem/` Go core and `shared/platform/`);
`skills/` and the SDK, CLI and contract packages stay **MIT**.

The BSL Additional Use Grant permits internal evaluation, local development, CI, and
self-hosted use for your own first-party traffic including production. **BBS reps running
caveman locally are inside that grant.** The boundary it draws is offering the licensed work
to third parties as a hosted, managed or embedded service — which BBS does not do. BSL
versions convert to Apache-2.0 on the earlier of 2030-06-21 or four years from that
version's first BSL distribution.

**This was already true at v2.6.0 and went unrecorded at intake** — `proxy/`, `engine/`,
`LICENSE.BSL` and `LICENSING.md` all arrived in a single commit, `82864c8f`, on 2026-08-11,
tagged `v2.0.0`, a month before the ruling that pinned v2.6.0. That is the reason the
license and API-key filters are re-applied at **every** refresh rather than treated as
settled at intake: the thing was there to be read and nobody read it. Nothing "grew between
quarterly checks" — the tier was ruled on 2026-09-13 and no quarterly interval has elapsed
since.

---

## Maintainer-tier entries (in the catalog, not a rep default)

Developer- or designer-aimed tools Parker asked for. They are pinned like every other
commons entry, are **not** in `enabledPlugins` in managed settings, and carry the
**`maintainer` keyword** on their `marketplace.json` entry.

**How they stay off rep machines (Parker, 2026-10-28, in session).** Leaving an entry out
of `enabledPlugins` is not enough on its own: `scripts/bbs-setup.ps1` and
`scripts/bbs-setup.sh` install every plugin in `marketplace.json` that managed settings do
not set to `false`. So both bootstraps also skip any entry keyworded `maintainer`. Parker
installs one on his own machine by hand:

```bash
claude plugin install taste-skill@bbs-claude-marketplace --scope user
```

Managed settings are not used for this: a `false` there would very likely block the tool
on Parker's machine too, since managed settings outrank user settings. **A maintainer-tier
entry without the `maintainer` keyword reaches every rep at their next setup run.** The one
earlier maintainer-tier draft (#20, `andrej-karpathy-skills`, 2026-09-17) relied on
`enabledPlugins` alone and was closed unmerged on 2026-10-02.

| Plugin | Pin | Release model · cadence | Why it is here | Watch for |
|---|---|---|---|---|
| `taste-skill` | `v2.1.5`, sha `12af471f` | `multi-train`, authoritative train bare `vX.Y.Z` (ignore the two `archive/` tags) · monthly: tagged, but seven releases from 2026-10-13 to 2026-10-25 (`CHANGELOG.md`), faster than quarterly | Parker, 2026-10-27: design work on the customer bots. Art direction for websites, product pages, dashboards and app screens, with a screenshot look-and-fix loop | **One skill, `design-taste-frontend`; no hooks (no `hooks/` directory, no `.claude-plugin/plugin.json`; the `.codex-plugin/plugin.json` it carries is for Codex and inert here), no commands, no agents at the pin.** Its description fires on "landing page", "product page", "dashboard", "redesign" and "looks generic", so on any machine that has it, it competes for selection with `impeccable`, `document-skills`' `frontend-design` and `bbs-website:product-page`. Scripts need Node and a local Chrome, Edge or Chromium (`CHROME_PATH` overrides). `assets.mjs` queries api.openverse.org, commons.wikimedia.org, api.artic.edu, collectionapi.metmuseum.org, archive.org and images-api.nasa.gov with no key and downloads the chosen images and video (archive.org and NASA) into the working project, refusing a licence outside the allowed set unless run with `--license all`; `draw.mjs` prints picsum.photos links and writes `~/.taste-skill/history.json`. No download-and-execute anywhere in the tree. Upstream `install.sh` symlinks into `~/.claude/skills`: **do not use it**, that is the user-level copy this file forbids. MIT |

**Provenance.** Method as above (`git ls-remote` and a shallow clone through the agent
proxy).

| Entry | Verified | Tag object | Peeled commit | Upstream date |
|---|---|---|---|---|
| `taste-skill` `v2.1.5` | 2026-10-27, agent | — (lightweight tag: `refs/tags/v2.1.5` resolves straight to the commit) | `12af471f627f866411b4bd785b19646d3672784c` | 2026-10-25 (`CHANGELOG.md` `## 2.1.5 - 2026-10-25`); also HEAD of the default branch at pin time |

The entry carries both `ref` and `sha`, so a force-moved tag cannot change what installs.
The upstream ships no `.claude-plugin/plugin.json` (only its own `marketplace.json`), so the
entry is `strict: false`, the same shape as `document-skills`.

---

## Considered, not included

| Candidate | Reason |
|---|---|
| humanizer / avoid-ai-writing | Already inside `bbs-voice-template` (35 patterns vendored from blader/humanizer) |
| superpowers (full) | Developer workflow; its session hook injects a large mandatory block. **Parker-only.** Ruling re-verified 2026-09-16: at `v6.3.0` the `SessionStart` hook is declared in `hooks/hooks.json` and **not** in `plugin.json`, so a check of the manifest alone would wrongly report it gone |
| `brainstorming` | Ships inside the same `superpowers` tree (`skills/brainstorming/`), so it inherits that hook and that ruling. There is no way to take it without the rest — see "`skills:` does not filter." Parker-only, confirmed still correct |
| Playwright MCP | Isolated browser, no logins, ~25 tool schemas per session |
| `internal-comms` | Free to add and correctly licensed, but it teaches **Anthropic's** internal comms formats, not BBS's. If the need is real it belongs in `bbs-foundations` carrying BBS formats, not pinned from outside. (It already reaches reps anyway, inside the `document-skills` pin) |
| `csv-data-summarizer` | Upstream `coffeefuelbump/csv-data-summarizer-claude-skill`, HEAD `9b3affd270f85aaf1c8a7a457f510034d5736cde`, **last commit 2025-10-16 — eleven months stale.** Fails the maintenance bar, and `xlsx` already covers the need |
| `postgres` | Reps do not write SQL, the Supabase MCP is already configured for the catalog work, and the host repo is 24 skills of which roughly 9 are Google-stack — BBS is Microsoft 365. All 24 would ship |
| `kaizen` | Developer-aimed by its own frontmatter, and 204 `SKILL.md` files is a selection surface, not a toolbox |
| `meeting-insights-analyzer` | No independent upstream — it is a directory inside an aggregator list. Pin unverified, and there is nothing maintained to pin |
| claude-persona | Marketing tier, burns seat limits; admin only |
| `google-workspace-skills` | BBS is Microsoft 365 |

### `ComposioHQ/awesome-claude-skills` — evaluated in full, zero additions

Parker supplied it. HEAD `be2a406907dbc61b73e6827ded415c96139d13a2`, last commit 2026-07-24.
It yielded **nothing installable**, and the reason is structural rather than about taste, so
it is written down here to save the next evaluation.

- **Its headline entries are directories vendored into the awesome-list repo itself** —
  `./meeting-insights-analyzer/`, `./invoice-organizer/`, `./lead-research-assistant/` and
  roughly eleven more. The only pinnable upstream is therefore a marketing aggregator that
  did not write the code and does not maintain it. Pinning that violates "pin the real
  home or pin neither."
- **It also vendors stale copies** of `brand-guidelines`, `canvas-design`, `mcp-builder`,
  `skill-creator`, `theme-factory` and `document-skills` — every one of which has a real,
  maintained home in `anthropics/skills`, which this marketplace already pins.
- **The rest fail a hard filter**: API key (`connect` / Composio's own funnel,
  `deep-research`, `imagen`, `jules`, `langsmith-fetch`), Google or otherwise wrong stack,
  or developer-aimed.

An aggregator list is a candidate source, not an install path. **Its install guidance is a
user-level copy into a personal skills directory. Do not follow it** — that is exactly the
pattern that produced this company's shadowed personal skills, where the maintained
marketplace copy loses to a stale local one.

---

## Refresh procedure

Run by `commons-curator`, per entry, on that entry's cadence. Every command below was run
against a live upstream on 2026-09-16 and returns what it claims to.

```bash
U=https://github.com/JuliusBrussee/caveman.git     # the entry's url

# 1. DISCOVERY — read plain refs. Use --refs here: it strips the ^{} duplicates.
#    Do NOT discover by grepping for ^{} lines: that keeps only ANNOTATED tags and
#    silently drops every lightweight one. On caveman's v-train that is 12 of 26
#    (v1.0.0 v1.1.0 v1.2.0 v1.3.0 v1.3.5 v1.4.1 v1.5.0 v1.5.1 v1.6.0 v1.7.0
#    v1.8.0 v1.8.1). It returns the right answer today only because v2.7.0 happens
#    to be annotated; the next lightweight release returns the previous annotated
#    tag and the refresh records "checked, current" while the pin rots.
#    Filter to the train first, then sort -V — lexical sort puts v1.9.0 above
#    v1.10.0 and superpowers-chrome has both.
NEWEST=$(git ls-remote --tags --refs "$U" \
  | sed 's|.*refs/tags/||' \
  | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)

# 2. PEEL the winner — and only the winner, where ^{} is what you want.
#    An annotated tag returns two lines and the ^{} one is the commit; a lightweight
#    tag returns one line which already IS the commit. tail -1 is correct for both.
git ls-remote "$U" "refs/tags/$NEWEST" "refs/tags/$NEWEST^{}" | tail -1 | cut -f1

#    Re-check the CURRENT pin the same way. Tags are mutable; a force-move is silent.
git ls-remote "$U" 'refs/tags/v2.7.0' 'refs/tags/v2.7.0^{}' | tail -1 | cut -f1
#      -> must equal the recorded peeled commit 8b0c1d36…
#      The bare 'refs/tags/v2.7.0' line alone is the TAG OBJECT, not the pin.

# 3. Liveness: last commit on the UPSTREAM default branch.
#    `git log -1 --format=%cI origin/HEAD` with no clone is the trap — run from this
#    repo it reports BBS's own last commit wherever origin/HEAD is set, and errors
#    where it is not. Either way it never measures the upstream. Clone shallow:
git clone -q --filter=blob:none --no-checkout --depth 1 "$U" /tmp/liveness-probe
git -C /tmp/liveness-probe log -1 --format=%cI HEAD
```

Then diff the manifest (**especially `hooks`**, and read `hooks/hooks.json` too, not only
`plugin.json`), the tree's skill, command and agent counts, and the license files.
Re-apply the three hard filters. Bump the pin only with a reason that names what changed
for a BBS rep, and state the **size** of the change, not only the part that motivated it.
Update the provenance row.

**Re-test whether `skills:` filters yet.** Three fixture plugins in an isolated
`CLAUDE_CONFIG_DIR`, one skill named in `skills:` and two not; ask a live session what it
can see. If it ever starts restricting, the roster's "reps receive the whole tree" rows
become wrong on the same day, and several "Considered, not included" rulings can be
revisited.

Then validate, and open a PR; an agent that did not write it reviews it.

A refresh that changes nothing is a successful refresh. Record "checked, current" with the
date and move on.

## Propose an addition

One line in the Teams sales channel: what it does, the task it would replace, a link.
Parker tries it a week on live work first. Same bar as above; the candidate must have an
independent, maintained upstream to pin, and **the whole tree has to be acceptable**,
because selection does not work.

## Open for Parker

- **The 2026-09-13 ruling was made on a premise that turned out false.** It admitted this
  tier on the understanding that an entry could be narrowed to the skills BBS wanted. It
  cannot. `caveman` means 20 skills, 6 commands and 3 agents; `document-skills` means all
  19 skills. **Does the ruling still hold on all-or-nothing terms?** Not decided here.
- **`skillOverrides` in managed settings** is the only candidate that would cut the
  *listing*. It did not reproduce in testing here. Account/managed-settings-side, not
  repo-side.
- **`permissions.deny: ["Skill(caveman:*)"]`** — or per-skill — is a control that does work
  today: it stops the skills running. It does not reduce context or selection noise, and it
  does not reach commands. One line in managed settings, if the risk is what matters.
- **`caveman-init` bypasses the pin** — download-and-execute from upstream `main`. Options
  are to accept it, to drop `caveman`, or to deny at the Bash level the `curl … | node -`
  the command tells Claude to run. **There is no `SlashCommand()` permission type**, so
  denying the command itself is not available; the Bash deny is blunter and catches only
  that shape of invocation.
- **Windows hook shell**, above: untested and the highest blast radius in the tier.
- **LibreOffice** is now in both bootstraps (`scripts/bbs-setup.ps1` via winget
  `TheDocumentFoundation.LibreOffice`, `scripts/bbs-setup.sh` via `brew install --cask
  libreoffice`). Three pinned document skills plus `bbs-quote-builder` still reference
  `soffice`. Behaviour on a rep's Windows box is unverified until a pilot run.
- **Account-synced personal copies** of `docx`, `pdf`, `xlsx` and `pptx` compete with the
  pinned copies. Account-side; no repo change fixes it.

---

*Maintainer: Parker Marshall · Curator agent: `.claude/agents/commons-curator.md` · Last
verified: 2026-09-16 (roster) · 2026-10-27 (maintainer tier)*
