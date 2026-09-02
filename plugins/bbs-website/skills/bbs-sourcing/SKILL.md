---
name: bbs-sourcing
description: Source pricing from vendors for a competitive bid RFQ at Black Box Safety. Use this skill whenever a BBS sales rep needs to turn an inbound competitive RFQ from a California state agency into vendor outreach — including when they say "source this RFQ," "get me pricing on these items," "reach out to vendors for this bid," "help me quote this," or paste/upload an RFQ worksheet and ask what to do next. Also use when the rep wants to follow up with non-responding vendors or leverage one vendor's quote against another's. Always use this skill for competitive, SB/DVBE, or Fair-and-Reasonable bids. DO NOT use when the RFQ is NASPO-routed or every item is available on grainger.com — those go through Provision Connect instead. Output is a sourcing brief plus vendor emails drafted in BBS's voice, rendered inline with pop-out buttons for Outlook.
---
> **BBS Website pipeline — stage: Quote bot.** See `site-wiring-map` for how this fits the whole flow.

> **Known gap:** this skill references companion files under `references/` (vendor directory, email templates, triage, input-handling) that are not yet included in the package. Until they are added, follow the inline guidance and flag the gap via `/bbs-review`.

# BBS Sourcing Skill

This skill converts a competitive-bid RFQ into a sourcing brief plus vendor outreach emails. It works for Black Box Safety sales reps responding to California state government RFQs where pricing has to come from direct accounts, wholesalers, or retail — not from NASPO/Grainger.

The skill has three modes, auto-detected from context:

1. **Initial sourcing** — rep brings in a new RFQ, skill triages and drafts first-round outreach
2. **Follow-up** — rep says "it's been 24 hours, no responses from X and Y" → skill drafts nudges
3. **Leverage** — rep has multiple vendor quotes in hand and wants a price-match ask → skill drafts the soft-leverage email

## Why this skill exists

Three failure modes break BBS's competitive bid margin, and this skill is built to prevent all three:

1. **Single-vendor sourcing** — sending the RFQ to one vendor and taking whatever price comes back. This leaves money on the table on every bid.
2. **No follow-up** — vendors don't respond, 24 hours pass, rep forgets, BBS submits its bid with incomplete pricing intel.
3. **Bidding on dead SKUs** — the state asks for an item that's been discontinued, the vendor quotes it anyway, BBS wins the bid, and then the order can't actually be fulfilled. This has happened at BBS before (SKU 44NF00BKR is a real example).

Every section below is engineered around one of these three problems. If you find yourself skipping a step, you're re-introducing one of these failure modes.

---

## Step 1 — Triage the RFQ (competitive vs. NASPO)

Before any sourcing work, determine whether this RFQ should even be sourced manually. If all the items are on grainger.com, it's a NASPO request and goes through Provision Connect — not this skill.

This check matters because subject lines lie. The RFQ Angel Ochoa at CDCR CRC sent for "ROUNDUP, TRIMMER HEADS, LINE SPOOL AND ELECTROLYTES" looks like a competitive bid but is actually NASPO — every item is on Grainger's catalog. Running the sourcing workflow on a NASPO RFQ wastes everyone's time.

**Triage procedure:**

1. Extract the 3–5 most specific item names from the RFQ (brand + model where possible).
2. For each, run a quick web search scoped to `grainger.com` to see if the item is listed there.
3. Count the matches:
   - **All items found on Grainger** → Tell the rep: "This looks NASPO-eligible — route through Provision Connect, not manual sourcing." Stop.
   - **Some items on Grainger, some not** → Tell the rep: "Mixed RFQ — items [X, Y, Z] are NASPO-sourceable. I'll source the remaining items. Confirm before I proceed." Wait for confirmation.
   - **No items on Grainger** → Proceed to Step 2.

See `references/competitive-vs-naspo-triage.md` for edge cases and signal words.

---

## Step 2 — Extract RFQ metadata

Pull out the following from the RFQ (email body, attached worksheet, or PDF):

- **Agency** — e.g., CDCR California Men's Colony, CAL FIRE Butte Unit, CalVet Fresno, DSH Atascadero, EDD, Water Boards
- **Requestor** — the state employee's name and email
- **Deadline** — date + time, e.g., "Due 4/20/26 by 3:00 PM PST"
- **Line items** — SKU/part number if given, description, quantity, unit of measure, specs
- **Ship-to address** — the destination for the goods
- **Required forms** — OBS 4007(B), Bidder Declaration, Darfur Contracting Act, CalRecycle 74, GenAI Disclosure, etc. (relevant for the Compliance Forms skill later — not this one)

**If the rep pasted text:** parse from what they pasted.
**If the rep uploaded a PDF/XLSX:** use the appropriate file-reading approach (see `references/input-handling.md`).
**If the rep pointed at an Outlook email:** fetch the email + attachments via the M365 tools.

**Missing data handling:**
- **Ship-to not in RFQ** → ask the rep directly. Don't guess. Facility addresses vary within the same agency.
- **Deadline ambiguous** → ask the rep. Deadline drives the vendor-facing response window.
- **Line-item specs vague** (e.g., "safety glasses, black, medium-heavy duty" with no SKU) → see Step 4.

