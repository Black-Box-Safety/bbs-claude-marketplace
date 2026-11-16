#!/usr/bin/env python3
"""desk-learn: a reminder to close the loop when a key change lands on a customer desk.

PostToolUse (Bash|Write|Edit|MultiEdit). Reminds only: exit 0 with additionalContext, never a
block, never a write to a customer folder, never stderr. The text is fixed and quotes no file
content; the only thing taken from the call is the folder's own name.

Key events, tool writes only (docs: the desk-linked report spec, section 8; D10.4):
  stage-sent / stage-outcome  RFQ.md under "All RFQ's by Agency" written with the Stage header at sent or
                              outcome and not already there: an Edit or MultiEdit whose old and new
                              Stage lines differ, or a Write whose stage differs from the deal's
                              last-seen stage (<temp>/bbs-desk-learn/stage--<deal>, not session-keyed),
                              or a Bash call to rfq_record.py set-stage <rfq> sent|outcome.
                              rfq-state.json is never read: rfq_record rewrites it on every compile and
                              PostToolUse hooks run in parallel, so its age proves nothing.
  quote-log                   quote-log.md under the CA tree written with a table row in it, or a Bash
                              append (>> or tee -a) to one; a relative path resolves against cwd. An edit
                              whose text carries the outcome close-out flow's wording ("per BC", "no order
                              in BC", [FLAG) is a batch the rep did not decide: ledger line Q, no reminder,
                              nothing pending.
  filled                      a Write under a FILLED/ folder in the CA tree, or a bbs-fill call whose
                              command names a FILLED/ path
  award                       a PO, award or NOA file (by filename) written in a CA or Sentinel deal folder.
                              Not detected: cp or mv of a PO into a folder; the scanner and the weekly
                              report catch those.
  sentinel-log                Bechtel/sentinel/learning/quote-log.md written with a table row in it
  sentinel-banner             a CLAUDE.md under Bechtel/sentinel/<site>/<rfp>/ written with a
                              "**Status" banner line in it (with or without the leading ">")
Files dropped in by OneDrive or n8n are not tool events; the weekly report and the scanner catch them.

Once per deal per event per session (a marker in <temp>/bbs-desk-learn keyed on session_id). The
session's ledger holds the event only, never a folder name (names can carry account numbers). When the
hook input marks a subagent (agent_id), the ledger is updated and nothing is said: a subagent cannot ask
a rep. A call that hits several deals gets one line. A `desk_memory.py add` or `close` Bash call, or a
write to learning/lessons.md, is a capture and clears the ledger.

Stop backstop (hook_event_name Stop): after a turn boundary. The first Stop after a key change only arms
(ledger line S); a later Stop with the change still uncaptured speaks, once per session. Default is
MESSAGE-ONLY: {"systemMessage": ...}, which only shows the rep a line. The one switch is the environment
variable BBS_DESK_LEARN_STOP: unset or "message" keeps it passive; "continue" lets the hook resume the
turn once ({"decision":"block"} with a fixed reason), and never when stop_hook_active is already true.
Set it in the `env` block of a settings file (managed settings for everyone, ~/.claude/settings.json for
one person). Parker has not ruled which; the default stays message-only until he does.

Temp dir: the first of TMPDIR, TEMP, TMP that is set, else the platform default. Python's tempfile and
PowerShell's GetTempPath order these differently on Windows, so both halves and desk-learn.sh pick
explicitly and always look at the same folder.

The Python half of desk-learn.ps1: same output on every input, proven by hooks/tests/desk_learn_parity.py.
Change both or neither (invariant 3). Fails open on anything unreadable. Stdlib only.
"""
import json
import os
import re
import sys
import tempfile

TREE = "All RFQ's by Agency"
SENTINEL = "/bechtel/sentinel/"
MARKERS = "bbs-desk-learn"
STOP_ENV = "BBS_DESK_LEARN_STOP"

