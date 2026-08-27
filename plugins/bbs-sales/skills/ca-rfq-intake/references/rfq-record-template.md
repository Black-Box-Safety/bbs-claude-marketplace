# RFQ record template

Copy into the deal folder as `RFQ.md` at intake. Later stages append; nothing here gets
rewritten silently. A field you can't fill gets `[FLAG: why]`, never a guess.

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

## Lines (<n> items)

| # | Item / part # | Description | Qty | UOM | Lane |
|---|---|---|---|---|---|
| 1 | | | | | grainger / catalog / sourcing / FLAG |

Source states <n> lines; <n> captured.

## Forms the buyer requires

- [ ] <form> — <blank attached | we supply | already on file>

## Stated requirements

- <no-substitution language, delivery window, brand restrictions, addenda>

## Flags

- <anything unreadable, ambiguous, or missing — one line each>

## Status

| Stage | State | Date |
|---|---|---|
| Logged | done | <date> |
| Priced | | |
| Packet built | | |
| Sent | | |
| Outcome | | |
```
