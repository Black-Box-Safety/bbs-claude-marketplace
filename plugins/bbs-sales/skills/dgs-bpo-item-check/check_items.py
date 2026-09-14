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
Output: one line per item, in the order provided.
    Item 102WZ8: ✅ Found
    Item FAKE123: ❌ Not Found
"""

import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOOKUP_FILE = os.path.join(SCRIPT_DIR, 'assets', 'bpo_part_numbers.txt')


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

    for original, normalized in items:
        if normalized in bpo_set:
            print(f"Item {original}: ✅ Found")
        else:
            print(f"Item {original}: ❌ Not Found")


if __name__ == '__main__':
    main()
