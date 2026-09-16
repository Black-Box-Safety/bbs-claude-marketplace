# Plan — commons toolbox

*Spec: `docs/superpowers/specs/2026-09-16-commons-toolbox-design.md`. Branch:
`claude/commons-toolbox`, off `origin/main`.*

---

## Objective

Turn the commons from three hand-maintained pins into a tier with a recorded release model
per upstream, a cadence derived from it, provenance on every pin, and one agent that owns
the lifecycle end to end.

## Done condition

- `python3 scripts/check_marketplace.py` exits 0.
- `.claude-plugin/marketplace.json` parses, and its three commons entries carry the
  bumped `caveman` pin, a `skills:` filter on `caveman`, and `./skills/pptx` on
  `document-skills`.
- `.claude/agents/commons-curator.md` exists, has a `description` with explicit negative
  scope, and names a model ID read from `models.json`.
- `docs/COMMONS.md` records the lifecycle, the per-upstream release model and cadence,
  the `caveman` license split, a provenance line per entry, and the rejections.
- One PR, off `origin/main`, referencing this plan and the spec.

## Steps

### 1 — Verify the inherited facts rather than re-deriving them *(done)*

The pins came from a prior session's `git ls-remote` / `git clone` work. The clones are
still on disk in this session's scratchpad, so each stated fact was re-read from them
rather than trusted or re-derived from the network:

| Claim | How it was confirmed |
|---|---|
| `caveman` v2.7.0 tag object `e6c5e68b…`, peeled commit `8b0c1d36…`, 2026-09-14 | `git rev-parse` / `git rev-list -n1` / `git log -1` on the tag |
| v2.6.0 peeled commit `b82c0ad4…` | same |
| The Windows `HOOK_ROOT` rewrite | `git show v2.7.0:.claude-plugin/plugin.json` against `v2.6.0` — both hook commands differ exactly as described |
| 20 skills, 6 command files | `git ls-tree -r v2.7.0 skills/` → 20 `SKILL.md`; `git ls-tree v2.7.0 commands/` → 6 files (5 unique names; `caveman-init` ships `.md` and `.toml`) |
| The BSL/MIT split | `git show v2.7.0:LICENSING.md` |
| `document-skills` at `34040c9c…`, `./skills/pptx` present, `Proprietary` + own `LICENSE.txt`, 732-char description | clone at that SHA; frontmatter parsed |
| `superpowers-chrome` v3.0.5 peeled `782358eb…`, newest tag and branch tip | `git rev-list -n1` == `git rev-parse HEAD` |
| `obra/superpowers` v6.3.0 declares `SessionStart` in `hooks/hooks.json` and not in `plugin.json` | `git show v6.3.0:` on both |
| `awesome-claude-skills` HEAD `be2a4069…`, 2026-07-24 | clone |
| `csv-data-summarizer` HEAD `9b3affd2…`, 2025-10-16 | clone |

No pin was altered. Two observations are **additive** to the brief and recorded as such:
`caveman` carries nine tag prefixes rather than three, and its `commands/` directory holds
six files under five names.

### 2 — Spec, then plan *(done)*

Written before any edit, per the repo's build discipline.

### 3 — `marketplace.json`, commons entries only

Three edits, none outside `category: "commons"`:

- `caveman`: `ref` → `v2.7.0`, `version` → `2.7.0`, add `skills: ["./skills/caveman",
  "./skills/caveman-help"]`, rewrite the description to say what is selected and why the
  bump was taken.
- `document-skills`: add `"./skills/pptx"` to `skills`, rewrite the description so it no
  longer says `pptx` is excluded.
- `superpowers-chrome`: description only — "refreshed quarterly per docs/COMMONS.md"
  becomes the release model and cadence now recorded there. The pin does not move.

`bbs-sales`'s description is not touched; PR #12 rewrites exactly that field.

### 4 — `.claude/agents/commons-curator.md`

Shaped after `.claude/agents/steward.md`. Encodes the ten lifecycle rules from the spec,
plus the escalation list and the negative scope. Model from
`plugins/bbs-foundations/skills/bbs-claude-md-forge/references/models.json` — `opus` is
`claude-opus-5`; effort high, because the artefact is a pin that reaches every rep machine
and a wrong one is invisible.

### 5 — `docs/COMMONS.md`

Rewritten around the lifecycle. Roster table gains release model, cadence and provenance.
`pptx` moves out of "Considered, not included" into the roster. The rejection rows gain
their real reasons, including the structural one for `awesome-claude-skills`.

### 6 — Verify

```bash
python3 scripts/check_marketplace.py
python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'))"
claude plugin validate . --strict      # if present
```

### 7 — Commit and open one PR

Referencing this plan and the spec, carrying the escalations and the follow-up checker
proposal.

## Blast radius

`.claude-plugin/marketplace.json` (three commons entries), `docs/COMMONS.md`,
`.claude/agents/commons-curator.md`, two new files under `docs/superpowers/`. No managed
artefact. No skill body. No checker.

The one live-behaviour change is the `caveman` bump: it alters two hook command strings
that run at `SessionStart` and `UserPromptSubmit` on every machine that has the plugin
enabled. That is the change most worth a reviewer's attention, and the reason the
before/after manifests are quoted in the PR rather than summarised.

## Known risks

- **`pptx` + no LibreOffice.** Carried, recorded, escalated. Not resolved here; adding
  LibreOffice to `bbs-setup.ps1` is out of scope for a commons PR and belongs with whoever
  owns rep-machine provisioning.
- **Base ordering.** `bbs-deck-voice` — the skill whose dangling `pptx` pointer motivates
  change 3 — arrives with PR #12 and is not on `main`. This branch is off `main` as
  briefed, so the rationale becomes live when #12 lands. The change is correct either way;
  `pptx` is useful to a rep with or without `bbs-deck-voice`.
- **`caveman` velocity.** Ten days from pin to staleness. The monthly cadence this plan
  sets may itself prove too slow; the curator is told to say so rather than absorb it.

---

Owner: Parker Marshall. Verified 2026-09-16.
