#!/usr/bin/env python3
"""test_mine_precedents.py — a pre-threshold SB claim never surfaces as a precedent.

Run it:
    python3 test_mine_precedents.py

Packets BBS filed while it was a California small business carry SB claims. They
were correct when filed (Parker, 2026-09-23) and must not reach a bid made today.
`mine_precedents.py` builds the precedent table a new fill copies from, so these
tests run its real `main()` over a fake corpus and assert the SB values land in
`historical_only` and nowhere in `filled_values`.

No real filled California PDF exists in this repo, and pypdf may not be installed,
so `pypdf.PdfReader` is replaced with a stub that serves each fake file's page text
and AcroForm values. That covers the routing, not pypdf's field extraction.

Stdlib only, no pytest, so it runs wherever the plugin is installed.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))

# name -> (page-0 text, {field: value}); filled in per test.
FAKE_CORPUS = {}


class _Page:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _Reader:
    def __init__(self, path):
        text, fields = FAKE_CORPUS[os.path.basename(path)]
        self.pages = [_Page(text)]
        self._fields = fields

    def get_fields(self):
        return {k: {"/V": v} for k, v in self._fields.items()}


sys.modules["pypdf"] = types.SimpleNamespace(PdfReader=_Reader)
sys.path.insert(0, HERE)
import mine_precedents  # noqa: E402

BIDDER = "STATE OF CALIFORNIA BIDDER DECLARATION GSPD-05-105"
OBS = "OBS RFQ 4007(B) LINE ITEM COST WORKSHEET"


def mine(corpus):
    """Run the real main() over a temp folder holding `corpus`; return its JSON."""
    FAKE_CORPUS.clear()
    FAKE_CORPUS.update(corpus)
    with tempfile.TemporaryDirectory() as root:
        for name in corpus:
            with open(os.path.join(root, name), "wb") as f:
                f.write(b"%PDF-1.4 stub\n")
        out = os.path.join(root, "mine.json")
        argv = sys.argv
        sys.argv = ["mine_precedents.py", root, "--out", out]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mine_precedents.main()
        finally:
            sys.argv = argv
        with open(out) as f:
            return json.load(f)


def all_keys(table):
    return {k for per_form in table.values() for k in per_form}


def test_sb_certification_text_is_historical_only():
    r = mine({
        "a.pdf": (BIDDER, {"Text1": "SB, DVBE"}),
        "b.pdf": (BIDDER, {"Text1": "DVBE, SB"}),
        "c.pdf": (BIDDER, {"Text1": "DVBE"}),
        "d.pdf": (BIDDER, {"Certification #": "SB/DVBE 2009473"}),
        "e.pdf": (BIDDER, {"Certification #": "DVBE 2009473"}),
    })
    current = all_keys(r["filled_values"])
    historical = all_keys(r["historical_only"])
    for bad in ("Text1 = SB, DVBE", "Text1 = DVBE, SB",
                "Certification # = SB/DVBE 2009473"):
        assert bad not in current, f"{bad!r} offered as a current precedent"
        assert bad in historical, f"{bad!r} dropped from the historical record"
    assert "Text1 = DVBE" in current
    assert "Certification # = DVBE 2009473" in current


def test_checked_sb_box_is_historical_only():
    r = mine({
        "obs1.pdf": (OBS, {"OBS RFQ 4007(B) - SB Checkbox": "/Yes",
                           "OBS RFQ 4007(B) - DVBE Checkbox": "/Yes",
                           "OBS RFQ 4007(B) - SB/MB/DVBE Cert#": "2009473"}),
        "obs2.pdf": (OBS, {"OBS RFQ 4007(B) - SB Checkbox": "/Off"}),
    })
    current = all_keys(r["filled_values"])
    assert not any("SB Checkbox" in k for k in current), current
    assert "OBS RFQ 4007(B) - SB Checkbox = /Yes" in all_keys(r["historical_only"])
    # DVBE box and the shared cert-number field are current, correct values.
    assert "OBS RFQ 4007(B) - DVBE Checkbox = /Yes" in current
    assert "OBS RFQ 4007(B) - SB/MB/DVBE Cert# = 2009473" in current


def test_small_business_wording_is_historical_only():
    r = mine({"f.pdf": (BIDDER, {"Text1": "Small Business / DVBE"})})
    assert not all_keys(r["filled_values"])
    assert "Text1 = Small Business / DVBE" in all_keys(r["historical_only"])


def test_lookalike_tokens_stay_current():
    # SBE / SLBE / SBA are not the California SB claim; do not over-strip them.
    for field, value in (("Local cert", "SLBE 17BB1659"), ("Note", "SBE"),
                         ("Note", "SBA size standard")):
        assert not mine_precedents.is_historical_sb_claim(field, value), value


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL  {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
