---
name: bbs-order-reconciliation
description: >-
  Diagnose and resolve a problem on an order BBS has already taken — wrong item or size
  delivered, a price or unit-of-measure discrepancy on a PO line, a shortage, a lost shipment,
  extras shipped free of charge, an item discontinued mid-order, a pending return or credit, a
  vendor credit that never arrived, or a customer asking for an amended purchase order. Use
  whenever someone reports that something is wrong with an existing order, invoice, shipment
  or PO line, however vaguely — "the gloves are wrong", "there's a price discrepancy", "we're
  short on this line", "did we ever get that credit" — and whenever purchasing or AR needs to
  reconcile a customer PO against what we quoted, what we ordered and what actually shipped.
  Use it before replying to the customer, before processing a return and before reordering,
  because the fix depends on which of those three records is wrong. Do NOT use for new quotes
  or bids that have not been awarded — those are naspo-quote and ca-rfq-intake.
requires: [business-central, grainger, microsoft-365, python3, openpyxl]
---

# Reconciling a problem on an existing order

A problem on a live order is almost never what it looks like in the email that reports
it. Someone says "the price is wrong on the PO" — but the PO is just a mirror. It
reflects whatever we put in the quote, which reflects whatever our sourcing sheet said,
which reflects whatever the rep pasted in from a vendor page in a hurry three months ago.
The reported symptom is the last link in a chain, and the fix has to attach to the
broken link, not the symptom.

So the core discipline here is: **do not resolve anything until you can say which record
is wrong.** There are four records, and exactly one of them usually is:

1. What the customer asked for (the RFQ / their original line description)
2. What we quoted them (the submitted cost worksheet)
3. What their PO says (the document we are contractually held to)
4. What we actually ordered and shipped (BC sales order, vendor order, packing slip)

The person reporting the problem can usually only see one of these. You have access to
all four. That is the whole value of this skill.

The second discipline: **the problem is rarely limited to the PO in front of you.** These
orders go out in families — one bid, ten prisons, ten POs built from the same worksheet.
If a line is wrong on one, check whether that line exists on the others before you answer.
Finding the sixth affected PO after you have already told the customer about the first is
much worse than taking twenty more minutes up front.

---

## Phase 0 — Pin the report down

Before opening anything, get these straight. If the reporting email does not say, ask.

- **PO number(s)** — the customer's number, e.g. `4500755180`
- **Line number on the PO** — not our internal line number; they are different
- **The item** — manufacturer part number if you have it
- **Institution / ship-to**
- **The symptom in their words** — quote it, don't paraphrase it yet

Write these down. Everything below hangs off them.

If the report is vague ("the gloves are wrong"), do not guess which of the many possible
wrongs it is. Resolve that first — a size problem and a price problem have completely
different fixes, and the customer usually knows which one they mean.

---

## Sizing the job before you start it

Not every problem earns twelve phases. The person using this skill is the same person who
should be managing vendors and negotiating terms, and an afternoon spent proving a $9 line
was mispriced is an afternoon taken from work that compounds. Decide the depth up front
and say which depth you chose, so it is a deliberate call rather than drift.

- **Under a few hundred dollars, single order, obvious cause** — confirm the cause, fix it,
  record it. Phases 2, 4, and 11 only. Do not run the full sweep.
- **Repeating, or spanning several orders, or above roughly a thousand dollars** — full
  workflow. The blast-radius and precedent phases are where the value is, and they are the
  ones people skip under time pressure.
- **The customer is already unhappy, or someone has promised them something** — full
  workflow regardless of dollar value. The exposure is the relationship, not the line.

If the investigation runs long without converging, stop and say what you know, what you do
not, and what it would take to close the gap. A partial answer delivered today is worth
more than a complete one on Thursday, because the customer is waiting either way.

---

## Phase 1 — Find where the order lives

Customer work lives under the Customers root:

```
Black Box Safety - MASTER/Customers/<Agency>/<Sub-org>/<Project>/
```

For CDCR the path is deeper than people expect — the institution is not the top level.
A CDCR DRP project looks like `Customers/CDCR/DRP_/PLUMBING 2026/`, and inside a mature
project folder you will find the records you need in predictable places:

| Folder | What it holds | Why you care |
|---|---|---|
| `DRP PO's/` | The customer PO PDFs | Record 3 — what we are held to |
| `DRP PO's/_ocr/` | Searchable text of those PDFs | Grep this instead of opening PDFs |
| `1. Processing Sheets/` | Per-PO order sheets | Our line-by-line working record |
| `presubmission-work/` | What we bid, and the sourcing behind it | Record 2, and the intent behind it |
| `BC Import/SO Lines/` | What got loaded into Business Central | Record 4's starting point |
| `prison-folders/` | Per-institution copies | Often carries notes the master lost |