---

## Step 3 — Confirm rep identity and compute vendor deadline

**Rep identity:** Check memory for the rep's name and email. If not stored, ask once: "Which BBS rep is running this — name and email for the signature block?" Store the answer so future runs skip this step for the same person.

**Vendor deadline = agency deadline − 48 hours.** Hard rule. Vendors need buffer, and BBS needs buffer to compile the final quote. If the agency deadline is less than 72 hours out, flag it to the rep: "Tight timeline — you'll want to phone-follow-up these vendors, not just email."

---

## Step 4 — Classify and verify each line item

For every line item, do two things in parallel:

**4a. Availability check.**
Quick web search on the brand + model/SKU. Look for signals like "discontinued," "obsolete," "end of life," or the item not appearing on the manufacturer's current product listing. Flag anything suspect to the rep as: **"⚠️ Line X: [item] may be discontinued — confirm with vendor before quoting."** Don't skip this. BBS has been burned by winning bids on dead SKUs before.

**4b. Vertical classification.**
Match each item to one of these verticals (same taxonomy as `references/vendor-directory.md`):

Medical Supplies · Tactical Gear · Office Supplies · Janitorial/Sanitation · HVAC/Plumbing · Safety/PPE · Industrial Kitchen · IT Goods · Firefighting Equipment · Fleet/Auto Parts · Specialty/Other

If an item doesn't fit cleanly, mark it "Specialty/Other" and handle per Step 5c.

---

## Step 5 — Select vendors per line item

This is where the skill's decision quality compounds. The procedure:

### 5a. Ask the rep about preferences first

Before doing any research, ask: "For these items, do you have vendors you want to reach out to, or should I pick?"

