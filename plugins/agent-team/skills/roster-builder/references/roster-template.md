# Roster template — `<home-repo>/<path>/ROSTER.md`

One table, one row per owner. Names are stable so ownership is unambiguous. The steward plans and
assigns; owners stay on their lane across sessions.

```markdown
# Delivery roster

| # | Lane | Owner | Model | Primary repo(s) |
|---|---|---|---|---|
| 01 | <slice name, e.g. Intake> | **<Name>** | `<tier id>` | <repo> |
| 02 | <slice name> | **<Name>** | `<tier id>` | <repo> · <repo> |
| — | <cross-cutting surface, e.g. Database lineage> | **<Name>** | `<tier id>` | <repo> (db/) |
| — | <cross-cutting surface, e.g. Security audit (read-only)> | **<Name>** | `<tier id>` | all repos' external surfaces |
| — | Program planning & status | **<Steward name>** | `<steward tier id>` | all |

## Role docs
- <Name> → [`roles/<name>-<lane>.md`](roles/<name>-<lane>.md)

## Charters (one line each)
- **<Name> — <Lane>.** Owns <mission sentence>. Chartered <date> via `roster-builder`; ships with a <N>-item opening gap list.

## How assignment works
1. The steward decomposes each lane's remaining work into session tasks (one session, one draft PR, no gate mid-flight).
2. Each task carries its owner, a one-session scope, acceptance criteria and a verification step.
3. The principal picks which sessions run; the named owner executes and lands the draft PR.
4. Owners are sticky per lane.
```
