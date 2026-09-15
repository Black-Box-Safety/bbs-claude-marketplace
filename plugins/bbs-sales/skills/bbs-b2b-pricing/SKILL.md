---
name: bbs-b2b-pricing
description: Pull account-specific Grainger pricing for Black Box Safety (BBS) through the b2b.blackboxsafety.com punch-out. Use whenever the user asks to price items, quote an RFQ or NASPO line-item worksheet, look up Grainger pricing for a specific facility account, check what Grainger sells a part for under a BBS account, or "run this through the punch-out." Also triggers on phrases like "price these Grainger items," "check b2b pricing," "pull NASPO pricing," "run the Grainger punch-out," or when a spreadsheet / PDF / list of manufacturer part numbers is provided alongside a BBS facility account number. This is the authorized path for Grainger pricing at BBS — always prefer it over open-web Grainger searches.
---

# BBS B2B Grainger Pricing

This skill pulls account-specific Grainger pricing for Black Box Safety customers using the b2b.blackboxsafety.com punch-out. It's the authorized path — BBS policy forbids looking up Grainger pricing via open web search, but the punch-out under a specific facility account is allowed because the prices returned are already negotiated contract pricing tied to that account.

The typical use is pricing a NASPO, RFQ, or bid response where the customer has sent a list of manufacturer part numbers and BBS needs to return unit pricing for each item that Grainger carries — plus a clean sourcing RFQ email for any items Grainger doesn't carry.

## When to use this skill

Trigger any time the user:
- Provides a list of manufacturer part numbers (Hach, 3M, Honeywell, etc.) and a BBS facility account number and asks for pricing
- Uploads a NASPO/RFQ line-item worksheet with empty Unit Price / Extended Price columns
- Says "price these on account XXXXXXXXX," "run this through the punch-out," "pull the B2B pricing," or any variant
- Asks for a Grainger quote for a California state agency, CDCR facility, UC/CSU campus, or any other BBS customer

If the user mentions they need Grainger pricing but you don't have an account number yet, ask for it before navigating.

## Workflow

### Step 1: Gather inputs

You need three things:

1. **Account number** — 9-digit BBS facility account (e.g., 887895111). If the user hasn't provided one, ask.
2. **Items to price** — a list of manufacturer part numbers with quantities. Input can arrive as:
   - A spreadsheet (read with openpyxl; the part numbers are usually in a column literally called "Part Number," "P/N," "Mfr Part #," or similar)
   - A PDF (use the `pdf` skill to extract, then parse the line items)
   - A plain list pasted in chat
3. **Ship-to address** — only needed if items get flagged for sourcing. Don't block on this until you know something needs sourcing.

If the input format is anything other than a plain list, first extract a clean list of `{item_description, manufacturer_part_number, qty, unit}` tuples before doing any browser work.

### Step 2: Open the punch-out

The BBS B2B site is `https://b2b.blackboxsafety.com/`. In most sessions the user is already logged in — check first rather than assuming you need to authenticate. If not logged in, stop and ask the user to log in (BBS policy: Claude does not enter passwords).

Once on the B2B home page, look for a "Grainger" / punch-out link. The underlying link has the format:

```
https://b2b.blackboxsafety.com/admin/no_app/data_dumps_mis/goto_punchout.cfm?cid={ACCOUNT_NUMBER}&uid={SESSION_UID}&supplier_id=1&adminbuy=64
```

`supplier_id=1` is Grainger. The `cid` parameter carries the facility account, so confirm the `cid=` value matches the account number the user specified before clicking through. If it doesn't match, the user may need to switch accounts in the admin portal first — ask them, don't guess.

Clicking the punch-out lands you on `grainger.com` with the account's contract pricing active. Every subsequent search returns "Your Price" — the account-specific price — alongside a "Contract Reference Price." Capture **Your Price**, not Contract Reference Price.

### Step 3: Price each item

For each manufacturer part number, navigate to:

```
https://www.grainger.com/search?searchQuery={MFR_PART_NUMBER}
```

