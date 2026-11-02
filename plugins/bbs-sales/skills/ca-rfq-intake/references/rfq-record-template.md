# RFQ record template

Copy into the deal folder as `RFQ.md` at intake. Later stages append; nothing here gets
rewritten silently. A field you can't fill gets `[FLAG: why]`, never a guess.
Stages, line stages and strategies are the enums in `rfq-record-v2.md`; the hook rejects anything else.

```markdown
# RFQ — <buyer> / <institution> — <item>, <M.D.YY>

**Received:** <date> via <email | portal | phone>
**Buyer:** <name>, <title> · <email> · <phone>
**Agency / institution:** <agency> / <institution>
**Grainger account:** <number>   **BC customer:** <id>
**Ship to:** <address>

**Due:** <date time TZ>          **Submit via:** <email address | portal | their sheet>
**Solicitation #:** <number, or "none issued — reference BBS quote">
**Vehicle:** <NASPO ValuePoint 07-25-51-02.3 | DGS BPO | competitive>
**Pricing rule:** <at cost, no markup | bid — margin is the rep's call>
**Rep:** <Kim Quezon | Aanya Samarasinghe>
**CRM RFQ:** <RFQ-00xxxx | [not in CRM]>
**BC quote:** <SQ-10xxxx | none>
**PC quote:** <Q 1xxxx | none>
**Stage:** logged

## Lines (<n> items)

| # | Item / part # | Description | Qty | UOM | Lane |
|---|---|---|---|---|---|
| 1 | | | | | grainger / catalog / sourcing / FLAG |

Source states <n> lines; <n> captured.

## Pricing

| # | Vendor | Vendor ref | Cost | Sell | Strategy | Lead | Line stage | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | [sourcing] | | | | | | open | |

## Forms the buyer requires

- [ ] <form> — <blank attached | we supply | already on file>

## Stated requirements

- <no-substitution language, delivery window, brand restrictions, addenda>

## Flags

- <anything unreadable, ambiguous, or missing — one line each>

## Status

| Stage | Date | Evidence |
|---|---|---|
| logged | <YYYY-MM-DD> | RFQ.md created |
| sourcing | | |
| priced | | |
| quote built | | |
| packet built | | |
| delivered to rep | | |
| sent | | |
| outcome | | |
```
