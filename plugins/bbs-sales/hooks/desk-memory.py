#!/usr/bin/env python3
"""SessionStart: put what reps asked Claude to remember for this folder in front of Claude.

Reads LEARNED.md in the session's folder and in each folder above it, up to the quote-desk
tree folder, nearest first. It walks up and never sideways, so a session in one buyer's folder
is never handed another buyer's or another agency's lines. A session opened one level above the
tree (the desk root the workspace opens) gets the desk-wide file only.

Only lines in the entry format are shown; anything else in the file is counted and skipped, so
pasted text never reaches context through this hook. The entry format is written by the
desk-remember skill's scripts/desk_memory.py. Change the format in both, and in desk-memory.ps1.

The Python half of desk-memory.ps1: same output on every input, proven by
hooks/tests/desk_memory_parity.py. Change both or neither (invariant 3).

Plain stdout is added to context. Silent when nothing is found. Always exits 0, never writes to
stderr. Stdlib only.
"""
import json
import os
import re
import sys

TREE = "All RFQ's by Agency"
FILE = "LEARNED.md"
PER_LEVEL = 12
MAX_UP = 8
ENTRY = re.compile(
    r"^- ([0-9]{4}-[0-9]{2}-[0-9]{2}) \| ([^|]{1,60}) \| (preference|change|watch-out) \| ([^|]{1,300})"
    r"( \| wider: [^|]{1,120})?$")
HEAD = ("DESK MEMORY -- what BBS reps asked Claude to remember, nearest folder first. Each line is one "
        "person's dated statement, not a system of record: take no price, stock, lead time, account "
        "number, certification or contract fact from it.")


def split_lines(text):
    parts = re.split(r"\r\n|\n|\r", text)
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def read_lines(path):
    with open(path, "rb") as fh:
        return split_lines(fh.read().decode("utf-8-sig", "replace"))


def level_block(path, label):
    """Lines to print for one LEARNED.md, or [] when it holds no entry."""
    try:
        lines = read_lines(path)
    except OSError:
        return []
    ents = []
    skipped = 0
    for i, l in enumerate(lines):
        if ENTRY.match(l):
            # Newest first; on the same date the line added later comes first.
            ents.append((int(l[2:12].replace("-", "")) * 100000 + i, l))
        elif l.startswith("- "):
            skipped += 1
    if not ents and not skipped:
        return []
    ents.sort(key=lambda e: e[0], reverse=True)
    out = [f"{label} -- {path}:"]
    out.extend(e[1] for e in ents[:PER_LEVEL])
    if len(ents) > PER_LEVEL:
        out.append(f"(+{len(ents) - PER_LEVEL} older not shown)")
    if skipped:
        out.append(f"({skipped} lines skipped: not in the entry format)")
    return out


# Path handling is done on the string, the same way in both halves: "/" and "\\" both separate.
def strip_seps(d):
    while len(d) > 1 and d[-1] in "/\\":
        d = d[:-1]
    return d


def last_sep(d):
    return max(d.rfind("/"), d.rfind("\\"))


def base(d):
    return d[last_sep(d) + 1:]


def collect(cwd):
    d = strip_seps(cwd)
    tree = TREE.lower()
    # One level above the tree (the desk root the workspace opens): the desk-wide file only.
    if tree not in d.lower():
        below = d + os.sep + TREE
        if os.path.isdir(below):
            return level_block(below + os.sep + FILE, "DESK-WIDE")
        return []
    blocks = []
    reached = False
    for n in range(MAX_UP):
        is_tree = base(d).lower() == tree
        label = "DESK-WIDE" if is_tree else ("THIS FOLDER" if n == 0 else f"{n} UP")
        f = d + os.sep + FILE
        if os.path.isfile(f):
            blocks.append(level_block(f, label))
        if is_tree:
            reached = True
            break
        i = last_sep(d)
        if i <= 0:
            break
        d = d[:i]
    if not reached:
        return []           # could not place the folder under the tree: show nothing
    out = []
    for b in blocks:
        out.extend(b)
    return out


def main():
    raw = sys.stdin.buffer.read().decode("utf-8-sig", "replace")
    if not raw.strip():
        return
    try:
        h = json.loads(raw)
    except ValueError:
        return
    if not isinstance(h, dict):
        return
    d = h.get("cwd")
    if not isinstance(d, str) or not d or not os.path.isdir(d):
        return
    out = collect(d)
    if out:
        sys.stdout.flush()
        sys.stdout.buffer.write(("\n".join([HEAD] + out) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 -- fail open, silently
        pass
    sys.exit(0)
