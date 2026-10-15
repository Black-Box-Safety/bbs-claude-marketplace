# Track Routing

Black Box Safety is one brand in two expressions. Every piece runs exactly one track, or is a
declared bridge piece. Mixing tracks inside one piece is a `brand-check` failure.

Read this before choosing a layout, a palette, or a proof point.

## Choosing the track

Ask **who wears or uses the item, and which vehicle pays for it** — not which product category a
catalog files it under.

| The piece is about... | Track |
|---|---|
| MRO, facilities, janitorial, sanitation, office, medical supplies | `mro-procurement` |
| Safety equipment and PPE for general agency staff — hard hats, hi-vis, gloves, eye and fall protection | `mro-procurement` |
| Contract vehicles, punchouts, DVBE spend credit, procurement mechanics | `mro-procurement` |
| Body armor, plate carriers, duty gear, optics, holsters, tactical apparel | `public-safety` |
| Equipment issued to sworn personnel | `public-safety` |
| Officer-direct retail, personal gear | `public-safety` |

### The "Public Safety Equipment" ambiguity, settled

The LE/MRO brochure lists **Public Safety Equipment** as one of five product categories alongside
MRO, office, janitorial, and medical. The Body Tactical brochure treats public safety as a
standalone specialty. Both are correct about different things, and the collision is real enough
that it must be decided once:

> **A product category is not a track.** "Public Safety Equipment" sold to a public agency through
> a Grainger or co-op MRO vehicle is an **`mro-procurement`** piece — the buyer is a procurement
> officer, the argument is spend credit and vehicle access, and the dress is navy/Grainger.
> Armor and duty gear sold to sworn personnel through the DGS body armor LPA, Sourcewell
> `091924-BBS`, or NPPGov is a **`public-safety`** piece — the buyer is an equipment unit, the
> argument is specialist credibility, and the dress is charcoal/tactical.

Test to apply: **if the argument you are making is about how the purchase is transacted, it is
MRO. If it is about whether the equipment is good enough to wear on duty, it is public safety.**

### Track follows the piece, not the program or the account

The same account can receive pieces on both tracks. A city that buys janitorial supplies through
OMNIA and plate carriers through the DGS LPA gets an `mro-procurement` piece for the first and a
`public-safety` piece for the second. Do not average them into one dress.

### When genuinely undecided

Default to `mro-procurement` and say so in the project README. It is the calmer dress and the
lower-risk compliance surface. Do not invent a hybrid.

## Bridge pieces

A bridge piece presents both tracks as parallel columns under one company. Reference example:
`brand/sources/LE and MRO Brochure Digital.pdf`.

Use a bridge piece when **all three** hold:

1. The recipient agency demonstrably buys across both categories
2. The goal is breadth of capability, not depth on one product line
3. There is room for both columns without either being reduced to a logo strip

Otherwise pick one track. A bridge piece that is 80% MRO with a token armor mention is an MRO
piece with a compliance problem.

### Bridge construction rules

- Shared elements come from `core.md` only — wordmark, palette, credentials, company facts
- Each column uses its own track's proof and vehicle numbers, never the other's
- One shared headline in the core voice; the columns carry the track-specific lines
- The bridge layout uses the **MRO dress as the container** — navy and gold. It is the calmer of
  the two and reads as corporate rather than as one track winning
- A bridge piece is audited at both scopes: `--scope mro --scope public-safety`

## Declaring the track

Every project README carries `track:` in its frontmatter, with one of:

```
track: mro-procurement
track: public-safety
track: bridge
```

`brand-check` reads it to select scope. **A missing `track` is a failure, not a default** — an
agent that cannot say which track it is writing in has not made the decision the piece requires.

## What this file does not decide

Program folder (`programs/…`) and track are independent. A bid-response piece lives under the
program that owns the account regardless of which track it is dressed in. See the root
`CLAUDE.md` for program routing.
