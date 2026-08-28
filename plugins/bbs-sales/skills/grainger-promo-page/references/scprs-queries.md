# SCPRS segment queries

Run these with the `explore_sql` tool against the SCPRS warehouse. They turn an
agency name into three named, sized, sendable lists.

Substitute `<BUSINESS_UNIT>` (the agency's SCPRS code, e.g. `3540` for CAL FIRE),
`<SUPPLIER>` (the prime whose spend you are displacing, e.g. `WW GRAINGER INC`),
and `<START_DATE>`. The Segment A query below reproduces the CAL FIRE H2 2026
numbers exactly, so if you point it at a new agency and it returns something
implausible, the query is not the suspect.

## The rule that outranks the queries

The warehouse holds **two deliberate slices** of SCPRS and is not all California
procurement:

- `sb_dvbe_visible`: non-IT goods bought through SB/DVBE and related
  certified-supplier programs. This is what `silver_line_items` and every gold
  mart are scoped to.
- `mro_prime_direct`: the SCPRS spend of the NASPO MRO LPA primes,
  supplier-filtered. Reachable only through `silver_line_items_all_slices`.

**Every total, share, and "X% of spend" you report is of one slice. Say which one,
every time, in the README table and on the page if the number appears there.**
Never call a warehouse total "the market", "the agency's budget", or "state
procurement". `silver_line_items_all_slices` mixes both slices by construction, so
any query touching it either filters `corpus_slice` or labels which slices each
number covers. Segments A and B come from different slices and their spend figures
therefore cannot be added together.

Two more standing facts about this data:

- Spend is gross of credits. Returns and adjustments are excluded from Silver, not
  netted out. A large single-buyer figure is worth eyeballing before it goes in an
  email.
- **`buyer_email` is not queryable.** The connector refuses any query that reads
  it, however it is aliased or wrapped (ruling D13, 2026-08-17). `buyer_name` is
  available, and buyers are real state employees: use names at **relationship
  grain**, meaning "this person's department bought this from that supplier", to
  be useful to them. Never build a profile of a person. Contact routing happens
  through Business Central and the rep, not here.

## 1. Find the agency's business unit

Business unit is a code, not a name, and the display name varies by fiscal year.
Look it up rather than guessing.

```sql
SELECT business_unit,
       COUNT(*)                    AS lines,
       ROUND(SUM(line_total), 2)   AS spend,
       MIN(po_start_date)          AS first_po,
       MAX(po_start_date)          AS last_po
FROM   silver_line_items_all_slices
WHERE  business_unit LIKE '<PREFIX>%'
GROUP  BY business_unit
ORDER  BY spend DESC
```

If you only have a name, find the code through the descriptions the agency's own
buyers wrote:

```sql
SELECT DISTINCT business_unit
FROM   silver_line_items_all_slices
WHERE  item_description ILIKE '%<AGENCY KEYWORD>%'
LIMIT  50
```

Confirm the code against a known supplier relationship before you build on it. A
wrong business unit produces a campaign sized for the wrong department, and every
number downstream will look reasonable.

## 2. Rank the prime-direct suppliers

This is the "who are we actually displacing" query and it decides which prime's
sheet is worth building a page around.

```sql
SELECT supplier_name,
       ROUND(SUM(line_total), 2)        AS spend,
       COUNT(DISTINCT buyer_name)       AS buyers,
       COUNT(DISTINCT po_number)        AS pos,
       MAX(po_start_date)               AS last_po
FROM   silver_line_items_all_slices
WHERE  business_unit  = '<BUSINESS_UNIT>'
  AND  corpus_slice   = 'mro_prime_direct'
  AND  fiscal_year IN ('FY2023-2024', 'FY2024-2025', 'FY2025-2026')
GROUP  BY supplier_name
ORDER  BY spend DESC
```

Label the result "MRO-prime direct slice, FY<x> to FY<y>". On CAL FIRE this
returned `WW GRAINGER INC` at $9.71M across 489 buyer names, with the next prime an
order of magnitude down. That concentration is what makes a single-prime hot list
worth a landing page.

## 3. Segment A: buys the prime direct, no BBS history

The wedge: same items, same price, and now the spend reports.

```sql
WITH bbs AS (
    SELECT DISTINCT buyer_name
    FROM   silver_line_items_all_slices
    WHERE  business_unit = '<BUSINESS_UNIT>'
      AND  supplier_name ILIKE '%BLACK BOX SAFETY%'
)
SELECT COUNT(DISTINCT s.buyer_name)   AS buyers,
       ROUND(SUM(s.line_total), 2)    AS spend
FROM   silver_line_items_all_slices s
WHERE  s.business_unit = '<BUSINESS_UNIT>'
  AND  s.corpus_slice  = 'mro_prime_direct'
  AND  s.supplier_name = '<SUPPLIER>'
  AND  s.po_start_date >= DATE '<START_DATE>'
  AND  s.buyer_name NOT IN (SELECT buyer_name FROM bbs)
```

Swap the aggregate for the roster when you need the list itself:

```sql
SELECT s.buyer_name,
       ROUND(SUM(s.line_total), 2)  AS spend,
       COUNT(DISTINCT s.po_number)  AS pos,
       MAX(s.po_start_date)         AS last_po
FROM   silver_line_items_all_slices s
WHERE  ... same predicates ...
GROUP  BY s.buyer_name
ORDER  BY spend DESC
```

The `bbs` CTE deliberately has no slice filter: any BBS purchase in any slice
means the buyer is not a cold prime-direct buyer, and putting a slice filter there
would leak warm relationships into the cold segment.

## 4. Segment B: buys the categories from other suppliers, no BBS history

The wedge: these categories have already been competed, so there is no
solicitation to run.

```sql
WITH bbs AS (
    SELECT DISTINCT buyer_name
    FROM   silver_line_items_all_slices
    WHERE  business_unit = '<BUSINESS_UNIT>'
      AND  supplier_name ILIKE '%BLACK BOX SAFETY%'
)
SELECT COUNT(DISTINCT buyer_name)  AS buyers,
       ROUND(SUM(line_total), 2)   AS spend
FROM   silver_line_items_all_slices
WHERE  business_unit  = '<BUSINESS_UNIT>'
  AND  corpus_slice   = 'sb_dvbe_visible'
  AND  po_start_date >= DATE '<START_DATE>'
  AND  supplier_name NOT ILIKE '%BLACK BOX SAFETY%'
  AND  ( <CATEGORY_PREDICATE> )
  AND  buyer_name NOT IN (SELECT buyer_name FROM bbs)
```

`<CATEGORY_PREDICATE>` is the tuning knob of this whole exercise and it must be
written down beside the number it produced. Two forms work:

**UNSPSC family prefixes**, coarse and reproducible:

```sql
LEFT(unspsc_code, 2) IN ('46', '47', '26', '24', '12', '52')
-- 46 safety and security, 47 cleaning equipment and supplies,
-- 26 power generation including batteries, 24 packaging and containers,
-- 12 chemicals, 52 domestic appliances and camp supplies
```

**Description keywords**, narrower and closer to the actual hot list:

```sql
item_description ILIKE '%shelter%' OR item_description ILIKE '%mcleod%'
OR item_description ILIKE '%pulaski%' OR item_description ILIKE '%helmet%'
OR item_description ILIKE '%glove%'   OR item_description ILIKE '%goggle%'
OR item_description ILIKE '%batter%'  OR item_description ILIKE '%toilet paper%'
OR item_description ILIKE '%paper towel%' OR item_description ILIKE '%detergent%'
OR item_description ILIKE '%cleaner%' OR item_description ILIKE '%trash bag%'
OR item_description ILIKE '%disinfect%'
```

The two give materially different totals on the same agency, which is the point:
the segment size is a function of how you defined "these categories". Paste the
predicate you used into the README beside the number. A segment size with no
predicate recorded is not reproducible and should not be repeated in a meeting.

## 5. Segment C: has BBS history, now buying elsewhere

The wedge: warm, individual, and it references a real relationship. This segment
is usually single digits and it is the most valuable list in the campaign.

```sql
WITH bbs AS (
    SELECT buyer_name,
           MAX(po_start_date)          AS last_bbs_po,
           ROUND(SUM(line_total), 2)   AS bbs_spend
    FROM   silver_line_items_all_slices
    WHERE  business_unit = '<BUSINESS_UNIT>'
      AND  supplier_name ILIKE '%BLACK BOX SAFETY%'
    GROUP  BY buyer_name
)
SELECT s.buyer_name,
       ROUND(SUM(s.line_total), 2)          AS spend_elsewhere,
       COUNT(DISTINCT s.supplier_name)      AS other_suppliers,
       MAX(s.po_start_date)                 AS last_po_elsewhere,
       b.last_bbs_po,
       b.bbs_spend
FROM   silver_line_items_all_slices s
JOIN   bbs b ON b.buyer_name = s.buyer_name
WHERE  s.business_unit  = '<BUSINESS_UNIT>'
  AND  s.corpus_slice   = 'sb_dvbe_visible'
  AND  s.po_start_date >= DATE '<START_DATE>'
  AND  s.supplier_name NOT ILIKE '%BLACK BOX SAFETY%'
  AND  ( <CATEGORY_PREDICATE> )
GROUP  BY s.buyer_name, b.last_bbs_po, b.bbs_spend
ORDER  BY spend_elsewhere DESC
```

`last_bbs_po` against `last_po_elsewhere` is the line the rep actually uses: it
says how long the relationship has been dormant and what has been going elsewhere
since. Use it at relationship grain in an email a human sends. Do not put a named
buyer's spend on a web page.

## 6. Size the hot list against the agency's real spend

This is the check that stops a campaign being built on the wrong story. Map each
hot-list category onto what the agency actually buys, and rank by their spend
rather than by what looks impressive on the sheet.

```sql
SELECT CASE
         WHEN item_description ILIKE '%shelter%'
           OR item_description ILIKE '%pulaski%'
           OR item_description ILIKE '%mcleod%'      THEN 'FIRE TOOLS'
         WHEN item_description ILIKE '%helmet%'
           OR item_description ILIKE '%glove%'
           OR item_description ILIKE '%goggle%'
           OR item_description ILIKE '%hood%'        THEN 'PPE'
         WHEN item_description ILIKE '%batter%'      THEN 'BATTERIES'
         WHEN item_description ILIKE '%toilet paper%'
           OR item_description ILIKE '%paper towel%'
           OR item_description ILIKE '%detergent%'
           OR item_description ILIKE '%cleaner%'     THEN 'JAN/SAN'
         WHEN item_description ILIKE '%car wash%'
           OR item_description ILIKE '%wax%'         THEN 'FLEET'
         ELSE 'OTHER'
       END                              AS category,
       ROUND(SUM(line_total), 2)        AS spend,
       COUNT(DISTINCT buyer_name)       AS buyers,
       COUNT(DISTINCT po_number)        AS pos
FROM   silver_line_items_all_slices
WHERE  business_unit = '<BUSINESS_UNIT>'
  AND  corpus_slice  = '<SLICE>'
  AND  fiscal_year IN ('FY2024-2025', 'FY2025-2026')
GROUP  BY category
ORDER  BY spend DESC
```

Two uses for the output. It orders the hero product cards by what the agency
actually reorders most, which is a better page than one ordered by price. And it
tells you where the discount story really is: on CAL FIRE the deep discounts sat
in janitorial and fleet consumables, not the signature wildland gear, so a
campaign headlined "deep discounts on fire gear" would have died on contact with a
buyer who knew the prices.

A ranking derived this way is a claim about the agency once it appears on a page.
State the SCPRS attribution on the piece and check whether it needs a registry
row.
