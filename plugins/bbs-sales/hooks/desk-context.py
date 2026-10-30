#!/usr/bin/env python3
"""Quote-desk buyer context, two events:

  SessionStart  cwd inside the desk tree: put that buyer's newest quote-log rows and open FLAGS
                entries in front of Claude before the first prompt.
  PostToolUse   first Write/Edit inside a dated deal folder (<Agency>/<Buyer>/<Item M.D.YY>/ or
                <Agency>/<Institution>/<Buyer>/<Item M.D.YY>/): the same rows and flags, the
                buyer's CLAUDE.md / quote-log.md / FLAGS.md named as the files to keep current,
                and the buyer's quote-log rows older than 30 days with no final outcome listed
                for close-out. Once per buyer per session (temp-dir marker keyed on session_id).

The Python half of desk-context.ps1: same output on every input, proven by
hooks/tests/parity.py. Change both or neither (invariant 3).

SessionStart prints plain text; PostToolUse prints hookSpecificOutput JSON. Silent when the folder
shape is unclear or nothing relevant is found. Always exits 0, never writes to stderr. Stdlib only.
BBS_TODAY=YYYY-MM-DD pins "today" for the tests.
"""
import datetime
import json
import os
import re
import sys
import tempfile

TREE = "All RFQ's by Agency"
BUYER_FILES = ("CLAUDE.md", "quote-log.md", "FLAGS.md")
STALE_DAYS = 30
DEAL_START = re.compile(r"^\s*[0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})(?![0-9])")
DEAL_END = re.compile(r"[ _-][0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})\s*$")
DEAL_ISO = re.compile(r"[ _-][0-9]{4}-[0-9]{2}-[0-9]{2}\s*$")
ISO = re.compile(r"^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})$")
MDY = re.compile(r"^([0-9]{1,2})[./]([0-9]{1,2})[./]([0-9]{2}|[0-9]{4})$")
DATE_TOKEN = re.compile(r"(?<![0-9])([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4}))(?![0-9])")
SEPARATOR = re.compile(r"^\|[\s:|-]+$")
FINAL = re.compile(r"^(won|lost|no answer)\b", re.I)
CLOSED = re.compile(r"^(closed|resolved)\b", re.I)
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
BULLET_DONE = re.compile(r"^(\[x\]|~~|closed\b|resolved\b)", re.I)
LEAD_MARKUP = re.compile(r"^[`*_ ]+")
TREE_RE = re.compile(re.escape(TREE), re.I | re.A)


def split_lines(text):
    # Lines without their newlines; a final newline does not add an empty line.
    parts = re.split(r"\r\n|\n|\r", text)
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8-sig", "replace")


def read_lines(path):
    return split_lines(read_text(path))


def cells(line):
    t = line.strip()
    if not t.startswith("|"):
        return None
    t = t[1:]
    if t.endswith("|"):
        t = t[:-1]
    return [c.strip() for c in t.split("|")]


def parse_date(s):
    """(y, m, d) from ISO or M.D.YY / M/D/YYYY, or None."""
    m = ISO.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = MDY.match(s)
        if not m:
            return None
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(3)) == 2:
            y += 2000
    try:
        datetime.date(y, mo, d)
    except ValueError:
        return None
    return (y, mo, d)


def date_key(t):
    return t[0] * 10000 + t[1] * 100 + t[2]


def today():
    raw = os.environ.get("BBS_TODAY", "")
    t = parse_date(raw) if raw else None
    return datetime.date(*t) if t else datetime.date.today()


def log_rows(lines):
    """(header line or None, rows). A row: idx, line, cells, key (0 when the date will not parse)."""
    header = None
    rows = []
    for i, l in enumerate(lines):
        c = cells(l)
        if c is None or SEPARATOR.match(l.strip()) or not c[0]:
            continue
        if c[0].lower() == "date":
            if header is None:
                header = l
            continue
        d = parse_date(c[0])
        rows.append({"idx": i, "line": l, "cells": c, "d": d, "key": date_key(d) if d else 0})
    return header, rows


def recent_rows(rows, n):
    # Newest first; ties keep file order.
    return sorted(rows, key=lambda r: r["key"] * 1000000 + (999999 - r["idx"]), reverse=True)[:n]


def stale_rows(rows):
    """Rows older than STALE_DAYS with no final outcome and no FLAG already written, oldest first."""
    out = []
    now = today()
    for r in rows:
        if r["d"] is None or (now - datetime.date(*r["d"])).days <= STALE_DAYS:
            continue
        c = r["cells"]
        outcome = LEAD_MARKUP.sub("", c[5]) if len(c) > 5 else ""
        if FINAL.match(outcome) or "[flag" in outcome.lower():
            continue
        out.append(r)
    return sorted(out, key=lambda r: r["key"] * 1000000 + r["idx"])


def flag_entries(lines, n):
    """Newest n open FLAGS entries: dated table rows and bullets, closed ones dropped."""
    ents = []
    for i, l in enumerate(lines):
        c = cells(l)
        if c is not None:
            if SEPARATOR.match(l.strip()) or not c[0]:
                continue
            d = parse_date(c[0])
            if d is None or CLOSED.match(c[-1]):
                continue
        else:
            m = BULLET.match(l)
            if not m or BULLET_DONE.match(m.group(1)):
                continue
            t = DATE_TOKEN.search(m.group(1))
            d = parse_date(t.group(1)) if t else None
        ents.append((( date_key(d) if d else 0) * 1000000 + i, l))
    ents.sort(key=lambda e: e[0], reverse=True)
    return [e[1] for e in ents[:n]]


