# Onboarding — bbs-foundations

You do not need to know what a CLAUDE.md is to use this. In one sitting:

1. Open any BBS repo or customer folder in Claude Code and run `/bbs-claude-md audit`.
   Read the report. Every FAIL names a file and a line.
2. If the folder has no CLAUDE.md, run `/bbs-claude-md init`. Read the draft before you
   say go. If a line in it is wrong, say so — the skill fixes the fact in the reference,
   not just in your file.
3. Run `/skill-bus:onboard` once so the doctrine injects automatically from then on.

The real test: a teammate who is not Parker opens a repo they have never seen, reads the
CLAUDE.md, and does one task without asking anyone. If they had to ask, run
`/bbs-claude-md audit` and put the answer in the file.
