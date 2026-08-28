#!/usr/bin/env python3
"""
scaffold_folder_context.py — give every agency and buyer folder in the State of CA
Agencies tree the two markdown files the quote desk reads first.

Why this exists: what we know about a buyer currently lives in a loose `<Name>.txt`
signature block, if it exists at all. That is unreadable to the pipeline and invisible
to the next rep. This turns each buyer folder into an ICM context layer — a CLAUDE.md
an agent reads on entry, and a quote-log.md that accumulates outcomes — seeded from the
notes already on disk so nobody retypes anything.

It never overwrites. A file that exists is left exactly as it is; run it as often as
you like. New buyer folders get scaffolded, old ones keep whatever a human wrote.

Usage:
    python scaffold_folder_context.py "<State of CA Agencies>/All RFQ's by Agency" --list
    python scaffold_folder_context.py "<...>/All RFQ's by Agency" --dry-run
    python scaffold_folder_context.py "<...>/All RFQ's by Agency" --write

Seeding: a buyer folder's `<Name>.txt` is parsed for email, phone, Grainger/Proco
account, and BC customer id. Anything it can't find is written as a `[TBD]` line rather
than omitted, because a visible gap gets filled and a missing field never does.
"""
import argparse
import os
import re
import sys

ACCOUNT_RE = re.compile(r"\b(0?88[0-9]{7})\b")
EMAIL_RE = re.compile(r"[\w.\-']+@[\w.\-]+\.\w+")
PHONE_RE = re.compile(r"\(?\d{3}\)?[ .\-]\d{3}[ .\-]\d{4}(?:\s*(?:ext\.?|x)\s*\d+)?", re.I)
BC_RE = re.compile(r"\bC1\d{4}\b")
DATEISH_RE = re.compile(r"\d")
PERSON_RE = re.compile(r"^[A-Z][A-Za-z'.\-]*(?:\s+\(?[A-Z][A-Za-z'.\-]*\)?){0,3}$")


def looks_like_person(name):
    """A buyer folder is a person's name; a deal folder carries a date or an item.

    The tree mixes them at the same depth, so the name is the only signal. Digits mean
    a date or a quantity, which means a deal folder — buyers never have them.
    """
    if DATEISH_RE.search(name):
        return False
    return bool(PERSON_RE.match(name.strip()))


TITLE_HINTS = ("analyst", "technician", "officer", "buyer", "purchasing", "coordinator",
               "manager", "specialist", "sergeant", "lieutenant", "supervisor", "agpa",
               "administrator", "sponsor", "clerk")


def parse_note(path):
    """Pull what we can out of a buyer's signature-block .txt."""
    try:
        text = open(path, errors="replace").read()
    except OSError:
        return {}
    out = {}
    if (m := EMAIL_RE.search(text)):
        out["email"] = m.group(0)
    if (m := PHONE_RE.search(text)):
        out["phone"] = m.group(0).strip()
    if (m := ACCOUNT_RE.search(text)):
        out["account"] = m.group(1).lstrip("0")
    if (m := BC_RE.search(text)):
        out["bc"] = m.group(0)
    for line in (l.strip() for l in text.splitlines()):
        if line and any(h in line.lower() for h in TITLE_HINTS) and len(line) < 70:
            out.setdefault("title", line)
    # a trailing address block: the last run of non-empty lines with no @ in them
    tail = [l.strip() for l in text.splitlines() if l.strip() and "@" not in l]
    if len(tail) >= 2:
        out["address_guess"] = ", ".join(tail[-3:]) + "  [parsed from the note — verify]"
    return out


def agency_context(agency, account, buyers):
    roster = "\n".join(f"- {b}" for b in buyers) if buyers else "- _none logged yet_"
    acct = f"`{account}`" if account else "[TBD — not in the folder name; check a buyer note]"
    return f"""# {agency}

**Grainger account:** {acct}
**Contract vehicle:** NASPO ValuePoint 07-25-51-02.3 (CA State Agency) unless an RFQ says otherwise
**Pricing rule:** at cost — customer price equals BBS cost, no markup

## Buyers

{roster}

## Standard cert packet

OBS Line-Item Cost Worksheet · CalRecycle 74 · DGS PD 843 · Darfur OBS 1500 ·
OBS 1000 GenAI · Bidder Declaration GSPD-05-105. Individual buyers add to this; note
additions in their CLAUDE.md rather than here.

## Agency-level notes

- _What holds for every buyer at this agency: procurement quirks, PO habits,
  delivery access, invoicing address. Leave empty rather than filling with generics._
"""


