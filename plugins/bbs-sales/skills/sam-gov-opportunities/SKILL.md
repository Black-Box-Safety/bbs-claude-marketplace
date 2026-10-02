---
name: sam-gov-opportunities
description: >-
  Look up open federal solicitations on SAM.gov by NAICS code, agency, solicitation number or
  title words, through the official Get Opportunities API, and say for each one whether BBS can
  respond to its set-aside as an SDVOSB, VOSB and federal small business. Read-only: one GET
  request per NAICS code, BBS's shared key from the SAM_GOV_API_KEY environment variable. Use when Kim, Griffin or
  any rep asks "what's open on SAM for NAICS …", "any SDVOSB set-asides at the VA", "is this
  solicitation still open", "federal opportunities in California", or wants the current list
  of open federal notices before a pursuit or a deck. Do NOT use for past federal awards,
  incumbents or spend (usaspending-awards), California state bids (ca-rfq-intake, SCPRS), drafting a
  response or a deck (bbs-deck-voice), or registering, bidding or submitting anything on
  SAM.gov — this skill only reads.
requires: [sam-gov, python3]
---

# SAM.gov opportunities

A narrow lookup. It answers one question: **which federal notices are open right now for this
NAICS code or this agency, and can BBS respond to them?** It does not research, bid, register,
draft or send anything.

**Federal channel.** Every line this skill writes uses **SDVOSB** (and VOSB for VA
veteran-owned set-asides), and calls BBS a small business only federally. It never says DVBE: that is the California state credential and has
no place in a federal answer. The certification facts are in `bbs-foundations`
`skills/bbs-claude-md-forge/references/canonical-facts.md`, "Certifications, by jurisdiction"
and "Small-business status is channel-dependent". BBS's NAICS and PSC codes are in the same
file, "Federal codes". Point there; never restate a number.

## Setup (once per machine)

