#!/usr/bin/env python3
"""
DGS BPO Item Check
Checks one or more Grainger part numbers against the bundled BPO master list.

Usage:
    python check_items.py "102WZ8"
    python check_items.py "102WZ8, 103N88, FAKE123"
    python check_items.py "102WZ8 103N88
    FAKE123"

Input parsing: splits on commas, whitespace, and newlines. Case-insensitive.
Output: first, one line naming the fiscal-year list checked against (and a
STALE warning when that fiscal year has ended); then one line per item, in the
order provided.
    Checked against: DGS BPO item list FY25-26 (Final_BPO_Item_List_25-26B.xlsx), valid 07/01/2025-06/30/2026
    Item 102WZ8: ✅ Found
    Item FAKE123: ❌ Not Found
"""

import sys
import os
import re
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOOKUP_FILE = os.path.join(SCRIPT_DIR, 'assets', 'bpo_part_numbers.txt')

# The one place that says which list is bundled. When the list is replaced,
# change these with it: the answer names the list year, and a list whose
# California fiscal year (1 July - 30 June) has ended is reported STALE on
# every run rather than passed off as current. The dates are the California
# fiscal year the file name ("25-26") denotes; the spreadsheet itself carries
# no validity dates.
BPO_LIST_FY = "FY25-26"
BPO_LIST_SOURCE = "Final_BPO_Item_List_25-26B.xlsx"
BPO_LIST_VALID_FROM = date(2025, 7, 1)
BPO_LIST_VALID_TO = date(2026, 6, 30)


def list_header(today=None):
    """The line(s) every answer starts with: which list, and whether it is stale."""
    today = today or date.today()
    lines = [f"Checked against: DGS BPO item list {BPO_LIST_FY} ({BPO_LIST_SOURCE}), "
             f"valid {BPO_LIST_VALID_FROM:%m/%d/%Y}-{BPO_LIST_VALID_TO:%m/%d/%Y}"]
    if today > BPO_LIST_VALID_TO:
        lines.append(f"⚠ STALE LIST: the {BPO_LIST_FY} list expired "
                     f"{BPO_LIST_VALID_TO:%m/%d/%Y}. The current fiscal year's list is "
                     f"not bundled yet, so a Found / Not Found below reflects "
                     f"{BPO_LIST_FY}, not the BPO in force today. Confirm against the "
                     f"current list before relying on it.")
    return lines


def load_bpo_set():
    """Load the BPO part numbers into a set for O(1) lookup."""
    if not os.path.exists(LOOKUP_FILE):
        sys.stderr.write(f"ERROR: Lookup file not found at {LOOKUP_FILE}\n")
        sys.exit(1)
    with open(LOOKUP_FILE, 'r') as f:
        return {line.strip() for line in f if line.strip()}


def parse_input(raw):
    """
    Split input on commas, whitespace, and newlines.
    Preserves order, removes duplicates while preserving first occurrence.
    Returns a list of (original_input, normalized_uppercase) tuples.
    """
    # Split on any whitespace, comma, semicolon, or newline
    tokens = re.split(r'[,;\s]+', raw.strip())
    tokens = [t.strip() for t in tokens if t.strip()]

    seen = set()
    result = []
    for t in tokens:
        norm = t.upper()
        if norm not in seen:
            seen.add(norm)
            result.append((t, norm))
    return result


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python check_items.py \"<item1>, <item2>, ...\"\n")
        sys.exit(1)

    raw_input_str = ' '.join(sys.argv[1:])
    items = parse_input(raw_input_str)

    if not items:
        sys.stderr.write("No item numbers provided.\n")
        sys.exit(1)

    bpo_set = load_bpo_set()

    for line in list_header():
        print(line)

    for original, normalized in items:
        if normalized in bpo_set:
            print(f"Item {original}: ✅ Found")
        else:
            print(f"Item {original}: ❌ Not Found")


if __name__ == '__main__':
    main()
