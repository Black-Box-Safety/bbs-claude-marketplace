# Glossary — the five kinds of tools (plain words)

You do not need to memorize these. Knowing what each one *is* means Claude feels less
like magic. The calm human reading path is this plugin's `docs/TOOLKIT.md`.

## Skill

A playbook Claude follows for a specific job. You usually do not call it by name — Claude
notices the job and uses it. Example jobs: "log this RFQ," "price these Grainger items,"
"make a brand page."

## Command

A shortcut **you** type, always starting with `/`. It kicks off a job on purpose.
Examples: `/bbs-checkup`, `/bbs-my-voice`, `/ca-rfq`, `/bbs-what-can-i-do`.

## Plugin

A bundle of related skills and commands for one area of work (quote desk, website,
foundations, this coach). Installing a plugin gives you everything inside it. On a managed
BBS machine, Parker turns plugins on for everyone — you do not install by hand day to day.

## Connector (MCP)

A live link to a real system so Claude reads real data instead of guessing: Business
Central for orders and invoices, Grainger for pricing, Outlook and Teams for mail and
messages. **Connectors are not plugins.** Parker assigns them in the Claude admin console.
Run `/mcp` to see yours. Without a connector, skills still load — they just have nothing
real to read.

## Hook

Something that runs quietly in the background. At BBS, hooks mostly inject company rules
into a job so the guardrails are there without you thinking about them. You rarely touch
these.

## Draft vs send

Everything Claude produces — quotes, emails, filled forms, promo pages — is a **draft**
until a person reviews it. Claude can send an email or Teams message only after you click
Allow on that send; it never sends on its own. That rail is on for everyone. See `aup-rails.md`.

## Related words you will hear

| Word | Meaning here |
|---|---|
| Marketplace | This repo — the catalog of BBS plugins plus pinned outside tools |
| Commons | Third-party plugins we pin (Chrome browsing, document skills, terse mode) — the marketplace repo's `docs/COMMONS.md` lists them |
| Managed settings | Policy Parker pushes from the admin console (plugins on, send tools denied, company memory) |
| System of record | The place a fact is true (Business Central for money, Supabase for catalog, SharePoint for documents) |
