# Vendor email templates — bbs-sourcing

Five shells, placeholders only. Step 7 of `SKILL.md` picks the tier, Step 8 fills the
shell, Mode 2 and Mode 3 use the last two. Nothing in this file is a fact about a vendor,
a price, or BBS: every `{{placeholder}}` is filled at run time from the RFQ, the rep, or
the one file the table below names, and a placeholder that cannot be filled stays in the
draft as `[MISSING — NEEDS INPUT: <what>]` so the rep sees it before anything goes out.
A person sends every email. These are drafts.

The shell fixes what an email must contain. How it reads is the rep's own `<first>-voice`
skill's job: fill the shell, then run that skill over the body (strip the AI patterns,
match the profile). With no voice skill on the machine the shell goes out as written,
which is plain and acceptable; the signature rule at the end of this file still applies.

## Placeholders, and where each one comes from

| Placeholder | Filled from | Never |
|---|---|---|
| `{{vendor_contact_first_name}}` | Step 6, the named account manager. Writing to a generic inbox (the vendor's sales@ address): greeting is `Hello,` with no name | Guessed from a surname, a website photo, or a LinkedIn title that may be stale |
| `{{vendor_name}}` | Step 5 | — |
| `{{rep_first_name}}`, `{{sign_off}}` | Step 3. The sign-off is the rep's default external one from their voice profile; `Thank you,` when there is no voice skill | — |
| `{{agency}}` | Step 2, the end-customer agency exactly as the RFQ names it, e.g. `CAL FIRE Butte Unit` | The requestor's name, email or phone. The vendor gets the agency, not the person |
| `{{item_type}}` | Two to four words for what the lines are, for the subject line (`Safety Glasses`, `Trimmer Heads and Line`) | — |
| `{{line_items}}` | Step 2 and Step 4: a table with line #, SKU / model, description, quantity, unit of measure, and a reference link where the rep or the RFQ supplied one | A price, a not-to-exceed, or a "previous price" from the RFQ (Guardrail 3). Vendors quote blind |
| `{{availability_ask}}` | Step 4a. Present only when a line was flagged as possibly discontinued: `Please confirm {{item}} is current and available, or name the replacement you would quote.` Otherwise omit the line | A guess at the replacement part |
| `{{ship_to}}` | Step 2, or the rep when the RFQ has none (Guardrail 5) | The agency's headquarters, assumed |
| `{{vendor_deadline}}` | Step 3: the agency deadline minus 48 hours, with date, time and time zone | The agency's own deadline |
| `{{bill_to}}` | `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json`, the `address` block (`address.mailing_street`, `address.city`, `address.state`, `address.zip`), on Cold and Referral only | Typed from memory |
| `{{colleague}}`, `{{colleague_context}}` | Step 7, Referral tier: the teammate the rep named and the one-line context the rep gave | Found by searching a mailbox or the CRM. Step 7 says ask the rep |
| `{{prior_thread_context}}` | Step 7, Warm tier: one sentence from the rep on what the last exchange was. Optional | Auto-detected from mail. Step 7 says ask the rep |
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
- **The vendor deadline on every outreach email**, never the agency's.

## What never goes in a vendor email

- Any price the customer supplied: a not-to-exceed, a budget, a previous award (Guardrail 3).
- The agency requestor's name or contact details.
- The agency's deadline. The vendor gets `{{vendor_deadline}}`.
- A quantity, unit of measure or spec the RFQ does not state. Vague lines go back to the
  rep (Step 2), not to the vendor as a guess.
- Another vendor's name, in a price-match or anywhere else.
- A BBS fact typed from memory. The bill-to comes from `vendor_profile.json`; the
  signature comes from the rep's voice assets.

---

## Cold

Use when nobody at BBS has prior contact with the vendor (Step 7).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

My name is {{rep_first_name}} and I work with Black Box Safety, Inc., a distributor to
the State of California. We are quoting {{agency}} on the items below and would like
pricing from {{vendor_name}}.

{{line_items}}

{{availability_ask}}

The items would ship to:
{{ship_to}}

Please include freight to that address and lead time with the quote, and let me know if
you need anything else from me. I'm getting quotes from a few different vendors to get
best pricing, so I would need your numbers by {{vendor_deadline}}.

If you need a bill-to address to set up the quote:
{{bill_to}}

{{escalation_line}}

{{sign_off}}
{{signature}}
```

`{{escalation_line}}` is the verbatim escalation sentence above when the address is a
generic inbox, and nothing otherwise.

## Referral

Use when the rep has no history with the vendor but a BBS teammate does; the rep named
the colleague and gave the context (Step 7).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

{{colleague}} on our team worked with you on {{colleague_context}} and suggested I reach
out. I'm {{rep_first_name}} with Black Box Safety, Inc. We are quoting {{agency}} on the
items below and would like pricing from {{vendor_name}}.

{{line_items}}

{{availability_ask}}

The items would ship to:
{{ship_to}}

Please include freight to that address and lead time with the quote. I'm getting quotes
from a few different vendors to get best pricing, so I would need your numbers by
{{vendor_deadline}}.

If you need a bill-to address on file:
{{bill_to}}

{{escalation_line}}

{{sign_off}}
{{signature}}
```

## Warm

Use when the rep running the skill has their own prior thread with this vendor (Step 7,
confirmed by the rep, never auto-detected).

```
Subject: Pricing Quote Request - {{item_type}} - {{agency}} - {{vendor_name}}

Hi {{vendor_contact_first_name}},

{{prior_thread_context}} I have another one for you: {{agency}} needs the items below and
I would like your pricing.

{{line_items}}

{{availability_ask}}

Ship to:
{{ship_to}}

Freight and lead time with the quote, please. I would need it by {{vendor_deadline}}.

{{sign_off}}
{{signature}}
```

No bill-to on Warm: the vendor has BBS on file. The transparency line stays unless the
rep drops it.

## Follow-up (Mode 2)

A reply in the original thread, 24 hours or more after the outreach, to a vendor that has
not answered. Tone is "just making sure you got this", never "why haven't you responded".
Three sentences; the original email is quoted below it, so the line items are not
repeated.

```
Hi {{vendor_contact_first_name}},

Just making sure this reached you. I'm still looking for pricing on the items in my note
below for {{agency}}, and I would need it by {{vendor_deadline}} to include
{{vendor_name}} in our quote. Let me know if anything on the list needs clarifying.

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

Thank you for the quote. I want to be upfront with you: the current low price I have on
{{line_or_items}} is {{current_low_quote}}. {{relational_reason}} If you are able to get
under the current low price in any meaningful way, I would be glad to take an updated
quote before I finalize on {{vendor_deadline}}. Either way, I appreciate you taking the
time on this one.

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
shipped; the signature rule follows `bbs-voice-template` step 3b (2026-10-30).
