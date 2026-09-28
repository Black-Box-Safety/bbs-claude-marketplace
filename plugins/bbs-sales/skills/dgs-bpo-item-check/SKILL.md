---
name: dgs-bpo-item-check
description: >-
  Determine whether Grainger part numbers are on California's DGS Blanket Purchase Order item
  list by looking each one up in the bundled BPO master list, which names its fiscal year and
  warns when that year has ended. Use whenever a rep asks to check, verify, confirm, or cross-reference
  Grainger part numbers against the BPO, the DGS blanket purchase order, or the BPO list — "is
  this on the BPO", "BPO check", "are these approved". Answers on-list or off-list from the
  bundled file only; never from memory and never a guess. Do NOT use to obtain a price (use
  grainger-pricing) or to extract item numbers from a PDF, cart or screenshot. If a rep says
  only "check these Grainger items" without making clear whether they mean BPO eligibility or
  price, ask which before running.
requires: [python3]
---

# DGS BPO Item Check

Checks one or more Grainger part numbers against the bundled DGS BPO master item list (the California FY25–26 list — see *Coverage period*) to determine which items are on that list. Every answer names the list's fiscal year and says STALE once it has ended.

## When to use

the rep provides one or more Grainger part numbers and wants to know whether each is on the BPO list. Inputs may arrive as:
- A single item: `102WZ8`
- A comma-separated list: `102WZ8, 103N88, 10A236`
- A space- or newline-separated list pasted from another doc
- Mixed case (`102wz8`, `102Wz8` — all treated the same)

## How to use

Run the bundled script with the item number(s) as a single quoted argument.
`SKILL_DIR` is the folder holding this SKILL.md — wherever the plugin was
installed, not the directory you happen to be standing in:

```bash
python "$SKILL_DIR/check_items.py" "<item numbers>"
```

The script finds its own lookup file relative to itself, so it works from any
working directory.

The script handles parsing — it splits on commas, whitespace, semicolons, and newlines, deduplicates, and normalizes to uppercase. You don't need to clean the input first.

### Examples

**Single item:**
```bash
python "$SKILL_DIR/check_items.py" "102WZ8"
```

**Multiple items (comma-separated):**
```bash
python "$SKILL_DIR/check_items.py" "102WZ8, 103N88, FAKE123"
```

**Multiple items (newline-pasted from another source):**
```bash
python "$SKILL_DIR/check_items.py" "102WZ8
103N88
10A236"
```

## Output format

The script first names the list it checked against, then prints one line per item, in the
order the rep provided them, using this exact format:

```
Checked against: DGS BPO item list FY25-26 (Final_BPO_Item_List_25-26B.xlsx), valid 07/01/2025-06/30/2026
⚠ STALE LIST: the FY25-26 list expired 06/30/2026. ...
Item 102WZ8: ✅ Found
Item FAKE123: ❌ Not Found
```

The `Checked against` line is on every answer, so the rep always knows which fiscal
year's list the answer came from. The `⚠ STALE LIST` line appears whenever that fiscal
year has ended; never drop it or soften it.

After running the script, return that output to the rep as-is — do not add a summary, table, or extra commentary unless the rep asks. Do not reformat into a table. Do not add prices, descriptions, or other columns — the rep only wants the found/not-found status.

## Important notes

- **The bundled list is the source of truth.** Do not search the web, do not check Grainger.com, do not guess. The skill uses the file at `assets/bpo_part_numbers.txt` which contains 19,390 unique Grainger part numbers from the FY25–26 BPO list.
- **Case-insensitive matching.** `102wz8`, `102WZ8`, and `102Wz8` all match the same record.
- **Coverage period.** The bundled list is the California **FY25–26** list (1 July 2025 – 30 June 2026), not calendar 2025–2026. FY26–27 began 1 July 2026; its list is blocked on Aanya providing it (Parker, 2026-09-28: "Aanya will provide"). Until it is bundled this skill keeps checking FY25–26 and says so as STALE on every answer. Never substitute another source and never synthesize a list. When the new list lands, replace both asset files and the `BPO_LIST_*` constants (including the two fingerprints) at the top of `check_items.py` together — the script refuses to answer (exit 1) if the named source file is missing, its name lacks the FY token, the years are not consecutive, the dates are not that fiscal year, or either file does not match its fingerprint.
- **Duplicates in input.** If the same item appears twice in the rep's input, it's reported once (first occurrence wins, original casing preserved in output).

## Files in this skill

- `check_items.py` — the lookup script
- `assets/bpo_part_numbers.txt` — pre-processed lookup file (one part number per line, uppercase)
- `assets/Final_BPO_Item_List_25-26B.xlsx` — the original source spreadsheet, kept as a backup reference. Only use this file if the rep specifically asks for description, price, vendor, or other column data — for the standard found/not-found check, always use the .txt lookup file via `check_items.py`.
