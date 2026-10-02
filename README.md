<p align="center">
  <img src="https://img.shields.io/badge/company-Black%20Box%20Safety%2C%20Inc.-051c2c" alt="Black Box Safety, Inc.">
  <img src="https://img.shields.io/badge/certs-channel%20split%20%C2%B7%20see%20canonical--facts-b19800" alt="Certification language follows the channel; the numbers live in canonical-facts">
  <img src="https://img.shields.io/badge/runs%20in-Claude%20Code%20%C2%B7%20Cursor%20%C2%B7%20VS%20Code%20%C2%B7%20Desktop-6E56CF" alt="Runs in Claude Code CLI, Cursor, VS Code, and Desktop">
  <img src="https://img.shields.io/badge/plugins-6%20BBS%20%2B%205%20pinned-2dd4bf" alt="Six BBS plugins plus five pinned external">
</p>

# Black Box Safety — Claude Marketplace

**How the same small team runs company memory, the California book, marketing pieces, the order after the win, and the storefront, with a coach so a non-technical teammate can start any of them.**

Black Box Safety sells safety, tactical, and MRO equipment to government buyers. Six plugins run the work today: foundations, coach, sales, marketing, back-office, and website. A person reviews every number. A person sends.

The skill lists live in each plugin README. Certification strings live in [`plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`](plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md). This file points at those. It does not retype them. How the files point at each other is [`docs/OPERATING-LAYER.md`](docs/OPERATING-LAYER.md).

## Foundations

**Who.** Everyone.

**What.** The company memory the other plugins inherit: how a `CLAUDE.md` is written, the voice a teammate sounds like in email, and a checkup of the machine.

**How work moves.** A `CLAUDE.md` stays under 150 lines. A fact points at its system of record. `/bbs-claude-md` drafts or audits one and writes nothing until you say go. `/bbs-my-voice` builds a personal voice skill from your own sent mail, on your machine, never in a repo.

**First command.** `/bbs-checkup`

**Will not.** Quote a buyer or fill a form. Detail: [`plugins/bbs-foundations/README.md`](plugins/bbs-foundations/README.md).

## Coach

**Who.** Everyone. Roles overlap, so nothing here is locked to one plugin.

**What.** Understand the toolkit, start the job in front of you, and extend it when you find a gap.

**How work moves.** You name the job. The coach shows what Claude can do for that job, the first concrete step, or a plain-language explanation of skills, commands, plugins, and connectors. The job plugins do the job.

**First command.** `/bbs-what-can-i-do` (also `/bbs-start`, `/bbs-explain-claude`)

**Will not.** Quote or fill a form. Detail: [`plugins/bbs-claude-coach/README.md`](plugins/bbs-claude-coach/README.md).

## Sales

**Who.** The California book: territory, then the request, then the page that goes back out. Body armor and CSU/UC stay out of the Kim/Aanya California book. They stay in the company.

**What.** Territory work in front of the RFQ, then the desk that takes a request through a signed packet, plus Grainger promo pages.

**How work moves.** Segment the book, then `/ca-rfq`: file the request, pull the items out, check the vehicle, price from the system of record, build the quote, fill the packet. A promo page runs the other direction from a Grainger hot list. One request is enough to see the shape: a state facility emails an RFQ, Claude files it in the buyer folder that already exists, prices from Grainger and Business Central, and drafts the packet. The rep reviews every number.

**First command.** `/ca-territory-handoff` for the book in front of you. `/ca-rfq` once a request is in hand.

**Will not.** Send the quote, place the order, or treat an order already taken as a quote. That order goes to back office. Certification language follows the channel; the strings are in canonical-facts. Detail: [`plugins/bbs-sales/README.md`](plugins/bbs-sales/README.md).

## Back office

**Who.** Whoever is asked after the win: purchasing, accounting, a rep with a customer on the phone.

**What.** Read Business Central. Do not write to it. Four questions:

| Ask | Skill | The failure it exists to stop |
|---|---|---|
| Where is this customer PO? | `so-search` | An uninvoiced order is not "not found." |
| What has the vendor actually shipped? | `bbs-po-status` | The PO header `fullyReceived` flag is unreliable. Answer from the receipt lines. |
| What did we earn after the Grainger rebate? | `bbs-rebate-profitability` | BC margin ignores the rebate. Item ledger COGS is Grainger list. |
| What is actually wrong (wrong item, short ship, price on the PO)? | `bbs-order-reconciliation` | The reported symptom is the last link. The fix attaches to the cause. Uses the current Business Central connector (`bc_*`). |