Folder names are inconsistent across projects — misspellings, trailing underscores,
year suffixes, "copy" duplicates, and archived variants are all normal. Find the project
by searching for the PO number rather than by browsing:

```bash
grep -rl "4500755180" "Black Box Safety - MASTER/Customers" 2>/dev/null
```

If several folders match, prefer the one with a `_ocr/` directory and processing sheets —
that is the working copy. Folders named `DO NOT USE`, `copy`, or `_ARCHIVE-*` are exactly
what they say.

`references/where-things-live.md` has the fuller map, including what the per-PO order
sheet tabs mean and which ones carry rep notes.

---

## Phase 2 — Read the PO of record

Pull the line from the OCR text, not the PDF. Grep with context:

```bash
grep -n -B8 -A8 "34-874" "DRP PO's/_ocr/CTF_combined.txt"
```

Capture, verbatim:

- **Unit of measure** — `EA`, `PAC`, `PK`, `PR`. This one field causes more post-award
  problems than any other, because a pack priced as an each is off by the pack quantity
  and nobody notices until the invoice.
- **Unit price and extension** — check the arithmetic; extension ÷ qty tells you the
  unit price the customer actually believes they are paying
- **Quantity**
- **The full description as printed**, including any size and pack-count language

Then read the PO header, which people skip and then have to come back for. It carries the
names you will need in Phase 7:

- Agency contact / buyer (the `CONTACT NAME` and email block)
- The Procurement Official who signed it
- LPA / contract number and purchasing authority number
- The local institution contact and phone

A CDCR STD. 65 puts the buyer's email in the header block and the authorizing signature
near the bottom of page 1. They are usually different people with different powers.

---

## Phase 3 — Reconstruct what we quoted, and what we meant to quote

This is the step that finds the real error, and the step people skip.

Open the processing sheet for that PO and find the line. Then open the presubmission
sourcing workbook and find the same master line number. You are looking for a **mismatch
between the submitted line and the sourcing intent behind it.**

The pattern to watch for: the same dollar figure appearing under two different
denominators. A sourcing tab computing 360 each × $2.89 = $1,040.40 and a bid tab
computing 30 packs × $2.89 = $86.70 are the same number doing two different jobs. The
second one is wrong, and it is wrong in a way that looks completely normal on the page.

A fast way to see every place an item appears across a project (`python` is the
interpreter `scripts/bbs-setup.ps1` installs on Windows, where `python3` is only the
Microsoft Store stub; on a Mac, use `python3` — the same rule for every command here):

```bash
python - <<'EOF'
import openpyxl, os
TARGET = "34-874"          # mfg PN, Grainger SKU, or a distinctive description word
for root, dirs, files in os.walk('.'):
    if '/.' in root: continue
    for f in files:
        if not f.endswith('.xlsx') or f.startswith('~'): continue
        p = os.path.join(root, f)
        try: wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
        except Exception: continue
        for ws in wb:
            for r in ws.iter_rows(values_only=True):
                s = ' | '.join(str(x) for x in r if x is not None)
                if TARGET in s:
                    print(f"{p} :: {ws.title} :: {s[:220]}")
EOF
```

Run this from the project root. It is the single highest-yield command in this skill —
it shows you the item's whole life across sourcing, bid, processing and BC import in one
pass, and the inconsistency usually jumps out of the column alignment.

---

## Phase 4 — Price and identify the item live

Never trust a cross-reference in a spreadsheet. Verify it against the vendor now.

For Grainger items, price against **the account that actually buys** — pricing is
per-account and the wrong account returns a wrong number that still looks valid:

```
grainger_price(productCodes=["19K974"], account="Correctional Training Facility")
```

If the account name is not recognized, the error message lists valid ones; institution
names usually resolve better than abbreviations (`Correctional Training Facility`, not
`CTF`).

Then check four things against the customer's description — not just price:

| Check | Failure it catches |
|---|---|
| Manufacturer part number matches | Cross-reference points at a different product |
| **Brand** matches | Substitute from another maker slipped in |
| **Size** matches | Right glove, wrong size — very common |
| **UOM and pack quantity** match | Each vs pack — the expensive one |

A cross-reference can be wrong on all four at once and still sit quietly in a sheet for
months. If the mfg PN in the customer's description does not appear in the vendor record
you just pulled, the cross-reference is broken — search the vendor catalog by the
manufacturer part number instead and find the item that actually matches.

