# SAM.gov opportunities skill — plan

Spec: `docs/superpowers/specs/2026-10-02-sam-gov-opportunities-design.md`.

## PR 1 (review side): registry entry

[Black-Box-Safety/bbs-claude-marketplace#51](https://github.com/Black-Box-Safety/bbs-claude-marketplace/pull/51)

1. Add `sam-gov` to `EXTERNAL_SYSTEMS`.
2. Probe it with a throwaway skill: undeclared use FAILs, declared use is clean.

## PR 2 (stacked on PR 1; merges after it): the skill

1. `plugins/bbs-sales/skills/sam-gov-opportunities/scripts/sam_opportunities.py`: GET only,
   key from the environment, one request per NAICS code, a request cap, loud failures and a
   set-aside fit column.
2. `tests/test_sam_opportunities.py`: offline, with a fake opener. Covers GET-only, key
   redaction, every refusal, 404 as a failure, counted exclusions, truncation, the set-aside
   map and no DVBE in the output.
3. `SKILL.md`: `requires: [sam-gov, python3]`, setup, presentation rules and stop rules.
4. Wiring: the `bbs-sales` README (badge, the federal paragraph, setup), `plugin.json`, the
   root README connector row, the coach jobs map row, and `docs/evals/` (rebuilt
   `skills.json` plus two routing queries).
5. Team-rollout page: SAM.gov moves from Coming next to a Ready row for Kim and Griffin. The
   page's text greps must pass, and the headless render must show the row only where it
   should.
6. Register entry in `docs/STEWARD.md` with the open asks.
7. Run both checkers, `claude plugin validate plugins/bbs-sales`, and the test file.

## Acceptance once merged

- **Live run.** Kim or Griffin runs one lookup with their own key and gets a 200. That is
  the only live verification; this build could not make one.
- **Republish.** The published team-rollout page is republished from the page source. The
  build session does not do this.
