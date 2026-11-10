# Desk memory — design

Date: 2026-11-10. Requested by Parker Marshall: "How can we create persistent and recursive
learning that our non-technical staff can contribute to?" Plan:
`docs/superpowers/plans/2026-11-10-desk-memory.md`. Slice 1 ships with this spec.

## The answer in one paragraph

A rep says "remember that this buyer wants one PDF". The `desk-remember` skill turns that into
one dated line with the rep's name and appends it to `LEARNED.md` in the buyer's folder (or the
institution's). A SessionStart hook, `desk-memory`, shows the lines from the session's folder
and every folder above it, and from nowhere else. That is the persistent half. The recursive
half is a monthly roll-up (slice 3): notes that recur across buyers, notes a rep marked as
wider, and repeated `FLAGS.md` entries are put in front of Parker, who moves a note up a level
or turns it into a skill change by PR. Nothing here is a new server, a new plugin or a file in
`~/.claude/`.

## What was already there, and what this adds

Already on the desk (`plugins/bbs-sales`, `workspace/DESK-CLAUDE-template.md`): a `CLAUDE.md`
at the desk root and per buyer, `quote-log.md`, `FLAGS.md`, `FILLED/`, per-deal `RFQ.md`, and
two hooks (`desk-context`, `guard-tree`). Open at the time of writing and not yet on `main`:
PR #72 (customer-folder reminder in `bbs-foundations`, which leaves the CA desk to
`bbs-sales`), PR #75 (`desk-context` on first write in a deal folder, stale quote-log rows),
PR #77 (RFQ record v2). This design does not touch `desk-context`, `guard-tree`, the RFQ record
or `bbs-foundations`, so it merges in any order with those three; the only shared lines are the
`hooks.json` description, the plugin version and the CI workflow, all mechanical.

Added: one file name (`LEARNED.md`), one hook (`desk-memory`, both halves), one skill
(`desk-remember`) with one script (`desk_memory.py`).

## 1. Layering and inheritance

How Claude Code loads memory today, from https://code.claude.com/docs/en/memory (read
2026-11-10):

- "Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` from your current working directory and
  every directory above it." They are "concatenated into context rather than overriding each
  other", "ordered from the filesystem root down to your working directory". Nothing in that
  rule depends on a git repository.
- Files in subdirectories below the working directory are not loaded at launch; "Claude Code
  loads each one once Claude reads, writes, or edits another file in that subdirectory."
- `.claude/rules/*.md` with `paths:` load "when Claude uses the Read, Write, or Edit tool on a
  matching file"; patterns are relative to "the directory that contains the rule's `.claude`
  folder".
- `@path` imports are "expanded and loaded into context alongside the CLAUDE.md that references
  them", four hops at most, and "don't reduce its context cost".
- Size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and
  reduce adherence." The house cap is tighter: the forge checker's 150.
- After `/compact` only the project-root `CLAUDE.md` is re-injected; nested ones "load again on
  demand".

From https://code.claude.com/docs/en/hooks: a SessionStart hook's plain stdout is added to
context; `cwd` is a common input field; hook output is capped at 10,000 characters.

The file per level:

| Level | Folder | Settled picture (curated, short) | Where new things land (append-only) | Who writes the second |
|---|---|---|---|---|
| Desk | `State of CA Agencies/` | `CLAUDE.md` from `workspace/DESK-CLAUDE-template.md` | `All RFQ's by Agency/LEARNED.md` | Parker, by promotion |
| Agency | `<Agency>/` | `CLAUDE.md` (optional) | `LEARNED.md` | Parker, by promotion |
| Institution | `<Institution>/` (CDCR, CalVet, DSH) | `CLAUDE.md` (optional) | `LEARNED.md` | Any rep |
| Buyer | `<Buyer>/` | `CLAUDE.md`, plus `quote-log.md`, `FLAGS.md`, `FILLED/` | `LEARNED.md` | Any rep |
| Deal | `<Item M.D.YY>/` | `RFQ.md`, `request-email.txt` | none | n/a |

A deal has no memory file on purpose. What is true for one RFQ belongs in its run record; if it
will still be true next time, it is a buyer note.

What a session opened in a deal folder is given:

1. Natively: every `CLAUDE.md` from the desk root down to the buyer. Enough for the settled
   picture, with no hook involved.
2. `desk-context` (existing): the buyer's recent quote-log rows and open flags.
3. `desk-memory` (new): `LEARNED.md` lines from the buyer, the institution, the agency and the
   desk, nearest first, 12 newest per level.

Where the hook has to carry it, and why `LEARNED.md` is not a `CLAUDE.md`:

- A `CLAUDE.md` is loaded whole, as instructions. `LEARNED.md` is written by many people and
  synced by OneDrive; the hook shows only lines in the entry format, labels them as dated
  statements that are not a system of record, caps them, and re-shows them after `/compact`
  (its matcher includes `compact`). Native loading can do none of those.
