# Daily rep summary — setup, kickoff, Routine prompt, check-in template

Everything rep-specific is a placeholder here. Fill it in the saved Routine and in the
conversation with the rep, not in this repo. The method is in `../SKILL.md`.

Placeholders: `<Rep>` the rep's first name · `<Chat>` the name of the Teams chat the rep
posts check-ins in · `<Folder>` the SharePoint or OneDrive folder the summary files land in.

---

## 1. Before the first run: three things Parker confirms

A scheduled run acts without a person in the room, so these are confirmed once, in writing,
before the Routine is enabled.

| Confirm | Why |
|---|---|
| **Connectors the Routine may use:** Sales CRM, Microsoft 365 (Teams, SharePoint, Parker's own calendar and mail), Business Central. Nothing else. | The Routine stores its connector grant. Pass only these. |
| **Sends are refused.** The send-class ask and deny rules apply in the scheduled environment, and the prompt never asks to send. | A scheduled run cannot answer an Allow prompt. The reply block is in the file for Parker to send. |
| **Where the file lands:** `<Folder>`, a folder of Parker's own. Never under `Black Box Safety - MASTER/Customers/…`. | The customer tree holds customer documents. A manager's daily log is not one. |

One more, not a system setting: **the rep has been told**, per section 2, before the first
file is written.

## 2. The kickoff conversation with the rep

Fifteen minutes, in person or on a call, before anything runs. An outline, not a script.

1. **Why.** Numbers are off, and the plan is to turn them around together. The first step is
   for Parker to actually see the day, because most of a sales day is invisible in the
   systems and that invisibility cuts against the rep.
2. **What it is.** One short file every morning about the previous day: the rep's own
   check-in on top, then what the CRM, Business Central and the quote folders show, then
   where Parker can help, then a reply from Parker.
3. **What it reads, exactly.** The rep's CRM records. Business Central documents. Files
   modified in the agency quote folders. The agreed Teams chat. The DGS BPO tracker, if DGS is
   in their book. Their territory call list, if one exists, for what it dates ahead. Parker's own calendar and
   mail where the rep was in the meeting or on the thread. Show the table in the skill.
4. **What it does not read.** The rep's mailbox. Chats Parker is not in. Hours, start and
   stop times, location, anything about pace. Say it plainly: there is no delegate access to
   the rep's mailbox and no intention to ask for one.
5. **What the rep controls.** The check-in is theirs: every prompt is optional, one line is
   enough, "nothing to add" is an answer, and anything they put on the record is quoted, not
   graded. They see the same file Parker sees, every day. They can correct any line and the
   correction is carried forward.
6. **What accountability means here.** Tomorrow's top three, set by the rep, checked by the
   rep the next day. Plus the things the pipeline already owes: overdue RFQs and quotes with
   no outcome. Nothing else is scored.
7. **Ask what they want in it.** A section they would find useful, a question they would
   rather not be asked, a time of day that works for the check-in. Change the template
   accordingly before the first run.
8. **Show a sample file** built from a day that already happened, with the rep present.

## 3. The check-in message (the rep posts this, in `<Chat>`, end of day)

Paste-ready. The rep can keep it pinned, or ask Claude to draft it ("draft my check-in") and
then edit before posting. Every line is optional.

```
Check-in <D Mon>

Worked on:
-

Off-screen (who — name, role, site — result, next date; new or departed buyers):
-

Stuck on / waiting for:
-

Need from Parker:
-

Tomorrow's top 3:
1.
2.
3.

Yesterday's top 3 (mark each done / moved / dropped):
1.
2.
3.

Anything else (optional):
```

## 4. The Routine prompt (paste-ready)

Mode: a fresh session on each firing, so the prompt is standalone. Schedule: weekday
mornings, Pacific time, after the rep's check-in has had the night to land. Example
expression: `CRON_TZ=America/Los_Angeles 41 6 * * 1-5`.

```
Run the bbs-daily-rep-summary skill in summary mode for <Rep>.

Scope: the previous working day. On a Monday, cover Friday plus anything dated over the
weekend. Put the date in the heading.

Sources, read-only, in this order:
1. The check-in: the most recent message from <Rep> in the Teams chat "<Chat>" dated the day
   being summarized. Carry it into the file in their own words under their name. If there is
   none, write "No check-in posted for <date>" once, under Data gaps, and nowhere else.
2. Sales CRM bbs_rfqs where the owner is <Rep>: received, submitted and modified on the day;
   overdue; due in the next two working days; submitted more than ten working days ago with
   no confirmed outcome as canon's "What counts as a win" defines it (never bbs_accepted),
   top five by value, framed as follow-ups.
3. Business Central quotes sent and orders booked on the day, attributed the way
   bbs-weekly-sales-report attributes them, in the CA state book scope from canon. Mark a
   figure that cannot be split as a team figure.
4. SharePoint files modified on the day under the agency quote folders <Rep> works.
   Folder and file name only, last modified by <Rep> where the result shows it. Never the
   DGS BPO/ folder, which a script regenerates.
4a. If DGS is in <Rep>'s book: the DGS BPO tracker, read-only, as the skill's step 6
   describes. Do not write to it and do not run its scripts.
4b. If a ca-territory-handoff call list for <Rep> exists, the actions it dates for the next
   two working days. Forward-looking, not graded.
5. My own calendar, mail and Teams channels, for meetings and threads <Rep> was in. My
   accounts only.
6. The previous day's file in <Folder>, for yesterday's top three and any correction <Rep>
   posted to it.

Put one calendar line under the heading from ca-budget-timing's fixed statewide calendar
(fiscal-year half, next statewide date, days to it). Do not restate the dates.

Write one markdown file named YYYY-MM-DD_<Rep>.md to <Folder>, using the skill's summary
structure, ending with a reply block addressed to <Rep> that I will send myself.

Rules, no exceptions: read-only; send nothing; write nothing to the CRM or Business Central;
report no start, stop or gap times; set no self-report against a timestamp; every figure has
a source and an as-of; an unreachable source is "data pending", never an estimate; nothing
in the file compares <Rep> to anyone or totals across days.

If a connector needs authorization, write the file with that section marked "data pending"
and say which connector in Data gaps. Then stop.
```

## 5. Optional: the Friday addendum

If Parker wants a once-a-week view of commitments without a second routine, add to the
prompt: "On Fridays, append a section 'This week's top-three outcomes' listing each day's
tomorrow's-top-three with the rep's own done / moved / dropped, no counts, no percentages."
Patterns show in five rows without a number being attached to a person. Anything heavier is
the weekly report's job.

## 6. Turning it off

Disable the Routine, tell the rep the same day, and leave the files where they are. The
files belong to the two people in the conversation.
