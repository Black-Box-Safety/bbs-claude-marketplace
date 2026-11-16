#!/usr/bin/env python3
"""desk-learn: a reminder to close the loop when a key change lands on a customer desk.

PostToolUse (Bash|Write|Edit|MultiEdit). Reminds only: exit 0 with additionalContext, never a
block, never a write to a customer folder, never stderr. The text is fixed and quotes no file
content; the only thing taken from the call is the folder's own name.

Key events, tool writes only (docs: the desk-linked report spec, section 8; D10.4):
  stage-sent / stage-outcome  RFQ.md under "All RFQ's by Agency" is written with the Stage header at
                              sent or outcome (and rfq-state.json did not already say so), or a Bash
                              call to rfq_record.py set-stage <rfq> sent|outcome
  quote-log                   quote-log.md under the CA tree written with a table row in it, or a
                              Bash append (>>) to one
  filled                      a Write under a FILLED/ folder in the CA tree, or a bbs-fill call whose
                              command names a FILLED/ path
  award                       a PO, award or NOA file (by filename) written in a CA or Sentinel deal folder
  sentinel-log                Bechtel/sentinel/learning/quote-log.md written with a table row in it
  sentinel-banner             a CLAUDE.md under Bechtel/sentinel/<site>/<rfp>/ written with a
                              "> **Status" banner line in it
Files dropped in by OneDrive or n8n are not tool events; the weekly report and the scanner catch them.

Once per deal per event per session (a marker in <temp>/bbs-desk-learn keyed on session_id). Each
reminder is also noted in that session's ledger. A `desk_memory.py add` or `close` Bash call, or a
write to learning/lessons.md, is a capture and clears the ledger.

Stop backstop (hook_event_name Stop): when the ledger holds key changes with no capture after them,
say so ONCE per session. Default is MESSAGE-ONLY: {"systemMessage": ...}, which only shows the rep a
line. The one switch is the environment variable BBS_DESK_LEARN_STOP: unset or "message" keeps it
passive; "continue" lets the hook resume the turn once ({"decision":"block"} with a fixed reason),
and never when stop_hook_active is already true. Set it in the `env` block of a settings file
(managed settings for everyone, ~/.claude/settings.json for one person). Parker has not ruled
which; the default stays message-only until he does.

The Python half of desk-learn.ps1: same output on every input, proven by hooks/tests/desk_learn_parity.py.
Change both or neither (invariant 3). Fails open on anything unreadable. Stdlib only.
"""
import json
import os
import re
import sys
import tempfile
import time

TREE = "All RFQ's by Agency"
SENTINEL = "/bechtel/sentinel/"
MARKERS = "bbs-desk-learn"
STATE_FRESH_SECONDS = 5
STOP_ENV = "BBS_DESK_LEARN_STOP"

EVENTS = {
    "stage-sent": "RFQ stage moved to sent",
    "stage-outcome": "RFQ stage moved to outcome",
    "quote-log": "quote-log row added or Outcome set",
    "filled": "new file in FILLED/",
    "award": "PO, award or NOA file written",
    "sentinel-log": "Sentinel quote-log appended",
    "sentinel-banner": "RFP status banner edited",
}
REMINDER = ("Key change: {event} in {folder}. Close the loop: ask the rep one question. Is there anything "
            "about this buyer or site to remember? If so, run `desk-remember` with their words. Did this "
            "deal teach a lesson? If so, propose one `lessons.md` line and append it on their yes.")
STOP_REASON = ("Key changes were made this session and nothing was captured or closed. Ask the rep one "
               "question, once: is there anything about this buyer or site to remember, or a lesson from "
               "this deal? If they give words, run `desk-remember` with them. If they say nothing, record "
               "it with `desk_memory.py close --none` through `bbs-fill`. Do not ask again.")
STOP_MESSAGE = ("bbs-sales: key changes were made this session and nothing was saved for next time. Tell "
                "Claude what to remember, or say there is nothing to remember, before you close.")