- If rep names vendors → use those. Then find the exact manufacturer product that matches each line-item description (this is where BBS's product expertise lives — the vendor names the category, the skill finds the SKU match).
- If rep has no preference → proceed to 5b.

### 5b. Consult the BBS vendor directory

Look up the vertical in `references/vendor-directory.md`. Pick candidates per the ranking below. **Minimum 2 vendors per line item.** This is the hard floor — never send to one vendor. Three is the default target. Go to four for high-dollar lines (>$10K per line).

**Ranking priority (always in this order):**
1. **DPA Buying Group members** — Radians, R3 Distribution, Global Glove, Mechanix, etc. Quarterly rebates make these the highest-margin sources. Full list in the vendor directory.
2. **Direct accounts** — BBS has payment terms and pricing history with these manufacturers. ~30% typical GP.
3. **Wholesalers** — Safeware, Airgas, Essendant, Waxie, Ferguson, etc. ~20% typical GP.
4. **Retail** — Amazon, Home Depot, Webstaurant. Only as last resort or benchmarking fallback.

If the vertical has DPA members available, at least one of them should be in the outreach list.

### 5c. Search online for new vendors

Do this when the BBS directory doesn't cover the item, or when the rep wants more options for a high-dollar line.

**Credibility ranking for online finds:**
1. Authorized distributor (verified on manufacturer's site — look for a "Where to Buy" or "Find a Distributor" page)
2. B2B wholesaler with real business presence (clear phone, address, B2B quote process)
3. Retail ecommerce (Amazon, eBay, etc.) — benchmarking only, never preferred

Present web-found vendors to the rep for approval before including them in outreach.

### 5d. Group items by vendor

Once vendors are selected per item, group: one email per vendor, covering all line items that vendor can credibly quote. This matches the BBS convention — Parker's AmericanFlags.com outreach bundled four items into one email to one vendor.

---

## Step 6 — Identify the right contact per vendor

For each vendor, decide who to email.

**Named account manager preferred.** In this order:
1. LinkedIn search for "[vendor name] government sales" or "[vendor name] account manager California"
2. Manufacturer's "Find a Rep" or regional sales page
3. Manufacturer's "Contact Us" page

**If no named contact found after those three tries:** use the generic `sales@vendor.com` address AND include this sentence in the email body: *"If you're not the right contact for government distributor quotes, could you please connect me with your account manager?"* This captures the escalation without requiring a second outreach.

---

## Step 7 — Select the email template tier

Three tiers. Pick one per vendor based on relationship state. See `references/email-templates.md` for the exact template text.

| Tier | Trigger |
|---|---|
| **Warm** | Rep running the skill has prior email thread with this vendor (ask the rep, don't auto-detect) |
| **Referral** | Rep has no history, but another BBS teammate does — rep names the colleague and a short context |
| **Cold** | Nobody at BBS has prior contact with the vendor |

For the Referral tier: ask the rep "has anyone at BBS worked with [vendor] before?" If yes, ask "who, and what did they work on?" Use those details in the opening line.

If multiple BBS teammates have worked with the vendor, ask the rep which one to name.

---

## Step 8 — Draft the emails

Use the templates in `references/email-templates.md`. The skill's job here is three things:

1. Fill in the template variables: vendor contact name, end-customer agency (e.g., "CAL FIRE Butte Unit"), line items with links/SKUs/qty, ship-to address, vendor response deadline.
2. Use BBS's full signature block (see `references/email-templates.md` — includes SDVOSB UEI, DVBE #, all three contract vehicle numbers).
3. Render each email with the **message_compose_v1** tool (`kind: "email"`). This produces a preview card inline with "Open in Mail" → launches the rep's Outlook with the draft pre-filled.

Every cold/referral email must include the transparency line: *"I'm getting quotes from a few different vendors to get best pricing."* This is BBS's soft-leverage baseline — vendors expect competition, and saying so upfront sets the tone for future price-match asks without being adversarial.

---

## Step 9 — Produce the sourcing brief in chat

After all emails are composed, summarize in chat as a brief the rep can glance at and act on. Use this structure:

```
## Sourcing Brief: [Agency] — [RFQ short name]
**Agency deadline:** [date/time]
**Vendor response deadline:** [date/time, 48hr buffer]
**Procurement method:** [SB/DVBE | Informal Competitive | Fair & Reasonable | Formal Solicitation]
**Ship-to:** [address]

### Line items
| # | Item | Qty | Vertical | Vendors contacted | Notes |
|---|---|---|---|---|---|
| 1 | [description] | [qty] | [vertical] | [vendor A, B, C] | [availability flag if any] |

### Vendor outreach sent
- **[Vendor name]** — [cold/referral/warm] — [items X, Y] — contact: [name or sales@ with escalation ask]
- ...

### Follow-up plan
- Plan to check for responses on **[date = send date + 24 hrs]**
- Non-responders at that point → run the Follow-up mode of this skill to draft nudges
- When 2+ quotes are in → run the Leverage mode to draft price-match asks where a meaningful delta exists

### ⚠️ Flags
- [any discontinued SKU concerns]
- [any items with vague specs the rep should confirm with the agency]
- [tight-timeline warnings]
```

---

## Mode 2 — Follow-up emails

**Trigger:** Rep says something like "follow up with the vendors who haven't responded" or "it's been 24 hours, nudge them."

**Procedure:**
1. Ask rep which vendors need a nudge (rep confirms from the original outreach list)
2. For each non-responder, draft a short follow-up using the template in `references/email-templates.md` (Follow-up section)
3. Render with message_compose_v1, kind "email"

Keep follow-ups short. Tone is: "just making sure you got this." Not: "why haven't you responded."

---

## Mode 3 — Leverage emails

**Trigger:** Rep has vendor quotes in hand and wants to push one vendor to match another's price.

**When to trigger a price-match ask (not every bid):**
- Delta between high quote and low quote is **≥15%** or **≥$500 on the line**, whichever is greater
- The high-quote vendor is one BBS wants to keep engaged (DPA member, direct account, or strategic relationship) — if they're a random retail find, just go with the low quote and skip the leverage email
- The agency deadline allows time for a requote (at least 24 hours remaining)

**Procedure:**
1. Rep provides the quotes (e.g., "Culinary Depot came in at $10K, Chef's Toys at $11K")
2. Skill asks: "Do you have a personal reason you want to keep working with [high-quote vendor]? E.g., past project, helpful rep, desire to establish an active account?"
3. Rep provides the reason (or says "use the generic one")
4. Skill drafts the leverage email using the Price-Match template in `references/email-templates.md`

The leverage template follows Parker's exact voice: thank them, state the current low quote transparently, include the relational reason, give them a clear opportunity to requote "if you are able to get under the current low price in any meaningful way." No pressure, no deadlines beyond the vendor deadline already set.

---

## Guardrails

These are the rules the skill must not relax, no matter what the rep asks:

1. **Minimum 2 vendors per line item.** If the skill can only find one vendor for an item, flag it and ask the rep how to proceed — don't quietly proceed with single-vendor sourcing.
2. **Availability check on every SKU.** Discontinued items must be flagged before outreach goes out.
3. **Never use customer-provided pricing as the basis for vendor outreach.** If the RFQ mentions "not to exceed $X" or "previous price was $Y," that's for the BBS quote side — do NOT share it with vendors. Vendors quote blind.
4. **End-customer agency is always named** in cold and referral emails. It gives the vendor context and motivates their response. Warm emails can skip this for known vendors.
5. **Ship-to address is always included** in every email. Vendors can't quote freight without it.
6. **Full BBS signature on every email.** SDVOSB UEI, DVBE #, all three contract vehicles. These credentials matter for DPA Buying Group pricing and DVBE set-aside qualification — they also tell the vendor this is a real opportunity.

---

## Reference files

- **`references/vendor-directory.md`** — BBS's vendors by product vertical, with tier flags (DPA Buying Group, Direct Account, Wholesaler, Retail) and account notes
- **`references/email-templates.md`** — Full text for all five templates: Cold, Referral, Warm, Follow-up, Price-Match. Plus the BBS signature block.
- **`references/competitive-vs-naspo-triage.md`** — How to distinguish competitive RFQs from NASPO requests. Signal words, Grainger check procedure, edge cases.
- **`references/input-handling.md`** — How to read the RFQ when it arrives as pasted text, PDF, XLSX, or an Outlook email reference.