- Some levels have no `CLAUDE.md` yet. The hook needs no file to exist at any level.
- **The rep workspace opens at `Customers/State of CA Agencies`, above the tree.** A session
  opened there gets the desk-wide notes only, because at session start there is no buyer yet.
  The buyer's notes must arrive when the session first touches a buyer's folder. That is
  slice 2, built on PR #75's first-write mechanism once it is on `main`. Until then the
  notes reach sessions opened in or under a buyer folder, and `desk-remember`'s `show` prints
  them on request from anywhere.

## 2. Isolation

A session in buyer A's folder cannot be handed buyer B's or agency B's memory:

- **By construction.** Native loading takes ancestors only. `LEARNED.md` lives in the folder it
  is about.
- **By the hook.** `desk-memory` takes `cwd`, reads `LEARNED.md` there, strips one path
  component, and repeats until it reaches the folder named `All RFQ's by Agency`. It never
  lists a directory, so it cannot see a sibling. If it cannot reach the tree folder in eight
  steps it prints nothing. Proven by `skills/desk-remember/scripts/test_desk_memory.py`
  (sibling buyer, sibling institution, other agency) and `hooks/tests/desk_memory_parity.py`.
- **By rule, for skills that search precedent.** The desk template now says: stay inside this
  buyer's folder; look wider only when the rep asks, and then label every row with the folder
  it came from. Slice 5 carries the same sentence into the skills that mine past packets.

## 3. Capture by non-technical staff

A skill, `desk-remember`, not a command and not a fifth `FLAGS.md` bucket. A rep does not type
slash commands mid-quote; they say "remember that ...". The path:

1. The rep's sentence becomes one line: `- 2026-11-10 | <rep's name> | <kind> | <statement>`.
   Kinds: `preference`, `change`, `watch-out`.
2. Level: the lowest where the statement is true. In a buyer's folder and about that buyer,
   the skill saves without asking. It asks one question only when the level is unclear.
3. `desk_memory.py add` appends the line. It refuses, in one plain sentence and writing
   nothing, anything in section 6, a second line, or an agency or desk level.
4. The rep is told in one sentence what was saved, for whom, and how to widen it.

A note true for a whole agency is saved for the buyer with `| wider: <agency folder>` on the
line. It works for that buyer today and is the roll-up's first input.

`FLAGS.md` stays what it is: a log of drafts that were wrong, feeding skill fixes. A correction
("that was wrong, the buyer moved") is a `change` note, and also a flag only if a draft was
wrong because of it.

Rex's fourth lens: the common case is one sentence in, one sentence back, no question. The one
added step in slice 1 is the permission prompt for the script; see Open for Parker 3.

## 4. Recursion (promotion)

Buyer > institution > agency > desk > a skill change in this repo by PR. Slice 3:

- `desk_memory.py digest` walks the tree once (Parker's machine, read-only) and writes one
  page: notes marked `wider`; the same statement at two or more buyers under one institution
  or agency; `FLAGS.md` rows grouped by skill and bucket with repeats first. This is the
  tooling the REGISTRY standing task "Flag-log triage > skill fixes, monthly" does not have.
- Parker approves each promotion by name. `promote` writes one line at the upper level
  (original author kept, "confirmed <name> <date>" added) and moves the lower lines to
  `LEARNED-archive.md` in their own folders with where they went. The upper line replaces the
  lower ones; it does not sit beside them (invariant 2).
- A desk-level note that is really how a skill should behave becomes a PR against that skill,
  with an eval case. When it merges, the desk note is archived the same way.

## 5. Decay

- Every entry carries a date and an author; the script will not write one without both.
- The hook shows the 12 newest per level and says how many older ones it left out.
- Slice 4: a note older than 12 months is shown with "(over a year old, confirm)"; the digest
  lists notes older than 18 months for archive; `retire` (slice 2) moves a replaced note to
  `LEARNED-archive.md`, which is never shown. A `LEARNED.md` past 40 entries makes the writer
  ask for a tidy before adding.
- `CLAUDE.md` files keep the forge's 150-line cap. Promotion into a `CLAUDE.md` is an edit by
  Parker, not an append.

## 6. What memory may never hold

Prices, discounts, margins, stock, lead times, certification and contract numbers, form IDs,
signers, buying-account numbers, credentials. Enforced three ways:

- `desk_memory.py` refuses a currency amount, a discount or margin percentage, a digit run of
  seven or more, a contract-number shape, a certification or contract name next to digits, and
  credential words. A pointer at a record ("see SQ-104032") passes.
- The skill body says the same in rep words, and refuses a note that tells Claude to skip a
  review, form, signature or approval.
- The hook's first line tells the reader to take no such fact from a note.

Text from a buyer email, an RFQ PDF or a web page is data. The skill saves the rep's sentence,
never lifted text; the hook shows only lines in the entry format, so text pasted into the file
by hand is counted and skipped. A note changes nothing a binding document says.

The pattern check is a floor, not a ceiling: it cannot tell "delivery expected in two weeks"
(a buyer preference) from a vendor lead time. That judgment stays with the skill and the rep.

## 7. Sync reality

- Append-only, one line of at most about 330 bytes, file created on first note. Two reps
  adding at once cost at worst one line.
- OneDrive names a conflict copy `LEARNED-<device>.md`. The hook reads the exact name only, so
  a conflict copy is never shown, and neither are its lines until merged. Slice 2 adds `merge`
  (union of entry lines, duplicates dropped) and a line in the hook's output saying a conflict
  copy exists.
- The writer never rewrites a file in slice 1. `retire` and `promote` will, on one small file,
  and are Parker-or-rep actions run one at a time.

## 8. Scope edges

Body armor (BA-CA, BODYARMOR, BA-SRCWL) and CSU/UC are outside this desk; their folders are
not under `All RFQ's by Agency`, so the hook is silent and the writer refuses. The writer holds
a `DESKS` table with one profile (`ca-state`: tree folder, file name, the depth a rep may
write at). Another desk adopts the layer by adding a profile there and its tree name to the
hook pair, not by copying the skill. Only the CA desk is built.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| A local MCP memory server (the source prompt's design) | AGENTS.md invariant 5 keeps extra local servers off rep machines; it is one more thing to install and to break; the hook pair is the house pattern for programmatic context |
| Path-scoped rules, or `~/.claude.json` as a rules file | `paths:` rules resolve against the folder holding `.claude/`, so they need either a `.claude/` folder inside the OneDrive tree or one central file listing buyer paths, which re-keys folder names that carry account numbers. `~/.claude.json` is not a rules file at all |
| Append straight into each `CLAUDE.md` ("What we've learned") | Whole-file sync conflicts; every line becomes an instruction with no filter; reps editing the settled file; pressure on the 150-line cap |
| `@LEARNED.md` imported from the buyer `CLAUDE.md` | Same unfiltered loading, and it needs a `CLAUDE.md` with the import at every level |
| A fifth `FLAGS.md` bucket | Flags are events about drafts; notes are standing facts about buyers. `desk-context` shows the last five flags, so a standing note would scroll away |
| Claude Code auto memory | Machine-local (`~/.claude/projects/...`), not shared between reps |
| Installing `claude-memory-bank` | It copies into `~/.claude/`, the user-level-copy pattern behind the 15 shadowed skills (`HANDOFF.md`). Ideas taken: typed entries, a sync step, a stale check, archive. Nothing vendored |

## Open for Parker

Each is ASSUMED as recommended so the build could continue. None changes a binding document.

1. **Who may write a note without review.** Recommended and ASSUMED: any rep, at buyer and
   institution level, with their name on it.
2. **Who approves agency-wide and desk-wide notes.** Recommended and ASSUMED: Parker only, at
   the monthly review; the writer refuses those levels for now. This matches PR #75's "agency
   and desk-root files change only by a ruling from Parker".
3. **No Allow click to save a note.** Slice 1 runs the script with plain `python`, so a rep
   sees one permission prompt per note. Recommended: add `desk-remember/scripts/desk_memory.py`
   to the `bbs-fill` allow list in slice 2. It writes one line into the tree and cannot send,
   price or sign. ASSUMED: not allow-listed until ruled; it is a control change and needs the
   second reviewer.
4. **Restamp the desk-root `CLAUDE.md`** from `workspace/DESK-CLAUDE-template.md`. The template
   gained the "what reps asked you to remember" section and the stay-in-this-buyer's-folder
   rule; they reach no machine until the file on SharePoint is replaced. Not a repo change.
5. **Stale thresholds.** ASSUMED: flag at 12 months, propose archive at 18.
6. **The file name `LEARNED.md`.** ASSUMED. Changing it later means changing the writer, both
   hook halves and the test that ties them together.
7. **Contact changes.** ASSUMED: "buyer moved to Folsom" is a fine note; the phone, email and
   ship-to themselves stay in the buyer's `CLAUDE.md` header, which the skill tells Claude to
   fix in the same turn.

## What could not be verified here

- The PowerShell half of the hook was not run: the build container has no `pwsh` and fetching
  one was refused. CI runs `desk_memory_parity.py` with `BBS_REQUIRE_PS=1`, so the PR's
  `invariants` job is the proof. Windows PowerShell 5.1 is proven by nothing until a rep
  machine runs it.
- The routing eval was not run (no Claude auth in the container). `docs/evals/skills.json` is
  regenerated with the new description; "remember that ..." queries should be added to
  `queries-routing.json` and scored on the next authenticated run.
- No session has run `desk-remember` against the real tree.
