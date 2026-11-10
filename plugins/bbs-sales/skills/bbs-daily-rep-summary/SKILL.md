---
name: bbs-daily-rep-summary
description: >-
  Daily summary of one California state book rep's working day for Parker, from the rep's
  own end-of-day check-in plus the systems of record, so Parker can see the work, spot where
  to help, and hold the rep to their own commitments, without surveillance. Two modes:
  check-in (the rep, end of day: draft their own five-minute report, including off-computer
  work such as calls, visits, sizings and portals) and summary (Parker,
  next morning, usually a scheduled Routine: reads the check-in from Teams, pipeline from the
  Sales CRM, bookings from Business Central, quote-folder activity from SharePoint; writes one
  file to Parker's folder, sends nothing). Use when Parker says "daily summary for <rep>",
  "what did <rep> do yesterday" or "set up the daily rep routine", or a rep says "draft my
  check-in" or "what do I tell Parker". Do NOT use for a week or longer
  (bbs-weekly-sales-report), to read any mailbox but the signed-in person's, or to rate a rep
  from timestamps.
requires: [sales-crm, microsoft-365]
degrades-without: [business-central]
---

# BBS daily rep summary

A sales day is mostly invisible to the systems. The CRM sees a record created, Business
Central sees a quote sent, SharePoint sees a folder touched. It does not see the forty-minute
call with a CDCR buyer, the drive to a sizing at a CAL FIRE unit, the vendor rep who finally
called back, or the afternoon lost to a portal. A manager who reads only the systems sees a
thin, wrong picture, and a rep who is judged on that picture learns to work the systems
instead of the territory.

This skill exists to put the rep's own account of the day next to the systems' account, every
day, in one short file, so the person managing them can do the three things that actually
turn a quarter around: understand the work, remove what is in the way, and hold the rep to
commitments the rep set.

**The rep is the primary source. The systems corroborate and fill in. Never the reverse.**

## Two modes, one file

| Mode | Who runs it | When | Produces |
|---|---|---|---|
| **Check-in** | The rep, on their own machine, signed in as themselves | End of the working day, five minutes | A draft of their check-in message, which they edit and post themselves in the agreed Teams chat |
| **Summary** | Parker, signed in as himself, usually a scheduled Routine | Next working morning | One markdown file for the previous working day, with a short reply to the rep that Parker sends himself |

A rep can skip the draft and just type the check-in in Teams from a phone, in a parking lot,
after the last visit. The template is in
`references/routine-prompt.md`, and so is
the Routine prompt, the kickoff conversation, and the setup checklist. The rep-specific
values (name, chat, folder) live in the saved Routine and in the kickoff conversation, never
in this skill: this file is the method for any rep, any day.

## Where a day's work actually happens

Read this table before pulling anything. Most of the right-hand column is reachable only
through the rep's check-in, which is why the check-in is not optional.

| Where the work happens | What a system can see | Where it is visible | Readable by the summary? |
|---|---|---|---|
| Phone calls with buyers, vendors, Grainger account managers | Nothing | Rep's memory, paper notes | **Check-in only** |
| Site visits, sizings, samples dropped, in-person meetings | A calendar event, if one was made | Rep's calendar | Check-in; Parker's calendar if he was invited |
| Trade shows, agency vendor fairs, training, conferences | A calendar event, if one was made | Rep's calendar | Check-in |
| Driving, waiting, a day in the warehouse, a half day, PTO | Nothing | Rep | Check-in |
| An RFQ logged, a quote submitted, a due date set | The record | Sales CRM `bbs_rfqs` (owner = rep) | Yes, `crm_list_records` |
| A quote built, an order booked, an item card entered | The document | Business Central | Yes, `bc_query_entity`, with the attribution caveats below |
| A packet filled, a quote-log row, attachments saved | Files modified | SharePoint `Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/…` | Yes, `sharepoint_search` by modified date |
| Email with agencies and vendors | The thread | Rep's mailbox | **No.** Parker's mailbox only (`outlook_email_search`), for threads he is on |
| Teams with Parker or in team channels | The messages | Chats and channels Parker is in | Yes, `chat_message_search`; never a chat Parker is not in |
| Agency portals: Cal eProcure, Provision Connect, Grainger carts | Nothing, except a Provision Connect quote the rep logged in the CRM (`bbs_quotemethod`) | Rep | Check-in; the CRM for logged Provision Connect quotes |
| Solicitations found on Cal eProcure, not yet logged | Nothing until `/ca-rfq` intake | Rep | Check-in; the reply asks once whether to log them |
| Thinking, planning, reading a solicitation, chasing a vendor who has not replied | Nothing | Rep | Check-in |

Treat an empty systems column as **"not visible from here"**, never as "nothing happened".

## MCP connectors the summary mode needs

| Connector | Used for | If it is absent |
|---|---|---|
| Sales CRM (`crm_list_records`, `crm_get_record`, `crm_list_attributes`) | The rep's `bbs_rfqs`: received, submitted, overdue, due soon, and stale-submitted | Mark the pipeline section "data pending" and say so in Data gaps; the rest of the summary still runs. Do not substitute Business Central quote counts: the weekly report's first trap applies here too |
| Microsoft 365, reads (`chat_message_search`, `teams_list_chats`, `sharepoint_search`, `outlook_calendar_search`, `outlook_email_search`) | The check-in from the agreed Teams chat; folder activity; the previous day's file; Parker's own calendar and mail for shared touchpoints | Without Teams: in an interactive run, ask Parker to paste the check-in; in a scheduled run, which cannot ask, record "check-in not readable" in Data gaps. Without SharePoint search, mark folder activity "data pending" |
| Microsoft 365, the one write (`sharepoint_upload_file`) | Saving the day's file to Parker's summary folder, and nowhere else | If the upload fails, return the whole file in the session output, with a first line saying the upload failed and why |
| Business Central (`bc_query_entity`, `bc_get_sales_document`) | Quotes sent and orders booked on the day | Mark bookings "data pending". The summary still runs |

The summary reads the systems and writes one file, with `sharepoint_upload_file`, to the
SharePoint folder Parker named for these summaries. That folder is the only write target: never
anywhere under `Black Box Safety - MASTER/Customers/`, never an overwrite of a file it did not
write, never any other tool that writes. It sends no mail and no Teams message, and writes
nothing to the CRM or Business Central.

## Summary mode, step by step

1. **Fix the day.** The summary covers the previous working day. On a Monday that is Friday,
   plus anything dated over the weekend. Say the date in the heading.
2. **Read the check-in first.** Search the agreed Teams chat for the rep's message for that
   day. Carry it into the file in the rep's own words, lightly tidied, under their name. If
   there is none, the file says "No check-in posted for <date>" once, in the data-gaps section,
   and nowhere else. A late check-in goes into the next day's file, labelled with its date.
3. **Pipeline, from the CRM**, filtered on `_ownerid_value` for the rep and on the day:
   received (`bbs_receiveddate`), submitted (`bbs_submitteddate`), modified, **overdue**
   (`bbs_duedate` passed, no `bbs_submitteddate`), **due in the next two working days**, and
   **submitted more than ten working days ago with no confirmed outcome**, as canon defines it
   (`bbs-foundations` `references/canonical-facts.md`, "What counts as a win"). Show the five
   largest by value; this is a follow-up prompt, not a shortfall. Each row names the agency, the
   item or title, the value and the date. The field meanings and the status codes are the ones
   `bbs-weekly-sales-report` documents; do not re-derive them.
4. **Bookings, from Business Central**, on `documentDate` for the day, in the rep's scope.
   Attribute per rep exactly the way `bbs-weekly-sales-report` does, by CRM owner or the
   agency mapping, never by Business Central salesperson code alone. The account split and
   agency mapping come from the account-synced `ca-state-sales-grounding`; if it is not
   installed, say so in Data gaps and attribute by CRM owner only. Apply the
   book's scope from canon ("CA state book scope" in `bbs-foundations`
   `references/canonical-facts.md`). Where a figure cannot be split, it is a team figure and
   the file says so.
