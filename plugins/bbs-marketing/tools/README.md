# tools

## brand_check.py

`brand_check` is the blocking gate that runs before a marketing piece is rendered
or sent out. It reads `references/CLAIMS.md` — the registry of approved claim wording —
and audits a piece for three things:

- **superseded** wording that the registry has replaced (a defunct certification
  authority, a transposed contract number, a stale contact email)
- **expired** claims that are still printed after their re-verification date
- **missing** wording that the registry marks `required` for the scope you name

It exits `1` on any finding and `0` on a clean piece, so it can gate a build. It
exists because pieces shipped with all of those errors: `VA CVE Verified SDVOSB`
(the VA stopped certifying veteran-owned businesses in January 2023), contract
`1-23-87-04` instead of `1-23-84-07`, "headquartered in San Diego" instead of
El Cajon, and `jackson@blackboxsafety.com` in a footer.

### Run it on a piece

Point it at rendered HTML or extracted text, and name the tracks the piece belongs
to with `--scope` (repeatable). Scope is what decides which claims apply:

```
python3 tools/brand_check.py \
  "../claude-marketing/joey-marketing/campaigns/projects/2026-07-ladwp-grainger-leavebehind/brochure.template.html" \
  --scope mro --scope agency
```

```
brand-check FAIL  .../brochure.template.html  (3 finding(s))
  [superseded] dvbe-cert: found 'CA SB/DVBE Cert. 2009473'; approved wording is 'CA DVBE Cert. 2009473'
  [superseded] sdvosb: found 'VA CVE Verified SDVOSB'; approved wording is 'SDVOSB'
  [missing] agency-disclaimer: required wording absent for scope 'agency': ...
```

For a PDF, extract the text first (`pdftotext piece.pdf /tmp/piece.txt`) and audit
the text file. Anything set as artwork rather than live text — badge lockups, logo
lettering — is invisible to the gate.

`--claims` overrides the registry path; it defaults to `references/CLAIMS.md`.

Worked examples of real audits, with every finding explained, are in
`tools/tests/BASELINE.md`.

### Run the tests

System Python on this machine is 3.9.6 and has no pytest, so `python3 -m pytest`
will not work. Use a venv:

```
python3 -m venv /tmp/bbs-venv && /tmp/bbs-venv/bin/pip install -q pytest
/tmp/bbs-venv/bin/python -m pytest tools/tests/test_brand_check.py -v
```

The venv is for the test runner only.

### Stdlib only, by design

`brand_check.py` imports nothing outside the Python standard library, so the CLI
runs anywhere — any machine, any checkout, no install step — which is what lets it
sit in front of a build as a gate. Keep it that way: if a fix seems to need a
third-party package, it belongs somewhere else.
