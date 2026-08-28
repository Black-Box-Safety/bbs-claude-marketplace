#!/usr/bin/env python3
"""
mine_precedents.py — read the State of CA Agencies folder and emit what past
packets actually said.

The folder is the corpus: every prior RFQ has the blank forms the agency sent and,
usually, the filled versions BBS returned. That history answers the questions that
otherwise go back to the rep — which form revisions an agency uses, what BBS wrote
in a given field last time, which solicitation numbers are live, which Grainger
account belongs to which institution.

Run it after a batch of new RFQs to refresh `references/agency-registry.md` and
`references/filled-form-precedents.md`. It reads only; it writes JSON to stdout or
`--out`.

Usage:
    python mine_precedents.py "<path to State of CA Agencies>" --out /tmp/mine.json
    python mine_precedents.py "<path>" --since 2026-06-01     # recent packets only

Output JSON:
  form_counts        how many of each form type are in the corpus
  filled_values      {form type: {"field = value": times seen}} — the precedent table
  solicitations      solicitation/contract numbers found, with the files they came from
  accounts           {institution folder: Grainger account number from the folder name}
  contacts           buyer note files, parsed loosely
  unclassified       filenames that matched no known form (candidates for a new map)

Requires: pypdf
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import sys

try:
    import pypdf
except ImportError:
    sys.exit("pypdf required: pip install pypdf --break-system-packages -q")

FORM_SIGNATURES = [
    ("CalRecycle 74", ("CALRECYCLE", "POSTCONSUMER RECYCLED")),
    ("PD 843 DVBE Declaration", ("DISABLED VETERAN BUSINESS ENTERPRISE DECLARATION",
                                 "DGS PD 843", "STD. 843")),
    ("GSPD-05-105 Bidder Declaration", ("BIDDER DECLARATION",)),
    ("Darfur OBS 1500", ("DARFUR",)),
    ("OBS 1000 GenAI", ("GENERATIVE ARTIFICIAL",)),
    ("OBS Line-Item Cost Worksheet", ("LINE ITEM COST WORKSHEET", "LINE-ITEM COST")),
    ("STD 204 Payee Data Record", ("PAYEE DATA RECORD",)),
    ("STD 205 Payee Data Supplement", ("PAYEE DATA SUPPLEMENT",)),
    ("CV 012 Commercially Useful Function", ("COMMERCIALLY USEFUL FUNCTION",)),
    ("BBS Sales Quote", ("SALES QUOTE",)),
    ("Purchase Order", ("PURCHASE ORDER",)),
]

SOLICITATION_RE = re.compile(
    r"(?:NASPO[:\s]*|SOLICITATION\s*#?\s*|RFQ\s*#?\s*)([0-9]{1,2}-[0-9]{2}-[0-9]{2}-[0-9.]+|[0-9]{2}-[0-9]{2}-[0-9]{3})",
    re.I)
ACCOUNT_RE = re.compile(r"\b(88[0-9]{7})\b")


def classify(text_upper):
    for name, keys in FORM_SIGNATURES:
        if any(k in text_upper for k in keys):
            return name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out")
    ap.add_argument("--since", help="YYYY-MM-DD — only files modified on/after this")
    ap.add_argument("--max-mb", type=float, default=12.0,
                    help="skip PDFs larger than this (scanned catalogs, not forms)")
    args = ap.parse_args()

    cutoff = None
    if args.since:
        cutoff = dt.datetime.strptime(args.since, "%Y-%m-%d").timestamp()

    counts = collections.Counter()
    filled = collections.defaultdict(collections.Counter)
    solicitations = collections.defaultdict(set)
    unclassified = []
    accounts = {}
    contacts = {}

    for dirpath, _dirs, files in os.walk(args.root):
        m = ACCOUNT_RE.search(os.path.basename(dirpath))
        if m:
            accounts[os.path.basename(dirpath)] = m.group(1)

        for fname in files:
            path = os.path.join(dirpath, fname)
            rel = os.path.relpath(path, args.root)

            if fname.lower().endswith(".txt"):
                try:
                    contacts[rel] = open(path, errors="replace").read()[:1200]
                except OSError:
                    pass
                continue

            if not fname.lower().endswith(".pdf"):
                continue
            try:
                st = os.stat(path)
            except OSError:
                continue
            if cutoff and st.st_mtime < cutoff:
                continue
            if st.st_size > args.max_mb * 1024 * 1024:
                counts["skipped (too large)"] += 1
                continue

            try:
                reader = pypdf.PdfReader(path)
                text = (reader.pages[0].extract_text() or "")
            except Exception:
                counts["unreadable"] += 1
                continue

            kind = classify(text.upper())
            counts[kind or "unclassified"] += 1
            if not kind:
                unclassified.append(rel)

            for hit in SOLICITATION_RE.findall(text):
                solicitations[hit].add(rel)

            try:
                fields = reader.get_fields() or {}
            except Exception:
                fields = {}
            for key, spec in fields.items():
                val = spec.get("/V")
                if kind and val not in (None, "", "/Off"):
                    filled[kind][f"{key} = {val}"] += 1

    result = {
        "root": args.root,
        "form_counts": dict(counts),
        "filled_values": {k: dict(v) for k, v in filled.items()},
        "solicitations": {k: sorted(v)[:8] for k, v in solicitations.items()},
        "accounts": accounts,
        "contacts": contacts,
        "unclassified": unclassified,
    }
    text = json.dumps(result, indent=1, default=str)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"wrote {args.out}: {sum(counts.values())} PDFs, "
              f"{len(filled)} form types with filled values")
    else:
        print(text)


if __name__ == "__main__":
    main()
