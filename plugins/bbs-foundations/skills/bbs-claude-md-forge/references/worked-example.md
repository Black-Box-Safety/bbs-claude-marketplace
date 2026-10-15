# Worked example — the Bechtel Sentinel customer tree

Built 2026-09-02 for `MASTER/Customers/Bechtel/sentinel/`, a OneDrive tree of about 550
files across 27 RFQs from Bechtel National's Sentinel (LGM-35A) program office. Not git.
Two sites (Utah and Vandenberg), one closed-bid playbook that predated the work.

## What was built

```
sentinel/
├── CLAUDE.md                                   143 lines   root: contract, certs, forms, Grainger rule, systems, gotchas
├── utah-sentinel/CLAUDE.md                      87 lines   Ogden office, two ship-to modes, buyers, folder index
├── vandenberg-sentinel-rfps/CLAUDE.md          100 lines   VLC, DFARS stack, gate passes, buyers, live RFP
└── vandenberg-sentinel-rfps/RFP-747947-…/CLAUDE.md  150 lines   closed bid, kept as a playbook
```

Root imports both site files at column one. Both site files import `@../CLAUDE.md`. The
747947 file is linked from the Vandenberg file as read-on-demand, not imported: 150 lines
of one bid's sourcing detail should not load into every session about the account.

## What the root file carries, and why

- **The contract number that appears on every PO** (`5300017317`) — it is the same string
  as Bechtel's subaward in USAspending, so one line ties a $141B program to a $6,801 PO.
- **SDVOSB, not DVBE.** Bechtel is a federal prime. The first draft of a quote email led
  with DVBE. The rule is in the root file so no site file has to repeat it.
- **Two reps-and-certs tiers by award value**, because the wrong form is the most common
  reason a Bechtel award stalls.
- **The Grainger punch-out rule** verbatim from the older 747947 file, promoted to the root
  because it applies to every RFQ, not one.
- **Business Central customer numbers** (`C11312` Sentinel, `C10475` WTP), and the rule
  that BC's document linkage beats an email thread when they disagree about which PO maps
  to which RFQ — a subagent had guessed wrong from email and BC settled it.
- **Folder naming gotchas**: `rfq-76666-PPE` is a typo for 766666; `vandenburg` was
  misspelled (renamed to vandenberg in Sep 2026); the same RFQ number appears in both
  site folders and was reassigned to a second buyer mid-life. An agent that does not know these will file things twice.

## The two mistakes, and how the checker catches each

**Inline imports.** The first root file read `**Chain:** @utah-sentinel/CLAUDE.md ·
@vandenburg-sentinel-rfps/CLAUDE.md` (the folder's old name). It looked chained. Claude
Code resolves `@` imports only at column one, so nothing loaded; a session in the root never saw either site file.
`claude-md-link-check` reported "0 references checked," which is the tell. Now a FAIL:
"inline `@path` (not at column one)."

**A stale READ-FIRST banner.** The 747947 file opened with "Proposal due June 22, 2026 —
days remaining ~4" in September. Business Central showed no award on the requisition, so
the file was reframed as a closed-bid playbook: dead "Open Items" removed, reusable
sourcing knowledge kept, the tooling section's `/mnt/skills/...` paths (from a hosted
session that authored it) replaced with the skill name. Now a WARN ("days remaining",
past date) and a FAIL (sandbox path).

## Numbers that made the file worth writing

27 solicitations in 14 weeks, roughly two a week; 24-hour quote windows; one RFQ closed
6 hours after invitation; $172,568.78 lifetime Bechtel revenue across both accounts in
BC. A folder that generates that much activity on that clock cannot depend on one person
remembering which form goes with which award value.
