# Jobs map — start from the work in front of you

Everyone gets the whole toolkit. Nothing below is locked to a title. If two rows fit, pick
the closer job and say so.

| The job | First step | Usually lives in | Needs a live connector? |
|---|---|---|---|
| Cold outreach / follow-up email | Ask Claude to draft it; once, run `/bbs-my-voice` so it sounds like you | `bbs-foundations` (voice) | Outlook helps sampling for voice |
| California state RFQ just arrived | Tell Claude what arrived, or `/ca-rfq-log` then `/ca-rfq-quote` | `bbs-sales` | BC, Grainger, M365, SCPRS as assigned |
| Price Grainger / NASPO lines | Ask to price the list (Grainger MCP — never memory or the open web) | `bbs-sales` | **Grainger MCP** |
| Fill CA / CDCR compliance packet | Ask after pricing — `ca-form-filler` / packet path | `bbs-sales` | usually local PDF tools from bootstrap |
| Marketing one-pager, deck, brand page | Ask; design polish via `impeccable`; docs via document-skills | commons + `bbs-website` / foundations deck voice | varies |
| Order / invoice / "what do they owe us?" | Ask about the PO, order, or vendor balance | `bbs-back-office` | **Business Central** |
| Problem order / reconciliation | Ask what the order needs; foundations also has related doctrine | `bbs-back-office` | **Business Central** |
| Supplier scouting / product research | Ask Claude to open your real Chrome and look; prices still from a real source | commons `superpowers-chrome` | Chrome/Node from bootstrap |
| Channel-partner / federal deck copy | Ask for deck copy in BBS voice (`bbs-deck-voice`) | `bbs-foundations` | document skills for assembly |
| Read or build a PDF / Word / Excel / PPT | Hand the file over or ask to build it | commons `document-skills` | LibreOffice caveat for some PDF paths |
| "Is my machine set up?" | `/bbs-checkup` | `bbs-foundations` | checkup probes the connectors it can |
| "What even is a skill?" | `/bbs-explain-claude` | **this plugin** | none |
| "I want a new shared tool" | See `how-to-extend.md` — tell Parker or propose; do not copy shared skills into `~/.claude/skills/` | Parker / PR | none |

## If they are unsure

Ask one question: **"What are you trying to finish in the next half hour?"** Match the
table. Give **one** first step. Offer a second step only after they finish the first.

## What this map must not do

- Invent a price, cert number, form ID, or signer.
- Say a plugin is "only for sales" or "only for ops" as a hard wall — recommend the fit,
  invite them to use what the job needs.
- Replace the playbooks in `bbs-sales` / `bbs-website` / `bbs-back-office`. Route there.
