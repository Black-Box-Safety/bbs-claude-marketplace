# Vendor email templates — bbs-sourcing

Five shells, placeholders only. Step 7 of `SKILL.md` picks the tier, Step 8 fills the
shell, Mode 2 and Mode 3 use the last two. Nothing in this file is a fact about a vendor,
a price, or BBS: every `{{placeholder}}` is filled at run time from the RFQ, the rep, or
the one file the table below names, and a placeholder that cannot be filled stays in the
draft as `[MISSING — NEEDS INPUT: <what>]` so the rep sees it before anything goes out.
A person sends every email. These are drafts.

The shell fixes what an email must contain and how it is laid out. How it reads is the
rep's own `<first>-voice` skill's job: fill the shell, then run that skill over the body
(strip the AI patterns, match the profile). With no voice skill on the machine the shell
goes out as written, which is plain and acceptable; the signature rule at the end of this
file still applies.

## Layout

The shells follow the BBS house email format, `email-format.md` in `bbs-voice-template`
(bbs-foundations), which every `<first>-voice` skill carries unchanged. It was read from
Parker's sent vendor requests on 2026-10-30. In brief, so the shells make sense without
opening it:

- Greeting on its own line, then one blank line between every block.
- One short paragraph of opener and context that ends in the ask: "...get a quote from
  you on the following:"