5. **Folder activity, from SharePoint**: files modified on the day under the rep's agency
   folders. List the folder and the file, not the contents. A packet rendered at 4 pm that
   never reached the CRM is work; this is where it shows. Agency folders are shared: keep only
   files whose last modifier is the rep where the result carries it, otherwise label the
   section "author not shown". Files kept by an agent or regenerated by a script, the DGS
   `BPO/` folder among them, are never the rep's folder activity.
6. **DGS BPO signals, only if DGS is in the rep's book** (attributed as in step 4; otherwise
   leave the section out, do not write "none"). Read `bpo-tracker.json` in the DGS `BPO/`
   folder described in `${CLAUDE_PLUGIN_ROOT}/agents/brenda.md`, "The tracker you keep".
   Status meanings are in that folder's `README.md`: read the status, never recompute pace,
   never run the folder's scripts. Show BPOs logged on the day; any BPO at `at_risk` or
   `overspent`; any `next_follow_up_date` on or before the next working day; any file dated
   the day in `exceptions/`. Each row gives BPO number, facility department, status,
   remaining balance and order-by date as the tracker states them, with the tracker's as-of
   date. Remaining excludes orders not yet invoiced; say so once. No item prices, no contacts.
   A balance the tracker holds as null is "data pending". Remaining is account state, not a
   rep figure. If the folder cannot be read, note it in Data gaps and use no other source.
