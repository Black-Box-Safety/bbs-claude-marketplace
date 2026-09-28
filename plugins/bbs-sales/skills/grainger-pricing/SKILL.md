---
name: grainger-pricing
description: >-
  Get live Grainger pricing, stock and ship dates for Black Box Safety through the Grainger
  MCP — the authorized path for every Grainger price at BBS, which replaced the
  b2b.blackboxsafety.com punch-out. Use whenever a rep wants unit prices for Grainger item
  numbers, is filling the Unit Price column of an RFQ or NASPO worksheet, asks what Grainger
  charges on a facility's account, needs an item number found from a description or
  manufacturer part number, asks which account a buyer prices on, or asks whether something is
  in stock and when it ships. Never price a Grainger item from the open web or from memory. Do
  NOT use to extract item numbers from a cart PDF, screenshot or DWR RFQ (rfq-item-extract
  produces the list this prices), to check DGS BPO eligibility (dgs-bpo-item-check), or to
  build the quote document (bbs-quote-builder). If a rep says only "check these items", ask
  whether they mean price or BPO eligibility.
requires: [grainger]
---

# Grainger pricing — via the Grainger MCP

Every Grainger price at BBS comes from the Grainger MCP. It replaced the
`b2b.blackboxsafety.com` punch-out, so there is no browser automation to drive and no
session to log into — the tools return contract pricing directly.

**Never take a Grainger price from the open web, a search result, a cached page, or
memory.** A grainger.com list price is not what the buying account pays.

## The two rules that make a price right or wrong

**1. Pricing is per-account, and a wrong account returns a wrong price that still looks
valid.** Each account has its own discount off the contract reference price, set by its
pricing schedule and sometimes overridden per account. There are 178 accounts across 8
schedules. You must price against the account that will actually buy. The tools require it
and fail rather than guess — do not work around that by picking a plausible account.

**2. BBS sells Grainger at cost. Never apply markup.** `unitPrice` from the MCP is BBS's
cost *and* the customer's price; BBS is paid through a contract rebate rather than margin.
Confirm it on the response: `account.sellRule` reads `at_cost` on every schedule today. If
you ever see a different sell rule, stop and ask the rep rather than inventing a margin.
Rare exceptions are handled by the rep directly, not here.

This second rule matters when the quote document is built: pass these prices through to
`bbs-quote-builder` as final, and do not let its markup math touch a Grainger line.

## Workflow

### 1. Resolve the account first

If you do not already have the account number, find it before pricing anything:

```
grainger_accounts(query="Porterville")      # facility name, department, account #, or track code
```

It searches by facility name, department (CDCR, DSH, CSU, CalVet…), account number or
pricing schedule, and returns each match with its pricing schedule and sell rule.
Deactivated accounts come back clearly labelled — a buyer sitting on a dead account shows
up as a fact rather than a mystery error. If more than one account plausibly matches, ask
the rep which facility is buying; do not choose for them.

### 2. Price the items

With exact Grainger item numbers:

```
grainger_price(account="Porterville", productCodes=["6GRH5", "1A101"])
```

Up to 48 item numbers per call. Pass `response_format="markdown"` when the rep wants a
readable table — it calls out the account, the sell rule and the per-row discount.

If you only have a description, search for the item number:

```
grainger_search(account="Porterville", query="nitrile gloves")
```

Paginated — check `has_more` and pass `offset` for the next page.

**If the line carries a manufacturer part number *and* a description, use
`grainger_resolve_part` instead of `grainger_search`.** That is the normal shape of a
requisition, the two fields disagree often, and the part number is usually the corrupt
one. `rfq-item-extract` feeds exactly these lines in.

```
grainger_xref(action="lookup", parts=["B402"])        # free; recalls what was already proven
grainger_resolve_part(account="Porterville", parts=[
    {"mfrPart": "B402", "expect": {"Extinguisher Capacity": "20 lb"},
     "note": "requisition line 0004"}])
```

Read the `verdict` and do not paraphrase it:

| verdict | what it means | what to do |
|---|---|---|
| `match` | catalogue agrees with the requisition | price it |
| `mismatch` | the catalogue disagrees with the stated expectation. **Not** unavailable | resolve with the buyer *before* quoting — do not silently pick either side |
| `not_found` | no Grainger item for that part number | flag for sourcing |
| `lookup_failed` | the gateway was unreachable | **never report this as the item being unavailable.** It is a failed call — retry or flag it |

Check `grainger_xref` first; it is free and carries forward what an earlier session
verified. When you establish a correction by other means, write it back with
`action="learn"` so the next session does not re-make the mistake.

### 3. Stock and ship dates, when the rep needs them

```
grainger_availability(account="Porterville", postalCode="95811",
                      items=[{"code": "6GRH5", "qty": 10}])
```

Real-time stock, ship date and branch pickup at a destination ZIP. `shipComplete=true`
quotes the date the whole order can ship together — use it when the agency needs one
delivery rather than trickled shipments.

### 4. Report what you actually got

State the account you priced against, in the output, every time. A price without its
account is not checkable.

Anything the tools did not return is `[FLAG: why]`, never an estimate. An item the search
cannot find is an item to source — hand it to `bbs-sourcing` or `vendor-quote-email`
rather than guessing a price.

**Never substitute a product.** If Grainger does not carry the exact part number, flag it
for sourcing. Do not pick an alternate to keep the line populated, and do not accept the
alternates Grainger itself offers on a miss — the customer specified that manufacturer part
number for a reason. A substitution needs the rep's explicit approval, not yours.

**Confirm the unit of measure matches the pack size requested.** Grainger sells by each,
by the pack of 12, by the case. A price that is right per-package and wrong per-each is a
wrong extended price on the bid, and nothing flags it. If the requisition does not state a
pack size, or the returned unit does not match it, flag the line rather than assuming.

## Where the list comes from, and where it goes

- **Items arrive** as a cart PDF, a screenshot or a DWR RFQ → `rfq-item-extract` produces
  the list first.
- **Eligibility** is a separate question → `dgs-bpo-item-check` tests the part numbers
  against the active DGS BPO. Being priceable and being on the BPO are not the same thing.
- **The customer document** → `bbs-quote-builder`, with these prices passed through at
  cost.
- **A whole state RFQ response** → `naspo-quote` orchestrates pricing plus the compliance
  packet.

## If the connector is missing

The Grainger MCP is an admin-assigned connector. If `/mcp` does not list it, pricing
cannot be done on this machine — say so and send the rep to Parker. Do not fall back to
the open web; that is the failure this skill exists to prevent.

---

Owner: Parker. Last verified 2026-09-15.
