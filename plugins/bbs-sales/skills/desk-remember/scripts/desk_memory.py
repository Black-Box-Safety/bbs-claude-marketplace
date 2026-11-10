#!/usr/bin/env python3
"""Write one remembered line into the right LEARNED.md of a customer desk, or show what loads.

  where  --at PATH                      which folders a line could be saved to, nearest first
  add    --at PATH --level N --author NAME --kind KIND --text "..." [--wider N] [--date D]
                                        append one line to that folder's LEARNED.md
  show   --at PATH                      the lines a session opened at PATH would be given

--level and --wider are the numbers `where` prints (1 = the nearest folder). A dated deal folder
is never a level: what is true for one deal belongs in its RFQ.md, not in memory.

Refuses, and writes nothing, when the text holds what belongs to a system of record or a secret
(a dollar amount, a long digit run such as an account or contract number, a certification or
contract number pattern), when it is more than one line, or when the level needs Parker.
The line format is read by hooks/desk-memory.py and desk-memory.ps1: change all three together.

Exit 0 = done. Exit 2 = refused, with one plain sentence on stdout saying why. Stdlib only.
"""
import argparse
import datetime
import os
import re
import sys

# One profile per desk. Another desk adopts this by adding a profile, not a second script.
DESKS = {
    "ca-state": {
        "tree": "All RFQ's by Agency",
        "file": "LEARNED.md",
        # Levels a rep may write to directly, counted in folders below the tree folder.
        # Depth 1 is an agency, depth 0 the whole desk: those change by Parker's ruling.
        "rep_min_depth": 2,
    },
}
KINDS = ("preference", "change", "watch-out")
MAX_TEXT = 200
MAX_AUTHOR = 60
DEAL = re.compile(
    r"^\s*[0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})(?![0-9])"
    r"|[ _-][0-9]{1,2}\.[0-9]{1,2}\.(?:[0-9]{2}|[0-9]{4})\s*$"
    r"|[ _-][0-9]{4}-[0-9]{2}-[0-9]{2}\s*$")
HEADER = [
    "# Learned here",
    "",
    "One line per thing a BBS rep asked Claude to remember for this folder and the folders",
    "under it. Add a line by telling Claude \"remember that ...\"; do not paste email or web",
    "text here. Never a price, stock level, lead time, account number, certification or",
    "contract fact: those live in Business Central, the Grainger connector and the vendor",
    "profile. Format: `- date | who said it | kind | what`.",
    "",
]
# What memory may not hold. Each is (pattern, the plain reason given to the rep).
REFUSE = [
    (re.compile(r"[$€£]\s*[0-9]|[0-9]\s*(?:dollars|usd)\b"
                r"|[0-9]\s*%\s*(?:off|discount|margin|mark-?up)|(?:discount|margin|mark-?up)[^.]{0,20}[0-9]\s*%", re.I),
     "it has a price, discount or margin in it. Prices live in Business Central and the Grainger "
     "connector; say where the number is recorded instead (for example the quote number)"),
    (re.compile(r"(?<![0-9])[0-9]{7,}(?![0-9])"),
     "it has a long number in it that could be an account or contract number. Those are "
     "not kept in memory; name the record that holds it instead"),
    (re.compile(r"\b[0-9]-[0-9]{2}-[0-9]{2}-[0-9]{2}\b|\b(?:dvbe|sdvosb|osds|uei|fein|gsa|naspo|lpa|sourcewell)\b[^.]{0,20}[0-9]{3,}", re.I),
     "it states a certification or contract number. Those come from the vendor profile and "
     "canonical facts, never from memory"),
    (re.compile(r"\b(?:password|passcode|api key|token|login)\b", re.I),
     "it looks like a credential. Credentials are never written down here"),
]
# Pointers at a record are welcome ("see SQ-104032"); they are removed before the checks above.
POINTER = re.compile(r"\b(?:SQ|SO|INVP|PO)-?[0-9]{4,}\b", re.I)
# The line format. hooks/desk-memory.py and .ps1 carry the same pattern; test_desk_memory.py
# fails when they differ.
ENTRY = re.compile(
    r"^- ([0-9]{4}-[0-9]{2}-[0-9]{2}) \| ([^|]{1,60}) \| (preference|change|watch-out) \| ([^|]{1,300})"
    r"( \| wider: [^|]{1,120})?$")


class Refused(Exception):
    pass


def split_path(p):
    return [c for c in re.split(r"[\\/]+", p) if c != ""]


def find_desk(path):
    """(profile, tree_dir, components below the tree) or raise Refused."""
    full = os.path.abspath(path)
    for name, prof in DESKS.items():
        m = None
        for hit in re.finditer(re.escape(prof["tree"]), full, re.I):
            a, b = hit.start(), hit.end()
            if (a == 0 or full[a - 1] in "/\\") and (b == len(full) or full[b] in "/\\"):
                m = hit
                break
        if m:
            return prof, full[:m.end()], split_path(full[m.end():])
    raise Refused("that folder is not inside a customer desk this skill knows, so nothing was saved")


def levels(path):
    """Folders a line could be saved to, nearest first: [(number, dir, name, depth, rep_ok)]."""
    prof, tree_dir, comps = find_desk(path)
    sep = os.sep
    # Keep only folders that exist, and stop above the first dated deal folder.
    dirs = []
    d = tree_dir
    for c in comps:
        if c.startswith(".") or DEAL.search(c):
            break
        nxt = d + sep + c
        if not os.path.isdir(nxt):
            break
        d = nxt
        dirs.append((d, c))
    out = []
    n = 1
    for depth in range(len(dirs), 0, -1):
        dd, name = dirs[depth - 1]
        out.append((n, dd, name, depth, depth >= prof["rep_min_depth"]))
        n += 1
    out.append((n, tree_dir, "the whole desk", 0, False))
    return prof, out


