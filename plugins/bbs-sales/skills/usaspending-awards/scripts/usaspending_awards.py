#!/usr/bin/env python3
"""
USAspending awards: a narrow, read-only lookup of past federal contract awards.

Three questions, one request each (plus one to check an agency name):

    awards          which prime contracts match (who won, how much, when)
    top-recipients  who holds the most obligations in a market
    subawards       first-tier subcontracts primes have reported

Usage:
    python usaspending_awards.py awards --naics 423450 --agency VA
    python usaspending_awards.py awards --recipient FRK5MJD35GN5 --start 2022-10-01
    python usaspending_awards.py top-recipients --naics 423450 --agency "Department of Veterans Affairs"
    python usaspending_awards.py subawards --recipient "Bechtel" --naics 3329
    python usaspending_awards.py awards --naics 423450 --set-aside SDVOSBC --json

No key: the API is public. It is searched with POST requests, but only the
search endpoints: nothing is created, changed or downloaded in bulk.

Exit codes:
    0  ran (zero rows is still a run)
    1  the API refused or failed; the reason is printed
    2  bad input, including an agency name USAspending does not know

API contract, from the endpoint docs in fedspendingtransparency/usaspending-api,
api_contracts/ (read 2026-10-02), and checked against the live API that day:
  * POST https://api.usaspending.gov/api/v2/search/spending_by_award/
    and .../spending_by_category/recipient/. award_type_codes is required.
  * naics_codes is {"require": [...]}: a code matches as a prefix.
  * agencies[].name must be USAspending's exact toptier name. A near miss such
    as "Veterans Affairs" returns zero rows and no error, so every --agency is
    checked against GET .../references/toptier_agencies/ before searching.
  * recipient_search_text takes ONE string: a name or a UEI.
  * Searches start no earlier than 2007-10-01.
"""

import argparse
import difflib
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

API = "https://api.usaspending.gov/api/v2"
SITE = "https://www.usaspending.gov"
CONTRACT_TYPES = ["A", "B", "C", "D"]  # BPA call, purchase order, delivery order, definitive contract
EARLIEST = date(2007, 10, 1)
MAX_ROWS = 100
# The API repeats this on every response. It is about searches before EARLIEST,
# which this script refuses, so it is noise here rather than a warning.
BOILERPLATE = "time period start and end dates are currently limited to an earliest date of 2007-10-01"

AWARD_FIELDS = ["Award ID", "Recipient Name", "Recipient UEI", "Award Amount", "Awarding Agency",
                "Awarding Sub Agency", "Start Date", "End Date", "NAICS", "PSC", "Description",
                "Place of Performance State Code", "generated_internal_id", "recipient_id"]
SUB_FIELDS = ["Sub-Award ID", "Sub-Awardee Name", "Sub-Recipient UEI", "Sub-Award Amount",
              "Sub-Award Date", "Sub-Award Description", "Prime Recipient Name", "Prime Award ID",
              "Awarding Agency", "NAICS", "PSC"]


class LookupFailed(RuntimeError):
    pass


