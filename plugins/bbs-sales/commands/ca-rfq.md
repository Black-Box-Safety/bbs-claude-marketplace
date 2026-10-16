---
description: Run a California state RFQ end to end under one contract — intake gate, recognition, extraction, eligibility, pricing, quote, packet and signature, visual verification, delivery to the rep. Order and gates only; every step runs its own skill.
---

# /ca-rfq

One state RFQ, one running order.

**This file carries order and gates. It carries no procedure.** Every step names the skill
that owns it: invoke that skill and follow its body. Where this file and a skill look like
they disagree about *how* a step is done, the skill is right and this file is stale — say
so rather than reconciling them by hand.

Nothing here restates a price rule, a form ID, a signer, a folder convention, a cert number
or a field map. Those live in the skills, in
`${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md` (what the forms mean, who signs, what
stays blank) and in `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` (every static BBS
value). If you are about to type one of those into this file, you are in the wrong file.

**A gate is a condition that must hold before the run moves on.** A gate that cannot be
satisfied stops the run and reports to the rep. It never guesses its way past. These
documents bind BBS to a price and a certification; a wrong value does not crash, it gets
submitted.

---

## Gate 0 — Intake. Explicit, and skippable.

Say out loud which of three cases this is. Do not assume one.

**(a) Already logged** — a deal folder and its run record exist for this request, because
the rep named it or you found it. → **Skip intake. Enter at Gate 1.** Re-running intake on
a logged request is how a second folder gets created for a buyer who already has one, which
is the expensive intake error `ca-rfq-intake` exists to prevent.

**(b) Not logged, and the rep asked to file, log, intake or "start" it.** → Run
`ca-rfq-intake` and follow it. Then Gate 1.

**(c) Not logged, and the rep asked for a price, a quote or a packet.** → **File it
first.** Run `ca-rfq-intake`, then Gate 1. Ruled by Parker 2026-09-24: a fresh *"the agency
emailed asking us to quote these"* is filed before it is priced, always. Filing first is what
finds the precedent and prevents the duplicate buyer folder; pricing first and filing later
is how a quote goes out with no record behind it. Say in one line that you are filing it
first, and do not ask the rep which order they want. The ruling is listed in
`bbs-foundations` `references/canonical-facts.md`, "Rulings on binding documents".

## Gate 1 — Recognize the customer and the packet

**Two facts are established here on every branch: the contract vehicle, and the account
that will actually buy.** Gate 3 routes on the first, Gate 4 on both, and the price itself
depends on the second. Nothing downstream re-derives them.

Where they come from depends on Gate 0. If intake has run, read what it wrote and do not
re-derive it: `ca-rfq-intake` wrote the run record and says which fields decide the rest of
the run and how a vehicle is classified. If intake has **not** run — Gate 0 (c),
price-first — the same two facts come out of the same documents by the same rules; classify
them `ca-rfq-intake`'s way, carry them through this run, and let intake write them down when
it runs at Gate 8. A price-first run is not an unrouted run.

`naspo-quote` says what else the buyer folder holds and in what order to read it.
`ca-form-filler` owns identifying which forms the agency actually sent.

**Gates.**

- A decisive field you cannot name — or one the run record carries as `[FLAG: …]` — is
  resolved with the rep **now**, not at Gate 6. A vehicle you cannot name and a buying
  account you cannot name each change the price, not just the paperwork. With no run record
  to read a flag out of, this gate is not satisfied by default: unknown is still unknown,
  and it still stops here.
- **An open ruling stops the run.** Rulings on binding-document facts (a signer, a form
  ID, a certification checkbox, a price rule) are listed in `bbs-foundations`
  `references/canonical-facts.md`, "Rulings on binding documents", in a *Ruled* table and
  an *Open* list. If a skill marks a field **Escalated** and that question is not in the
  *Ruled* table, stop here and tell the rep it is awaiting Parker. This command does not resolve,
  restate, or route around an open ruling. A packet is not delivered on a guessed answer.

## Gate 2 — Extract the line items

