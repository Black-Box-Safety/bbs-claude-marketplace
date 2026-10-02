---
name: sam-gov-opportunities
description: >-
  Look up open federal solicitations on SAM.gov by NAICS code, agency, solicitation number or
  title words, through the official Get Opportunities API, and say for each one whether BBS can
  respond to its set-aside as an SDVOSB and federal small business. Read-only: one GET request
  per NAICS code, key from the SAM_GOV_API_KEY environment variable. Use when Kim, Griffin or
  any rep asks "what's open on SAM for NAICS …", "any SDVOSB set-asides at the VA", "is this
  solicitation still open", "federal opportunities in California", or wants the current list
  of open federal notices before a pursuit or a deck. Do NOT use for past federal awards or
  spend (USAspending, in Cursor), California state bids (ca-rfq-intake, SCPRS), drafting a
  response or a deck (bbs-deck-voice), or registering, bidding or submitting anything on
  SAM.gov — this skill only reads.
requires: [sam-gov, python3]
---

# SAM.gov opportunities

A narrow lookup. It answers one question: **which federal notices are open right now for this
NAICS code or this agency, and can BBS respond to them?** It does not research, bid, register,
draft or send anything.

**Federal channel.** Every line this skill writes uses **SDVOSB**, and calls BBS a small
business only federally. It never says DVBE: that is the California state credential and has
no place in a federal answer. The certification facts are in `bbs-foundations`
`skills/bbs-claude-md-forge/references/canonical-facts.md`, "Certifications, by jurisdiction"
and "Small-business status is channel-dependent". Point there; never restate a number.

## Setup (once per person)

1. **Get a key.** Sign in at sam.gov, open **Account Details**, and request a public API key.
   SAM.gov shows the key only once, until you leave the page.
2. **Put it in your environment, outside Claude.** On Windows: Start → "Edit environment
   variables for your account" → New → name `SAM_GOV_API_KEY`, value the key. On a Mac, add
   `export SAM_GOV_API_KEY=…` to `~/.zshrc`. Then quit and reopen Claude so the new session
   can see it.
3. **Never paste the key into a chat**, a file in a repo, or a customer folder. If someone
   pastes it into the conversation anyway, do not repeat it, do not save it, and tell them to
   generate a new key on Account Details.

**Daily limit.** A personal key on an account with no role on an entity gets **10 requests a
day**. One whose account has a role on an entity registration gets 1,000. Each NAICS code
costs one request. If a run comes back with HTTP 429, the day's budget is spent: say so, and
say that a role on BBS's entity registration raises the limit (Parker arranges that).

## Run it

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sam-gov-opportunities/scripts/sam_opportunities.py" --naics 423450
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

**BBS's own NAICS codes are not on file in this marketplace.** If someone asks for "our
NAICS codes", do not supply any from memory or from a past document: ask which codes, or
write `[MISSING — NEEDS INPUT: BBS NAICS codes]`. A plausible code is the failure this rule
prevents.

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
  - SDVOSB set-asides are eligible.
  - Small-business set-asides carry a FLAG to confirm the size standard for that NAICS.
  - VA veteran-owned set-asides carry a FLAG, because canon records SDVOSB, not VOSB.
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
  `bbs-deck-voice`; past awards to an agency are USAspending (Cursor, `bbs-usaspending`).

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