def _call(path, payload=None, opener=None):
    opener = opener or urllib.request.urlopen
    url = f"{API}/{path}"
    if payload is None:
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    else:
        req = urllib.request.Request(url, method="POST", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json",
                                              "Accept": "application/json"})
    try:
        with opener(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            body = e.read().decode("utf-8", "replace")
            detail = json.loads(body).get("detail", body)
        except Exception:
            pass
        raise LookupFailed(f"USAspending returned HTTP {e.code}. {str(detail)[:400]}".strip()) from None
    except urllib.error.URLError as e:
        raise LookupFailed(f"could not reach USAspending: {e.reason}") from None
    except ValueError:
        raise LookupFailed("USAspending answered with something that is not JSON.") from None


def resolve_agency(name, opener=None):
    """USAspending's exact toptier name for `name`, or a LookupFailed listing near matches.

    Accepts the exact name in any case, or the agency's abbreviation (VA, DOD).
    Anything else is refused: a near-miss name silently returns zero rows.
    """
    data = _call("references/toptier_agencies/", opener=opener)
    agencies = data.get("results") or []
    want = name.strip().lower()
    for a in agencies:
        if (a.get("agency_name") or "").lower() == want:
            return a["agency_name"]
    abbr = [a for a in agencies if (a.get("abbreviation") or "").lower() == want]
    if len(abbr) == 1:
        return abbr[0]["agency_name"]
    names = [a.get("agency_name") or "" for a in agencies]
    near = [n for n in names if want in n.lower()] or difflib.get_close_matches(name, names, n=5, cutoff=0.5)
    hint = f" Did you mean: {'; '.join(near[:5])}?" if near else ""
    raise ValueError(f"USAspending has no toptier agency named {name!r}. A near miss returns zero "
                     f"rows with no error, so this run stops here.{hint}")


def build_filters(args, agency):
    f = {"award_type_codes": CONTRACT_TYPES,
         "time_period": [{"start_date": args.start.isoformat(), "end_date": args.end.isoformat()}]}
    if args.new_only:
        f["time_period"][0]["date_type"] = "new_awards_only"
    naics = [c.strip() for c in (args.naics or "").split(",") if c.strip()]
    if naics:
        f["naics_codes"] = {"require": naics}
    if agency:
        f["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency}]
    if args.recipient:
        f["recipient_search_text"] = [args.recipient.strip()]
    if args.keyword:
        f["keywords"] = [args.keyword.strip()]
    if args.set_aside:
        f["set_aside_type_codes"] = [c.strip().upper() for c in args.set_aside.split(",") if c.strip()]
    if args.state:
        f["place_of_performance_locations"] = [{"country": "USA", "state": args.state.strip().upper()}]
    return f


def _code(v):
    if isinstance(v, dict):
        return v.get("code") or ""
    return "" if v is None else str(v)


def _money(v):
    if v is None or v == "":
        return "[none given]"
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _md(s):
    return ("" if s is None else str(s)).replace("|", "/").replace("\n", " ").strip()


def rows_for(mode, results):
    out = []
    for r in results:
        if mode == "awards":
            gid = r.get("generated_internal_id")
            out.append({
                "awardId": r.get("Award ID"), "recipient": r.get("Recipient Name"),
                "recipientUei": r.get("Recipient UEI"), "awardAmount": r.get("Award Amount"),
                "agency": r.get("Awarding Agency"), "subAgency": r.get("Awarding Sub Agency"),
                "start": r.get("Start Date"), "end": r.get("End Date"),
                "naics": _code(r.get("NAICS")), "psc": _code(r.get("PSC")),
                "state": _code(r.get("Place of Performance State Code")),
                "description": r.get("Description"),
                "link": f"{SITE}/award/{gid}" if gid else "",
            })
        elif mode == "subawards":
            pgid = r.get("prime_award_generated_internal_id")
            out.append({
                "subAwardId": r.get("Sub-Award ID"), "subAwardee": r.get("Sub-Awardee Name"),
                "subRecipientUei": r.get("Sub-Recipient UEI"), "subAwardAmount": r.get("Sub-Award Amount"),
                "subAwardDate": r.get("Sub-Award Date"), "description": r.get("Sub-Award Description"),
                "prime": r.get("Prime Recipient Name"), "primeAwardId": r.get("Prime Award ID"),
                "agency": r.get("Awarding Agency"), "naics": _code(r.get("NAICS")),
                "psc": _code(r.get("PSC")),
                "primeLink": f"{SITE}/award/{pgid}" if pgid else "",
            })
        else:
            rid = r.get("recipient_id")
            out.append({
                "recipient": r.get("name"), "recipientUei": r.get("uei"), "amount": r.get("amount"),
                "link": f"{SITE}/recipient/{rid}/latest" if rid else "",
            })
    return out


AMOUNT_MEANS = {
    "awards": ("Award amount is USAspending's 'Award Amount' for the whole award, every year of it, "
               "not only the part inside the window. The window selects awards with activity in it."),
    "top-recipients": ("Amount is the sum of obligations on transactions dated inside the window "
                       "(spending_level=transactions), so it is not total contract value."),
    "subawards": ("Sub-award amount is as the prime reported it. Subaward data is only what primes "
                  "report for their first tier, so an empty result does not prove there was none."),
}


def render(mode, rows, meta):
    out = [f"Source: USAspending API ({meta['endpoint']}), queried {meta['retrieved']} UTC.",
           f"Filters: {meta['filters']}.",
           f"Requests used: {meta['requests']}. Rows: {len(rows)}"
           + (" (more exist: narrow the query or raise --rows)." if meta["hasNext"] else "."),
           AMOUNT_MEANS[mode]]
    for m in meta["messages"]:
        out.append(f"USAspending says: {m}")
    out.append("")
    if not rows:
        out.append("No rows matched.")
        return "\n".join(out)
    if mode == "awards":
        out.append("| Award amount | Recipient | UEI | Agency / sub-agency | Award ID | Start | End | NAICS | PSC | PoP | Description | Link |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            out.append("| " + " | ".join(_md(x) for x in (
                _money(r["awardAmount"]), r["recipient"], r["recipientUei"],
                " / ".join(x for x in (r["agency"], r["subAgency"]) if x), r["awardId"], r["start"],
                r["end"], r["naics"], r["psc"], r["state"], (r["description"] or "")[:120], r["link"])) + " |")
    elif mode == "subawards":
        out.append("| Sub-award amount | Sub-awardee | UEI | Date | Prime | Prime award | Agency | NAICS | Description | Prime link |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            out.append("| " + " | ".join(_md(x) for x in (
                _money(r["subAwardAmount"]), r["subAwardee"], r["subRecipientUei"], r["subAwardDate"],
                r["prime"], r["primeAwardId"], r["agency"], r["naics"],
                (r["description"] or "")[:120], r["primeLink"])) + " |")
    else:
        out.append("| Obligations in window | Recipient | UEI | Link |")
        out.append("|---|---|---|---|")
        for r in rows:
            out.append("| " + " | ".join(_md(x) for x in (
                _money(r["amount"]), r["recipient"], r["recipientUei"], r["link"])) + " |")
    return "\n".join(out)