EVENTS = {
    "stage-sent": "RFQ.md written at stage sent",
    "stage-outcome": "RFQ.md written at stage outcome",
    "quote-log": "quote-log row added or Outcome set",
    "filled": "new file in FILLED/",
    "award": "PO, award or NOA file written",
    "sentinel-log": "Sentinel quote-log appended",
    "sentinel-banner": "RFP status banner edited",
}
REMINDER = ("Key change: {event} in {folder}. Close the loop: ask the rep one question. Anything about this "
            "buyer or site worth remembering, or a lesson from this deal? If they give words, run "
            "`desk-remember` with their own words. If they offer a lesson, show the one-line draft and append "
            "it to `learning/lessons.md` only on their yes (if the desk has no `lessons.md`, say so and write "
            "nothing). If they say nothing, run `desk_memory.py close --none`.")
STOP_REASON = ("Key changes were made this session and nothing was captured or closed. Ask the rep one "
               "question, once: anything about this buyer or site worth remembering, or a lesson from this "
               "deal? If they give words, run `desk-remember` with their own words. If they offer a lesson, "
               "show the one-line draft and append it to `learning/lessons.md` only on their yes (if the "
               "desk has no `lessons.md`, say so and write nothing). If they say nothing, run "
               "`desk_memory.py close --none`. Do not ask again.")
STOP_MESSAGE = ("bbs-sales: key changes were made this session and nothing was saved for next time. Tell "
                "Claude what to remember, or say there is nothing to remember, before you close.")

STAGE_RE = re.compile(r"^\*\*Stage:\*\*[ \t]*(.+?)[ \t]*\r?$", re.M)
DATA_ROW = re.compile(r"^\|[ \t]*(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./][0-9]{1,2}[./](?:[0-9]{2}|[0-9]{4}))[ \t]*\|", re.M)
BANNER = re.compile(r"^(?:>[ \t]*)?\*\*Status", re.M)
AWARD = re.compile(r"(?i)(?:^|[^A-Za-z])(?:PO|NOA|award|purchase[ _-]?order|notice[ _-]of[ _-]award)(?:[^A-Za-z]|$)")
SET_STAGE = re.compile(r"""rfq_record\.py["']?\s+set-stage\s+("[^"]*"|'[^']*'|\S+)\s+["']?(sent|outcome)["']?(?=\s|$)""")
MEMORY_CAPTURE = re.compile(r"""desk_memory\.py["']?\s+(?:add|close)(?=\s|$)""")
APPEND_LOG = re.compile(r"""(?:\x3e\x3e|\btee[ \t]+-a)[ \t]*(?:"([^"\n]*?quote-log\.md)"|'([^'\n]*?quote-log\.md)'|([^\s"';&|]*quote-log\.md))""")
FILLED_TOKEN = re.compile(r"/FILLED/", re.I)
CLOSEOUT = re.compile(r"(?i)\bper BC\b|\bno order in BC\b|\[FLAG")
ABSOLUTE = re.compile(r"^(?:/|[A-Za-z]:/|~)")


def norm(p):
    return str(p or "").replace("\\", "/")


def resolve(n, cwd):
    """A path from a Bash command, made absolute against the session's cwd when it is relative."""
    if not n or ABSOLUTE.match(n) or not cwd:
        return n
    return cwd.rstrip("/") + "/" + re.sub(r"^\./", "", n)


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
    for v in ("TMPDIR", "TEMP", "TMP"):
        x = os.environ.get(v)
        if x:
            return os.path.join(x, MARKERS)
    return os.path.join(tempfile.gettempdir(), MARKERS)


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8-sig", "replace")


def stage_of(text):
    m = STAGE_RE.search(str(text or ""))
    return m.group(1).strip().lower() if m else None


def stage_path(folder):
    return os.path.join(tmp_dir(), "stage--" + safe(norm(folder).lower()))


def last_stage(folder):
    try:
        return read_text(stage_path(folder)).strip()
    except OSError:
        return None


def set_last_stage(folder, st):
    try:
        os.makedirs(tmp_dir(), exist_ok=True)
        with open(stage_path(folder), "wb") as fh:
            fh.write(st.encode("utf-8"))
    except OSError:
        pass


def pairs(tool, inp):
    """(old, new) text pairs of an Edit or MultiEdit."""
    if tool == "Edit":
        return [(str(inp.get("old_string") or ""), str(inp.get("new_string") or ""))]
    eds = inp.get("edits")
    if isinstance(eds, list):
        return [(str(e.get("old_string") or ""), str(e.get("new_string") or "")) for e in eds if isinstance(e, dict)]
    return []


