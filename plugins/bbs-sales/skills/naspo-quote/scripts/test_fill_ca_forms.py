#!/usr/bin/env python3
"""test_fill_ca_forms.py — a missing signature image stops the run before any PDF.

Run it:
    python3 test_fill_ca_forms.py

AGENTS.md invariant 4: a packet must never look signed when a signature could not
be applied, and a run must never skip a signer silently. `check_signatures()` runs
before fitz opens anything, so these tests exercise it (and `main()`'s exit) with
no pymupdf installed and no real form PDF. They do not cover the stamping itself.

Stdlib only, no pytest, so it runs wherever the plugin is installed.
"""
import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fill_ca_forms  # noqa: E402
from fill_ca_forms import SignatureMissing, check_signatures  # noqa: E402


def _form(who="parker", src="CalRecycle- Form 74 (01-2023).pdf"):
    return {"src": src, "out": "x.pdf", "sign": {"Signature": {"who": who}}}


def _raises(forms, sigs):
    try:
        check_signatures(forms, sigs)
    except SignatureMissing as e:
        return str(e)
    raise AssertionError("expected SignatureMissing")


def test_missing_file_names_signer_and_path():
    path = os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "parker-signature.png")
    msg = _raises([_form()], {"parker": path})
    assert "signature image for parker not found at " + path in msg, msg
    assert "leave the line unsigned for the rep" in msg, msg


def test_signer_absent_from_spec():
    msg = _raises([_form(who="jackson")], {"parker": __file__})
    assert "signature image for jackson not given" in msg, msg


def test_every_form_checked_not_just_the_first():
    with tempfile.NamedTemporaryFile(suffix=".png") as ok:
        forms = [_form("parker"), _form("jackson", src="DGS PD 843.pdf")]
        msg = _raises(forms, {"parker": ok.name, "jackson": "/nope/JACKSON_SIG.png"})
        assert "jackson" in msg and "DGS PD 843.pdf" in msg, msg
        assert "parker" not in msg.split("Fix the path")[0], msg


def test_present_files_pass_and_unsigned_forms_need_nothing():
    with tempfile.NamedTemporaryFile(suffix=".png") as ok:
        check_signatures([_form(), {"src": "a.pdf", "out": "a.pdf"}], {"parker": ok.name})
    check_signatures([{"src": "a.pdf", "out": "a.pdf"}], {})


def test_main_exits_before_writing_anything():
    with tempfile.TemporaryDirectory() as d:
        out_dir = os.path.join(d, "out")
        spec = {"src_dir": d, "out_dir": out_dir,
                "signatures": {"parker": os.path.join(d, "gone.png")},
                "forms": [{"src": "a.pdf", "out": "a.pdf"}, _form()]}
        spec_path = os.path.join(d, "spec.json")
        with open(spec_path, "w") as fh:
            json.dump(spec, fh)
        argv = sys.argv
        sys.argv = ["fill_ca_forms.py", spec_path]
        try:
            fill_ca_forms.main()
        except SystemExit as e:
            assert "STOP: signature image for parker not found at" in str(e.code), e.code
        else:
            raise AssertionError("main() did not stop")
        finally:
            sys.argv = argv
        assert not os.path.exists(out_dir), "output directory created before the check"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