Run `rfq-item-extract` when the items arrived as a file or an image rather than a clean
list. **Which sources it reads is its own to state** — read its description and its opening
table rather than a list copied into this file, which goes stale the day it gains another
source. If what arrived is not one of them, it says so instead of extracting; believe it.

**Skip it** when the rep already handed over a clean list — and on the state path, where a
NASPO or state **Line-Item Cost Worksheet** is not one of the sources `rfq-item-extract`
reads: pulling the items, the quantities and the header data out of that worksheet is
`naspo-quote` §1's job, and Gate 4 gets the list from there. Skipping this gate must not
mean arriving at Gate 4 with no list; it means the list comes from the other owner.

**Gate.** The line count you carry forward and the line count the solicitation asks for
agree, or the difference is named out loud. A line silently dropped here is a
non-responsive bid later.

## Gate 3 — Eligibility, when the vehicle requires it

Run `dgs-bpo-item-check` when Gate 1 named the DGS BPO. **Skip it** on any other vehicle.
Gate 1 names a vehicle on every branch, price-first included; arriving here without one is
Gate 1 unsatisfied, not permission to skip. An off-list part quoted onto a BPO bid is the
failure this gate exists to prevent.

**Gate.** An off-list item stops that line and goes to the rep. Substituting a different
part is a rep decision, never this command's.

## Gate 4 — Price

Route on the vehicle and the account Gate 1 established, not on what the request looked
like.

**On a CA state / NASPO-routed response, `naspo-quote` owns the whole back half — enter it
here, once.** It prices, builds the quote, fills and signs the packet, renders and delivers.
Gates 5 through 8 still bind, but on the state path they are conditions checked against that
one run, not four further invocations. It is not decomposable: handing it the run again at a
later gate re-runs its earlier sections and produces two prices and two quote numbers for
one RFQ.

Otherwise:

| Gate 1 established | Skill |
|---|---|
| Grainger-sourceable lines | `grainger-pricing` |
| Competitive, or lines Grainger does not carry | `bbs-sourcing` (it dispatches `supplier-scout` for items BBS has never sourced) |
| One vendor, one ask | `vendor-quote-email` |

**Gates.**

- **Every unit price has a source you can point at, and it is the route's own source.** On
  `grainger-pricing`, and on `naspo-quote`'s pricing half, that is a tool result on the
  buying institution's own account — the account decides the price, so the wrong one returns
  a wrong number that still looks valid. On `bbs-sourcing` and `vendor-quote-email` there is
  no buying account behind the line at all: the source is the vendor's own written quote,
  attributed and dated. Holding those routes to an account they never had would flag every
  line on a competitive SB/DVBE bid. A line with neither is `[FLAG: why]`, not a number —
  including a price the customer put on their own paperwork, which is their number and not
  a source.
- The sell-rule and per-account rules are `grainger-pricing`'s to state and `naspo-quote`'s
  to apply. Read them there before a number moves to Gate 5; do not carry a remembered
  version of them into this run.

## Gate 5 — Build the customer's quote

**The customer's quote is a Business Central sales quote, created through the BC write path.
It is not a PDF generated in Claude.** Ruled by Parker, in session, 2026-10-16, while running
the CAL FIRE Atwater helmet-cover RFQ; the earlier practice of rendering the customer document
with `bbs-quote-builder` is retired as the quote desk's path. Two halves, in this order:

1. **Items first, and never twice.** Every line's item number is looked up in BC
   (`bc_find_item`) before anything is written. A number that exists is quoted as it is:
   never re-created, never patched from here. A number BC does not have is entered through
   `bc-item-entry` (vendor, sourced cost, named review) before the quote is touched.
2. **Then the quote.** The header and lines are created in BC through the BC-Write-API quote
   builder (`PM Claude/BC-Write-API` on SharePoint, one spec-driven script per deal until the
   quote-entry skill ships), from a spec saved beside the deal as
   `BC-import/quote-<yyyy-mm-dd>.json` with a review sheet next to it. The script dry-runs
   first (reads only); the rep reads the sheet and approves it **by name in the chat**; only
   then does it write. It sets CONTRACT from the vehicle Gate 1 named, gates the header on
   ship-to by read-back before a single line is added, verifies every line by read-back, and
   never releases, converts or sends.

