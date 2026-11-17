#!/usr/bin/env python3
"""bc_quote_pdf.py - fetch Business Central's own PDF of a RELEASED sales quote into a deal folder.
Read-only: it reads BC and writes one local file. It never changes a quote.

    python3 bc_quote_pdf.py fetch <SQ-number> --out <deal folder> [--institution <name>]
                                 [--released-confirmed-by "<rep name>"] [--account <user@blackboxsafety.com>]

Why it exists: a rep releases a quote in BC, which is where tax is calculated, and prints it; BC's
print is the only customer document (there is no Claude-rendered copy of a quote). The desk can now
fetch that same document so the rep gets it next to the filled packet. The rep still proofs it
(DVBE 2009473 only, and tax) and still sends it; this script sends nothing and prints nothing in BC.

The one BC call that matters is Microsoft's documented API v2.0 navigation
    GET .../companies({id})/salesQuotes({id})/pdfDocument
    GET .../companies({id})/salesQuotes({id})/pdfDocument/pdfDocumentContent      (the PDF bytes)
(learn.microsoft.com .../api-reference/v2.0/resources/dynamics_pdfdocument). If either answers
anything but 200 the script stops and says so; it tries no other path.

Release gate. A Draft quote's PDF has no tax and is not the customer document, so a quote is refused
unless BC shows it was released. The catch, recorded in bbs-claude-marketplace memory bc-write-path
(seen 2026-10-16 on SQ-105183): the API's `status` field reads "Draft" even when the header is
Released, so the API alone cannot prove release. Therefore: status Sent or Accepted passes; status
Draft is refused UNLESS a named rep states the quote is released (--released-confirmed-by "<name>",
which is Parker's own "printed SQ-xxxxxx" text); Expired and anything unknown are refused. The
quote's tax and total are printed beside the file either way so the proof is easy, and a zero tax
amount is called out.

Connection, delegated sign-in, HTTP helpers and the token cache are IMPORTED from the sibling skill
(bc-item-entry/scripts/bc_item_entry.py) exactly as bc_quote_entry.py imports them: one connection
file, one cache, one error table. No secret, no app-only default (an app-only setting is refused here).

GET only. No other HTTP method exists in this file, ReadOnlyBC refuses the sibling's write helpers,
and test_bc_quote_pdf.py asserts both. Stdlib only, except msal through the import. Never prints a
secret or an auth token.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "bc-item-entry", "scripts")
if ITEM_SCRIPTS not in sys.path:
    sys.path.insert(0, ITEM_SCRIPTS)
try:
    import bc_item_entry as item  # noqa: E402  the sibling skill, same plugin
except ImportError:
    print(f"\nSTOP at import: this skill reuses bc_item_entry.py from the bc-item-entry skill in the same "
          f"plugin, expected at {ITEM_SCRIPTS}. Both ship in bbs-sales; reinstall the plugin.")
    sys.exit(1)

die, explain_error, odq, qp, http_fail, norm = item.die, item.explain_error, item.odq, item.qp, item.http_fail, item.norm

RELEASED_STATUSES = ("Sent", "Accepted")      # API statuses that can only follow a release
REFUSED_STATUSES = ("Expired",)
DRAFT = "Draft"
PDF_MAGIC = b"%PDF-"
MAX_BYTES = 25 * 1024 * 1024                  # a quote PDF is tens of KB; refuse anything absurd


def normalize_sq(text):
    """'sq-105183', 'SQ 105183' and '105183' all mean SQ-105183. Anything else is refused."""
    m = re.fullmatch(r"(?:SQ[\s-]*)?(\d{4,})", str(text or "").strip(), re.I)
    if not m:
        die("quote number", f"{text!r} is not a sales quote number like SQ-105183.")
    return f"SQ-{m.group(1)}"


def file_part(text):
    """A file-name-safe piece: letters and digits, runs of anything else become one underscore."""
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text or "")).strip("_")


def target_path(folder, institution, sq):
    """<folder>/<Institution>_Quote_<SQ>.pdf. The folder must already exist: folder names carry
    buying-account numbers, so this never creates or renames one."""
    if not os.path.isdir(folder):
        die("output folder", f"{folder!r} is not an existing folder. Nothing is created; point --out at the deal folder.")
    inst = file_part(institution)
    if not inst:
        die("file name", "no institution name to put in the file name; pass --institution.")
    return os.path.join(folder, f"{inst}_Quote_{sq}.pdf")


def release_gate(quote, confirmed_by=None):
    """Returns (ok, [notes]). Refuses a quote BC does not show as released, and says why."""
    status = norm(quote.get("status"))
    if status in RELEASED_STATUSES:
        return True, [f"BC status is {status}, which only follows a release."]
    if status in REFUSED_STATUSES:
        return False, [f"status is {status}: an expired quote is not the document to send. The rep re-issues it in BC."]
    if status == DRAFT:
        rep = str(confirmed_by or "").strip()
        if rep:
            return True, [f"BC's API reads Draft even for a released quote (SQ-105183, 2026-10-16), so release rests on "
                          f"{rep}'s statement that it is released. The tax shown below is the check."]
        return False, ["the API status is Draft. A Draft quote's PDF has no tax and is not the customer document. "
                       "The API also reads Draft for a quote that IS released, so it cannot tell. Have the rep release "
                       "it in BC and say so (--released-confirmed-by \"<rep name>\"); if it is not released yet, the "
                       "rep releases it in BC first."]
    return False, [f"status {status!r} is not one this script knows; refusing rather than guessing."]


class ReadOnlyBC(item.BC):
    """The sibling's connection and delegated sign-in with every write helper switched off."""

    def __init__(self, account=None):
        if os.environ.get("BBS_BC_AUTH", "").strip().lower() not in ("", "delegated"):
            die("auth", "this script runs under the rep's own sign-in only; unset BBS_BC_AUTH.")
        super().__init__(account=account)

    def post(self, url, body):                       # the sibling's helpers, refused
        raise RuntimeError("bc_quote_pdf.py is read-only")

    def patch(self, url, etag, body):
        raise RuntimeError("bc_quote_pdf.py is read-only")

    def get_bytes(self, url):
        """GET a binary stream. Returns (status, bytes, content-type); on an error status the bytes are the body."""
        req = urllib.request.Request(url, method="GET", headers={**self.auth, "Accept": "application/pdf, */*"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read(MAX_BYTES + 1)
                return r.status, data, r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, e.read()[:600], e.headers.get("Content-Type", "")
        except urllib.error.URLError as e:
            die("network", str(e))

    def quote_by_number(self, sq):
        st, body = self.get(f"{self.api}/salesQuotes?" + qp(
            f"number eq '{odq(sq)}'",
            select="id,number,status,customerNumber,customerName,externalDocumentNumber,documentDate,"
                   "totalAmountExcludingTax,totalTaxAmount,totalAmountIncludingTax"))
        if st != 200:
            http_fail("quote lookup", st, body)
        rows = body.get("value") or []
        return rows[0] if rows else None


def check_pdf_document(bc, qid):
    """Proves the documented navigation exists for this quote and belongs to it. Stops, never improvises."""
    st, body = bc.get(f"{bc.api}/salesQuotes({qid})/pdfDocument")
    if st != 200:
        hint = explain_error(json.dumps(body) if not isinstance(body, str) else body, st)
        die("pdfDocument", f"salesQuotes({qid})/pdfDocument answered HTTP {st}: {json.dumps(body)[:300]}"
            + (f"\n  {hint}" if hint else "") + "\n  No other path is tried. Report this to Parker; the rep prints from BC.")
    doc = body.get("value", [body])[0] if isinstance(body, dict) and "value" in body else body
    parent = norm((doc or {}).get("parentId")).lower()
    if parent and parent != str(qid).lower():
        die("pdfDocument", f"the pdfDocument names parent {parent}, not quote {qid}; refusing to save it.")
    return doc


def fetch_pdf(bc, qid):
    st, data, ctype = bc.get_bytes(f"{bc.api}/salesQuotes({qid})/pdfDocument/pdfDocumentContent")
    if st != 200:
        text = data.decode(errors="replace") if isinstance(data, bytes) else str(data)
        hint = explain_error(text, st)
        die("pdfDocumentContent", f"HTTP {st}: {text[:300]}" + (f"\n  {hint}" if hint else ""))
    if len(data) > MAX_BYTES:
        die("pdfDocumentContent", f"the response is over {MAX_BYTES} bytes; not a quote PDF.")
    if not data.startswith(PDF_MAGIC):
        die("pdfDocumentContent", f"the response is not a PDF (content type {ctype!r}, {len(data)} bytes); nothing saved.")
    return data


def cmd_fetch(args):
    sq = normalize_sq(args.number)
    folder = os.path.abspath(os.path.expanduser(args.out))
    bc = ReadOnlyBC(account=args.account)
    quote = bc.quote_by_number(sq)
    if not quote:
        die("quote lookup", f"no sales quote {sq} in Business Central. Nothing fetched.")
    print(f"[quote] {quote.get('number')} for {quote.get('customerNumber')} {quote.get('customerName')!r}, "
          f"status {norm(quote.get('status'))}, external doc {quote.get('externalDocumentNumber')!r}")
    ok, notes = release_gate(quote, args.released_confirmed_by)
    for n in notes:
        print(f"[release] {n}")
    if not ok:
        die("release gate", "not fetched. Nothing was written.")
    institution = args.institution or quote.get("customerName")
    path = target_path(folder, institution, sq)
    if os.path.exists(path):
        die("output file", f"{path} already exists; not overwritten. Move it, or the rep decides.")
    check_pdf_document(bc, quote["id"])
    data = fetch_pdf(bc, quote["id"])
    with open(path, "xb") as fh:
        fh.write(data)
    print(f"[tax] excl tax {quote.get('totalAmountExcludingTax')}, tax {quote.get('totalTaxAmount')}, "
          f"incl tax {quote.get('totalAmountIncludingTax')} (BC's figures; the PDF is the document)")
    if not quote.get("totalTaxAmount"):
        print("[tax] FLAG: BC shows no tax on this quote. A released quote for a taxable ship-to carries tax; "
              "if this one should, it is probably still Draft. Do not send it until the rep has looked.")
    print(f"[saved] {path} ({len(data)} bytes)")
    print("[proof] Not sent, not printed in BC. The rep reads this PDF before it goes out: the certification line is "
          "DVBE 2009473 only (never SB, never SDVOSB) and tax is right (bc-quote-entry SKILL.md step 7, R5). A person sends.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="save BC's PDF of a released sales quote into the deal folder")
    f.add_argument("number", help="sales quote number, e.g. SQ-105183")
    f.add_argument("--out", required=True, help="the deal folder (must exist)")
    f.add_argument("--institution", default=None, help="name for the file; default the quote's customer name from BC")
    f.add_argument("--released-confirmed-by", default=None,
                   help="the rep who states the quote is released; needed because BC's API reads Draft for a released quote")
    f.add_argument("--account", default=None, help="cached sign-in to use when more than one is cached (or BBS_BC_ACCOUNT)")
    args = ap.parse_args()
    {"fetch": cmd_fetch}[args.cmd](args)


if __name__ == "__main__":
    main()