def buyer_context(buyer, agency, facts):
    def val(key, fallback="[TBD]"):
        return facts.get(key, fallback)
    return f"""# {buyer} — {agency}

**Role:** {val('title')}
**Reach:** {val('email')} · {val('phone')}
**Grainger account:** {val('account', '[TBD — inherit the agency folder unless a note says otherwise]')}
**BC customer:** {val('bc')}
**Ship to:** {val('address_guess')}

## How they buy

- Vehicle: [TBD — NASPO, DGS BPO, or competitive]
- Sends: [TBD — worksheet, bare email list, portal]
- Turnaround: [TBD]

## What we've learned

- _Add a line only when something surprised you: an equivalent they accepted, a form
  beyond the standard packet, a recycled-content answer they took, a deadline that was
  or wasn't real. Generic lines cost a read and return nothing._

## Open items

- [TBD] Confirm anything marked TBD above on the next contact.
"""


QUOTE_LOG = """# Quote log — {buyer}

| Date | Item | Quote # | Vehicle | Value | Outcome |
|---|---|---|---|---|---|

Outcome is `sent`, `won`, `lost`, or `no answer`. On a loss, add a clause on why —
that is the row the next quote learns from.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="path to \"All RFQ's by Agency\"")
    ap.add_argument("--write", action="store_true", help="create missing files")
    ap.add_argument("--dry-run", action="store_true", help="show what would be created")
    ap.add_argument("--list", action="store_true", help="print the tree and exit")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        sys.exit(f"not a directory: {args.root}")
    if not (args.write or args.dry_run or args.list):
        sys.exit("pass --list, --dry-run, or --write")

    planned, skipped = [], 0

    for agency in sorted(os.listdir(args.root)):
        apath = os.path.join(args.root, agency)
        if not os.path.isdir(apath):
            continue
        m = ACCOUNT_RE.search(agency)
        account = m.group(1).lstrip("0") if m else None
        buyers = sorted(d for d in os.listdir(apath) if os.path.isdir(os.path.join(apath, d)))

        if args.list:
            print(f"{agency}" + (f"  [{account}]" if account else ""))
            for b in buyers:
                print(f"    {b}")
            continue

        target = os.path.join(apath, "CLAUDE.md")
        if os.path.exists(target):
            skipped += 1
        else:
            planned.append((target, agency_context(agency, account, buyers)))

        for child in buyers:
            cpath = os.path.join(apath, child)
            grandkids = sorted(d for d in os.listdir(cpath)
                               if os.path.isdir(os.path.join(cpath, d)))

            if looks_like_person(child):
                # A buyer. Their subfolders are deal folders; we stop here.
                note = next((os.path.join(cpath, f) for f in os.listdir(cpath)
                             if f.lower().endswith(".txt")), None)
                facts = parse_note(note) if note else {}
                for name, body in (("CLAUDE.md", buyer_context(child, agency, facts)),
                                   ("quote-log.md", QUOTE_LOG.format(buyer=child))):
                    t = os.path.join(cpath, name)
                    if os.path.exists(t):
                        skipped += 1
                    else:
                        planned.append((t, body))
                continue

            # Not a person's name: an institution (CDCR prisons, CalVet homes, DSH
            # hospitals, Caltrans districts) whose children are the buyers — or a deal
            # folder that was filed one level too high, which we leave alone.
            child_buyers = [g for g in grandkids if looks_like_person(g)]
            if not child_buyers:
                continue

            sub_m = ACCOUNT_RE.search(child)
            sub_account = sub_m.group(1).lstrip("0") if sub_m else account
            t = os.path.join(cpath, "CLAUDE.md")
            if os.path.exists(t):
                skipped += 1
            else:
                planned.append((t, agency_context(f"{child} ({agency})",
                                                  sub_account, child_buyers)))

            for buyer in child_buyers:
                bpath = os.path.join(cpath, buyer)
                note = next((os.path.join(bpath, f) for f in os.listdir(bpath)
                             if f.lower().endswith(".txt")), None)
                facts = parse_note(note) if note else {}
                for name, body in (("CLAUDE.md", buyer_context(buyer, child, facts)),
                                   ("quote-log.md", QUOTE_LOG.format(buyer=buyer))):
                    t = os.path.join(bpath, name)
                    if os.path.exists(t):
                        skipped += 1
                    else:
                        planned.append((t, body))

    if args.list:
        return

    for path, body in planned:
        rel = os.path.relpath(path, args.root)
        if args.write:
            with open(path, "w") as f:
                f.write(body)
            print("created", rel)
        else:
            print("would create", rel)

    print(f"\n{len(planned)} to create, {skipped} left alone (already exist)")


if __name__ == "__main__":
    main()
