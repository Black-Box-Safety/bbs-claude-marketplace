# CalRecycle 74 — recycled content and SABRC codes

Derived from ~113 CalRecycle 74s in the State of CA Agencies corpus. This is the
one genuinely per-item judgment on the whole packet, it's sworn under penalty of
perjury, and the answer is **not** a constant — it follows the product's material.

## The rule BBS has actually applied

| Product material | SABRC code | Postconsumer % | Seen |
|---|---|---|---|
| Metal — tools, blades, fasteners, hardware, fittings | `11A` | `10%` | 32 rows |
| Plastic — bags, strapping, binders, chair mats, tubing, dispensers | `6` | `20%` | 21 rows |
| Paper / office — folders, filing supplies | `1G` | `30%` | 4 rows |
| Tissue — toilet paper, paper towels | `1A` | `45%` | 2 rows |
| Glass | `15A` | per product | 2 rows |
| Mixed materials, wood, lumber, chemicals, electronics, batteries, plumbing assemblies | `N/A` | `0%` | 90 rows |

Worked examples straight out of past packets:

```
11A | 10% | Straight Flute Taper Tap
11A | 10% | Nails
11A | 10% | Drill Bits, Center Drill
11A | 10% | Saw Blades
 6  | 20% | Trash Bags, Cable Ties
 6  | 20% | Plastic Strap
 6  | 20% | SDS Binder
 1G | 30% | Folders
 1A | 45% | Toilet Paper
N/A |  0% | Lumber
N/A |  0% | Plumbing Supplies (Mixed Materials)
N/A |  0% | Battery
N/A |  0% | Pressure Gauge
N/A |  0% | MSA multi-gas detection instruments
```

## How to choose

Ask what the item is *made of*, not what it's *for*. A metal bolt cutter is 11A/10%;
a multi-gas detector is an electronic assembly, so N/A/0%. When a line bundles
several materials ("Glue, Wood, Batteries, Cleaner"), past packets wrote the line
as mixed and used N/A/0% — that's defensible and consistent.

The form's own footnote 3 backs the N/A cases: wood products, aggregate, concrete,
and electronics such as computers, TVs, software, and telephones are named as
common N/A categories.

Precedent beats theory. Check whether the same institution already accepted an
answer for the same product — look in sibling folders under that buyer before
deciding fresh.

When the material is genuinely unclear and there's no precedent, write
`[REP TO CONFIRM]` in both columns and say so in the cover summary. Two rows in
the corpus do exactly that. Inventing a percentage on a perjury certification to
avoid a follow-up question is the wrong trade.

## Description column

Keep it to the material-level phrase the code has to justify, not the full catalog
description — "Metal Products - R&B Wire Model 669 steel wire hamper frame" reads
naturally against 11A. The field clips around 55 characters at 8pt.

## Meets SABRC checkbox

Left unchecked in every packet in the corpus. Fill the percentage and code columns;
leave the checkbox alone unless a buyer specifically asks for it.
