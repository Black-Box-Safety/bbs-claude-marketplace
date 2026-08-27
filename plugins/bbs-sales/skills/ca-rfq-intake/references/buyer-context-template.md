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
| 8.27.26 | Metal detectors ×15 | 900008 | NASPO | $2,630.40 | sent |
```

One row per request, oldest last. Outcome is `sent`, `won`, `lost`, or `no answer` —
and `lost` is worth a clause on why, because that's the row the next quote learns from.
