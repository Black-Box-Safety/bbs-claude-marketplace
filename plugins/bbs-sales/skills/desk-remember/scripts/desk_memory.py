#!/usr/bin/env python3
"""Write one remembered line into the right LEARNED.md of a customer desk, or show what loads.

  where  --at PATH                      which folders a line could be saved to, nearest first
  add    --at PATH --level N --author NAME --kind KIND --text "..." [--wider N] [--date D]
                                        append one line to that folder's LEARNED.md
  show   --at PATH                      the lines a session opened at PATH would be given

--level and --wider are the numbers `where` prints (1 = the nearest folder). A dated deal folder
is never a level: what is true for one deal belongs in its RFQ.md, not in memory.

Refuses, and writes nothing, when the text holds what belongs to a system of record, a contact
detail or a secret (REFUSE_TABLE: prices, stock and lead times, certification and small-business
or preference claims, account and contract numbers, phone numbers and email addresses,
credentials), when it tells Claude to get around a review or approval, when it is more than one
line, or when the level needs Parker.

Importable: another desk or plugin may reuse ENTRY, REFUSE_TABLE, POINTER_PATTERN, check_text and
check_author rather than build a second mechanism.
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
# What memory may not hold, as (pattern, the plain reason given to the rep). The patterns are
# plain strings valid in Python and .NET regex: hooks/desk-memory.py and desk-memory.ps1 carry
# the same list (and POINTER) and withhold a matching line on read; test_desk_memory.py fails
# when the three differ. They are applied to the statement after POINTER is removed.
# The table is a floor that catches the obvious phrasings, not the control: prices, signers and
# certifications are enforced by the deterministic gates in the quote and form scripts. Widen
# it by meaning (a category), not by chasing every phrasing.
REFUSE_TABLE = [
    (r"(?i)[$\u20AC\u00A3]\s*[0-9]|[0-9]\s*(?:dollars|usd|cents)\b|\b[0-9]+\.[0-9]{2}\b|\b[0-9]+(?:\.[0-9]+)?\s*(?:per|/|a|an|each)\s*(?:box|case|each|unit|pair|pack|pk|bx|cs|dozen|dz|roll|item|ea)\b|[0-9]\s*%\s*(?:off|discount|margin|mark-?up)|\b(?:discount|margin|mark-?up|price[ds]?|costs?|priced)\b[^.]{0,20}[0-9]",
     "it has a price, discount or margin in it. Prices live in Business Central and the Grainger connector; say where the number is recorded instead (for example the quote number)"),
    (r"(?i)\bmark\s?-?\s?ups?\b|\bmarked\s+up\b|\bmargins?\b|\bdiscount(?:s|ed)?\b|\b(?:sell|charge|bill|quote|price)\w*\b[^.]{0,30}\b(?:at|for)\s+(?:about\s+|around\s+|roughly\s+)?(?:[0-9]|one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)|\b(?:dollars?|bucks|cents)\b|\b(?:mark|bump|raise|add)\w*\b[^.]{0,30}\b(?:percent|per\s*cent)\b",
     "it sets a price rule (a markup, margin, discount or sell price) or names an amount. Price rules come from Business Central, the contract and the rep on each quote, never from a note"),
    (r"(?i)\b(?:grainger|cost|list\s+price)\b[^.]{0,20}(?:\+|\bplus\b)|\badd\w*\b[^.]{0,15}[0-9]+\s*(?:%|percent|points?)|\b(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:%|percent|points?)\s+(?:over|above|under|below|on\s+top\s+of)\b|\bon\s+top\s+of\s+(?:the\s+)?(?:grainger|cost|list)\b",
     "it sets a markup over Grainger or cost. Grainger sell rules depend on the channel and are applied by the rep on each quote, never by a note"),
    (r"(?i)\b(?:grainger|cost)\b[^.]{0,40}?\b[0-9]+(?:\.[0-9]+)?\s*(?:%|percent|per\s*cent|points?)|\b[0-9]+(?:\.[0-9]+)?\s*(?:%|percent|per\s*cent|points?)?\s+(?:over|above|higher|more|uplift)\b[^.]{0,30}\b(?:grainger|cost)\b|\b[0-9]+(?:\.[0-9]+)?\s*(?:%|percent|per\s*cent|points?)?\s+(?:over|above|higher|more)\s+(?:than\s+)?(?:grainger|cost)\b|\bgrainger\b[^.]{0,20}\btimes\b|\buplift\b|(?:%|percent|per\s*cent)\s+(?:goes\s+)?on\s+top\b|\b(?:full|at)\s+list\b[^.]{0,30}\bgrainger\b|\bgrainger\b[^.]{0,30}\b(?:full|at)\s+list\b",
     "it sets a markup over Grainger or cost. Grainger sell rules depend on the channel and are applied by the rep on each quote, never by a note"),
    (r"(?i)\bbuck\b",
     "it sets a price rule (a markup, margin, discount or sell price) or names an amount. Price rules come from Business Central, the contract and the rep on each quote, never from a note"),
    (r"(?i)\blead[- ]?times?\b|\bin[- ]stock\b|\bout[- ]of[- ]stock\b|\bback[- ]?order(?:ed|s)?\b|\bon[- ]hand\b|\bstock(?:ed)?\s+(?:level|levels|is|are|of|at)\b|\bships?\s+in\s+[0-9]+|\b[0-9]+\s*(?:-\s*[0-9]+\s*)?(?:business\s+)?(?:days?|weeks?)\s+(?:lead|to\s+ship|ARO|turnaround)\b|\bARO\b",
     "it states stock or a lead time. Those change daily and come from the Grainger connector, Business Central or the vendor's quote, never from a note"),
    (r"(?i)\bon\s+(?:the\s+)?shel(?:f|ves)\b|\bavailable\s+now\b|\b[0-9]+\s+(?:in\s+stock|on\s+hand|available)\b|\btakes?\s+(?:about\s+|around\s+|roughly\s+)?(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|a\s+few|a\s+couple(?:\s+of)?|several)\s+(?:business\s+)?(?:days?|weeks?|months?)\b|\b(?:days?|weeks?)\s+(?:after|from|of)\s+(?:the\s+)?(?:PO|order|award|receipt)\b|\bdeliver(?:s|ed|y|ies)?\s+(?:in|within)\s+(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|a\s+few|a\s+couple(?:\s+of)?|several)\b|\b(?:lands?|arrives?|ships?)\s+(?:in|within)\s+(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|a\s+few|a\s+couple(?:\s+of)?|several)\s+(?:business\s+)?(?:days?|weeks?)\b",
     "it states stock or a lead time. Those change daily and come from the Grainger connector, Business Central or the vendor's quote, never from a note"),
    (r"(?i)\b(?:small[- ]business(?:es)?|DVBE|SDVOSB|VOSB|OSDS|DOBE|SLBE|SBE|MBE|WBE|micro[- ]?business)\b|\bSB\b|\bcertified\b|\bcertifications?\b|\b(?:SB|DVBE|bid|price|small[- ]business|veteran|5\s*%)\s+(?:preferences?|incentives?)\b|\bpreference\s+(?:points?|percent|program|claim)\b|\bincentives?\b",
     "it says something about a certification, small-business status or a bid preference. Those come from the vendor profile and canonical facts, never from a note"),
    (r"(?i)\bS\s?\.\s?B\b\.?|\bS\s+B\b|\b(?:5|five)\s*(?:%|percent|per\s*cent|pct)|\b(?:bump|credit|boost|bonus|preference)\b[^.]{0,20}(?:%|percent|per\s*cent)|(?:%|percent|per\s*cent)[^.]{0,20}\b(?:bump|credit|boost|bonus|preference)\b|\bqualif\w*\b[^.]{0,30}\b(?:preference|bump|credit|incentive|set-?aside)\b",
     "it says something about a certification, small-business status or a bid preference. Those come from the vendor profile and canonical facts, never from a note"),
    (r"(?i)\bsmall\s+biz\b|\bS\s?-\s?B\b|\bdisabled\s+veteran|\bstate\s+preference|\bveteran-?\s?owned\b",
     "it says something about a certification, small-business status or a bid preference. Those come from the vendor profile and canonical facts, never from a note"),
    (r"(?i)\bpre-?\s?approv\w*|\bauthori[sz](?:ed|es|ing|ation)\b|\bsign-?\s?offs?\b|\bimplied\b[^.]{0,25}\b(?:approv\w*|consent|ok|okay)\b|\b(?:approv\w*|consent)\b[^.]{0,25}\bimplied\b|\bon\s+behalf\s+of\b|\bsign\s+(?:\w+(?:\x27|\u2019)s?\s+|the\s+|their\s+|his\s+|her\s+)?(?:line|lines|signature\s+block|block|name)\b|\bsign\s+\w+(?:\x27|\u2019)s\b|\bsign\s+for\b|\b(?:treat|count|take|consider|accept)\w*\b[^.]{0,50}\bas\b[^.]{0,30}\b(?:approv\w*|sign-?\s?off|authori[sz]ation|consent|go-?ahead)\b",
     "it reads as an approval, a sign-off, or authority to sign or act for someone. A note never grants approval and never changes a signer; that comes from the person, each time"),
    (r"(?i)\bsigns?\b[^.]{0,20}\bfor\s+(?:him|her|them|jackson|parker|griffin|the\s+rep|the\s+buyer|\w+(?:\x27|\x60)s)\b|\bokay(?:ed|s)\b|\bok(?:ed|\x27d)\b|\bgreen-?\s?lit\b|\bgreen\s+light\b|\bgood\s+to\s+go\b|\bsaid\s+yes\b[^.]{0,20}\b(?:quote|price|markup|order|bid|send|sending|commit|approval)",
     "it reads as an approval, a sign-off, or authority to sign or act for someone. A note never grants approval and never changes a signer; that comes from the person, each time"),
    (r"(?i)\b(?:skip|skipping|ignore|ignoring|bypass|override|disable|waive|drop)\b[^.]{0,40}\b(?:reviews?|approvals?|sign-?offs?|signatures?|checks?|forms?|rules?|instructions?|permissions?|gates?|allow)\b|\bno\s+need\s+(?:for|to)\b[^.]{0,30}\b(?:reviews?|approvals?|sign-?offs?|check)|\b(?:commit|send|submit|post|release|sign)\w*\b[^.]{0,30}\bwithout\s+(?:a\s+|the\s+|any\s+)?(?:reviews?|approvals?|sign-?offs?|asking|checking|permission)|\b(?:directly|automatically)\s+(?:commit|send|submit|post|release)\w*|\b(?:commit|send|submit|post|release)\w*\s+(?:the\s+)?(?:quotes?\s+|bids?\s+|packets?\s+)?(?:directly|automatically|straight)\b",
     "it tells Claude to skip or get around a review, approval, form or signature. That is not a memory; a change like that needs Parker"),
    (r"(?i)[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}|(?<![0-9])\(?[0-9]{3}\)?\s?[-. ]?[0-9]{3}[-. ][0-9]{4}(?![0-9])|\b[A-Za-z0-9._-]+\s*(?:\s+at\s+|\(at\)|\[at\])\s*[A-Za-z0-9-]+(?:\s*(?:\s+dot\s+|\(dot\)|\[dot\])\s*[A-Za-z0-9-]+)+\b",
     "it has an email address or phone number in it. Contact details belong in the buyer's CLAUDE.md header, where they are kept current; say what changed instead"),
    (r"(?<![0-9])[0-9]{7,}(?![0-9])",
     "it has a long number in it that could be an account or contract number. Those are not kept in memory; name the record that holds it instead"),
    (r"(?i)\b[0-9]-[0-9]{2}-[0-9]{2}-[0-9]{2}\b|\b(?:uei|fein|gsa|naspo|lpa|sourcewell|cage)\b[^.]{0,20}[0-9]{3,}",
     "it states a contract or registration number. Those come from the vendor profile and canonical facts, never from a note"),
    (r"(?i)\b(?:password|passcode|api\s+key|token|login|username)\b",
     "it looks like a credential. Credentials are never written down here"),
]
REFUSE = [(re.compile(p), why) for p, why in REFUSE_TABLE]
# Pointers at a record are welcome ("see SQ-104032"); they are removed before the checks above.
POINTER_PATTERN = r"(?i)\b(?:SQ|SO|INVP|PO)-?[0-9]{4,}\b"
POINTER = re.compile(POINTER_PATTERN)
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