- The items as a numbered list, "Description, qty N", link on the item when there is one.
  More than about five lines with part numbers: a three-column table (Item | Mfr # | Qty).
- Any item-specific question directly under the list, one or two sentences each.
- "Items would ship to:" then the address on line breaks. "If needed, our bill to address
  is:" the same way, Cold and Referral only.
- "Some quick notes:" then two to four numbered requests that apply to every line.
- The deadline as a question with its reason.
- Closer, sign-off, signature. Nothing bold in the body. No em dashes.

Questions to a vendor follow the same discipline as questions to a buyer: only what the
vendor alone can answer (a fit, an included accessory, the replacement for a discontinued
part, a minimum), one sentence each, under the list they refer to. What the rep can settle
from the manufacturer's sheet or the RFQ is settled before the email goes out.

## Placeholders, and where each one comes from

| Placeholder | Filled from | Never |
|---|---|---|
| `{{vendor_contact_first_name}}` | Step 6, the named account manager. Writing to a generic inbox (the vendor's sales@ address): greeting is `Hello,` with no name | Guessed from a surname, a website photo, or a LinkedIn title that may be stale |
| `{{vendor_name}}` | Step 5 | — |
| `{{rep_first_name}}`, `{{sign_off}}` | Step 3. The sign-off is the rep's default external one from their voice profile; `Thank you,` when there is no voice skill | — |
| `{{agency}}` | Step 2, the end-customer agency exactly as the RFQ names it, e.g. `CAL FIRE Butte Unit` | The requestor's name, email or phone. The vendor gets the agency, not the person |
| `{{item_type}}` | Two to four words for what the lines are, for the subject line (`Safety Glasses`, `Trimmer Heads and Line`) | — |
| `{{line_items}}` | Step 2 and Step 4: a numbered list, one line per item, "Description, qty N and unit", SKU or model where the RFQ gives one, the reference link on the item where the rep or the RFQ supplied one. A table past about five lines with part numbers | A price, a not-to-exceed, or a "previous price" from the RFQ (Guardrail 3). Vendors quote blind |
| `{{item_questions}}` | Step 4: one short paragraph per line that needs the vendor's answer, directly under the list. A line Step 4a flagged as possibly discontinued gets: `On item N, can you confirm {{item}} is still current? If not, what would you quote as the replacement?` Nothing when there are none | A guess at the replacement part. A question the manufacturer's sheet already answers |
| `{{ship_to}}` | Step 2, or the rep when the RFQ has none (Guardrail 5). Address on line breaks | The agency's headquarters, assumed |
| `{{vendor_deadline}}` | Step 3: the agency deadline minus 48 hours, as a day and time with its zone, e.g. `2PM Pacific on Monday, November 2` | The agency's own deadline as a date |
| `{{bill_to}}` | `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`, the `address` block (`address.mailing_street`, `address.city`, `address.state`, `address.zip`), on Cold and Referral only. Address on line breaks | Typed from memory |
| `{{colleague}}`, `{{colleague_context}}` | Step 7, Referral tier: the teammate the rep named and the one-line context the rep gave | Found by searching a mailbox or the CRM. Step 7 says ask the rep |
| `{{prior_thread_context}}` | Step 7, Warm tier: one sentence from the rep on what the last exchange was, e.g. `Thank you again for your help on the order this summer.` Optional | Auto-detected from mail. Step 7 says ask the rep |
| `{{line_or_items}}` | Mode 3: the line, or lines, the price-match is about | — |
| `{{current_low_quote}}` | Mode 3 step 1: the low quote the rep typed in, the number and the basis (per unit or per line) | The competing vendor's name |
| `{{relational_reason}}` | Mode 3 step 2: the rep's own reason, or the generic line in the Price-Match shell | Invented |
| `{{signature}}` | The rep's own `<first>-voice` skill assets. See "Signature" below | A block typed from memory, copied from an old email, or carried in this file |

## Subject lines

| Template | Subject |
|---|---|
| Cold, Referral, Warm | `Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}`. The same formula `vendor-quote-email` uses, so a vendor's inbox threads BBS requests the same way whichever skill wrote them |
| Follow-up, Price-Match | A reply in the original thread. The subject stays |

## Lines that are not optional

- **The transparency line**, verbatim, on Cold and Referral (Step 8): *I'm getting quotes
  from a few different vendors to get best pricing.* On Warm it stays unless the rep says
  the relationship makes it unnecessary.
- **The escalation line**, verbatim, whenever the address is a generic inbox (Step 6):
  *If you're not the right contact for government distributor quotes, could you please
  connect me with your account manager?*
- **The agency, named** on Cold and Referral (Guardrail 4). Warm may drop it for a vendor
  that already knows the account.
- **Ship-to on every email** (Guardrail 5), and the freight ask with it. A vendor cannot
  quote freight without the address.
- **The vendor deadline on every outreach email**, as a question with its reason.

## What never goes in a vendor email

- Any price the customer supplied: a not-to-exceed, a budget, a previous award (Guardrail 3).
- The agency requestor's name or contact details.
- The agency's deadline as a date. The vendor gets `{{vendor_deadline}}` and the reason
  "our bid is due shortly after that".
- A quantity, unit of measure or spec the RFQ does not state. Vague lines go back to the
  rep (Step 2), not to the vendor as a guess.
- Another vendor's name, in a price-match or anywhere else.
- A question the rep could have answered from the manufacturer's sheet or the RFQ.
- A BBS fact typed from memory. The bill-to comes from `vendor_profile.json`; the
  signature comes from the rep's voice assets.

---

## Cold

Use when nobody at BBS has prior contact with the vendor (Step 7).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

I hope you're doing well! My name is {{rep_first_name}} and I work with Black Box Safety,
Inc., a distributor to the State of California. We're putting together a quote for
{{agency}} and were hoping to get a quote from you on the following:

{{line_items}}

{{item_questions}}

Items would ship to:
{{ship_to}}

If needed, our bill to address is:
{{bill_to}}

Some quick notes:

1. Please include freight to the ship-to address in the quote. The customer needs
   delivered pricing.
2. Can you please list lead time and any minimums for each item?

I'm getting quotes from a few different vendors to get best pricing. Are you able to get
this back to me by {{vendor_deadline}}? Our bid is due shortly after that.

{{escalation_line}}

Please let me know if you have any questions. Thank you!

{{sign_off}}
{{signature}}
```

`{{escalation_line}}` is the verbatim escalation sentence above when the address is a
generic inbox, and nothing otherwise. `{{item_questions}}` is nothing when no line needs
the vendor's answer; the blank line around it goes with it.

## Referral

Use when the rep has no history with the vendor but a BBS teammate does; the rep named
the colleague and gave the context (Step 7).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

I hope you're doing well! {{colleague}} on our team worked with you on
{{colleague_context}} and suggested I reach out. I'm {{rep_first_name}} with Black Box
Safety, Inc. We're putting together a quote for {{agency}} and were hoping to get a quote
from you on the following:

{{line_items}}

{{item_questions}}

Items would ship to:
{{ship_to}}

If needed, our bill to address is:
{{bill_to}}

Some quick notes:

1. Please include freight to the ship-to address in the quote. The customer needs
   delivered pricing.
2. Can you please list lead time and any minimums for each item?

I'm getting quotes from a few different vendors to get best pricing. Are you able to get
this back to me by {{vendor_deadline}}? Our bid is due shortly after that.

{{escalation_line}}

Please let me know if you have any questions. Thank you!

{{sign_off}}
{{signature}}
```

## Warm

Use when the rep running the skill has their own prior thread with this vendor (Step 7,
confirmed by the rep, never auto-detected).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

I hope you're doing well! {{prior_thread_context}}

{{agency}} has a new request and we were hoping to get pricing from you on the following:

{{line_items}}

{{item_questions}}

Items would ship to:
{{ship_to}}

Some quick notes:

1. Please include freight to the ship-to address in the quote. The customer needs
   delivered pricing.
2. Can you please list lead time and any minimums for each item?

Are you able to get this back to me by {{vendor_deadline}}? Our bid is due shortly after
that.

Please let me know if you have any questions. Thank you!

{{sign_off}}
{{signature}}
```

No bill-to on Warm: the vendor has BBS on file. The transparency line is left out of the
shell; the rep adds it as the sentence before the deadline question when they want it.

## Follow-up (Mode 2)

A reply in the original thread, 24 hours or more after the outreach, to a vendor that has
not answered. Tone is "just making sure you got this", never "why haven't you responded".
Three lines; the original email is quoted below it, so nothing is repeated.

```
Hi {{vendor_contact_first_name}},

I wanted to follow up and see if this had been quoted? I would need it by
{{vendor_deadline}} to include {{vendor_name}} in our quote for {{agency}}.

{{sign_off}}
{{signature}}
```

## Price-Match (Mode 3)

A reply in the original thread, only when Mode 3's trigger conditions hold (the delta,
the vendor is one BBS wants to keep, time remains). Thank them, state the current low
price plainly, give the reason, and leave the door open. No pressure and no deadline
beyond the vendor deadline already set.

```
Hi {{vendor_contact_first_name}},

Thank you for the quote! I want to be upfront with you: the current low price I have on
{{line_or_items}} is {{current_low_quote}}. {{relational_reason}}

If you are able to get under the current low price in any meaningful way, I would be glad
to take an updated quote before I finalize on {{vendor_deadline}}. Either way, I appreciate
you taking the time on this one.

{{sign_off}}
{{signature}}
```

Generic `{{relational_reason}}`, when the rep says to use it: *I would rather keep
{{vendor_name}} on this one if the numbers allow it.* The rep's own reason (a past
project, a helpful rep, wanting an active account) replaces it word for word as the rep
gave it.

---

## Signature

The signature is the rep's, not the company's, and it is never typed here. It is read
from the rep's own `<first>-voice` skill, which `/bbs-my-voice` (bbs-foundations,
`bbs-voice-template` step 3b) builds in their own `~/.claude/skills/<first>-voice/` from
their real sent mail. Which asset to paste depends on what the run produces:

| The run produces | Paste as `{{signature}}` |
|---|---|
| An Outlook draft through the Microsoft 365 connector (`outlook_create_draft`, `outlook_create_reply_draft`) | `assets/signature-outlook-draft.html`, verbatim, as the last block of the body. The connector strips images and styling, so this is the text form; say so in the chat reply and never drop the block to avoid saying it |
| Plain text: the `message_compose_v1` card, a chat draft, `bodyType: text` | `assets/signature.txt`, verbatim |

Any other channel: the voice skill's own "Sign it" table decides, not this file.

**No `<first>-voice` skill for this rep, or no signature files in its `assets/`:** write
`[MISSING — NEEDS INPUT: signature]` where the signature goes, in every email of the
run, and add one line to the sourcing brief's Flags: *signature missing, run
`/bbs-my-voice` once and re-render*. Do not substitute Parker's block, a block from an
old email, or one from memory. A signature carries certification and contract numbers,
and a wrong one on vendor mail is the same class of defect as a wrong one on a bid.

**Check the asset before pasting it.** The California certification line must read
`CA DVBE 2009473`. An asset that reads `SB/DVBE`, or claims SB on the California line in
any form, was built before Parker's ruling of 2026-09-22 (bbs-foundations
`canonical-facts.md`, "Small-business status is channel-dependent": OSDS 2009473 carries
DVBE only, and BBS is not a California small business). Stop, flag it in the brief, and
have the rep re-run `/bbs-my-voice`. Do not edit the asset in place and do not paste it.
That is the whole check this file makes: what else the block carries is the voice
template's job and `vendor_profile.json`'s fact, not this file's.

---

Owner: Parker Marshall. Written 2026-10-30 to replace a file the skill named but never
shipped; shells laid out to his sent vendor requests of the same date; the signature rule
follows `bbs-voice-template` step 3b (2026-10-30).
