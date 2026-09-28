#!/usr/bin/env python3
"""test_fill_ca_forms.py — a signature that can't be applied means nothing is written.

Run it:
    python3 test_fill_ca_forms.py

AGENTS.md invariant 4: a packet must never look signed when a signature could not
be applied, and a run must never skip a signer silently. These tests cover the
pre-write checks (sign shape, MASTER/ path resolution, PNG header, blank-form
presence) and the all-or-nothing write in `main()`.

pymupdf may not be installed and no real California form PDF is in this repo, so
`main()` runs against a tiny fake `fitz` that serves widgets by name and records
stamps. That covers the control flow, not PyMuPDF's drawing.

Stdlib only, no pytest, so it runs wherever the plugin is installed.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fill_ca_forms  # noqa: E402
from fill_ca_forms import (  # noqa: E402
    PNG_MAGIC, SignatureMissing, check_signatures, preflight, resolve_sig_path)


# ---------- fixtures ----------

def _png(d, name="sig.png", data=PNG_MAGIC + b"rest-of-png"):
    path = os.path.join(d, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _form(who="parker", src="a.pdf", out="a-out.pdf", field="Signature"):
    return {"src": src, "out": out, "sign": {field: {"who": who}}}


def _raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except SignatureMissing as e:
        return str(e)
    raise AssertionError("expected SignatureMissing")


class _Rect:
    def __init__(self, x0=0, y0=0, x1=100, y1=20):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.width, self.height = x1 - x0, y1 - y0


class _Widget:
    def __init__(self, name):
        self.field_name, self.rect, self.xref = name, _Rect(), 0

    def update(self):
        pass


class _Page:
    def __init__(self, names):
        self._w = [_Widget(n) for n in names]
        self.stamps = []

    def widgets(self):
        return list(self._w)

    def delete_widget(self, w):
        self._w.remove(w)

    def insert_image(self, box, filename, overlay):
        self.stamps.append(filename)


class _Doc:
    def __init__(self, names):
        self.pages = [_Page(names)]

    def __iter__(self):
        return iter(self.pages)

    def save(self, path):
        with open(path, "wb") as fh:
            fh.write(b"%PDF-fake")

    def close(self):
        pass


class _FakeFitz:
    """Every blank form carries one field, 'Signature'."""
    Rect = _Rect

    class Pixmap:
        def __init__(self, path):
            self.width, self.height = 200, 50

    @staticmethod
    def open(path):
        return _Doc(["Signature"])


def _run_main(spec, d):
    """Run main() with the fake fitz. Returns (exit code or None, stderr)."""
    spec_path = os.path.join(d, "spec.json")
    with open(spec_path, "w") as fh:
        json.dump(spec, fh)
    argv, real = sys.argv, fill_ca_forms.fitz
    sys.argv, fill_ca_forms.fitz = ["fill_ca_forms.py", spec_path], _FakeFitz
    err = io.StringIO()
    code = None
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            fill_ca_forms.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv, fill_ca_forms.fitz = argv, real
    return code, err.getvalue()


def _spec(d, forms, signatures, **kw):
    for f in forms:
        _png(d, os.path.join("blank", f["src"]), b"%PDF-blank")
    spec = {"src_dir": os.path.join(d, "blank"), "out_dir": os.path.join(d, "out"),
            "signatures": signatures, "forms": forms}
    spec.update(kw)
    return spec


# ---------- missing signer / file (original cases) ----------

def test_missing_file_names_signer_and_path():
    path = os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "parker-signature.png")
    msg = _raises(check_signatures, [_form()], {"parker": path})
    assert "⚑ SIGNATURE REQUIRED — signature image for parker not found at " + path in msg, msg
    assert "leave the line unsigned for the rep" in msg, msg


def test_signer_absent_from_spec():
    msg = _raises(check_signatures, [_form(who="jackson")], {"parker": "/x.png"})
    assert "signature image for jackson not given" in msg, msg


def test_every_form_checked_not_just_the_first():
    with tempfile.TemporaryDirectory() as d:
        ok = _png(d)
        forms = [_form("parker"), _form("jackson", src="DGS PD 843.pdf")]
        msg = _raises(check_signatures, forms, {"parker": ok, "jackson": "/nope/J.png"})
        assert "jackson" in msg and "DGS PD 843.pdf" in msg, msg
        assert "parker" not in msg.split("Fix the path")[0], msg


def test_present_png_passes_and_unsigned_forms_need_nothing():
    with tempfile.TemporaryDirectory() as d:
        ok = _png(d)
        got = check_signatures([_form(), {"src": "b.pdf", "out": "b.pdf"}], {"parker": ok})
        assert got == {"parker": ok}, got
    assert check_signatures([{"src": "b.pdf", "out": "b.pdf"}], {}) == {}


# ---------- S1: MASTER/-relative paths ----------

def test_master_path_joined_onto_master_root():
    with tempfile.TemporaryDirectory() as root:
        rel = "MASTER/Jackson Dalton Signature/Copy of JACKSON_SIG.png"
        want = _png(root, os.path.join("Jackson Dalton Signature", "Copy of JACKSON_SIG.png"))
        assert resolve_sig_path(rel, root) == want
        got = check_signatures([_form("jackson")], {"jackson": rel}, master_root=root)
        assert got == {"jackson": want}, got


def test_master_path_without_master_root_stops():
    rel = "MASTER/Customers/x/parker-signature.png"
    msg = _raises(check_signatures, [_form()], {"parker": rel})
    assert "no `master_root`" in msg and rel in msg, msg


def test_old_ellipsis_and_relative_paths_stop():
    msg = _raises(check_signatures, [_form()], {"parker": ".../Customers/p.png"})
    assert "old '...' prefix" in msg, msg
    msg = _raises(check_signatures, [_form()], {"parker": "sigs/p.png"})
    assert "neither absolute nor" in msg, msg


def test_main_resolves_master_paths_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "Black Box Safety - MASTER")
        _png(root, os.path.join("Customers", "p.png"))
        spec = _spec(d, [_form()], {"parker": "MASTER/Customers/p.png"}, master_root=root)
        code, err = _run_main(spec, d)
        assert code is None, (code, err)
        assert os.path.isfile(os.path.join(d, "out", "a-out.pdf"))


# ---------- S2: bad image bytes, missing blank form, all-or-nothing ----------

def test_zero_byte_image_stops_and_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()], {"parker": _png(d, data=b"")})
        code, _ = _run_main(spec, d)
        assert "is empty (0 bytes)" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_non_png_image_stops_and_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()], {"parker": _png(d, "sig.jpg", b"\xff\xd8\xff\xe0JFIF..")})
        code, _ = _run_main(spec, d)
        assert "is not a PNG" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_missing_blank_form_stops_before_anything_is_written():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [{"src": "a.pdf", "out": "a.pdf"}], {})
        spec["forms"].append({"src": "never-downloaded.pdf", "out": "b.pdf"})
        msg = _raises(preflight, spec)
        assert "blank form not found" in msg and "never-downloaded.pdf" in msg, msg
        code, _ = _run_main(spec, d)
        assert code and "never-downloaded.pdf" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_failure_on_a_later_form_leaves_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [{"src": "a.pdf", "out": "a.pdf"}, _form(src="b.pdf")],
                     {"parker": _png(d)})

        class Boom(_FakeFitz):
            class Pixmap:
                def __init__(self, path):
                    raise RuntimeError("cannot decode image")

        spec_path = os.path.join(d, "spec.json")
        with open(spec_path, "w") as fh:
            json.dump(spec, fh)
        argv, real = sys.argv, fill_ca_forms.fitz
        sys.argv, fill_ca_forms.fitz = ["fill_ca_forms.py", spec_path], Boom
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fill_ca_forms.main()
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected the stamp failure to propagate")
        finally:
            sys.argv, fill_ca_forms.fitz = argv, real
        assert not os.path.exists(spec["out_dir"]), "first form was written"


# ---------- S3: a sign field that matches nothing ----------

def test_unmatched_sign_field_exits_non_zero_and_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [{"src": "a.pdf", "out": "a.pdf"},
                         _form(src="b.pdf", field="Signatur")], {"parker": _png(d)})
        code, err = _run_main(spec, d)
        assert code, "exited zero"
        assert "⚑ SIGNATURE NOT APPLIED — parker: b.pdf field 'Signatur' not found" in err, err
        assert not os.path.exists(spec["out_dir"])


def test_matched_sign_field_is_written():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()], {"parker": _png(d)})
        code, err = _run_main(spec, d)
        assert code is None, (code, err)
        assert os.listdir(spec["out_dir"]) == ["a-out.pdf"]


# ---------- sign shape ----------

def test_sign_shape_is_validated():
    for bad, want in [({"Signature": "parker"}, "must be an object with a `who`"),
                      ({"Signature": {"dx": 2}}, "names no signer"),
                      ({"Signature": {"who": ""}}, "names no signer"),
                      (["Signature"], "must be an object of field")]:
        form = {"src": "a.pdf", "out": "a.pdf", "sign": bad}
        msg = _raises(check_signatures, [form], {"parker": "/x.png"})
        assert want in msg and "None" not in msg, (bad, msg)


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