On the state path `naspo-quote` §3 supplies the line values (Grainger at cost, no tax on the
worksheet, the solicitation number as the external document number); the mechanics above are
the same.

**Salesperson follows the account split, quote by quote** (Parker, in session, 2026-10-16): on a
California state quote the BC salesperson is `KQUEZON` for Kim Quezon's agencies (CDCR, CHP, CAL FIRE,
CMD, CDFW, Cal OES, DOJ, DPR, DWR, DCC, CCC, ABC, DOC, State Water Board, OIG, POST, Horse Racing Board,
Gambling Control Commission) and `AANYA` for every other state agency. `CA STATE TEAM` is not used on
new quotes, even where the customer card still defaults to it. Body armor and CSU/UC keep their own owners.

**Gates.** The quote number is the SQ number BC assigned on creation, read back from BC;
nothing is generated or predicted. No item is created as a side effect of quoting. The rep
releases the quote in BC (that is where tax is calculated) and the customer document is the
PDF BC prints from the released quote. `bbs-quote-builder` runs only when the rep asks for a
Claude-rendered copy of a quote that already exists in BC.

## Gate 6 — Fill and sign the packet

**On the state path, `naspo-quote` fills and signs the packet itself, inside the run you
entered at Gate 4 — it does not hand the paperwork to `ca-form-filler`.** Read its body
rather than this line: it routes *away* from `ca-form-filler`, and its own section fills the
forms. Start neither skill here; this gate checks what that run produced.

Otherwise — the rep wants the forms without a state-routed quote, or the agency sent a bound
packet — run `ca-form-filler`.

**Gates, all hard, because everything past this point is binding.**

- The certification-expiry check against the due date has run and passed.
- Nothing carrying `[MISSING — NEEDS INPUT]` is resolved by inference. It goes to the rep.
- A line whose correct signer you cannot determine is flagged, never signed. Which signer
  owns which line, and whose signature may be applied at all, is `ca-form-rules.md`'s to
  say — read it there rather than recalling it.
- Gate 1's rule on open rulings applies here too. Reaching an unruled escalation stops the run.

## Gate 7 — Verify by looking

**The render belongs to whichever skill ran the back half** — `naspo-quote`'s verify section
on the state path, `ca-form-filler`'s on either of its paths. Both have a real render step,
and neither is optional.

**Gate.** Every page that was touched has been rendered and *looked at*. Reading a field
value back out of the PDF is not verification, and a fill script exiting 0 is not
verification. The skills say what to look for; this gate only insists that somebody looked.

## Gate 8 — Deliver to the rep, and stop

**If Gate 0 (c) put the filing after the pricing, run `ca-rfq-intake` now, before the
hand-off.** The request gets its folder, its run record and its deadline, and the answer the
rep gave at Gate 0 is written down where the ruling can later be read out of it. A priced
RFQ that was never filed is the one that misses its next deadline.

Write the files where the skill says, hand the rep the file list, and state in the reply
itself every judgment call made on their behalf. Those are the ones that come back.

**Gate. The run ends with a person.** This command has no send step and never will; any send
is the rep's, outside this command. Do not draft-and-send, do not queue, do
not offer to transmit. The rep reviews and the rep sends.

---

## What this command deliberately does not do

- It does not restate any skill's steps. If a reviewer can diff this file against the skills
  it names and find a restated procedure, that is a defect in this file.
- It does not resolve an open ruling; it checks `canonical-facts.md`, "Rulings on binding
  documents", and stops if the question is not in the *Ruled* table.
- It does not price, sign, or send anything on its own authority.

**Replaces** `/ca-rfq-log` and `/ca-rfq-quote`, now retired: they paraphrased the bodies of
`ca-rfq-intake` and `naspo-quote` and had begun to disagree with them.
