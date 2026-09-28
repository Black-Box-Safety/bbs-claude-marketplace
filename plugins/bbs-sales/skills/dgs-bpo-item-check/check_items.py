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

import hashlib
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
# Fingerprints that tie the bundle together: the source spreadsheet's bytes,
# and the lookup file's part-number SET (sorted, stripped, newline-joined), so a
# Windows CRLF checkout of the .txt still matches. A lookup file regenerated
# from another list, or a spreadsheet swapped without its lookup file, fails.
BPO_LIST_SOURCE_SHA256 = "a1f14cfee87bb3f021b20b06eb6f338464f47c7a4b545b5600d966f45e2bdb6a"
BPO_LOOKUP_SET_SHA256 = "0a27360e172f4bc5bed6981a8e45fc2e9e69a563edbc800c858ebdb8c2161442"
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def _lookup_set_sha256(path):
    with open(path, 'r', encoding='utf-8') as fh:
        parts = sorted({line.strip() for line in fh if line.strip()})
    return hashlib.sha256('\n'.join(parts).encode('utf-8')).hexdigest()


def constants_problem():
    """Why the BPO_LIST_* constants cannot be trusted, or None.

    The constants are typed by hand when the list is replaced, so they are
    checked against the bundled files rather than believed: the source
    spreadsheet they name must be in assets/, its name must carry the FY token
    ("25-26" for "FY25-26"), and the validity dates must be that token's
    California fiscal year. A list swapped without its constants -- or the
    reverse -- stops the run instead of answering under the wrong year.
    """
    m = re.fullmatch(r'FY(\d{2})-(\d{2})', BPO_LIST_FY)
    if not m:
        return f"BPO_LIST_FY {BPO_LIST_FY!r} is not of the form FYyy-yy"
    token = f"{m.group(1)}-{m.group(2)}"
    if int(m.group(2)) != (int(m.group(1)) + 1) % 100:
        return f"BPO_LIST_FY {BPO_LIST_FY} is not two consecutive years"
    if not os.path.isfile(os.path.join(ASSETS_DIR, BPO_LIST_SOURCE)):
        return f"the source file {BPO_LIST_SOURCE} named by BPO_LIST_SOURCE is not in assets/"
    if token not in BPO_LIST_SOURCE:
        return (f"BPO_LIST_SOURCE {BPO_LIST_SOURCE} does not carry the fiscal-year token "
                f"{token} from BPO_LIST_FY")
    if (BPO_LIST_VALID_FROM != date(2000 + int(m.group(1)), 7, 1)
            or BPO_LIST_VALID_TO != date(2000 + int(m.group(2)), 6, 30)):
        return (f"BPO_LIST_VALID_FROM/TO {BPO_LIST_VALID_FROM}-{BPO_LIST_VALID_TO} are not "
                f"the California fiscal year {BPO_LIST_FY}")
    if _sha256_file(os.path.join(ASSETS_DIR, BPO_LIST_SOURCE)) != BPO_LIST_SOURCE_SHA256:
        return f"{BPO_LIST_SOURCE} does not match BPO_LIST_SOURCE_SHA256"
    if not os.path.isfile(LOOKUP_FILE) or _lookup_set_sha256(LOOKUP_FILE) != BPO_LOOKUP_SET_SHA256:
        return ("assets/bpo_part_numbers.txt does not match BPO_LOOKUP_SET_SHA256 -- it was not "
                f"generated from {BPO_LIST_SOURCE}, or was edited")
    return None


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

    problem = constants_problem()
    if problem:
        sys.stderr.write(f"ERROR: the bundled BPO list and check_items.py disagree: {problem}. "
                         f"Replace the asset files and the BPO_LIST_* constants together; "
                         f"no answer given.\n")
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
