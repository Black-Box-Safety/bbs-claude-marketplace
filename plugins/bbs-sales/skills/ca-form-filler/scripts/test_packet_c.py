#!/usr/bin/env python3
"""test_packet_c.py — CDCR Packet C is assembled, filled through the vetted
engine, keeps the agency's values, and signs only under the limit.

Run it:
    python3 test_packet_c.py

The PDFs are built with PyMuPDF at test time from the form table's markers and
FORM_FIELDS' own IDs, so no state form is committed. To run the same flow on
real blanks, set BBS_BLANK_FORMS to a folder holding OBS4007C.pdf, Darfur.pdf,
CalRecycle74.pdf, OBS1000.pdf, PD843.pdf and STD204.pdf (the end-to-end test
uses them instead). Needs pymupdf; skips without it. Stdlib otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fill_packet_c as fpc  # noqa: E402

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

fcf = fpc._signing()
TABLE = fcf.load_form_table()
with open(fpc.VENDOR_PROFILE, encoding="utf-8") as _fh:
    VP = json.load(_fh)
LIMIT = VP["signature_delegation"]["limit_usd"]
REPS = {r["role"]: r for r in VP["authorized_representatives"]}
PARKER = REPS["sales_manager"]


def _synthetic(path, kind, prefill=None):
    """One page carrying `kind`'s markers and every FORM_FIELDS ID for it."""
    fmap = fpc.FORM_FIELDS[kind]
    doc = fitz.open()
    page = doc.new_page(height=1400)
    page.insert_text((30, 30), " ".join(TABLE[kind]["markers"]), fontsize=8)
    names = list(fmap.get("text", {})) + list(fmap.get("signer_fields", {}).values())
    names += [fmap["sign"][1]] + list((prefill or {}))
    y = 60
    for name in dict.fromkeys(names):
        w = fitz.Widget()
        w.field_name, w.rect = name, fitz.Rect(30, y, 400, y + 14)
        w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        if prefill and name in prefill:
            w.field_value = prefill[name]
        page.add_widget(w)
        y += 18
    for name in fmap.get("checks", {}):
        w = fitz.Widget()
        w.field_name, w.rect = name, fitz.Rect(420, y, 432, y + 12)
        w.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
        page.add_widget(w)
        y += 18
    w = fitz.Widget()
    w.field_name, w.rect = fmap["sign"][0], fitz.Rect(30, y, 300, y + 16)
    w.field_type = fitz.PDF_WIDGET_TYPE_SIGNATURE
    page.add_widget(w)
    doc.save(path)
    doc.close()


def _png(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 20), False)
    pix.clear_with(0)
    pix.save(path)


AGENCY = {"OBS RFQ 4007(C) - Solicitation": "CEN-26-0412",
          "OBS RFQ 4007(C) - Buyer Name": "T. Ryan Kemp"}
KINDS = ("OBS4007C", "Darfur", "CalRecycle74", "PD843", "STD204")


def _setup(d, total, signer=None, kinds=KINDS):
    blanks = os.environ.get("BBS_BLANK_FORMS")
    paths = []
    for kind in kinds:
        path = os.path.join(d, kind + ".pdf")
        if blanks:
            src = fitz.open(os.path.join(blanks, kind + ".pdf"))
            if kind == "OBS4007C":
                for p in src:
                    for w in p.widgets() or []:
                        if w.field_name in AGENCY:
                            w.field_value = AGENCY[w.field_name]
                            w.update()
            src.save(path)
            src.close()
        else:
            _synthetic(path, kind, AGENCY if kind == "OBS4007C" else None)
        paths.append(path)
    root = os.path.join(d, "Black Box Safety - MASTER")
    for r in REPS.values():
        if r.get("signature_image"):
            _png(fcf.resolve_sig_path(r["signature_image"], root))
    signer = signer or {"name": PARKER["name"], "title": PARKER["title"],
                        "email": PARKER["email"]}
    inp = {"product_summary": "MSA gas detector kit", "signature_date": "10.1.26",
           "rep": {"name": "Kim Quezon", "title": "Account Manager",
                   "email": REPS["rep_kim"]["email"]},
           "signer": signer, "quote_total_incl_tax": total, "quote_ref": "SQ-TEST",
           "master_root": root, "attachments": paths[1:]}
    ip = os.path.join(d, "inputs.json")
    with open(ip, "w") as fh:
        json.dump(inp, fh)
    return paths[0], ip, os.path.join(d, "out", "packet.pdf")


