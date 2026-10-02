#!/usr/bin/env python3
"""test_sam_opportunities.py — the lookup is read-only, loud, and never leaks the key.

Run it:
    python3 test_sam_opportunities.py

Stdlib only, no pytest, no network: every test hands main() a fake opener that
records the request it was given and returns a canned SAM.gov response.
"""
import io
import json
import os
import sys
import traceback
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import sam_opportunities as so  # noqa: E402

KEY = "TESTKEY-not-a-real-key-123"
NOW = datetime(2026, 10, 2, 18, 0, tzinfo=timezone.utc)
TODAY = date(2026, 10, 2)


def notice(nid, type_="Solicitation", deadline="2026-10-20T14:00:00-07:00", set_aside=None,
           active="Yes", naics="423450"):
    return {
        "noticeId": nid, "title": f"Title {nid}", "solicitationNumber": f"SOL-{nid}",
        "fullParentPathName": "VETERANS AFFAIRS, DEPARTMENT OF.VETERANS AFFAIRS, DEPARTMENT OF.262-NETWORK CONTRACT OFFICE 22",
        "postedDate": "2026-09-20", "type": type_, "responseDeadLine": deadline,
        "naicsCode": naics, "classificationCode": "8415", "typeOfSetAside": set_aside,
        "typeOfSetAsideDescription": None, "active": active,
        "placeOfPerformance": {"state": {"code": "CA"}},
        "uiLink": f"https://sam.gov/opp/{nid}/view",
    }


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Opener:
    def __init__(self, bodies=None, error=None):
        self.bodies = list(bodies or [])
        self.error = error
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        if self.error:
            raise self.error
        return FakeResp(json.dumps(self.bodies.pop(0)).encode())


def run(argv, opener, key=KEY):
    old = os.environ.get(so.KEY_ENV)
    if key is None:
        os.environ.pop(so.KEY_ENV, None)
    else:
        os.environ[so.KEY_ENV] = key
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = so.main(argv, opener=opener, today=TODAY, now=NOW)
    finally:
        if old is None:
            os.environ.pop(so.KEY_ENV, None)
        else:
            os.environ[so.KEY_ENV] = old
    return code, out.getvalue(), err.getvalue()


def body(*notices, total=None):
    return {"totalRecords": len(notices) if total is None else total, "limit": 1000,
            "offset": 0, "opportunitiesData": list(notices)}


# --- tests -----------------------------------------------------------------

def test_get_only_and_documented_params():
    op = Opener([body(notice("a"))])
    code, out, _ = run(["--naics", "423450", "--state", "ca"], op)
    assert code == 0
    assert len(op.requests) == 1
    req = op.requests[0]
    assert req.get_method() == "GET"
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
    assert req.full_url.startswith("https://api.sam.gov/opportunities/v2/search?")
    assert q["ncode"] == ["423450"] and q["state"] == ["CA"]
    assert q["postedTo"] == ["10/02/2026"] and q["postedFrom"] == ["07/04/2026"]
    assert q["limit"] == ["1000"] and q["offset"] == ["0"]


def test_key_never_printed():
    op = Opener([body(notice("a"))])
    code, out, err = run(["--naics", "423450"], op)
    assert KEY not in out and KEY not in err
    code, out, err = run(["--naics", "423450", "--json"], Opener([body(notice("a"))]))
    assert KEY not in out and KEY not in err


def test_key_redacted_from_api_error():
    err_body = io.BytesIO(f"An invalid api_key was supplied: {KEY}".encode())
    e = urllib.error.HTTPError(so.API_URL + "?api_key=" + KEY, 403, "Forbidden", {}, err_body)
    code, out, err = run(["--naics", "423450"], Opener(error=e))
    assert code == 1
    assert KEY not in out and KEY not in err
    assert "[REDACTED]" in err and "HTTP 403" in err


def test_rate_limit_hint():
    e = urllib.error.HTTPError(so.API_URL, 429, "Too Many Requests", {}, io.BytesIO(b""))
    code, _, err = run(["--naics", "423450"], Opener(error=e))
    assert code == 1 and "10 requests a day" in err and "entity" in err


def test_404_is_not_reported_as_an_empty_result():
    """A refused request also answers 404; "nothing matched" would be a plausible wrong answer."""
    e = urllib.error.HTTPError(so.API_URL, 404, "Not Found", {}, io.BytesIO(b""))
    code, out, err = run(["--naics", "423450"], Opener(error=e))
    assert code == 1 and "No open notices matched." not in out
    assert "NOT a confirmed empty result" in err