STAGE_RE = re.compile(r"^\*\*Stage:\*\*[ \t]*(.+?)[ \t]*\r?$", re.M)
DATA_ROW = re.compile(r"^\|[ \t]*(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./][0-9]{1,2}[./](?:[0-9]{2}|[0-9]{4}))[ \t]*\|", re.M)
BANNER = re.compile(r"^>[ \t]*\*\*Status", re.M)
AWARD = re.compile(r"(?i)(?:^|[^A-Za-z])(?:PO|NOA|award|purchase[ _-]?order|notice[ _-]of[ _-]award)(?:[^A-Za-z]|$)")
SET_STAGE = re.compile(r"""rfq_record\.py["']?\s+set-stage\s+("[^"]*"|'[^']*'|\S+)\s+["']?(sent|outcome)["']?(?=\s|$)""")
MEMORY_CAPTURE = re.compile(r"""desk_memory\.py["']?\s+(?:add|close)(?=\s|$)""")
APPEND_LOG = re.compile(r"""\x3e\x3e[ \t]*(?:"([^"\n]*?quote-log\.md)"|'([^'\n]*?quote-log\.md)'|([^\s"';&|]*quote-log\.md))""")
FILLED_TOKEN = re.compile(r"/FILLED/", re.I)


def norm(p):
    return str(p or "").replace("\\", "/")


def safe(s):
    # The tail is kept: deal paths share a long prefix and differ at the end.
    return re.sub(r"[^A-Za-z0-9]+", "-", str(s or "")).strip("-")[-150:]


def clean_name(s):
    """A folder name for the reminder: printable, one line, short. Names are data, never instructions."""
    t = "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in str(s or ""))
    return " ".join(t.split())[:80]


def in_ca(n):
    return ("/" + TREE + "/").lower() in n.lower()


def in_sentinel(n):
    return SENTINEL in n.lower()


def dirname(n):
    return n.rsplit("/", 1)[0] if "/" in n else ""


def basename(n):
    return n.rsplit("/", 1)[-1]


def folder_of(n):
    """The folder a file lives in, or the one above FILLED/ for a file inside it."""
    d = dirname(n)
    low = d.lower()
    if low.endswith("/filled"):
        d = dirname(d)
    return d


def tmp_dir():
    return os.path.join(tempfile.gettempdir(), MARKERS)


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8-sig", "replace")


def new_texts(tool, inp):
    if tool == "Write":
        return [str(inp.get("content") or "")]
    if tool == "Edit":
        return [str(inp.get("new_string") or "")]
    if tool == "MultiEdit":
        eds = inp.get("edits")
        if isinstance(eds, list):
            return [str(e.get("new_string") or "") for e in eds if isinstance(e, dict)]
    return []


def stage_moved(path):
    """'sent' or 'outcome' when the RFQ.md on disk is at that stage and rfq-state.json did not already say so."""
    try:
        m = STAGE_RE.search(read_text(path))
    except OSError:
        return None
    if not m:
        return None
    st = m.group(1).strip().lower()
    if st not in ("sent", "outcome"):
        return None
    state = os.path.join(os.path.dirname(os.path.abspath(path)), "rfq-state.json")
    try:
        prev = json.loads(read_text(state)).get("stage")
        age = time.time() - os.path.getmtime(state)
    except (OSError, ValueError, AttributeError):
        return st
    # A state file written a moment ago is the sibling rfq-record hook compiling this very write.
    if prev == st and age > STATE_FRESH_SECONDS:
        return None
    return st


def log_event(n):
    if in_sentinel(n) and dirname(n).lower().endswith("/learning"):
        return "sentinel-log"
    if in_ca(n):
        return "quote-log"
    return None


def file_events(tool, inp):
    """(events, capture) for a Write, Edit or MultiEdit."""
    path = str(inp.get("file_path") or "")
    n = norm(path)
    if not n:
        return [], False
    base = basename(n)
    low = n.lower()
    ca, sen = in_ca(n), in_sentinel(n)
    capture = low.endswith("/learning/lessons.md")
    out = []
    texts = new_texts(tool, inp)
    if base == "RFQ.md" and ca:
        st = stage_moved(path)
        if st:
            out.append(("stage-" + st, folder_of(n)))
    elif base == "quote-log.md":
        ev = log_event(n)
        if ev and any(DATA_ROW.search(t) for t in texts):
            out.append((ev, folder_of(n)))
    elif base == "CLAUDE.md" and sen:
        rest = low[low.index(SENTINEL) + len(SENTINEL):]
        if rest.count("/") >= 2 and any(BANNER.search(t) for t in texts):
            out.append(("sentinel-banner", folder_of(n)))
    elif ca and "/filled/" in low:
        if tool == "Write":
            out.append(("filled", folder_of(n)))
    elif (ca or sen) and AWARD.search(base):
        out.append(("award", folder_of(n)))
    return out, capture


