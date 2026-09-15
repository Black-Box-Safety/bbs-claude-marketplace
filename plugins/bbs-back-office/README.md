# bbs-back-office

The lane that used to end at "bid submitted."

Everything in this plugin reads Black Box Safety's **Business Central** and answers a
question somebody asks after the quote goes out. None of it writes to BC — these
skills report, they don't post.

| Ask | Skill |
|---|---|
| "What SO is this customer PO?" / "where's my order?" | `so-search` |
| "What has this vendor actually shipped us?" / "what's still outstanding on PO-xxxx?" | `bbs-po-status` |
| "Did we actually make money on this?" / margin by account or contract vehicle | `bbs-rebate-profitability` |
| "They sent the wrong item" / short shipment / the price on the PO is wrong | `bbs-order-reconciliation` |

## Why these four are together

They share a data source and a failure mode: **the surface answer is wrong**, and each
skill exists to stop someone trusting it.

- `bbs-po-status` — the PO header's `fullyReceived` flag is systematically unreliable.
  Answer from the receipt lines, never the flag.
- `bbs-rebate-profitability` — item ledger entries carry COGS at Grainger *list*, so
  raw BC margin understates every Grainger deal. The real number appears only after
  layering in the rebate tied to each invoice's contract-code dimension.
- `so-search` — an order that has not been invoiced yet does not appear where people
  look for it, so the skill falls back to open sales orders rather than reporting
  "not found".
- `bbs-order-reconciliation` — the reported symptom is the last link in a chain. "The
  price is wrong on the PO" is usually a quote that mirrored a sourcing sheet that
  mirrored something a rep pasted in months ago; the fix has to attach to the cause.
  Moved here from `bbs-foundations`, where it sat apart from the rest of the post-award
  work.

## Install

```bash
/plugin marketplace add Black-Box-Safety/bbs-claude-marketplace
/plugin install bbs-back-office@bbs-claude-marketplace
```

Needs the BBS Business Central MCP connector. Without it these skills have nothing to
read; connect it first.
