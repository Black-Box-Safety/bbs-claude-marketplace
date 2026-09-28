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
    PNG_MAGIC, SignatureMissing, check_signatures, check_signer, load_delegation,
    preflight, resolve_sig_path)

DOMAIN, DELEGATES = load_delegation()  # read from vendor_profile.json, never typed here
_BY_ROLE = {d["role"]: d for d in DELEGATES}


# ---------- fixtures ----------

def _png(d, name="sig.png", data=PNG_MAGIC + b"rest-of-png"):
    path = os.path.join(d, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _form(who="parker", src="a.pdf", out="a-out.pdf", field="Signature",
          kind="CalRecycle74", **sig):
    return {"form": kind, "src": src, "out": out, "sign": {field: dict(sig, who=who)}}


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


# Every spec names its signer (ca-form-rules.md, "Rep-signed lines"). The
# default is Parker, the delegate whose `who` is "parker" in these fixtures.
PARKER = {"name": _BY_ROLE["sales_manager"]["name"], "title": "Sales Manager",
          "email": _BY_ROLE["sales_manager"]["email"]}
JACKSON = {"name": _BY_ROLE["dvbe_owner"]["name"], "title": "President",
           "email": _BY_ROLE["dvbe_owner"]["email"]}
EMPLOYEE = {"name": "Test Rep", "title": "Account Manager", "email": "test.rep@" + DOMAIN}


def _profile_png(root, role):
    """Where the profile says `role`'s signature is, under a fake MASTER root."""
    return resolve_sig_path(_BY_ROLE[role]["signature_image"], root)


def _spec(d, forms, signatures=None, **kw):
    """A spec over a fake MASTER root holding both delegates' PNGs at their
    vendor_profile.json paths. No `signatures` map unless a test passes one."""
    for f in forms:
        _png(d, os.path.join("blank", f["src"]), b"%PDF-blank")
    root = os.path.join(d, "Black Box Safety - MASTER")
    for role in _BY_ROLE:
        path = _profile_png(root, role)
        _png(os.path.dirname(path), os.path.basename(path))
    spec = {"src_dir": os.path.join(d, "blank"), "out_dir": os.path.join(d, "out"),
            "master_root": root, "signer": dict(PARKER), "forms": forms}
    if signatures is not None:
        spec["signatures"] = signatures
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
        spec = _spec(d, [_form()])
        code, err = _run_main(spec, d)
        assert code is None, (code, err)
        assert os.path.isfile(os.path.join(d, "out", "a-out.pdf"))


# ---------- S2: bad image bytes, missing blank form, all-or-nothing ----------

def test_zero_byte_image_stops_and_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()])
        _png(*os.path.split(_profile_png(spec["master_root"], "sales_manager")), data=b"")
        code, _ = _run_main(spec, d)
        assert "is empty (0 bytes)" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_non_png_image_stops_and_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()])
        _png(*os.path.split(_profile_png(spec["master_root"], "sales_manager")),
             data=b"\xff\xd8\xff\xe0JFIF..")
        code, _ = _run_main(spec, d)
        assert "is not a PNG" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_missing_blank_form_stops_before_anything_is_written():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [{"form": "other", "src": "a.pdf", "out": "a.pdf"}])
        spec["forms"].append({"form": "other", "src": "never-downloaded.pdf", "out": "b.pdf"})
        msg = _raises(preflight, spec)
        assert "blank form not found" in msg and "never-downloaded.pdf" in msg, msg
        code, _ = _run_main(spec, d)
        assert code and "never-downloaded.pdf" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_failure_on_a_later_form_leaves_out_dir_untouched():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [{"form": "other", "src": "a.pdf", "out": "a.pdf"},
                         _form(src="b.pdf")])

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
        spec = _spec(d, [{"form": "other", "src": "a.pdf", "out": "a.pdf"},
                         _form(src="b.pdf", field="Signatur")])
        code, err = _run_main(spec, d)
        assert code, "exited zero"
        assert "⚑ SIGNATURE NOT APPLIED — parker: b.pdf field 'Signatur' not found" in err, err
        assert not os.path.exists(spec["out_dir"])