Also record current stock status. "Discontinued" is frequently a misreading of a broken
cross-reference: the wrong item is dead, the right item is in stock.

---

## Phase 5 — Find out what actually happened

Business Central holds record 4. Useful entry points:

- `bc_get_sales_document` with the SO or invoice number — header plus all lines
- `bc_customer_snapshot` for the institution — open orders, quotes, unpaid invoices
- `bc_list_open_sales_orders` — "open" means not fully shipped, not draft status

Compare the BC line against the PO line: item, quantity, UOM, unit price. A divergence
here means the problem entered at order entry, not at bid time, which points at a
different fix and a different person.

Watch for duplicate sales orders. The ProCo integration has produced them, and a doubled
line looks like an overshipment to the customer and like a shortage in the numbers.

---

## Phase 6 — Recover the context that never left the rep's inbox

This is where the answer usually is, and it is the hardest part for anyone who was not on
the original thread. Reps resolve things verbally and in one-off replies, and none of it
reaches the folder.

Search email deliberately, in this order:

1. **By PO number** — `outlook_email_search(query="4500755180")`. Catches the award, the
   amendments, the shipping notices, the complaints.
2. **By item number** — both the manufacturer PN and the vendor SKU. Catches the sourcing
   conversation where the substitution was decided.
3. **By the customer contact's name or address** — catches promises made directly to them.
4. **By the symptom word** across a date range — "shortage", "credit", "RMA", "amended",
   "discontinued", "wrong size".

Read the full body of anything promising, not just the summary line — the operative
sentence is usually buried in a quoted reply four levels down. Long HTML emails exceed
the tool's return limit; when that happens the result is saved to a file, and stripping
the tags makes it readable:

```bash
python -c "
import re
t = open('<saved-file>', encoding='utf-8', errors='replace').read()
t = re.sub(r'<[^>]+>', ' ', t); t = re.sub(r'\s+', ' ', t)
i = t.find('<a phrase you expect>')
print(t[max(0,i-2500):i+3000])
"
```

Specifically hunt for:

- **An approval already given** — and by whom (Phase 7 decides whether it counts)
- **A promise already made** to the customer that we now have to honor or walk back
- **An unanswered question** from us to them, which may be the real reason the order is stuck
- **A free-of-charge replacement** already shipped, so we do not ship a second one

---

## Phase 7 — Establish precedent before you propose anything

Ask: has this exact problem happened before on this account?

Search the item number and the symptom across the last year, and look at sibling projects
from the same customer — the carpentry project and the plumbing project from the same
division are built by the same people from the same sourcing table and fail the same way.

Precedent changes everything about the resolution:

- If the customer has already accepted this correction once, you are asking them to repeat
  a decision, not make a new one. That is a far easier conversation and it belongs at the
  front of the request.
- The earlier fix tells you the mechanism that worked — who authorized it, what form it
  took, how it was worded.
- Two occurrences of the same error means the upstream source is still broken and will
  produce a third. That is a finding in its own right.

Quote the customer's own earlier words back where they exist. A procurement officer's
prior description of the problem is more persuasive than ours.

---

## Phase 8 — Find every affected order

Before proposing anything, determine the full blast radius.

Take the internal master line number for the item and find every PO in the project family
that carries it. The per-PO processing sheets and the consolidated order list make this
quick. For each one, record: PO number, institution, PO line number, quantity, what the PO
says, what it should say, and the difference.

Total it. One line at one prison is a rounding error; the same line across a whole award
is a real number, and it changes who needs to approve the fix.

---

## Phase 9 — Classify the error

The fix follows from the type. Name it explicitly.

| Type | What it looks like | Where it broke |
|---|---|---|
| **UOM mismatch** | Pack priced as each, or ordered as each and shipped as pack | Our bid worksheet |
| **Broken cross-reference** | Vendor SKU is a different brand, size, or pack than the mfg PN | Our sourcing table |
| **Size / spec transcription** | Right product, wrong size or variant | Our bid or order entry |
| **Order-entry divergence** | BC line disagrees with the PO line | Order entry |
| **Fulfillment** | Shortage, overage, lost in transit, duplicate shipment | Vendor or carrier |
| **Availability** | Item genuinely discontinued or unavailable after award | Vendor, mid-order |
| **Authority** | An approval we are relying on came from someone without the power to give it | Our process |

Be honest about which of these is ours. On a government order, owning a clerical error
plainly is what makes it fixable; arguing about it is what turns it into a dispute.

