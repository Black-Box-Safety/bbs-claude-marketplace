# The opening words, by band

Read this when writing the call list. A segmentation with no sentences in it is a
spreadsheet, and the whole reason to band a book is that each band needs a different first
sentence. Give the rep the words; they are new to this and will otherwise improvise the
apology.

These are openings, not sequences. Anything longer than the first exchange belongs to the
`sales-*` craft skills (Sloane, where installed).

## Recover — the relationship left with the departed rep

> "One order from us counts toward your DVBE participation goal."

Black Box Safety is a certified DVBE in California, so a line item placed with BBS counts
toward the agency's DVBE goal. BBS is **not** a California small business and does not move
the agency's SB number — never say it does (canonical-facts.md, "Small-business status is
channel-dependent"). Where an agency's own published DVBE attainment sits below its goal,
name the gap: it is current, checkable, and it is a reason for the buyer to take the call
that has nothing to do with who left.

What not to do: do not lead with the departure, do not apologise for it, and do not promise
continuity you cannot describe. The buyer cares about their next order, not our org chart.

## Defend — still buying, needs no rescuing

There is no win-back sentence here. The opening is the reorder: what they bought last, when,
on what vehicle, and when they will need it again. A rep who opens a healthy account with a
handover apology tells that buyer their supplier is unstable.

If the account's own reorder gap says they are due, say that. If it does not, this is a call
about the next thing on their list, not this one.

## Provisioned whitespace — the account exists and has never been used

> "Your facility already has an account with us that has never been used — here is what it
> prices at."

Quote-first, not conversation-first. Pricing is live against that account today, so the
opening can carry actual numbers. Then, where it applies, the mechanism — the SB/DVBE
Option. Read `ca-budget-timing` §1 before saying anything about it: the agency needs Option
purchasing authority, it is still a competitive solicitation (only the advertising goes),
and because BBS is DVBE only in California, BBS can only be one of two or more DVBE quotes.
Do not paraphrase it from memory and do not promise a buyer that BBS alone makes it easy;
say what §1 says, or say you will confirm and come back. Used correctly it converts a
never-used account into a first order, because it removes work rather than adding a vendor.

## Cold start — no account, no history

> "The competition on this is already done — you can order off our statewide contract today."

Name the vehicle this buyer can actually use and say what it removes from their desk. The
vehicle list and numbers live in `bbs-foundations` `references/canonical-facts.md`,
"Contract vehicles" — take the number from there, never from memory. Which one fits depends
on the channel:

| Buyer | Vehicle to name |
|---|---|
| California state agency | The NASPO ValuePoint CA MRO statewide LPA |
| California state agency, body armor | The CA Body Armor LPA |
| UC campus | UC / OMNIA — a UC vehicle, not a state-agency one |
| Local law enforcement | NPPGov — not a state-agency vehicle |
| Body armor, where the buyer orders through Sourcewell | Sourcewell Body Armor — not a state-agency vehicle |

A vehicle a buyer's channel cannot use is not a speed argument, it is a wrong statement in
front of a procurement officer. Body armor and CSU/UC are also outside the Kim/Aanya state
book (canonical-facts.md, "CA state book scope"), so on that book the MRO LPA is almost
always the one. The public buyer's constraint is process, not preference; being the easiest
compliant path is the only lever that moves them.

## The true things, and where they come from

Everything above rests on four facts. Carry the sourcing with them so a rep can defend the
statement when a buyer pushes:

| The claim | Where it comes from |
|---|---|
| In California BBS is DVBE-certified and is not a California small business; federally it is SDVOSB and a small business. Never both channels on one document | canonical-facts.md, "Certifications, by jurisdiction", for the ruling; `${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json` for the cert number and expiry |
| The SB/DVBE Option — authority, mechanics, threshold, and BBS's place in it | `ca-budget-timing` §1, which carries the SCM citation and the figure |
| Encumbrance is a signed PO, not a delivery | Gov. Code §16304, SAM §8325 — see `ca-budget-timing` |
| An agency's DVBE attainment against its goal | The agency's own published attainment; cite the report and its date |

Never state a dollar figure, a deadline or a contact in an opening that has not been checked
this run. Verify before it is spoken, not after.

## Objections, with answers

**"We already have a supplier for this."** Correct, and this is not a replacement pitch.
Ask what they buy and on what vehicle; that answer is the next call.

**"I have to run a solicitation."** Often they do — the SB/DVBE Option is still a
competitive solicitation, only without advertising, and it has conditions BBS alone cannot
meet (`ca-budget-timing` §1). The stronger answer is usually the vehicle they can already
order from, where the competition is done.

**"I don't have budget right now."** Ask when their money has to be encumbered rather than
accepting the close. Invoke `ca-budget-timing` before the call and know both deadlines; a
buyer who thinks 30 June governs everything is often wrong about their own timeline.

**"Send me something."** Fine, but get the definition of done first: the name, the role, the
direct line, and the date of their next expected need. An email into a void is not a contact.

**"Who are you again?"** The honest version. Do not overstate history with a facility that
has none — the record is checkable and a rep who inflates it once is not believed again.

## What to do with each outcome

| Outcome | Next action |
|---|---|
| **Reached the buyer, need identified** | Log the request — `/ca-rfq`, whose Gate 0 runs `ca-rfq-intake`. Date the next touch |
| **Reached the buyer, no need now** | Record their next expected need date, and set the next action to that date |
| **Reached the wrong person** | Take the referral, record both names. Two names is the bar |
| **No answer** | Second channel, dated. Three unanswered attempts in a band means the contact record is wrong, not that the account is cold — go back to the buyer folders and SCPRS for a current name |
