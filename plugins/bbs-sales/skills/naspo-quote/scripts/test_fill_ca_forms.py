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
    # Every fake blank reads as a CalRecycle 74 page (the fixtures' default kind),
    # using the form table's own markers.
    TEXT = "CalRecycle 74 Postconsumer-Content Certification"

    def __init__(self, names):
        self._w = [_Widget(n) for n in names]
        self.stamps = []

    def get_text(self):
        return self.TEXT

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


LIMIT = fill_ca_forms.load_limit()   # read from vendor_profile.json, never typed here
UNDER = LIMIT - 0.01


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
        if not _BY_ROLE[role]["signature_image"]:
            continue  # no PNG recorded yet for this delegate
        path = _profile_png(root, role)
        _png(os.path.dirname(path), os.path.basename(path))
    spec = {"src_dir": os.path.join(d, "blank"), "out_dir": os.path.join(d, "out"),
            "master_root": root, "signer": dict(PARKER), "forms": forms,
            "quote_total_incl_tax": UNDER}
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
        # A sign field the PDF does not have is an unknown field ID: refused before
        # anything is drawn, exactly like a mistyped text field.
        assert "b.pdf has no field 'Signatur'" in str(code), code
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
    # Joyce Newell is a BBS employee but not one of the six (Parker, 2026-10-01).
    msg = _raises(check_signer, _signer_spec(PARKER, [_form("joyce")]))
    assert "'joyce'" in msg and "not a signature delegate" in msg, msg


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


def test_obs1000_is_a_rep_signed_line():
    # Ruled 2026-10-01 (Parker: "Yes, rep-signed"): the named signer's stamp goes on it.
    check_signer(_signer_spec(PARKER, [_form("parker", kind="OBS1000")]))
    msg = _raises(check_signer, _signer_spec(PARKER, [_form("jackson", kind="OBS1000")]))
    assert "never applied to someone" in msg, msg


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


# ---------- real PDFs: the limit, field IDs, pre-filled values, page checks ----------
# Built with PyMuPDF at test time (no form PDF is committed). Headers reuse the
# form table's own markers, read from ca-form-rules.md, never typed here.

TABLE = fill_ca_forms.load_form_table()


def _header(kind):
    return "STATE OF CALIFORNIA " + " ".join(TABLE[kind]["markers"]) + " Page 1"


def _real_pdf(path, pages):
    """pages: [(header text, [(name, type, value)])]. Types: text, check, sig."""
    import fitz as real
    doc = real.open()
    for header, fields in pages:
        page = doc.new_page()
        page.insert_text((40, 40), header, fontsize=9)
        y = 80
        for name, ftype, value in fields:
            w = real.Widget()
            w.field_name = name
            w.rect = real.Rect(40, y, 300, y + 18)
            w.field_type = {"text": real.PDF_WIDGET_TYPE_TEXT,
                            "check": real.PDF_WIDGET_TYPE_CHECKBOX,
                            "sig": real.PDF_WIDGET_TYPE_SIGNATURE}[ftype]
            if value and ftype == "text":
                w.field_value = value
            page.add_widget(w)
            y += 30
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()


def _real_png(path):
    import fitz as real
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pix = real.Pixmap(real.csRGB, real.IRect(0, 0, 60, 20), False)
    pix.clear_with(0)
    pix.save(path)


def _real_spec(d, forms, pages_by_src, **kw):
    root = os.path.join(d, "Black Box Safety - MASTER")
    for role in _BY_ROLE:
        if _BY_ROLE[role]["signature_image"]:
            _real_png(_profile_png(root, role))
    for src, pages in pages_by_src.items():
        _real_pdf(os.path.join(d, "blank", src), pages)
    spec = {"src_dir": os.path.join(d, "blank"), "out_dir": os.path.join(d, "out"),
            "master_root": root, "signer": dict(PARKER), "forms": forms,
            "quote_total_incl_tax": UNDER, "signature_date": "10.1.26"}
    spec.update(kw)
    return spec


def _run_real(spec, d):
    spec_path = os.path.join(d, "spec.json")
    with open(spec_path, "w") as fh:
        json.dump(spec, fh)
    argv = sys.argv
    sys.argv = ["fill_ca_forms.py", spec_path]
    out, err, code = io.StringIO(), io.StringIO(), None
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            fill_ca_forms.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = argv
    return code, out.getvalue(), err.getvalue()


