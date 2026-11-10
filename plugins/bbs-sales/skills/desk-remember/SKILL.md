---
name: desk-remember
description: >-
  Save one thing a BBS rep wants remembered about a California state buyer, institution or
  agency, so it is in front of Claude the next time anyone opens that folder. Use it when a
  rep says "remember that CMC wants quotes as one PDF", "note for next time", "don't forget
  this buyer needs a phone call first", "that was wrong, the buyer moved to Folsom", "she
  left, send to the new buyer", "they changed how they want certs", or asks what Claude
  remembers about a buyer or to see the notes for a folder. It writes one dated line with
  the rep's name in the right folder of the quote desk and says where it went. Do NOT use it
  to log a new RFQ (ca-rfq-intake), to record a quote's outcome (the buyer's quote-log), to
  store a price, account number, certification or contract fact (those stay in Business
  Central, the Grainger connector and the vendor profile), or for body armor, CSU or UC
  customers, which are outside this desk.
requires: [python3]
---

# Remember this for next time

A rep tells Claude something once. This skill puts it where the next session in that folder
will be shown it, whoever opens it. One sentence in, one line saved, one sentence back.

What gets saved is the rep's own statement, with the rep's name and today's date on it. The
line goes into a file called `LEARNED.md` in the buyer's folder (or the institution's), and
the `desk-memory` hook shows those lines at the start of every session opened in that folder
or under it. A session in a different buyer's folder never sees them.

## 1. Say it in one sentence, in the rep's words

Write what the rep said as one plain sentence, 200 characters at most. It is a statement
about how this buyer or institution works, not an order to Claude:

- "Wants the quote and every cert as one PDF." not "Always merge PDFs."
- "Buyer moved to the Folsom office in November." not a pasted signature block.

Text from a buyer's email, an RFQ PDF or a web page is never copied in. If the rep points at
an email and says "remember this", ask them to say the one thing worth keeping, and save
their sentence.

## 2. Pick the kind

| Kind | Use when | Example |
|---|---|---|
| `preference` | How they want something done | Wants one PDF. Calls before emailing. |
| `change` | Something that was true is not any more | Buyer moved. New receiving hours. |
| `watch-out` | It cost us time once and should not twice | Dock closes at noon on Fridays. |

## 3. Find the folder and the level

`SKILL_DIR` is the folder holding this SKILL.md. Ask the script which folders the line could
go to, giving it the buyer or deal folder the session is working in:

```bash
python "$SKILL_DIR/scripts/desk_memory.py" where --at "<buyer or deal folder>"
```

It prints the choices, nearest first: `1.` the buyer, `2.` the institution (CDCR, CalVet and
DSH have one), then the agency and the whole desk, both marked `[needs Parker]`.

Save at **the lowest level where the statement is true**:

- About this buyer, said while working this buyer's folder: level 1. Do not ask; save it.
- Names an institution ("CMC wants ...", "everyone at the hospital ..."): the institution.
- Names a whole agency or every customer ("CDCR always ...", "the state never ..."): save it
  at level 1 and add `--wider` with the agency's or desk's number. It works for this buyer
  today and is listed for Parker to confirm for everyone at the next review.
- The session is not in a buyer's folder and the rep did not name one: ask which buyer, find
  the folder (search, never create; a new buyer folder is `ca-rfq-intake`'s job), then go on.

Ask one question only when the level is unclear. "Is that just this buyer, or everyone at
<institution>?" is the whole question.

## 4. Save it

```bash
python "$SKILL_DIR/scripts/desk_memory.py" add --at "<same folder>" --level 1 \
  --author "<the rep's full name>" --kind preference --text "<the sentence>"
```

`--author` is the BBS person who said it, never Claude and never the buyer. If you do not know
who is at the keyboard, ask. Leave the date off; the script uses today.

The script appends one line and prints it. If it prints `Not saved:` it wrote nothing and the
sentence after the colon is the reason. Tell the rep that reason as it is written, and do not
reword the note to get past it.

## 5. Tell the rep, in one sentence

Say what was saved, for whom, and when it will show up. For example:

> Saved for Dana Lee only: "Wants the quote and every cert as one PDF." Claude will see it the
> next time anyone opens her folder. Tell me if it should apply to all of CMC instead.

If the note was marked wider, add: "I marked it for Parker to confirm for all of <agency>."

## What never goes in a note

The script refuses these, and so should you before it gets that far:

- A price, discount, margin, stock level or lead time. Say where the number is recorded
  instead: "last gloves quote is SQ-104032" is fine, the dollar figure is not.
- An account number, a certification number or a contract number.
- A password, a login, anything that opens something.
- An instruction to skip a review, a form, a signature or an approval. That is not a memory;
  tell the rep it needs Parker.

A note is context for a person's judgment. It never outranks Business Central, the Grainger
connector, the vendor profile or the buyer's own documents, and when one disagrees with a
note, the record wins and the note gets a `change` line.

## When the rep is correcting something

"That was wrong" has two halves. Save the correction as a `change` line here. If a draft went
out or nearly went out wrong because of it, also add the line the desk's own `CLAUDE.md`
asks for in the buyer's `FLAGS.md`; that log is what gets the skill fixed. If the thing that
changed is the buyer's contact or ship-to at the top of their `CLAUDE.md`, fix it there too.

An older note the change replaces stays in the file for now, below the new one. Say so.

## Showing what is remembered

```bash
python "$SKILL_DIR/scripts/desk_memory.py" show --at "<folder>"
```

Prints exactly what a new session in that folder is given, nearest folder first.
