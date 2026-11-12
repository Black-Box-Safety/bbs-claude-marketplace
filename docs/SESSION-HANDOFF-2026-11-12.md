# Session handoff — 2026-11-12 (steward, marketplace cleanup)

Dated narrative. Not edited after today. The rulings themselves live in the register in
`docs/STEWARD.md`; this file only says where things stand and what is open.

## What this session did (2026-11-10 to 2026-11-12)

- **Queue drained.** Merged to `main`: #80, #79, #75 (merged by Rex before Parker's per-PR
  approval rule existed; Parker kept them), #82, #81, #83, #74, #71, #53, #77, #76, #72, #84,
  #68, #86, #85, #88. Closed after their content was ported: #73 (into #74), #78 (into #71).
- **Managed settings re-pasted by Parker, 2026-11-12** (file from `main` 5ae15f3). Agents can no
  longer merge (R1). Payroll denied; Vercel purchases ask; Outlook/Teams sends ask on every
  prefix; sessions start on Opus at medium.
- **Quote path:** reps create items then quotes in Business Central (`bc-item-entry` →
  `bc-quote-entry`); `bbs-quote-builder` retired. NASPO lines must equal cost exactly.
- **Desk memory:** slices 1 and 2 shipped (`desk-remember`, `LEARNED.md`, first-touch hook).
- **Rep material:** the CA desk handbook (#88, https://claude.ai/artifact/9Xg2vdxjvLPnLrXZeRozoX)
  and the Quote Desk Field Card (https://claude.ai/artifact/XypT8eoVTVw65QRr2eXM72). Both are
  private until Parker shares them. An announcement email sits in Parker's Outlook Drafts.
- **Working docs archived** (this PR): finished specs and plans moved to
  `docs/archive/superpowers/`, older session handoffs to `docs/archive/session-handoffs/`.
  Live ones stay in `docs/superpowers/`: desk memory (slices 3–4 unbuilt), bbs-fill into
  bbs-sales (PR B unbuilt), the folder-first RFQ pipeline (decision just ruled).

## Open PRs

| PR | State | Next step |
|---|---|---|
| #87 bbs-fill gate, PR A | Cleared by Rex at `0552c6c` | Parker runs V1–V3 from the PR body on a real machine (one Windows), then merges |
| #89 rulings 2026-11-11/12 | Cleared by Rex at `b72a772` | Parker merges |
| This PR (archive + handoff + STRUCTURE.md) | Draft | Rex review, then Parker merges |

## Live sessions

- **Dashboard–folder sync design** (`session_01BEpKzUzYAUwagXC42dCXfM`, medium). Ends in one
  draft PR. Reports to the handbook session.
- **Quote Velocity redesign** (`session_01BEpKzSiw1SCaVm4RkQD3gz`, medium). Builds `index.v2*`
  beside the live dashboard. It must not republish the live artifact or overwrite SharePoint
  until Rex has reviewed it.
- **Handbook session** (`session_01BEpKzSaL5bxwUjS5fULdKy`): kept open only to receive those two
  reports. Archive it once both are in.
- **bbs-fill worker** (`session_01BEpKzULfMJMg3DG3DB5HSJ`): waits for #87 to merge and check 12
  to pass on a rep machine, then builds PR B (retire `bbs-tools`, remove `Bash(bbs-fill *)`,
  re-paste).
- **Rulings worker** (`session_01BEpKzSLab17hK1AbgRVoEo`): archive once #89 merges.

## Parker's open items

1. Merge #89; run V1–V3 and merge #87.
2. Share the handbook and field card; send the Drafts email.
3. Live test of the paste: payroll read blocked, Vercel purchase asks, new session opens on Opus/medium.
4. Admin console: add `bc-quote-entry` to the organization instruction's BC-writes sentence.
5. Restamp the SharePoint desk-root `CLAUDE.md` from `workspace/DESK-CLAUDE-template.md`.
6. Delete the account-synced `bbs-quote-builder` skill in claude.ai.
7. Each rep runs `whoami` once; confirm item rights in BC.
8. One Windows rep: desk-memory notes show once in a buyer folder; the quote-log reminder shows on save.
9. GitHub: delete merged branches (`wip/ca-weekly-rep-review` first, it holds real data);
   turn on "Automatically delete head branches"; protect `main` with bypass off.
10. Folders-as-record follow-up: change the five files #89 lists (one is the managed `claudeMd`
    line, so another re-paste), and `ca-state-sales-grounding` in claude.ai.

## Follow-ups not yet dispatched

- Routing eval on `bc-quote-entry` (owed since #68; needs Claude credits).
- `models.json` refresh (stale since 2026-09-15).
- Review-side checker gaps: a plugin missing its `description`; canon strings in shipped `.html`.
- #77 non-blocking items: python ≥3.7 probe, interpreter-chain test, `python` wording.
- #84 inherited marker collision; #75 compact reset.
- Desk memory slice 3 (monthly roll-up and promotion) and slice 4 (stale notes).

## How the loop runs now

Workers start on Opus at medium. They report only to their parent session, never ask Parker
directly, and schedule nothing. Rex reviews review-only. The steward brings cleared PRs to
Parker, who merges in the GitHub UI. Sessions are archived when their PR merges or closes.

Owner: Parker Marshall. Written by the steward session, 2026-11-12.
