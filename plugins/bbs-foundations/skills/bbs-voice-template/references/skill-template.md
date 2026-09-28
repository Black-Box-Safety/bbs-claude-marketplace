---
name: <first>-voice
description: Write email, quotes, and follow-ups in <First Last>'s voice — <one clause on their role, e.g. "BBS account manager for CDCR and CalVet"> — by first stripping the 35 known AI-writing patterns and then matching the profile built from their real sent mail. Use for any draft <First> will send under their own name; sample their prior emails to the same recipient first. Do NOT use for other teammates or for customer-facing web copy.
---

# <First> Voice

Two jobs, in this order:

1. **Strip the AI tells.** Run the draft against the 35 patterns in
   `references/ai-patterns.md`.
2. **Write it as <First>.** Match `references/voice-profile.md`, and where possible match
   their prior emails to *that specific recipient*.

Order matters. Removing AI patterns first leaves plain, factual text; the profile then
makes it sound like a person.

## Step 1 — Sample the recipient thread first

```
outlook_email_search  folderName="Sent Items"  query="<contact name or domain>"
```

Read two or three. <First> writes differently to a buyer than to a vendor rep than to a
teammate. No prior thread → fall back to the profile's first-contact register.

## Step 2 — Clean the AI patterns

The ones that matter most in <First>'s email, from the profile's "never does" list:

- <tell 1, e.g. "Em dashes (#14). Never.">
- <tell 2, e.g. "Bold in an email body (#15, #16).">
- <tell 3>
- Filler and preambles (#23, #28). Overused AI words (#7). Chatbot leftovers (#20).
  Generic positive endings (#25). Passive voice (#13).

## Step 3 — Write as <First>

Greeting on its own line; opener only when the relationship warrants it; one idea per
paragraph; asks phrased the way the profile shows; problems owned plainly; the closer and
sign-off from the profile; full signature block on external mail.

## Step 4 — Verify

- [ ] Every "never does" item is absent
- [ ] Greeting, opener, sign-off match the profile
- [ ] Every fact traces to source material — nothing invented
- [ ] Would a reader who knows <First> believe they typed this?

## Hard rules

**Never invent facts to make prose flow.** Missing detail → bracketed placeholder, flagged.
**Never soften substance to sound friendlier.** Warm tone, precise content.
**Do not replicate their typos.** Match the rhythm, not the errors.
**Certification discipline:** SDVOSB for federal and primes (BBS is a small business
federally too); OSDS DVBE 2009473 for California state, never "SB" or "SB/DVBE" there;
the signature block carries both certifications.
**Leave untouched:** quoted prior emails, signature blocks, part numbers, specs, prices,
contract language.

## Attribution

Pattern catalog adapted from [blader/humanizer](https://github.com/blader/humanizer) (MIT).
Built with `bbs-voice-template` from `bbs-foundations`, <YYYY-MM-DD>.
