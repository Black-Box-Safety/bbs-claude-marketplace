#!/usr/bin/env python3
"""test_usaspending_awards.py — search endpoints only, exact agency names, loud failures.

Run it:
    python3 test_usaspending_awards.py

Stdlib only, no pytest, no network: main() gets a fake opener that records each
request and returns a canned USAspending response.
"""
import io
import json
import os
import sys
import traceback
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import usaspending_awards as ua  # noqa: E402

NOW = datetime(2026, 10, 2, 18, 0, tzinfo=timezone.utc)
TODAY = date(2026, 10, 2)
AGENCIES = {"results": [
    {"agency_name": "Department of Veterans Affairs", "abbreviation": "VA"},
    {"agency_name": "Department of Defense", "abbreviation": "DOD"},
    {"agency_name": "United States Court of Appeals for Veterans Claims", "abbreviation": "USCAVC"},
]}


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Opener:
    def __init__(self, routes=None, error=None):
        self.routes = routes or {}
        self.error = error
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        if self.error:
            raise self.error
        for frag, body in self.routes.items():
            if frag in req.full_url:
                return FakeResp(json.dumps(body).encode())
        raise AssertionError(f"unexpected URL {req.full_url}")


def run(argv, opener):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ua.main(argv, opener=opener, today=TODAY, now=NOW)
    return code, out.getvalue(), err.getvalue()


def payload(req):
    return json.loads(req.data.decode())


AWARD = {"Award ID": "36C24W25P0124", "Recipient Name": "SOME VENDOR", "Recipient UEI": "ABC123DEF456",
         "Award Amount": 315475.36, "Awarding Agency": "Department of Veterans Affairs",
         "Awarding Sub Agency": "Department of Veterans Affairs", "Start Date": "2025-11-17",
         "End Date": "2026-01-31", "NAICS": {"code": "423450"}, "PSC": {"code": "6515"},
         "Place of Performance State Code": "CA", "Description": "GLOVES",
         "generated_internal_id": "CONT_AWD_X"}
BOILER = ("For searches, time period start and end dates are currently limited to an earliest "
          "date of 2007-10-01.  For data going back ...")


def awards_body(*rows, has_next=False, messages=(BOILER,)):
    return {"results": list(rows), "page_metadata": {"page": 1, "hasNext": has_next},
            "messages": list(messages)}


# --- tests -----------------------------------------------------------------

def test_search_endpoint_and_documented_filters():
    op = Opener({"spending_by_award": awards_body(AWARD)})
    code, out, _ = run(["awards", "--naics", "423450,3391", "--state", "ca", "--set-aside", "sdvosbc"], op)
    assert code == 0 and len(op.requests) == 1
    req = op.requests[0]
    assert req.get_method() == "POST"
    assert req.full_url == "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    f = payload(req)["filters"]
    assert f["award_type_codes"] == ["A", "B", "C", "D"]
    assert f["naics_codes"] == {"require": ["423450", "3391"]}
    assert f["set_aside_type_codes"] == ["SDVOSBC"]
    assert f["place_of_performance_locations"] == [{"country": "USA", "state": "CA"}]
    assert f["time_period"] == [{"start_date": "2023-10-03", "end_date": "2026-10-02"}]


def test_only_search_and_reference_endpoints_are_called():
    op = Opener({"toptier_agencies": AGENCIES, "spending_by_category": awards_body()})
    run(["top-recipients", "--agency", "VA"], op)
    for r in op.requests:
        assert "/api/v2/search/" in r.full_url or "/api/v2/references/" in r.full_url
        assert "download" not in r.full_url


def test_agency_abbreviation_and_case_resolve_to_exact_name():
    for given in ("VA", "department of veterans affairs"):
        op = Opener({"toptier_agencies": AGENCIES, "spending_by_award": awards_body(AWARD)})
        code, _, _ = run(["awards", "--agency", given], op)
        assert code == 0
        assert payload(op.requests[1])["filters"]["agencies"] == [
            {"type": "awarding", "tier": "toptier", "name": "Department of Veterans Affairs"}]