def test_matched_sign_field_is_written():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()])
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


# ---------- the signer (ca-form-rules.md, "Rep-signed lines") ----------

def _signer_spec(signer, forms=None):
    spec = {"forms": forms if forms is not None else [_form("parker")]}
    if signer is not None:
        spec["signer"] = signer
    return spec


def test_no_signer_is_missing_and_main_writes_nothing():
    msg = _raises(check_signer, _signer_spec(None))
    assert msg.startswith("[MISSING — NEEDS INPUT] `signer`"), msg
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()])
        del spec["signer"]
        code, _ = _run_main(spec, d)
        assert "MISSING" in str(code), code
        assert not os.path.exists(spec["out_dir"])


def test_nameless_non_bbs_signer_refused_before_name_check():
    msg = _raises(check_signer, _signer_spec({"email": "buyer@cdcr.ca.gov"}))
    assert msg.startswith("REFUSED: the signer must be a BBS employee"), msg


def test_double_at_and_lookalike_domain_refused():
    for email in ("x@evil.com@" + DOMAIN, "x@evil" + DOMAIN):
        msg = _raises(check_signer, _signer_spec({"name": "X", "email": email}, forms=[]))
        assert msg.startswith("REFUSED"), (email, msg)


def test_parker_via_recorded_alias_gets_his_image():
    alias = _BY_ROLE["sales_manager"]["aliases"][0]
    got, _ = check_signer(_signer_spec(dict(PARKER, email=alias)))
    assert got["role"] == "sales_manager", got


def test_parkers_name_with_another_email_refused_with_the_right_reason():
    msg = _raises(check_signer, _signer_spec(dict(PARKER, email="parker.m@" + DOMAIN)))
    assert "email does not match the delegate's recorded address" in msg, msg


def test_non_delegate_signer_cannot_use_a_delegate_image_on_a_rep_line():
    for who in ("parker", "jackson"):
        msg = _raises(check_signer, _signer_spec(EMPLOYEE, [_form(who)]))
        assert "never applied to someone else's line" in msg and "not a signature delegate" in msg, msg


def test_non_delegate_signer_with_no_rep_line_image_passes():
    dv = _form("jackson", src="pd843.pdf", kind="PD843", line="dv_owner")
    other = {"form": "CalRecycle74", "src": "c.pdf", "out": "c.pdf"}
    assert check_signer(_signer_spec(EMPLOYEE, [dv, other]))[0] is None


def test_dv_owner_line_is_the_dvbe_owners_only():
    bad = _form("parker", src="pd843.pdf", kind="PD843", line="dv_owner")
    msg = _raises(check_signer, _signer_spec(PARKER, [bad]))
    assert "only the dvbe_owner signs" in msg, msg


def test_who_that_is_not_a_delegate_refused():
    msg = _raises(check_signer, _signer_spec(PARKER, [_form("kim")]))
    assert "'kim'" in msg and "not a signature delegate" in msg, msg


def test_jackson_as_named_signer_may_sign_a_rep_line():
    assert check_signer(_signer_spec(JACKSON, [_form("jackson")]))[0]["role"] == "dvbe_owner"


def test_refused_signer_writes_nothing_through_main():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form()], signer=EMPLOYEE)
        code, _ = _run_main(spec, d)
        assert "REFUSED" in str(code), code
        assert not os.path.exists(spec["out_dir"])


# ---------- B1: a delegate's image comes from the profile, not the spec ----------

def test_image_is_the_delegates_profile_image():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form("parker"),
                         _form("jackson", src="pd.pdf", out="pd-out.pdf", kind="PD843",
                               line="dv_owner")])
        sigs = preflight(spec)
        root = spec["master_root"]
        assert sigs == {"parker": _profile_png(root, "sales_manager"),
                        "jackson": _profile_png(root, "dvbe_owner")}, sigs