def test_zero_matches_on_200_is_an_empty_result():
    code, out, _ = run(["--naics", "423450"], Opener([body()]))
    assert code == 0 and "No open notices matched." in out


def test_missing_key_is_loud():
    op = Opener([body()])
    code, out, err = run(["--naics", "423450"], op, key=None)
    assert code == 2 and "[MISSING — NEEDS INPUT]" in err and "Never paste" in err
    assert op.requests == []


def test_needs_a_narrowing_filter():
    op = Opener([body()])
    code, _, err = run([], op)
    assert code == 2 and op.requests == []


def test_window_over_a_year_refused():
    code, _, err = run(["--naics", "1", "--days", "400"], Opener([body()]))
    assert code == 2 and "one year" in err


def test_request_cap_refuses_before_spending():
    op = Opener([body()] * 5)
    code, _, err = run(["--naics", "1,2,3,4,5"], op)
    assert code == 2 and op.requests == []


def test_one_request_per_naics_and_dedupe():
    op = Opener([body(notice("a"), notice("b")), body(notice("b"), notice("c"))])
    code, out, _ = run(["--naics", "423450,339113", "--json"], op)
    assert code == 0 and len(op.requests) == 2
    data = json.loads(out)
    assert [n["noticeId"] for n in data["notices"]] == ["a", "b", "c"]
    assert data["meta"]["requests"] == 2


def test_closed_and_excluded_types_are_counted_not_dropped_silently():
    op = Opener([body(
        notice("open"),
        notice("past", deadline="2026-09-01T12:00:00-04:00"),
        notice("archived", active="No"),
        notice("award", type_="Award Notice"),
        notice("nodate", type_="Sources Sought", deadline=None),
    )])
    code, out, _ = run(["--naics", "423450", "--json"], op)
    meta = json.loads(out)["meta"]
    ids = [n["noticeId"] for n in json.loads(out)["notices"]]
    assert ids == ["open", "nodate"]
    assert meta["closed"] == 2 and meta["excludedTypes"] == {"Award Notice": 1}
    assert meta["undated"] == 1


def test_truncation_is_reported():
    op = Opener([body(notice("a"), total=2400)])
    code, out, _ = run(["--naics", "423450"], op)
    assert code == 0 and "TRUNCATED" in out and "1 of 2400" in out


def test_sorted_by_deadline():
    op = Opener([body(notice("late", deadline="2026-12-01"), notice("soon", deadline="2026-10-05"))])
    _, out, _ = run(["--naics", "1", "--json"], op)
    assert [n["noticeId"] for n in json.loads(out)["notices"]] == ["soon", "late"]


def test_set_aside_fit_follows_canon_and_flags_the_rest():
    f = so.set_aside_fit
    assert f("SDVOSBC", "423450").startswith("Eligible: SDVOSB")
    assert "sole source" in f("SDVOSBS", "423450")
    assert "[FLAG: confirm the size standard for NAICS 423450]" in f("SBA", "423450")
    assert f("VSA", "1").startswith("[FLAG:")
    assert f("8A", "1").startswith("Not eligible as recorded") and "8(a)" in f("8A", "1")
    assert f("HZC", "1").startswith("Not eligible as recorded")
    assert f("BICiv", "1").startswith("Not eligible as recorded")
    assert f("NEWCODE", "1").startswith("[FLAG: unrecognized")
    assert f(None, "1") == so.FIT_OPEN


def test_federal_output_never_says_dvbe():
    """Certifications follow the channel: a federal lookup says SDVOSB, never DVBE."""
    codes = ["SDVOSBC", "SDVOSBS", "SBA", "SBP", "VSA", "VSS", "LAS", None, "X"] + list(so.NO_CERT)
    for c in codes:
        assert "DVBE" not in so.set_aside_fit(c, "1").replace("EDWOSB", "")
    op = Opener([body(notice("a", set_aside="SDVOSBC"))])
    _, out, _ = run(["--naics", "1"], op)
    assert "DVBE" not in out


def test_table_has_source_and_timestamp():
    _, out, _ = run(["--naics", "1"], Opener([body(notice("a"))]))
    assert out.startswith("Source: SAM.gov Get Opportunities API (v2), queried 2026-10-02 18:00 UTC.")
    assert "https://sam.gov/opp/a/view" in out


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
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
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
