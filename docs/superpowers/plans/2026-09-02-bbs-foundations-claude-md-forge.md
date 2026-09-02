# bbs-foundations / BBSClaudeMDForge — Plan

Spec: `docs/superpowers/specs/2026-09-02-bbs-foundations-claude-md-forge-design.md`.
Branch `feat/bbs-foundations-claude-md-forge` → PR to `main`. Tasks 1–8 are in this PR;
9–12 are follow-ups and are listed so they are not lost.

## In this PR

- [x] **1. Research.** Read every CLAUDE.md, README, SKILL.md, and settings file across the
  14 org repos (read-only sweep); read the `bbs-ops` spec/plan, `github-standards`,
  `parker-voice`, the skill-bus plugin, `claudeforge` internals, and Anthropic's
  `claude-md-improver` rubric. Output: the 25 rules, 19 contradictions, house-style notes.
- [x] **2. Plugin skeleton.** `plugins/bbs-foundations/{.claude-plugin/plugin.json, README.md,
  docs/ONBOARDING.md}`. Verify: `node -e "JSON.parse(...)"` → ok.
- [x] **3. Skill.** `skills/bbs-claude-md-forge/SKILL.md` (<2,000 words) + five references.
  Verify: frontmatter parses; body word count; every `references/` link resolves.
- [x] **4. Checker.** `scripts/check_claude_md.py`. Verify: zero FAIL on the Sentinel tree;
  known-defect fixtures fail; strong fleet files produce no false FAIL.
- [x] **5. Command.** `commands/bbs-claude-md.md`.
- [x] **6. Skill-bus hooks.** `hooks/skill-bus.json` with `bbs-claude-md-doctrine` and the
  relocated `bbs-grounding-doctrine`. Verify: JSON parses; `skill-bus simulate` fires.
- [x] **7. Marketplace.** Append `bbs-foundations`; add `claudeforge` as a pinned github
  source (`Black-Box-Safety/ClaudeForge`, ref `dev`); bump marketplace version 0.1.0 → 0.2.0;
  update `PLUGINS.md`; add two rows to the root README plugins table.
- [x] **8. Commit + PR.** Conventional prefixes, one concern per commit, PR body states
  what is live vs planned.

## Follow-ups (not in this PR)

- [x] **9. Repoint `bbs-ops` grounding subscriptions** to the foundations copy and delete
  the `bbs-ops` insert. Done 2026-09-02 (`chore/repoint-grounding-doctrine`); the
  `site-wiring-map` now says grounding ships with `bbs-foundations`.
- [ ] **10. Fix the contradictions in their home repos**, one PR each: `bbs-agent` LPA
  `-52-` → `-51-` and `claude-opus-4-5` → current; `ca-quote-hub` "5% SB preference";
  `bbs-bc-mcp-proxy` duplicate Base64 bullet; `bbs-sales-vault` dangling `quote-desk/`
  reference. Cite `canonical-facts.md` in each.
- [ ] **11. Remove the separate marketplace registration** for the ClaudeForge fork from
  `~/.claude/remote-settings.json` (added 2026-09-02) once `claudeforge@bbs-claude-marketplace`
  installs; one marketplace for the team.
- [ ] **12. Push the 120-line-warning removal to the ClaudeForge fork** so the plugin copy
  matches the local install and Decision 1 in the spec.
- [x] **13. Decided 2026-09-02.** `github-standards` stays put (Grace's). `parker-voice` is
  the exemplar inside a new `bbs-voice-template` skill in `bbs-foundations`; teammates
  build their own `<first>-voice` locally from it. Shipped on
  `feat/foundations-sb-ruling-and-voice-template`.
- [ ] **14. Acceptance gate.** A non-Parker teammate runs `/bbs-claude-md init` on a repo
  with no CLAUDE.md and passes the checker unaided. Record pass/fail here.
