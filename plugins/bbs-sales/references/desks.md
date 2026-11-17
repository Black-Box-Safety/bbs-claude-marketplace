# Desk registry

`desks.json` lists the desks that the bbs-sales hooks and scripts treat as deal trees. Python code reads it through `scripts/desks.py` (`load`, `find`, `find_all`); PowerShell code reads it through its twin `scripts/Desks.ps1` (`Get-BbsDesks`, `Find-BbsDeskRoot`, `Find-BbsDeskRootAll`). Nothing else hard-codes a desk root. The built-in `ca-state` entry exists in two copies, `FALLBACK` in `desks.py` and `$FALLBACK_JSON` in `Desks.ps1`; `scripts/check_marketplace.py` requires both to equal the `desks.json` entry.

File shape: `{"schema_version": 1, "desks": [ ... ]}`. Every desk has exactly the eight keys below.

"Read by" names what acts on the key today. The schema check in `load()` validates every key; that is not counted as a read.

| Key | Meaning | Read by |
|---|---|---|
| `desk_id` | Unique id, `^[a-z][a-z0-9-]*$`. | `skills/desk-remember/scripts/desk_memory.py` (profile lookup) and the `guard-tree` twins (one near-duplicate check per desk and root). Not read by `rfq_record.py`. |
| `kind` | `rfq` or `order`. Only `rfq` desks are searched by `find` and `find_all`. | `find` and `find_all` in the loaders (so every hook and `rfq_record.py`), the `desk-memory` twins, and `desk_memory.py`. |
| `roots` | Non-empty list of folder-name roots. Matched case-insensitively anywhere in a path, `\` read as `/`. Both loaders fold ASCII A-Z only. | Every hook (`guard-tree`, `desk-context`, `desk-memory`, `rfq-record-hook`, each in both twins), `rfq_record.py`, and `desk_memory.py`. |
| `deal_depth` | `[min, max]` folder levels below the root that hold a deal folder. | `desk-context` twins only. Not read by the guard hooks or `rfq_record.py`. |
| `deal_name_rule` | How a deal folder is named. Only `date` is accepted. | Nothing yet. Validated, not yet read; reserved for Plan 4 (roadmap: `docs/superpowers/plans/2026-11-17-bbs-sales-system-plan-1-rulings-and-registry.md` in the marketplace repo; spec section 6.2 in the same repo). |
| `rep_min_depth` | Depth below the root at which the rep folder exists. | The `desk-memory` twins and `desk_memory.py`. Not read by the guard hooks or `rfq_record.py`. |
| `guard` | Booleans `no_rename`, `near_duplicate`, `filled_immutable`: which folder-guard checks apply. | `guard-tree` twins only. A command that names several desks gets each desk's own flags. |
| `record_profile` | Name of the record layout used in the desk (`ca-v2`). | Nothing yet. Validated, not yet read; reserved for Plan 4 (roadmap and spec as for `deal_name_rule`). |

Rules:

- A profile is a PR. Add or change a desk by editing `desks.json` in a reviewed pull request; do not edit it in place on a rep's machine.
- Customer bindings arrive in Plan 4 (roadmap: `docs/superpowers/plans/2026-11-17-bbs-sales-system-plan-1-rulings-and-registry.md` in the marketplace repo; spec section 6.2 in the same repo).
- Reporting keys are documented separately and are not part of this file.

Fallback: if the file is missing, unreadable, invalid JSON (including nesting too deep to parse), or fails the schema, `load()` (and `Get-BbsDesks`) returns the built-in `ca-state` desk plus a one-line reason naming the file. It never raises. Only the `desk-context` SessionStart reports that reason, as a final line; every other hook silently uses the California fallback. Set `BBS_DESKS_FILE` to point at another registry (tests do this).
