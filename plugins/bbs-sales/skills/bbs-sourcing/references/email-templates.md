# Vendor outreach email templates

Five shells for `bbs-sourcing` Steps 7 and 8 and Modes 2 and 3. Every `{{variable}}` is
filled from the RFQ, the vendor directory or the rep. Nothing in a shell is a fact about a
vendor, a price or a part. Added 2026-10-30; the skill had pointed at this file since it
shipped without it, so drafts were produced with no template and no signature source.

## Rules that apply to every template

- Fill every `{{variable}}` or replace it with `[MISSING — NEEDS INPUT: what]`. Never send a
  brace to a vendor, and never guess a ship-to, a deadline or a part number.
- Customer pricing never enters a vendor email (Guardrail 3). "Not to exceed" and
  "previous price" stay on the BBS side.
- Ship-to address in every email (Guardrail 5). End-customer agency named in Cold and
  Referral (Guardrail 4); Warm may skip it for a vendor who already knows the account.
- Vendor deadline is the agency deadline minus 48 hours (Step 3).
- Cold and Referral carry the transparency line verbatim: *I'm getting quotes from a few
  different vendors to get best pricing.*
- A generic sales@ address gets the escalation sentence verbatim (Step 6): *If you're not
  the right contact for government distributor quotes, could you please connect me with
  your account manager?*
- Run the filled draft through the rep's `<first>-voice` skill before rendering, so it
  reads like the rep and not like a form letter. The shells are plain on purpose.

## Signature

The signature is not in this file. It is the rep's own, from their `<first>-voice` skill
in `~/.claude/skills/<first>-voice/assets/`, built with `/bbs-my-voice`:

| Output | File |
|---|---|
| HTML that can carry images (an .html or .eml file, a mail-merge template) | `signature.html` |
| A draft created through the Microsoft 365 connector | `signature-outlook-draft.html`; the connector rejects images and inline styles |
| Plain text | `signature.txt` |

It carries the SDVOSB UEI, the DVBE number and all three contract vehicles, which is what
Guardrail 6 asks for. No voice skill on the machine means `[MISSING — NEEDS INPUT:
signature]` at the foot of the draft. Never type a company block from memory: hand-typed
blocks are how `SB/DVBE` survived in signatures after the 2026-09-22 ruling that OSDS
2009473 carries DVBE only.

## Variables

| Variable | Comes from |
|---|---|
| `{{contact_first_name}}` | Step 6. A generic sales@ address gets no name: open with "Hi," and add the escalation sentence |
| `{{rep_first_name}}` | Step 3 |
| `{{agency}}` | Step 2, as the agency names itself, e.g. CAL FIRE Butte Unit, CDCR California Men's Colony |
| `{{line_items}}` | Step 2. One line per item: quantity, unit of measure, description, SKU or model, link when there is one. Availability flags from Step 4a stay on the BBS side |
| `{{ship_to}}` | Step 2, or the rep when the RFQ has none |
| `{{vendor_deadline}}` | Step 3, date and time with zone |
| `{{escalation_sentence}}` | Step 6, only when the address is generic |
| `{{colleague_name}}`, `{{colleague_context}}` | Referral tier, from the rep |
| `{{prior_context}}` | Warm tier, one line from the rep's own thread with the vendor, or nothing |
| `{{original_subject}}` | Modes 2 and 3, the subject of the outreach being followed |
| `{{items_quoted}}`, `{{low_quote}}`, `{{relational_reason}}` | Mode 3, from the rep. The low quote is stated as the rep gives it; the skill never rounds or invents it |
| `{{signature}}` | The rep's asset, per the Signature section |

## 1. Cold

Nobody at BBS has prior contact with the vendor.

```text
Subject: Quote request for {{agency}}

Hi {{contact_first_name}},

My name is {{rep_first_name}} with Black Box Safety, a veteran-owned distributor of safety,
tactical and MRO equipment to California state agencies and federal customers. We are
quoting the items below for {{agency}} and would like your pricing and availability.

{{line_items}}

Ship-to: {{ship_to}}

Could you send pricing, lead time and freight by {{vendor_deadline}}? I'm getting quotes
from a few different vendors to get best pricing.

{{escalation_sentence}}

Please let me know if you have any questions.

Best,

{{signature}}
```

## 2. Referral

The rep has no history with the vendor, but a BBS teammate does. The rep names the
colleague and the context; the skill does not infer either.

```text
Subject: Quote request for {{agency}}

Hi {{contact_first_name}},

{{colleague_name}} on our team worked with you on {{colleague_context}} and suggested I
reach out. I am {{rep_first_name}} with Black Box Safety. We are quoting the items below
for {{agency}} and would like your pricing and availability.

{{line_items}}

Ship-to: {{ship_to}}

Could you send pricing, lead time and freight by {{vendor_deadline}}? I'm getting quotes
from a few different vendors to get best pricing.

Please let me know if you have any questions.

Best,

{{signature}}
```

## 3. Warm

The rep has their own email thread with this vendor. Ask the rep; do not auto-detect.
Sample that thread first so the greeting and sign-off match what the rep actually uses
with this person.

```text
Subject: Quote request: {{agency}}

Hi {{contact_first_name}},

I hope you're doing well. {{prior_context}} We have another one for you:

{{line_items}}

Ship-to: {{ship_to}}

Can you get me pricing and lead time by {{vendor_deadline}}?

Thank you,

{{signature}}
```

## 4. Follow-up (Mode 2)

Short. The tone is "making sure this reached you," never "why haven't you responded."
Sent as a reply on the original outreach so the vendor has the items in the thread.

```text
Subject: Re: {{original_subject}}

Hi {{contact_first_name}},

Just making sure this reached you. We are still looking for pricing on the items below by
{{vendor_deadline}}. If someone else on your side should get this, could you point me to
them?

{{line_items}}

Thank you,

{{signature}}
```

## 5. Price-match (Mode 3)

Only when Mode 3's thresholds are met (delta of at least 15% or $500 on the line, a vendor
BBS wants to keep, at least 24 hours left). Thank them, state the current low quote
plainly, give the rep's relational reason, offer the requote with the exact wording below,
and add no deadline beyond the vendor deadline already set.

```text
Subject: Re: {{original_subject}}

Hi {{contact_first_name}},

Thank you for the quote on {{items_quoted}}. The current low quote I have is {{low_quote}}.
{{relational_reason}}, so I wanted to give you the opportunity to requote if you are able to
get under the current low price in any meaningful way. The deadline is still
{{vendor_deadline}}.

Please let me know either way.

Best,

{{signature}}
```

---

Owner: Parker Marshall. Added 2026-10-30 to close the gap the skill's own banner recorded.
