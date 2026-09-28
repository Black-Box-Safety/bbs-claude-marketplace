#!/usr/bin/env python3
"""test_fill_obs_packet.py — who and what lands on two binding lines of Packet B.

Run it:
    python3 test_fill_obs_packet.py

Two rulings are executed here rather than trusted to a comment:

- **DGS PD 843 "Name of DVBE" is the legal name** (Parker, 2026-09-18, confirmed
  2026-09-28: "do legal name"). The expected value is read out of
  vendor_profile.json at test time, never typed here, so the test follows the
  profile and fails if the script ever writes the short name.
- **CalRecycle 74 is signed by the rep preparing the bid, who may be any BBS
  employee** (Parker, 2026-09-28: "anyone is permitted to sign"). The signature
  is applied only for a signature delegate; any other rep's line is left for
  them to sign by hand and flagged; a non-BBS signer stops the run.

These call `build_field_values()` — the exact list the filler writes — and do
not open a PDF. No real California form PDF exists in this repo, so none of this
is evidence about a rendered packet; that still needs a blank packet in hand.

Stdlib only, no pytest, so it runs wherever the plugin is installed.
"""
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fill_obs_packet as fop  # noqa: E402

with open(fop.VENDOR_PROFILE, encoding="utf-8") as _fh:
    VP = json.load(_fh)

PD843_NAME = "DVBE Dec. DGS PD 843 - Name of DVBE"
CR_SIG = "DORRR CalRec 74 - Signature"
CR_DATE = "DORRR CalRec 74 - Date"
CR_PRINT = "DORRR CalRec 74 - Print Name"
CR_TITLE = "DORRR CalRec 74 - Title"


def _delegate(role_name):
    return next(d for d in VP["signature_delegation"]["delegates"]
                if d["name"] == role_name)


def _inputs(rep):
    with open(os.path.join(os.path.dirname(HERE), "assets", "inputs_template.json"),
              encoding="utf-8") as fh:
        inp = json.load(fh)
    inp["rep"] = rep
    return inp


def _fields(inp):
    return {f["field_id"]: f["value"]
            for f in fop.build_field_values(fop.load_profile(), inp)}


def _employee_domain():
    return VP["contact"]["email"].rsplit("@", 1)[1]


def _non_delegate_rep():
    """A BBS employee who is not a signature delegate — built, not assumed."""
    delegate_emails = {d["email"].lower() for d in VP["signature_delegation"]["delegates"]}
    email = "test.rep@" + _employee_domain()
    assert email not in delegate_emails
    return {"name": "Test Rep", "title": "Account Manager", "email": email,
            "signature": "Test Rep"}


# ---------- DGS PD 843 ----------

def test_pd843_name_of_dvbe_is_legal_name():
    legal = VP["business_identity"]["legal_name"]
    got = _fields(_inputs(dict(_delegate("Parker Marshall"), title="Sales Manager",
                               signature="Parker Marshall")))
    assert got[PD843_NAME] == legal, (PD843_NAME, got.get(PD843_NAME), legal)


def test_pd843_name_of_dvbe_is_never_short_name():
    short = VP["business_identity"]["short_name"]
    assert short != VP["business_identity"]["legal_name"]
    got = _fields(_inputs(_non_delegate_rep()))
    assert got[PD843_NAME] != short


def test_pd843_follows_the_profile_not_a_literal():
    """Change the profile's legal name and the PD 843 field follows it."""
    real = fop.load_profile

    def patched():
        p = real()
        p["legal_name"] = "Profile Legal Name, Inc."
        return p
    fop.load_profile = patched
    try:
        got = _fields(_inputs(_non_delegate_rep()))
    finally:
        fop.load_profile = real
    assert got[PD843_NAME] == "Profile Legal Name, Inc."


# ---------- CalRecycle 74 ----------

def test_calrecycle74_delegate_rep_is_signed():
    rep = dict(_delegate("Parker Marshall"), title="Sales Manager",
               signature="Parker Marshall")
    inp = _inputs(rep)
    got = _fields(inp)
    assert got[CR_SIG] == "Parker Marshall"
    assert got[CR_DATE] == inp["signature_date"]
    assert got[CR_PRINT] == "Parker Marshall"
    assert fop.signature_flags(fop.load_profile(), inp) == []


def test_calrecycle74_non_delegate_employee_is_left_blank_and_flagged():
    rep = _non_delegate_rep()
    inp = _inputs(rep)
    got = _fields(inp)
    assert CR_SIG not in got, "a non-delegate's signature was applied"
    assert CR_DATE not in got, "date filled on a line the rep has not signed"
    assert got[CR_PRINT] == rep["name"] and got[CR_TITLE] == rep["title"]
    flags = fop.signature_flags(fop.load_profile(), inp)
    assert len(flags) == 1 and "SIGNATURE REQUIRED" in flags[0]
    assert "CalRecycle 74" in flags[0] and rep["name"] in flags[0]


def test_calrecycle74_never_carries_a_delegates_signature_for_another_rep():
    """A non-delegate asking for Parker's or Jackson's signature gets neither."""
    for d in VP["signature_delegation"]["delegates"]:
        rep = dict(_non_delegate_rep(), signature=d["name"])
        got = _fields(_inputs(rep))
        assert CR_SIG not in got, "delegate %s signed for %s" % (d["name"], rep["name"])


def test_calrecycle74_delegate_email_with_another_name_is_not_delegated():
    rep = {"name": "Test Rep", "title": "Account Manager",
           "email": _delegate("Parker Marshall")["email"], "signature": "Test Rep"}
    got = _fields(_inputs(rep))
    assert CR_SIG not in got


def test_calrecycle74_rep_without_email_is_left_blank_and_flagged():
    rep = {"name": "Parker Marshall", "title": "Sales Manager", "signature": "Parker Marshall"}
    inp = _inputs(rep)
    got = _fields(inp)
    assert CR_SIG not in got
    assert "SIGNATURE REQUIRED" in fop.signature_flags(fop.load_profile(), inp)[0]


def test_calrecycle74_missing_rep_is_flagged_missing():
    inp = _inputs({})
    got = _fields(inp)
    assert CR_SIG not in got
    assert fop.signature_flags(fop.load_profile(), inp)[0].startswith(
        "[MISSING — NEEDS INPUT]")


def test_calrecycle74_non_bbs_signer_refuses():
    rep = {"name": "Agency Buyer", "title": "Buyer",
           "email": "buyer@cdcr.ca.gov", "signature": "Agency Buyer"}
    try:
        _fields(_inputs(rep))
    except SystemExit as e:
        assert "REFUSED" in str(e.code) and "CalRecycle 74" in str(e.code)
    else:
        raise AssertionError("a non-BBS signer was accepted on CalRecycle 74")


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
        except Exception:
            failed.append(name)
            print("FAIL %s" % name)
            traceback.print_exc()
        else:
            print("ok   %s" % name)
    print("\n%d/%d passed" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