def _run(*argv):
    out, code = io.StringIO(), None
    real = sys.argv
    sys.argv = ["fill_packet_c.py", *argv]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            fpc.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = real
    return code, out.getvalue()


def _inspect(path):
    doc = fitz.open(path)
    stamped = [p.number + 1 for p in doc if any(
        img for img in p.get_images())]
    values = {w.field_name: w.field_value for p in doc for w in (p.widgets() or [])}
    pages = doc.page_count
    doc.close()
    return stamped, values, pages


def test_under_the_limit_assembles_fills_and_signs():
    if fitz is None:
        return
    with tempfile.TemporaryDirectory() as d:
        packet, ip, out = _setup(d, LIMIT - 0.01)
        code, text = _run(packet, ip, out)
        assert not code, (code, text)
        _stamped, values, _pages = _inspect(out)
        assert "Signatures stamped: 5" in text, text   # 4007(C), Darfur, CalRec, PD 843, STD 204
        assert "OBS1000       MISSING" in text and "GSPD05105     MISSING" in text, text
        assert values["OBS RFQ 4007(C) - Business Name"] == VP["business_identity"]["legal_name"]
        assert values["OBS RFQ 4007(C) - Buyer Name"] == "T. Ryan Kemp"     # agency's, kept
        assert values["OBS RFQ 4007(C) - Solicitation"] == "CEN-26-0412"
        assert "kept agency value" in text


def test_at_or_over_the_limit_or_no_total_writes_it_unsigned():
    if fitz is None:
        return
    for total in (LIMIT, LIMIT + 1, None, "TBD"):
        with tempfile.TemporaryDirectory() as d:
            packet, ip, out = _setup(d, total)
            code, text = _run(packet, ip, out)
            assert not code, (total, code)
            assert "SIGNATURES WITHHELD" in text, (total, text)
            assert text.count("⚑ SIGNATURE REQUIRED") == 5, (total, text)


def test_a_delegate_without_a_png_stops_with_nothing_written():
    if fitz is None:
        return
    kim = REPS["rep_kim"]
    with tempfile.TemporaryDirectory() as d:
        packet, ip, out = _setup(d, LIMIT - 0.01, signer={
            "name": kim["name"], "title": kim["title"], "email": kim["email"]})
        code, _text = _run(packet, ip, out)
        assert code and "MASTER/Signatures/" in str(code), code
        assert not os.path.exists(out)


def test_a_non_delegate_signer_gets_no_rep_stamps_but_jackson_still_signs():
    if fitz is None:
        return
    joyce = {"name": "Joyce Newell", "title": "POs", "email": "joyce@" +
             VP["contact"]["email"].rsplit("@", 1)[1]}
    with tempfile.TemporaryDirectory() as d:
        packet, ip, out = _setup(d, LIMIT - 0.01, signer=joyce)
        code, text = _run(packet, ip, out)
        assert not code, (code, text)
        assert "Signatures stamped: 2" in text, text            # PD 843 and STD 204
        assert text.count("not one of the six delegates") == 3, text


def test_not_a_packet_c_stops():
    if fitz is None:
        return
    with tempfile.TemporaryDirectory() as d:
        packet, ip, out = _setup(d, LIMIT - 0.01, kinds=("Darfur", "CalRecycle74"))
        code, _text = _run(packet, ip, out)
        assert code and "not a Packet C" in str(code), code
        assert not os.path.exists(out)


def test_form_fields_cover_every_signed_kind_in_the_table():
    signed = {k for k, v in TABLE.items() if v["line"]} - {"OBS4007B", "STD205"}
    assert signed <= set(fpc.FORM_FIELDS), signed - set(fpc.FORM_FIELDS)
    for kind, fmap in fpc.FORM_FIELDS.items():
        assert fmap["sign"][2] == TABLE[kind]["line"], kind


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