def _iso(s):
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{s!r} is not YYYY-MM-DD")


def build_parser():
    p = argparse.ArgumentParser(description="Read-only lookup of past federal contract awards.")
    p.add_argument("mode", choices=["awards", "top-recipients", "subawards"])
    p.add_argument("--naics", help="NAICS codes or prefixes, comma-separated (one request)")
    p.add_argument("--agency", help="awarding toptier agency: exact USAspending name or abbreviation")
    p.add_argument("--recipient", help="ONE recipient name or UEI")
    p.add_argument("--keyword", help="a keyword search across the award")
    p.add_argument("--set-aside", dest="set_aside", help="set-aside type codes, comma-separated, e.g. SDVOSBC")
    p.add_argument("--state", help="place-of-performance state, e.g. CA")
    p.add_argument("--start", type=_iso, help="YYYY-MM-DD (default three years before --end)")
    p.add_argument("--end", type=_iso, help="YYYY-MM-DD (default today)")
    p.add_argument("--new-only", dest="new_only", action="store_true",
                   help="only awards whose base transaction falls in the window")
    p.add_argument("--rows", type=int, default=25, help=f"rows to return (default 25, max {MAX_ROWS})")
    p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    return p


def main(argv=None, opener=None, today=None, now=None):
    args = build_parser().parse_args(argv)
    if not any((args.naics, args.agency, args.recipient, args.keyword)):
        print("Give at least one of --naics, --agency, --recipient or --keyword. All federal "
              "contracts at once is not a narrow lookup.", file=sys.stderr)
        return 2
    if not 1 <= args.rows <= MAX_ROWS:
        print(f"--rows must be between 1 and {MAX_ROWS}.", file=sys.stderr)
        return 2
    today = today or date.today()
    args.end = args.end or today
    args.start = args.start or (args.end - timedelta(days=3 * 365))
    if args.start > args.end:
        print("--start is after --end.", file=sys.stderr)
        return 2
    if args.start < EARLIEST:
        print(f"USAspending searches start no earlier than {EARLIEST.isoformat()}.", file=sys.stderr)
        return 2

    requests = 0
    agency = None
    try:
        if args.agency:
            requests += 1
            agency = resolve_agency(args.agency, opener)
        filters = build_filters(args, agency)
        if args.mode == "top-recipients":
            endpoint = "search/spending_by_category/recipient/"
            payload = {"filters": filters, "category": "recipient", "limit": args.rows, "page": 1,
                       "spending_level": "transactions"}
        else:
            sub = args.mode == "subawards"
            fields = SUB_FIELDS if sub else AWARD_FIELDS
            endpoint = "search/spending_by_award/"
            payload = {"filters": filters, "fields": fields, "limit": args.rows, "page": 1,
                       "sort": fields[3], "order": "desc",
                       # spending_level, not the `subawards` flag the API says it will retire.
                       "spending_level": "subawards" if sub else "awards"}
        requests += 1
        body = _call(endpoint, payload, opener)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    except LookupFailed as e:
        print(f"USAspending lookup failed on request {requests}: {e}", file=sys.stderr)
        return 1

    if "results" not in body:
        print(f"USAspending lookup failed: the response has no results list. "
              f"{json.dumps(body)[:400]}", file=sys.stderr)
        return 1
    rows = rows_for(args.mode, body.get("results") or [])
    now = now or datetime.now(timezone.utc)
    shown = {k: v for k, v in filters.items() if k != "award_type_codes"}
    meta = {
        "endpoint": endpoint, "retrieved": now.strftime("%Y-%m-%d %H:%M"),
        "filters": json.dumps(shown, separators=(", ", ": ")), "requests": requests,
        "hasNext": bool((body.get("page_metadata") or {}).get("hasNext")),
        "messages": [m for m in (body.get("messages") or []) if BOILERPLATE not in m],
    }
    if args.json:
        print(json.dumps({"meta": meta, "rows": rows}, indent=2))
    else:
        print(render(args.mode, rows, meta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