7. **Shared touchpoints, from Parker's own Microsoft 365**: meetings on Parker's calendar
   the rep was in, and threads in Parker's mailbox or in Teams channels where the rep wrote
   or was copied. His accounts only. Never imply coverage of the rep's mailbox.
8. **Commitments.** Take yesterday's "tomorrow's top three" from the previous day's check-in
   (or the previous file) and set them beside today's check-in: done, moved, dropped, in the
   rep's words where they gave them, otherwise "not mentioned". This is the whole
   accountability mechanism. It works because the rep wrote the list. If the rep works from a
   `ca-territory-handoff` call list (`.sales-team/sal/` under State of CA Agencies, if
   present), list the actions it dates for the next two working days. That list looks
   forward and is not graded: the plan's dates are not the rep's commitments.
9. **Account work, this day only.** From the check-in, plus CRM `bbs_rfqs` naming a contact
   not on any earlier record for that account: named buyers reached, attempts, new names,
   departed buyers. Contact versus attempt is as `ca-territory-handoff`
   `references/scoreboard.md` defines it. No rates and no running totals; response rate and
   weekly indicators belong to the weekly report.
10. **Where Parker can help.** Up to three items, concrete, each traceable to a line above:
   an ask the rep made, a quote waiting on a price or an approval, an overdue RFQ with no
   vendor reply, a buyer who should hear from Parker too, a visit in tomorrow's top three
   (offer `ca-site-visit-brief`), an account where only the rep has ever spoken to the buyer
   and Parker can be the second BBS name (`ca-territory-handoff`, "Multi-thread: the two-name
   rule"), or a BPO at `at_risk` or `overspent` where a call from Parker to the DGS buyer would
   move it before the order-by date. Label them as the summary's inference, separate from the
   rep's own asks.
11. **Save the file** and the reply block to Parker's summary folder, as above. Stop. Parker
   reads, then sends the reply himself.

## The check-in, from the rep's side

Check-in mode drafts the message for the rep to edit and post. Signed in as the rep, it may
read the rep's own CRM records, own calendar and own quote folders for the day, to pre-fill the
on-screen half. It returns the draft in this conversation and stops. It never posts to Teams. The rep adds the off-screen half,
cuts anything they do not want to share, and posts it. **The rep posts; the skill never
does.** The draft never contains anything the rep did not do or say.

Pre-fill yesterday's three from the rep's previous check-in, so the rep only marks each one.
If DGS is in the rep's book, the draft may list under prompt 3 each BPO follow-up the tracker
shows as due, as a question the rep answers: sent / not yet / n/a. A follow-up sent from the
rep's own mailbox shows up nowhere else.

The five prompts, in the order a tired person can answer them at 5 pm:

1. What I worked on today (quotes, RFQs, calls, visits, vendors, admin, training, anything).
2. Off-screen: who I reached (name, role, agency or site), what came of it, the next date.
   Anyone new at an account, or anyone gone.
3. What is stuck, and what it is waiting on (a vendor, a price, an approval, an agency, a portal).
4. What I need from Parker, specifically (a call, a decision, an intro, a price approval).
5. Tomorrow's top three.

Plus two lines: yesterday's top three, each marked done / moved / dropped; and, optionally,
anything else for the record (a win, a worry, a half day, PTO, context for a slow day).

Every prompt is optional. "Nothing to add" is a complete answer. The rep may write one line
or twenty. The point is that the rep owns the account of their day; the summary quotes it, it
does not grade it.

## Summary structure

```markdown
# Daily summary — <Rep first name> — <Day, D Month YYYY>
Calendar: <FY>, <first or second half>; next statewide date and days to it, from
`ca-budget-timing` "The fixed statewide calendar". Do not restate dates here.

## In <Rep>'s words
[The check-in, tidied, under their name. Verbatim where it matters. "No check-in posted" goes
in Data gaps, not here.]

## Pipeline (Sales CRM, as of <timestamp>)
| Agency | Request | Value | Received | Due | Submitted | Status |
Overdue: [...]   Due next 2 working days: [...]   Submitted >10 working days, no confirmed outcome (top 5 by value): [...]

## Bookings (Business Central, as of <timestamp>)
[Quotes sent and orders booked on the day, in scope. "Team figure, cannot be split" where true.]

## Folder activity (SharePoint)
[Folder → file, modified on the day, by the rep. "Author not shown" where the result lacks it.]

## DGS BPOs (tracker, as of <date>) — only if DGS is in the rep's book
| BPO | Facility dept | Status | Remaining (excl. uninvoiced) | Order-by | Follow-up due |
Logged today: [...]   Exceptions filed today: [...]

## Touchpoints with Parker (his calendar, mail and Teams only)
[...]

## Commitments
| Yesterday's top three | Outcome (rep's words) |
Tomorrow's top three: [from today's check-in]
Call-list actions dated for the next two working days: [if a ca-territory-handoff list exists]

## Account work (this day only)
[Named buyers reached, attempts, new names, departed buyers. Contact vs attempt per
ca-territory-handoff references/scoreboard.md. No rates, no running totals.]

## Where Parker can help (summary's inference, max 3)
- [...]

## Data gaps
[Each source that could not be read and why. "No check-in posted for <date>" lives here.]

## Reply to <Rep> (Parker sends)
[Three to five sentences. Acknowledge the off-screen work by name. Answer each ask or say when
you will. One question at most. No grades.]
```

## House rules

- **Transparency before the first run.** The rep hears, from Parker, exactly which sources are
  read and which are not, sees a sample file, and knows they receive the same summary Parker
  does. The kickoff outline is in the references file. A summary the rep has not been told about
  is surveillance, whatever it is called.
- **The rep's words are the rep's.** Record them as "<Rep> reports …". Never set a self-report
  against a timestamp in the file. If something does not line up, that is a conversation, not a
  line in a document.
- **Timestamps are not hours.** Never report a first or last activity time, a gap between
  records, or anything that reads as when the rep started or stopped. The CRM's
  `modifiedon` is when a record changed, not when a person worked.
- **A quiet systems day is not a bad day.** A sizing day produces no CRM rows. Say "not visible
  from here" and look to the check-in.
- **Counts are signals, not verdicts.** Where a day looks thin, say why before saying who: a
  fiscal-year boundary, a vendor who has not replied, an agency on furlough, a territory in
  transition. The same rule the weekly report runs under.
- **Every figure has a source and an as-of.** An unreachable source is "data pending", never an
  estimate. No price, value or date from memory.
- **One write, no sends.** The summary saves one file to Parker's folder. Parker sends the reply. A scheduled run
  cannot answer an Allow prompt, so it must never try to send; if it finds itself about to, it
  stops and says so in Data gaps.
- **Not a performance record.** The files are a working log for a manager and a rep. Nothing in
  them is an HR document, and the skill writes nothing that would read as one: no ratings, no
  comparisons to the other rep, no totals across days. Weekly and longer views are the weekly
  report's job and carry its own caveats.
- **The rep can correct the file.** A reply from the rep that corrects anything is carried into
  the next day's file under "Corrections to <date>", in their words.

## Setting it up

Setup is three things Parker confirms before the Routine is turned on, the kickoff
conversation with the rep, and the Routine prompt itself, all in
`references/routine-prompt.md`. The
Routine fires on weekday mornings in Pacific time, saves the file to the SharePoint folder
Parker named (a folder of his own, never under the customer tree), and stops.
