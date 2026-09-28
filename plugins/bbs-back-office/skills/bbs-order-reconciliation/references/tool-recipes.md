# Tool recipes

Concrete lookups for reconciling an existing order, with the failure modes that waste the
most time.

## Contents

- [Business Central](#business-central)
- [Grainger](#grainger)
- [Outlook](#outlook)
- [OCR and spreadsheets](#ocr-and-spreadsheets)

---

## Business Central

Read-only. Company is "Black Box Safety", production.

### Picking the right call

| Question | Call |
|---|---|
| "What happened on SO-10012739 / INVP-10007601?" | `bc_get_sales_document` — type is auto-detected, returns header + all lines |
| "Where do we stand with this institution?" | `bc_customer_snapshot` — orders, quotes, unpaid invoices, recent invoices in one call |
| "What is still not shipped?" | `bc_list_open_sales_orders` |
| "What do they owe us?" | `bc_list_unpaid_invoices` |
| "Do we stock this / what is our cost?" | `bc_find_item` — returns unitPrice, unitCost, on-hand |
| Anything else | `bc_list_entity_sets` → `bc_describe_entity` → `bc_query_entity` |

### Gotchas that cost time

- **Text search is case-sensitive.** `contains(displayName,'california')` returns nothing;
  `'California'` works. This bites constantly on institution names.
- **"Open" means not fully shipped**, not draft. Filter `fullyShipped eq false`. The
  `status` field only holds Draft or Open and says nothing about shipment.
- **`remainingAmount` is not filterable.** Filter on `status` or `dueDate` and read
  `remainingAmount` from the results.
- **Sales order lines cannot be queried on their own.** They come back only via expand on
  the document, which `bc_get_sales_document` already does.
- Resolve a customer name to a **customer number** with `bc_find_customer` first, then pass
  the number to everything else.

### What to compare against the PO

Pull the BC line and set it beside the PO line:

- Item number — does it match the cross-reference we intended?
- Quantity and **UOM** — a BC line in EA against a PO line in PAC is the error, visible
- Unit price — divergence here means it changed at order entry, not at bid
- Shipment status and dates — tells you whether a fix is still cheap

Watch for **duplicate sales orders**. The ProCo integration has created them. A doubled
line reads as an overshipment to the customer and as a shortage in our numbers.

---

## Grainger

### Pricing is per-account — this is the main trap

The discount is set by pricing schedule and can be overridden per account. Pricing against
the wrong account returns a number that is wrong but looks completely valid.

```
grainger_price(productCodes=["575D15"], account="Correctional Training Facility")
```

Account accepts a number or a facility name. Abbreviations usually fail — `CTF` returns an
error, `Correctional Training Facility` resolves. When it fails, the error lists valid
examples; the institution's full name is the reliable form.

**BBS sells at cost on these accounts.** `unitPrice` is both our cost and the customer
price — never mark it up. Confirm with `account.sellRule` (`at_cost` on every schedule
today).

### Verifying a cross-reference

Given a manufacturer part number from the customer's description, search by it rather than
trusting a stored SKU:

```
grainger_search(query="34-874", account="Correctional Training Facility")
```

Then check all four of these against the customer's line, because a bad cross-reference
often fails on several at once:

- `mfrPartNumber` — matches the customer's manufacturer PN
- `brand` — same maker
- size, in `description` or the `Size- Alpha` spec
- `uom` and `uomQty` — `PK` with `uomQty: 12` is a pack of twelve; `PR` with `uomQty: 1`
  is a single pair

A stored SKU that comes back as a different brand, a different size, and a single pair
when the customer ordered a twelve-pack is not a pricing problem — it is a wrong item.

`status` also matters. "Discontinued" reported by a rep is frequently a broken
cross-reference: the wrong item is dead, the correct one shows "Typically in Stock".

### Availability

```
grainger_availability(items=[{"code":"575D15","qty":16}], postalCode="93960", account="...")
```

Use the ship-to ZIP, and use it before promising a date on a replacement.

---

## Outlook

Read-only in this setup — searching and reading works, creating drafts does not. If a
draft is needed, the connector requires `Mail.ReadWrite`, which an administrator grants.

### Search patterns, in useful order

```
outlook_email_search(query="4500755180", limit=25)                    # by PO
outlook_email_search(query="34-874", limit=25)                        # by item
outlook_email_search(sender="berenice", afterDateTime="2026-08-25",
                     order="newest", limit=25)                        # by person + recency
outlook_email_search(query="amended purchase order", limit=25)        # by symptom
```

Constraints worth knowing before a search returns nothing useful:

- 25 results maximum per call; page with `nextOffset`.
- `order` is **not** compatible with a free-text `query` — combine `order` with
  sender/date/folder filters instead.
- `order` without a `folderName` scopes to Inbox. Pass `folderName: "Sent Items"` to sort
  within sent mail.
- `recipient` is not compatible with `folderName`, `mailboxOwnerEmail`, or `order`.
- Free-text search in a folder or shared mailbox pages by `cursor`, not `offset`.

### Reading a long thread

`read_resource` with the message URI returns the full body. Long HTML emails exceed the
return limit and get saved to a file instead. Strip the markup and seek to the part you
need rather than reading the whole thing:

```bash
python -c "
import re
t = open('<saved-file>').read()
t = re.sub(r'<[^>]+>', ' ', t)
t = re.sub(r'&nbsp;|&#160;', ' ', t)
t = re.sub(r'&amp;', '&', t)
t = re.sub(r'\s+', ' ', t)
i = t.find('<a phrase you expect to appear>')
print(t[max(0,i-2500):i+3000])
"
```

Quoted reply chains run newest-first, so the original request sits at the **bottom** of the
stripped text. The sentence that resolves the question is usually four levels down in a
forward, not in the top message.

### What to extract

- Who said what, with the date — you will need to cite it
- Approvals, and the **role** of whoever gave them
- Commitments made to the customer
- Unanswered questions from us to them
- Free-of-charge replacements already sent

---

## OCR and spreadsheets

### PO text

```bash
grep -n -B8 -A8 "34-874" "DRP PO's/_ocr/CTF_combined.txt"
```

Generous context is necessary — OCR splits a line item across many short lines and the
quantity often lands above the unit.

Header fields across every PO in a project at once:

```bash
for f in CTF FSP SOL SQ VSP; do
  echo "=== $f ==="
  head -60 "DRP PO's/_ocr/${f}_combined.txt" | grep -i -E "CONTACT NAME|cdcr.ca.gov|AUTHORIZING NAME|Attn"
done
```

### Finding an item everywhere in a project

The highest-yield command in the workflow. Run from the project root:

```bash
python - <<'EOF'
import openpyxl, os
TARGET = "34-874"
for root, dirs, files in os.walk('.'):
    if '/.' in root: continue
    for f in files:
        if not f.endswith('.xlsx') or f.startswith('~'): continue
        p = os.path.join(root, f)
        try: wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
        except Exception: continue
        for ws in wb:
            for r in ws.iter_rows(values_only=True):
                s = ' | '.join(str(x) for x in r if x is not None)
                if TARGET in s:
                    print(f"{p} :: {ws.title} :: {s[:220]}")
EOF
```

Read the output by column alignment. The same dollar figure appearing under two different
quantity denominators — 360 each in one tab, 30 packs in another — is the signature of a
unit-of-measure error.

### Dumping specific tabs

```bash
python - <<'EOF'
import openpyxl
wb = openpyxl.load_workbook('1. Processing Sheets/CTF_PO_4500755180_Order_Sheet.xlsx',
                            data_only=True)
for name in ['Dashboard', 'Open Items', 'Quote vs PO Validation']:
    if name not in wb.sheetnames: continue
    ws = wb[name]
    print(f"--- {name} ({ws.max_row} rows)")
    for r in ws.iter_rows(values_only=True):
        s = ' | '.join(str(x) for x in r if x is not None).strip()
        if s: print('   ', s[:240])
EOF
```

Large dumps exceed the output limit and get written to a file. Narrow to the tabs you
need, or grep the saved file rather than re-running.
