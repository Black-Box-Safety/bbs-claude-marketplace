# Rep setup — one sitting, ~20 minutes

You already use Claude Code in the Desktop app. **Everything you do today keeps working.**
This adds the VS Code quote desk: same Claude, same skills — plus you can SEE the files
Claude is reading, side by side. Screenshots live in the Teams sales channel pinned post.

## Set up (once)

1. **Install VS Code** — code.visualstudio.com, all defaults.
2. **Install the Claude Code extension** — Extensions sidebar (Ctrl+Shift+X), search
   "Claude Code", install, then sign in with your BBS Claude account (same login as the
   Desktop app).
3. **Open the quote desk** — grab `workspace/bbs-rep.code-workspace` from the marketplace
   repo (Parker posts it in Teams). First open: replace `REPLACE-ON-FIRST-OPEN` with your
   OneDrive root per `workspace/README.md`, save, reopen. Accept the 4 recommended
   extensions.
4. **Run `/bbs-checkup`** in a Claude panel. Everything ✅? Done. Anything ❌? It prints the
   exact sentence to send Parker — send it, use the Desktop app meanwhile.
5. **Run `/bbs-my-voice`** once (builds your personal writing voice from your sent mail).

## Daily use

- New RFQ lands (or appears in `_inbox/`): open the workspace, tell Claude what arrived —
  `ca-rfq-intake` files it and starts the record. Then `/ca-rfq-quote` when you're ready
  to price. You review every number. You send.
- Where you'd have asked "what did we quote them last time?" — ask Claude. It reads the
  quote-log and Business Central and cites what it finds.
- One outbound motion a week: a promo page, a winback batch, or a follow-up sweep. Log it.
- Claude got something wrong? One line in `FLAGS.md`. That's a catch, not a confession.
- Session hygiene: one RFQ per Claude session — `/clear` before the next one. Side question?
  `/btw` keeps it out of the session. Corrected Claude twice on the same thing? `/clear` and
  restart with a sharper prompt. Multi-day deal? `/rename <agency>-<item>` so
  `claude --resume` finds it tomorrow.

## When to use which window

- **VS Code**: quote work — you want the RFQ, the worksheet, and Claude on one screen.
- **Desktop app**: everything else, or if VS Code is ever broken. Same Claude.

## Want an agency storefront?

Twelve agencies already have their own BBS gear-assistant page (cdcr.blackboxsafety.com
etc.). If your buyer's agency should have one: drop the agency name + what they buy into
the buyer's folder and ping Parker — that's the whole request process today.

## The ground rules

Read and sign the one-page use policy (bbs-foundations → docs/AUP.md). Short version:
approved tools only for company data, every number human-reviewed, you send everything,
log it when Claude gets it wrong, experiment freely otherwise.

## Level up (optional, free)

Anthropic Academy "Claude 101": anthropic.skilljar.com/claude-101. Ask the deputy champion
the how-do-I questions; ask Parker the it's-broken ones (with your /bbs-checkup line).
