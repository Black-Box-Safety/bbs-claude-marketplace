---
name: usaspending-awards
description: >-
  Look up past federal contract awards on USAspending.gov: who won contracts under a NAICS
  code or at an agency, how much, and when; who the biggest vendors are in a federal market;
  what first-tier subcontracts a prime has reported; and BBS's own federal award history by
  its UEI. Read-only search of the public USAspending API, no key. Use when Kim, Griffin or
  any rep asks "who won the last VA award for NAICS …", "who's the incumbent", "what has
  DoD bought under 339113", "top vendors for body armor at DHS", "what federal awards has
  BBS won", or "who does Bechtel subcontract to". Do NOT use for open solicitations that can
  still be bid (sam-gov-opportunities), California state purchasing (SCPRS,
  ca-procurement-intel), BBS's own books (Business Central), or drafting a pursuit or deck
  (bbs-deck-voice). It only reads.
requires: [usaspending, python3]
---

# USAspending awards

A narrow lookup of **what the federal government already bought, from whom**. It is the
other half of `sam-gov-opportunities`, which lists what is open now. Together they answer
"what is open, and who usually wins this kind of work".

**Federal channel.** BBS is SDVOSB, VOSB and a small business federally; never DVBE. Those
facts, BBS's UEI, and its NAICS, PSC and GSA SIN codes live once, in `bbs-foundations`
`skills/bbs-claude-md-forge/references/canonical-facts.md` ("Certifications, by
jurisdiction" and "Federal codes"). Read them there for every run; never type them from
memory.

## Run it

Through the vetted launcher, which runs it without a permission prompt (Parker, 2026-10-02):

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/usaspending-awards/scripts/usaspending_awards.py" awards --naics 339113 --agency VA
```

| Mode | Answers | Amount means |
|---|---|---|
| `awards` | Which prime contracts match, largest first | USAspending's Award Amount for the whole award, all years |
| `top-recipients` | Who holds the most obligations in that market | Obligations on transactions dated in the window, not contract value |
| `subawards` | First-tier subcontracts primes reported (`--recipient` is the sub-awardee) | As the prime reported it |

| Flag | What it does |
|---|---|
| `--naics 339113,4234` | Codes or prefixes, all in one request. "Our NAICS" means canon's list; pass it. |
| `--agency VA` | Awarding toptier agency, by its exact USAspending name or abbreviation. A near miss is refused with suggestions, because USAspending answers a wrong name with zero rows and no error. |
| `--recipient FRK5MJD35GN5` | One recipient name or UEI. BBS's UEI comes from canon. |
| `--keyword`, `--set-aside SDVOSBC`, `--state CA` | Keyword, set-aside codes, place of performance. |
| `--start / --end` | YYYY-MM-DD, default the last three years; nothing before 2007-10-01. |
| `--new-only` | Only awards first signed inside the window. |
| `--rows 25` | Up to 100. |
| `--json` | Machine-readable. |

At least one of `--naics`, `--agency`, `--recipient` or `--keyword` is required.

## Presenting the result

- **Keep the header.** It gives the source, the query time, the exact filters, the request
  count, whether more rows exist, and what the amount column means. Keep any
  "USAspending says" line too.
- **Every number is the API's.** No estimates, no shares of a market, no "likely incumbent"
  unless a row shows it.
- **Do not add amounts across modes.** The modes measure different things.
- **A total across rows is fine** when it is labelled as the sum of the rows shown.
- **"More exist" means the list is partial.** Never call a partial list the market.
- **An empty subaward result is not proof of none.** Only first-tier subawards that primes
  reported are in it; a supplier to a sub, as BBS is on Bechtel's Sentinel work, does not
  appear.
- **Exit 1 is a failure, exit 2 a refused input.** Say which, with the printed reason.
  Neither is "no awards".
- **Incumbents for a SAM.gov notice.** Run `awards` with the notice's NAICS and agency.
  `--new-only` with a recent window is the usual cut.

## Stop at the list

- No outreach to a recipient or contracting officer.
- No CRM write.
- No pursuit call; that is Griffin's.
- No bulk downloads.

Suggest the next step only: a pursuit deck is `bbs-deck-voice`, and open notices are
`sam-gov-opportunities`.

## Tests

`tests/test_usaspending_awards.py` runs offline against a fake USAspending. It covers:

- Search endpoints only, with the documented filters.
- Exact agency names, with near misses refused before searching.
- The input refusals.
- HTTP errors reported as failures.
- What each amount means.
- The empty-subaward caveat.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/usaspending-awards/tests/test_usaspending_awards.py"
```
