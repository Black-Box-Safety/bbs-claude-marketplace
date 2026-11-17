# Desk registry

`desks.json` lists the desks that the bbs-sales hooks and scripts treat as deal trees. Loaders read it through `scripts/desks.py` (`load`, `find`, `find_all`). Nothing else hard-codes a desk root; `desks.py` holds the one built-in copy (`FALLBACK`) of the `ca-state` entry.

File shape: `{"schema_version": 1, "desks": [ ... ]}`. Every desk has exactly the eight keys below.

| Key | Meaning | Read by |
|---|---|---|
| `desk_id` | Unique id, `^[a-z][a-z0-9-]*$`. | all loaders, `rfq_record.py`, `desk_memory.py` |
| `kind` | `rfq` or `order`. Only `rfq` desks are searched by `find` and `find_all`. | `desks.py` |
| `roots` | Non-empty list of folder-name roots. Matched case-insensitively anywhere in a path, `\` read as `/`. Both loaders (`desks.py`, `Desks.ps1`) fold ASCII A-Z only. | `desks.py`, the guard hooks |
| `deal_depth` | `[min, max]` folder levels below the root that hold a deal folder. | guard hooks, `rfq_record.py` |
| `deal_name_rule` | How a deal folder is named. Only `date` is supported. | guard hooks |
| `rep_min_depth` | Depth below the root at which the rep folder exists. | guard hooks, `rfq_record.py` |
| `guard` | Booleans `no_rename`, `near_duplicate`, `filled_immutable`: which folder-guard checks apply. | guard hooks |
| `record_profile` | Name of the record layout used in the desk (`ca-v2`). | `rfq_record.py` |

Rules:

- A profile is a PR. Add or change a desk by editing `desks.json` in a reviewed pull request; do not edit it in place on a rep's machine.
- Customer bindings arrive in Plan 4.
- Reporting keys are documented separately and are not part of this file.

Fallback: if the file is missing, unreadable, invalid JSON, or fails the schema, `load()` returns `FALLBACK` (the `ca-state` desk) plus a one-line reason naming the file. It never raises. Set `BBS_DESKS_FILE` to point at another registry (tests do this). The checker requires `FALLBACK` to equal the `desks.json` entry.
