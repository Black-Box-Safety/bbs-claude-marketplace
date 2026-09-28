# Spec: log local/co-op and federal/prime quotes the way CA state quotes are logged

*Written 2026-09-28, before implementation. Plan:
`docs/superpowers/plans/2026-09-28-intake-local-federal.md`. Design only; nothing here is
built yet.*

---

## Summary for Parker

You asked for the State of CA intake workflow to apply to other quotes that arrive by
email, so they get logged. This spec does that for two new **channels**: local
government and co-op (cities, counties, special districts, fire and law enforcement,
NPPGov, Sourcewell, direct bids), and federal and primes (federal agencies, Bechtel, USACE).
Higher ed and private work stay out.

The core change: the intake skill learns to tell the three channels apart, and runs
the same steps for each. Those steps are: find or create the folder, save what arrived,
open the run record, add a row to the quote log, and draft the CRM record for the rep.
It works out the channel from what the documents say about who is buying, checks that
against the sender's email domain and the folder the rep is working in, and **stops and
asks when those signals disagree or say too little**. It never falls back to a default
channel. The reason is that the channel decides which certification goes on a binding
document. DVBE on a federal bid or SB on a California bid is a false certification, and
it looks exactly like a correct one.

Reps keep typing `/ca-rfq` for state work, and nothing about it changes. A new `/rfq`
handles any channel. The two new folder trees sit beside `State of CA Agencies`. Local
work gets a new tree. Federal work goes into the existing `Federal Agencies` folder, which
already uses the State layout, instead of a new near-duplicate beside it. Bechtel stays
where it is. The hooks are taught each tree's layout, and **no customer folder is renamed
or moved**. This first version covers logging. Pricing and packets for the new channels
still go through the existing skills or the rep, and nothing is sent, signed onto a
federal form, or written to Business Central.

## Open rulings for Parker

Each of these is a fact about BBS that the repo does not hold. They are listed here
rather than guessed. The plan's slices that depend on one say which.

1. **Folder names.** Confirm `Customers/Local Agencies and Co-ops/` as the new local tree,
   and confirm that federal agency work goes into the existing `Customers/Federal Agencies/`
   rather than a new `Federal and Primes/` folder (§4).
2. **Bechtel's home.** Bechtel work lives in three places today: `Customers/Bechtel/`
   (with `sentinel/` and `hanford-DOE/`), `Customers/Federal Agencies/Bechtel - DOE/`, and
   the legacy `Customers/Hanford_Bechtel/` (2024). Which is canonical for a **new** Bechtel
   DOE request, `Bechtel/hanford-DOE/` or `Federal Agencies/Bechtel - DOE/`? The
   recommendation is to **teach the hooks Bechtel's existing layout and rename nothing**.
   Folder names carry account numbers (desk landmine 4). `naspo-quote` also reads Parker's
   signature image from a path inside `Customers/Bechtel/sentinel/`, so moving that tree
   would break signing on state packets.
3. **What BBS certifies to a California city, county or special district.** Canon covers
   federal (SDVOSB and small business), California state (DVBE 2009473 only, never SB), LA
   County (local DVBE `10086`), and the City of San Diego (SLBE `17BB1659`). It does not say
   what BBS claims to any other California local agency. Is DVBE 2009473 claimed? Is BBS
   ever a small business to a local agency whose program sets its own threshold? Until you
   rule, the local profile writes `[FLAG: local certification not ruled]` and never fills
   one in.
4. **Which vehicle a local Grainger request goes on.** Canon's vehicles are NASPO MRO LPA
   `7-25-51-02.03` (a California state LPA), Sourcewell `091924-BBS` (body armor only),
   NPPGov `PS25650` (law enforcement), and GSA MAS. Canon does not say whether a city or
   county buys Grainger lines from BBS on the NASPO LPA, and a Sourcewell request for
   anything other than body armor has no BBS vehicle behind it. Rule the default, or rule
   that it is always the rep's call and flagged.
5. **Who owns local/co-op and federal/prime intake.** Canon's CA state book scope says only
   what is *out* of the Kim/Aanya book. The 2026-07 quote-desk list names Griffin for
   federal and Jeff for body armor, but that is a role list, not an ownership ruling. Say
   who logs, and who is the CRM owner, for each new channel.
