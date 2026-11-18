# BBS Sales System — Plan 1: Rulings and Desk Registry

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the rulings the BBS Sales System rests on (spec slice S0), then replace the hard-coded `All RFQ's by Agency` tree with one desk registry that every bbs-sales hook and script reads (slice S2). CA behaviour must stay byte-identical.

**Architecture:** A JSON registry (`references/desks.json`) holds desk profiles. One loader per language (`scripts/desks.py`, `scripts/Desks.ps1`) reads it and finds a desk root inside a path. If the registry is missing or broken, the loader falls back to a built-in copy of the CA profile, so CA protection never drops. Every hook twin, `rfq_record.py` and `desk_memory.py` call the loader instead of a `TREE` literal. The registry ships with `ca-state` only; a synthetic second desk in a test fixture proves every hook honours whatever the registry says.

**Tech Stack:** Python 3 stdlib; PowerShell 5.1 + 7 (twins); POSIX sh (`desk-post.sh`); existing parity harnesses; `scripts/check_marketplace.py`.

**Spec:** `docs/superpowers/specs/2026-11-16-bbs-sales-system-design.md` (approved by Parker, 2026-11-17).

## Plan roadmap (later plans are written when their turn comes)

| Plan | Spec slices | Prerequisite | What |
|---|---|---|---|
| **1 (this)** | S0, S2 | — | Rulings PR; desk registry and loaders, CA byte-identical |
| 2 | S3, S4 | Plan 1 merged; #96 merged | #100 reworked onto the registry (`bechtel-sentinel` profile with `near_duplicate: false`, desk-learn reads the registry); weekly-report branch reads the registry for its desk list |
| 3 | S5 | Mail rule live ~2 weeks; Entra app + access policy; Archive Quotes = Always | Two-desk proof: a read-only join script (BC quote → sent metadata → exact-quote-number PO → deal record), join rate per desk |
| 4 | S6 | Plan 2 | Schema v3, customer bindings + `bind-desk`, `rfq-intake` + `/rfq`, `bc-quote-entry` writes `BC quote` + `quote built`, Sentinel adopts `RFQ.md` |
| 5 | S7 | Plan 4 | Outcome engine, `/rfq-fold`, privacy-gate card class, Tier 1 shadow |
| 6 | S8 | Plan 5 | Cross-desk dashboard |
| 7 | S9 | Plan 4 (+ O2 ruling) | Pricing loop |
| 8 | S10 | Plan 4 | Learning loop on every desk |
| — | — | — | CSU/UC order desk: its own design (session `design-the-csu-uc-order`) |

## Global Constraints