Three outcomes are possible. Match the behavior to what you see on the page:

**A. Exact hit.** Product detail or search result shows a HACH/3M/Honeywell/etc. item that matches the part number. Capture:
- Grainger Item # (6–7 char alphanumeric like `897Y19`, `2VHW1`)
- Your Price (the "account specific price")
- Unit (each, pkg of 12, etc.) — confirm it matches the requested pack size

**B. No direct hit, Grainger shows alternates.** The page reads "Grainger does not carry the product you searched for. These N products are potential alternates..." This means **Grainger does not carry it.** Flag for sourcing. Do not substitute an alternate without explicit user approval — the customer specified the manufacturer part number for a reason.

**C. Redirected to a category page with no matching product.** Search was interpreted as a category browse (common with numeric-only part numbers). Retry once with `hach <partnumber>` (or the actual manufacturer name) in the search query. If still no match, flag for sourcing.

Record results as a table with: `Item Description | Mfr P/N | Grainger Item # | QTY | Unit Price | Extended Price | Status (priced / flagged)`.

### Step 4: Populate the output

**If input was a spreadsheet:** Use openpyxl to fill the existing "Unit Price" and "Extended Price" columns. Insert a new "Grainger Item #" column so the traceability is preserved. Use the template at `assets/fill_worksheet.py` as a starting point — it handles the NASPO line-item worksheet pattern and marks flagged rows with a soft-red fill.

**If input was a list or PDF:** Return a clean markdown table in chat showing priced items and a separate table of flagged items. Save the priced table as `priced_items.xlsx` in the outputs folder for easy re-use.

### Step 5: Handle flagged items (if any)

For any item Grainger doesn't carry, draft a sourcing RFQ email to Grainger customer service using the BBS standard template at `references/sourcing_email_template.md`. Do **not** guess target prices or vendor contacts — leave the template's placeholder language ("Grainger carries other products from this manufacturer and should have internal contact") unless the user has given specific guidance.

Required fields for the email:
- Account number (from Step 1)
- Ship-to address (ask the user if not already provided)
- Per-item block: QTY, P/n, Description, Vendor (manufacturer name), Vendor contact (placeholder text)
- Signed from the user (Parker Marshall, Sales Manager, Black Box Safety, Inc. by default)

Save the draft as a `.md` file in outputs. If the user asks to send it, open a pre-populated Outlook compose window in the browser — but **never click Send.** Leave that to the user.

## Important policies

- **Contract price is BBS's cost, not the sell price.** The "Your Price" returned by the punch-out is what BBS pays Grainger on this account. It is not the NASPO / cooperative / RFQ sell price the customer will see. Make this clear in your final summary — Parker applies his own margin before submitting to the customer.
- **Never substitute products.** If Grainger doesn't carry the exact part number, flag it. Do not pick an "alternate" to keep the line populated.
- **Never search Grainger on the open web.** Only use the punch-out path. If for any reason the punch-out is inaccessible (account locked, punch-out errors, session expired), stop and tell the user — do not fall back to `grainger.com` without a punch-out session.
- **Don't fabricate prices.** If you can't get a clean read of Your Price, capture the Grainger item number and mark the price as "needs verification" rather than guessing from the Contract Reference Price.

## Output format

Always end with a summary that includes:

1. Subtotal of priced items (clearly labeled as Grainger account cost, not sell price)
2. Count and list of flagged items needing sourcing
3. File links to the populated worksheet and the sourcing email draft (if one was created)
4. A one-line note reminding the user to apply NASPO/RFQ margin before responding to the customer

## Reference files

- `references/sourcing_email_template.md` — The exact format Parker uses for Grainger sourcing quote requests (per-item blocks with QTY, P/n, Description, Vendor, Vendor contact).
- `references/grainger_search_patterns.md` — Tips for handling tricky manufacturer part numbers (numeric-only SKUs, redirects, "does not carry" language, pack-size mismatches).
- `assets/fill_worksheet.py` — Reference Python that populates a NASPO-style worksheet with Grainger pricing and flags items not carried.
