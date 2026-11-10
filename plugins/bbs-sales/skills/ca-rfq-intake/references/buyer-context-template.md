# Buyer folder markdown

Two files per buyer folder. They are the first thing read on the next quote, so they
earn their length by being short and specific — what the documents can't tell you.

## CLAUDE.md

```markdown
# <Buyer Name> — <Institution>, <Agency>

**Role:** <title>
**Reach:** <email> · <phone>
**Grainger account:** <number>   **BC customer:** <id>
**Ship to:** <address as they last confirmed it>

## How they buy

- <vehicle they use, and whether they name it>
- <format they send: worksheet, bare email list, portal>
- <turnaround they expect, and whether the deadline is real>
- <who else signs off on their side>

## What we've learned

- <accepted an equivalent on X / insists on exact part numbers>
- <recycled-content answers they've accepted>
- <forms they always require, including any beyond the standard packet>
- <anything that cost us time once and shouldn't twice>

## Open items

- <unconfirmed ship-to, missing account number, unanswered question>
```

Write the "learned" lines only when something actually surprised you. A file of
generic statements is worse than a short one, because it costs a read and returns
nothing.

## quote-log.md

```markdown
# Quote log — <Buyer Name>

| Date | Item | Quote # | Vehicle | Value | Outcome |
|---|---|---|---|---|---|
| 8.27.26 | Metal detectors ×15 | SQ-###### | NASPO | $2,630.40 | sent |
```

One row per request. Row order does not matter: the desk-context hook sorts by the Date
cell (`M.D.YY` or `YYYY-MM-DD`) and shows the newest first. Outcome is `sent`, `won`, `lost`, or
`no answer`. Name the source in the cell (`won - SO <number> per BC <date>`), and give `lost`
a clause on why, because that's the row the next quote learns from. A row older than 30 days
that still says `sent` is listed for close-out on the first write in this buyer's next deal
folder; if the outcome can't be sourced from Business Central or this folder, write
`[FLAG: why]` in the cell, never a guess.