BBS uses **one SAM.gov account and one shared key** for everyone (Parker, 2026-10-02: "It
will all link to the same sam.gov account, we dont need multiple").

1. **Parker gives you the value.** Do not request your own key.
2. **The bootstrap asks for it when run with the SAM.gov flag:** `bbs-setup.ps1 -SamGov`
   (Windows) or `bbs-setup.sh --sam-gov` (Mac). It prompts with hidden input and saves the key:
   to the user environment on Windows, to `~/.zprofile` on a Mac. Without the flag it asks
   nothing, so people who never use SAM.gov are not prompted. Then quit and reopen Claude.
   - By hand instead: on Windows, Start → "Edit environment variables for your account" →
     New, named `SAM_GOV_API_KEY`. On a Mac, add `export SAM_GOV_API_KEY='…'` to
     `~/.zprofile`.
3. **Never paste the key into a chat**, a repo file or a customer folder. If someone pastes it
   anyway, do not repeat it, save it or write it anywhere.

**One daily budget for everyone.** The key belongs to the SAM.gov account that holds BBS's
entity registration, so it is on the 1,000-requests-a-day tier, and every person's lookups
draw on that one budget:

- Each NAICS code costs one request.
- HTTP 429 means the day's budget is spent for the whole team: say so, and tell Parker.
- HTTP 401 or 403 usually means the key has lapsed. Its expiry date is in canon, "Federal
  codes"; say the lookup failed and tell Parker.

## Run it

Through the vetted launcher, which runs it without a permission prompt (Parker, 2026-10-02):

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/sam-gov-opportunities/scripts/sam_opportunities.py" --naics 339113
```

| Flag | What it does |
|---|---|
| `--naics 423450,339113` | One request per code, merged and de-duplicated. Up to 4 codes a run (`--max-requests`). |
| `--agency "Veterans Affairs"` | Department or sub-tier name search. |
| `--solnum 36C26226Q0123` | One solicitation. Add `--include-closed` to see it after its deadline. |
| `--keyword "gloves"` | Words in the notice title. |
| `--set-aside SDVOSBC` | One set-aside code, filtered by SAM.gov. |
| `--state CA` | Place of performance. |
| `--days 90` | Posted in the last N days (default 90, at most 364). |
| `--types o,k,p,r` | Notice types kept (default: solicitation, combined synopsis/solicitation, presolicitation, sources sought). |
| `--json` | Machine-readable instead of a table. |

At least one of `--naics`, `--agency`, `--solnum` or `--keyword` is required.

If `bbs-fill` is not found, the `bbs-tools` plugin is missing: tell the rep to rerun the
bootstrap, and in the meantime run the same line with `python` (Windows) or `python3` (Mac)
in place of `bbs-fill`, which will ask for permission. If it answers `REFUSED … is not a
vetted script`, `bbs-tools` is older than 0.2.0: tell the rep to update plugins and start a
new session. Neither is a SAM.gov failure; never report it as one.

**"Our NAICS codes"** means the list in canon, "Federal codes". Each code is one request,
so the whole list is over the default cap of 4. Ask which codes matter, or start with the
primary one; for the whole list, pass `--max-requests` equal to the number of codes in canon
(the script refuses anything over 20). Never supply a
code from memory.

## What comes back, and how to present it

The script prints a header and then one row per open notice, soonest deadline first:

- **Header lines.** Keep these in the answer: the source and query time, the query itself,
  the requests used, how many notices SAM.gov returned and how many matched, and what was
  excluded (closed or archived, and other notice types, each counted).
- **Rows.** Each row has the response deadline, title, agency and office, solicitation
  number, type, set-aside, BBS fit, NAICS, PSC, place of performance, and the sam.gov link.

Present the table as it came back. Rules:

- **Every value comes from the response.** Do not add an estimated value, an incumbent, a
  "likely" anything, or a deadline the row does not give. A row with `[none given]` stays that
  way.
- **BBS fit is the script's column, unedited.** It is computed from the set-aside code against
  canon:
  - SDVOSB set-asides are eligible, with a FLAG to confirm BBS is small under that NAICS
    size standard (every SDVOSB, VOSB and small-business set-aside carries it).
  - Small-business set-asides carry the same FLAG.
  - VA veteran-owned set-asides are eligible: BBS is VOSB (canon, ruled 2026-10-02), with
    the same size-standard FLAG.
  - Set-asides for certifications BBS does not hold say so.
  - An unknown code is flagged.
  
  Never upgrade a FLAG to "eligible" in the summary.
- **TRUNCATED means narrow the query.** One request reads at most 1,000 notices. Suggest a
  NAICS code, a state or a shorter window; do not offer to raise a cap.
- **A failure is a failure.** Exit 1 means SAM.gov did not answer. In particular, a 404 is
  **not** "no results": a refused request looks the same. Say the lookup failed and give the
  reason printed; never report it as "nothing open".
- **Zero rows on a successful run** is a real answer: say "No open notices matched", with the
  query, so the person can widen it.

A short closing line is fine: say which rows are SDVOSB set-asides and which deadlines fall
within the next 14 days. Nothing more.

## Stop at the list

- **No outreach.** No email to a contracting officer, and nothing written to the CRM.
- **No pursuit.** No bid or no-bid call; that is Griffin's.
- **No registration.** The skill never logs in to SAM.gov or touches BBS's entity record.
- **Points of contact.** The script deliberately leaves out the notice's point-of-contact
  emails and phones. They are on the sam.gov page behind the link.
- **Next steps.** Offer the obvious next ones as suggestions only: a deck for a pursuit is
  `bbs-deck-voice`; who won this kind of work before is `usaspending-awards` (`awards` with the notice's NAICS
  and agency).

## Tests

`tests/test_sam_opportunities.py` runs offline, with a fake SAM.gov, and covers:

- GET only, with the documented parameters.
- The key never printed and redacted from errors.
- The missing-key, narrowing-filter, one-year-window and request-cap refusals.
- 404 reported as a failure, not as an empty result.
- Closed and excluded notices counted.
- Truncation reported.
- The set-aside mapping, and no DVBE in federal output.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sam-gov-opportunities/tests/test_sam_opportunities.py"
```
