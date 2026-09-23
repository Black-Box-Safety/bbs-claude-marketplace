---
name: bbs-deck-voice
description: Generate customer-facing PowerPoint slide copy in Parker Marshall's voice for Black Box Safety (BBS) federal pursuits (SDVOSB / GSA Schedule / set-asides). Use this skill whenever Parker needs slide headlines, sub-bullets, speaker notes, or full-deck copy for a federal customer or teaming presentation, or says "write the deck copy," "put this on slides," "slide headlines for the [agency] deck," "capability briefing," "make this slide-ready," or hands over raw content and asks for presentation-ready wording. This is the authorized voice standard for BBS federal decks. Always use it so certification discipline (SDVOSB, never DVBE in federal context), federal-traction honesty, and Parker's no-filler, no-em-dash style stay uniform. Do NOT use for CA state agency decks (that context uses DVBE), for email drafts (Parker's email voice lives elsewhere), or for building the .pptx file itself (use the pptx skill for assembly; this skill produces the words).
requires: []
---

# BBS Federal Deck Voice

Produce slide copy for BBS federal (SDVOSB / GSA) customer presentations that sounds like Parker: direct, credentialed, buyer-centric, no filler. This skill governs the **words on the slide**, not the file build. When a `.pptx` needs assembling, this skill supplies the copy and the `pptx` skill lays it out.

## The core translation

Parker's email voice is a one-to-one prose discipline. A slide is read by a room while Parker talks over it. The voice carries, but the format changes. Translate every input against these rules before writing a single line.

**The headline asserts a point. It never labels a topic.**
A slide title is the one thing the audience should walk away believing. "Contract Vehicles" is a filing label. "You can buy from us today, no bid required" is a point. If a headline could be a folder name, rewrite it as a claim.

**Lead with what the agency gains, not what BBS sells.**
Every slide answers the buyer's silent question: what's in this for my mission, my timeline, my paperwork? BBS features (certifications, contracts, catalog depth) are proof, not the headline. Feature goes in the support line; benefit goes up top.

**One idea per slide.**
If a slide makes two arguments, it makes neither. Split it or cut one.

**Numbers do the persuading. Adjectives don't.**
"Became the largest small business seller to the State of California" beats "trusted, proven partner." Concrete figures, contract numbers, and SLAs carry weight. Marketing adjectives (world-class, premier, cutting-edge, best-in-class) get cut on sight. Parker is credentialed, not boastful.

**No em dashes. Anywhere.** Use periods, commas, or a colon. This is a hard rule from Parker's style.

**No filler, no hedging, no restating what the buyer already knows.** Cut "we are pleased to," "in today's environment," "as you know." A federal buyer does not need to be told what body armor is.

**Sub-bullets are fragments, not sentences.** Slide bullets are scannable. Trim articles and verbs where the meaning survives. Three to five words each where possible. Never more than four bullets on a content slide.

## Federal guardrails (non-negotiable)

Federal context is not state context. Getting this wrong is a credibility hit in front of a contracting officer. Read `references/federal-positioning.md` before writing certification, contract-vehicle, or track-record copy. The essentials:

- **Certification is SDVOSB, never DVBE.** DVBE is California-only. In a federal deck, DVBE does not appear. If the input mentions DVBE, silently convert the framing to SDVOSB (VA-verified).
- **The GSA Schedule is #47QSWA23D000Y.** Cite it exactly when referencing the vehicle.
- **Do not overstate federal traction.** BBS's federal volume is currently low and growing. Never imply a large federal install base. Position around SDVOSB set-aside eligibility, the GSA vehicle, and an early-mover opportunity for the agency. Honesty here is a strategic asset, not a weakness: the pitch is access and a veteran-owned alternative, not incumbency.
- **CA track record is the proof, framed as capability transfer.** The $30M CA business and the largest-small-business-seller-to-California standing are legitimate proof points. Frame them as evidence BBS can execute at scale, then point that capability at the federal buyer. Do not present CA contracts as if they serve federal customers.
- **Sourcewell #091924-BBS is national** and available to any public agency for body armor. Fair to cite in SLED-adjacent federal contexts.

## Slide-type playbook

Different slide types carry different jobs. Match the pattern.

**Title slide.** Agency name and the specific opportunity, not a generic company tagline. Sub-line names the vehicle that makes the purchase frictionless.

**"Why us" / positioning slide.** One headline claim, three proof bullets. For federal: veteran-owned mission, SDVOSB + GSA access, proven execution at scale (CA track record). Never a laundry list.

**Contract vehicle slide.** Headline states the buyer benefit ("Compliant procurement without a full open competition"). Bullets name the vehicle, the certification, and the no-bid or set-aside path.

**Capability / catalog slide.** Lead with the category the agency actually buys, not the full catalog. Depth is a bullet, not the headline.

**Body armor slide (if applicable).** Point Blank / Paraclete distributor standing, Sourcewell access, 24-hour response SLA, in-person sizing, armor recycling program, FOB destination pricing. These are concrete differentiators. Use them.

**Proof / track record slide.** Numbers only. INC 5000 ranking, $30M revenue, became the largest CA small-business seller, NaVOBA award. No adjectives around them.

**Close / CTA slide.** One specific next step. Not "let's partner." Something like "Send your next SDVOSB set-aside requirement and get a quote in 24 hours." A single CTA, matching Parker's email discipline.

## Speaker notes

When asked for speaker notes, write what Parker would *say*, not a re-read of the slide. Notes carry the context, the story, and the transition to the next slide. They can be fuller sentences than the slide, but they keep the voice: direct, no filler, no em dashes. A good note gives Parker one memorable line and one bridge.

## Output format

Default output, per slide:

```
SLIDE [n]: [internal purpose label]
Headline: [the asserted point]
Bullets:
  - [fragment]
  - [fragment]
  - [fragment]
Speaker note: [what Parker says] (only if requested)
```

Deliver copy inline in chat for fast review and iteration. Do not build a `.pptx` unless asked. If Parker wants the assembled deck, hand this copy to the `pptx` skill.

Before returning, run the self-check in `references/self-check.md` against every slide. It catches the failures that matter: a topic-label headline, a feature-led benefit, a stray em dash, a DVBE reference in federal context, or an overstated federal claim.

## When input is thin

If Parker hands over a topic but no substance ("make me a capability deck for Tinker AFB"), do not invent facts. Pull real BBS proof points from the federal guardrails, ask for the one or two agency-specific details that would sharpen the copy (the target commodity, the specific set-aside if known), and draft against what is verifiable. One clarifying question maximum, matching Parker's low-friction style.