def check_text(text):
    if "\n" in text or "\r" in text:
        raise Refused("it is more than one line. One thing per line; say it in one sentence")
    t = " ".join(text.split())
    if not t:
        raise Refused("there was nothing to save")
    if len(t) > MAX_TEXT:
        raise Refused(f"it is {len(t)} characters and the limit is {MAX_TEXT}. Shorten it to one plain sentence")
    if "|" in t:
        raise Refused("it has a | character in it, which the file uses to separate columns. Reword without it")
    if any(ord(ch) < 32 or ord(ch) > 0xFFFF for ch in t):
        raise Refused("it has a character the file cannot hold (an emoji or a control character). Reword in plain text")
    probe = POINTER.sub("", t)
    for pat, why in REFUSE:
        if pat.search(probe):
            raise Refused(why)
    return t


def check_author(author):
    a = " ".join((author or "").split())
    if not a or len(a) > MAX_AUTHOR or "|" in a or any(ord(ch) < 32 or ord(ch) > 0xFFFF for ch in a):
        raise Refused("a line needs the name of the BBS person who said it, and none was given")
    if a.lower() in ("claude", "assistant", "ai", "buyer", "customer", "unknown", "rep"):
        raise Refused("a line needs the name of the BBS person who said it; a role or 'Claude' is not a name")
    return a


def check_date(s):
    if not s:
        return datetime.date.today().isoformat()
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise Refused("the date must look like 2026-11-10")


def pick(lv, number, what):
    for row in lv:
        if row[0] == number:
            return row
    raise Refused(f"there is no {what} number {number} for that folder; run `where` to see the choices")


def cmd_where(args):
    _, lv = levels(args.at)
    for n, d, name, depth, rep_ok in lv:
        note = "" if rep_ok else "  [needs Parker: save lower and mark it wider]"
        print(f"{n}. {name}{note}")
        print(f"   {d}")
    return 0


def cmd_add(args):
    prof, lv = levels(args.at)
    n, d, name, depth, rep_ok = pick(lv, args.level, "level")
    if not rep_ok and not any(r[4] for r in lv):
        raise Refused("this folder is an agency or the whole desk, and a note there changes what every rep "
                      "under it is told, so it goes through Parker. Open the buyer's folder and save it there")
    if not rep_ok:
        raise Refused(f"a note for {name} changes what every rep under it is told, so it goes through "
                      "Parker. Save it for the nearest folder and mark it wider; it is listed for him at the next review")
    text = check_text(args.text)
    author = check_author(args.author)
    date = check_date(args.date)
    line = f"- {date} | {author} | {args.kind} | {text}"
    if args.wider is not None:
        wn, wd, wname, wdepth, _ = pick(lv, args.wider, "wider level")
        if wdepth >= depth:
            raise Refused("the wider folder has to be above the one the line is saved in")
        if "|" in wname or len(wname) > 120:
            raise Refused("that folder's name cannot be written on the line; save without --wider and tell Parker")
        line += f" | wider: {wname}"
    path = d + os.sep + prof["file"]
    new = not os.path.exists(path)
    existing = ""
    if not new:
        with open(path, "rb") as fh:
            existing = fh.read().decode("utf-8-sig", "replace")
        said = [m.group(4).strip().lower() for m in map(ENTRY.match, re.split(r"\r\n|\n|\r", existing)) if m]
        if text.lower() in said:
            print(f"Already there, nothing added: {path}")
            return 0
    # Append only: one short line, so a sync conflict between two reps costs one line.
    with open(path, "ab") as fh:
        if new:
            fh.write(("\n".join(HEADER) + "\n").encode("utf-8"))
        elif existing and not existing.endswith(("\n", "\r")):
            fh.write(b"\n")
        fh.write((line + "\n").encode("utf-8"))
    print(f"Saved for {name}: {path}")
    print(line)
    return 0


def cmd_show(args):
    here = os.path.dirname(os.path.abspath(__file__))
    hook = os.path.normpath(os.path.join(here, "..", "..", "..", "hooks", "desk-memory.py"))
    import json
    import subprocess
    p = subprocess.run([sys.executable, hook], capture_output=True,
                       input=json.dumps({"hook_event_name": "SessionStart", "cwd": os.path.abspath(args.at)}).encode("utf-8"))
    out = p.stdout.decode("utf-8", "replace")
    print(out if out.strip() else "Nothing is remembered for that folder yet.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Desk memory: one remembered line, in the right folder.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("where"); w.add_argument("--at", required=True); w.set_defaults(fn=cmd_where)
    a = sub.add_parser("add")
    a.add_argument("--at", required=True)
    a.add_argument("--level", type=int, required=True)
    a.add_argument("--author", required=True)
    a.add_argument("--kind", choices=KINDS, required=True)
    a.add_argument("--text", required=True)
    a.add_argument("--wider", type=int)
    a.add_argument("--date")
    a.set_defaults(fn=cmd_add)
    s = sub.add_parser("show"); s.add_argument("--at", required=True); s.set_defaults(fn=cmd_show)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Refused as r:
        print(f"Not saved: {r}.")
        return 2
    except OSError as e:
        print(f"Not saved: the file could not be written ({e.strerror or e}). Nothing was changed.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