def test_swapped_signature_keys_refused_both_ways():
    with tempfile.TemporaryDirectory() as d:
        jack = _BY_ROLE["dvbe_owner"]["signature_image"]
        park = _BY_ROLE["sales_manager"]["signature_image"]
        # Jackson's PNG keyed as "parker" on Parker's CalRecycle 74
        spec = _spec(d, [_form("parker")], {"parker": jack})
        msg = _raises(preflight, spec)
        assert "REFUSED" in msg and "not Parker" in msg and "signature_image" in msg, msg
        code, _ = _run_main(spec, d)
        assert "REFUSED" in str(code) and not os.path.exists(spec["out_dir"]), code
        # Parker's PNG keyed as "jackson" on Jackson's PD 843
        spec = _spec(d, [_form("jackson", kind="PD843", line="dv_owner")],
                     {"jackson": park})
        msg = _raises(preflight, spec)
        assert "REFUSED" in msg and "not Jackson" in msg, msg


def test_legacy_signatures_entry_naming_the_same_file_is_accepted():
    with tempfile.TemporaryDirectory() as d:
        park = _BY_ROLE["sales_manager"]["signature_image"]
        spec = _spec(d, [_form("parker")], {"parker": park})
        assert preflight(spec)["parker"] == _profile_png(spec["master_root"], "sales_manager")


# ---------- B2: DV-owner lines follow the form, not the spec's label ----------

def test_dv_owner_label_on_calrecycle74_refused():
    griffin = {"name": "Griffin Forsyth", "title": "Vice President",
               "email": "griffin@" + DOMAIN}
    spec = _signer_spec(griffin, [_form("jackson", src="CalRecycle74.pdf",
                                        kind="CalRecycle74", line="dv_owner")])
    msg = _raises(check_signer, spec)
    assert "marked `dv_owner`" in msg and "PD843" in msg, msg


def test_dv_owner_on_pd843_accepted_whoever_signs():
    for signer in (EMPLOYEE, PARKER):
        spec = _signer_spec(signer, [_form("jackson", kind="PD843", line="dv_owner")])
        check_signer(spec)


def test_dv_owner_form_rejects_unmarked_or_other_delegate_stamps():
    for kind in ("PD843", "CV012", "STD204", "STD205"):
        msg = _raises(check_signer, _signer_spec(JACKSON, [_form("jackson", kind=kind)]))
        assert "DV-owner declaration" in msg and "unmarked" in msg, (kind, msg)
        msg = _raises(check_signer, _signer_spec(PARKER, [_form("parker", kind=kind)]))
        assert "DV-owner declaration" in msg, (kind, msg)


def test_obs1000_signer_not_ruled_so_never_stamped():
    msg = _raises(check_signer, _signer_spec(PARKER, [_form("parker", kind="OBS1000")]))
    assert "signer is not ruled" in msg, msg


def test_missing_or_unknown_form_kind_refused():
    for form in ({"src": "a.pdf", "out": "a.pdf"}, {"form": "PD 843", "src": "a.pdf",
                                                      "out": "a.pdf"}):
        msg = _raises(check_signer, _signer_spec(PARKER, [form]))
        assert "must be one of" in msg, msg


# ---------- print name / title come from the signer ----------

def test_signer_fields_filled_from_signer_and_conflict_refused():
    with tempfile.TemporaryDirectory() as d:
        form = dict(_form(), signer_fields={"name": "Print Name", "title": "Title"})
        spec = _spec(d, [form])
        preflight(spec)
        assert spec["forms"][0]["text"] == {"Print Name": PARKER["name"],
                                            "Title": PARKER["title"]}
        form = dict(_form(), signer_fields={"name": "Print Name"},
                    text={"Print Name": "Somebody Else"})
        msg = _raises(preflight, _spec(d, [form]))
        assert "Somebody Else" in msg and "REFUSED" in msg, msg


def test_non_ascii_lookalike_email_refused():
    kelvin = dict(EMPLOYEE, email="\u212aim@" + DOMAIN)   # KELVIN SIGN, folds to "k"
    msg = _raises(check_signer, _signer_spec(kelvin, forms=[]))
    assert msg.startswith("REFUSED"), msg


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
