#!/usr/bin/env python3
"""test_fill_obs_packet.py — who signs, and what name goes where, on Packet B.

Run it:
    python3 test_fill_obs_packet.py

Parker's rulings, executed rather than trusted to a comment:

- **DGS PD 843 "Name of DVBE" is the legal name** (2026-09-18, confirmed
  2026-09-28: "do legal name").
- **CalRecycle 74, OBS 1000 and Darfur OBS 1500 company names are the legal
  name** (2026-09-28: "Yes, they can match legal name").
- **Rep-signed lines — OBS 4007(B) bidder, Darfur OBS 1500, CalRecycle 74 — may
  be signed by any BBS employee the rep names** (2026-09-28: "anyone is permitted
  to sign"; "whomever the rep says, they can sign it with anyone"). No default
  signer; a non-BBS signer stops the run; a signature is applied only for a
  signature delegate, as the delegate's name of record, never free text.

Expected values are read out of vendor_profile.json at test time, never typed
here. These call `build_field_values()` — the exact list the filler writes —
and do not open a PDF. No real California form PDF exists in this repo, so none
of this is evidence about a rendered packet.

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
TEMPLATE = os.path.join(os.path.dirname(HERE), "assets", "inputs_template.json")

PD843_NAME = "DVBE Dec. DGS PD 843 - Name of DVBE"
DARFUR_NAME = "Darfur OBS 1500 - CompanyVendor Name Printed"
OBS1000_NAME = "OBS 1000 - Business Name"
CR_PRINT, CR_TITLE = "DORRR CalRec 74 - Print Name", "DORRR CalRec 74 - Title"
# (signature field, its date field) for each rep-signed line
SIGNED = {
    "CalRecycle 74": ("DORRR CalRec 74 - Signature", "DORRR CalRec 74 - Date"),
    "OBS 4007(B) Bidder": ("OBS RFQ 4007(B) - Bidder Signature", "OBS RFQ 4007(B) - Bidder Sig Date"),
    "Darfur OBS 1500": ("Darfur OBS 1500 - By Authorized Signature", "Darfur OBS 1500 - Date"),
}
LEGAL = VP["business_identity"]["legal_name"]
SHORT = VP["business_identity"]["short_name"]
DOMAIN = VP["contact"]["email"].rsplit("@", 1)[1]


DELEGATES = fop.load_profile()["signature_delegates"]  # roles resolved by the loader


def _delegate(name):
    return next(d for d in DELEGATES if d["name"] == name)


def _inputs(signer, rep=None):
    with open(TEMPLATE, encoding="utf-8") as fh:
        inp = json.load(fh)
    if rep is not None:
        inp["rep"] = rep
    inp["signer"] = signer
    return inp


def _fields(inp):
    return {f["field_id"]: f["value"]
            for f in fop.build_field_values(fop.load_profile(), inp)}


def _exit_message(inp):
    try:
        _fields(inp)
    except SystemExit as e:
        return str(e.code)
    raise AssertionError("expected the run to stop, and it wrote fields")


def _parker(**over):
    d = _delegate("Parker Marshall")
    return dict({"name": d["name"], "title": "Sales Manager", "email": d["email"]}, **over)


def _employee(**over):
    delegate_emails = {d["email"].lower() for d in DELEGATES}
    email = "test.rep@" + DOMAIN
    assert email not in delegate_emails
    return dict({"name": "Test Rep", "title": "Account Manager", "email": email}, **over)


KIM_REP = {"name": "Kim Quezon", "title": "Sales", "email": "kim@" + DOMAIN}


def _assert_signed(got, inp, name):
    for line, (sig, date) in SIGNED.items():
        assert got.get(sig) == name, (line, got.get(sig))
        assert got.get(date) == inp["signature_date"], (line, got.get(date))


def _assert_blank(got):
    for line, (sig, date) in SIGNED.items():
        assert sig not in got, "%s signature applied for a non-delegate" % line
        assert date not in got, "%s dated on a line nobody has signed" % line


# ---------- company names ----------

def test_pd843_name_of_dvbe_is_legal_name():
    assert LEGAL != SHORT
    assert _fields(_inputs(_parker()))[PD843_NAME] == LEGAL


def test_pd843_follows_the_profile_not_a_literal():
    real = fop.load_profile

    def patched():
        p = real()
        p["legal_name"] = "Profile Legal Name, Inc."
        return p
    fop.load_profile = patched
    try:
        got = _fields(_inputs(_employee()))
    finally:
        fop.load_profile = real
    assert got[PD843_NAME] == got[DARFUR_NAME] == got[OBS1000_NAME] == "Profile Legal Name, Inc."


def test_calrecycle_obs1000_darfur_company_name_is_legal_name():
    got = _fields(_inputs(_employee()))
    assert got[DARFUR_NAME] == LEGAL and got[OBS1000_NAME] == LEGAL
    cr = [a for a in fop.ANNOTATIONS if a["page"] == 15]
    assert len(cr) == 1 and cr[0]["key"] == "legal_name", cr
    assert fop.load_profile()[cr[0]["key"]] == LEGAL


# ---------- the template ----------

def test_template_has_no_prefilled_signer():
    with open(TEMPLATE, encoding="utf-8") as fh:
        t = json.load(fh)
    assert "signature" not in t.get("rep", {}), "template carries a typed signature"
    assert not any(str(v).strip() for v in t.get("signer", {}).values()), t.get("signer")


def test_no_signer_stops_missing():
    msg = _exit_message(_inputs({}))
    assert msg.startswith("[MISSING — NEEDS INPUT] Signer"), msg
    with open(TEMPLATE, encoding="utf-8") as fh:
        assert _exit_message(json.load(fh)).startswith("[MISSING — NEEDS INPUT]")


def test_signer_without_email_stops_missing():
    assert _exit_message(_inputs({"name": "Test Rep", "title": "x"})).startswith(
        "[MISSING — NEEDS INPUT]")


# ---------- BBS employees only ----------

def test_non_bbs_signer_refused():
    msg = _exit_message(_inputs({"name": "Agency Buyer", "email": "buyer@cdcr.ca.gov"}))
    assert msg.startswith("REFUSED"), msg


def test_nameless_signer_with_non_bbs_email_refused():
    """The domain check runs before the name check."""
    assert _exit_message(_inputs({"email": "buyer@cdcr.ca.gov"})).startswith("REFUSED")


def test_double_at_refused():
    msg = _exit_message(_inputs({"name": "X", "email": "x@evil.com@" + DOMAIN}))
    assert msg.startswith("REFUSED"), msg


def test_non_ascii_lookalike_email_refused():
    # KELVIN SIGN (U+212A) lower-cases to "k"; it must not pass as a BBS address
    msg = _exit_message(_inputs({"name": "Kim", "email": "\u212aim@" + DOMAIN}))
    assert msg.startswith("REFUSED"), msg


def test_lookalike_domain_refused():
    msg = _exit_message(_inputs({"name": "X", "email": "x@evil" + DOMAIN}))
    assert msg.startswith("REFUSED"), msg


# ---------- delegates ----------

def test_delegate_signer_signs_all_three_lines():
    inp = _inputs(_parker())
    got = _fields(inp)
    _assert_signed(got, inp, "Parker Marshall")
    assert got[CR_PRINT] == "Parker Marshall" and got[CR_TITLE] == "Sales Manager"


def test_parker_via_recorded_alias_signs():
    alias = _delegate("Parker Marshall")["aliases"][0]
    inp = _inputs(_parker(email=alias))
    _assert_signed(_fields(inp), inp, "Parker Marshall")


def test_rep_names_parker_on_a_bid_kim_prepared():
    inp = _inputs(_parker(), rep=KIM_REP)
    got = _fields(inp)
    _assert_signed(got, inp, "Parker Marshall")
    assert got["OBS RFQ 4007(B) - Business Contact Person"] == "Kim Quezon"


def test_parkers_name_with_another_email_is_flagged_as_email_mismatch():
    inp = _inputs(_parker(email="parker.m@" + DOMAIN))
    _assert_blank(_fields(inp))
    block = fop.signer_confirmation(fop.load_profile(), inp)
    assert any("email does not match the delegate's recorded address" in l for l in block), block
    assert not any("not a signature delegate" in l for l in block)


def test_delegate_email_with_another_name_is_not_applied():
    inp = _inputs(_employee(email=_delegate("Parker Marshall")["email"]))
    _assert_blank(_fields(inp))


def test_signature_text_is_never_free_text():
    """A typed `signature` in the inputs is ignored; the name of record is written."""
    inp = _inputs(_parker(name="parker   marshall", signature="Somebody Else"))
    inp["rep"]["signature"] = "Somebody Else"
    got = _fields(inp)
    _assert_signed(got, inp, "Parker Marshall")
    assert "Somebody Else" not in got.values()


# ---------- any other BBS employee ----------

def test_non_delegate_signer_blank_and_flagged_on_all_three_lines():
    signer = _employee()
    inp = _inputs(signer)
    got = _fields(inp)
    _assert_blank(got)
    assert got[CR_PRINT] == signer["name"] and got[CR_TITLE] == signer["title"]
    block = fop.signer_confirmation(fop.load_profile(), inp)
    flag = [l for l in block if "SIGNATURE REQUIRED" in l]
    assert len(flag) == 1 and signer["name"] in flag[0]
    for line in SIGNED:
        assert line in flag[0], line


def test_non_delegate_asking_for_a_delegates_name_gets_nothing():
    for d in DELEGATES:
        got = _fields(_inputs(_employee(signature=d["name"])))
        _assert_blank(got)


def test_confirmation_block_format():
    inp = _inputs(_employee())
    first = fop.signer_confirmation(fop.load_profile(), inp)[0]
    assert first.startswith("Signer: Test Rep <test.rep@%s> — applied to: " % DOMAIN), first
    assert "CalRecycle 74, OBS 4007(B) Bidder, Darfur OBS 1500 (blank for hand signature)" in first
    assert "CalRecycle 74 PCRC/SABRC = NA/NA — confirm before sending." in first
    inp = _inputs(_parker())
    assert "(delegated signature applied)" in fop.signer_confirmation(fop.load_profile(), inp)[0]


# ---------- the profile's delegation ----------

def test_delegation_roles_resolve_to_representatives():
    roles = VP["signature_delegation"]["delegates"]
    reps = {r["role"]: r for r in VP["authorized_representatives"]}
    assert roles == ["sales_manager", "dvbe_owner"], roles
    assert [d["name"] for d in DELEGATES] == [reps[r]["name"] for r in roles]
    assert "pmarshall@" + DOMAIN in _delegate("Parker Marshall")["aliases"]
    for r in roles:
        assert reps[r]["signature_image"], r
    assert "signature_image" not in VP["default_rep"], "Parker's image moved to sales_manager"


def test_no_profile_entry_assigns_obs1000_a_signer():
    """OBS 1000's signer is not ruled (field-maps.md; canon, Open). The profile
    must not say otherwise, or a skill reading `signs` would stamp it."""
    for r in VP["authorized_representatives"] + [VP["default_rep"]]:
        assert "OBS 1000" not in r.get("signs", ""), (r["role"], r["signs"])


# ---------- unchanged: DV-owner lines ----------

def test_dv_owner_lines_stay_jacksons_whoever_signs():
    owner = next(r for r in VP["authorized_representatives"] if r["role"] == "dvbe_owner")
    got = _fields(_inputs(_employee(), rep=KIM_REP))
    assert got["DGS PD 843 - DVBE Owner/ Signature 1"] == owner["name"]
    assert got["Payee Data Record STD 204 - Auth Rep. Signature"] == owner["name"]


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