def _images_on(path):
    import fitz as real
    doc = real.open(path)
    n = sum(len(p.get_images()) for p in doc)
    values = {w.field_name: w.field_value for p in doc for w in (p.widgets() or [])}
    doc.close()
    return n, values


CALREC = {"a.pdf": [(_header("CalRecycle74"), [("Signature", "text", ""),
                                                ("Date", "text", "")])]}


def _calrec_form():
    return {"form": "CalRecycle74", "src": "a.pdf", "out": "a-out.pdf",
            "sign": {"Signature": {"who": "parker", "date": "Date"}}}


def _needs_fitz():
    return fill_ca_forms.fitz is None


def test_limit_just_under_signs():
    if _needs_fitz():
        return
    with tempfile.TemporaryDirectory() as d:
        spec = _real_spec(d, [_calrec_form()], CALREC, quote_total_incl_tax=f"${UNDER:,.2f}")
        code, out, err = _run_real(spec, d)
        assert not code, (code, err)
        n, values = _images_on(os.path.join(spec["out_dir"], "a-out.pdf"))
        assert n == 1 and values.get("Date") == "10.1.26", (n, values)
        assert "WITHHELD" not in out


def test_limit_exactly_at_over_missing_and_unreadable_withhold_every_signature():
    if _needs_fitz():
        return
    for total in (LIMIT, f"${LIMIT:,.2f}", LIMIT + 1, None, "", "about nine thousand", True):
        with tempfile.TemporaryDirectory() as d:
            spec = _real_spec(d, [_calrec_form()], CALREC, quote_total_incl_tax=total)
            code, out, err = _run_real(spec, d)
            assert not code, (total, code, err)
            n, values = _images_on(os.path.join(spec["out_dir"], "a-out.pdf"))
            assert n == 0, (total, n)
            assert not values.get("Date"), (total, values)   # hand-signed means hand-dated
            assert "SIGNATURES WITHHELD" in out and "⚑ SIGNATURE REQUIRED" in out, out


def test_withheld_also_covers_jacksons_owner_lines():
    if _needs_fitz():
        return
    with tempfile.TemporaryDirectory() as d:
        pages = {"p.pdf": [(_header("PD843"), [("DVBEowner1signature", "sig", "")])]}
        form = {"form": "PD843", "src": "p.pdf", "out": "p-out.pdf",
                "sign": {"DVBEowner1signature": {"who": "jackson", "line": "dv_owner"}}}
        spec = _real_spec(d, [form], pages, quote_total_incl_tax=LIMIT)
        code, out, _err = _run_real(spec, d)
        assert not code and _images_on(os.path.join(spec["out_dir"], "p-out.pdf"))[0] == 0
        assert "jackson" in out and "WITHHELD" in out, out


def test_delegate_without_a_png_gets_a_blank_flagged_line_not_a_stop():
    if _needs_fitz():
        return
    kim = next(r for r in _BY_ROLE.values() if r["role"] == "rep_kim")
    assert kim["signature_image"] is None   # null until Kim's PNG is in MASTER/Signatures/
    with tempfile.TemporaryDirectory() as d:
        form = dict(_calrec_form(), sign={"Signature": {"who": "kim", "date": "Date"}})
        spec = _real_spec(d, [form], CALREC,
                          signer={"name": kim["name"], "title": "Account Manager",
                                  "email": kim["email"]})
        code, out, err = _run_real(spec, d)
        assert not code, (code, err)
        n, values = _images_on(os.path.join(spec["out_dir"], "a-out.pdf"))
        assert n == 0 and not values.get("Date"), (n, values)
        assert "Kim Quezon): no signature image on file yet" in out, out


def test_a_set_but_missing_png_still_stops():
    with tempfile.TemporaryDirectory() as d:
        spec = _spec(d, [_form("parker")])
        os.remove(_profile_png(spec["master_root"], "sales_manager"))
        msg = _raises(preflight, spec)
        assert "not found" in msg, msg


