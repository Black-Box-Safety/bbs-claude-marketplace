#!/usr/bin/env python3
"""bc_item_entry.py - create Business Central item cards from a reviewed spec, with a vendor,
a cost, and a named approval on every item.

    python3 bc_item_entry.py whoami
    python3 bc_item_entry.py check  <spec.json>
    python3 bc_item_entry.py commit <spec.json> --approve <token> --approved-by "<rep name>"

`check` reads Business Central and writes nothing. It validates every row, gates on the vendor,
duplicate-checks every item number, writes `<spec>.review.md`, and prints the approval token
(a hash of the spec file). `commit` refuses unless the token still matches the spec, then
creates each item, sets Vendor No. (and Vendor Item No.) through the Item Card web service,
verifies every write by read-back, and appends to `<spec>.bc-log.jsonl`.

Authentication (in this order):
  1. BBS_BC_ENV_FILE names a KEY=VALUE file. With BC_CLIENT_SECRET present the script runs
     app-only (service principal). Without it the script signs the rep in with a device code
     (msal, delegated) and caches the token in ~/.bbs/bc_token_cache.json.
  2. The same keys as environment variables: BC_TENANT_ID, BC_CLIENT_ID, BC_ENVIRONMENT,
     BC_COMPANY_ID, BC_COMPANY_NAME (optional), BC_CLIENT_SECRET (optional).

Rules enforced here (see references/item-rules.md for the why):
  vendor exists and is not blocked; the script never creates a vendor
  cost > 0 with a source that names a document (number or date, never "verbal" or "roughly"),
  cost basis equals the base unit of measure
  --approved-by must be the rep named as preparedBy on the spec
  price, when given, is never below cost; price equal to cost needs zeroMarginOk
  item number 1-20 ASCII chars, description 1-100 ASCII chars, manufacturer first
  type Inventory, PRODUCTS, INVENTORY, TAXABLE, explicit base UoM that exists in BC
  an item number that already exists stops the run; nothing is ever patched over

Stdlib only, except `msal` for delegated sign-in. Never prints a secret or a token.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request

API_RESOURCE = "https://api.businesscentral.dynamics.com"
ITEM_NO_MAX, DESC_MAX, DESC2_MAX, VENDOR_ITEM_MAX = 20, 100, 50, 50
ITEM_PAYLOAD_FIXED = {"type": "Inventory", "generalProductPostingGroupCode": "PRODUCTS",
                      "inventoryPostingGroupCode": "INVENTORY", "taxGroupCode": "TAXABLE"}


# ----------------------------------------------------------------------------- helpers
def die(step, msg, code=1):
    print(f"\nSTOP at {step}: {msg}")
    sys.exit(code)


def odq(s):
    """Escape a value for an OData string literal."""
    return str(s).replace("'", "''")


def qp(filter_expr, select=None):
    """Query string with %20 encoding. '+' for spaces makes BC answer 'Error in query syntax'."""
    parts = {"$filter": filter_expr}
    if select:
        parts["$select"] = select
    return "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in parts.items())


def http(method, url, headers=None, body=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:600]
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            die("network", "TLS certificate verification failed. On a Mac run this with "
                "/usr/bin/python3, not the python.org build.")
        die("network", str(e))


def norm(v):
    return str(v).replace("_x002D_", "-").replace("_x0020_", " ") if v is not None else ""


def is_ascii(s):
    return all(32 <= ord(c) < 127 for c in s)


def money(v):
    return f"{v:,.2f}"


# ----------------------------------------------------------------------------- auth
def load_connection():
    env = {}
    path = os.environ.get("BBS_BC_ENV_FILE", "").strip()
    if path:
        if not os.path.isfile(path):
            die("auth", f"BBS_BC_ENV_FILE points at {path!r}, which does not exist.")
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("BC_TENANT_ID", "BC_CLIENT_ID", "BC_ENVIRONMENT", "BC_COMPANY_ID",
              "BC_COMPANY_NAME", "BC_CLIENT_SECRET"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    missing = [k for k in ("BC_TENANT_ID", "BC_CLIENT_ID", "BC_ENVIRONMENT", "BC_COMPANY_ID") if not env.get(k)]
    if missing:
        die("auth", "missing connection values: " + ", ".join(missing) + ". Set BBS_BC_ENV_FILE to the "
            "connection file Parker issued (tenant, client id, environment, company id), or export those "
            "names as environment variables.")
    env.setdefault("BC_COMPANY_NAME", "Black Box Safety")
    return env


def token_app_only(env):
    form = urllib.parse.urlencode({
        "grant_type": "client_credentials", "client_id": env["BC_CLIENT_ID"],
        "client_secret": env["BC_CLIENT_SECRET"], "scope": f"{API_RESOURCE}/.default"}).encode()
    req = urllib.request.Request(f"https://login.microsoftonline.com/{env['BC_TENANT_ID']}/oauth2/v2.0/token",
                                 data=form, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())["access_token"], "app-only (service principal)"
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            j = json.loads(body)
            body = f"{j.get('error')}: {str(j.get('error_description', ''))[:200]}"
        except Exception:
            body = body[:200]
        die("auth", f"service-principal token request failed HTTP {e.code}: {body}")


def token_delegated(env):
    try:
        import msal
    except ImportError:
        die("auth", "delegated sign-in needs the msal package: python3 -m pip install msal "
            "(or set BBS_BC_ENV_FILE to a connection file that carries BC_CLIENT_SECRET).")
    cache_dir = os.path.join(os.path.expanduser("~"), ".bbs")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "bc_token_cache.json")
    cache = msal.SerializableTokenCache()
    if os.path.isfile(cache_path):
        try:
            cache.deserialize(open(cache_path, encoding="utf-8").read())
        except Exception:
            pass
    app = msal.PublicClientApplication(env["BC_CLIENT_ID"],
                                       authority=f"https://login.microsoftonline.com/{env['BC_TENANT_ID']}",
                                       token_cache=cache)
    scopes = [f"{API_RESOURCE}/user_impersonation"]
    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
    if not result or "access_token" not in result:
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            die("auth", f"could not start device-code sign-in: {json.dumps(flow)[:300]}")
        print(f"\nSIGN IN: {flow['message']}\n")
        result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        die("auth", f"sign-in failed: {result.get('error')}: {str(result.get('error_description', ''))[:300]}")
    if cache.has_state_changed:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(cache.serialize())
        os.chmod(cache_path, stat.S_IRUSR | stat.S_IWUSR)
    who = (result.get("id_token_claims") or {}).get("preferred_username") or (accounts[0].get("username") if accounts else "<unknown>")
    return result["access_token"], f"delegated, signed in as {who}"


class BC:
    def __init__(self):
        self.env = load_connection()
        if self.env.get("BC_CLIENT_SECRET"):
            token, self.mode = token_app_only(self.env)
        else:
            token, self.mode = token_delegated(self.env)
        self.auth = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        tenant, bc_env = self.env["BC_TENANT_ID"], urllib.parse.quote(self.env["BC_ENVIRONMENT"], safe="")
        self.api = f"{API_RESOURCE}/v2.0/{tenant}/{bc_env}/api/v2.0/companies({self.env['BC_COMPANY_ID']})"
        self.odata = (f"{API_RESOURCE}/v2.0/{tenant}/{bc_env}/ODataV4/"
                      f"Company('{urllib.parse.quote(odq(self.env['BC_COMPANY_NAME']), safe='')}')")
        print(f"[auth] {self.mode} - environment {self.env['BC_ENVIRONMENT']}, company {self.env['BC_COMPANY_NAME']}")

    def get(self, url):
        return http("GET", url, self.auth)

    def post(self, url, body):
        return http("POST", url, self.auth, body)

    def patch(self, url, etag, body):
        return http("PATCH", url, {**self.auth, "If-Match": etag}, body)

    # --- lookups -------------------------------------------------------------
    def vendor(self, number):
        st, body = self.get(f"{self.api}/vendors?" + qp(f"number eq '{odq(number)}'"))
        if st != 200:
            die("vendor lookup", f"HTTP {st}: {json.dumps(body)[:300]}")
        rows = body.get("value") or []
        return rows[0] if rows else None

    def item(self, number):
        st, body = self.get(f"{self.api}/items?" + qp(f"number eq '{odq(number)}'"))
        if st != 200:
            die("item lookup", f"HTTP {st}: {json.dumps(body)[:300]}")
        rows = body.get("value") or []
        return rows[0] if rows else None

    def item_card(self, number):
        st, body = self.get(f"{self.odata}/Item_Card_Excel?" + qp(f"No eq '{odq(number)}'"))
        if st != 200:
            die("item card lookup", f"HTTP {st}: {json.dumps(body)[:300]}")
        rows = body.get("value") or []
        return rows[0] if rows else None

    def units_of_measure(self):
        st, body = self.get(f"{self.api}/unitsOfMeasure?$select=code")
        if st != 200:
            die("units of measure", f"HTTP {st}: {json.dumps(body)[:300]}")
        return {r["code"] for r in body.get("value") or []}


# ----------------------------------------------------------------------------- spec
def spec_token(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]


def load_spec(path):
    try:
        spec = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        die("spec", f"cannot read {path}: {e}")
    if not isinstance(spec, dict) or not isinstance(spec.get("items"), list) or not spec["items"]:
        die("spec", "spec must be an object with a non-empty 'items' list")
    return spec


def validate_rows(spec, uoms):
    """Pure validation, no BC writes. Returns (rows, errors, warnings)."""
    errs, warns, rows = [], [], []
    default_vendor = (spec.get("vendorNo") or "").strip()
    numbers_in_spec = [str(it.get("number", "")).strip() for it in spec["items"]]
    seen = set()
    for i, it in enumerate(spec["items"], 1):
        tag = f"row {i}"
        num = str(it.get("number", "")).strip()
        if not num:
            errs.append(f"{tag}: number is blank"); continue
        tag = f"row {i} {num}"
        if num in seen:
            errs.append(f"{tag}: duplicated inside the spec")
        seen.add(num)
        if len(num) > ITEM_NO_MAX:
            errs.append(f"{tag}: number is {len(num)} chars, limit {ITEM_NO_MAX}")
        if not is_ascii(num):
            errs.append(f"{tag}: number has non-ASCII characters")
        if num != str(it.get("number")):
            errs.append(f"{tag}: number has leading or trailing spaces")

        desc = str(it.get("displayName", "")).strip()
        if not desc:
            errs.append(f"{tag}: displayName is blank")
        if len(desc) > DESC_MAX:
            errs.append(f"{tag}: displayName is {len(desc)} chars, limit {DESC_MAX}; shorten it deliberately")
        if not is_ascii(desc):
            bad = sorted({c for c in desc if not (32 <= ord(c) < 127)})
            errs.append(f"{tag}: displayName has non-ASCII characters {bad!r}; use plain hyphens and quotes")
        mfr = str(it.get("manufacturer", "")).strip()
        if not mfr:
            errs.append(f"{tag}: manufacturer is required (house style puts it first in the description)")
        elif not desc.lower().startswith(mfr.lower()):
            errs.append(f"{tag}: displayName must start with the manufacturer {mfr!r}")
        desc2 = str(it.get("displayName2", "") or "").strip()
        if len(desc2) > DESC2_MAX:
            errs.append(f"{tag}: displayName2 is {len(desc2)} chars, limit {DESC2_MAX}")
        if desc2 and not is_ascii(desc2):
            errs.append(f"{tag}: displayName2 has non-ASCII characters")

        uom = str(it.get("baseUoM", "")).strip().upper()
        if not uom:
            errs.append(f"{tag}: baseUoM is required (EA unless the vendor sells a pack, case or box)")
        elif uoms and uom not in uoms:
            errs.append(f"{tag}: baseUoM {uom!r} is not a unit of measure in BC ({', '.join(sorted(uoms))})")
        cost_per = str(it.get("costPer", "")).strip().upper()
        if not cost_per:
            errs.append(f"{tag}: costPer is required and must equal baseUoM (states what one unit of cost buys)")
        elif uom and cost_per != uom:
            errs.append(f"{tag}: cost is per {cost_per} but the item is stocked per {uom}; convert the cost "
                        f"or change the UoM (a case cost on an each item is the PO 791645 defect)")

        vendor = str(it.get("vendorNo") or default_vendor).strip()
        if not vendor:
            errs.append(f"{tag}: no vendorNo on the row and no top-level vendorNo")
        vendor_item = str(it.get("vendorItemNo", "") or "").strip()
        if len(vendor_item) > VENDOR_ITEM_MAX:
            errs.append(f"{tag}: vendorItemNo is {len(vendor_item)} chars, limit {VENDOR_ITEM_MAX}")

        included_with = str(it.get("includedWith", "") or "").strip()
        try:
            cost = float(it.get("unitCost")) if it.get("unitCost") is not None else None
        except (TypeError, ValueError):
            cost = None; errs.append(f"{tag}: unitCost is not a number")
        try:
            price = float(it.get("unitPrice")) if it.get("unitPrice") not in (None, "") else None
        except (TypeError, ValueError):
            price = None; errs.append(f"{tag}: unitPrice is not a number")
        source = str(it.get("costSource", "") or "").strip()
        if included_with:
            if included_with not in numbers_in_spec:
                errs.append(f"{tag}: includedWith {included_with!r} is not another item in this spec")
            if cost not in (None, 0.0) or price not in (None, 0.0):
                errs.append(f"{tag}: an includedWith accessory carries cost 0 and price 0; its value sits on the parent")
            cost = cost or 0.0
            price = price if price is not None else 0.0
        else:
            if cost is None or cost <= 0:
                errs.append(f"{tag}: unitCost must be greater than 0 (a $0 cost is never accepted; use includedWith "
                            f"for an accessory bundled with another item)")
            if not source:
                errs.append(f"{tag}: costSource is required: the vendor quote number and date, or the Grainger "
                            f"account and date the price was read")
            else:
                guessy = re.search(r"(?i)\b(verbal|estimat|approx|roughly|about|ballpark|from memory|phone|guess|"
                                   r"last time|usual|typical|tbd|later)\b", source)
                if guessy:
                    errs.append(f"{tag}: costSource {source!r} describes a guess ({guessy.group(0)!r}), not a document. "
                                f"A cost is read from a quote, price list, or the Grainger connector, and the source "
                                f"names it")
                elif not re.search(r"\d{2,}", source):
                    errs.append(f"{tag}: costSource {source!r} carries no document number or date; write the quote "
                                f"number and date, or the Grainger account and date")
            if price is not None and cost is not None and cost > 0:
                if price < cost:
                    errs.append(f"{tag}: unitPrice {money(price)} is below unitCost {money(cost)}")
                elif abs(price - cost) < 0.005 and not it.get("zeroMarginOk"):
                    errs.append(f"{tag}: unitPrice equals unitCost (0% margin); set zeroMarginOk: true only if the "
                                f"rep accepts selling at cost")
            if price is None:
                warns.append(f"{tag}: no unitPrice; normal for a Grainger item priced at quote time, an exception "
                             f"for anything else")
        gm = None
        if price and cost is not None and price > 0:
            gm = (price - cost) / price * 100
        rows.append({"i": i, "number": num, "displayName": desc, "displayName2": desc2, "manufacturer": mfr,
                     "baseUoM": uom, "vendorNo": vendor, "vendorItemNo": vendor_item, "unitCost": cost,
                     "unitPrice": price, "costSource": source, "includedWith": included_with, "gm": gm})
    return rows, errs, warns


def vendor_gate(bc, rows, spec):
    """Every distinct vendor must exist and be unblocked. Returns {vendorNo: record}."""
    vendors, errs = {}, []
    hint = (spec.get("vendorName") or "").strip().lower()
    for vno in sorted({r["vendorNo"] for r in rows if r["vendorNo"]}):
        rec = bc.vendor(vno)
        if not rec:
            errs.append(f"vendor {vno} does not exist in Business Central")
            continue
        blocked = norm(rec.get("blocked")).strip()
        if blocked:
            errs.append(f"vendor {vno} ({rec.get('displayName')}) is blocked: {blocked}")
        if hint and vno == (spec.get("vendorNo") or "").strip() and hint not in str(rec.get("displayName", "")).lower():
            errs.append(f"vendor {vno} is {rec.get('displayName')!r} in BC but the spec says vendorName "
                        f"{spec.get('vendorName')!r}; wrong vendor number?")
        vendors[vno] = rec
        print(f"[vendor] {vno} = {rec.get('displayName')!r}, {rec.get('city') or '-'}, {rec.get('state') or '-'}"
              f"{'  BLOCKED ' + blocked if blocked else ''}")
    return vendors, errs


VENDOR_CREATE_STEPS = """
  The script never creates a vendor. Create it in Business Central first:
    Purchasing > Vendors > New. Fill Name, Address, Phone, Email, Payment Terms, and save.
    Note the Vendor No. BC assigns (V#####), put it in the spec as vendorNo, and run check again.
  No house SOP covers the Vendor Card yet [FLAG: BBS Vendor Card SOP does not exist as of 2026-10-14];
  if unsure which terms or posting groups to pick, ask Parker before saving the card.
"""


def dup_gate(bc, rows):
    errs = []
    for r in rows:
        ex = bc.item(r["number"])
        if ex:
            card = bc.item_card(r["number"]) or {}
            errs.append(f"item {r['number']} already exists: {ex.get('displayName')!r}, type {norm(ex.get('type'))}, "
                        f"cost {money(float(ex.get('unitCost') or 0))}, price {money(float(ex.get('unitPrice') or 0))}, "
                        f"vendor {card.get('Vendor_No') or '-'}. Nothing is patched over an existing card. If this is "
                        f"the same product, quote the existing number; if it is a different product, pick a number "
                        f"that does not collide (Grainger SKU or a prefixed manufacturer PN).")
    return errs


def review_sheet(spec, rows, vendors, warns, token, spec_path):
    lines = [f"# Item entry review - {os.path.basename(spec_path)}", "",
             f"Prepared by: {spec.get('preparedBy') or '[MISSING - NEEDS INPUT]'}  ",
             f"Source: {spec.get('source') or '[MISSING - NEEDS INPUT]'}  ",
             f"Checked: {dt.datetime.now().isoformat(timespec='seconds')}  ",
             f"Approval token: `{token}` (changes if the spec file changes)", "",
             "Every item will be created as Inventory / PRODUCTS / INVENTORY / TAXABLE with the vendor below. "
             "Nothing is written until the rep approves this sheet by name.", "",
             "| # | Item No. | Description | UoM | Vendor | Vendor Item | Cost | Price | GM% | Cost source |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        v = vendors.get(r["vendorNo"], {})
        vname = f"{r['vendorNo']} {v.get('displayName', '')}".strip()
        price = money(r["unitPrice"]) if r["unitPrice"] is not None else "(none)"
        gm = f"{r['gm']:.1f}" if r["gm"] is not None else "-"
        src = r["costSource"] or (f"included with {r['includedWith']}" if r["includedWith"] else "")
        d = r["displayName"] + (f" / {r['displayName2']}" if r["displayName2"] else "")
        lines.append(f"| {r['i']} | {r['number']} | {d} | {r['baseUoM']} | {vname} | {r['vendorItemNo'] or '-'} | "
                     f"{money(r['unitCost'] or 0)} | {price} | {gm} | {src} |")
    if warns:
        lines += ["", "Warnings (not blocking):"] + [f"- {w}" for w in warns]
    lines += ["", "To commit after the rep has read this sheet:", "",
              f"    python3 bc_item_entry.py commit \"{spec_path}\" --approve {token} --approved-by \"<rep name>\"", ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- commands
def cmd_whoami(_):
    bc = BC()
    st, body = bc.get(f"{bc.api}/companyInformation?$select=displayName")
    name = ((body or {}).get("value") or [{}])[0].get("displayName") if st == 200 else f"HTTP {st}"
    print(f"[whoami] {bc.mode}; company information reads {name!r}")


def run_checks(bc, spec, spec_path):
    uoms = bc.units_of_measure()
    rows, errs, warns = validate_rows(spec, uoms)
    if errs:
        print("\n[pre-flight] FAILED, nothing written:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print(f"[pre-flight] {len(rows)} rows pass the field rules")
    vendors, verrs = vendor_gate(bc, rows, spec)
    if verrs:
        print("\n[vendor gate] FAILED, nothing written:")
        for e in verrs:
            print("  -", e)
        if any("does not exist" in e for e in verrs):
            print(VENDOR_CREATE_STEPS)
        sys.exit(1)
    derrs = dup_gate(bc, rows)
    if derrs:
        print("\n[duplicate gate] FAILED, nothing written:")
        for e in derrs:
            print("  -", e)
        sys.exit(1)
    print(f"[duplicate gate] {len(rows)} item numbers are free")
    return rows, vendors, warns


def cmd_check(args):
    spec = load_spec(args.spec)
    bc = BC()
    rows, vendors, warns = run_checks(bc, spec, args.spec)
    token = spec_token(args.spec)
    sheet = review_sheet(spec, rows, vendors, warns, token, args.spec)
    out = os.path.splitext(args.spec)[0] + ".review.md"
    open(out, "w", encoding="utf-8").write(sheet)
    print("\n" + sheet)
    print(f"[check] review sheet written to {out}")
    print(f"[check] APPROVAL TOKEN {token}. Show the sheet to the rep. Commit only with their name.")


def cmd_commit(args):
    token = spec_token(args.spec)
    if args.approve != token:
        die("approval", f"token {args.approve!r} does not match the spec on disk ({token}). Run check again, "
            f"have the rep read the new sheet, and commit with the new token.")
    who = (args.approved_by or "").strip()
    if len(who) < 3 or who.lower() in ("rep", "me", "user", "claude", "n/a", "na"):
        die("approval", "--approved-by must be the reviewing rep's real name")
    spec = load_spec(args.spec)
    prepared = str(spec.get("preparedBy") or "").strip()
    if not prepared:
        die("approval", "spec has no preparedBy; the rep whose batch this is must be named on the spec")
    if who.lower() != prepared.lower():
        die("approval", f"--approved-by {who!r} is not the rep named on the spec ({prepared!r}). The person who "
            f"reads the sheet is the person named on it; nobody approves on another rep's behalf")
    bc = BC()
    rows, vendors, warns = run_checks(bc, spec, args.spec)
    log_path = os.path.splitext(args.spec)[0] + ".bc-log.jsonl"
    log = open(log_path, "a", encoding="utf-8")

    def record(**kw):
        kw.update({"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "spec": os.path.basename(args.spec), "token": token, "approvedBy": who, "auth": bc.mode})
        log.write(json.dumps(kw) + "\n"); log.flush()

    record(event="commit-start", items=[r["number"] for r in rows])
    print(f"\n[commit] approved by {who}; creating {len(rows)} items")
    done = []
    for r in rows:
        num = r["number"]
        if bc.item(num):
            record(event="stop", item=num, reason="appeared between check and commit")
            die(f"create {num}", f"item appeared in BC between check and commit; created so far: {done or 'none'}")
        payload = {"number": num, "displayName": r["displayName"], **ITEM_PAYLOAD_FIXED,
                   "baseUnitOfMeasureCode": r["baseUoM"], "unitCost": r["unitCost"] or 0}
        if r["displayName2"]:
            payload["displayName2"] = r["displayName2"]
        if r["unitPrice"] is not None:
            payload["unitPrice"] = r["unitPrice"]
        st, res = bc.post(f"{bc.api}/items", payload)
        if st != 201:
            record(event="error", item=num, step="POST items", http=st, body=str(res)[:300])
            die(f"create {num}", f"HTTP {st}: {json.dumps(res)[:300]}; created so far: {done or 'none'}")
        rb = bc.item(num)
        checks = {
            "displayName": bool(rb) and rb.get("displayName") == r["displayName"],
            "type": bool(rb) and norm(rb.get("type")) == "Inventory",
            "genProd": bool(rb) and rb.get("generalProductPostingGroupCode") == "PRODUCTS",
            "invPost": bool(rb) and rb.get("inventoryPostingGroupCode") == "INVENTORY",
            "tax": bool(rb) and rb.get("taxGroupCode") == "TAXABLE",
            "uom": bool(rb) and rb.get("baseUnitOfMeasureCode") == r["baseUoM"],
            "cost": bool(rb) and abs(float(rb.get("unitCost") or 0) - (r["unitCost"] or 0)) < 0.005,
            "price": bool(rb) and (r["unitPrice"] is None or abs(float(rb.get("unitPrice") or 0) - r["unitPrice"]) < 0.005),
        }
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            record(event="error", item=num, step="verify item", failed=bad)
            die(f"verify {num}", f"read-back mismatch on {bad}; created so far: {done + [num]}")
        # vendor through the Item Card web service (the v2.0 items entity has no Vendor No.)
        card = bc.item_card(num)
        if not card:
            record(event="error", item=num, step="item card read")
            die(f"vendor {num}", f"item created but its card could not be read; created so far: {done + [num]}")
        vpatch = {"Vendor_No": r["vendorNo"]}
        if r["vendorItemNo"]:
            vpatch["Vendor_Item_No"] = r["vendorItemNo"]
        st, res = bc.patch(f"{bc.odata}/Item_Card_Excel('{urllib.parse.quote(odq(num), safe='')}')",
                           card["@odata.etag"], vpatch)
        if st not in (200, 204):
            record(event="error", item=num, step="PATCH Vendor_No", http=st, body=str(res)[:300])
            die(f"vendor {num}", f"item created but Vendor No. PATCH failed HTTP {st}: {json.dumps(res)[:300]}; "
                f"created so far: {done + [num]}")
        card = bc.item_card(num) or {}
        if card.get("Vendor_No") != r["vendorNo"] or (r["vendorItemNo"] and card.get("Vendor_Item_No") != r["vendorItemNo"]):
            record(event="error", item=num, step="verify vendor", got=card.get("Vendor_No"))
            die(f"vendor {num}", f"read-back shows Vendor_No {card.get('Vendor_No')!r}; created so far: {done + [num]}")
        done.append(num)
        record(event="created", item=num, displayName=r["displayName"], baseUoM=r["baseUoM"], unitCost=r["unitCost"],
               unitPrice=r["unitPrice"], vendorNo=r["vendorNo"], vendorItemNo=r["vendorItemNo"], costSource=r["costSource"])
        print(f"  {num:20} CREATED + VERIFIED  {r['baseUoM']:5} cost {money(r['unitCost'] or 0):>10}  "
              f"price {(money(r['unitPrice']) if r['unitPrice'] is not None else '(none)'):>10}  vendor {r['vendorNo']}")
    record(event="commit-done", created=done)
    print(f"\nDONE: {len(done)} items created and verified, vendor set on every one. Log: {log_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami", help="authenticate and print who the writes would be attributed to")
    c = sub.add_parser("check", help="validate the spec and gates; write the review sheet; no writes")
    c.add_argument("spec")
    m = sub.add_parser("commit", help="create the items after the rep approved the review sheet")
    m.add_argument("spec")
    m.add_argument("--approve", required=True, help="token printed by check")
    m.add_argument("--approved-by", required=True, help="name of the rep who read the review sheet")
    args = ap.parse_args()
    {"whoami": cmd_whoami, "check": cmd_check, "commit": cmd_commit}[args.cmd](args)


if __name__ == "__main__":
    main()