- Every hook ships as Python and PowerShell twins with a parity test, and the PowerShell half runs on 5.1 and 7 (no `?.`, no ternary, no `-AsHashtable`).
- Stdlib only in Python; no new dependencies anywhere.
- **CA behaviour byte-identical:** every existing test passes with no edits to its expectations: `hooks/tests/parity.py`, `hooks/tests/run-tests.ps1`, `hooks/tests/desk_memory_parity.py`, `hooks/tests/fill_gate_parity.py`, `scripts/tests/*`, `skills/desk-remember/scripts/test_desk_memory.py`.
- A changed plugin bumps its `plugin.json` version in the same PR. Check open PRs (#96 bumps bbs-sales) and claim the next free number.
- Draft PRs only, at most five open. `rex` reviews; only Parker merges, in the GitHub UI. No agent takes a PR out of draft.
- Rulings live in `docs/STEWARD.md`. Desk facts (cert channel, salesperson, forms) are never values in the registry. No buying-account number, certificate number or API key is written anywhere.
- Never rename or move a customer folder. Tests write only inside temp dirs.
- Work in a **git worktree**, not the main checkout: the CSU/UC design session (`design-the-csu-uc-order`) shares `/Users/parkermarshall/bbs-claude-marketplace`. Never touch `docs/superpowers/specs/*csu-uc*`.

## Review Focus

1. **Registry missing, unreadable, or invalid JSON** (a half-saved edit, an OneDrive conflict copy): every hook keeps CA protection through the built-in fallback, and the SessionStart desk-context output says once that the registry was unreadable. Pinned in Task 5 (`test_load_invalid_json_falls_back`) and Task 8 (`registry_error_line`).
2. **Windows paths** (`C:\…\All RFQ's by Agency\…`, mixed `\` and `/`): match exactly as forward-slash paths do, in both languages. Pinned in Task 5 (`test_find_backslash_path`) and Task 6 (parity cases).
3. **A path naming the root twice, or a decoy folder whose name contains it** (`Old All RFQ's by Agency backup/All RFQ's by Agency/…`): today's substring, leftmost behaviour is kept. Pinned in Task 5 (`test_find_all_two_occurrences`, `test_find_leftmost`).
4. **Non-ASCII characters in a path** (é and ñ in buyer names; Unicode case-fold oddities): Python and PowerShell agree. Pinned in Task 6 (parity cases with `Peñasquitos` and `K`, the Kelvin sign).
5. **Two desks whose roots overlap or nest** (a future `Bechtel` root vs `Bechtel/sentinel`): deterministic — leftmost start wins, and on a tie the longer root wins. Pinned in Task 5 (`test_find_overlap_prefers_longest`).

---

## Part A — Rulings PR (spec S0)

Branch: `docs/sales-system-rulings`, cut from `origin/main`, in a worktree:

```bash
git -C /Users/parkermarshall/bbs-claude-marketplace fetch origin
git -C /Users/parkermarshall/bbs-claude-marketplace worktree add ../bbs-mkt-sales-rulings -b docs/sales-system-rulings origin/main
```

Copy into the worktree, unchanged:
- `docs/superpowers/specs/2026-11-16-bbs-sales-system-design.md`
- this plan

Both currently sit untracked in the main checkout.

### Task 1: Record the rulings in the STEWARD register

**Files:**
- Modify: `docs/STEWARD.md`. Append to the register, after the last dated entry (currently "Rachelle does not sign through Claude — RULED 2026-10-02", ~line 1196), in the register's unnumbered `- **Title — RULED date.**` style.

**Interfaces:**
- Produces: register entries that Part B, Plans 2–8 and `rex` cite by title.

- [ ] **Step 1: Append these entries verbatim.** The quoted strings are Parker's own words or the option labels he selected in session.

```markdown
- **BBS Sales System: one desk model for every customer — RULED 2026-11-16.** Parker, in
  session; design `docs/superpowers/specs/2026-11-16-bbs-sales-system-design.md`, approved
  2026-11-17 ("Approve design"). Records here the program decisions D10.1–D10.5 kept in
  `Customers/State of CA Agencies/sales-process/docs/pm/DECISIONS.md`:
  - folders plus interactive dashboards are the target;
  - one desk model, rolled out by desk profile;
  - reps update the CRM (D10.1);
  - a desk that declares a profile may keep a hand-kept outcome record, and Sentinel's
    `learning/quote-log.md` is that desk's (D10.5, amends R6);
  - agents in the CA tree always use and update `desk-remember`.
- **Quote-sent capture is an Exchange mail flow rule — RULED 2026-11-16.** Parker: "Exchange
  mail rule". Outbound mail carrying a BC sales-quote PDF is copied to one logging mailbox.
  Parker creates the rule.
- **The logging mailbox is read metadata only — RULED 2026-11-16.** Parker: "Metadata only".
  - A script on Parker's Mac keeps sender, buyer domain, sent timestamp and quote number.
  - Bodies and attachments are never stored or read by Claude.
  - Retention is about 90 days.
  - For this mailbox only, this supersedes 2026-10-30 spec §13.8 item 1 and 2026-11-12 spec §7.
- **A Tier 1 PO match becomes Won after a shadow bar — RULED 2026-11-16.** Parker: "Auto after
  it proves out".
  - Tier 1 means the PO cites our quote number and the customer and pre-tax total check out.
  - It runs in shadow until the matcher is at least 95% precise on 30 or more cases. Then it
    counts as Won automatically, and the rep can undo it.
  - Weaker matches always need a rep's confirmation.
  - Amends canon "What counts as a win" and METRICS-SIGNOFF Q-A.
- **Sentinel adopts RFQ.md for new RFQs — RULED 2026-11-16.** Parker: "Yes, new RFQs onward".
  - Sentinel's dashboard data is built from those records.
  - The tracker xlsx, hand indexes and stage JSON collapse into one store.
  - Existing RFQs are untouched.
- **Folders are the RFQ working record for every customer — RULED 2026-11-16.** Parker: "Yes,
  CRM until a switch". Reps keep updating the CRM until each desk passes a parity switch (two
  straight weeks where folder sent and CRM Submitted agree within 1 per rep per week, with ≥90%
  of in-scope deals carrying a sent date). Then CRM entry stops for that desk. Amends
  canon "Systems of record" (2026-11-12, CA state only).
- **Build approach: extend in place — RULED 2026-11-16.** Parker: "Extend in place". The outcome
  engine runs as a routine on Parker's Mac.
- **CSU/UC and body armor are not in the first build — RULED 2026-11-17.** Parker: "I want to
  integrate Joey's down the line for CSU/UC. That is a very recurring order based system and
  does not have the system type of RFQ basis." CSU/UC gets its own order-desk design. Body armor
  is out unless Parker says otherwise.
```

- [ ] **Step 2: Verify the register parses and nothing else moved**

Run: `git diff --stat docs/STEWARD.md && python3 scripts/check_marketplace.py`
Expected: only `docs/STEWARD.md` changed (additions only); the checker exits 0.

### Task 2: Amend canon

**Files:**
- Modify: `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`
  - "Systems of record" table: the row beginning `California state RFQ working state` (~line 146) and the row beginning `Outreach, federal and local pipeline` (~line 147)
  - "What counts as a win" (~lines 184–199)
- Modify: `plugins/bbs-foundations/.claude-plugin/plugin.json` (version, currently `0.5.7` → next free)

- [ ] **Step 1: Replace the two systems-of-record rows with these rows:**

```markdown
| RFQ working state, sent and outcome included, for every desk in bbs-sales `references/desks.json` | **Deal folders** (`RFQ.md`, the desk's `quote-log.md`); `RFQ.md` is written only through `rfq_record.py` | Ruled 2026-11-12 for California state; extended to every profiled desk 2026-11-16 (STEWARD: "Folders are the RFQ working record for every customer"). Where reps already keep `bbs_rfqs` (California state today) the Sales CRM stays a cross-check and the count source until that desk's switch; desks with no `bbs_rfqs` history are folder-only |
| Outreach and pre-RFQ pipeline | Dynamics 365 Sales | RFQ working state left Dynamics for every profiled desk, 2026-11-16 |
```

- [ ] **Step 2: In "What counts as a win", replace the first bullet with:**

```markdown
- **A win is confirmed by Business Central** — a sales quote with an `acceptedDate`, or a
  quote converted to a sales order — **or by a quote-log Outcome of *won* that the rep has
  confirmed, or by a Tier 1 PO match once the matcher has passed its shadow bar** (≥95%
  precise on ≥30 cases, signed by Parker; STEWARD: "A Tier 1 PO match becomes Won after a
  shadow bar", 2026-11-16). Until that bar is signed, a Tier 1 match is a proposal the rep
  folds. Nothing else is a win.
```

- [ ] **Step 3: Bump the bbs-foundations version; run the checks**

Run: `python3 scripts/check_marketplace.py && python3 scripts/check_marketplace.py --requirements`
Expected: both exit 0.

### Task 3: Draft the managed-settings and org-instruction texts

**Files:**
- Modify: `plugins/bbs-foundations/docs/bbs-managed-settings.json`, the `claudeMd` string
- Modify: `plugins/bbs-foundations/docs/MANAGED-SETTINGS.md`, adding a "Pending paste" section

- [ ] **Step 1: In the `claudeMd` string,**
  - replace the sentence fragment `on the CA desk they live in quote-log.md; outside it there is no quote-log yet, the Business Central sales quote is the record, and no outcome file is created by hand.` with
    `they live in each profiled desk's quote-log.md (bbs-sales references/desks.json), appended through rfq_record.py; a folder with no desk profile has no outcome file, and none is created by hand.`
  - In the "Systems of record" bullet, add `RFQ working state for every profiled desk: deal folders (RFQ.md via rfq_record.py).`
  - Keep the JSON valid. Escape quotes exactly as the surrounding string does.

- [ ] **Step 2: Add to `MANAGED-SETTINGS.md`** a `## Pending paste (2026-11-17)` section. It holds:
  - one line saying the `claudeMd` change above awaits Parker's redeploy;
  - the organization-instruction text below, for Parker to paste into the claude.ai org settings himself.

```text
- Mail, files, and CRM access are the signed-in person's. Do not imply you can see a
  teammate's mailbox. One exception (Parker, 2026-11-16): the quote-sent logging mailbox is
  read metadata-only (sender, buyer domain, timestamp, quote number) by the outcome engine on
  Parker's Mac; no session reads its bodies or attachments.
```

- [ ] **Step 3: Validate**

Run: `python3 -c "import json,sys; json.load(open('plugins/bbs-foundations/docs/bbs-managed-settings.json'))" && python3 scripts/check_marketplace.py`
Expected: no output from the first command; the checker exits 0.

### Task 4: Commit and open the rulings PR

- [ ] **Step 1: Commit**

```bash
git add docs/STEWARD.md docs/superpowers/specs/2026-11-16-bbs-sales-system-design.md \
  docs/superpowers/plans/2026-11-17-bbs-sales-system-plan-1-rulings-and-registry.md \
  plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md \
  plugins/bbs-foundations/.claude-plugin/plugin.json \
  plugins/bbs-foundations/docs/bbs-managed-settings.json plugins/bbs-foundations/docs/MANAGED-SETTINGS.md
git commit -m "docs(rulings): BBS Sales System rulings, design and plan 1 (S0)"
```

- [ ] **Step 2: Open the draft PR, only if fewer than five PRs are open.**
  - Run `gh pr list --state open --json number --jq length` first.
  - If the result is 5 or more, stop. Hand Parker the branch name and wait.
  - The PR body ends with the attribution line, and says that Parker re-pastes managed settings and org instructions after merge.

---

## Part B — Desk registry (spec S2)

**Base:** `origin/main` **after #96 merges** (#96 rewrites `set_stage` in `rfq_record.py`). Branch `feat/desk-registry`, in a worktree:

```bash
git -C /Users/parkermarshall/bbs-claude-marketplace worktree add ../bbs-mkt-desk-registry -b feat/desk-registry origin/main
```

All paths below are relative to `plugins/bbs-sales/` unless they start with `scripts/check_marketplace.py` or `.github/`.

### Task 5: Registry file and the Python loader

**Files:**
- Create: `references/desks.json`
- Create: `references/desks.md` (human doc for the registry. The unpushed weekly-report branch's `references/desk-profile.md` covers *reporting* keys; Plan 2 links the two, so do not create `desk-profile.md` here.)
- Create: `scripts/desks.py`
- Test: `scripts/tests/test_desks.py`, plus fixture `scripts/tests/fixtures/desks-two.json`

**Interfaces:**
- Produces (`scripts/desks.py`):
  - `REGISTRY_ENV = "BBS_DESKS_FILE"`: an env override; tests point it at fixtures.
  - `FALLBACK: list[dict]`: the built-in `ca-state` profile, equal to the `desks.json` entry. The checker enforces equality (Task 10). This is the only other copy of the root string.
  - `registry_path() -> str`: `$BBS_DESKS_FILE` if set, else `<plugin root>/references/desks.json`, resolved from `__file__`.
  - `load(path: str | None = None) -> tuple[list[dict], str | None]`: returns `(desks, error)`. On a missing file, unreadable file, invalid JSON, or schema failure it returns `(FALLBACK, "<one-line reason>")`, and it never raises.
  - `class Match(NamedTuple): desk: dict; root: str; start: int; end: int`
  - `find(path: str, desks: list[dict]) -> Match | None`
    - Search the path with `\` → `/` (length-preserving), for each root of each `kind == "rfq"` desk.
    - Matching is case-insensitive ASCII: `re.compile(re.escape(root.replace("\\", "/")), re.I | re.A)`.
    - The result is the leftmost match; on a tie, the longest root.
  - `find_all(path: str, desks: list[dict]) -> list[Match]`: every non-overlapping match, ordered by start.

`references/desks.json`, exactly:

```json
{
  "schema_version": 1,
  "desks": [
    {
      "desk_id": "ca-state",
      "kind": "rfq",
      "roots": ["All RFQ's by Agency"],
      "deal_depth": [2, 3],
      "deal_name_rule": "date",
      "rep_min_depth": 2,
      "guard": {"no_rename": true, "near_duplicate": true, "filled_immutable": true},
      "record_profile": "ca-v2"
    }
  ]
}
```

Schema rules that `load` enforces and Task 10's checker repeats:
- `schema_version == 1`;
- every desk has exactly the eight keys above;
- `desk_id` matches `^[a-z][a-z0-9-]*$` and is unique;
- `kind` is `rfq` or `order`;
- `roots` is a non-empty list of non-empty strings;
- `deal_depth` is `[min, max]` with `1 ≤ min ≤ max`;
- `deal_name_rule` is `date` (the only rule this plan supports);
- `rep_min_depth` is an int ≥ 1;
- `guard` holds those three booleans.

`scripts/tests/fixtures/desks-two.json` is `desks.json` plus a second desk: `desk_id: "test-desk"`, `roots: ["Synthetic Desk Root"]`, `guard.near_duplicate: false`, everything else as `ca-state`.

- [ ] **Step 1: Write the failing tests** in `scripts/tests/test_desks.py` (unittest, matching the folder's style):

```python
def test_default_registry_has_ca_state(self):
    desks, err = desks_mod.load()
    self.assertIsNone(err)
    self.assertEqual([d["desk_id"] for d in desks], ["ca-state"])
    self.assertEqual(desks[0]["roots"], ["All RFQ's by Agency"])

def test_fallback_equals_registry(self):
    desks, _ = desks_mod.load()
    self.assertEqual(desks_mod.FALLBACK, desks)

def test_env_override(self):          # BBS_DESKS_FILE -> fixtures/desks-two.json
    self.assertEqual([d["desk_id"] for d in desks], ["ca-state", "test-desk"])

def test_load_invalid_json_falls_back(self):   # file containing '{"desks": ['
    desks, err = desks_mod.load(bad)
    self.assertEqual(desks, desks_mod.FALLBACK)
    self.assertIn("desks.json", err)    # reason names the file

def test_load_missing_file_falls_back(self): ...   # same assertions, err mentions "not found"
def test_load_schema_error_falls_back(self): ...   # kind "deal" -> err mentions "kind"

def test_find_case_insensitive(self):
    m = desks_mod.find("/x/all rfq's BY AGENCY/CDCR/Buyer/a.md", desks)
    self.assertEqual((m.desk["desk_id"], m.root, m.start), ("ca-state", "All RFQ's by Agency", 3))

def test_find_backslash_path(self):
    m = desks_mod.find("C:\\Desk\\All RFQ's by Agency\\A\\B\\x.md", desks)
    self.assertEqual(m.start, 8)

def test_find_none_outside(self):
    self.assertIsNone(desks_mod.find("/x/Customers/Bechtel/sentinel/a.md", desks))

def test_find_leftmost(self):
    p = "/x/Old All RFQ's by Agency backup/All RFQ's by Agency/a.md"
    self.assertEqual(desks_mod.find(p, desks).start, 7)

def test_find_all_two_occurrences(self):
    self.assertEqual([m.start for m in desks_mod.find_all(p, desks)], [7, 34])

def test_find_overlap_prefers_longest(self):   # inline registry roots ["Bechtel", "Bechtel/sentinel"]
    self.assertEqual(desks_mod.find("/C/Bechtel/sentinel/x", reg).root, "Bechtel/sentinel")

def test_order_desks_never_match(self):        # inline registry with kind "order"
    self.assertIsNone(desks_mod.find("/x/BBS CSU UC/a", reg))
```

- [ ] **Step 2: Run the tests; confirm they fail**

Run: `python3 -m unittest plugins/bbs-sales/scripts/tests/test_desks.py -v`
Expected: FAIL / ERROR, `No module named 'desks'`.

- [ ] **Step 3: Write `references/desks.json`, the fixture, and `scripts/desks.py`** to the interfaces above. Then write `references/desks.md`:
  - one table, one row per key, each row saying what reads the key;
  - the rule "a profile is a PR; customer bindings arrive in Plan 4";
  - the fallback behaviour.

- [ ] **Step 4: Run the tests; confirm they pass**

Run: `python3 -m unittest plugins/bbs-sales/scripts/tests/test_desks.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit** `feat(bbs-sales): desk registry and Python loader`

### Task 6: The PowerShell loader and loader parity

**Files:**
- Create: `scripts/Desks.ps1` (dot-sourced)
- Test: `hooks/tests/desks_parity.py`

**Interfaces:**
- Consumes: `references/desks.json`, and `FALLBACK` from Task 5 (the PS fallback must equal it; Task 10 checks).
- Produces (`scripts/Desks.ps1`, PS 5.1-safe):
  - `Get-BbsDeskRegistryPath` → `[string]`: honours `$env:BBS_DESKS_FILE`, else `Join-Path $PSScriptRoot '..\references\desks.json'`, normalised.
  - `Get-BbsDesks [-Path <string>]` → `[pscustomobject]@{ Desks = <object[]>; Error = <string or $null> }`. Same fallback and schema rules as `load`.
  - `Find-BbsDeskRoot -Path <string> -Desks <object[]>` → `[pscustomobject]@{ Desk; Root; Start; End }` or `$null`.
  - `Find-BbsDeskRootAll -Path <string> -Desks <object[]>` → `object[]`.
  - Use the call `desk-context.ps1` already uses for `$TREE`, `[regex]::Matches(..., [regex]::Escape(...), $ICASE)`, with `$ICASE` defined as it is there, on `$Path.Replace('\','/')`.

- [ ] **Step 1: Write `hooks/tests/desks_parity.py`.**
  - It runs `scripts/desks.py` (through a tiny `python3 -c` driver) and `Desks.ps1` (through `pwsh -Command ". ./scripts/Desks.ps1; …"`) over the same case list, and compares JSON `{desk_id, root, start, end}` or `null`.
  - It skips the PS half when no pwsh/powershell is found, unless `BBS_REQUIRE_PS=1` (the same contract as `parity.py`).
  - Cases:
    - every path from Task 5's find tests;
    - `C:/Desk/All RFQ's by Agency/Peñasquitos/Juan Núñez/a.md`;
    - a path containing `K` (U+212A) before the root;
    - an empty string;
    - the registry overrides `desks-two.json` and an invalid-JSON file, comparing `Error is null` vs non-null.
- [ ] **Step 2: Run it; confirm it fails**

Run: `BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desks_parity.py`
Expected: FAIL, because `Desks.ps1` does not exist.

- [ ] **Step 3: Write `scripts/Desks.ps1`** to the interface.
- [ ] **Step 4: Run it; confirm it passes**

Run: `BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desks_parity.py`
Expected: `all pass`, exit 0.

- [ ] **Step 5: Commit** `feat(bbs-sales): PowerShell desk loader with parity test`

### Task 7: guard-tree on the registry

**Files:**
- Modify: `hooks/guard-tree.py` (remove `TREE` at :23; `near_duplicate` :99–131; `main` :134–213)
- Modify: `hooks/guard-tree.ps1` (remove `$TREE` at :14 and its uses)
- Test: `hooks/tests/parity.py` (add cases), `hooks/tests/run-tests.ps1` (add the same cases)

**Interfaces:**
- Consumes: `desks.load`, `desks.find`, `Match` (Task 5); `Get-BbsDesks`, `Find-BbsDeskRoot` (Task 6). Python imports through `sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))`. PowerShell dot-sources `. (Join-Path $PSScriptRoot '..\scripts\Desks.ps1')`.
- Behaviour:
  - Every `TREE` test becomes "`find()` returns a match".
  - Every message that interpolated `TREE` interpolates `match.root`, so CA messages are byte-identical.
  - The rename deny applies only when the matched desk's `guard.no_rename` is true; the FILLED/ checks only when `guard.filled_immutable`; the near-duplicate check only when `guard.near_duplicate`.
  - `near_duplicate(path)` takes the match: the root dir is `path[:m.end]`, the rest is `path[m.end:]`.
  - The `mkdir` quoted-target regex uses `re.escape(m.root)` for the root that `find` matched on the command string.

- [ ] **Step 1: Add the synthetic-desk cases to `parity.py` and `run-tests.ps1`.** With `BBS_DESKS_FILE` pointing at `fixtures/desks-two.json`:
  - a `mv` inside `Synthetic Desk Root/A/B` is denied, and the reason contains `inside 'Synthetic Desk Root'`;
  - creating a folder `Synthetic Desk Root/A/Buyerr` beside an existing `Synthetic Desk Root/A/Buyer` is **allowed** (`near_duplicate: false`);
  - a Write to an existing `Synthetic Desk Root/A/B/FILLED/p.pdf` is denied;
  - with the default registry, the same `mv` is allowed (silent), because the synthetic root is not a desk.
- [ ] **Step 2: Run them; confirm the new cases fail and the old cases pass**

Run: `BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/parity.py; pwsh -NoProfile -File plugins/bbs-sales/hooks/tests/run-tests.ps1`
Expected: only the four new cases fail.

- [ ] **Step 3: Convert both twins** to the behaviour above.
- [ ] **Step 4: Run the same commands; confirm everything passes**
- [ ] **Step 5: Commit** `refactor(bbs-sales): guard-tree reads the desk registry`

### Task 8: desk-context and desk-memory on the registry

**Files:**
- Modify: `hooks/desk-context.py`:
  - `TREE` :30, `TREE_RE` :48;
  - `session_start` :183: the registry-error line goes here;
  - `locate` :205: the depth comes from `desk["deal_depth"]`;
  - `memory_first_touch` :299–312.
- Modify: `hooks/desk-context.ps1` (the same functions; `$TREE` :22, :172, :189, :312)
- Modify: `hooks/desk-memory.py` (`TREE` :37, `TREE_RE` :51, `chain` :161, `touched` :199)
- Modify: `hooks/desk-memory.ps1` (the same; `$TREE` :30)
- Test: `hooks/tests/parity.py`, `hooks/tests/desk_memory_parity.py`, `hooks/tests/run-tests.ps1` (add cases)

**Interfaces:**
- Consumes: Tasks 5–6.
- Behaviour:
  - Every `TREE`/`TREE_RE` use becomes `find`/`find_all` against the loaded registry.
  - Every walk-up stops at the matched root dir. The deal-depth bounds come from the matched desk.
  - The **marker key logic stays as it is today:** the `by agency` token in `dir_marker` and `desk-post.sh`. It is the shell prefilter token, which Task 10 ties to the registry. Generalising the marker is Plan 2's job.
  - **Registry-error line:** when `load()` returns an error, the SessionStart output of desk-context ends with exactly `bbs-sales: the desk registry could not be read (<reason>); only the built-in California desk is active.` Nothing else changes, and no other hook prints the error.

- [ ] **Step 1: Add the cases.**
  - (a) With `desks-two.json`, SessionStart in `Synthetic Desk Root/A/Buyer` (which holds a `quote-log.md` with one row) prints that row's precedent block, exactly as the CA fixture does for Mule Creek.
  - (b) A `LEARNED.md` at `Synthetic Desk Root/A/Buyer` appears in desk-memory's chain from a deal folder below it.
  - (c) `registry_error_line`: with `BBS_DESKS_FILE` set to an invalid-JSON file, SessionStart in the CA fixture prints the usual CA output plus the registry-error line, identically in both halves.
- [ ] **Step 2: Run them; confirm only the new cases fail**

Run: `BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/parity.py; BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desk_memory_parity.py; pwsh -NoProfile -File plugins/bbs-sales/hooks/tests/run-tests.ps1`

- [ ] **Step 3: Convert the four files.**
- [ ] **Step 4: Run the same commands; confirm everything passes**
- [ ] **Step 5: Commit** `refactor(bbs-sales): desk-context and desk-memory read the desk registry`

### Task 9: rfq-record hook, `rfq_record.py`, and `desk_memory.py` on the registry

**Files:**
- Modify: `hooks/rfq-record-hook.py` (`TREE` :24, marker :53)
- Modify: `hooks/rfq-record-hook.ps1` (:9, :26; it still validates nothing, and only the path test changes)
- Modify: `scripts/rfq_record.py` (`_deal_path` :906–908)
- Modify: `skills/desk-remember/scripts/desk_memory.py` (`DESKS` :44–52 and where it resolves a desk)
- Test: `scripts/tests/test_rfq_record_cli.py`, `skills/desk-remember/scripts/test_desk_memory.py`, `hooks/tests/parity.py` (add cases)

**Interfaces:**
- Consumes: Tasks 5–6.
- Behaviour:
  - **rfq-record hook:** "under a desk" means `find(norm_path)` returns a match `m` with `norm[m.start-1] == "/"` and `norm[m.end] == "/"`. That reproduces today's `"/" + TREE + "/"` test.
  - **`rfq_record._deal_path(path) -> str`:** returns `os.path.abspath(path)` when `find` matches it, else `""`.
  - **`desk_memory.py`:**
    - `DESKS` is replaced by `profile_for(path) -> tuple[str, dict, str] | None`, returning `(desk_id, {"tree": m.root, "file": LEARNED_FILE, "rep_min_depth": desk["rep_min_depth"]}, root_dir)`, where `LEARNED_FILE = "LEARNED.md"`.
    - It imports the loader from `<plugin>/scripts` by path, the same way the hooks do.
    - Its refusal messages stay byte-identical for CA.

- [ ] **Step 1: Add these tests.**
  - `test_deal_path_synthetic_desk` (CLI `compile` under `Synthetic Desk Root/A/B/2026-11-01/RFQ.md` with `BBS_DESKS_FILE=desks-two.json` → the sidecar's `deal_path` is non-empty).
  - `test_deal_path_outside_any_desk` (→ `""`).
  - A `desk_memory` test: saving a note at depth 2 under `Synthetic Desk Root` succeeds, and at depth 1 it is refused with the same sentence CA gives.
  - A `parity.py` case: the rfq-record PS half gives its python3 notice for an `RFQ.md` under `Synthetic Desk Root/` (registry override) and stays silent outside.
- [ ] **Step 2: Run them; confirm only the new tests fail**

Run: `python3 -m unittest discover -s plugins/bbs-sales/scripts/tests && python3 plugins/bbs-sales/skills/desk-remember/scripts/test_desk_memory.py && BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/parity.py`

- [ ] **Step 3: Convert the four files.**
- [ ] **Step 4: Run the same commands; confirm everything passes**
- [ ] **Step 5: Commit** `refactor(bbs-sales): rfq record and desk memory read the desk registry`

### Task 10: Checker, docs, CI, version, PR

**Files:**
- Modify: `scripts/check_marketplace.py` (add `check_desk_registry()` and register it where the other bbs-sales checks run)
- Modify: `hooks/desk-post.sh`: add one comment line, `# PREFILTER-TOKENS: by Agency`, directly under the existing step-2 comment. Behaviour is unchanged.
- Modify: `hooks/hooks.json` (`description`): "the tree" becomes "a desk root from `references/desks.json`"; mention the fallback.
- Modify: `README.md` (bbs-sales row/section: the registry exists; the skill count is unchanged)
- Modify: `.claude-plugin/plugin.json` (next free version after #96's)
- Modify: `.github/workflows/check-marketplace.yml` (add `python3 plugins/bbs-sales/scripts/tests/test_desks.py`, already covered by the existing `unittest discover` step if it runs; verify, and add `BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desks_parity.py` to the "Quote-desk guard parity" step)

**Interfaces:**
- `check_desk_registry()` fails the run (in the checker's existing error style) when any of these hold:
  1. `references/desks.json` breaks a Task 5 schema rule.
  2. The literal `All RFQ's by Agency` appears in any of these files except `scripts/desks.py`, `scripts/Desks.ps1`, `references/desks.json`, `references/desks.md` and tests:
     - `hooks/*.py`, `hooks/*.ps1`
     - `scripts/rfq_record.py`
     - `skills/desk-remember/scripts/desk_memory.py`
  3. `desks.FALLBACK`, imported by path, differs from the `ca-state` entry. The checker also parses the PS fallback with a regex on `Desks.ps1`'s fallback block, written as one JSON string literal so it can be compared. **Decision: write the PS fallback as `$FALLBACK_JSON = '<json>'` and `ConvertFrom-Json` it, so both fallbacks compare as JSON.**
  4. Some root in `desks.json` contains none of the `PREFILTER-TOKENS` (case-insensitive), or some token's bracket form is missing from `desk-post.sh`, or the `dir_marker` token in `desk-memory.py`/`.ps1` differs from the tokens. The bracket form is built as `''.join(f'[{c.upper()}{c.lower()}]' if c.isalpha() else ('\\ ' if c == ' ' else c) for c in token)`, e.g. `[Bb][Yy]\ [Aa][Gg][Ee][Nn][Cc][Yy]`.

- [ ] **Step 1: Write the checker's own test cases** (the checker's existing self-test pattern, if one exists; otherwise a `scripts/tests/test_check_desk_registry.py` that runs `check_desk_registry()` against temp copies). Cases:
  - a stray literal in a temp `hooks/x.py` fails;
  - a mismatched fallback fails;
  - a root without a prefilter token fails;
  - the real tree passes.
- [ ] **Step 2: Run them; confirm the failure cases fail for the right reason**
- [ ] **Step 3: Implement `check_desk_registry()`**, then make the docs, CI and version edits.
- [ ] **Step 4: Run the full gate**

Run:
```bash
python3 scripts/check_marketplace.py && python3 scripts/check_marketplace.py --requirements \
&& python3 -m unittest discover -s plugins/bbs-sales/scripts/tests \
&& BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/parity.py \
&& BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desk_memory_parity.py \
&& BBS_REQUIRE_PS=1 python3 plugins/bbs-sales/hooks/tests/desks_parity.py \
&& python3 plugins/bbs-sales/hooks/tests/fill_gate_parity.py \
&& python3 plugins/bbs-sales/skills/desk-remember/scripts/test_desk_memory.py \
&& pwsh -NoProfile -File plugins/bbs-sales/hooks/tests/run-tests.ps1 \
&& claude plugin validate plugins/bbs-sales
```
Expected: every command exits 0. The pre-existing CA expectations are untouched: `git diff origin/main -- plugins/bbs-sales/hooks/tests/parity.py` shows only added cases.

- [ ] **Step 5: Commit and open the draft PR**, only if fewer than five PRs are open. Otherwise hand Parker the branch name.
  - Commit message: `feat(bbs-sales): one desk registry for every hook and script (S2)`.
  - The PR body names this plan, the spec §6.2, and the STEWARD rulings entry, and ends with the attribution line.
  - Ask `rex` to review. Parker merges.
