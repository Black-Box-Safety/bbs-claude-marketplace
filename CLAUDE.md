# CLAUDE.md — BBS Claude marketplace

@AGENTS.md

The shared contract above is the substance and is read by Cursor too. What follows is
Claude-Code-specific and does not belong in a vendor-neutral file.

## Who does what

Claude builds and designs. Cursor reviews and maintains. They share **facts** (the file
above) and differ in **stance** — identical instructions would mean identical blind spots.

- **Build/design agents** live in `.claude/agents/`. The `steward` dispatches them.
- **Review/maintenance posture** lives in `.cursor/rules/`.
- **`scripts/check_marketplace.py` belongs to the review side.** A checker authored by the
  thing it validates encodes that thing's assumptions — this one initially flagged its own
  fixes until it was taught counter-example awareness.

## Running a work session

`docs/STEWARD.md` is the operating manual: how a night is scoped, the loop each session
runs, and what the steward may and may not decide without Parker.

One rule worth repeating here because it is the one most often broken: **a session ends at
a PR, not at a merge.** The agent that wrote the change does not approve it.

## Plugin agents have a constraint

Agents shipped inside `plugins/*/agents/` silently ignore `hooks`, `mcpServers` and
`permissionMode`. Anything needing those must live in `.claude/agents/`, which also
outranks a plugin agent of the same name.

## Design work in a cloud session

`impeccable` is pinned in `.claude-plugin/marketplace.json` but a fresh cloud container does
not have it installed. When a task names it (the explainer prompts do), fetch only the skill
folder from the fork and load it into the session:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/Black-Box-Safety/impeccable.git "$SCRATCH/impeccable"
git -C "$SCRATCH/impeccable" sparse-checkout set plugin
cp -r "$SCRATCH/impeccable/plugin/skills/impeccable" ~/.claude/skills/impeccable
```

That copies the skill only, so the plugin's edit hooks stay off, as the marketplace entry
intends. Its static `detect` reports false low-contrast hits on a two-theme page (it pairs
one theme's text with the other's surface); measure contrast in a real browser before acting
on them. Explainer pages live in `docs/explainers/<date>-<topic>/`, one HTML source each,
published privately with the Artifact tool; the page source in git is the truth, not the
published copy.

## Model IDs

Read them from `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/models.json`.
It is generated from the API by `refresh_models.py`; do not hand-edit it and do not carry
a copy anywhere. Prompts and system prompts brought in from other projects routinely carry
superseded IDs — treat every one as stale until checked against that file.

---

Owner: Parker Marshall. Last verified 2026-10-01.
