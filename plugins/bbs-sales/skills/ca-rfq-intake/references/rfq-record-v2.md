# RFQ.md v2 reference

Format of the run record the parser (`plugins/bbs-sales/scripts/rfq_record.py`) reads and
the hook validates. Template: `rfq-record-template.md`. Schema version 2. The JSON sidecar
is derived and regenerable; RFQ.md is the record.

## Header keys (in order)

Each is a `**Key:** value` line. Unknown is `[FLAG: why]`, never a guess.

- Received: date and channel (email, portal, phone). From the request.
- Buyer: name, title, email, phone. From the request or the buyer CLAUDE.md.
- Agency / institution: from the folder path.
- Grainger account: from the buyer folder name or note. Buyer notes override the folder name.
- BC customer: Business Central customer id (read, not typed from memory).
- Ship to: address from the request.
- Due: date, time, timezone.
- Submit via: email address, portal, or the buyer's sheet.
- Solicitation #: number, or "none issued - reference BBS quote".
- Vehicle: NASPO ValuePoint, DGS BPO, or competitive.
- Pricing rule: at cost, no markup, or bid (margin is the rep's call).
- Rep: Kim Quezon or Aanya Samarasinghe, from the buyer CLAUDE.md Account owner line.
- CRM RFQ: RFQ-00xxxx, or `[not in CRM]`. Looked up read-only; never created here.
- BC quote: SQ-10xxxx, or `none`. Set when the quote is read back from BC.
- PC quote: Provision Connect number (Q 1xxxx) from the saved PDF name, or `none`.
- Stage: one value from the stage enum. The highest Status row with a date.

## Tables

Lines (what the buyer asked for): `| # | Item / part # | Description | Qty | UOM | Lane |`.
Lane is grainger, catalog, sourcing or FLAG.

Pricing (one row per line): `| # | Vendor | Vendor ref | Cost | Sell | Strategy | Lead | Line stage | Evidence |`
- Vendor: Grainger, the vendor's BC name, or `[sourcing]` while open.
- Vendor ref: Grainger SKU, CSP number, vendor quote number or file name.
- Cost, Sell: numbers only, excl. tax, or `[FLAG: why]`.
- Lead: lead time as stated by the vendor.
- Evidence: the file or record that proves the row.

Status: `| Stage | Date | Evidence |`, eight fixed rows in stage order, ISO dates. The
outcome row's Evidence carries one of the outcome values.

## Enums

- Stages: logged, sourcing, priced, quote built, packet built, delivered to rep, sent, outcome.
- Outcomes: won, lost, no answer, no bid, cancelled (the solicitation was withdrawn or not awarded).
- Line stages: open, sourcing, vendor quoted, priced, quoted, substituted, parked, no bid.
- Strategies: NASPO at cost, BPO price list, cost plus <n>% (matches `^cost plus \d+(\.\d+)?%$`),
  competitive bid, vendor quote, substitute offered, parked, no bid.

## Which stages apply

- NASPO through Provision Connect: logged, priced, quote built (PC quote), packet built only
  when Forms the buyer requires lists a form, delivered to rep, sent, outcome.
- DGS BPO release: logged, priced, quote built, sent, outcome.
- Competitive and Fair and Reasonable bids: every row.
- Sourcing applies whenever any Lines row has lane sourcing.
- Inapplicable rows are marked `n/a`. Next step is the first applicable row without a date.

## Never backward, never silent

A stage date, once written, is not removed or earlier-stage-overwritten. Stage never moves
to a lower row. A correction is a new Evidence note, not a silent rewrite. `set-stage` holds
these at write time:

- Same stage, same date: nothing changes; new evidence items (separated by `; `) are appended.
- Same stage, a different date, or an `outcome` with a different outcome word on any date:
  refused (`conflict`) unless `--correct "<reason>" --by <person>`. The new evidence then leads
  the cell, followed by `previously: <old evidence>` and who corrected it, when and why.
- Correcting a stage below the current one needs both `--force` and `--correct` (with `--by`).
- Dates are compared as dates: a Status date typed as `11/5/2026` reads as `2026-11-05`.
- `outcome` needs a dated `sent` row, except `no bid` and `cancelled`.
- A `sent` date is not before Received and not after today in California.
- A lower stage may fill its own empty date when that date is not after any later dated stage
  (a date fill). Any other backward write needs `--force --by <person>`, and the Evidence cell
  records `[forced by <person> <when> from <stage>]`.
- Every CLI write is refused while a OneDrive conflict copy (`RFQ-<COMPUTERNAME>.md`, or with a
  `-<n>` suffix) sits beside the record: merge it by hand and delete it first. A rep's own file
  is never taken for one: anything ending in `-notes` in any case (`RFQ-Notes.md`), a name with no
  letter in it (`RFQ-12345.md`, `RFQ-2026-11-12.md`), or any lowercase `rfq-…`.

## CLI synopsis

`python3 plugins/bbs-sales/scripts/rfq_record.py <command> <RFQ.md> ...` (stdlib only). Every
command takes the record path first. Writing commands re-validate before writing, write the
record, then rewrite `rfq-state.json` beside it. Exit codes: 0 ok; `validate` exits 2 and lists
problems on stderr; any other failure exits 1 with one line on stderr (a backward stage move
says `backward`).

```
F=scripts/tests/fixtures/v2_competitive_sourcing.md
rfq_record.py validate $F
rfq_record.py current-stage $F
rfq_record.py compile $F -o /tmp/rfq-state.json
rfq_record.py set-stage $F priced --date 2026-10-28 --evidence "Grainger MCP 880000001 2026-10-28" [--force --by "<person>"] [--correct "<reason>" --by "<person>"]
rfq_record.py set-header $F "BC quote" SQ-900002
rfq_record.py upsert-pricing $F --json '{"num": 2, "vendor": "Acme Valve", "vendor_ref": "QuoteCB0000024667.pdf", "cost": 310.0, "sell": 372.0, "strategy": "cost plus 20%", "lead": "5 days", "line_stage": "vendor quoted", "evidence": "QuoteCB0000024667.pdf"}'
rfq_record.py migrate scripts/tests/fixtures/v1_cmd_hvac.md --rep "Kim Quezon" --dry-run
```

`migrate` rewrites a v1 record in place and prints the judgment notes; it refuses a record
that is already v2. `--dry-run` prints the notes and writes nothing, not even the sidecar.
The sidecar records the deal path only when the RFQ.md path contains `All RFQ's by Agency/`.
