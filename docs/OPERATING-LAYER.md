# Operating layer

A pointer map. Facts live in the files named here. This page does not restate them.

## Thesis

Six plugins are the work Claude is for. Foundations and coach cover everyone. Sales is the California book. Marketing is one-page pieces, campaign email drafts, logo rights, and prior brochures and decks. Back office is Business Central after the win, and it is read-only. Website is the catalog and the storefront. Marketing does not create California buyer folders and it does not run the quote desk.

Out of scope everywhere: sending, placing orders, writing to Business Central, renaming customer folders. Body armor and CSU/UC stay out of the Kim/Aanya California book. They stay in the company. They are part of why marketing is its own plugin.

The jobs, the first commands, and the connectors are in [`README.md`](../README.md).

## Global rules

| What | Where |
|---|---|
| Invariants every agent in this repo works under | [`AGENTS.md`](../AGENTS.md) |
| Company memory pushed to every managed session | the `claudeMd` block in [`plugins/bbs-foundations/docs/bbs-managed-settings.json`](../plugins/bbs-foundations/docs/bbs-managed-settings.json) |
| Doctrine injected when a subscribed skill runs | [`plugins/bbs-foundations/hooks/doctrine/`](../plugins/bbs-foundations/hooks/doctrine/) |
| Certification strings and the channel split | [`plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`](../plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md) |

## Runbooks and accepted work

| What | Where |
|---|---|
| How a work session runs | [`docs/STEWARD.md`](STEWARD.md) |
| Admin calendar, including monthly FLAGS triage | [`docs/ADMIN-RUNBOOK.md`](ADMIN-RUNBOOK.md) §6 |
| Rep setup | [`docs/REP-SETUP.md`](REP-SETUP.md) |
| Accepted packets | the buyer folder's `FILLED/` on the SharePoint desk named below |
| Cases a repeated flag is supposed to become | [`docs/evals/`](evals/) |

This map does not add those eval cases.

## Per desk

Clients and people stay out of this repo.

| What | Path | Do not |
|---|---|---|
| California buyer folders: `CLAUDE.md`, `quote-log.md`, `FLAGS.md`, filled packets | SharePoint `Customers/State of CA Agencies/All RFQ's by Agency/<Agency>/…` | Copy a buyer file into git |
| Desk-root context to stamp onto that tree | [`workspace/DESK-CLAUDE-template.md`](../workspace/DESK-CLAUDE-template.md) | Edit the live SharePoint copy from this repo |
| Per-customer private profile | `bbs-sales-vault` `accounts/` | Copy the profile here |
| Roster | `bbs-sales-vault` `team.md` | Copy the roster here |

## Corrections

The log shape is [`plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md`](../plugins/bbs-foundations/skills/bbs-claude-md-forge/references/flags-template.md): factual error, buyer preference, missing information, style, and whether it happened more than once.

A repeat is supposed to become a rule in the owning skill and a case in `docs/evals`, in the same change. Wednesday is the hour for that pass. The calendar entry stays the monthly FLAGS triage in [`docs/ADMIN-RUNBOOK.md`](ADMIN-RUNBOOK.md) §6. The draft-fix rate counted from those lines is one row in [`docs/MEASUREMENT.md`](MEASUREMENT.md). No baseline is invented there.

## Reviewer job card

Applies to every plugin: a quote, an order answer, a customer email, and a product page.

1. Check the draft against that plugin's rules.
2. Score pass, or send it back.
3. Never email. Never sign. Never invent a number.

The draft stops at a person. This card is the spec a later review skill has to match. This change does not add that skill.
