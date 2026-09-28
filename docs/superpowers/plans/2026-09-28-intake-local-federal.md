# Plan: log local/co-op and federal/prime quotes the way CA state quotes are logged

Spec: `docs/superpowers/specs/2026-09-28-intake-local-federal.md`. Each slice is one
session, on its own branch off `main`, and ends at a PR, not a merge. The reviewer did not
write it. "Rulings" means the numbered open rulings in the spec. A slice that depends on an
unruled item does not start; it does not guess.

Every slice's verification includes `python3 scripts/check_marketplace.py` at 0 FAIL. The
baseline on 2026-09-28 is 34 skills, 0 FAIL, 15 WARN.

---

## 0: Prerequisites (no code in this repo's behaviour)

**Do:**
- Draft a re-instantiation of the live `Customers/State of CA Agencies/CLAUDE.md` from
  `workspace/DESK-CLAUDE-template.md`, diffed against the live file. A person applies it on
  SharePoint. It removes `/ca-rfq-log`, `/ca-rfq-quote` and "OSDS SB/DVBE 2009473".
- Verify the signature-image path in `naspo-quote/SKILL.md:155` and
  `bbs-sales/README.md:134` (`vandenburg-sentinel-rfps`) against the live folder
  (`vandenberg-sentinel-rfps` per the 2026-09-28 read). If the live name differs, fix the
  pointer, not the folder.
- Put rulings 1–11 in front of Parker. Record each answer in `docs/STEWARD.md`, and put canon
  facts (rulings 3, 4, 5) in `canonical-facts.md`, one home each.

**Done:** live desk `CLAUDE.md` matches the template (confirmed by a rep reading it);
signature path resolves; rulings recorded, or explicitly still open.
**Blast radius:** the State desk's session context for every rep, which is today carrying a
false SB claim. The signature pointer is used on every state packet.
**Negative scope:** no folder renamed; no skill behaviour changed; canon gets only what
Parker actually ruled.
**Verification:** a rep opens a session in the State tree and the injected context
contains no SB claim; `Test-Path` on the signature file from a rep machine.

## 1: Desk roots as data; hooks read them

**Depends on:** ruling 1 (names) and ruling 2 (which Bechtel paths are desks). It can land
with the State entry only, then gain entries as rulings arrive.

**Do:**
- Add `plugins/bbs-sales/hooks/desk-roots.json` (schema in spec §4.3).
- `guard-tree.ps1` and `desk-context.ps1`: replace the `All RFQ's by Agency` literal with a
  segment match against the file. Near-duplicate siblings are compared from each desk's RFQ
  root. `desk-context` honours `quote_log` (per-buyer walk, or a fixed path) and prints the
  `DESK:` line pointing at canon.
- `hooks/tests/run-tests.ps1`: keep every existing case byte-for-byte. Add a fixture per desk:
  a rename denied inside `Federal Agencies`; a near-duplicate agency denied in `Local Agencies
  and Co-ops`; `FILLED/` immutable in a Bechtel deal folder; `Hanford_Bechtel` and
  `Bechtel - DOE` **not** matched as the `Bechtel` desk; the Sentinel program-level quote log
  injected; a folder outside every desk still gets nothing.

**Done:** all old and new tests pass; the State desk behaves identically.
**Blast radius:** every tool call on every rep machine (PreToolUse hook), and every session
start. A bug here blocks legitimate writes or silently stops guarding.
**Negative scope:** no desk-specific facts in the JSON (no contract numbers, BC numbers or
certs); no change to what the three guards forbid; no folders created.
**Verification:** `run-tests.ps1` under pwsh 7. Say in the PR that Windows PowerShell 5.1 is
unverified unless a rep machine runs it. Check the hook JSON on stdin with a path containing
an apostrophe (`All RFQ's`).

## 2: Create the local tree and the desk-root CLAUDE.md files

**Depends on:** ruling 1; ruling 3 for the local certification line; ruling 2 for Bechtel.