def test_unidentified_page_is_never_signed():
    if _needs_fitz():
        return
    for kind, who, line in (("CalRecycle74", "parker", None), ("PD843", "jackson", "dv_owner")):
        with tempfile.TemporaryDirectory() as d:
            pages = {"a.pdf": [("MASTER SERVICES AGREEMENT between the parties",
                                [("Signature", "text", "")])]}
            sig = {"who": who}
            if line:
                sig["line"] = line
            form = {"form": kind, "src": "a.pdf", "out": "a-out.pdf",
                    "sign": {"Signature": sig}}
            spec = _real_spec(d, [form], pages)
            code, _out, _err = _run_real(spec, d)
            assert code and "no known form" in str(code), (kind, code)
            assert not os.path.exists(spec["out_dir"])


def test_zero_and_foreign_formatted_totals_are_unreadable():
    for raw in ("$0.00", 0, "0", "300.000,00", "9.054,75", "1,23", "$ 12,34.5", "12e5"):
        assert fill_ca_forms.parse_total(raw) is None, raw
    for raw, want in (("$9,054.75", 9054.75), ("9054.75", 9054.75), (9054.75, 9054.75),
                      ("249,999.99", 249999.99), ("1000 USD", 1000.0)):
        assert fill_ca_forms.parse_total(raw) == want, raw


def test_agency_radio_choice_is_kept():
    # The index _widget_index() builds: one radio group, the agency picked "Yes".
    index = {"Is GenAI utilized?": [(0, "RadioButton", "Yes"), (0, "RadioButton", "Off")]}
    spec = {"src": "r.pdf", "radios": {"Is GenAI utilized?": {"index": 1, "on": "No"}}}
    msg = _raises(fill_ca_forms.check_prefilled, spec, index)
    assert "already set to 'Yes'" in msg, msg
    spec["replace_prefilled"] = {"Is GenAI utilized?": "rep: agency ticked the wrong box"}
    fill_ca_forms.check_prefilled(spec, index)                    # the rep's call, recorded
    same = {"src": "r.pdf", "radios": {"Is GenAI utilized?": {"index": 0, "on": "Yes"}}}
    fill_ca_forms.check_prefilled(same, index)                    # same choice: fine


def test_unknown_field_and_wrong_type_refused_nothing_written():
    if _needs_fitz():
        return
    with tempfile.TemporaryDirectory() as d:
        for form, want in ((dict(_calrec_form(), text={"Signatur Date": "x"}), "no field"),
                           (dict(_calrec_form(), checks={"Date": True}), "not CheckBox")):
            spec = _real_spec(d, [form], CALREC)
            code, _out, _err = _run_real(spec, d)
            assert code and want in str(code), (want, code)
            assert not os.path.exists(spec["out_dir"])


def test_agency_prefilled_values_are_kept_and_never_overwritten_silently():
    if _needs_fitz():
        return
    pages = {"c.pdf": [(_header("OBS4007C"), [("Solicitation", "text", "RFQ-123"),
                                              ("Buyer Name", "text", "T. Ryan Kemp"),
                                              ("Bidder Signature", "text", "")])]}
    base = {"form": "OBS4007C", "src": "c.pdf", "out": "c-out.pdf",
            "sign": {"Bidder Signature": {"who": "parker"}}}
    with tempfile.TemporaryDirectory() as d:
        spec = _real_spec(d, [dict(base, text={"Solicitation": "RFQ-123"})], pages)
        code, out, err = _run_real(spec, d)
        assert not code, (code, err)
        assert "kept agency value: c.pdf 'Buyer Name' = 'T. Ryan Kemp'" in out, out
        _n, values = _images_on(os.path.join(spec["out_dir"], "c-out.pdf"))
        assert values["Buyer Name"] == "T. Ryan Kemp" and values["Solicitation"] == "RFQ-123"
    with tempfile.TemporaryDirectory() as d:
        spec = _real_spec(d, [dict(base, text={"Buyer Name": "Someone Else"})], pages)
        code, _out, _err = _run_real(spec, d)
        assert code and "already holds 'T. Ryan Kemp'" in str(code), code
        assert not os.path.exists(spec["out_dir"])
    with tempfile.TemporaryDirectory() as d:
        spec = _real_spec(d, [dict(base, text={"Buyer Name": "Someone Else"},
                                   replace_prefilled={"Buyer Name": "rep: agency typo"})],
                          pages)
        code, _out, err = _run_real(spec, d)
        assert not code, (code, err)


