#!/usr/bin/env python3
"""bc_item_entry.py - create Business Central item cards from a reviewed spec, with a vendor,
a cost, and a named approval on every item.

    python3 bc_item_entry.py whoami
    python3 bc_item_entry.py check  <spec.json>
    python3 bc_item_entry.py commit <spec.json> --approve <token> --approved-by "<rep name>"
    python3 bc_item_entry.py logout [--account <user@blackboxsafety.com> | --all]

`check` reads Business Central and writes nothing. It proves the read path a commit would use
(items, vendors, Item_Card_Excel), validates every row, gates on the vendor, duplicate-checks
every item number, writes `<spec>.review.md`, and prints the approval token (a hash of the
spec file). `commit` refuses unless the token still matches the spec, re-runs every gate, then
creates each item, sets Vendor No. (and Vendor Item No.) through the Item Card web service,
verifies every write by read-back, and appends to `<spec>.bc-log.jsonl`.

Connection values, in order of precedence (every run prints where each came from):
  1. Environment variables BC_TENANT_ID, BC_CLIENT_ID, BC_ENVIRONMENT, BC_COMPANY_ID.
  2. BBS_BC_ENV_FILE, a KEY=VALUE file with the same names (Parker's service-principal file).
  3. references/bc-connection.json beside this script: tenantId, clientId, environment,
     companyId, and nothing else. The script stops if that file carries any other key.
The company name is read from BC at run time (/companies({companyId})), never configured.

Authentication:
  Delegated (default): the rep signs in as themselves with msal. Interactive browser sign-in
  first, device code as the fallback (or BBS_BC_SIGNIN=device to force it). The token cache is
  encrypted through msal-extensions (Keychain on a Mac, DPAPI on Windows); when that library is
  missing the cache is a 0600 file in a 0700 ~/.bbs. With more than one cached account, pick
  one with --account or BBS_BC_ACCOUNT. `logout` removes a cached account.
  App-only (service principal): runs ONLY with BBS_BC_AUTH=app-only and BC_CLIENT_SECRET from
  the env file or the environment. A secret without the flag is ignored and said so. Writes
  made app-only are attributed to the service principal, not the rep, and are flagged.

Rules enforced here (see references/item-rules.md for the why):
  vendor exists and is not blocked; the script never creates a vendor
  every vendor number in the spec carries a vendorName, and BC's name must contain it
  cost > 0 with a source that names a document (number or date, never "verbal", "estimate",
  "approx", "roughly" or any stem of those), cost basis equals the base unit of measure
  --approved-by must be the rep named as preparedBy on the spec
  price, when given, is never below cost; price equal to cost needs zeroMarginOk
  item number 1-20 upper-case ASCII chars, description 1-100 ASCII chars, manufacturer first
  type Inventory, PRODUCTS, INVENTORY, TAXABLE, explicit base UoM that exists in BC
  an item number that already exists stops the run; nothing is ever patched over

Stdlib only, except `msal` and `msal-extensions` for delegated sign-in. Never prints a secret
or an auth token. The approval token it prints is a hash of the spec file, not a credential.
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
HERE = os.path.dirname(os.path.abspath(__file__))
CONNECTION_FILE = os.path.join(os.path.dirname(HERE), "references", "bc-connection.json")
CONNECTION_KEYS = ("tenantId", "clientId", "environment", "companyId")
ENV_FOR = {"tenantId": "BC_TENANT_ID", "clientId": "BC_CLIENT_ID",
           "environment": "BC_ENVIRONMENT", "companyId": "BC_COMPANY_ID"}
# Characters an item number may carry. The number becomes the key segment of
# Item_Card_Excel('...') on the PATCH that sets Vendor No.; only these have been exercised
# there (existing cards carry #, parentheses, dots, spaces and hyphens). A slash, percent
# or ampersand in a URL path segment is untested, so the script stops rather than finds
# out after the item exists.
ITEM_NO_CHARS = re.compile(r"^[A-Z0-9#()._' -]+$")
GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".bbs")
PIP_HINT = f"{sys.executable} -m pip install --user msal msal-extensions"
RECOVERY = ("Recovery: set Vendor No. on the card in the BC UI, or run bc_patch_item_vendor.py in "
            "PM Claude/BC-Write-API on SharePoint (--vendor V##### --items <number>). Do not re-run "
            "commit for this item: it now exists and the duplicate gate will stop on it.")

# Words that mean the cost was not read from a document. Stems take any suffix, so
# "estimate", "estimated", "approximately" and "Guesstimate" all fail; a vendor whose
# name happens to be "Usual" does not.
GUESS_WORDS = re.compile(r"(?i)\b(verbal|estimat\w*|approx\w*|roughly|about(?=\s*\$?\d)|ballpark|from memory|"
                         r"phone|guess\w*|last time|typical|tbd|later)\b")

# Sign-in and BC errors in plain language. The code is what Entra or BC returns; the text is
# what the rep does about it. Matched by substring against the raw error text.
ERROR_TABLE = [
    ("AADSTS65001", "consent is missing: a tenant admin has to grant admin consent for the app's "
                    "delegated Business Central permission (user_impersonation). Ask the admin."),
    ("AADSTS90094", "consent is missing: a tenant admin has to grant admin consent for the app's "
                    "delegated Business Central permission (user_impersonation). Ask the admin."),
    ("AADSTS50020", "wrong or personal account: sign in with your @blackboxsafety.com work account, "
                    "not a personal Microsoft account or another tenant's user."),
    ("AADSTS700016", "wrong client id or tenant: the app registration in bc-connection.json was not "
                     "found in that tenant. Check the file (or your BC_* overrides)."),
    ("AADSTS53003", "blocked by Conditional Access: an admin policy stops this sign-in flow. Ask "
                    "the admin which flow is allowed."),
    ("AADSTS7000218", "the app registration does not allow public client flows. An admin turns on "
                      "'Allow public client flows' on the app's Authentication page."),
    ("AADSTS50011", "the redirect URI http://localhost is not registered on the app under 'Mobile "
                    "and desktop applications'. Ask the admin; device-code sign-in works meanwhile "
                    "(BBS_BC_SIGNIN=device)."),
    ("expired_token", "the sign-in code timed out before you finished. Run the command again."),
    ("authorization_pending", "the sign-in was not completed. Run the command again."),
]


# ----------------------------------------------------------------------------- helpers
def die(step, msg, code=1):
    print(f"\nSTOP at {step}: {msg}")
    sys.exit(code)


def explain_error(text, http_status=None):
    """Plain-language meaning of an Entra or BC error, or '' when the table has nothing."""
    text = str(text or "")
    for code, meaning in ERROR_TABLE:
        if code in text:
            return f"{code}: {meaning}"
    if http_status == 401:
        return ("HTTP 401: Business Central rejected the sign-in. Usually no BC user for this "
                "account, or no licence on it. A BC admin adds you on the Users page.")
    if http_status == 403:
        return ("HTTP 403: your BC user lacks a permission set covering this page (item insert, the "
                "Item Card page, or vendor read). A BC admin fixes it on the Users page.")
    return ""


def odq(s):
    """Escape a value for an OData string literal."""
    return str(s).replace("'", "''")


def qp(filter_expr=None, select=None, top=None):
    """Query string with %20 encoding. '+' for spaces makes BC answer 'Error in query syntax'."""
    parts = {}
    if filter_expr:
        parts["$filter"] = filter_expr
    if select:
        parts["$select"] = select
    if top:
        parts["$top"] = str(top)
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


def http_fail(step, st, body):
    hint = explain_error(json.dumps(body) if not isinstance(body, str) else body, st)
    die(step, f"HTTP {st}: {json.dumps(body)[:300]}" + (f"\n  {hint}" if hint else ""))


def norm(v):
    return str(v).replace("_x002D_", "-").replace("_x0020_", " ") if v is not None else ""


def is_ascii(s):
    return all(32 <= ord(c) < 127 for c in s)


def is_guid(s):
    return bool(GUID_RE.match(str(s or "")))


def money(v):
    return f"{v:,.2f}"


# ----------------------------------------------------------------------------- connection
def read_connection_file(path):
    """The shipped file: exactly the four keys, every GUID well formed. Anything else stops."""
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        die("connection", f"cannot read {path}: {e}")
    if not isinstance(data, dict):
        die("connection", f"{path} must be a JSON object")
    extra = sorted(set(data) - set(CONNECTION_KEYS))
    if extra:
        die("connection", f"{path} carries keys outside the allowed four {CONNECTION_KEYS}: {extra}. "
            f"That file holds connection values only, never a secret. Remove them.")
    missing = [k for k in CONNECTION_KEYS if not str(data.get(k) or "").strip()]
    if missing:
        die("connection", f"{path} is missing {missing}")
    for k in ("tenantId", "clientId", "companyId"):
        if not is_guid(data[k]):
            die("connection", f"{path}: {k} is not a well-formed GUID")
    return {k: str(data[k]).strip() for k in CONNECTION_KEYS}


def read_env_file(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_connection():
    """Returns (values, sources, secret). sources says where each value came from."""
    values, sources = {}, {}
    if os.path.isfile(CONNECTION_FILE):
        for k, v in read_connection_file(CONNECTION_FILE).items():
            values[k], sources[k] = v, "bc-connection.json"
    secret = None
    env_path = os.environ.get("BBS_BC_ENV_FILE", "").strip()
    if env_path:
        if not os.path.isfile(env_path):
            die("connection", f"BBS_BC_ENV_FILE points at {env_path!r}, which does not exist.")
        file_env = read_env_file(env_path)
        for k, envk in ENV_FOR.items():
            if file_env.get(envk):
                values[k], sources[k] = file_env[envk], f"BBS_BC_ENV_FILE ({os.path.basename(env_path)})"
        if file_env.get("BC_CLIENT_SECRET"):
            secret = file_env["BC_CLIENT_SECRET"]
    for k, envk in ENV_FOR.items():
        if os.environ.get(envk):
            values[k], sources[k] = os.environ[envk].strip(), f"environment variable {envk}"
    if os.environ.get("BC_CLIENT_SECRET"):
        secret = os.environ["BC_CLIENT_SECRET"]
    missing = [k for k in CONNECTION_KEYS if not values.get(k)]
    if missing:
        die("connection", f"missing connection values {missing}. The plugin ships them in "
            f"{CONNECTION_FILE}; BBS_BC_ENV_FILE or BC_* environment variables override them.")
    for k in ("tenantId", "clientId", "companyId"):
        if not is_guid(values[k]):
            die("connection", f"{k} ({sources[k]}) is not a well-formed GUID")
    return values, sources, secret


def auth_mode(secret):
    """'delegated' unless BBS_BC_AUTH=app-only is set explicitly AND a secret is present."""
    flag = os.environ.get("BBS_BC_AUTH", "").strip().lower()
    if flag in ("", "delegated"):
        if secret:
            print("[auth] a BC_CLIENT_SECRET is present but BBS_BC_AUTH is not app-only; ignoring it "
                  "and signing you in as yourself")
        return "delegated"
    if flag == "app-only":
        if not secret:
            die("auth", "BBS_BC_AUTH=app-only but no BC_CLIENT_SECRET in BBS_BC_ENV_FILE or the "
                "environment. App-only is Parker's path, not a rep's; unset BBS_BC_AUTH to sign in "
                "as yourself.")
        return "app-only"
    die("auth", f"BBS_BC_AUTH={flag!r} is not a mode. Leave it unset (delegated) or set app-only.")


# ----------------------------------------------------------------------------- auth
def token_app_only(conn, secret):
    form = urllib.parse.urlencode({
        "grant_type": "client_credentials", "client_id": conn["clientId"],
        "client_secret": secret, "scope": f"{API_RESOURCE}/.default"}).encode()
    req = urllib.request.Request(f"https://login.microsoftonline.com/{conn['tenantId']}/oauth2/v2.0/token",
                                 data=form, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            j = json.loads(body)
            body = f"{j.get('error')}: {str(j.get('error_description', ''))[:200]}"
        except Exception:
            body = body[:200]
        hint = explain_error(body)
        die("auth", f"service-principal token request failed HTTP {e.code}: {body}"
            + (f"\n  {hint}" if hint else ""))


def _import_msal():
    try:
        import msal  # noqa: F401
        return msal
    except ImportError:
        die("auth", "delegated sign-in needs the msal package (and msal-extensions for the encrypted "
            f"token cache). Install both into THIS interpreter:\n  {PIP_HINT}\nOn a Mac run every "
            "command here with /usr/bin/python3; the python.org build fails TLS verification.")


def _ensure_cache_dir():
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(CACHE_DIR, 0o700)
    except OSError:
        pass


def open_token_cache(msal):
    """Encrypted through msal-extensions when it is there; otherwise a 0600 file. Returns
    (cache, kind, save) where save() persists a plain cache and is a no-op for the encrypted one."""
    _ensure_cache_dir()
    try:
        from msal_extensions import build_encrypted_persistence, PersistedTokenCache
        persistence = build_encrypted_persistence(os.path.join(CACHE_DIR, "bc_token_cache.bin"))
        cache = PersistedTokenCache(persistence)
        return cache, "encrypted (msal-extensions)", (lambda: None)
    except Exception as e:  # ImportError, or the platform has no encrypted store
        reason = "msal-extensions is not installed" if isinstance(e, ImportError) else f"{type(e).__name__}"
        plain = os.path.join(CACHE_DIR, "bc_token_cache.json")
        cache = msal.SerializableTokenCache()
        if os.path.isfile(plain):
            try:
                cache.deserialize(open(plain, encoding="utf-8").read())
            except Exception:
                pass

        def save():
            if not cache.has_state_changed:
                return
            fd = os.open(plain, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(cache.serialize())
            os.chmod(plain, stat.S_IRUSR | stat.S_IWUSR)
        print(f"[auth] token cache is a plain 0600 file ({reason}); install msal-extensions for an "
              f"encrypted cache: {PIP_HINT}")
        return cache, "plain file, 0600", save


def public_app(msal, conn, cache):
    return msal.PublicClientApplication(conn["clientId"],
                                        authority=f"https://login.microsoftonline.com/{conn['tenantId']}",
                                        token_cache=cache)


def choose_account(accounts, wanted):
    """One cached account is used; several need --account or BBS_BC_ACCOUNT. Never accounts[0]."""
    wanted = (wanted or os.environ.get("BBS_BC_ACCOUNT", "")).strip().lower()
    if wanted:
        hits = [a for a in accounts if a.get("username", "").lower() == wanted]
        if not hits:
            die("auth", f"no cached sign-in for {wanted!r}. Cached: "
                f"{[a.get('username') for a in accounts] or 'none'}. Run whoami to sign in as that account.")
        return hits[0]
    if len(accounts) == 1:
        return accounts[0]
    if len(accounts) > 1:
        die("auth", "more than one cached sign-in: " + ", ".join(a.get("username", "?") for a in accounts)
            + ". Pick one with --account <username> or BBS_BC_ACCOUNT, or logout the one you do not want.")
    return None


def token_delegated(conn, account_pref=None):
    msal = _import_msal()
    cache, cache_kind, save = open_token_cache(msal)
    app = public_app(msal, conn, cache)
    scopes = [f"{API_RESOURCE}/user_impersonation"]
    account = choose_account(app.get_accounts(), account_pref)
    result = app.acquire_token_silent(scopes, account=account) if account else None
    if not result or "access_token" not in result:
        result = sign_in(app, scopes)
    if "access_token" not in result:
        err = f"{result.get('error')}: {str(result.get('error_description', ''))[:300]}"
        hint = explain_error(err)
        die("auth", f"sign-in failed: {err}" + (f"\n  {hint}" if hint else ""))
    save()
    who = (result.get("id_token_claims") or {}).get("preferred_username") or \
          (account.get("username") if account else "<unknown>")
    return result["access_token"], who, cache_kind


def sign_in(app, scopes):
    """Interactive browser first, device code as the fallback. BBS_BC_SIGNIN=device forces the latter."""
    forced = os.environ.get("BBS_BC_SIGNIN", "").strip().lower()
    if forced not in ("device",):
        print("\nSIGN IN: a browser window is opening for your Microsoft work account. If none opens "
              "within a few seconds, re-run with BBS_BC_SIGNIN=device.\n")
        try:
            result = app.acquire_token_interactive(scopes, prompt="select_account", timeout=180)
            if "access_token" in result:
                return result
            print(f"[auth] browser sign-in did not complete ({result.get('error')}); "
                  f"{explain_error(json.dumps(result)) or 'falling back to a device code'}")
        except Exception as e:  # no browser, loopback port taken, headless session
            print(f"[auth] browser sign-in unavailable ({type(e).__name__}); falling back to a device code")
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        die("auth", f"could not start device-code sign-in: {json.dumps(flow)[:300]}")
    print(f"\nSIGN IN: {flow['message']}\n")
    return app.acquire_token_by_device_flow(flow)


class BC:
    def __init__(self, account=None):
        self.conn, self.sources, secret = load_connection()
        self.mode = auth_mode(secret)
        if self.mode == "app-only":
            token, self.user, self.cache_kind = token_app_only(self.conn, secret), "service principal", "-"
            self.mode_text = "app-only (service principal) [FLAG: writes are attributed to the app, not to a rep]"
        else:
            token, self.user, self.cache_kind = token_delegated(self.conn, account)
            self.mode_text = f"delegated, signed in as {self.user} (token cache {self.cache_kind})"
        self.auth = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        tenant = self.conn["tenantId"]
        bc_env = urllib.parse.quote(self.conn["environment"], safe="")
        self.api_root = f"{API_RESOURCE}/v2.0/{tenant}/{bc_env}/api/v2.0"
        self.api = f"{self.api_root}/companies({self.conn['companyId']})"
        self.company_name, self.company_display = self.company()
        self.odata = (f"{API_RESOURCE}/v2.0/{tenant}/{bc_env}/ODataV4/"
                      f"Company('{urllib.parse.quote(odq(self.company_name), safe='')}')")
        print(f"[auth] {self.mode_text}")
        print(f"[auth] environment {self.conn['environment']}, company {self.company_display!r} "
              f"(OData name {self.company_name!r}, read from BC)")
        print("[auth] connection values: " + ", ".join(f"{k} from {self.sources[k]}" for k in CONNECTION_KEYS))

    def get(self, url):
        return http("GET", url, self.auth)

    def post(self, url, body):
        return http("POST", url, self.auth, body)

    def patch(self, url, etag, body):
        return http("PATCH", url, {**self.auth, "If-Match": etag}, body)

    # --- lookups -------------------------------------------------------------
    def company(self):
        st, body = self.get(f"{self.api_root}/companies({self.conn['companyId']})?$select=name,displayName")
        if st != 200:
            http_fail("company lookup", st, body)
        name = (body or {}).get("name")
        if not name:
            die("company lookup", f"companies({self.conn['companyId']}) returned no name: {json.dumps(body)[:300]}")
        return name, (body or {}).get("displayName") or name

    def path_probe(self):
        """The three reads a commit depends on, $top=1 each. Returns [(what, ok, detail)]."""
        out = []
        for what, url in (("items (API)", f"{self.api}/items?" + qp(select="number", top=1)),
                          ("vendors (API)", f"{self.api}/vendors?" + qp(select="number", top=1)),
                          ("Item_Card_Excel (OData web service, sets Vendor No.)",
                           f"{self.odata}/Item_Card_Excel?" + qp(select="No", top=1))):
            st, body = self.get(url)
            ok = st == 200 and isinstance(body, dict) and "value" in body
            detail = "PASS" if ok else f"FAIL HTTP {st}: {json.dumps(body)[:160]}"
            hint = "" if ok else explain_error(json.dumps(body), st)
            out.append((what, ok, detail + (f" ({hint})" if hint else "")))
        return out

    def require_path(self):
        probes = self.path_probe()
        for what, ok, detail in probes:
            print(f"[path] {what}: {detail}")
        if not all(ok for _, ok, _ in probes):
            die("path check", "a read this skill depends on failed, so nothing can be checked or "
                "committed. If Item_Card_Excel is the one that failed, a commit would create items "
                "with no vendor, which is why it stops here. Fix the access (see references/rep-setup.md) "
                "and run again.")
        return probes

    def vendor(self, number):
        st, body = self.get(f"{self.api}/vendors?" + qp(f"number eq '{odq(number)}'"))
        if st != 200:
            http_fail("vendor lookup", st, body)
        rows = body.get("value") or []
        return rows[0] if rows else None

    def item(self, number):
        st, body = self.get(f"{self.api}/items?" + qp(f"number eq '{odq(number)}'"))
        if st != 200:
            http_fail("item lookup", st, body)
        rows = body.get("value") or []
        return rows[0] if rows else None

    def item_card(self, number):
        st, body = self.get(f"{self.odata}/Item_Card_Excel?" + qp(f"No eq '{odq(number)}'"))
        if st != 200:
            http_fail("item card lookup", st, body)
        rows = body.get("value") or []
        return rows[0] if rows else None

    def units_of_measure(self):
        st, body = self.get(f"{self.api}/unitsOfMeasure?$select=code")
        if st != 200:
            http_fail("units of measure", st, body)
        codes = {r["code"] for r in body.get("value") or []}
        if not codes:
            die("units of measure", "BC returned no units of measure; baseUoM cannot be validated, so nothing "
                "is checked or committed. A permission set that hides the Units of Measure table is the usual cause.")
        return codes


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


def cost_source_problem(source):
    """Why a costSource is not a document, or None when it passes."""
    m = GUESS_WORDS.search(source or "")
    if m:
        return f"describes a guess ({m.group(0)!r}), not a document"
    if not re.search(r"\d{2,}", source or ""):
        return "carries no document number or date"
    return None


def validate_rows(spec, uoms):
    """Pure validation, no BC calls. Returns (rows, errors, warnings, vendor_names)."""
    errs, warns, rows = [], [], []
    default_vendor = str(spec.get("vendorNo") or "").strip()
    default_name = str(spec.get("vendorName") or "").strip()
    vendor_names = {}            # vendorNo -> set of names the spec gives for it
    if default_vendor:
        if default_vendor != default_vendor.upper():
            errs.append(f"top-level vendorNo {default_vendor!r} must be upper-case (BC Code field)")
        if default_name:
            vendor_names.setdefault(default_vendor, set()).add(default_name)
        else:
            errs.append("top-level vendorNo is set but vendorName is blank; every vendor number in the "
                        "spec carries the name as it reads on the quote, and BC's name must contain it")
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
        elif not ITEM_NO_CHARS.match(num.upper()):
            bad = sorted({c for c in num if not ITEM_NO_CHARS.match(c.upper())})
            errs.append(f"{tag}: number carries {bad!r}; item numbers here use letters, digits, # ( ) . _ ' space "
                        f"and hyphen only, because the number becomes the URL key of the Item Card web service "
                        f"that sets Vendor No. and other characters are untested there")
        elif num != num.upper():
            errs.append(f"{tag}: item numbers are upper-case in BC (Code field); write it as {num.upper()!r} "
                        f"so the spec, the review sheet and the card agree")
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

        row_vendor = str(it.get("vendorNo") or "").strip()
        row_name = str(it.get("vendorName") or "").strip()
        vendor = row_vendor or default_vendor
        if not vendor:
            errs.append(f"{tag}: no vendorNo on the row and no top-level vendorNo")
        elif vendor != vendor.upper():
            errs.append(f"{tag}: vendorNo {vendor!r} must be upper-case (BC Code field)")
        if row_vendor and row_vendor != default_vendor and not row_name:
            errs.append(f"{tag}: the row overrides vendorNo to {row_vendor!r} but carries no vendorName; "
                        f"every distinct vendor is name-checked against BC")
        if row_name and vendor:
            vendor_names.setdefault(vendor, set()).add(row_name)
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
                problem = cost_source_problem(source)
                if problem:
                    errs.append(f"{tag}: costSource {source!r} {problem}. A cost is read from a quote, price "
                                f"list, or the Grainger connector, and the source names it with its number or date")
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
    for vno in sorted({r["vendorNo"] for r in rows if r["vendorNo"]}):
        if vno not in vendor_names:
            errs.append(f"vendor {vno} has no vendorName anywhere in the spec; a vendor number with no name is "
                        f"a number carried in someone's head. Add vendorName where that number is set")
    return rows, errs, warns, vendor_names


def vendor_gate(bc, rows, vendor_names):
    """Every distinct vendor must exist, be unblocked, and carry the name the spec gives it."""
    vendors, errs = {}, []
    for vno in sorted({r["vendorNo"] for r in rows if r["vendorNo"]}):
        rec = bc.vendor(vno)
        if not rec:
            errs.append(f"vendor {vno} does not exist in Business Central")
            continue
        blocked = norm(rec.get("blocked")).strip()
        if blocked:
            errs.append(f"vendor {vno} ({rec.get('displayName')}) is blocked: {blocked}")
        bc_name = str(rec.get("displayName", ""))
        for hint in sorted(vendor_names.get(vno, ())):
            if hint.lower() not in bc_name.lower():
                errs.append(f"vendor {vno} is {bc_name!r} in BC but the spec says vendorName {hint!r}; "
                            f"wrong vendor number?")
        vendors[vno] = rec
        print(f"[vendor] {vno} = {bc_name!r}, {rec.get('city') or '-'}, {rec.get('state') or '-'}"
              f"{'  BLOCKED ' + blocked if blocked else ''}")
    return vendors, errs


VENDOR_CREATE_STEPS = """
  The script never creates a vendor. Create it in Business Central first:
    Purchasing > Vendors > New. Fill Name, Address, Phone, Email, Payment Terms, and save.
    Note the Vendor No. BC assigns (V#####), put it in the spec as vendorNo with its vendorName,
    and run check again.
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


def review_sheet(bc, spec, rows, vendors, warns, token, spec_path):
    lines = [f"# Item entry review - {os.path.basename(spec_path)}", "",
             f"Prepared by: {spec.get('preparedBy') or '[MISSING - NEEDS INPUT]'}  ",
             f"Source: {spec.get('source') or '[MISSING - NEEDS INPUT]'}  ",
             f"Checked: {dt.datetime.now().isoformat(timespec='seconds')}  ",
             f"Writes as: {bc.mode_text}  ",
             f"Connection: {bc.conn['environment']} / {bc.company_display}; values from "
             + ", ".join(sorted({bc.sources[k] for k in CONNECTION_KEYS})) + "  ",
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
    if bc.mode == "app-only":
        lines += ["", "[FLAG: this run is app-only. The item cards will show the service principal as creator, "
                      "not the rep. A rep's own batch runs delegated.]"]
    lines += ["", "To commit after the rep has read this sheet:", "",
              f"    python3 bc_item_entry.py commit \"{spec_path}\" --approve {token} --approved-by \"<rep name>\"", ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- commands
def cmd_whoami(args):
    bc = BC(account=args.account)
    probes = bc.path_probe()
    for what, ok, detail in probes:
        print(f"[path] {what}: {detail}")
    if all(ok for _, ok, _ in probes):
        print(f"[whoami] {bc.mode_text}; company {bc.company_display!r}; the three reads a commit depends on PASS. "
              f"Next: run check on a one-item test spec.")
    else:
        print("[whoami] a read FAILED above; check and commit will refuse until it passes. "
              "See references/rep-setup.md for what each failure means.")
        sys.exit(1)


def cmd_logout(args):
    msal = _import_msal()
    conn, _, _ = load_connection()
    cache, kind, save = open_token_cache(msal)
    app = public_app(msal, conn, cache)
    accounts = app.get_accounts()
    if not accounts:
        print("[logout] no cached sign-in"); return
    if args.all:
        targets = accounts
    elif args.account:
        targets = [a for a in accounts if a.get("username", "").lower() == args.account.strip().lower()]
        if not targets:
            die("logout", f"no cached sign-in for {args.account!r}. Cached: {[a.get('username') for a in accounts]}")
    elif len(accounts) == 1:
        targets = accounts
    else:
        die("logout", "more than one cached sign-in: " + ", ".join(a.get("username", "?") for a in accounts)
            + ". Name one with --account, or --all.")
    for a in targets:
        app.remove_account(a)
        print(f"[logout] removed cached sign-in for {a.get('username')}")
    save()
    plain = os.path.join(CACHE_DIR, "bc_token_cache.json")
    if not app.get_accounts() and os.path.isfile(plain):
        os.remove(plain)


def run_checks(bc, spec, spec_path):
    bc.require_path()
    uoms = bc.units_of_measure()
    rows, errs, warns, vendor_names = validate_rows(spec, uoms)
    if errs:
        print("\n[pre-flight] FAILED, nothing written:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print(f"[pre-flight] {len(rows)} rows pass the field rules")
    vendors, verrs = vendor_gate(bc, rows, vendor_names)
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
    bc = BC(account=args.account)
    rows, vendors, warns = run_checks(bc, spec, args.spec)
    token = spec_token(args.spec)
    sheet = review_sheet(bc, spec, rows, vendors, warns, token, args.spec)
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
    bc = BC(account=args.account)
    if bc.mode == "app-only":
        if os.environ.get("BBS_BC_AUTH", "").strip().lower() != "app-only":
            die("approval", "commit refuses app-only auth unless BBS_BC_AUTH=app-only is set explicitly")
        print("[commit] FLAG: app-only run. The cards will show the service principal as creator, not "
              f"{who}. The log records both.")
    elif not any(part.lower() in bc.user.split("@")[0].lower() for part in who.split() if len(part) > 1):
        print(f"[commit] note: approved by {who}, but the sign-in writing is {bc.user}. The log records both; "
              f"this is acceptable only because {who} is in the chat reading the sheet.")
    rows, vendors, warns = run_checks(bc, spec, args.spec)
    log_path = os.path.splitext(args.spec)[0] + ".bc-log.jsonl"
    log = open(log_path, "a", encoding="utf-8")

    def record(**kw):
        kw.update({"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "spec": os.path.basename(args.spec), "token": token, "approvedBy": who,
                   "auth": bc.mode, "signedInAs": bc.user})
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
            hint = explain_error(json.dumps(res), st)
            die(f"create {num}", f"HTTP {st}: {json.dumps(res)[:300]}" + (f"\n  {hint}" if hint else "")
                + f"; created so far: {done or 'none'}")
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
            die(f"verify {num}", f"read-back mismatch on {bad}; item {num} EXISTS in BC without a vendor. "
                f"{RECOVERY} Created so far: {done + [num]}")
        # vendor through the Item Card web service (the v2.0 items entity has no Vendor No.)
        card = bc.item_card(num)
        if not card:
            record(event="error", item=num, step="item card read")
            die(f"vendor {num}", f"item {num} was created but its card could not be read, so it EXISTS in BC "
                f"without a vendor. {RECOVERY} Created so far: {done + [num]}")
        vpatch = {"Vendor_No": r["vendorNo"]}
        if r["vendorItemNo"]:
            vpatch["Vendor_Item_No"] = r["vendorItemNo"]
        st, res = bc.patch(f"{bc.odata}/Item_Card_Excel('{urllib.parse.quote(odq(num), safe='')}')",
                           card["@odata.etag"], vpatch)
        if st not in (200, 204):
            record(event="error", item=num, step="PATCH Vendor_No", http=st, body=str(res)[:300])
            hint = explain_error(json.dumps(res), st)
            die(f"vendor {num}", f"item {num} was created but the Vendor No. PATCH failed HTTP {st}: "
                f"{json.dumps(res)[:300]}" + (f"\n  {hint}" if hint else "")
                + f"\n  Item {num} now EXISTS in BC without a vendor. {RECOVERY} Created so far: {done + [num]}")
        card = bc.item_card(num) or {}
        if card.get("Vendor_No") != r["vendorNo"] or (r["vendorItemNo"] and card.get("Vendor_Item_No") != r["vendorItemNo"]):
            record(event="error", item=num, step="verify vendor", got=card.get("Vendor_No"))
            die(f"vendor {num}", f"read-back shows Vendor_No {card.get('Vendor_No')!r}, so item {num} EXISTS in BC "
                f"with the wrong or no vendor. {RECOVERY} Created so far: {done + [num]}")
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
    acct = dict(default=None, help="cached sign-in to use when more than one is cached (or BBS_BC_ACCOUNT)")
    w = sub.add_parser("whoami", help="sign in, prove the read path a commit needs, print who writes would be attributed to")
    w.add_argument("--account", **acct)
    c = sub.add_parser("check", help="validate the spec and gates; write the review sheet; no writes")
    c.add_argument("spec")
    c.add_argument("--account", **acct)
    m = sub.add_parser("commit", help="create the items after the rep approved the review sheet")
    m.add_argument("spec")
    m.add_argument("--approve", required=True, help="token printed by check")
    m.add_argument("--approved-by", required=True, help="name of the rep who read the review sheet")
    m.add_argument("--account", **acct)
    lo = sub.add_parser("logout", help="remove a cached sign-in")
    lo.add_argument("--account", default=None, help="which cached sign-in to remove")
    lo.add_argument("--all", action="store_true", help="remove every cached sign-in")
    args = ap.parse_args()
    {"whoami": cmd_whoami, "check": cmd_check, "commit": cmd_commit, "logout": cmd_logout}[args.cmd](args)


if __name__ == "__main__":
    main()
