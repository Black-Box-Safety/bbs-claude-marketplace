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

**(c) Not logged, and the rep asked for a price, a quote or a packet.** → **This is an open
business ruling. Do not decide it here.** Whether a fresh *"the agency emailed asking us to
quote these"* is filed first or priced first is awaiting Parker; it is tracked in the
marketplace repo, not in this file, and it is deliberately untuned. Ask the rep, in one
line, which order they want — file it first and then price, or price now and file after.
Record their answer in the run record. Continue to Gate 1 either way: the only thing their
answer changes is whether `ca-rfq-intake` runs before this point or after Gate 7.

> When the ruling lands, case (c) collapses into (a) or (b): replace this paragraph with the
> ruled default and change nothing else in this file. Until then the answers reps actually
> give accumulate in the run records, which is evidence to rule with. **Do not tune this
> gate to make a test pass.**

## Gate 1 — Recognize the customer and the packet

Read what is already on disk; do not re-derive it. `ca-rfq-intake` wrote the run record and
says which fields decide the rest of the run. `naspo-quote` says what else the buyer folder
holds and in what order to read it. `ca-form-filler` owns identifying which forms the agency
actually sent.

**Gates.**

- A decisive field still carrying a `[FLAG: …]` is resolved with the rep **now**, not at
  Gate 6. A vehicle you cannot name and a buying account you cannot name each change the
  price, not just the paperwork.
- **Open escalations stop the run.** Two questions inside `ca-form-filler` are awaiting
  Parker's ruling. This command does not resolve them, restate them, or route around them.
  If the run reaches one, stop here and tell the rep it is awaiting Parker. A packet is not
  delivered on a guessed answer to an open ruling.

## Gate 2 — Extract the line items

Run `rfq-item-extract` when the items arrived as a cart PDF, a screenshot, or a DWR RFQ.
**Skip it** when the rep already handed over a clean list.

**Gate.** The line count you carry forward and the line count the solicitation asks for
agree, or the difference is named out loud. A line silently dropped here is a
non-responsive bid later.

## Gate 3 — Eligibility, when the vehicle requires it

Run `dgs-bpo-item-check` when Gate 1 named the DGS BPO. **Skip it** on any other vehicle.

**Gate.** An off-list item stops that line and goes to the rep. Substituting a different
part is a rep decision, never this command's.

## Gate 4 — Price

Route on what Gate 1 recorded, not on what the request looked like:

| Gate 1 recorded | Skill |
|---|---|
| Grainger-sourceable lines | `grainger-pricing` |
| Competitive, or lines Grainger does not carry | `bbs-sourcing` (it dispatches `supplier-scout` for items BBS has never sourced) |
| One vendor, one ask | `vendor-quote-email` |

**Gates.**

- Every unit price traces to a tool result on the buying institution's own account. A line
  you cannot trace that way is `[FLAG: why]`, not a number — including a price the customer
  put on their own paperwork, which is their number and not a source.
- The sell-rule and per-account rules are `grainger-pricing`'s to state and `naspo-quote`'s
  to apply. Read them there before a number moves to Gate 5; do not carry a remembered
  version of them into this run.

## Gate 5 — Build the customer's quote

Run `bbs-quote-builder`.

**Gate.** The rep confirms the quote number before it reaches a document. Nothing is
assigned silently.

## Gate 6 — Fill and sign the packet

Run `ca-form-filler`. On a NASPO-routed response, `naspo-quote` runs this half itself and
calls `ca-form-filler` for the paperwork — let it, rather than driving both.

**Gates, all hard, because everything past this point is binding.**

- The certification-expiry check against the due date has run and passed.
- Nothing carrying `[MISSING — NEEDS INPUT]` is resolved by inference. It goes to the rep.
- A line whose correct signer you cannot determine is flagged, never signed. Which signer
  owns which line, and whose signature may be applied at all, is `ca-form-rules.md`'s to
  say — read it there rather than recalling it.
- The open escalations from Gate 1 apply here too. Reaching one stops the run.

## Gate 7 — Verify by looking

**Gate.** Every page that was touched has been rendered and *looked at*. Reading a field
value back out of the PDF is not verification, and a fill script exiting 0 is not
verification. The skills say what to look for; this gate only insists that somebody looked.

## Gate 8 — Deliver to the rep, and stop

Write the files where the skill says, hand the rep the file list, and state in the reply
itself every judgment call made on their behalf. Those are the ones that come back.

**Gate. The run ends with a person.** This command has no send step and never will. The
send-class tools are denied by managed settings. Do not draft-and-send, do not queue, do
not offer to transmit. The rep reviews and the rep sends.

---

## What this command deliberately does not do

- It does not restate any skill's steps. If a reviewer can diff this file against the skills
  it names and find a restated procedure, that is a defect in this file.
- It does not decide the open routing ruling at Gate 0 (c).
- It does not resolve `ca-form-filler`'s open escalations.
- It does not price, sign, or send anything on its own authority.

**Replaces** `/ca-rfq-log` and `/ca-rfq-quote`, which paraphrased the bodies of
`ca-rfq-intake` and `naspo-quote` and had begun to disagree with them.