**Do:**
- Add per-channel desk templates beside `workspace/DESK-CLAUDE-template.md`, e.g.
  `DESK-CLAUDE-local-template.md` and `DESK-CLAUDE-federal-template.md`. Each carries its
  landmines and points at the canon certification row instead of restating it. The State
  template is unchanged.
- **A person** creates `Customers/Local Agencies and Co-ops/All RFQ's by Agency/` on
  SharePoint and places the desk `CLAUDE.md`. Claude drafts it. `Federal Agencies/` gets a
  desk `CLAUDE.md` if it has none (checked live first; never overwrite one).
- Bechtel: no change to its tree. If ruling 9 or 10 says so, draft the correction to the
  stale punch-out/margin lines in `sentinel/CLAUDE.md` for a person to apply.

**Done:** the local tree exists; each desk root has a `CLAUDE.md` that passes
`check_claude_md.py` (the federal one with no DVBE claim); a session opened in each desk gets
the right `DESK:` line.
**Blast radius:** SharePoint, where every synced machine receives the new folders; and the
context of sessions opened there.
**Negative scope:** no existing folder renamed, moved or reshaped; no `All RFQ's by Agency`
layer inserted into `Federal Agencies/`; no flat legacy folder touched.
**Verification:** `check_claude_md.py` on each template and each instantiated file; a live
folder listing after creation, read back through the connector.

## 3: Legacy inventory (read-only)

**Depends on:** nothing. Acting on it depends on ruling 11.

**Do:** list the roughly 200 flat `Customers/` folders and classify each as local, federal,
state-outside-tree, private, higher ed, or unknown. Mark candidates for "earlier history"
pointers. Deliver it to Parker as a document, not a change.

**Done:** Parker has the inventory. "Unknown" is a legitimate classification and is used
rather than guessed.
**Blast radius:** none (read).
**Negative scope:** **no moves, renames or new folders**; no pointer written until ruling 11.
**Verification:** folder count in the inventory equals the live listing count.

## 4: `rfq-intake` with channel profiles

**Depends on:** rulings 3, 4 and 5 for profile content. Where one is unruled, the profile
writes the `[FLAG: …]` the spec names, so the slice can land with flags in place.

**Do:**
- `git mv` `ca-rfq-intake` to `rfq-intake`. Move today's body into
  `references/channels/ca-state.md` **verbatim**, and assert that with a diff in the PR.
  Write `SKILL.md` as the channel-neutral steps plus the router: the document signal is
  required; domain and desk are corroborating; any disagreement stops; there is no default.
- Write `local-coop.md` and `federal-prime.md` from spec §3, as pointers only.
- `RFQ.md` template: add `Channel:` (with evidence) and `Certification basis:` (a canon
  pointer).
- Find-before-create searches the whole `Customers/` listing (spec §4.4).
- Repoint every pointer: `/ca-rfq`, `naspo-quote`, the desk templates, the README,
  `docs/evals/skills.json`, and the managed-settings `claudeMd` block if it names the skill.
  Frontmatter: `requires: [python3]`, `degrades-without: [microsoft-365, sales-crm]`.
- Remove the `rep_cockpit` "tracker of record" line only if ruling 7 says so; otherwise leave
  it and note it.

**Done:** `check_marketplace.py` 0 FAIL, with no surviving `ca-rfq-intake` pointer;
description under 1024 characters and quoted if it holds a colon; routing eval re-run and
committed; router test cases (below) pass by hand.
**Blast radius:** every state intake, since the CA profile is today's behaviour; and skill
selection for anything that sounds like "log this request".
**Negative scope:** no change to CA intake behaviour; no pricing, forms or email in intake;
`ca-form-filler` and `naspo-quote` descriptions untouched.
**Verification:** the CA-profile diff is empty against the old body. Router cases, each with
the expected result:
`sdcounty.ca.gov` + County letterhead gives local; `cdcr.ca.gov` + CDCR worksheet gives state;
`sandiego.gov` + City bid gives local; `usace.army.mil` gives federal;
a `bechtel.com` RFP gives federal/prime; "CAL FIRE/Riverside County Fire" letterhead with a
county PO **stops**; a bare email with no letterhead and a Gmail sender **stops**; a
`.edu` sender **stops** as out of scope. Routing eval: `docs/evals/discriminate.py
--workers 4` (needs Claude auth; if unavailable, say so in the PR and do not claim it).