def test_near_miss_agency_refused_with_suggestion_before_searching():
    op = Opener({"toptier_agencies": AGENCIES, "spending_by_award": awards_body(AWARD)})
    code, _, err = run(["awards", "--agency", "Veterans Affairs"], op)
    assert code == 2 and "Department of Veterans Affairs" in err
    assert len(op.requests) == 1 and "toptier_agencies" in op.requests[0].full_url


def test_needs_a_narrowing_filter():
    op = Opener({})
    code, _, _ = run(["awards"], op)
    assert code == 2 and op.requests == []


def test_before_2007_refused():
    code, _, err = run(["awards", "--naics", "1", "--start", "2005-01-01"], Opener({}))
    assert code == 2 and "2007-10-01" in err


def test_http_error_detail_is_reported():
    body = io.BytesIO(b'{"detail": "Missing value: \'filters|award_type_codes\' is a required field"}')
    e = urllib.error.HTTPError(ua.API, 422, "Unprocessable", {}, body)
    code, out, err = run(["awards", "--naics", "1"], Opener(error=e))
    assert code == 1 and "HTTP 422" in err and "award_type_codes" in err and out == ""


def test_response_without_results_is_a_failure():
    code, _, err = run(["awards", "--naics", "1"], Opener({"spending_by_award": {"detail": "x"}}))
    assert code == 1 and "no results list" in err


def test_awards_table_carries_source_meaning_and_link():
    op = Opener({"spending_by_award": awards_body(AWARD, has_next=True)})
    code, out, _ = run(["awards", "--naics", "423450"], op)
    assert out.startswith("Source: USAspending API (search/spending_by_award/), queried 2026-10-02 18:00 UTC.")
    assert "every year of it" in out and "more exist" in out
    assert "315,475.36" in out and "https://www.usaspending.gov/award/CONT_AWD_X" in out
    assert BOILER[:40] not in out


def test_other_api_messages_are_shown():
    op = Opener({"spending_by_award": awards_body(AWARD, messages=(BOILER, "Field X is deprecated"))})
    _, out, _ = run(["awards", "--naics", "1"], op)
    assert "USAspending says: Field X is deprecated" in out


def test_subawards_mode_and_empty_result_caveat():
    op = Opener({"spending_by_award": awards_body()})
    code, out, _ = run(["subawards", "--recipient", "FRK5MJD35GN5"], op)
    p = payload(op.requests[0])
    assert "subawards" not in p and p["spending_level"] == "subawards"
    assert p["sort"] == "Sub-Award Amount"
    assert code == 0 and "No rows matched." in out and "does not prove there was none" in out


def test_top_recipients_amount_is_labelled_as_window_obligations():
    body = {"results": [{"name": "VENDOR", "uei": "U1", "amount": 1000.5, "recipient_id": "rid-C"}],
            "page_metadata": {"hasNext": False}, "messages": []}
    op = Opener({"spending_by_category/recipient": body})
    _, out, _ = run(["top-recipients", "--naics", "423450"], op)
    p = payload(op.requests[0])
    assert p["spending_level"] == "transactions" and p["category"] == "recipient"
    assert "not total contract value" in out and "1,000.50" in out
    assert "https://www.usaspending.gov/recipient/rid-C/latest" in out


def test_recipient_is_one_string():
    op = Opener({"spending_by_award": awards_body()})
    run(["awards", "--recipient", "  FRK5MJD35GN5 "], op)
    assert payload(op.requests[0])["filters"]["recipient_search_text"] == ["FRK5MJD35GN5"]


def test_new_only_sets_date_type():
    op = Opener({"spending_by_award": awards_body()})
    run(["awards", "--naics", "1", "--new-only"], op)
    assert payload(op.requests[0])["filters"]["time_period"][0]["date_type"] == "new_awards_only"


def test_rows_bounds():
    code, _, _ = run(["awards", "--naics", "1", "--rows", "500"], Opener({}))
    assert code == 2


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