**How work moves.** Name the order. Read the record that answers the question. Hand the draft to a person.

**First command.** There is no slash command. Ask one of the four questions.

**Will not.** Post to Business Central, send the customer an answer, or retarget `bbs-rebate-profitability` off CData. (`so-search` and `bbs-po-status` moved onto the Business Central connector by Parker's ruling of 2026-10-02.) Those gaps are named under Connectors. Detail: [`plugins/bbs-back-office/README.md`](plugins/bbs-back-office/README.md).

## Website

**Who.** The whole team. A catalog write and a deploy still wait for a person.

**What.** Price list to live product page: intake, contract pricing, enrichment, storefront, quote bot, with data QA and cross-sell beside them.

**How work moves.** Three repos, one catalog. Supabase (`bbs-database`) is the catalog. Shopify (`bbs-shopify`) renders it. The quote bot (`bbs-quote-bot`) advises over a snapshot. A database change reaches the storefront only after sync, and the bot only after a regen is committed. `/bbs-add-product` walks intake through the storefront. `/bbs-onboard` is the first sitting.

**First command.** `/bbs-onboard`

**Will not.** Write the catalog or deploy without a person approving it. The quote bot does not place orders or write to Business Central. Detail: [`plugins/bbs-website/README.md`](plugins/bbs-website/README.md).

## Marketing

**Who.** Reps making a piece, or looking up one that already exists.

**What.** A one-page sales piece, a campaign email draft, a logo check against the rights ledger, and a prior brochure or deck. Approved wording is the claims registry. Finished pieces and logo files live on the SharePoint desk `MARKETING/bbs-marketing/`.

**How work moves.** Intake writes the program folder and the brief, then stops. The one-page draft comes next, then one email draft, then whether a logo may be used, then a pointer to what was already printed or presented. One piece carries one channel. A Grainger hot-list page stays `grainger-promo-page` in sales. Federal slide copy stays `bbs-deck-voice` in foundations.

**First command.** `/bbs-one-pager`

**Will not.** Create California buyer folders or run the quote desk. It does not send email, place orders, write to Business Central, or file a quote under `Customers/State of CA Agencies/`. CSU, UC, and body-armor marketing stay in this plugin. They stay out of the Kim/Aanya quote book. A human sends. Detail: [`plugins/bbs-marketing/README.md`](plugins/bbs-marketing/README.md).

## The shared rule

Intake, prepare, review can send the draft back, a person sends. The same rule covers a quote, an order answer, a customer email, and storefront copy.

```mermaid
flowchart LR
  A["Intake"] --> B["Prepare the draft"]
  B --> C["Review can send it back"]
  C --> D["A person sends"]
```

## Pinned externals

These ship with the six BBS plugins. They are pinned so a third-party update does not move on its own.

| Plugin | For |
|---|---|
| `claudeforge` | The generic `CLAUDE.md` engine under foundations. [Fork](https://github.com/Black-Box-Safety/ClaudeForge) |
| `impeccable` | Anything with a frontend: `/impeccable`. Installed from the fork's `plugin/` folder only, with its automatic edit hooks switched off in the marketplace entry. [Fork](https://github.com/Black-Box-Safety/impeccable) |
| `superpowers-chrome` | The rep's real Chrome, for product research. |
| `document-skills` | Anthropic's Word, PDF, and Excel skills. |
| `caveman` | Terse mode. Off until someone asks. Managed settings keep it off; a person turns it on for a session. |

Commons detail: [`docs/COMMONS.md`](docs/COMMONS.md).

## The rules that never bend

Enforced in managed settings and in [`plugins/bbs-foundations/hooks/doctrine/`](plugins/bbs-foundations/hooks/doctrine/), and stated once in [`AGENTS.md`](AGENTS.md).

- **Review can send a draft back. A person approves every send.** On Claude Code, managed settings put Outlook and Teams sends behind an Allow prompt and deny the other send-class tools. On Cursor, `.cursor/rules/bbs-invariants.mdc` is the control and it stays draft-only. Cursor does not inherit managed settings.
- **Never an invented number.** No price, stock, lead time, or certification fact from memory or the open web. Unknown is `[FLAG: why]`.
- **Certification language follows the channel.** The numbers and the small-business split are in [`canonical-facts.md`](plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md). Do not retype them here.
- **Systems of record win.** Business Central for money, Supabase for the catalog, SharePoint for documents, Sales CRM for pipeline. Point at the record.
- **When it goes wrong, log it.** One line in the folder's `FLAGS.md`, with one of the four buckets in the [template](plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md). A caught error means the review worked.

## What it will not do

Place orders. Send anything. Write to Business Central. Rename a customer folder. Invent a price. It searches, files, drafts, prices from real sources, fills forms, and tells you where every number came from.

## Connectors

A connector is how a teammate gets a system of record. This repo does not ship the credential. Do not copy `mcp.json` from one machine to another. Do not commit a plugin `.mcp.json` that contains a key, a buying-account number, or a URL path token.

Each skill already declares what it needs in `requires:` and `degrades-without:`. The readable list is:

```bash
python3 scripts/check_marketplace.py --requirements
```

**Org claude.ai connectors.** In Claude Code, Desktop, or the Claude Code panel: open [claude.ai](https://claude.ai) → Settings → Connectors, connect the name below, then run `/mcp` and confirm it is listed. When a teammate cannot self-install, an admin assigns it. That assignment is the fallback ([`docs/ADMIN-RUNBOOK.md`](docs/ADMIN-RUNBOOK.md) §3), not the only path.

| Plugin | Connector | Job it unlocks | Connect |
|---|---|---|---|
| Foundations | Microsoft 365 | `/bbs-my-voice` samples sent mail. Checkup needs nothing of its own. | claude.ai → Settings → Connectors → Microsoft 365 |
| Coach | None | Teaches and routes. | — |
| Sales | Grainger | Per-account cost for anyone who quotes. | claude.ai → Settings → Connectors → Grainger |
| Sales | Business Central (`bc_*`) | Quotes, orders, invoices. Read-only. | claude.ai → Settings → Connectors → Business Central (BC MCP, Custom API) |
| Sales | Sales CRM | Pipeline. | claude.ai → Settings → Connectors → BBS Sales CRM |
| Sales | SCPRS (`ca-procurement-intel`) | Buyer segments and spend for the California book. | claude.ai → Settings → Connectors → ca-procurement-intel |
| Sales | Firecrawl | Optional. Page reads when a skill says it can continue without it. | claude.ai → Settings → Connectors, if it is listed. The key stays in the environment, never in git. |
| Sales | USAspending | Federal award questions for primes. Not in this marketplace. BBS already runs it in Cursor as `bbs-usaspending` (`usaspending_*`). The public award API needs no key. | Cursor Settings → MCP, on the machine that needs it. Do not copy another machine's `mcp.json`. Public API: [api.usaspending.gov](https://api.usaspending.gov). |
| Sales | SAM.gov opportunities | Open solicitations for a NAICS or an agency, beside USAspending. Narrow lookup only. | Official Get Opportunities API: [open.gsa.gov](https://open.gsa.gov/api/get-opportunities-public-api/). Request a free public API key from the SAM.gov Account Details page. Store it in an environment variable named `SAM_GOV_API_KEY`. The value stays out of the repo. This change does not add a server. |
| Back office | Business Central (`bc_*`) | `bbs-order-reconciliation`, `so-search`, `bbs-po-status`. | Same Business Central connector as sales. The retired `bc-mcp-proxy` is required by nothing now. |
| Back office | CData Connect AI | `bbs-rebate-profitability`. A third path to the same books. | Gap. Do not retarget that skill onto the current Business Central connector in order to "finish" it. |
| Website | Supabase | The catalog. Whole team. | claude.ai → Settings → Connectors → Supabase, or Cursor Settings → Plugins → Supabase. A catalog write still waits for a person. |
| Website | Shopify | The storefront. Whole team. | Shopify CLI on the machine. Managed settings already ask before `shopify theme push`. Keep that ask. |
| Website | Firecrawl | Enrichment scrapes. Whole team. | Same Firecrawl connect as sales. The key stays out of git. |
| Website | Sirv | The image CDN the image pipeline uploads product photos to. | Sign in on the machine that uploads. The credential stays in the environment, never in git. There is no Sirv server in this repo. |
| Website | Vercel | Deploy. Whole team. | Vercel CLI on the machine (`vercel login`). Managed settings already ask before `vercel deploy`. Keep that ask. No Vercel token in the repo. |

**Not connectors.** Do not add QuickBooks (money is Business Central), SignNow (a person sends; signing stays denied), a separate Excel, Adobe, or LAO connector (Word, PDF, and Excel are the pinned `document-skills`; a budget page is a web read), GitHub, Mobbin, or an image or video generator. Do not add a second path to Business Central, Grainger, the CRM, Microsoft 365, SCPRS, Supabase, Shopify, Firecrawl, Sirv, or Vercel. Do not add a 150-tool third-party government bundle beside the narrow SAM.gov lookup.

## Install

**1. Run the setup script for your computer.** One script, once; safe to rerun. Run only the
one that matches your computer. The other one stops with a message and changes nothing.

| Your computer | How to tell | Script | Run it |
|---|---|---|---|
| **Windows PC** | Windows logo (Start) on the taskbar | [`scripts/bbs-setup.ps1`](scripts/bbs-setup.ps1) | In PowerShell, from the folder you saved it in: `powershell -ExecutionPolicy Bypass -File .\bbs-setup.ps1` |
| **Mac** | Apple logo, top-left of the screen | [`scripts/bbs-setup.sh`](scripts/bbs-setup.sh) | Install [Homebrew](https://brew.sh) once, then in Terminal: `chmod +x bbs-setup.sh && ./bbs-setup.sh` |

Either script installs the tools the document skills use (Git, Node, Chrome, LibreOffice,
the PDF/OCR tools, and the Python and Node libraries) and puts each one on PATH. Python
itself comes from the Windows script, or on a Mac from Apple's command-line tools, which the
Mac script asks for if they are missing. It installs Claude Code's `claude` command if it is missing, then installs **every
plugin in this marketplace**: six BBS plugins and five pinned externals. If a plugin fails,
it prints Claude Code's own error. Add `-DryRun` (Windows) or `--dry-run` (Mac) to preview
without installing anything. A good run ends with `Done.` Anything else, send the window to
Parker. Step by step: [`docs/REP-SETUP.md`](docs/REP-SETUP.md).

**2. Restart, then check.** Close every VS Code or Cursor window and quit the Claude Desktop
app, so they pick up the new PATH. Reopening one window is not enough. Then run:

```text
/bbs-checkup
/bbs-what-can-i-do
```

Anything red in the checkup prints the exact sentence to send the admin.

**Without the script** (it could not run), install the plugins by hand in a Claude panel.
This does not install the tools in step 1.

```text
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace
/plugin install bbs-foundations@bbs-claude-marketplace
/plugin install bbs-claude-coach@bbs-claude-marketplace
/plugin install bbs-sales@bbs-claude-marketplace
/plugin install bbs-marketing@bbs-claude-marketplace
/plugin install bbs-back-office@bbs-claude-marketplace
/plugin install bbs-website@bbs-claude-marketplace
/plugin install bbs-tools@bbs-claude-marketplace
```

Managed settings ([`plugins/bbs-foundations/docs/bbs-managed-settings.json`](plugins/bbs-foundations/docs/bbs-managed-settings.json)) enable all twelve plugins for everyone, once the admin has pasted the current file ([`docs/ADMIN-RUNBOOK.md`](docs/ADMIN-RUNBOOK.md) §1).

## Pick your path

| You are | Start here | Time |
|---|---|---|
| New to any of this | [`plugins/bbs-claude-coach/docs/TOOLKIT.md`](plugins/bbs-claude-coach/docs/TOOLKIT.md), or `/bbs-what-can-i-do` | ~10 min read |
| Seeing how the jobs fit | [`docs/OPERATING-LAYER.md`](docs/OPERATING-LAYER.md) | ~5 min read |
| Deciding what we build next | [`docs/STEWARD.md`](docs/STEWARD.md) | ~10 min read |
| A sales rep | [`docs/REP-SETUP.md`](docs/REP-SETUP.md), then `/bbs-checkup` | ~20 min, once |
| The admin | [`docs/ADMIN-RUNBOOK.md`](docs/ADMIN-RUNBOOK.md) §0 → §3a | One morning |
| Parker, trying Cursor (future; not rep onboarding) | [`docs/CURSOR-SETUP.md`](docs/CURSOR-SETUP.md) | As needed |
| Maintaining the website | [`workspace/README.md`](workspace/README.md) (open `bbs-web`), then [`plugins/bbs-website/README.md`](plugins/bbs-website/README.md) and `/bbs-onboard` | ~15 min |
| Changing a skill | [`plugins/bbs-website/docs/CONTRIBUTING.md`](plugins/bbs-website/docs/CONTRIBUTING.md) and the [design spec](docs/superpowers/specs/2026-09-11-rep-workspace-rollout-design.md) | As needed |

## Repo layout

```text
bbs-claude-marketplace/
├── .claude-plugin/marketplace.json     # manifest: 6 BBS plugins (unpinned) + 5 external (pinned)
├── .cursor/rules/bbs-invariants.mdc    # always-on Cursor doctrine; stamp onto the desk too
├── README.md                           # this file
├── REGISTRY.md                         # every BBS repo and asset: canon, harvest, parked, archived
├── workspace/                          # bbs-rep · bbs-web · bbs-admin + desk CLAUDE.md template
├── scripts/bbs-setup.ps1 · bbs-setup.sh · bbs-clone-web-stack.sh
├── scripts/install-desktop-launchers.sh · install-desktop-launchers.ps1
├── docs/
│   ├── OPERATING-LAYER.md              # pointer map: thesis, rules, desks, reviewer card
│   ├── STEWARD.md · REP-SETUP.md · CURSOR-SETUP.md · ADMIN-RUNBOOK.md · ADMIN-CLEANUP.md · MEASUREMENT.md
│   ├── acceptance/                     # one file per pilot gate run
│   ├── assessments/                    # what we found, dated
│   └── superpowers/                    # design specs and implementation plans
└── plugins/
    ├── bbs-claude-coach/               # literacy coach: understand, start, extend
    ├── bbs-foundations/                # CLAUDE.md, voice, checkup, doctrine
    ├── bbs-sales/                      # California book
    ├── bbs-marketing/                  # claims registry, one-pagers, email, logos, decks
    ├── bbs-back-office/                # Business Central after the win, read-only
    ├── bbs-website/                    # price list to product page
    └── bbs-tools/                      # bbs-fill: the one way Claude runs the vetted form scripts
```

## How we keep it honest

- **Version policy.** The six BBS plugins carry no version pin. A set `version` freezes updates until someone bumps it. Anthropic's default is that pin. We leave it off so a push to `main` updates every machine. Freeze only for a pilot, then unfreeze. The five externals stay pinned.
- **Registry.** [`REGISTRY.md`](REGISTRY.md) gives every repo and asset exactly one status. Change the status in the same commit as the change.
- **Measurement.** [`docs/MEASUREMENT.md`](docs/MEASUREMENT.md). Draft-fix rate is counted from `FLAGS.md`. No baseline number is invented here.
- **Acceptance.** A rep who is not the admin runs a real RFQ end to end, unaided. Result recorded in [`docs/acceptance/`](docs/acceptance/README.md).
- **Models.** Read them from `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/models.json`. It is generated. Do not hand-edit it.
- **Two checks, both required.** `claude plugin validate` (or `/plugin validate`) is Anthropic's schema check. `python3 scripts/check_marketplace.py` is BBS's check for the facts schema cannot see, including a cert number. Validate does not know a cert number. A FAIL fails the pull request (`.github/workflows/check-marketplace.yml`, ruled 2026-09-18).
- **`skill-creator`.** Anthropic's tool for evals inside a skill. It is a maintainer tool, same ruling as full superpowers. It is not enabled for every rep.
- **Dependencies.** `python3 scripts/check_marketplace.py --requirements`.

Leave these out, so the next person does not "complete" the plugin:

- A plugin `.mcp.json` that contains a key or a token. Ship the connect step. Do not ship the credential.
- LSP servers, background monitors, and a plugin `settings.json` that sets a default `agent`.
- Submitting these plugins to the public community marketplace. The repo is private.

## Contributing

Scope a change to one skill or one stage. Write the acceptance criterion before the change. Run `claude plugin validate` on the plugin directory and `python3 scripts/check_marketplace.py`. Commit with a conventional message. Never push a model update and a skill update the same week. Details in [`CONTRIBUTING.md`](plugins/bbs-website/docs/CONTRIBUTING.md).

---

<sub>Maintained by Black Box Safety, Inc. · government distributor · El Cajon, CA ·
Internal use. No single point of failure by design.</sub>
