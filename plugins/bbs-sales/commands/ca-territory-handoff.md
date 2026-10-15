---
description: Segment a California state agency book by relationship state and turn it into a dated, prioritized call list — bands, the ranked at-risk list, and the words to open each call. Stops before any outreach is written.
---

# /ca-territory-handoff

A rep is taking over a book, or a book needs re-homing, or someone wants to know which accounts are at risk. Turn the book into something a rep can work on Monday. Run the `ca-territory-handoff` skill and follow it. This command is **order and gates only**: every rule, threshold and formula lives in the skill, and nothing below restates one.

1. **Scope** — skill §1. Take the book's exclusions from `bbs-foundations` `references/canonical-facts.md`, "CA state book scope"; invoke `ca-state-sales-grounding` for additional context where it is installed. *Gate:* if Business Central is unreachable, stop — there is no book to band.
2. **Pull the book by facility** — skill §1, the field table. *Gate:* a field that is unavailable is "data pending", never an estimate.
3. **Band it** — skill §2. The band rules and the silence test are there; apply them as written.
4. **Find what the departed rep took, and the zero-threaded accounts** — skill §3.
5. **Rank by dollars at risk** — skill §4, including its one-time-buy and partial-month traps.
6. **Size the pond** — skill §5 and `references/pond-sizing.md`. *Gate:* if the ca-procurement-intel connector is absent, pond sizing is "data pending".
7. **Anchor the dates** — skill §6, which invokes `ca-budget-timing`. *Gate:* no deadline restated from memory; say plainly when a target's arithmetic does not work.
8. **Write the dated call list** — skill §8 and `references/opening-lines.md`, with the definition of done from skill §9.
9. **Report and stop.** *Gate:* no outreach sequence, no email draft, nothing sent — sequences belong to the `sales-*` craft skills (Sloane, where installed).

Then hand off per the skill's *Handing off* section: a request or worksheet goes to **`/ca-rfq`** (Gate 0 is intake, through `ca-rfq-intake`), a NASPO order or item-number pricing ask to `naspo-quote`, and a segment that wants a promotion to `grainger-promo-page`.
