---
name: bbs-voice-template
description: Build a personal "voice" skill so Claude drafts email, quotes, and follow-ups that sound like a specific Black Box Safety teammate instead of a chatbot. Use when someone says "make my own voice skill", "build a <name>-voice like parker-voice", "why does this draft sound like AI", or asks to strip AI tells from an email; use it once per person, and again when their writing has changed. It samples the person's real Sent Items, strips the 35 known AI-writing patterns, renders their real Outlook signature (logo from the marketing folder, plus the form the Microsoft 365 draft tool accepts), and writes a profile the same shape as the parker-voice exemplar into their own ~/.claude/skills/<first>-voice/ — never into a shared repo, because a voice profile carries a person's phone numbers and signature block. Do NOT use it to write the email itself; that is the resulting <first>-voice skill's job.
requires: [microsoft-365]
---

# BBS voice template

Every rep at Black Box Safety writes differently, and every one of them can tell when a
draft was not written by them. `parker-voice` solved that for one person: strip the AI
patterns first, then match a profile built from his actual sent mail. This skill turns
that into a template so each teammate gets their own, built the same way, and Parker's
stays the worked example rather than the company default.

The order of the two steps is the whole method. Removing AI patterns first leaves plain
factual text; the profile then makes it sound like a person. Backwards produces
AI-flavored text wearing someone's greeting.

## 1. Sample the real thing

Ask for the person's first name and their mailbox. Then pull their own sent mail:

```
outlook_email_search  folderName="Sent Items"  limit=25
outlook_email_search  folderName="Sent Items"  query="<a customer they write to often>"
```

Read fifteen to twenty-five real emails across three kinds of recipient: a buyer they
know well, a first-contact or formal federal buyer, and a vendor or Grainger rep. Note
what they actually type, verbatim — greetings, openers, how they ask, how they apologize,
how they close, how they sign. Write nothing from memory or assumption. If a person has
under ten sent emails, stop and say the sample is too thin; a profile built on three
emails is a caricature.

## 2. Fill the profile

Copy `references/voice-profile-template.md` and fill each section only with quoted
phrases from the sample. `references/example-parker-voice.md` shows a finished one: the
register paragraph, the greetings table by situation, real openers and closers, the
"things they never do" list, and a before/after pair. Match the shape; do not copy the
content. Two BBS-wide rules go in every profile regardless of the person:

- **Certification discipline.** SDVOSB for federal and primes (Bechtel, USACE), where
  BBS is also a small business under SBA size standards; OSDS **DVBE** 2009473 for
  California state, where BBS is **not** a small business. The signature block carries
  both certifications; body copy follows the channel. Never write "SB" or "SB/DVBE" in a
  California context — see `canonical-facts.md`, "Small-business status is channel-dependent".
- **Never invent facts.** Dates, part numbers, prices, names, lead times come from source
  material or the person. A gap gets a bracketed placeholder and a flag.

## 3. Write the skill

Create `~/.claude/skills/<first>-voice/` with:

```
<first>-voice/
├── SKILL.md                      copy references/skill-template.md, fill the name
├── references/
│   ├── voice-profile.md          the filled profile from step 2
│   └── ai-patterns.md            copy references/ai-patterns.md unchanged
└── assets/
    ├── signature.html            step 3b: their real signature, logo embedded
    ├── signature-outlook-draft.html   step 3b: the form a connector draft can carry
    ├── signature.txt             step 3b: plain text
    └── bbs-logo-stacked.png      the mark from the marketing folder
```

The `SKILL.md` frontmatter description names the person so Claude picks the right voice
when several teammates share a machine. The body is the two-step method with the person's
biggest tells called out — for Parker it is "no em dashes, ever" and "no bold in an email
body"; for someone else it might be "always a subject-line question" or "never a greeting
on internal mail."

## 3b. Render their real signature

An Outlook draft Claude creates through the Microsoft 365 connector does not receive the
person's Outlook signature, so unless the skill appends one the mail goes out unsigned.
The signature is a fact about the person, not a design job: read it, do not compose it.

1. **Read it from their sent mail.** Open one recent external email from Sent Items with
   `read_resource` and copy the signature section of the HTML body. That is the layout,
   wording, fonts and colors Outlook actually sends. The person's own export (an `.rtfd`
   or `.htm` from their signature settings) is a second source; where the two differ, the
   sent mail wins. Never type the block from memory.
2. **Fill `references/signature-template.html`** with what you read. The template is the
   company layout as Outlook renders it; only the name, title, mobile and LinkedIn change
   per person. Keep both certifications and all three contract lines.
3. **Take the logo from the marketing folder**, never from a web search or an old export.
   Signature exports routinely lose the image (Parker's arrived as a 48×48 placeholder and
   his live sent mail has an empty logo cell). The stacked color mark lives in SharePoint
   at `Black Box Safety - MASTER/MARKETING/BBS Logo/Black Box Safety Logo/BBS Brand Logos+®
   PNGs USE THESE/Logos Color/Stacked/Logo Color Stacked 2.png` and matches the mark on
   every quote PDF. Embed it as a data URI or save it beside the HTML.
4. **Write the three renderings** into `assets/`: the full HTML, the connector-safe HTML
   (the Microsoft 365 connector's outbound allowlist, probed 2026-10-30, admits only `p`,
   `br`, `a[href]`, `b`, `i`, lists, headings, tables, `div`, `code`, `pre`, `hr`; no
   `style`, `class`, `id` or `<img>`), and plain text. Prove the connector-safe one by
   creating a draft with it, reading it back, and deleting the draft.
5. **Point the generated `SKILL.md` at them.** `references/skill-template.md` carries the
   channel table; fill the person's sign-off words and leave the file names alone.

## 4. Test it before handing it over

Take one AI-drafted email and one of the person's real emails. Run the new skill on the
draft. Put the result beside the real one. If the person would not believe they typed
the result, the profile is wrong — usually because the sample was too small or the
"never does" list is missing the tell that gives it away. Fix the profile, not the draft.

## Where it lives, and why

The template ships in `bbs-foundations`. The skills it produces live in each person's
`~/.claude/skills/` and are never committed: a voice profile holds a mobile number, a
signature block, and the way a specific person apologizes to a specific buyer. That is
theirs. `parker-voice` on Parker's machine is his instance; the copy in
`references/example-parker-voice.md` is documentation, current as of 2026-09-01.

---

*Owner: Parker Marshall. Part of `bbs-foundations`. The 35-pattern catalog is adapted
from [blader/humanizer](https://github.com/blader/humanizer) (MIT).*
