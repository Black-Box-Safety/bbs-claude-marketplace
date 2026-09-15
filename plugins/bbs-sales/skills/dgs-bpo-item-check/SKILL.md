---
name: dgs-bpo-item-check
description: Checks Grainger part numbers against the DGS BPO master item list to determine if items are approved for purchase under the active California DGS Blanket Purchase Order. Use this skill whenever Aanya asks to check, verify, look up, or cross-reference one or more Grainger part numbers against the BPO list. Trigger phrases include "is [part number] on the BPO", "check this BPO item", "is this item on the BPO list", "BPO check", "DGS BPO check", "verify BPO", "are these on the BPO", or any time a Grainger part number needs to be validated against the active BPO master list. Always use this skill — never attempt to answer from memory or guess. The skill uses a bundled lookup file covering 2025–2026 BPO pricing.
---

# DGS BPO Item Check

Checks one or more Grainger part numbers against the bundled DGS BPO master item list (covers 2025–2026 pricing) to determine which items are approved for purchase under the active California DGS Blanket Purchase Order.

## When to use

Aanya provides one or more Grainger part numbers and wants to know whether each is on the BPO list. Inputs may arrive as:
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

The script prints one line per item, in the order Aanya provided them, using this exact format:

```
Item 102WZ8: ✅ Found
Item FAKE123: ❌ Not Found
```

After running the script, return that output to Aanya as-is — do not add a summary, table, or extra commentary unless she asks. Do not reformat into a table. Do not add prices, descriptions, or other columns — Aanya only wants the found/not-found status.

## Important notes

- **The bundled list is the source of truth.** Do not search the web, do not check Grainger.com, do not guess. The skill uses the file at `assets/bpo_part_numbers.txt` which contains 19,390 unique Grainger part numbers from the active BPO.
- **Case-insensitive matching.** `102wz8`, `102WZ8`, and `102Wz8` all match the same record.
- **Coverage period.** This file covers BPO pricing for calendar years 2025 and 2026 only. Aanya will replace the bundled file in late 2026 or early 2027 when the new BPO list is published. Until then, never substitute another source.
- **Duplicates in input.** If the same item appears twice in Aanya's input, it's reported once (first occurrence wins, original casing preserved in output).

## Files in this skill

- `check_items.py` — the lookup script
- `assets/bpo_part_numbers.txt` — pre-processed lookup file (one part number per line, uppercase)
- `assets/Final_BPO_Item_List_25-26B.xlsx` — the original source spreadsheet, kept as a backup reference. Only use this file if Aanya specifically asks for description, price, vendor, or other column data — for the standard found/not-found check, always use the .txt lookup file via `check_items.py`.
