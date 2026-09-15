# Trigger-precision evals

A skill is chosen from its name and description, before anything in its body is read. With
14 skills in front of one rep, the wrong one can win silently — the rep gets a plausible
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
    --runs 5 --workers 10 --anonymize --out results.json
```

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

## Results, 2026-09-15

The field is the 14 skills a sales rep actually has installed. 5 runs per query,
pass = ≥80% of runs.

| Condition | Baseline | After |
|---|---|---|
| Real-world (name + description) | 20/20 | 20/20 |
| Description alone (`--anonymize`) | 18/20 | 20/20 |

Fixed: `naspo-quote` (40% → 100%; was losing to `ca-rfq-intake`) and `dwr-pdf-info`
(60% → 100%; its description led with "California Department of Water Resources" and never
said the bare acronym a rep actually types).

The Grainger cluster that the 2026-09-15 handoff predicted would collide — cart PDF,
screenshot, DWR PDF, BPO check, punch-out pricing — routed 5/5 in **both** conditions,
before and after. That prediction was wrong, and it took measurement to find out.

### The ambiguous set is the one that pays

`queries-ambiguous.json` holds queries with no single defensible answer. They are read by
hand, not scored by the pass threshold — what you want to see is the skill *declining to
guess*.

| Query | Baseline | After |
|---|---|---|
| "Can you check these Grainger items? 4CZ16, 6YPH8" | punch-out **pricing** ran, 4/5 | asks which, 5/5 |
| "Pull the Grainger numbers out of items.pdf" | **cart** skill ran, 3/5 | asks which, 5/5 |
| "I need pricing on the items in rfq.pdf" | pricing ran, 5/5 | asks, 5/5 |
| "Here are some Grainger part numbers: …" | asks, 5/5 | asks, 5/5 |

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
