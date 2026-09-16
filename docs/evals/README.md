# Trigger-precision evals

A skill is chosen from its name and description, before anything in its body is read. When
several skills sit on one desk the wrong one can win silently — the rep gets a plausible
answer from the wrong skill and no error is raised. This measures that.

## Why not `skill-creator`'s eval directly

`skill-creator`'s `scripts/run_eval.py` registers **one** description and asks "did it
fire?". That measures recall for a skill in isolation. It cannot answer the question that
matters here — *which of the siblings won* — because the siblings are never in the room.

`discriminate.py` registers **every competing description at once** in an isolated project
root, runs `claude -p <query>`, and records which skill the model actually invoked. Use
`run_eval.py` when tuning one skill; use this when skills compete.

## Running it

```bash
cd docs/evals
python3 discriminate.py --skills skills.json --queries queries-routing.json \
    --runs 5 --workers 4 --anonymize --out results.json
```

**Keep `--workers` at 4, and re-run anything that fails as `__none__`.** Throttling is the
main source of noise here, and it looks exactly like a regression. Measured on the same
code, minutes apart: a full set scored 16/21 at 10 workers and 21/21 at 4; later, under
sustained load, two queries scored 60% at 4 workers and 100% each when re-run alone at 2.

The tell is the shape of the failure. **A throttled run fails as `__none__`** — no skill
fired at all, across queries that are unrelated to each other. **A real routing defect
fails as the wrong skill name**, and it reproduces in isolation. Never act on a `__none__`
cluster without re-running the affected queries on their own; the numbers below are from
clean runs.

`skills.json` is `{"skill-name": "description", ...}`, and must hold **everything the
person has installed**, not one plugin — a skill cannot lose to a sibling that is not in
the room. For a sales rep that is all of `bbs-sales` plus `bbs-deck-voice` from
`bbs-foundations`. Regenerate it with `python3 build_skills_json.py`.

### `--anonymize` is the one that tells you something

Without it, the stub names match the skill names and the name alone carries most of the
routing signal — everything passes and you learn nothing. `--anonymize` replaces the names
with `skill-a`…`skill-n` so **only the description** can decide. Run both: the named run is
what a rep experiences, the anonymized run is the description's actual quality.

Two harness details that are easy to get wrong:

- **Isolation.** The run passes `--setting-sources project,local`. Without it the
  operator's account-synced copies of these same skills are also in the field and the
  measurement is meaningless. Verify: ask a bare `claude -p` in an empty directory to list
  skills matching `bbs` — it must answer NONE.
- **Fixtures.** A query about a screenshot or a PDF needs the file to exist, or the model
  routes correctly in prose ("I'll run it through grainger-screenshot") and never invokes
  the tool — scoring a correct decision as a miss. Queries carry a `files` list and the
  harness writes a real 1×1 PNG / minimal PDF.

## Results, 2026-09-16

The field is the 11 skills a sales rep has installed. 5 runs per query, pass = ≥80%.

| Condition | Baseline (14 skills) | After consolidation (11 skills) |
|---|---|---|
| Real-world (name + description) | 20/20 | 24/24 |
| Description alone (`--anonymize`) | 18/20 | **24/24** |

Artifact: `results-2026-09-16-after-anonymized.json` (24/24, every query 5/5,
`--workers 4`).

**The 2026-09-15 anonymized artifact recorded 22/24, not the 24/24 this table claimed.**
The two failures, `dwr-2` and `promo-1`, were each `__none__` on 2 of 5 runs while naming
the right skill on the other 3 — the signature of a harness fault, not a routing defect.
It was one: `discriminate.py` appended the exit-time drain to its buffer and broke without
parsing it, so a run that finished fast had its `tool_use` discarded and scored `__none__`.
Fixed in `71e3008`.

The re-run above is on the fixed harness and shows **zero `__none__` across all 120 runs**,
where the old artifact had four. The number in this table is now measured rather than
asserted, and the superseded artifact is kept beside it rather than deleted.

Two description defects were found and fixed before any consolidation: `naspo-quote`
(40% → 100%, was losing to `ca-rfq-intake`) and `dwr-pdf-info` (60% → 100%, its
description led with "California Department of Water Resources" and never said the bare
acronym a rep types).

The Grainger cluster the 2026-09-15 handoff predicted would collide — cart PDF,
screenshot, DWR PDF, BPO check, pricing — routed 5/5 in **both** conditions, before and
after. That prediction was wrong, and it took measurement to find out: the skills that
actually overlapped were the three item extractors and the two form fillers, which is a
different cut entirely.

### The ambiguous set is the one that pays

`queries-ambiguous.json` holds queries with no single defensible answer. They are read by
hand, not scored by the pass threshold — what you want to see is the skill *declining to
guess*.

| Query | Baseline | After |
|---|---|---|
| "Can you check these Grainger items? 4CZ16, 6YPH8" | **pricing** ran, 4/5 | asks which, 5/5 |
| "I need pricing on the items in rfq.pdf" | pricing ran, 5/5 | asks, 5/5 |
| "Here are some Grainger part numbers: …" | asks, 5/5 | asks, 5/5 |
| "CDCR Corcoran just emailed asking us to quote these…" | — | split 3/1/1 — see below |

"Pull the Grainger numbers out of items.pdf" used to split (the cart skill grabbed it 3/5
on a PDF nobody said was a cart). Merging the extractors made it unambiguous, so it moved
into the scored set at 5/5.

The Corcoran query is the one left open, and it is **a workflow question for Parker, not a
description defect**: `ca-rfq-intake` says to log a request before pricing anything and is
step 1 of the sales README, but the model reads "asking us to quote" as a quoting task and
picks `naspo-quote` about 3 times in 5. Whichever way Parker rules, one of the two
descriptions needs to say so outright. Tuning either one before that ruling would just be
fitting the test.

The fix was reciprocal `Do NOT use for` clauses that name the sibling and say *ask which*.
On a binding document a skill should fail loudly rather than produce a plausible wrong
value; the same reasoning applies one level up, to which skill runs at all.

## Cost

A full routing run is 100 `claude -p` calls, about 50 seconds wall-clock at 10 workers.
Detection kills each subprocess the moment the skill is named, so a correctly-routed query
costs one tool call, not a whole session.

## When to re-run

Before adding a 15th skill, and after editing any description. Add the new skill's queries
to `queries-routing.json`, and at least one query that *should* go to a sibling.

---

Owner: Parker. Last verified 2026-09-15.