def new_texts(tool, inp):
    if tool == "Write":
        return [str(inp.get("content") or "")]
    return [b for _, b in pairs(tool, inp)]


def stage_moved(tool, inp, folder):
    """'sent' or 'outcome' when this write puts the RFQ.md at that stage and it was not there already."""
    moved = None
    if tool == "Write":
        ns = stage_of(inp.get("content"))
        if ns:
            if ns in ("sent", "outcome") and ns != last_stage(folder):
                moved = ns
            set_last_stage(folder, ns)
        return moved
    for old, new in pairs(tool, inp):
        ns = stage_of(new)
        if ns:
            if ns in ("sent", "outcome") and ns != stage_of(old):
                moved = ns
            set_last_stage(folder, ns)
    return moved


def log_event(n):
    if in_sentinel(n) and dirname(n).lower().endswith("/learning"):
        return "sentinel-log"
    if in_ca(n):
        return "quote-log"
    return None


def file_events(tool, inp):
    """(events, capture) for a Write, Edit or MultiEdit. An event is (name, folder)."""
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
        folder = folder_of(n)
        st = stage_moved(tool, inp, folder)
        if st:
            out.append(("stage-" + st, folder))
    elif base == "quote-log.md":
        ev = log_event(n)
        if ev and any(DATA_ROW.search(t) for t in texts):
            if any(CLOSEOUT.search(t) for t in texts):
                out.append(("closeout", folder_of(n)))
            else:
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


def bash_events(inp, cwd):
    cmd = str(inp.get("command") or "")
    ncmd = norm(cmd)
    out = []
    capture = bool(MEMORY_CAPTURE.search(cmd))
    m = SET_STAGE.search(cmd)
    if m:
        rfq = resolve(norm(m.group(1).strip("\"'")), cwd)
        folder = dirname(rfq) or "RFQ"
        set_last_stage(folder, m.group(2))
        out.append(("stage-" + m.group(2), folder))
    if "bbs-fill" in cmd:
        m = FILLED_TOKEN.search(ncmd)
        if m:
            out.append(("filled", prefix_before(ncmd, m.start())))
    for m in APPEND_LOG.finditer(cmd):
        n = resolve(norm(m.group(1) or m.group(2) or m.group(3)), cwd)
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
    cwd = norm(h.get("cwd"))
    if tool == "Bash":
        found, capture = bash_events(inp, cwd)
    elif tool in ("Write", "Edit", "MultiEdit"):
        found, capture = file_events(tool, inp)
    else:
        return None
    sid = safe(h.get("session_id"))
    if capture and sid:
        ledger_add(sid, "C")
    subagent = bool(h.get("agent_id"))
    new = []
    for ev, folder in found:
        if ev == "closeout":
            if sid:
                ledger_add(sid, "Q\tquote-log")
            continue
        if subagent:
            if sid:
                ledger_add(sid, "K\t" + ev)
            continue
        if sid:
            m = os.path.join(tmp_dir(), sid + "--" + ev + "--" + safe(norm(folder).lower()))
            if os.path.exists(m):
                continue
            mark(m)
            ledger_add(sid, "K\t" + ev)
        new.append((ev, folder))
    if not new:
        return None
    if len(new) == 1:
        text = REMINDER.format(event=EVENTS[new[0][0]], folder=clean_name(basename(norm(new[0][1]))) or "this folder")
    else:
        evs = []
        for ev, _ in new:
            if EVENTS[ev] not in evs:
                evs.append(EVENTS[ev])
        text = REMINDER.format(event="; ".join(evs), folder="%d folders" % len(new))
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}


def ledger_state(sid):
    """(pending, armed): a key change with no capture after it, and whether a Stop has passed since."""
    try:
        text = read_text(ledger_path(sid))
    except OSError:
        return False, False
    p = a = False
    for l in re.split(r"\r\n|\n|\r", text):
        if l.startswith("K\t"):
            p, a = True, False
        elif l == "C":
            p, a = False, False
        elif l == "S" and p:
            a = True
    return p, a


def stop(h):
    sid = safe(h.get("session_id"))
    if not sid:
        return None
    p, a = ledger_state(sid)
    if not p:
        return None
    if not a:
        ledger_add(sid, "S")        # the turn the change landed in ends here: arm, say nothing
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
