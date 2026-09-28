---
name: vendor-quote-email
description: >
  Generates a vendor pricing quote request email for a Black Box Safety, Inc.
  sales rep. Use this skill whenever the user asks to draft a vendor quote
  email, pricing request, or wants to email a vendor/supplier for pricing.
  Trigger phrases include: "draft a quote email", "vendor quote", "pricing
  request email", "email a vendor for pricing", "quote request", "create a
  quote email", or any request to contact a vendor/supplier for item pricing
  on behalf of a customer agency. Always render the interactive form widget
  — never draft this email as free-form text without showing the form first.
requires: []
---

# Vendor Quote Email

Produces a professional vendor pricing quote request email for Black Box Safety,
Inc., sent by a BBS sales rep to a vendor/supplier on behalf of a California
state agency.

## When triggered

Always render the interactive HTML widget. The widget handles all input,
subject line preview, line item management, and generates two copy options:
plain text and Outlook-optimized HTML (formatted table, clickable links).

## Form sections

### Section 1 — Subject line
| Field | Example |
|---|---|
| Item type | Button Pullover & Pants |
| Customer agency | CPUC |
| Vendor | Bocomal |

Formula: `Pricing Quote Request - [Item Type] - [Customer Agency] - [Vendor]`

### Section 2 — Email details
| Field | Notes |
|---|---|
| Rep first name | Used in the email body greeting (e.g. "My name is [first name]") |
| Rep full name | Used in the email signature |
| Agency name | Used in the email body paragraph |
| Ship to address | Multi-line, free text |

The Rep first name and Rep full name fields persist in storage
(`bbs_quote_rep_first_name`, `bbs_quote_rep_full_name`) so they auto-fill
on subsequent uses — each rep enters their name once, then never again
on that device.

### Section 3 — Line items (min 1, no max)
- Line # (optional)
- SKU / Model / Item #
- QTY (plain text field — no spinner arrows)
- Description
- Reference link (renders as "Click Here" hyperlink in Outlook output)

Customer Agency, Vendor, and Agency Name fields use searchable autocomplete
dropdowns backed by persistent storage (bbs_quote_agencies / bbs_quote_vendors).
Values are saved on each generation so the lists grow over time.

## Email template

```
Good [morning/afternoon],   <- PDT timezone: before 12:00 = morning, else afternoon

I hope this email finds you well! My name is [Rep first name] and I work with
Black Box Safety, Inc. (a distributor for the State of California Government).
We have been working with [Agency Name] on a project for a few items and were
hoping to get a quote from you. The parts and quantities would be as follows:

[Table: SKU / Model # | QTY | Description | Reference Link]

Items would ship to:
[Ship to Address]

If needed, our Bill to Address is:
1950 Cordell Ct. Suite 103
El Cajon, CA 92020

Please include any shipping/freight cost estimation in the quote and let me know if
you need any additional information. I look forward to hearing from you soon! Thank
you and have a beautiful day!

Sincerely,
[Rep full name]
```

## Output

1. **Subject line** — copyable text field
2. **Email body** — two copy buttons:
   - "Copy as plain text" — plain text fallback
   - "Copy for Outlook" — rich HTML clipboard copy (ClipboardItem text/html)
     Outlook-safe: border HTML attributes, bgcolor on header row, Arial font,
     fully expanded inline border styles, no shorthand CSS.

## Greeting logic
- Timezone: America/Los_Angeles
- Hour < 12 -> "Good morning,"
- Hour >= 12 -> "Good afternoon,"

## Persistent storage keys
- bbs_quote_rep_first_name — saved rep first name (shared: false)
- bbs_quote_rep_full_name  — saved rep full name (shared: false)
- bbs_quote_agencies — saved agency names (shared: false)
- bbs_quote_vendors  — saved vendor names (shared: false)