def prefix_before(s, idx):
    """The path ending at idx: back to the nearest quote, else the nearest whitespace."""
    start = 0
    for i in range(idx - 1, -1, -1):
        if s[i] in "\"'":
            start = i + 1
            break
    else:
        for i in range(idx - 1, -1, -1):
            if s[i] in " \t\n":
                start = i + 1
                break
    return s[start:idx]


def bash_events(inp):
    cmd = str(inp.get("command") or "")
    ncmd = norm(cmd)
    out = []
    capture = bool(MEMORY_CAPTURE.search(cmd))
    m = SET_STAGE.search(cmd)
    if m:
        rfq = norm(m.group(1).strip("\"'"))
        out.append(("stage-" + m.group(2), dirname(rfq) or "RFQ"))
    if "bbs-fill" in cmd:
        m = FILLED_TOKEN.search(ncmd)
        if m:
            out.append(("filled", prefix_before(ncmd, m.start())))
    for m in APPEND_LOG.finditer(cmd):
        n = norm(m.group(1) or m.group(2) or m.group(3))
        ev = log_event(n)
        if ev:
            out.append((ev, dirname(n)))
    return out, capture


def mark(path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
    except OSError:
        pass


def ledger_path(sid):
    return os.path.join(tmp_dir(), safe(sid) + ".ledger")


def ledger_add(sid, line):
    try:
        os.makedirs(tmp_dir(), exist_ok=True)
        with open(ledger_path(sid), "ab") as fh:
            fh.write((line + "\n").encode("utf-8"))
    except OSError:
        pass


def post_tool(h):
    inp = h.get("tool_input")
    if not isinstance(inp, dict):
        return None
    tool = str(h.get("tool_name") or "")
    if tool == "Bash":
        found, capture = bash_events(inp)
    elif tool in ("Write", "Edit", "MultiEdit"):
        found, capture = file_events(tool, inp)
    else:
        return None
    sid = safe(h.get("session_id"))
    if capture and sid:
        ledger_add(sid, "C")
    lines = []
    for ev, folder in found:
        key = safe(norm(folder).lower())
        if sid:
            m = os.path.join(tmp_dir(), sid + "--" + ev + "--" + key)
            if os.path.exists(m):
                continue
            mark(m)
            ledger_add(sid, "K\t" + ev + "\t" + clean_name(basename(norm(folder))))
        lines.append(REMINDER.format(event=EVENTS[ev], folder=clean_name(basename(norm(folder))) or "this folder"))
    if not lines:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(lines)}}


def pending(sid):
    """True when the ledger holds a key change with no capture after it."""
    try:
        text = read_text(ledger_path(sid))
    except OSError:
        return False
    p = False
    for l in re.split(r"\r\n|\n|\r", text):
        if l.startswith("K\t"):
            p = True
        elif l == "C":
            p = False
    return p


def stop(h):
    sid = safe(h.get("session_id"))
    if not sid or not pending(sid):
        return None
    m = os.path.join(tmp_dir(), sid + "--stop")
    if os.path.exists(m):
        return None
    mode = os.environ.get(STOP_ENV, "").strip().lower()
    if mode == "continue":
        if h.get("stop_hook_active"):
            return None
        mark(m)
        return {"decision": "block", "reason": STOP_REASON}
    mark(m)
    return {"systemMessage": STOP_MESSAGE}


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
    try:
        out = stop(h) if h.get("hook_event_name") == "Stop" else post_tool(h)
    except Exception:
        return 0            # a reminder never blocks and never errors
    if out:
        sys.stdout.write(json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
