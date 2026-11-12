# bbs-quote-builder: Business Central SQ numbers — plan

Spec: `docs/superpowers/specs/2026-09-28-quote-builder-bc-sq.md`. Branch
`claude/quote-builder-bc-sq` off `origin/main` at `eccbab0`. Ends at a PR, not a merge.
Not touched (another worker records the ruling there): `docs/STEWARD.md`,
`canonical-facts.md`, `ca-form-rules.md`, `vendor_profile.json`.

## 1. `scripts/build_quote.js`

- Validation block before any math: reject top-level `quoteNumber` with a pointer to
  `bcQuote`; require `bcQuote.number` matching `^SQ-\d{6}$`, `bcQuote.customerNumber`,
  `bcQuote.customerName`; require non-empty `items[]`.
- Pricing: accept `margin | markup | at-cost`; `items[].source === "grainger"` forces
  at cost; fail if any non-Grainger line exists and method/rate are missing or unknown.
- `columns.leadTime` → Lead Time column, width taken from Description.
- Title prints `bcQuote.number`; summary line echoes number, customer, per-line basis.

## 2. `references/spec-schema.md`

Replace the `quoteNumber` row with the `bcQuote` rows; add `source`, `at-cost`,
`columns.leadTime`, `items[].leadTime`; update the math and the worked example (fixture SQ
number, one Grainger line).

## 3. `SKILL.md`

- Frontmatter: `requires: [business-central, node, docx-npm, libreoffice]`; description in
  a `>-` block, under 1024, no 900001 wording.
- Step 2 becomes "Read the quote back from Business Central" — rep creates the record, skill
  reads it, stops on `[MISSING — NEEDS INPUT]`. Explicitly: no prediction, no write.
- Pricing section: Grainger at cost with a pointer to canon; margin/markup kept for the rest.
- Naming example uses an SQ number.

## 4. Knock-ons

`naspo-quote/SKILL.md` §3 and `requires:`, its worked example note, `commands/ca-rfq.md`
Gate 5, `docs/MAINTAINER-GUIDE.md` bullet, `python3 docs/evals/build_skills_json.py`.

## 5. Verify

- `python3 scripts/check_marketplace.py` → 0 FAIL.
- `node --check scripts/build_quote.js`.
- Build a fixture spec (fake `SQ-100000`, one Grainger line, one margin line, lead time on)
  offline → docx → PDF via `soffice`; check the numbers. Negative runs: old `quoteNumber`
  spec, `900003`-style number, missing `bcQuote`, missing pricing — each must exit 1.
- `grep -rn 900001` — only counter-example / historical prose remains.