Be equally honest when it is **not** ours. Habitual ownership of every problem is its own
failure mode — it absorbs costs that belong to a vendor or a carrier, and it trains the
account to treat our quote as negotiable after award. Check specifically whether:

- The customer's PO deviates from what we quoted. They transcribe our worksheet by hand
  and they make mistakes too. If their PO says something our quote never said, that is a
  PO error, and the amendment is a correction to their document.
- The receiving side mis-counted or mis-identified what arrived. Packing slip against
  their claim settles it.
- A vendor shipped against a correct order incorrectly. That is a vendor claim with money
  attached, not a concession we make.

Say who owns it in one sentence, with the evidence. "Ours" and "theirs" both lead to clean
resolutions; ambiguity leads to us paying by default.

---

## Phase 10 — Establish who can actually authorize the fix

Berenice's most common dead end: asking a helpful person for something they have no power
to grant, getting a confused reply, and losing a week.

On a California state PO, three distinct roles matter, and they are rarely the same person:

- **Warehouse / receiving** — confirms what arrived, can accept or refuse goods, can tell
  you a substitute is acceptable to the end user. **Cannot change price, quantity, or
  issue an amendment.** An approval from this person does not protect us on money.
- **The buyer / agency contact** — named in the PO header. Raises the amendment, routes it
  for signature. This is who a price or quantity correction goes to.
- **The procurement official** — signs the PO and the amendment. We generally do not
  contact them directly; the buyer routes it.

There may also be a **program analyst** at the department level (for CDCR DRP, the
Procurement Unit) who directs the buyer. If precedent from Phase 7 shows an analyst drove
an earlier fix, that is the pattern to follow.

If someone has already given an approval, check it against this list. An acceptance from
receiving is genuinely useful for the goods question and worth nothing for the money
question — say so plainly rather than relying on it.

---

## Phase 11 — Prescribe the resolution

Produce a written recommendation. Not a description of the problem — a decision someone
can act on.

Structure it like this:

```
PROBLEM
  One sentence. Which record is wrong and how.

ROOT CAUSE
  Where it broke, from the error classification. Name the file or step.

BLAST RADIUS
  Every affected PO, line, quantity, and dollar difference. Totalled.

PRECEDENT
  Whether this has happened before, how it was resolved, by whom.

RESOLUTION OPTIONS
  Ranked, each with its dollar consequence and what it costs the customer.

RECOMMENDED
  One option, with the reason.

WHO AUTHORIZES
  Named person, role, and why them rather than the obvious contact.

HOLD
  What must not happen until this is resolved.

UPSTREAM FIX
  What to change so it does not recur.
```

Resolution options generally come from this set — match them to the error type:

| Situation | Options worth putting up |
|---|---|
| Price or UOM wrong on the PO | Amended PO at correct price · cancel the line and re-quote · substitute to a cheaper equivalent at the PO price |
| Wrong item or size delivered | RMA and reorder correct · vendor exchange · customer keeps at no charge and we reorder |
| Shortage or lost shipment | FOC replacement from vendor · credit the line · reorder and invoice on receipt |
| Extras or duplicate shipped | Customer returns at our cost · customer keeps FOC with written confirmation · credit |
| Item unavailable mid-order | Substitute with buyer's written approval · cancel the line · backorder with a committed date |

Two rules that keep these from going wrong:

**Always carry a fallback.** A request that offers only one outcome invites a refusal. A
price correction paired with "or cancel the line and we will absorb it" reframes the
amendment as the cooperative option.

**Always state the hold.** Name exactly what is frozen — usually the affected line, at
every affected institution — and confirm the rest of the order is still moving. An
unscoped problem tends to freeze an entire award in the customer's mind.

Then stop. Purchasing diagnoses, quantifies, and recommends; the salesperson who owns the
account decides what goes to the customer and sends it. Hand over the recommendation and
the named authorizer, and flag anything that needs a decision above purchasing — absorbing
a loss, offering goods free of charge, or anything that changes what the customer pays.

---

## Phase 12 — Harvest what the investigation is worth beyond this order

By the time you reach here you have done the expensive part: you have reconstructed what
was supposed to happen and what did. Four things fall out of that work almost free, and
they are where the time spent actually pays back. Skipping them is what keeps this job
purely reactive.

### The upstream hole

A reconciliation that fixes only the order guarantees the same work again next quarter.
If the error came from a sourcing table, a cross-reference, or a template still in use,
name the file as a separate finding. Check whether the same bad data feeds sibling
projects — one functional-equivalent table often serves several trades on the same award.

### Money owed back to us

