---
description: Build your own personal voice skill — sample your real Sent Items, fill the BBS voice profile, and write a <first>-voice skill into your own ~/.claude/skills/ so Claude drafts email that sounds like you. Runs the bbs-voice-template skill.
argument-hint: "[first-name]"
---

# /bbs-my-voice

Run the `bbs-voice-template` skill for the person in front of you. The steps below are the
shape of the run; the skill carries the rules.

1. **Confirm who.** First name (becomes the skill name, `<first>-voice`) and that the
   Outlook mailbox connected in this session is theirs. If it is someone else's mailbox,
   stop — a profile built from another person's mail is worse than none.

2. **Sample.** Pull 15–25 of their sent emails across three recipient types (a buyer they
   know, a formal or first-contact buyer, a vendor or Grainger rep). Quote, never
   paraphrase. Under ten emails: stop and say the sample is too thin.

3. **Fill the profile** from `references/voice-profile-template.md`, section by section,
   with quoted phrases only. Show it to them. The "things they never do" list is the part
   that makes it work; ask them to confirm each item — they know their own tells.

4. **Write the skill** to `~/.claude/skills/<first>-voice/` from
   `references/skill-template.md`, with the filled profile and a copy of
   `references/ai-patterns.md`. Never write it into a repo: it carries their phone number
   and signature block.

5. **Render their signature** (skill step 3b). Read the signature out of one of their
   sent emails, fill `references/signature-template.html`, take the stacked logo from the
   marketing folder on SharePoint, and write `assets/signature.html`,
   `assets/signature-outlook-draft.html` and `assets/signature.txt`. Prove the draft form
   by creating an Outlook draft with it, reading it back, and deleting it. Without this
   step every draft Claude creates for them goes out unsigned.

6. **Test.** Take one AI-drafted email and one of their real ones. Run the new skill on the
   draft and put the result next to the real one. If they would not believe they typed
   it, fix the profile and run again.

7. **Finish.** Tell them the path, that it fires automatically on drafts they will send
   under their own name, and that they can re-run `/bbs-my-voice` when their writing
   changes.

`parker-voice` is the worked example, in `references/example-parker-voice.md`. Match its
shape; do not copy its content.
