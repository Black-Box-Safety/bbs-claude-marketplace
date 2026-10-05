#!/usr/bin/env python3
"""SessionStart: when a session opens inside a buyer folder (or a few levels below one),
put that buyer's recent precedent and open flags in front of Claude before the first prompt.

The Python half of desk-context.ps1: same output on every input, proven by
hooks/tests/parity.py. Change both or neither (invariant 3).

Plain stdout is added to context. Silent when nothing relevant is found. Stdlib only.
"""
import json
import os
import re
import sys

TREE = "All RFQ's by Agency"


def read_lines(path):
    # Get-Content: lines without their newlines, no trailing empty line for a final newline.
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read().splitlines()


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return 0
    try:
        h = json.loads(raw)
    except ValueError:
        return 0
    if not isinstance(h, dict):
        return 0
    d = str(h.get("cwd") or "")
    if not d or not os.path.exists(d):
        return 0

    # Quote-desk tree only. A session anywhere else on the machine gets nothing injected, even
    # if some unrelated folder happens to hold a quote-log.md.
    if TREE.lower() not in d.lower():
        return 0

    out = []
    for _ in range(5):
        if not d:
            break
        ql = os.path.join(d, "quote-log.md")
        fl = os.path.join(d, "FLAGS.md")
        if os.path.exists(ql):
            out.append(f"PRECEDENT -- {ql} (most recent rows; cite these before pricing):")
            out.extend(read_lines(ql)[-12:])
        if os.path.exists(fl):
            rows = [l for l in read_lines(fl) if re.match(r"^\|\s*\d{4}-\d{2}-\d{2}", l)][-5:]
            if rows:
                out.append(f"OPEN FLAGS -- {fl} (latest; do not repeat these mistakes):")
                out.extend(rows)
        if out:
            break
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent

    if out:
        sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