Reconciliations surface amounts flowing the wrong direction, and nobody is watching for
them because everyone is focused on making the customer whole. Ask explicitly:

- Was a **vendor credit** promised for a return, a wrong shipment, or a lost package —
  and did it ever land? Credits get verbally agreed in a case and then quietly never
  issued.
- Did a vendor ship a **free-of-charge replacement** while we also paid for a reorder?
- Did we **absorb freight or a return fee** for an error that was the vendor's?
- Is there stock sitting at an institution that we paid for and nobody will use — is it
  returnable, or is it inventory we should reclaim rather than write off?

Name the amount and who owes it. This is recovered margin, and it is invisible unless
someone reconstructs the order history — which you just did.

### Vendor performance signal

Every one of these problems has a cause attributable to somebody. Recorded once it is an
anecdote; recorded consistently it is leverage in a vendor conversation, which is the
strategic work this reactive work is stealing time from.

For each reconciliation, note in one line: **the vendor, the failure mode, the order, the
date, and the cost to us.** Failure modes worth distinguishing — wrong item shipped,
wrong quantity, lost in transit, late against a committed date, catalog data wrong,
discontinued without notice, credit not issued.

Catalog-data failures deserve particular attention. A vendor whose cross-references are
unreliable costs us on every bid, not just on the order where it got caught, and that is
a concrete thing to raise with an account manager.

### A record that stops the third occurrence

Write what was found and how it was resolved into the project folder, next to the order
sheets — not only in email. Include the PO and line, the root cause, the resolution, who
authorized it, and the date.

The test for whether this record is good enough: someone who was not involved should be
able to answer the same question in ten minutes next time instead of three hours. The
reason this reconciliation was expensive is that the last one was never written down.

If the same error has now happened twice, say so in one sentence at the top of the
recommendation. Two occurrences is no longer an incident; it is a process defect, and it
should be escalated as one rather than quietly fixed a second time.

---

## Knowing what is not yours to decide

Purchasing diagnoses, quantifies, recommends, and executes the mechanics. Some decisions
sit above that, and taking them on is how a reconciliation turns into a liability:

- **Absorbing a loss** of any real size
- **Giving goods away** free of charge to settle a complaint
- **Changing what the customer pays**, in either direction
- **Anything a customer will read as a commitment** about future pricing or delivery
- **Telling a customer to discard or keep** material they received in error, before we have
  their written confirmation

Bring these to the account owner with the numbers already worked out and a recommendation
attached. That is faster for them than being handed a raw problem, and it keeps the
decision with the person accountable for the relationship.

---

## Writing for the person you are helping

This skill is used mostly by purchasing staff who work in English all day but read and
reason faster in Spanish. Getting the language right is not a courtesy — a reconciliation
finding that is misread is worse than no finding, because someone acts on it.

**Match the language the user writes to you in.** If they write in Spanish, write the
findings, the recommendation, and the explanations in Spanish. If they write in English,
answer in English. Do not ask which they prefer; follow what they are already doing.

When writing in Spanish, keep these in their original form, never translated:

- Part numbers, SKUs, PO numbers, SO and invoice numbers, contract and LPA numbers
- Unit-of-measure codes — `EA`, `PAC`, `PK`, `PR`
- Field and column names from Business Central, the order sheets, and the PO
- Product descriptions exactly as they appear on the customer's PO
- **Anything quoted from an email or a document** — quote it verbatim in its original
  language and put the explanation in Spanish around it

A finding reads well when the identifiers stay stable and the reasoning is in the
language the reader thinks in:

> La línea 84 del PO 4500755180 tiene UOM `PAC` (paquete de 12 pares) pero el precio
> unitario de $2.89 es el precio de **un par**, no del paquete. El precio correcto es
> $78.17 por `PAC`.

Two more things that matter more than vocabulary:

**Short sentences, one idea each.** Long conditional sentences are where
second-language reading breaks down, and reconciliation findings are full of conditions.
Split them.

**Lead with the conclusion, then the evidence.** Say which record is wrong in the first
sentence. Someone who has to read three paragraphs to find out what you concluded will
guess, and the guess is usually the symptom rather than the cause.

Anything that will be forwarded to a customer or a vendor gets written in the language
that recipient uses — usually English. Say plainly which parts of your output are internal
and which are meant to be sent onward.

---

## Reference files

- `references/where-things-live.md` — folder and file topology, order sheet tabs, PO
  header anatomy, naming traps
- `references/tool-recipes.md` — concrete Business Central, Grainger, Outlook and OCR
  lookups with the gotchas that waste time
