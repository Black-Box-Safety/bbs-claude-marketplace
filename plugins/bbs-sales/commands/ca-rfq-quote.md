---
description: Take a logged CA state RFQ folder end to end — live pricing on the right account, the quote, the signed cert packet, a visual check of every page, and delivery into the buyer's folder.
---

# /ca-rfq-quote

The RFQ is logged. Now price it and build the packet. Invoke the `naspo-quote` skill and work its steps — it carries the field maps, the precedents, and the CalRecycle guidance. This is the running order.

1. **Read the folder.** The `RFQ.md` record, the buyer's `CLAUDE.md`, the worksheet header for the solicitation number, and the sibling folders from this institution's earlier RFQs. The answer is usually already on disk.
2. **Price.** `grainger_price` on the institution's own account. Confirm `account.sellRule` — at cost on state schedules, no markup.
3. **Quote.** Build it with `bbs-quote-builder`: zero markup, zero tax, FOB Destination, the solicitation number off the worksheet. Propose the next 900001-series quote number rather than assigning one silently.
4. **Packet.** Fill the certs with `scripts/fill_ca_forms.py`. CalRecycle recycled content is the one per-item judgment; use the SABRC guide, and write `[REP TO CONFIRM]` where the material is genuinely unclear rather than inventing a number on a form sworn under penalty of perjury.
5. **Sign.** Ask which of the three signers is on this one — Griffin for most CalRecycle 74s, Parker for the ones he owns plus Darfur and OBS 1000, Jackson for the disabled-veteran declarations. Check the DVBE cert expiration against the due date first. If the rep hasn't reviewed the items with the buyer, fill everything and leave the signature lines blank with a note.
6. **Verify by rendering.** Render every page to PNG and look at it. Clipped values, double-filled radio groups, and signatures landing on the caption are silent failures. Fix and re-render; never deliver a packet you haven't seen.
7. **Deliver.** Write the files into the buyer's `FILLED/` subfolder with the standard names, add `cover_summary.md`, and hand the rep the file list. Call out every judgment call you made on their behalf in the response itself — a CalRecycle code, a shortened description, a substituted item. Those are the ones that come back.