def precedent_block(path):
    header, rows = log_rows(read_lines(path))
    pick = recent_rows(rows, 12)
    out = [f"PRECEDENT -- {path} (newest first; cite these before pricing):"]
    if header is not None and pick:
        out.append(header)
    out.extend(r["line"] for r in pick)
    return out


def flags_block(path):
    ents = flag_entries(read_lines(path), 5)
    if not ents:
        return []
    return [f"OPEN FLAGS -- {path} (latest; do not repeat these mistakes):"] + ents


def session_start(d):
    if TREE.lower() not in d.lower():
        return []
    out = []
    for _ in range(5):
        if not d:
            break
        ql = os.path.join(d, "quote-log.md")
        fl = os.path.join(d, "FLAGS.md")
        if os.path.exists(ql):
            out.extend(precedent_block(ql))
        if os.path.exists(fl):
            out.extend(flags_block(fl))
        if out:
            break
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return out


def locate(path):
    """(buyer_dir, buyer_rel, deal_name) when path is a file inside a dated deal folder, else None."""
    end = -1
    for m in TREE_RE.finditer(path):
        a, b = m.start(), m.end()
        if (a == 0 or path[a - 1] in "/\\") and b < len(path) and path[b] in "/\\":
            end = b
            break
    if end < 0:
        return None
    sep = path[end]
    comps = [c for c in re.split(r"[\\/]+", path[end + 1:]) if c != ""]
    if len(comps) < 4 or any(c.startswith(".") for c in comps):
        return None
    j = -1
    for k, c in enumerate(comps[:-1]):
        if DEAL_START.search(c) or DEAL_END.search(c) or DEAL_ISO.search(c):
            j = k
            break
    if j < 2 or j > 3:
        return None             # no dated deal folder, deal at agency level, or too deep to be sure
    buyer_dir = path[:end] + sep + sep.join(comps[:j])
    if not os.path.isdir(buyer_dir):
        return None
    if not any(os.path.isfile(os.path.join(buyer_dir, f)) for f in BUYER_FILES):
        # An institution folder (buyers one level down) is not the buyer.
        try:
            for e in sorted(os.listdir(buyer_dir)):
                sub = os.path.join(buyer_dir, e)
                if os.path.isdir(sub) and any(os.path.isfile(os.path.join(sub, f)) for f in ("CLAUDE.md", "quote-log.md")):
                    return None
        except OSError:
            return None
    return buyer_dir, "/".join(comps[:j]), comps[j]


def safe(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s)


def closeout_text():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desk-context", "outcome-closeout.md")
    return "\n".join(split_lines(read_text(path)))


def first_write(h):
    ti = h.get("tool_input")
    p = ti.get("file_path") if isinstance(ti, dict) else None
    if not isinstance(p, str) or not p.strip():
        return None
    loc = locate(p)
    if not loc:
        return None
    buyer_dir, rel, deal = loc

    sid = h.get("session_id")
    marker = None
    if isinstance(sid, str) and sid.strip():
        marker = os.path.join(tempfile.gettempdir(), "bbs-desk-buyer", safe(sid) + "--" + safe(rel))
        if os.path.exists(marker):
            return None

    out = [f"BUYER DESK -- first write in {deal} for {rel} (once per session). Keep this buyer's files current in {buyer_dir}:",
           "  CLAUDE.md -- how they buy, what we learned (add a line only when something surprised you)",
           "  quote-log.md -- one row per request; set the Outcome when you learn it",
           "  FLAGS.md -- one entry for anything that went wrong, caught before send or not"]
    missing = [f for f in BUYER_FILES if not os.path.isfile(os.path.join(buyer_dir, f))]
    if missing:
        out.append("MISSING: " + ", ".join(missing) + " -- create from the ca-rfq-intake skill's references/buyer-context-template.md "
                   "(FLAGS.md: bbs-foundations, bbs-claude-md-forge/references/flags-template.md).")
    ql = os.path.join(buyer_dir, "quote-log.md")
    fl = os.path.join(buyer_dir, "FLAGS.md")
    if os.path.isfile(ql):
        out.extend(precedent_block(ql))
        _, rows = log_rows(read_lines(ql))
        stale = stale_rows(rows)
        if stale:
            out.append(f"OUTCOMES TO CLOSE -- {len(stale)} quote-log rows older than {STALE_DAYS} days have no final outcome (won / lost / no answer):")
            out.extend(r["line"] for r in stale[:10])
            if len(stale) > 10:
                out.append(f"(+{len(stale) - 10} more)")
            out.append(closeout_text())
    if os.path.isfile(fl):
        out.extend(flags_block(fl))

    if marker:
        try:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            open(marker, "w").close()
        except OSError:
            pass                # no marker: the reminder repeats, it never blocks
    return out


def emit(text):
    sys.stdout.flush()
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


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

    if h.get("hook_event_name") == "PostToolUse":
        out = first_write(h)
        if out:
            ctx = "\n".join(out)
            emit('{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":%s}}'
                 % json.dumps(ctx, ensure_ascii=True))
        return

    d = str(h.get("cwd") or "")
    if not d or not os.path.exists(d):
        return
    out = session_start(d)
    if out:
        emit("\n".join(out) + "\n")


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 -- fail open, silently
        pass
    sys.exit(0)
