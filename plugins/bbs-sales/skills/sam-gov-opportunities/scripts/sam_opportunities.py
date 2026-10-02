#!/usr/bin/env python3
"""
SAM.gov opportunities: a narrow, read-only lookup of open federal solicitations.

Calls SAM.gov's public Get Opportunities API (v2) with GET requests only, using
the key in the SAM_GOV_API_KEY environment variable. Never writes anything,
never prints the key, never stores a result.

Usage:
    python sam_opportunities.py --naics 423450
    python sam_opportunities.py --naics 423450,339113 --state CA
    python sam_opportunities.py --agency "Veterans Affairs" --set-aside SDVOSBC
    python sam_opportunities.py --solnum 36C26226Q0123 --include-closed
    python sam_opportunities.py --naics 423450 --json

At least one of --naics, --agency, --solnum or --keyword is required: a date
window alone returns every federal notice and burns the daily request budget.

Exit codes:
    0  ran (zero results is still a run)
    1  the API refused or failed; the reason is printed, the key never is
    2  bad input, or SAM_GOV_API_KEY is not set

API contract, as documented at
https://open.gsa.gov/api/get-opportunities-public-api/ (read 2026-10-02):
  * GET https://api.sam.gov/opportunities/v2/search
  * api_key, postedFrom and postedTo (MM/dd/yyyy) are mandatory; the window is
    at most one year.
  * limit is at most 1000 per page. offset is "the page index", ambiguously, so
    this script never pages: over 1000 matches is reported TRUNCATED.
  * ncode takes one NAICS code; organizationName searches department or
    sub-tier names; typeOfSetAside takes one code.
  * A personal key whose SAM.gov account has no role on an entity is limited
    to 10 requests a day; one associated with an entity gets 1,000 (rate
    limits from GSA's PSC API page and the SAM.gov System Account User Guide,
    read 2026-10-02). So a run is one request per NAICS code, capped by
    --max-requests, and the request count is printed every time.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

API_URL = "https://api.sam.gov/opportunities/v2/search"
KEY_ENV = "SAM_GOV_API_KEY"
PAGE_LIMIT = 1000
MAX_WINDOW_DAYS = 364

# Notice types kept by default: the ones a supplier can still respond to. The
# filter runs on the response's `type` text rather than the `ptype` request
# parameter so that one request covers every kept type; at 10 requests a day
# per type it would not. Everything excluded is counted by type in the output,
# so a type string that does not match here shows up instead of vanishing.
TYPE_CODES = {
    "o": "Solicitation",
    "k": "Combined Synopsis/Solicitation",
    "p": "Presolicitation",
    "r": "Sources Sought",
    "s": "Special Notice",
    "i": "Intent to Bundle Requirements (DoD-Funded)",
    "a": "Award Notice",
    "u": "Justification",
    "g": "Sale of Surplus Property",
}
DEFAULT_TYPES = "o,k,p,r"
# A hard ceiling on one run's requests, whatever --max-requests says. The team shares one
# daily budget, and a planted instruction must not be able to spend it in a single run.
MAX_REQUESTS_CEILING = 20

# What a set-aside code means for BBS. The certification facts behind each
# answer live in canon, plugins/bbs-foundations/skills/bbs-claude-md-forge/
# references/canonical-facts.md, "Certifications, by jurisdiction" and
# "Small-business status is channel-dependent": federally BBS is SDVOSB AND a
# small business, and VOSB (ruled 2026-10-02). Nothing here restates a number. Every code not backed by a
# certification in canon says so rather than guessing, and the API's own
# documented codes are the only keys (an unknown code is flagged, not mapped).
SIZE_FLAG = "[FLAG: confirm BBS is small under the size standard for NAICS {naics}]"
FIT_SDVOSB = "Eligible: SDVOSB set-aside (BBS is SDVOSB, per canon); " + SIZE_FLAG
FIT_VOSB = "Eligible: VA veteran-owned {kind} (BBS is VOSB, per canon); " + SIZE_FLAG
FIT_SB = ("Eligible: small-business set-aside (BBS is a small business under SBA size "
          "standards, per canon); " + SIZE_FLAG)
FIT_OPEN = "Full and open: no set-aside"
SET_ASIDE_FIT = {
    "SDVOSBC": FIT_SDVOSB,
    "SDVOSBS": FIT_SDVOSB.replace("set-aside", "sole source", 1),
    "SBA": FIT_SB,
    "SBP": FIT_SB,
    "VSA": FIT_VOSB.replace("{kind}", "set-aside"),
    "VSS": FIT_VOSB.replace("{kind}", "sole source"),
    "LAS": "[FLAG: local area set-aside. Eligibility depends on the declared area; read the notice]",
}
NO_CERT = {
    "8A": "8(a)", "8AN": "8(a)", "HZC": "HUBZone", "HZS": "HUBZone",
    "WOSB": "WOSB", "WOSBSS": "WOSB", "EDWOSB": "EDWOSB", "EDWOSBSS": "EDWOSB",
    "IEE": "Indian Economic Enterprise", "ISBEE": "Indian Small Business Economic Enterprise",
    "BICIV": "Buy Indian",
}


def set_aside_fit(code, naics):
    """One line saying whether BBS can respond to this set-aside, or why it cannot tell."""
    if not code:
        return FIT_OPEN
    c = code.strip().upper()
    if c in SET_ASIDE_FIT:
        return SET_ASIDE_FIT[c].format(naics=naics or "[MISSING]")
    if c in NO_CERT:
        return f"Not eligible as recorded: canon holds no {NO_CERT[c]} certification for BBS"
    return f"[FLAG: unrecognized set-aside code {code!r}; read the notice]"


def redact(text, key):
    """The key must never reach stdout, stderr or a transcript."""
    if key and text:
        text = text.replace(key, "[REDACTED]")
        text = text.replace(urllib.parse.quote(key, safe=""), "[REDACTED]")
    return text


def parse_deadline(raw):
    """Response deadline as an aware datetime, or None when absent or unparseable."""
    if not raw or raw == "null":
        return None
    s = str(raw).strip().replace("Z", "+00:00")
    for candidate in (s, s[:10]):
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if dt.tzinfo is None:
            # A date with no time: open through the end of that day.
            if len(candidate) == 10:
                dt = dt.replace(hour=23, minute=59, second=59)
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None


def _text(v):
    if v is None or v == "null":
        return ""
    return str(v).strip()


def normalize(n):
    """One notice reduced to the fields the table shows, all taken from the response."""
    pop = n.get("placeOfPerformance") or {}
    pop_state = (pop.get("state") or {}).get("code") if isinstance(pop.get("state"), dict) else pop.get("state")
    path = _text(n.get("fullParentPathName"))
    parts = [p.strip() for p in path.split(".") if p.strip()] if path else []
    agency = parts[0] if parts else _text(n.get("department"))
    office = parts[-1] if len(parts) > 1 else _text(n.get("office"))
    deadline_raw = n.get("responseDeadLine", n.get("reponseDeadLine"))
    naics = _text(n.get("naicsCode"))
    set_aside = _text(n.get("typeOfSetAside"))
    return {
        "noticeId": _text(n.get("noticeId")),
        "title": _text(n.get("title")),
        "solicitationNumber": _text(n.get("solicitationNumber")),
        "agency": agency,
        "office": office,
        "type": _text(n.get("type")),
        "postedDate": _text(n.get("postedDate")),
        "responseDeadLine": _text(deadline_raw),
        "naicsCode": naics,
        "classificationCode": _text(n.get("classificationCode")),
        "setAsideCode": set_aside,
        "setAside": _text(n.get("typeOfSetAsideDescription")),
        "bbsFit": set_aside_fit(set_aside, naics),
        "placeOfPerformanceState": _text(pop_state),
        "active": _text(n.get("active")),
        "uiLink": _text(n.get("uiLink")),
    }


def select(notices, keep_types, include_closed, now):
    """Split raw notices into kept rows and counted exclusions. Nothing disappears silently."""
    kept, excluded_type, closed, undated = [], {}, 0, 0
    seen = set()
    for raw in notices:
        row = normalize(raw)
        if row["noticeId"] and row["noticeId"] in seen:
            continue
        seen.add(row["noticeId"])
        if row["type"] not in keep_types:
            excluded_type[row["type"] or "(no type)"] = excluded_type.get(row["type"] or "(no type)", 0) + 1
            continue
        deadline = parse_deadline(row["responseDeadLine"])
        if not include_closed:
            if row["active"] and row["active"].lower() != "yes":
                closed += 1
                continue
            if deadline is not None and deadline < now:
                closed += 1
                continue
        if deadline is None:
            undated += 1
        kept.append(row)
    far = datetime.max.replace(tzinfo=timezone.utc)
    kept.sort(key=lambda r: (parse_deadline(r["responseDeadLine"]) or far, r["title"]))
    return kept, excluded_type, closed, undated


class LookupError_(RuntimeError):
    """An API failure, already redacted."""


def fetch(params, key, opener=None):
    """One request for one query. Returns (notices, totalRecords).

    Deliberately no paging. The documentation calls `offset` "the page index"
    without saying whether it counts pages or records, and a wrong guess skips
    records without any error. More than PAGE_LIMIT matches is reported as
    TRUNCATED and the person narrows the query, which this lookup is for anyway.
    """
    opener = opener or urllib.request.urlopen
    q = dict(params, api_key=key, limit=str(PAGE_LIMIT), offset="0")
    url = API_URL + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with opener(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        hint = ""
        if e.code == 404:
            # The documentation lists 404 as "No Data found", but a gateway that refuses
            # the request answers 404 with an empty body too (seen 2026-10-02 from a
            # cloud container, with and without a key). Reporting that as "nothing
            # matched" would be a plausible wrong answer, so it is a failure.
            hint = (" The API documents 404 as 'No Data found', but a refused request looks "
                    "identical, so this is NOT a confirmed empty result. Retry from your own "
                    "machine, or check the same search on sam.gov.")
        elif e.code == 429:
            hint = (" The shared BBS key's daily request budget is spent, for everyone, until it "
                    "resets (10 requests a day without an entity role, 1,000 with one). Tell Parker.")
        elif e.code in (401, 403):
            hint = (" The shared BBS key was refused; it may have lapsed. Its expiry date is in "
                    "canon, \"Federal codes\". Tell Parker.")
        raise LookupError_(redact(f"SAM.gov returned HTTP {e.code}.{hint} {detail}".strip(), key)) from None
    except urllib.error.URLError as e:
        raise LookupError_(redact(f"could not reach SAM.gov: {e.reason}", key)) from None
    except ValueError:
        raise LookupError_("SAM.gov answered with something that is not JSON.") from None
    page = body.get("opportunitiesData") or []
    total = body.get("totalRecords")
    return page, int(total) if total is not None else len(page)


def _date_arg(s):
    try:
        return datetime.strptime(s, "%m/%d/%Y").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{s!r} is not MM/DD/YYYY")


def build_parser():
    p = argparse.ArgumentParser(description="Read-only lookup of open SAM.gov solicitations.")
    p.add_argument("--naics", help="one or more NAICS codes, comma-separated (one request each)")
    p.add_argument("--agency", help="department or sub-tier name (organizationName search)")
    p.add_argument("--solnum", help="solicitation number")
    p.add_argument("--keyword", help="words in the notice title")
    p.add_argument("--set-aside", dest="set_aside", help="one set-aside code, e.g. SDVOSBC or SBA")
    p.add_argument("--state", help="place-of-performance state, e.g. CA")
    p.add_argument("--days", type=int, default=90,
                   help="look back this many days of posting date (default 90, max 364)")
    p.add_argument("--posted-from", dest="posted_from", type=_date_arg, help="MM/DD/YYYY")
    p.add_argument("--posted-to", dest="posted_to", type=_date_arg, help="MM/DD/YYYY")
    p.add_argument("--types", default=DEFAULT_TYPES,
                   help=f"notice type codes to keep (default {DEFAULT_TYPES}); "
                        + ", ".join(f"{k}={v}" for k, v in TYPE_CODES.items()))
    p.add_argument("--include-closed", action="store_true",
                   help="keep notices whose response deadline has passed or that are archived")
    p.add_argument("--max-requests", dest="max_requests", type=int, default=4,
                   help="refuse a run needing more API requests than this (default 4)")
    p.add_argument("--rows", type=int, default=50, help="rows to print (default 50)")
    p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    return p


def queries(args):
    """The request parameters for each API call, one per NAICS code."""
    base = {}
    if args.agency:
        base["organizationName"] = args.agency
    if args.solnum:
        base["solnum"] = args.solnum
    if args.keyword:
        base["title"] = args.keyword
    if args.set_aside:
        base["typeOfSetAside"] = args.set_aside.strip().upper()
    if args.state:
        base["state"] = args.state.strip().upper()
    naics = [c.strip() for c in (args.naics or "").split(",") if c.strip()]
    return [dict(base, ncode=c) for c in naics] or [base]


def _md(s):
    return (s or "").replace("|", "/").replace("\n", " ")


def render_table(rows, meta):
    out = []
    out.append(f"Source: SAM.gov Get Opportunities API (v2), queried {meta['retrieved']} UTC.")
    out.append(f"Query: {meta['query']}; posted {meta['postedFrom']} to {meta['postedTo']}.")
    out.append(f"Requests used: {meta['requests']} (cap {meta['maxRequests']}). "
               f"Returned by SAM.gov: {meta['returned']} of {meta['totalRecords']} matching.")
    if meta["truncated"]:
        out.append(f"⚠ TRUNCATED: over {PAGE_LIMIT} notices matched one request and only the "
                   "first page was read. Narrow the query (a NAICS code, a state, a shorter window).")
    ex = ", ".join(f"{k} {v}" for k, v in sorted(meta["excludedTypes"].items()))
    out.append(f"Kept {meta['kept']} open notices. Excluded: {meta['closed']} closed or archived"
               + (f"; by type: {ex}" if ex else "") + ".")
    if meta["undated"]:
        out.append(f"{meta['undated']} kept notice(s) give no response deadline; read the notice.")
    out.append("")
    if not rows:
        out.append("No open notices matched.")
        return "\n".join(out)
    out.append("| Respond by | Title | Agency / office | Solicitation # | Type | Set-aside | BBS fit | NAICS | PSC | PoP | Link |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows[:meta["rows"]]:
        out.append("| " + " | ".join(_md(x) for x in (
            r["responseDeadLine"] or "[none given]", r["title"],
            " / ".join(x for x in (r["agency"], r["office"]) if x),
            r["solicitationNumber"], r["type"], r["setAside"] or r["setAsideCode"] or "None",
            r["bbsFit"], r["naicsCode"], r["classificationCode"],
            r["placeOfPerformanceState"], r["uiLink"])) + " |")
    if len(rows) > meta["rows"]:
        out.append(f"\n{len(rows) - meta['rows']} more not shown (raise --rows or narrow the query).")
    return "\n".join(out)


def main(argv=None, opener=None, today=None, now=None):
    args = build_parser().parse_args(argv)
    if not any((args.naics, args.agency, args.solnum, args.keyword)):
        print("Give at least one of --naics, --agency, --solnum or --keyword. A date window alone "
              "returns every federal notice and spends the daily request budget.", file=sys.stderr)
        return 2
    keep = set()
    for code in args.types.split(","):
        code = code.strip().lower()
        if code not in TYPE_CODES:
            print(f"Unknown notice type code {code!r}. Known: {', '.join(TYPE_CODES)}", file=sys.stderr)
            return 2
        keep.add(TYPE_CODES[code])

    today = today or date.today()
    posted_to = args.posted_to or today
    posted_from = args.posted_from or (posted_to - timedelta(days=args.days))
    if posted_from > posted_to or (posted_to - posted_from).days > MAX_WINDOW_DAYS:
        print("The posted-date window must run forwards and span at most one year "
              "(the API's limit).", file=sys.stderr)
        return 2

    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        print(f"[MISSING — NEEDS INPUT] {KEY_ENV} is not set in this environment. Set it outside "
              "Claude (see the skill's Setup section) and start a new session. Never paste the "
              "key into a chat.", file=sys.stderr)
        return 2

    if not 1 <= args.max_requests <= MAX_REQUESTS_CEILING:
        print(f"--max-requests must be between 1 and {MAX_REQUESTS_CEILING}: the team shares one "
              "daily request budget.", file=sys.stderr)
        return 2
    qs = queries(args)
    if len(qs) > args.max_requests:
        print(f"{len(qs)} NAICS codes need at least {len(qs)} requests, over the cap of "
              f"{args.max_requests}. Fewer codes, or a higher --max-requests if your key allows "
              "it.", file=sys.stderr)
        return 2

    window = {"postedFrom": posted_from.strftime("%m/%d/%Y"), "postedTo": posted_to.strftime("%m/%d/%Y")}
    notices, total, used, truncated = [], 0, 0, False
    for q in qs:
        used += 1
        try:
            got, t = fetch(dict(q, **window), key, opener)
        except LookupError_ as e:
            print(f"SAM.gov lookup failed on request {used} of {len(qs)}: {e}", file=sys.stderr)
            return 1
        notices.extend(got)
        total += t
        truncated = truncated or t > len(got)

    now = now or datetime.now(timezone.utc)
    rows, excluded, closed, undated = select(notices, keep, args.include_closed, now)
    shown_query = "; ".join(", ".join(f"{k}={v}" for k, v in q.items()) for q in qs)
    meta = {
        "retrieved": now.strftime("%Y-%m-%d %H:%M"),
        "query": shown_query, **window,
        "requests": used, "maxRequests": args.max_requests,
        "returned": len(notices), "totalRecords": total, "truncated": truncated,
        "kept": len(rows), "closed": closed, "excludedTypes": excluded, "undated": undated,
        "rows": args.rows,
    }
    if args.json:
        print(json.dumps({"meta": meta, "notices": rows}, indent=2))
    else:
        print(render_table(rows, meta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
