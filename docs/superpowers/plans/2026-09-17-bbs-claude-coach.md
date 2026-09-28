# Plan — bbs-claude-coach + plugin-github expert

*Spec: `docs/superpowers/specs/2026-09-17-bbs-claude-coach-design.md`. Branch:
`cursor/bbs-claude-coach-25a0`, off `cursor/toolkit-framework-doc-cdf4`.*

---

## Objective

Ship (1) a reusable `.claude/agents/bbs-plugin-github-expert.md` stance and (2) a first-party
`bbs-claude-coach` plugin that empowers BBS's non-technical team to understand, use, and
extend Claude — then open a draft PR. Do not merge.

## Done condition

- `python3 scripts/check_marketplace.py` exits 0.
- Expert agent present with when-to-use / when-not / negative scope.
- Plugin on disk, in `marketplace.json`, in `PLUGINS.md`, noted in managed-settings
  template `enabledPlugins`.
- Root README and `/bbs-checkup` list the new plugin.
- Draft PR against `main` referencing the spec and this plan.
- PR body states whether `claude plugin validate` ran (CLI absent → say so).

## Steps

### 1 — Expert agent

Write `.claude/agents/bbs-plugin-github-expert.md` matching steward / commons-curator
frontmatter style (`name`, `description` with negative scope, `model: opus`, `effort: high`,
`memory: project`). Body covers GitHub, Anthropic plugin craft, org distribution, working
rules. Escalate binding-document and managed-settings deployment to Parker.

### 2 — Plugin skeleton

```
plugins/bbs-claude-coach/
├── .claude-plugin/plugin.json
├── README.md
├── commands/
│   ├── bbs-what-can-i-do.md
│   ├── bbs-start.md
│   └── bbs-explain-claude.md
├── skills/
│   └── bbs-claude-coach/
│       ├── SKILL.md
│       └── references/
│           ├── glossary.md
│           ├── jobs-map.md
│           ├── how-to-extend.md
│           └── aup-rails.md
```

### 3 — Register and point

- Append marketplace entry (local `./plugins/bbs-claude-coach`, category foundations).
- Update `.claude-plugin/PLUGINS.md`, root README table + badge, TOOLKIT.md "run these"
  pointer, managed-settings template `enabledPlugins`, `/bbs-checkup` plugin list.

### 4 — Verify

```bash
python3 scripts/check_marketplace.py
# if available: claude plugin validate plugins/bbs-claude-coach
```

Fix every FAIL. Commit. Push. Open draft PR (writer does not merge).
