#!/usr/bin/env python3
"""Remind a session working in a customer folder to keep that customer's CLAUDE.md —
the python3 twin of customer-folder.ps1.

Same events, same output bytes (tests/customer_folder_parity.py proves it):
  SessionStart  — cwd is the place. Inside MASTER/Customers/<customer>/: no CLAUDE.md
                  between cwd and the customer root -> customer-folder/missing.md;
                  one there -> customer-folder/present.md naming the nearest.
  PostToolUse   — tool_input.file_path (or notebook_path) is the place. Missing only,
                  and once per customer per session: a marker in the temp dir keyed on
                  session_id stops it repeating on every write. SessionStart always
                  speaks, so a compacted session hears it again.
A customer folder is a child of a folder named Customers whose parent's name ends in
"Black Box Safety - MASTER" (the Mac and Windows OneDrive shapes both do). Two are not
this hook's: State of CA Agencies is the bbs-sales quote desk, whose learning lives in
buyer-level CLAUDE.md, quote-log.md and FLAGS.md (ca-rfq-intake), and a folder named
"DO NOT USE ..." is a dead tree. Both stay silent. Stdlib only.
Always exit 0, never print to stderr: a hook error must never block a tool. The texts
live in customer-folder/*.md; this script re-keys nothing.
"""
import json
import os
import re
import sys
import tempfile

MASTER_SUFFIX = "black box safety - master"
NOT_OURS = "state of ca agencies"
DEAD_PREFIX = "do not use"


def customer_root(start):
    """The Customers/<customer> folder at or above start, or None."""
    p = start.rstrip("/\\") or start
    for _ in range(64):
        parent = os.path.dirname(p)
        if not parent or parent == p:
            return None
        if (os.path.basename(parent).lower() == "customers"
                and os.path.basename(os.path.dirname(parent)).lower().endswith(MASTER_SUFFIX)):
            name = os.path.basename(p)
            low = name.lower()
            if name.startswith(".") or low == NOT_OURS or low.startswith(DEAD_PREFIX):
                return None             # hidden, the CA quote desk, or a dead tree
            if not os.path.isdir(p):
                return None             # a file sitting in Customers/
            return p
        p = parent
    return None


def nearest_claude_md(start, root):
    """The CLAUDE.md closest to start, looking up as far as root, or None."""
    d = start if os.path.isdir(start) else os.path.dirname(start)
    for _ in range(64):
        if not d:
            return None
        f = os.path.join(d, "CLAUDE.md")
        if os.path.isfile(f):
            return f
        if d == root:
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def text(fname, **tokens):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "customer-folder", fname)
    with open(path, encoding="utf-8-sig") as fh:
        t = fh.read().replace("\r\n", "\n").rstrip("\n")
    for k in ("name", "target"):
        t = t.replace("{" + k + "}", tokens[k])
    return t


def safe(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s)


def main():
    try:
        sys.stdin.reconfigure(encoding="utf-8-sig", errors="replace")
    except (AttributeError, ValueError):
        pass
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return
    h = json.loads(raw.lstrip("﻿"))
    if not isinstance(h, dict):
        return

    event = h.get("hook_event_name")
    if event == "SessionStart":
        start = h.get("cwd")
    elif event == "PostToolUse":
        ti = h.get("tool_input")
        start = None
        if isinstance(ti, dict):
            start = ti.get("file_path") or ti.get("notebook_path")
    else:
        return
    if not isinstance(start, str) or not start.strip():
        return

    root = customer_root(start)
    if not root:
        return
    found = nearest_claude_md(start, root)
    name = os.path.basename(root)

    sid = h.get("session_id")
    marker = None
    if isinstance(sid, str) and sid.strip():
        marker = os.path.join(tempfile.gettempdir(), "bbs-customer-folder",
                              safe(sid) + "--" + safe(name))

    if found:
        if event != "SessionStart":
            return
        context = text("present.md", name=name, target=found)
    else:
        if event == "PostToolUse" and marker and os.path.exists(marker):
            return
        context = text("missing.md", name=name, target=os.path.join(root, "CLAUDE.md"))
        if marker:
            try:
                os.makedirs(os.path.dirname(marker), exist_ok=True)
                open(marker, "w").close()
            except OSError:
                pass                    # no marker: the reminder repeats, it never blocks

    out = ('{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}'
           % (event, json.dumps(context, ensure_ascii=True)))
    sys.stdout.write(out)
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 — fail open, silently
        pass
    sys.exit(0)