## 5: `/rfq`, and the channel check in `/ca-rfq` Gate 0

**Depends on:** slice 4.

**Do:**
- `commands/rfq.md`: order and gates only. Route, intake, then for CA state enter `/ca-rfq`
  Gate 1. For local and federal, hand off with a named next skill (`grainger-pricing`,
  `bbs-sourcing`, `bbs-quote-builder`) and the forms list flagged for the rep. It checks
  `docs/STEWARD.md` *Already open for Parker* for rulings, not the empty `docs/PRODUCT.md`.
- `/ca-rfq` Gate 0: one added check. If the router says not-CA-state, stop and point to
  `/rfq`.

**Done:** a reviewer diffing `/rfq` against the skills it names finds no restated procedure;
`/ca-rfq` is otherwise byte-identical.
**Blast radius:** every `/ca-rfq` run passes through the new Gate 0 check.
**Negative scope:** no send step; nothing signs a federal or local form; `naspo-quote` is not
entered for non-state work.
**Verification:** the checker's retired-command and pointer checks pass; a dry walk of one
state and one federal request, by hand, recorded in the PR.

## 6: Email intake and found-but-not-logged

**Depends on:** slice 4.

**Do:** add the email mode to `rfq-intake` per spec §5: read a named thread; save
attachments into the synced tree; "what haven't I logged" over the rep's own mailbox, a named
window, business facts only, each item an offer to draft.

**Done:** the skill names only read tools (`outlook_email_search` plus the resource read)
and no send, move, label, forward or upload tool; `requires`/`degrades-without` are
accurate.
**Blast radius:** rep mailboxes, read-only.
**Negative scope:** no Routine, trigger or schedule; no other person's mailbox; nothing filed
without the rep choosing it; no sentiment or timing metrics.
**Verification:** grep the skill for `outlook_(send|forward|create_draft|move|modify|batch|trash)`
and `sharepoint_upload_file`, which should find nothing. The checker's dependency floor
passes.

## 7: CRM draft and report reconciliation

**Depends on:** rulings 6 and 8 for the channel marker and `bbs_lpa`. The interim
weekly-report note does not depend on them.

**Do:**
- `rfq-intake` §5 drafts the CRM block from spec §6.1. `bbs_quotevalue` unknown at intake
  becomes `[MISSING — NEEDS INPUT]`, never `0`. No `crm_update_record` call.
- `bbs-weekly-sales-report`: now, add the "Notes and data gaps" line that non-state records
  may be in the pipeline figures. After ruling 6, add the channel filter, anchored to where
  the ruling lives.
- The weekly rep review, when built, feeds new channels to its "other work" line. This slice
  only records that requirement in the review's brief/spec if it exists by then.

**Done:** a drafted block for one record in each channel, reviewed by a rep; weekly report
states the gap, or filters.
**Blast radius:** Parker's weekly form figures.
**Negative scope:** no CRM writes; no new CRM fields; `bbs_accepted` is not reinterpreted.
**Verification:** run the weekly report for the week of 2026-09-21 before and after. Pipeline
counts are unchanged until ruling 6, and the note is present.

## 8: Outcomes

**Depends on:** slice 4.

**Do:** in `rfq-intake` (and the quote-log template), say where Outcome is confirmed. A BC
`acceptedDate` or a converted order is read-only; the quote-log Outcome is updated by the rep.
Keep the quote-log columns unchanged. New rows use the BC SQ number.

**Done:** the template and skill agree with `bbs-weekly-sales-report`'s win rule, with no
second copy of it (pointer only).
**Blast radius:** win counts in reports.
**Negative scope:** does not fix the `900008` example or `bbs-quote-builder`'s 900001 series.
That touches the state path and is its own change.
**Verification:** the checker passes, and a reviewer finds the win rule stated once.

---

Owner: Parker Marshall. Written 2026-09-28.
