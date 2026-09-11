# External research briefs — SMB AI ops & Claude Code team practices

**Date:** 2026-09-11. Two research sweeps supporting the rep-workspace rollout design.
Condensed; source links preserved. Adopted items are marked ✅ (see the spec's
"Adopted operational practices" section for build mechanism and home).

---

## Brief A — What successful SMB AI adopters do after rollout

Evidence caveat: almost no published operational detail exists for sub-15-person *agentic*
AI rollouts — BBS is ahead of the written record. Enterprise practice scaled down and
first-principles adaptations are labeled in the full agent output.

### Measurement & ROI ✅
- MIT 2025: ~95% of GenAI pilots show no P&L impact; failure traces to adoption/measurement
  practices, not model quality. Back-office labor automation (extraction, drafting,
  form-filling — exactly the BBS workload) is where real ROI concentrates.
- Practice: baseline time-per-task **before/at** rollout (reconstructable now from Outlook
  timestamps — a window that closes); adoption tracked separately from time-saved (leading
  vs lagging); monthly 30-minute review of 3–4 numbers, never a BI project.
- Sources: [Anthropic deployment guide (PDF)](https://cdn.prod.website-files.com/6889473510b50328dbb70ae6/69f24d3e09b921b92403774e_Claude-Deploying-Claude-Across-Your-Organization-04292026.pdf),
  [Yahoo/Fortune — MIT report](https://finance.yahoo.com/news/mit-report-95-generative-ai-105412686.html),
  [SANSA — SMB AI ROI](https://sansatech.com/insights/measuring-ai-roi-in-an-smb-context)

### Evaluation & QA ✅
- Three-tier pattern: frozen **golden set** re-run on any change; **sampled human review**
  (100% for numbers going to buyers — under [FAR 14.407-4](https://www.acquisition.gov/far/14.407-4)
  and GAO case law a bid pricing error is binding); blameless **failure log** feeding the
  golden set.
- Make the AI show its work (source line beside each extracted field) so review is
  comparison, not re-derivation.
- Sources: [golden sets + sampling + human review](https://medium.com/@deolesopan/evaluation-at-scale-combine-golden-sets-sampling-and-human-review-to-keep-gen-ai-quality-high-aef9d9bc9984),
  [blameless culture](https://oneuptime.com/blog/post/2026-01-30-blameless-culture/view)

### Feedback loops ✅
- Weekly 15-min show-and-tell; one friction channel with a response-SLA (dead channels are
  worse than none); a deputy champion for "how do I ask it…" questions; fixes land in
  skill files, never verbal lore.
- Sources: [AI champions](https://www.layer3labs.io/guides/ai-champions-program),
  [Claude Code rollout playbook](https://systemprompt.io/guides/claude-code-organisation-rollout)

### Governance & risk ✅
- 11–50-person firms have the highest shadow-AI density; the best control is making the
  sanctioned tool better than free ChatGPT. One-page AUP; quarterly key-rotation/permission
  hygiene; vendor check before anything enters the marketplace; break-glass documentation
  (bus factor = 1 is the top structural risk).
- Sources: [shadow-AI governance gap](https://www.helpnetsecurity.com/2025/11/12/delinea-shadow-ai-governance/),
  [key rotation](https://blog.gitguardian.com/api-key-rotation-best-practices/),
  [bus factor](https://sanguinesa.com/bus-factor-are-you-prepared-key-people-disappear/)

### Change management ✅
- Every model bump is a breaking change in disguise; countermeasures at small scale:
  admin-as-canary, golden-set re-run before promoting, never landing a model update and a
  skill update on users the same week, two-line change notes in user language, revert-is-fine.
- Sources: [semver lie](https://tianpan.co/blog/2026-04-29-semver-lie-llm-minor-update-breaks-production),
  [prompt-update incidents](https://deepchecks.com/llm-production-challenges-prompt-update-incidents/)

### What kills SMB rollouts
Ranked for BBS: no measured P&L link; champion departure/bus factor; trust collapse after
an unhandled error (one binding wrong bid could end the program culturally); tool
sprawl/shadow AI; over-automating the *decision* instead of the *labor*; feedback loops
that go quiet; AI bolted beside the workflow instead of into it.

---

## Brief B — Claude Code team deployment capabilities (Sept 2026)

### Administration
- **Server-managed settings** from the claude.ai admin console: top of settings precedence,
  fetched at startup + refreshed hourly, no MDM needed. File/registry alternatives exist.
  [Admin setup](https://code.claude.com/docs/en/admin-setup) ·
  [Managed settings](https://code.claude.com/docs/en/managed-settings)
- Enforceable keys adopted for BBS ✅: `permissions.*` incl. `disableBypassPermissionsMode`;
  `strictKnownMarketplaces` (must include `skills-dir` + the official marketplace source);
  `strictPluginOnlyCustomization` (kills hand-copied-skill drift structurally);
  `forceLoginMethod` / `forceLoginOrgUUID`; `allowManagedHooksOnly`; sandbox keys;
  `claudeMd` (managed company memory); `availableModels`; `minimumVersion`.
- **Analytics** ✅: Team dashboard (DAU, sessions, accept rate) + per-user spend report.
  [Analytics](https://code.claude.com/docs/en/analytics)
- OpenTelemetry exists (incl. per-skill invocation names via `OTEL_LOG_TOOL_DETAILS`) —
  deferred: only worth it with an observability stack; the spend report suffices today.

### Plugins/marketplace
- `version` semantics ✅: omit `version` on actively developed internal plugins → every git
  push auto-updates; pin only stable releases.
  [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- `claude plugin validate .` before push; test via local marketplace add; semver +
  CHANGELOG discipline for anything pinned.

### Skills
- **Eval-first methodology** ✅: 3+ eval cases before extending a skill; two-Claude loop
  (author vs fresh runner); re-run evals on skill/schema/model change; no built-in runner —
  teams build a small harness (headless `claude -p` + grader).
  [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

### Guardrails
- **Hooks are enforced; CLAUDE.md is advisory** ✅. "To block an action regardless of what
  Claude decides, use a PreToolUse hook." Distribute via plugins; lock with
  `allowManagedHooksOnly`. [Hooks guide](https://code.claude.com/docs/en/hooks-guide)
- OS-level sandboxing with a network domain allowlist closes the "denied WebFetch, Bash
  curls anyway" gap. [Sandboxing](https://code.claude.com/docs/en/sandboxing)

### Features a small business commonly misses
- **Routines** ✅ — scheduled/webhook cloud agents, no server: the nightly audit vehicle.
  [Routines](https://code.claude.com/docs/en/routines)
- Claude Code on the web + org-shared cloud environments; Remote Control from phone.
- `/doctor`, `/status` (shows which managed-settings source won), `/context`,
  `InstructionsLoaded` hook — diagnostics `/bbs-checkup` should build on.
- **Cowork** — the folder-scoped desktop agent for non-technical users; relevant as the
  documented Desktop-app path reps already use.
- Free training: [Claude 101](https://anthropic.skilljar.com/claude-101),
  [Claude Code in Action](https://anthropic.skilljar.com/claude-code-in-action) ✅ (rep guide).

### Company memory
- Hierarchy: managed `claudeMd` (cannot be excluded) → user → project → path-scoped
  `.claude/rules/*.md` → local. Target <200 lines/file; add an entry when Claude makes the
  same mistake twice; `/doctor` trims. [Memory](https://code.claude.com/docs/en/memory)