def _packet_pages():
    return {"k.pdf": [
        (_header("OBS4007C"), [("Bidder Signature", "text", "")]),
        ("Line Item Cost Worksheet", [("Ext 1", "text", "")]),
        (_header("PD843"), [("DVBEowner1signature", "sig", "")]),
        (_header("OBS1000"), [("Signature", "sig", "")]),
    ]}


def _packet(sign):
    return {"form": "packet", "src": "k.pdf", "out": "k-out.pdf", "sign": sign}


def test_packet_stamps_each_line_by_the_page_it_sits_on():
    if _needs_fitz():
        return
    with tempfile.TemporaryDirectory() as d:
        spec = _real_spec(d, [_packet({
            "Bidder Signature": {"who": "parker", "line": "rep"},
            "DVBEowner1signature": {"who": "jackson", "line": "dv_owner"},
            "Signature": {"who": "parker", "line": "rep"}})], _packet_pages())
        code, _out, err = _run_real(spec, d)
        assert not code, (code, err)
        assert _images_on(os.path.join(spec["out_dir"], "k-out.pdf"))[0] == 3


def test_packet_refuses_a_line_whose_page_says_otherwise():
    if _needs_fitz():
        return
    cases = (
        # static check: Parker's stamp marked as a rep line on what is Jackson's page
        ({"DVBEowner1signature": {"who": "parker", "line": "rep"}}, PARKER, "whose line is dv_owner"),
        # Jackson named as signer passes the static check; the PD 843 page still says no
        ({"DVBEowner1signature": {"who": "jackson", "line": "rep"}}, JACKSON, "whose line is dv_owner"),
        ({"Bidder Signature": {"who": "jackson", "line": "dv_owner"}}, PARKER, "whose line is rep"),
        ({"Ext 1": {"who": "parker", "line": "rep"}}, PARKER, "no known form"),
        ({"Bidder Signature": {"who": "parker"}}, PARKER, "must say"),
    )
    for sign, signer, want in cases:
        with tempfile.TemporaryDirectory() as d:
            spec = _real_spec(d, [_packet(sign)], _packet_pages(), signer=dict(signer))
            code, _out, _err = _run_real(spec, d)
            assert code and want in str(code), (sign, code)
            assert not os.path.exists(spec["out_dir"])


def test_declared_kind_must_match_the_page():
    if _needs_fitz():
        return
    with tempfile.TemporaryDirectory() as d:
        pages = {"a.pdf": [(_header("PD843"), [("Signature", "text", "")])]}
        spec = _real_spec(d, [dict(_calrec_form(), sign={"Signature": {"who": "parker"}})],
                          pages)
        code, _out, _err = _run_real(spec, d)
        assert code and "reads as PD843" in str(code), code


def test_form_table_rows_are_well_formed_and_lines_match_the_rules():
    assert {k: v["line"] for k, v in TABLE.items() if v["line"]} == {
        "OBS4007C": "rep", "OBS4007B": "rep", "Darfur": "rep", "CalRecycle74": "rep",
        "OBS1000": "rep", "PD843": "dv_owner", "STD204": "dv_owner", "STD205": "dv_owner"}
    assert set(fill_ca_forms.DV_OWNER_FORMS) - {"CV012"} <= {
        k for k, v in TABLE.items() if v["line"] == "dv_owner"}


def test_markers_match_real_blanks_when_available():
    """Set BBS_BLANK_FORMS to a folder of blank state forms to check the markers
    against real PDFs (file stem = form kind, e.g. PD843.pdf). Skipped otherwise."""
    folder = os.environ.get("BBS_BLANK_FORMS")
    if not folder or _needs_fitz():
        return
    import fitz as real
    for name in sorted(os.listdir(folder)):
        kind = os.path.splitext(name)[0]
        if kind not in TABLE:
            continue
        doc = real.open(os.path.join(folder, name))
        hits = fill_ca_forms.classify_page(doc[0].get_text(), TABLE)
        doc.close()
        assert hits == [kind], (name, hits)


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