6. **How the CRM tells channels apart.** `bbs_rfqs` has no channel field. The account
   entity has a `bbs_customertype` picklist that exists but is **empty on every account**,
   and its option values could not be read through the connector. Options: (a) populate that
   existing field (it is not a new field, so it does not collide with the 2026-09-28 "no new
   CRM fields" ruling), or (b) keep the CRM as it is and identify channel by account list.
   This matters today, not only after this ships: `bbs-weekly-sales-report` counts every
   `bbs_rfqs` record a rep owns as CA state pipeline (§7).
7. **Tracker of record for deadlines.** `ca-rfq-intake` §5 still says the Supabase
   `rep_cockpit` pipeline in `ca-quote-hub` "remains the tracker of record for deadlines".
   `REGISTRY.md` says that pipeline is **parked**, and the territory and weekly-report skills
   treat Sales CRM `bbs_rfqs` as the pipeline of record. Which is it? This spec assumes the
   Sales CRM (with the folder's `RFQ.md` as the local copy) and does not extend
   `rep_cockpit` to new channels.
8. **What `bbs_lpa` means on a non-state record.** The field is a picklist. The values seen
   in production are `Y` (0), `N` (1) and `S` (2). The meaning of `S` is unverified, and
   `ca-site-visit-brief` reads it as Grainger Sourcing under the LPA. Should local and federal
   records carry `N`, carry a new value, or leave it blank?
9. **The Sentinel desk's pricing rules versus canon.** The live `sentinel/CLAUDE.md` still
   sends Grainger pricing through the **retired** `b2b.blackboxsafety.com` punch-out, and it
   prices Grainger with margin bands and an 8% rebate model. Canon says Grainger MCP, at cost.
   A commercial PO to a prime has no contract vehicle behind it, so it is not obvious that
   "at cost" was meant to reach it. Rule whether Grainger at cost applies to prime work. The
   punch-out line is stale either way and gets fixed in that file (on SharePoint, not in git).
10. **Business Central writes on the Sentinel desk.** Sentinel creates BC documents through
    service-principal scripts in `MASTER/PM Claude/BC-Write-API/` (dry-run, then live, then
    read back). Your 2026-09-28 ruling is that skills never write to BC, and nothing in this
    spec does. Should those scripts stay a Sentinel-only path run by a person, or should they
    never be offered to the quote builder at all? The default is the second.
11. **Legacy flat folders.** About 200 customer folders sit flat under `Customers/`,
    including cities, counties, police departments and federal agencies. When a request
    arrives from a customer that already has one (for example `City of San Diego`), should it
    be filed in that legacy folder, or in the new tree with a pointer back to the old one?
    The recommendation is the new tree plus a pointer line in the buyer's `CLAUDE.md`, with
    nothing moved (§4.4).

Also noted, not rulings:

- **The live State desk `CLAUDE.md` is stale.** `Customers/State of CA Agencies/CLAUDE.md`
  on SharePoint still cites the retired `/ca-rfq-log` and `/ca-rfq-quote`, and still says
  "OSDS SB/DVBE 2009473", which is the false SB claim that was fixed in git on 2026-09-22. It
  was instantiated from `workspace/DESK-CLAUDE-template.md` before those fixes.
  Re-instantiating it is a prerequisite (plan slice 0) and fixes a live defect regardless of
  this spec.
- **The quote-log example shows a 900001-series number** (`900008`, the
  `bbs-quote-builder` series). Your 2026-09-28 ruling is that quote numbers are Business
  Central SQ numbers. New-channel rows use the SQ number. Fixing the example and the
  builder's numbering is a separate change, because it touches the state path.
- **`docs/PRODUCT.md` is empty on main.** `/ca-rfq` Gate 1 tells the run to check its §9
  for rulings. `/rfq` checks the *Already open for Parker* register in `docs/STEWARD.md`
  instead, and does not repeat the dead pointer.

---

## 1. Shape: one intake skill with channel profiles, not siblings

### Decision

Generalise `ca-rfq-intake` into **one intake skill, `rfq-intake`, with three channel
profiles**:

```
plugins/bbs-sales/skills/rfq-intake/
├── SKILL.md                      the channel-neutral steps + the router
└── references/channels/
    ├── ca-state.md               today's ca-rfq-intake behaviour, moved verbatim
    ├── local-coop.md             cities, counties, special districts, fire/LE, NPPGov, Sourcewell
    └── federal-prime.md          federal agencies (buyer type: agency) and primes (buyer type: prime)
```

### Why not siblings

AGENTS.md, "When the work is a skill": per-customer variation belongs inside a skill as a
profile, because sibling skills compete on descriptions, and that competition is
probabilistic. A `local-rfq-intake` beside `ca-rfq-intake` would have to win on wording
every time a city emails. A city in California *is* a California agency, so the wrong
sibling would sometimes win and file a county bid as state. That is also where the DVBE-only
certification line lives. Profiles route on document content, which is deterministic and
testable. The job is the same across all three channels (make the request findable and its
deadline visible), so the "merge on the job, not the input" rule points the same way.

### Why rename

`ca-rfq-intake` describing federal work would be a name that lies. Renaming has costs:
every pointer (`/ca-rfq`, `naspo-quote`, the desk template, `docs/evals/skills.json`) has to
be repointed. `check_marketplace.py` already FAILs on a surviving pointer to a merged-away
skill, so the checker enforces the rename rather than trusting it. The description changes,
so the routing eval has to be re-run (it needs Claude auth; see AGENTS.md, "What it cannot
tell you").

### Entry points, and protecting muscle memory

| Command | Does | Change |
|---|---|---|
| `/ca-rfq` | State of CA, end to end | **None to its steps.** Gate 0 gains one check: if the router says the request is not CA state, the run stops and says "this is a <channel> request; run `/rfq`". It never proceeds as state. |
| `/rfq` *(new)* | Any channel. Runs the router, then intake, then hands off | Routes CA state into `/ca-rfq`'s own gates rather than duplicating them. For local and federal it runs intake and stops at a hand-off line naming the pricing skill (§3). |

Reps who type `/ca-rfq` get what they got yesterday. The skill auto-triggers on "log this",
"file this" and "an agency emailed", just as it does now, and its description names all three
channels. `/rfq`, like `/ca-rfq`, carries order and gates only, and no procedure (the
2026-09-16 orchestration spec's acceptance test applies to it unchanged).

## 2. What carries over unchanged in every channel

| Step | Carries over as | Owner |
|---|---|---|
| Find the folder before creating one | Same rule, same search (by buyer **and** by item), extended to legacy flat folders (§4.4) | `rfq-intake` §1 |
| Save everything as received | Unchanged: every attachment, unrenamed; `request-email.txt` when the request was only an email body | `rfq-intake` §2 |
| Run record `RFQ.md` | Same template, plus two lines: **`Channel:`** with the evidence that decided it, and **`Certification basis:`** as a pointer to the canon row, never the cert text itself | `rfq-intake` §3 |
| Due-date tracking | `Due:` in `RFQ.md` (date, time, timezone), and `bbs_duedate` / `bbs_timedue` in the CRM draft | same |
| `quote-log.md` row | Same columns: Date / Item / Quote # / Vehicle / Value / Outcome. Quote # is the BC SQ number (ruled 2026-09-28) | `rfq-intake` §5 |
| CRM record | **Drafted for the rep, never written** (§6) | `rfq-intake` §5 |
| Weekly reconciliation | Records carry a channel that the reports can filter on (§7) | reports |
| "Don't price, don't fill forms, don't email the buyer" at intake | Unchanged | `rfq-intake` |

**CRM precedent, stated plainly:** today `/ca-rfq` and `ca-rfq-intake` make **no CRM write
of any kind**. No skill in the repo calls `crm_update_record`; the only mention is the
checker's registry. The connector also exposes no create tool (its tools are
`crm_get_record`, `crm_list_attributes`, `crm_list_records`, `crm_update_record` and
`crm_whoami`), so Claude could not create a `bbs_rfqs` record even if it were allowed to.
This spec follows the existing precedent: no CRM writes. It adds a **drafted** record, a
field-by-field block the rep enters in Dynamics. That matches your 2026-09-28 ruling that
CRM record creation is drafted for the rep.

## 3. What differs per channel

Every value below is a **pointer**. The profile names the canon row, and the canon row holds
the value. A profile that re-keys a cert number is broken under invariant 2.

| | CA state (existing) | Local / co-op | Federal / prime |
|---|---|---|---|
| **Certification** | DVBE 2009473 only; never SB; SCM §1202 incentive on competitive bids, never §1204. Canon: "Small-business status is channel-dependent" | LA County: local DVBE `10086`. City of San Diego: SLBE `17BB1659`. **Any other California local agency: OPEN RULING 3**, written `[FLAG: local certification not ruled]` | SDVOSB **and** small business under SBA standards; never DVBE. Canon row "Federal, primes" |
| **Contract vehicle** | NASPO MRO LPA, CA Body Armor LPA, DGS BPO, or competitive (canon vehicle table) | NPPGov `PS25650` (law enforcement), Sourcewell `091924-BBS` (**body armor only**), or a direct/competitive bid. NASPO LPA for locals: **OPEN RULING 4** | Agency: GSA MAS `47QSWA23D000Y`, or open market. DOE Grainger is in canon with no number: `[FLAG]` when named. Prime: **no BBS vehicle applies**; it is a commercial PO (Sentinel desk) |
| **Compliance packet** | State forms: `naspo-quote` §5 on the NASPO path, `ca-form-filler` otherwise | **Never `ca-form-filler`.** Local agencies send their own forms. v1 lists them in `RFQ.md` "Forms the buyer requires" and leaves them to the rep | **Never `ca-form-filler`.** Federal: SAM-based reps and certs, FAR/DFARS clauses. Prime: the prime's reps and certs by award value (Sentinel: under $10K micro-purchase form; $10K and over, the FAR 52.212-3 commercial form), plus country of origin per line. v1 lists them and flags them. **Never assert an origin that cannot be documented** |
| **Signer** | `ca-form-rules.md` | `[FLAG: signer]`. `ca-form-rules.md` covers state forms only | Canon "People and signatures": Griffin signs federal and Sourcewell contracts. v1 fills and signs **nothing** on federal forms |
| **Pricing path** | `naspo-quote` (Grainger at cost via MCP on the institution's own account) or `bbs-sourcing` | Grainger lines: `grainger-pricing` on the **buyer's own Grainger account**, at cost. Other lines: `bbs-sourcing`. Its description currently scopes it to "a California state agency", which is a follow-up; until then the rep invokes it by name | Agency: as local. Prime: **OPEN RULING 9** on whether Grainger at cost applies; until ruled, the price is the rep's, flagged |
| **Book scope** | Kim/Aanya CA state book, minus body armor and CSU/UC (canon "CA state book scope") | **Not** the CA state book. Owner: **OPEN RULING 5** | **Not** the CA state book. Owner: **OPEN RULING 5** |
| **Customer-specific facts** | Buyer `CLAUDE.md`, agency folder name (Grainger account) | Buyer `CLAUDE.md` | The desk's own `CLAUDE.md` on SharePoint (prime contract number, BC customer numbers, NAICS, flowdowns). **Read there; never re-keyed into git** |

Body armor from a local agency (Sourcewell, NPPGov) is its own case. Canon puts body armor
outside the Kim/Aanya book whatever the channel, so the local profile logs it and names body
armor as out of that book. Who owns it is part of ruling 5.

## 4. Folder tree

### 4.1 What is on SharePoint today

Root: `Black Box Safety - MASTER/Customers/` (read live by the steward through the M365
connector, 2026-09-28).

- **`State of CA Agencies/`**: the desk root. It holds `CLAUDE.md`, `_README.md`,
  `BUILD-LOG.md`, `DUPLICATE-TREES.md`, `.sales-team/`, `Business Development/`, `docs/`,
  `Weekly Summaries/`, and **`All RFQ's by Agency/<Agency>/<Institution or Buyer>/<Item M.D.YY>/`**.
- **`Federal Agencies/`**: exists, partial, and **already uses the CA-style buyer layout**
  `<Agency>/<Buyer>/<Item M.D.YYYY>/`, with no `All RFQ's by Agency` layer and a four-digit
  year. Children include ATF, VA, DOD IG, DEA, U.S. Army, U.S. Navy, `Bechtel - DOE` (active
  September 2026: `Hunter Tyler/Filter Assembly 9.8.2026`), and `Wet Suits`.
- **`Bechtel/`**: an active customer desk with its own conventions. `sentinel/` has a root
  `CLAUDE.md` and site folders `utah-sentinel/` and `vandenberg-sentinel-rfps/`. Deal folders
  are `<site>/rfp-<6 digits>-<slug>/`; the prefix is inconsistent (`rfq-`, `rfp-`, `RFP-`),
  so match on the six-digit number. Each deal folder holds `CLAUDE.md`, `inbound-docs/`,
  `internal/`, `outbound/`, `learning/`. There is **one program-level quote log** at
  `sentinel/learning/quote-log.md`, not one per buyer. `hanford-DOE/` holds item folders.
- **`Hanford_Bechtel/`**: legacy (2024).
- **Dynamics document locations** `/account/<Account>_<guid>/bbs_rfq/<RFQ>_<guid>`:
  auto-created by the CRM. They are **not** the tree, and intake never files into them.
- **About 200 flat folders**: cities, counties, PDs (e.g. `City of San Diego`, `LA County`,
  `Fresno Police Dept`, `Anaheim PD 9.27.23`), federal agencies (Air Force, DEA, DLA, Border
  Patrol, Secret Service, Tinker AFB, `USACE-Vicksburg BPA's`, NAVFAC), private companies,
  and some state departments outside the State tree. `DOE` and `DOE (Department of Energy)`
  both exist at top level.

Repo references to Bechtel, found by grep: `naspo-quote/SKILL.md:155` and
`bbs-sales/README.md:134` (Parker's signature image under
`Customers/Bechtel/sentinel/vandenburg-sentinel-rfps/...`, spelled `vandenburg` there while
the live folder is `vandenberg`. **That pointer needs checking; plan slice 0.**), and
`bbs-claude-md-forge/references/worked-example.md` and `templates.md` (the Sentinel tree as
the customer-folder CLAUDE.md model). There is no Bechtel-specific intake workflow in the
repo.

### 4.2 Proposed trees (Parker confirms: ruling 1)

| Channel | Desk root | RFQ root | Layout below RFQ root |
|---|---|---|---|
| CA state | `Customers/State of CA Agencies/` | `.../All RFQ's by Agency/` | `<Agency>/<Institution or Buyer>/<Item M.D.YY>/` *(unchanged)* |
| Local / co-op | `Customers/Local Agencies and Co-ops/` **(new)** | `.../All RFQ's by Agency/` | `<Agency>/<Department or Buyer>/<Item M.D.YY>/` |
| Federal agency | `Customers/Federal Agencies/` **(existing, reused)** | the desk root itself | `<Agency>/<Buyer>/<Item M.D.YYYY>/` *(as found)* |
| Prime: Bechtel | `Customers/Bechtel/` **(existing)** | `sentinel/<site>/` and `hanford-DOE/` | as found; see ruling 2 |

Why each choice:

- **Local mirrors State exactly, including the `All RFQ's by Agency` layer.** It is a new
  tree, so there is nothing to migrate. The extra layer leaves room at the desk root for the
  same non-RFQ folders the State desk keeps (`Business Development/`, `Weekly Summaries/`).
  "Co-op" is in the name because NPPGov and Sourcewell requests land here, but co-ops are
  **vehicles, not customers**. The agency folder is the buying city or county, and the
  vehicle goes in the deal-folder name (`radios nppgov 10.2.26`). There is no `Sourcewell/`
  buyer folder.
- **Federal reuses `Federal Agencies/`.** Creating `Federal and Primes/` beside it would put
  two federal trees under one parent, which is the duplicate-tree problem
  `DUPLICATE-TREES.md` already records for the State desk. It is also what the near-duplicate
  guard exists to stop at buyer level. `Federal Agencies/` already has the right layout, and
  inserting an `All RFQ's by Agency` layer would mean moving folders, which is forbidden.
- **Primes keep their own desks.** Bechtel is a second instance of the customer-desk
  pattern the State desk names itself after: a desk root `CLAUDE.md`, deal-folder
  conventions, and a quote log. Its conventions differ, and they are described as data, not
  reshaped (§4.3). A future prime with no desk gets `Federal Agencies/<Prime>/<Buyer>/<Item>/`
  until it has enough volume to earn a desk of its own. That is a Parker call when it happens.

### 4.3 What the hooks must change

Today both hooks key on one hard-coded string. `desk-context.ps1` exits unless the session's
`cwd` contains `All RFQ's by Agency`. `guard-tree.ps1` sets `$TREE = "All RFQ's by Agency"`
and applies all three rules (no rename or move, no near-duplicate folder, `FILLED/`
immutable) only to paths containing it. So:

- **Local**, being a mirror, would be covered **with no code change**. That is an accident
  of the substring, not a design, and it should not be relied on.
- **`Federal Agencies/` and `Bechtel/` are not covered at all today.** A rename inside
  Bechtel's tree is allowed right now.

**Change:** replace the literal with one data file both hooks read,
`plugins/bbs-sales/hooks/desk-roots.json`. Each desk is an entry:

```json
{ "desk": "federal-agencies", "channel": "federal-prime",
  "root": "Customers/Federal Agencies", "rfq_root": "",
  "quote_log": "per-buyer",
  "deal_folder": "<Item M.D.YYYY>" }
{ "desk": "bechtel", "channel": "federal-prime",
  "root": "Customers/Bechtel", "rfq_root": "",
  "quote_log": "sentinel/learning/quote-log.md",
  "deal_folder": "rf[pq]-<6 digits>-<slug>" }
```

- **Matching is on path segments** (`...\Customers\Bechtel\...`), not substrings, so
  `Hanford_Bechtel` and `Bechtel - DOE` do not match the `Bechtel` desk. Each of those is a
  separate entry or nothing, per ruling 2.
- **All three guards apply equally to every desk.** The near-duplicate check compares against
  siblings from the matched desk's RFQ root, exactly as it does now from `All RFQ's by Agency`.
- **`desk-context.ps1`** reads `quote_log`. For `per-buyer` it walks up from `cwd` as now; for
  a fixed path it reads that file. It also prints one line, `DESK: <desk> (channel: <channel>
  — certification rules: canonical-facts.md "Certifications, by jurisdiction")`. That gives
  the router its third signal and names where the cert rule lives without restating it.
- **Desk-specific facts stay out of the file.** `desk-roots.json` holds layout, never a
  contract number, a BC customer number or a cert.
- **Tests:** `hooks/tests/run-tests.ps1` gains a fixture per desk. The existing CA fixtures
  must pass unchanged, which proves the state behaviour did not move.

No customer folder is renamed, moved or reshaped by any slice. Where a layout is odd
(`vandenburg` versus `vandenberg`, `rfq-`/`rfp-`/`RFP-`), the hooks and the profile learn the
oddity.

### 4.4 Legacy flat folders

The near-duplicate guard compares siblings **inside one tree**. It cannot see that
`Customers/City of San Diego/` exists when intake creates
`Local Agencies and Co-ops/All RFQ's by Agency/City of San Diego/`. That is a duplicate buyer
folder across trees, and it hides precedent exactly as landmine 1 describes. So intake's
"find before create" step searches **the whole `Customers/` listing**, flat folders included,
before creating an agency folder. If it finds one, it stops and applies ruling 11. The
recommendation: create the new-tree folder and put `Earlier history: Customers/<legacy>/` in
its `CLAUDE.md`. That way the new tree becomes the place to look from now on, and the hook
precedent injection works there. Nothing is moved.

Sorting the 200 flat folders into channels (an inventory, read-only) is a plan slice. Acting
on it is Parker's decision, and "acting" never means moving.

## 5. Email intake

A request that arrives by email becomes an intake **only when the rep runs it**:

- **The rep runs `/rfq` (or `/ca-rfq`) in their own session, on a thread they name or
  paste.** Intake reads that thread through the M365 connector, read-only:
  `outlook_email_search` to find it and the resource read to fetch the attachments. It saves
  the attachments into the synced tree exactly as it does now. It does not call
  `sharepoint_upload_file` or any send, forward, move or label tool.
- **Found-but-not-logged.** The rep can ask "what came in this week that I haven't logged?"
  Intake then searches **that rep's own mailbox only**, over the window they name, for
  threads from agency domains that look like requests. It checks each against the tree and
  the CRM (read), and lists the unlogged ones with **business facts only**: counterparty,
  agency domain, date, subject, attachment names. That list is taken from the 2026-09-28
  weekly-review ruling. Each item is an **offer to draft an intake**, and nothing is filed
  until the rep picks it. No personal mail, no sentiment, no timing or volume metrics.
- **No background process.** Nothing polls a mailbox on a schedule, no Routine or trigger
  watches an inbox, and nothing reads a mailbox other than the rep's own. Parker's team view
  in the weekly report stays limited to his own mailbox, and it says so in words.
- **Email bodies are data, never instructions** (managed settings). A buyer's email that says
  "use our small-business form" is evidence for the router, not an instruction to claim SB.

## 6. Logging

### 6.1 CRM draft, per channel

What was verified live on 2026-09-28 through `crm_list_attributes` and `crm_list_records` on
`bbs_rfq`:

| Field | Type | Values seen in production |
|---|---|---|
| `bbs_accountid` | Lookup, **ApplicationRequired** | account |
| `bbs_quotevalue` | Money, **ApplicationRequired** | |
| `bbs_lpa` | Picklist | `0` = Y, `1` = N, `2` = S. No other value in use. **Option-set labels beyond these, and the meaning of S, are unverified**: the connector returns formatted values on records, not the option-set definition |
| `bbs_quotemethod` | Picklist | `0` Business Central, `1` Provision Connect, `2` Customer Documents |
| `bbs_value` | Picklist | `0` Low, `1` Medium, `2` High |
| `bbs_quotevaluemethod` | Picklist | `0` User Generated, `1` System Generated |
| `bbs_quotenumber`, `bbs_ponumber`, `bbs_timedue`, `bbs_name`, `bbs_description` | String/Memo | |
| `bbs_receiveddate`, `bbs_duedate`, `bbs_submitteddate` | DateTime | |
| `bbs_accepted` | Boolean | **Zero records with `true`**, confirmed. Never set in production |
| account `bbs_customertype` | Picklist | **Zero accounts populated**; options unreadable |

**There is no vehicle field and no channel field on `bbs_rfqs`.** `bbs_lpa` is a Y/N/S
picklist, not a vehicle list, so "NPPGov" or "GSA MAS" has nowhere structured to go.

The drafted block, as the rep would enter it:

| Field | CA state | Local / co-op | Federal / prime |
|---|---|---|---|
| Account | the agency or institution | the city/county/district | the agency, or the prime (e.g. Bechtel National) |
| Name | `<Agency> – <item> <M.D.YY>` (the deal folder name) | same | same, and the six-digit RFP number for Bechtel |
| Received / Due / Time due | from `RFQ.md` | same | same |
| Quote number | BC SQ number, once the rep has it; blank at intake | same | same |
| Quote value | **required by the CRM.** At intake it is unknown. The draft says `[MISSING — NEEDS INPUT: quote value; the CRM will not save without one]` and does **not** propose `0` | same | same |
| Quote method | from how it will be quoted | same | same |
| LPA | per current practice | **ruling 8** | **ruling 8** |
| Description | vehicle, in words (the only structured-ish place for it), and the folder path | same | same |
| Channel marker | none today | **ruling 6** | **ruling 6** |

The rep decides whether to create it. The draft is never auto-created, and no field is ever
written by Claude.

### 6.2 Outcomes, given that `bbs_accepted` is empty

In order of authority:

1. **Business Central**: a quote with `acceptedDate`, or a quote converted to a sales order
   (read-only). This is the system of record for wins.
2. **`quote-log.md` Outcome**: `sent`, `won`, `lost` (with a clause on why), `no answer`. A
   `won` is confirmed against BC before any report counts it.
3. `bbs_accepted`: shown, if ever, as "accepted in CRM (unconfirmed)". This follows the open
   `bbs_accepted` ruling in `docs/STEWARD.md` and makes no new reading of it.

## 7. Weekly report and weekly rep review

- **`bbs-weekly-sales-report`** is scoped to the Kim/Aanya CA state book, but its pipeline
  section filters `bbs_rfqs` only on owner. A CRM record for a county bid, owned by Kim, is
  counted today as CA state pipeline. **The fix depends on ruling 6**: either filter on the
  account's `bbs_customertype`, or exclude an account list derived from the non-state desk
  roots. Until then, the report should add a "Notes and data gaps" line saying non-state
  records may be included. That is a small, safe edit, and it is slice 7.
- **The weekly rep review is not built yet** (no file on main mentions its "other work"
  line). Its approved brief reports non-state work on a separate "other work" line. The new
  channels feed that line, and **stay out of every CA state figure**.
- Both stay read-only and cite the canon scope section rather than restating it.

## 8. Risks and failure modes

| Failure | Why it is plausible | Guard |
|---|---|---|
| **Wrong channel, so the wrong certification on a binding document** | `.ca.gov` is not proof of state: **San Diego County's domain is `sdcounty.ca.gov`**. `.gov` is not proof of federal: the City of San Diego is `sandiego.gov`. Some county fire departments are run by CAL FIRE under contract ("CAL FIRE/Riverside County Fire"). A federal job can reach BBS through a prime's commercial PO | The router decides on **who the legal buyer is**, from document content: letterhead, solicitation terms (SCM/PCC vs municipal code vs FAR/DFARS), bill-to, and the vehicle named. Sender domain and desk folder are corroborating signals. **All present signals must agree, and at least the document signal must be present.** Disagreement or absence stops the run, lists the evidence, and asks the rep. **No default channel, ever.** The decision and its evidence are written to `RFQ.md` `Channel:` |
| DVBE language leaking onto federal work | The existing desk template, a stale live desk `CLAUDE.md`, and years of state habit | Each desk root gets its own `CLAUDE.md` from a per-channel template that points at canon. The existing `check_claude_md.py` FAIL on a DVBE claim in a federal-context file applies to those templates |
| A state form on a local or federal bid | `ca-form-filler` triggers on "the bid packet" | The local and federal profiles never hand to it; `/rfq` routes around it. Its description is not broadened |
| Duplicate buyer folder across trees | The guard only sees siblings | Search the whole `Customers/` listing first (§4.4) |
| A CRM record with a made-up value | `bbs_quotevalue` is required | `[MISSING — NEEDS INPUT]`, never `0` |
| New-channel pipeline inflating CA figures | No channel field | Ruling 6, and the interim note (§7) |
| Copying Sentinel's stale rules | Its `CLAUDE.md` is authoritative-looking | Rulings 9 and 10. The profile reads desk facts but takes pricing and cert rules from canon |
| Hook regression on the State desk | Both hooks change | Existing fixtures must pass unchanged. PowerShell 5.1 is still unverified, as recorded for the earlier hook work |
| Routing eval drift from the rename | The description changes | Re-run the discrimination eval; it needs Claude auth |
| Mailbox overreach | Email intake is new | The rep's own mailbox, on request, business facts only, no background process |

## 9. What this deliberately does not do

- It does not price, fill or sign a local or federal form, or build a federal packet skill.
  Those come later if volume earns them, as profiles.
- It does not write to Business Central, Dataverse, SharePoint (beyond saving into the synced
  tree the rep is working in), or any mailbox. It does not send.
- It does not rename, move or reshape any customer folder, including the flat legacy ones and
  Bechtel's three homes.
- It does not add CRM fields.
- It does not touch higher ed or private customers.
- It does not change `/ca-rfq`'s steps or `naspo-quote`.

---

Owner: Parker Marshall. Written 2026-09-28.
