# Authoring a `manufacturer_family_rules` row

The rule is the whole brain of the rollup. The generator (`etl/nonapparel_family_rollup.py`,
`Rule.from_row`) consumes one row per manufacturer.

## Schema (columns)
- `manufacturer_id` — FK; one row per manufacturer (UNIQUE).
- `parse_method` — `regex` | `llm` | `firecrawl` | `manual` (informational; regex is the executed path).
- `style_key_rule` (JSONB) — how to derive the family identity shared by all members. Two shapes:
  - single regex: `{"source":"sku"|"name", "pattern":"(?P<style>...)"}` — the named `style` group is the key.
  - procedural peel: `{"source":"name", "steps":[ "normalize ...", "strip <clause>", "peel trailing <axis>", "style_key = remainder" ]}` — for names where axes are trailing tokens.
- `axis_rules` (JSONB) — list of `{"axis":"<approved axis>", "source":"sku"|"name", "pattern":"(?P<val>...)", "value_map":{"raw":"Canonical"}}`. Each extracts one option axis's value per member.
- `min_size` — smallest family (default 2). `status` — `draft` while iterating, `approved` when ready.
- `notes` — document deviations/gaps for the next author.

`style_key` groups members; `axis_rules` values must be UNIQUE per member within a family (no duplicate
option-combos) or the family is rejected to review. Product TITLE is derived from member NAMES (axis values
stripped) — not the style_key — so SKU-keyed vendors still get readable titles.

## Approved axes (≤3 per family) and canon
`Color, Finish, Model, Formulation, Grip, Fitment, Mount, Size, Length, Width`. Canonical spellings live in
`rollup-standard.md §3` (e.g. XXL not 2XL; Title-Case colors; MultiCam/OD Green/Hi-Vis preserved). `Finish` =
coating of a hard good (Black Chrome/Airweight/Electroless; Dark Earth/Foliage) — use it, not Color, for hard
goods. `Fitment` = firearm/device fitted. `Mount` = attachment/hardware config (Tek-Lok/ASR; w/ Hardware/Bulk).

## Klass gate (what the generator enforces)
- klass **A** = 2–150 members, ≤3 axes, every member a unique option-value combo → rollable.
- singleton (1) → standalone. >150 → oversized (review). duplicate combo / unparsed / ambiguous → review.

## Worked examples (from the reference rollout)
- **Eberlestock (name peel, Color[+Size]):** SKU color letters unreliable → parse NAME.
  `style_key_rule: {"source":"name","steps":["normalize separators","peel trailing Color","peel trailing Size","style_key=remainder"]}`;
  Color axis regex over camo/pattern names (patterns ARE colors), Size axis over liter/S-XL/waist. → "Bandit Pack" (6 colors), "Cirrus Ultralight Dry Bag" (Color×Size). 104 families.
- **S&S Precision (SKU suffix, Color+Mount):** `style_key` = SKU base with color/mount suffix peeled; decode
  suffix tokens (BK/CT/MC/TV…) via value_map. Landmine: `TW` = Team Wendy (a Fitment token), NOT Tan.
- **ASP (Length×Finish grids + Fitment):** baton SKUs `52[len][finish]`; "Friction Baton" = Length(16/21/26")×Finish(Black Chrome/Airweight/Electroless). "Sentry" vs "Friction" vs "Protector" are different MODELS → different style_keys.
- **Blade-Tech (name Fitment/Mount/Color):** opaque SKUs → NAME parse. "Signature Double Mag Pouch - <firearm> - <ASR|Tek-Lok>". RH/LH kept in style_key (distinct molds = separate cards, not an axis).
- **Streamlight (name peel + leading fitment parenthetical):** peel trailing Color + a leading `(gun rail)`
  Fitment parenthetical; keep packaging/voltage/TAA INSIDE style_key so twins don't merge.

Full rules + counts for all 9 vendors: `docs/plans/nonapparel-dryruns/dryrun-<vendor>.md` in the
bbs-database repo (locate it via `site-wiring-map`; do not assume an absolute path).

## Known generator gaps (route to review, never corrupt — extend the generator to recover)
- **No default-axis-value:** a base SKU with no color token meant to = "Black" (SureFire `-BK` absent,
  Streamlight TLR-1 HL) can't be expressed → those members go to review. Add a `default` to the axis rule to fix.
- **No per-line allow-list / mid-SKU capture:** shared SKU roots that mix distinct subtypes (S&S SC/IFMSF,
  Nightstick parts sharing a series number), or a variant digit in the MIDDLE of the SKU (Team Wendy CloudLine
  `09-3X-001`), can't be split/captured by one global regex → under-collapse to singletons.
- **No noise-clause stripping in titles:** names with "Includes …"/stray parens leave title clutter (Streamlight).
- **One global rule per manufacturer** (no per-product-class routing) — messy multi-class catalogs (SABRE) lose
  a few families. Fine to accept + note; recover later by extending the generator.

## Per-vendor subagent brief (for a NEW manufacturer)
Dispatch one subagent per manufacturer to do the authoring + dry-run (prep only — it may upsert its ONE rule
row, but NO `--commit`, NO roll). Give it:
- The vendor name + its manufacturer_id (or have it look it up).
- This file + `rollup-standard.md`.
- The task: sample all unfamilied active members; study naming/SKU; author a generator-compatible
  `manufacturer_family_rules` row (name-parse where SKUs are opaque; approved axes; value_maps); Firecrawl the
  manufacturer site for 3–5 ambiguous lines; run `--dry-run --out`; self-review (counts vs expectation,
  `integrity_problems` empty, no family >150, axes approved, 3 sample families); report GO/NO-GO + counts +
  deviations + the prep JSON path. If the generator can't express the rule, encode the closest safe form and
  REPORT the gap (do NOT edit the generator — that's serialized on the main thread to avoid conflicts).

Then the main thread reviews, checkpoints with the user, and runs `--commit` + the roll driver.
</content>
