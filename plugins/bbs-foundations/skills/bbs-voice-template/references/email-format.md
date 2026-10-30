# BBS email format — layout and question discipline

Read from Parker Marshall's Sent Items on 2026-10-30: his quote requests to vendors (a
medical supplier on 2026-10-28, three instrument suppliers on 2026-10-30, a flag supplier on
2026-04-01), a quote cover note to a prime on 2026-10-29, and a one-line follow-up on
2026-10-30. Every rule below is what those emails do. The question discipline is Parker's
ruling, in session, 2026-10-30, on a generated draft that asked a buyer nineteen questions
in one unbroken numbered list: fewer questions, the deducible and off-critical-path ones
resolved by us, and the ones that remain spaced out.

This file ships unchanged inside every `<first>-voice` skill. The person's profile says how
they sound; this file says how the page is laid out and how many questions it may carry.
Where a person's own sent mail departs from it, their profile says so, and for them the
profile wins.

## The skeleton

Every external email is built from these blocks, in this order, with one blank line between
every block. Leave out a block that has nothing in it. Never merge two.

1. **Greeting**, on its own line: `Hi Sarah,` `Hello,` `Good afternoon,`
2. **Opener and context**, one short paragraph. The opener only when the relationship
   supports it ("I hope you're doing well! Thank you again for your help on the order this
   summer."), then the one sentence that says why the email exists and ends in the ask:
   "We're putting together a quote for {agency} and were hoping to get a quote from you on
   the following:"
3. **The list the email is about**: the items to quote, the questions, the notes. See
   "Lists".
4. **Item-specific questions**, one short paragraph each, directly under the list they
   refer to: "On item 1, can you confirm it includes the mounting hardware? The customer's
   spec lists it."
5. **Address blocks.** A lead-in line, then the address on consecutive lines with line
   breaks and no blank lines inside it:

   ```
   Items would ship to:
   {facility}
   {street}
   {city, state zip}
   ```

   Then, when the vendor may need it, `If needed, our bill to address is:` in the same
   shape.
6. **"Some quick notes:"** followed by the two to four requests that apply to every line:
   freight and delivered pricing, lead time, country of origin where it matters, spec
   sheets, pallet or packaging rules. One or two sentences each.
7. **The deadline, as a question with its reason**: "Are you able to get this back to me by
   2PM Pacific on Monday? Our bid is due the next day."
8. **Closer**: "Please let me know if you have any questions. Thank you!"
9. **Sign-off** on its own line, a blank line, then the signature block from `assets/`.

A quick operational reply keeps blocks 1, 3 or 4, 8 and 9. The follow-up that works is
three lines: greeting, "I wanted to follow up and see if this had been quoted?", sign-off.

## Spacing

- One blank line between blocks. A paragraph is one or two sentences about one thing.
- A list gets a lead-in line that ends with a colon, a blank line before the lead-in, and a
  blank line after the last item. No list runs straight into the next paragraph.
- Address blocks and the signature use line breaks, not blank lines, between their lines.
- Nothing in the body is bold (pattern 15 in `ai-patterns.md`). Bold labels inside a list
  (pattern 16) are the surest sign a draft was generated. The only bold is the signature
  block's own.
- No em dashes (pattern 14). A period, a comma, or a colon.

## Lists

- Numbered for the items being quoted and for requests the reader works through in order.
  Plain dashes for notes.
- **Five items is the ceiling for one list.** Past that, split into groups, each with its
  own lead-in line and its own blank lines: "On the batteries and chargers:" then "On the
  connectors:". A reader scans a group of three and skips a list of nineteen.
- When the lines carry a part number and there are more than about five, use a table
  (Item | Mfr # | Qty) instead of a list. The header row is the only bold.
- A line item reads "Description, qty N" or "N units of {link}". The link goes on the item
  when the rep has one.

## Questions to a buyer or a vendor

A question costs the reader a decision and costs BBS a day. Before any question goes into a
draft, every candidate passes these four checks, in order:

1. **Resolve what the documents already answer.** The spec, the line table, the drawing,
   the manufacturer's published sheet, the prior order, the catalog. When a table and a
   spec disagree, look for the solicitation's order-of-precedence clause first. If there is
   none, pick the reading the quote will be priced on, say which, and note the other in the
   quote notes.
2. **Drop what does not change the quote.** If either answer gives the same price, part,
   quantity and delivery, it is not a question. State the assumption in the quote notes:
   "Quoted the 10 ft length per the table; the section header reads 4 ft."
3. **Decide the rest with the more likely reading, and say so.** A buyer corrects a stated
   assumption faster than they answer an open question.
4. **Ask only what is left**: unresolvable from the documents, and it moves the number or
   the part. A short list. More than about five surviving questions means the quote is not
   ready, or the questions belong on a call, not in an email.

The ones that survive go in as blocks 3 and 4 of the skeleton: grouped by topic, a lead-in
line per group, one sentence per question, the answer deadline and its reason up front
("Answers by Monday would help, since the quote is due Tuesday.").

## Rendering

In a Microsoft 365 connector draft, each block is its own `<p>`, a list is `<ol>` or
`<ul>`, address lines break with `<br>`, and a line-item table is a plain `<table>` with a
header row. The connector's outbound allowlist admits those and strips `style`, `class`,
`id` and `<img>`, so there is no other formatting to lose. In plain text, a blank line is the
block separator and a list is `1.` or `-` at the start of the line.

## Before and after

**Generated:** one numbered list of nineteen clarification questions to a buyer, no groups,
no spacing, every discrepancy the reviewer found asked back whether or not it moved the
price.

**In the house format:** two or three groups with lead-ins, a blank line around each, one
sentence per question, five questions at most, the rest resolved and stated as assumptions
in the quote notes, the answer deadline and its reason in the opening paragraph.

---

Owner: Parker Marshall. Source: his Sent Items, read 2026-10-30; ruling in session the same
day. Part of `bbs-voice-template`; copied unchanged into every `<first>-voice`.
