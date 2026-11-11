#!/usr/bin/env python3
"""PostToolUse hook: validate an RFQ.md under "All RFQ's by Agency" and compile rfq-state.json.

Reads the hook JSON on stdin. Acts only when
tool_input.file_path, backslashes turned to slashes, contains "/All RFQ's by Agency/" and ends
with "/RFQ.md"; anything else exits 0 silently.

A v1 record (Status header "| Stage | State | Date |" inside the ## Status section) passes: exit 0,
no sidecar, stdout {"systemMessage": ...} telling the rep to try `migrate --dry-run`.
On a parse or validation failure: stderr "bbs-sales rfq-record: <n> problem(s) in RFQ.md", then
one problem per line, exit 2 (PostToolUse stderr is fed back to Claude). On success it writes
rfq-state.json beside the record and exits 0 silently. This is the ONLY validator: hooks.json runs
python3 first, and rfq-record-hook.ps1 (run only when python3 is missing) validates nothing and
returns a "needs python3; this edit was not checked" notice instead. Stdlib only. Fails open on
unreadable input.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

TREE = "All RFQ's by Agency"
V1_NOTICE = ("bbs-sales: this RFQ.md is still in the v1 or legacy format, so it was not checked and no rfq-state.json "
             "was written. Run python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/rfq_record.py\" migrate "
             "\"<path>\" --dry-run to see whether it converts.")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fail(problems):
    sys.stderr.write("bbs-sales rfq-record: %d problem(s) in RFQ.md\n" % len(problems))
    for p in problems:
        sys.stderr.write(p + "\n")
    return 2


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
    inp = h.get("tool_input") or {}
    if not isinstance(inp, dict):
        return 0
    path = str(inp.get("file_path") or "")
    norm = path.replace("\\", "/")
    marker = "/" + TREE + "/"
    if marker not in norm or not norm.endswith("/RFQ.md"):
        return 0
    if not os.path.isfile(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return 0

    import rfq_record as rr

    if rr.is_v1(text):
        sys.stdout.write(json.dumps({"systemMessage": V1_NOTICE}) + "\n")
        return 0
    try:
        rec = rr.parse(text)
    except rr.RecordError as e:
        return fail(e.problems)
    problems = rr.validate(rec)
    for i, r in enumerate(rec.status, 1):
        if r.date and not DATE_RE.match(r.date):
            problems.append("Status row %d Date %r is not YYYY-MM-DD" % (i, r.date))
    if problems:
        return fail(problems)
    deal = norm[norm.index(marker) + len(marker):-len("/RFQ.md")]
    rr.write_state(rec, path, deal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
