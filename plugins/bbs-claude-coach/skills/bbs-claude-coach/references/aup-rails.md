# The two rails — protection, not control

Signed company policy (read and sign the full one-pager):

the `bbs-foundations` plugin's `docs/AUP.md`

Do **not** restate every AUP paragraph here. Coach with these two rails and point at that
file for the rest.

## 1. Claude drafts; you approve every send

Every quote, price, email, and form is a draft until **you** review it. In Claude Code
Claude can send an email or Teams message only after you click Allow on that send
(managed settings and the admin console, Parker, 2026-10-02). What the Allow prompt shows
depends on the send: for a new email Claude writes, the recipients, subject and body; for
a forward, a Teams message or a reply to a meeting invite, the text but only an id for the
email, chat, channel or meeting. So before asking for Allow on one of those, Claude says in
plain words what the id points to: the forwarded email's sender, subject and date, or the
chat or channel by name and who is in it, or the meeting's title and time. If it cannot
say, it does not ask. Sending a saved Outlook draft, QuickBooks sends and SignNow
invites stay switched off: drafts Claude writes, you send from Outlook. In the ordinary
Claude chat window this rule is not guaranteed, so do sending in Claude Code.

## 2. Never an invented number

No price, stock, lead time, quantity, or certification fact from memory or the open web.
Unknown becomes `[FLAG: why]` (or ask the human) — never a plausible guess. A submitted bid
price is binding.

## Channel reminder (do not invent variants)

- Certification and small-business language follow the channel; the rule and its reasoning
  live in `bbs-foundations` `canonical-facts.md`, "Small-business status is
  channel-dependent" — read it there, never paraphrase it.
- Never mixed on one form, and never a small-business claim without naming the channel. The
  certification numbers, exact strings and vehicles live in `bbs-foundations` canonical
  facts and `bbs-sales` `vendor_profile.json` — point there; never re-key them here.

## Tone when coaching

Say the rails exist **to protect the person and the company**, then invite experiment
above them: new prompts, workflows, voice skill, FLAGS, asking for tools. Control culture
("you are only allowed…") is the wrong frame for this plugin.
