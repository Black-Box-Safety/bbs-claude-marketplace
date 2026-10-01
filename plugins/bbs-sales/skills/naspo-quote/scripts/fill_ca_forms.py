#!/usr/bin/env python3
"""
fill_ca_forms.py — fill (and optionally sign) California state compliance PDFs
from a single JSON spec.

Every CA state RFQ packet is the same handful of AcroForm PDFs with the same
fields, so the per-quote work is data, not code. This script takes that data
and does the mechanical part: text fields, checkboxes, radio groups (which are
fiddly — see below), and signature-image stamping.

Usage:
    python fill_ca_forms.py <spec.json>

STABLE INTERFACE — do not rename this file, move it, or change its arguments.
It is the one vetted fill-and-sign script for California forms that no packet
profile covers (`ca-form-filler` Path B, and `naspo-quote`), and the managed
settings allow it by path (`plugins/bbs-foundations/docs/bbs-managed-settings.json`,
the `naspo-quote/scripts/` rule). A new name or a new argument stops matching
that rule, and a rep in auto mode is stopped mid-packet. Change the spec, not
the command line.

Spec shape (see references/form-field-maps.md for the field names per form):

{
  "src_dir":  "/path/to/folder/with/blank/forms",
  "out_dir":  "/path/to/output",
  "master_root": "/path/to/Black Box Safety - MASTER",
  "signer": { "name": "Parker Marshall", "title": "Sales Manager",
              "email": "parker@blackboxsafety.com" },
  "quote_total_incl_tax": "9,054.75",
  "quote_ref": "SQ-104032",
  "signature_date": "10.1.26",
  "forms": [
    {
      "form": "CalRecycle74",
      "src": "CalRecycle- Form 74 (01-2023).pdf",
      "out": "BBS_CalRecycle74_AGENCY_20260827.pdf",
      "text":   { "State Agency": "CDCR - CMC" },
      "signer_fields": { "name": "Print Name", "title": "Title" },
      "checks": { "Check Box3": true },
      "radios": { "YNagent": {"index": 0, "on": "1"} },
      "sign":   { "Signature": {"who": "parker", "date": "Date", "dx": 2, "dy": 0} },
      "fontsize": { "Descriptions L1": 6.5 }
    },
    {
      "form": "PD843",
      "src": "DGS PD 843.pdf", "out": "BBS_PD843_AGENCY_20260827.pdf",
      "sign":   { "Signature": {"who": "jackson", "line": "dv_owner"} }
    }
  ]
}

`form` is required on every entry: one of the kinds in FORM_KINDS, or
`packet` for a bound PDF that carries several forms (CDCR Packet C). On a
`packet` every `sign` entry also says `"line": "rep"` or `"line": "dv_owner"`,
and the page each signature sits on must read as a form with that line in the
form table (ca-form-rules.md, "Machine-readable form table"). There is no
`signatures` map to fill in: each delegate's image is read from
vendor_profile.json (a legacy `signatures` entry is refused unless it names the
same file).

* the limit — `quote_total_incl_tax` is the quote's grand total including
  tax, from the quote of record (the BC sales quote / the SQ sent), never an
  estimate. A delegated signature is applied only when it is strictly under
  `signature_delegation.limit_usd` in vendor_profile.json. Missing, unreadable,
  or at/over the limit: no `sign` entry is stamped, their `date` fields stay
  blank, every one is reported "⚑ SIGNATURE REQUIRED", and the packet is
  written unsigned (ca-form-rules.md, "Delegated signatures").

* field IDs — every name in `text`, `checks`, `radios`, `sign` and
  `signer_fields` must exist in the blank, with the right type (a checkbox for
  `checks`, a radio for `radios`, a text field for `text`). One that doesn't
  stops the run with nothing written — the same rule fill_obs_packet.py applies.

* pre-filled values — an inbound packet often arrives with the agency's own
  entries in it (solicitation, buyer, ship-to, line items). Those are kept. A
  spec value that would change a non-empty field is refused unless the field is
  listed in the form's `replace_prefilled` with the reason (the rep's call: the
  vendor profile wins over an agency's stale copy of BBS's own details, but
  someone says so per field). Every kept value is reported.

Notes that save you a debugging cycle:

* radios — a radio group shares one field name across widgets. Setting
  `field_value` per widget is not enough: PyMuPDF can leave the losing widget's
  /AS appearance state on its own "on" name, so the form renders with two dots
  filled. This script writes /AS explicitly on every widget and /V on the parent,
  which is what actually makes the PDF render one selection. `index` is the
  widget's position top-to-bottom in the group; `on` is that widget's export
  value (get it from `inspect_form.py`).

* text overflow — most of these fields are single-line and silently clip rather
  than shrink. Keep values short, or set `fontsize` for that field. Always
  render and look (the script prints a reminder).

* signatures — a /Sig field can't hold text, so the widget is deleted and the
  PNG drawn in its place. Text fields labeled "Signature" get the same treatment.
  `dx`/`dy` nudge the image when the box's printed caption is in the way.
  Where each signer's PNG lives is recorded once, as `signature_image` on that
  person in ${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json.

* signature paths — taken from `signature_image` on the delegate in the vendor
  profile, never from the spec, so one delegate's PNG can never be stamped
  under another's name. A path starting `MASTER/` is joined onto `master_root`
  here, so nobody builds an absolute path by hand. `master_root` is the synced `Black Box Safety - MASTER`
  library folder (on a Teams-site sync its name carries a "… - " prefix). A
  `MASTER/` path with no `master_root` stops the run. Absolute paths also work.

* signer — the rep names who signs the rep-signed lines (CalRecycle 74, Darfur,
  OBS 1000, OBS 4007(B)/(C) bidder) on every run; the spec carries it as `signer` and there
  is no default. `check_signer()` runs first: no signer stops the run
  ([MISSING — NEEDS INPUT]); a signer whose email is not exactly one address on
  BBS's domain (from the vendor profile's `contact.email`) is REFUSED, checked
  before the name. Every `sign` entry's `who` must be a signature delegate
  (`signature_delegation` in the vendor profile: a role, or that person's email
  local part — "parker", "jackson"). On a DV-owner form (`form` PD843, CV012,
  STD204, STD205) the only stamp allowed is the dvbe_owner's, marked
  `"line": "dv_owner"`, whoever the signer is — those declarations are always
  Jackson's. On every other form `dv_owner` is refused and a stamp is a
  rep-signed line: its delegate must BE the signer (email or recorded alias,
  and name). OBS1000 is a rep-signed line (Parker, 2026-10-01). So a non-delegate signer can have no `sign` entry on a rep-signed
  line — the print name and title come from `signer_fields` (filled from the
  signer; a `text` value that differs is refused), signature and date stay
  blank, and the line is flagged "⚑ SIGNATURE REQUIRED". Rule: ca-form-rules.md,
  "Delegated signatures".

* nothing is written unless everything worked (AGENTS.md invariant 4).
  `preflight()` runs before any PDF is opened: it checks every `sign` entry's
  shape, that each signer's path resolves to a file whose first bytes are a PNG
  signature (reading them also forces an online-only OneDrive placeholder to
  download, or fails if it can't), and that every form's `src` exists. Forms
  are then filled into a temporary folder and moved into `out_dir` only after
  every one succeeded and every `sign` entry stamped at least one field. A
  `sign` field that matches nothing prints "⚑ SIGNATURE NOT APPLIED" and the run
  exits non-zero with `out_dir` untouched. The fix is the path or field name,
  or dropping that `sign` entry so the line is left unsigned for the rep.

Requires: pymupdf
"""
import json
import os
import shutil
import sys
import tempfile

try:
    import fitz  # PyMuPDF
except ImportError:  # checked in main(); check_signatures() needs no fitz
    fitz = None

TRUTHY = {True, "true", "yes", "on", "x", "1", "checked"}

PLUGIN_ROOT = (os.environ.get("CLAUDE_PLUGIN_ROOT")
               or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
VENDOR_PROFILE = os.path.join(PLUGIN_ROOT, "references", "vendor_profile.json")
FORM_RULES = os.path.join(PLUGIN_ROOT, "references", "ca-form-rules.md")
DV_OWNER_LINE = "dv_owner"
REP_LINE = "rep"
PACKET = "packet"
# What each form entry must say it is. DV-owner declarations are the disabled-
# veteran owner's (ca-form-rules.md): only these may carry a `dv_owner` stamp,
# and on these only the dvbe_owner's stamp is allowed.
FORM_KINDS = ("PD843", "CV012", "STD204", "STD205", "CalRecycle74", "Darfur",
              "OBS1000", "OBS4007B", "OBS4007C", "Supplement", "GSPD05105", "other",
              PACKET)
DV_OWNER_FORMS = ("PD843", "CV012", "STD204", "STD205")
# Forms that carry no signature BBS applies.
UNSIGNED_FORMS = ("Supplement", "GSPD05105", "other")
TABLE_BEGIN, TABLE_END = "<!-- bbs-form-table:begin -->", "<!-- bbs-form-table:end -->"
HEADER_CHARS = 400   # the form table's markers are read from a page's first 400 non-space chars
TEXT_TYPES = ("Text", "ComboBox", "ListBox")
SIGN_TYPES = ("Text", "Signature")


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MASTER_PREFIX = "MASTER/"
FIX_HINT = ("Fix the path, or leave the line unsigned for the rep (drop that "
            "`sign` entry). Nothing was written.")


class SignatureMissing(Exception):
    """A form asks for a signature that cannot be applied, or a form is missing."""


def _raise(problems):
    if problems:
        lines = "\n".join(f"⚑ SIGNATURE REQUIRED — {p}" if p.startswith("signature image")
                          else p for p in dict.fromkeys(problems))
        raise SignatureMissing(lines + "\n" + FIX_HINT)


def _sign_entries(form, problems):
    """Yield (field, who, sig) for each well-formed `sign` entry; record bad ones."""
    where = form.get("src", "?") if isinstance(form, dict) else "?"
    sign = form.get("sign") if isinstance(form, dict) else None
    if sign is None:
        return
    if not isinstance(sign, dict):
        problems.append(f"`sign` in {where} must be an object of field -> "
                        f"{{\"who\": ...}}, got {type(sign).__name__}")
        return
    for field, sig in sign.items():
        if not isinstance(sig, dict):
            problems.append(f"`sign` entry {field!r} in {where} must be an object "
                            f"with a `who`, got {type(sig).__name__}")
            continue
        who = sig.get("who")
        if not isinstance(who, str) or not who:
            problems.append(f"`sign` entry {field!r} in {where} names no signer "
                            f"(`who` missing or empty)")
            continue
        yield field, who, sig


def resolve_sig_path(path, master_root):
    """Return an absolute path, or raise ValueError saying why it can't be built."""
    p = path.replace("\\", "/")
    if p.startswith(MASTER_PREFIX):
        if not master_root:
            raise ValueError(f"{path} is relative to the MASTER library, but the spec "
                             f"has no `master_root`")
        return os.path.join(master_root, *p[len(MASTER_PREFIX):].split("/"))
    if p.startswith("..."):
        raise ValueError(f"{path} uses the old '...' prefix; use the `MASTER/` path "
                         f"from vendor_profile.json")
    if not os.path.isabs(path):
        raise ValueError(f"{path} is neither absolute nor `MASTER/`-relative")
    return path


def _png_problem(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(8)
    except OSError as e:
        return f"could not be read ({e.strerror or e})"
    if not head:
        return "is empty (0 bytes)"
    if head != PNG_MAGIC:
        return "is not a PNG"
    return None


def check_signatures(forms, sig_paths, master_root=None):
    """Return {signer: absolute path} for every signer any form asks for.

    Raises SignatureMissing naming each signer and path that can't be used:
    a malformed `sign` entry, a signer absent from `signatures`, a path that
    can't be resolved, a file that is missing, unreadable, empty or not a PNG.
    Before this existed, a missing signer died with a bare KeyError and a
    missing file died inside fitz.Pixmap — after earlier forms were saved signed.
    """
    problems, resolved = [], {}
    for form in forms:
        for field, who, _sig in _sign_entries(form, problems):
            where = f"{form.get('src', '?')} field {field!r}"
            raw = (sig_paths or {}).get(who)
            if not raw:
                problems.append(f"signature image for {who} not given in the spec's "
                                f"`signatures` ({where})")
                continue
            try:
                path = resolve_sig_path(raw, master_root)
            except ValueError as e:
                problems.append(f"signature image for {who}: {e} ({where})")
                continue
            if not os.path.isfile(path):
                problems.append(f"signature image for {who} not found at {path} ({where})")
                continue
            bad = _png_problem(path)
            if bad:
                problems.append(f"signature image for {who} at {path} {bad} ({where})")
                continue
            resolved[who] = path
    _raise(problems)
    return resolved


def check_sources(forms, src_dir):
    """Raise SignatureMissing if any form's blank `src` PDF is not there."""
    problems = []
    for form in forms:
        src = form.get("src")
        if not src:
            problems.append(f"a form has no `src` (out: {form.get('out', '?')})")
        elif not os.path.isfile(os.path.join(src_dir, src)):
            problems.append(f"blank form not found: {os.path.join(src_dir, src)}")
    _raise(problems)


def load_delegation(path=None):
    """(employee domain, [delegate]) from the vendor profile.

    signature_delegation lists roles; each resolves to its
    authorized_representatives entry, so a delegate's identity AND signature
    image are written once, there. The image path returned here is the only one
    a delegate's signature is ever stamped from.
    """
    with open(path or VENDOR_PROFILE, encoding="utf-8") as fh:
        vp = json.load(fh)
    reps = {r.get("role"): r for r in vp.get("authorized_representatives", [])}
    delegates = []
    for role in vp["signature_delegation"]["delegates"]:
        if role not in reps:
            raise SignatureMissing(f"signature_delegation names role {role!r}, which has "
                                   f"no authorized_representatives entry in the vendor "
                                   f"profile. Nothing was written.")
        r = reps[role]
        delegates.append({"role": role, "name": r["name"], "email": r["email"].lower(),
                          "aliases": [a.lower() for a in r.get("aliases") or []],
                          "signature_image": r.get("signature_image")})
    return vp["contact"]["email"].rsplit("@", 1)[1].lower(), delegates


def _norm(s):
    return " ".join(str(s or "").split()).lower()


def _delegate_for(who, delegates):
    """The delegate a `sign` entry's `who` names: a role or an email local part."""
    w = who.strip().lower()
    for d in delegates:
        locals_ = {a.split("@")[0] for a in [d["email"], *d["aliases"]]}
        if w == d["role"] or w in locals_:
            return d
    return None


def check_form_kinds(forms):
    """Every form entry names what it is, from FORM_KINDS. Raises otherwise."""
    problems = []
    for form in forms:
        kind = form.get("form") if isinstance(form, dict) else None
        if kind not in FORM_KINDS:
            problems.append(f"REFUSED: {form.get('src', '?') if isinstance(form, dict) else form}"
                            f" has `form` {kind!r}; it must be one of "
                            f"{', '.join(FORM_KINDS)}. Which lines are DV-owner lines "
                            f"depends on it")
    _raise(problems)


def check_signer(spec, profile_path=None):
    """Refuse a spec whose signer or signature use breaks the rep-signed-lines rule.

    Returns (signer delegate or None, delegates). Raises SignatureMissing
    (nothing written) on: no signer; a signer not on BBS's domain (checked
    before the name; non-ASCII addresses refused so no look-alike character can
    fold into a BBS address); a form with no valid `form`; a `sign` entry whose
    `who` is not a delegate; on a DV-owner form (PD 843, CV 012, STD 204,
    STD 205) any delegate stamp that is not the dvbe_owner marked `dv_owner`;
    on a form that carries no BBS signature, any stamp; on a `packet`, a stamp
    without a `line`, or whose delegate does not fit that line; on any other
    form a `dv_owner` stamp, or a stamp whose delegate is not the named signer.
    Which page a packet stamp lands on is checked later, against the PDF.
    """
    domain, delegates = load_delegation(profile_path)
    check_form_kinds(spec.get("forms", []))
    signer = spec.get("signer") or {}
    name = " ".join(str(signer.get("name", "")).split())
    email = str(signer.get("email", "")).strip()
    if not name and not email:
        raise SignatureMissing("[MISSING — NEEDS INPUT] `signer`: the rep names who signs "
                               "the rep-signed lines (OBS 4007(B)/(C) bidder, Darfur, "
                               "CalRecycle 74, OBS 1000); there is no default. Nothing "
                               "was written.")
    if not email:
        raise SignatureMissing(f"[MISSING — NEEDS INPUT] signer email for {name}: it is how "
                               f"the signer is confirmed as a BBS employee. Nothing was written.")
    if (not email.isascii() or email.count("@") != 1
            or email.lower().split("@")[1] != domain):
        raise SignatureMissing(f"REFUSED: the signer must be a BBS employee (an @{domain} "
                               f"address); {name or '(no name)'} <{email}> is not. "
                               f"Customers, agencies and third parties never sign BBS's "
                               f"lines. Nothing was written.")
    email = email.lower()
    if not name:
        raise SignatureMissing(f"[MISSING — NEEDS INPUT] signer name for {email}. "
                               f"Nothing was written.")
    by_email = next((d for d in delegates if email in {d["email"], *d["aliases"]}), None)
    by_name = next((d for d in delegates if _norm(name) == _norm(d["name"])), None)
    signer_delegate = by_email if by_email is not None and by_email is by_name else None
    if signer_delegate:
        why = None
    elif by_name:
        why = (f"{name}'s email does not match the delegate's recorded address "
               f"({by_name['email']})")
    elif by_email:
        why = (f"the name {name} does not match the delegate recorded for {email} "
               f"({by_email['name']})")
    else:
        why = f"{name} is not a signature delegate in vendor_profile.json"

    problems = []
    for form in spec.get("forms", []):
        dv_form = form["form"] in DV_OWNER_FORMS
        for field, who, sig in _sign_entries(form, []):
            where = f"{form.get('src', '?')} ({form['form']}) field {field!r}"
            d = _delegate_for(who, delegates)
            marked = sig.get("line") == DV_OWNER_LINE
            if d is None:
                problems.append(f"REFUSED: `who` {who!r} on {where} is not a signature "
                                f"delegate; only delegates' signatures are applied")
            elif form["form"] in UNSIGNED_FORMS:
                problems.append(f"REFUSED: {where} — this form carries no signature BBS "
                                f"applies; drop the `sign` entry")
            elif form["form"] == PACKET:
                line = sig.get("line")
                if line not in (REP_LINE, DV_OWNER_LINE):
                    problems.append(f"REFUSED: {where} is in a bound packet, so the `sign` "
                                    f"entry must say `\"line\": \"rep\"` or "
                                    f"`\"line\": \"dv_owner\"`; the page it sits on is "
                                    f"checked against that when the packet is filled")
                elif line == DV_OWNER_LINE and d["role"] != "dvbe_owner":
                    problems.append(f"REFUSED: {where} is marked as a DV-owner line; only "
                                    f"the dvbe_owner signs it, not {d['name']}")
                elif line == REP_LINE and d is not signer_delegate:
                    problems.append(f"REFUSED: {d['name']}'s signature on {where}, but the "
                                    f"signer the rep named is {name} <{email}>"
                                    + (f" — {why}" if why else "")
                                    + ". Leave it blank for a hand signature")
            elif dv_form:
                if not marked or d["role"] != "dvbe_owner":
                    problems.append(f"REFUSED: {where} is a DV-owner declaration; only the "
                                    f"dvbe_owner signs it, as `\"line\": \"dv_owner\"` — "
                                    f"not {d['name']}" + ("" if marked else " unmarked"))
            elif marked:
                problems.append(f"REFUSED: {where} is marked `dv_owner`, but only "
                                f"{', '.join(DV_OWNER_FORMS)} carry DV-owner lines")
            elif d is not signer_delegate:
                problems.append(f"REFUSED: {d['name']}'s signature on {where}, but the signer "
                                f"the rep named is {name} <{email}>"
                                + (f" — {why}" if why else "")
                                + ". A delegate's signature is never applied to someone "
                                  "else's line: leave it blank for a hand signature and flag "
                                  "⚑ SIGNATURE REQUIRED")
    if problems:
        raise SignatureMissing("\n".join(dict.fromkeys(problems)) + "\nNothing was written.")
    return signer_delegate, delegates


def delegate_signature_paths(spec, delegates):
    """{who: signature path} for every `who` the forms stamp, from the PROFILE.

    A delegate's image is the `signature_image` recorded on that delegate in
    vendor_profile.json -- never a path typed into the spec. A spec
    `signatures` entry is accepted only if it resolves to the same file as the
    profile's; any other path (e.g. Jackson's PNG keyed as "parker") is refused.
    """
    root = spec.get("master_root")
    given = spec.get("signatures") or {}
    paths, problems = {}, []
    for form in spec.get("forms", []):
        for _field, who, _sig in _sign_entries(form, []):
            d = _delegate_for(who, delegates)
            if d is None or who in paths:
                continue
            recorded = d.get("signature_image")
            if not recorded:
                problems.append(f"signature image for {who}: {d['name']} has no "
                                f"`signature_image` in vendor_profile.json")
                continue
            paths[who] = recorded
            if who in given:
                try:
                    same = (os.path.normcase(os.path.abspath(resolve_sig_path(given[who], root)))
                            == os.path.normcase(os.path.abspath(resolve_sig_path(recorded, root))))
                except ValueError:
                    same = False
                if not same:
                    problems.append(f"REFUSED: the spec's `signatures` path for {who} "
                                    f"({given[who]}) is not {d['name']}'s signature_image "
                                    f"in vendor_profile.json ({recorded}). A delegate's "
                                    f"signature comes from the profile only")
    _raise(problems)
    return paths


def apply_signer_fields(spec):
    """Fill each form's `signer_fields` (print name / title) from the signer.

    A form may name {"name": <field>, "title": <field>}; those fields are filled
    from `signer`, never typed. The same field also set in `text` to anything
    else is refused, so the printed name cannot differ from the signer.
    """
    signer = spec.get("signer") or {}
    problems = []
    for form in spec.get("forms", []):
        sf = form.get("signer_fields") or {}
        text = form.setdefault("text", {})
        for key, field in sf.items():
            if key not in ("name", "title"):
                problems.append(f"REFUSED: `signer_fields` key {key!r} in {form.get('src')}; "
                                f"only name and title")
                continue
            want = " ".join(str(signer.get(key, "")).split())
            if field in text and " ".join(str(text[field]).split()) != want:
                problems.append(f"REFUSED: {form.get('src')} field {field!r} is set to "
                                f"{text[field]!r} but the signer's {key} is {want!r}")
            text[field] = want
    _raise(problems)


def load_limit(path=None):
    """signature_delegation.limit_usd from the vendor profile (R1b, 2026-10-01)."""
    with open(path or VENDOR_PROFILE, encoding="utf-8") as fh:
        limit = json.load(fh)["signature_delegation"].get("limit_usd")
    if isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit <= 0:
        raise SignatureMissing("REFUSED: vendor_profile.json signature_delegation has no "
                               "usable `limit_usd`, so no delegated signature can be "
                               "applied. Nothing was written.")
    return float(limit)


def parse_total(value):
    """The quote total incl. tax as a float, or None if missing or unreadable.

    Accepts a number or a money string ("$9,054.75", "9054.75"). Anything else —
    empty, a word, a negative, two numbers — is unreadable, never guessed at.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        total = float(value)
    else:
        text = str(value).strip().replace("$", "").replace(",", "").replace("USD", "").strip()
        try:
            total = float(text)
        except ValueError:
            return None
    if total != total or total < 0 or total in (float("inf"),):
        return None
    return total


def signing_allowed(spec, limit):
    """(True, None) when delegated signatures may be applied, else (False, why)."""
    raw = spec.get("quote_total_incl_tax")
    total = parse_total(raw)
    if total is None:
        return False, ("the quote total including tax is missing or unreadable "
                       f"(`quote_total_incl_tax`: {raw!r}); take it from the quote of record")
    if total >= limit:
        return False, (f"the quote total including tax, ${total:,.2f}, is not under the "
                       f"${limit:,.0f} delegation limit")
    return True, None


def load_form_table(path=None):
    """The machine-readable form table in ca-form-rules.md, validated."""
    with open(path or FORM_RULES, encoding="utf-8") as fh:
        text = fh.read()
    try:
        body = text[text.index(TABLE_BEGIN) + len(TABLE_BEGIN):text.index(TABLE_END)]
        body = body.strip()
        if body.startswith("```"):
            body = body.split("\n", 1)[1].rsplit("```", 1)[0]
        table = json.loads(body)
    except (ValueError, IndexError) as e:
        raise SignatureMissing(f"REFUSED: the form table in ca-form-rules.md could not be "
                               f"read ({e}); no signature can be placed. Nothing was written.")
    for kind, row in table.items():
        ok = (isinstance(row, dict) and isinstance(row.get("markers"), list) and row["markers"]
              and all(isinstance(m, str) and m.strip() for m in row["markers"])
              and isinstance(row.get("none", []), list)
              and row.get("line") in (REP_LINE, DV_OWNER_LINE, None))
        if not ok:
            raise SignatureMissing(f"REFUSED: form table row {kind!r} in ca-form-rules.md is "
                                   f"malformed. Nothing was written.")
    return table


def _squash(text):
    return "".join(str(text).split()).lower()


def classify_page(text, table):
    """Every form kind whose markers the page header carries (usually 0 or 1)."""
    head = _squash(text)[:HEADER_CHARS]
    return [k for k, row in table.items()
            if all(_squash(m) in head for m in row["markers"])
            and not any(_squash(n) in head for n in row.get("none", []))]


def line_for_kind(kind, table):
    """Whose line a declared, single-form kind carries."""
    if kind in DV_OWNER_FORMS:
        return DV_OWNER_LINE
    if kind in UNSIGNED_FORMS or kind == PACKET:
        return None
    return table.get(kind, {}).get("line", REP_LINE)


def apply_dates(spec, allowed):
    """Fill each `sign` entry's `date` field with signature_date — only if it signs."""
    problems = []
    date = " ".join(str(spec.get("signature_date", "")).split())
    for form in spec.get("forms", []):
        text = form.setdefault("text", {})
        for field, _who, sig in _sign_entries(form, []):
            dfield = sig.get("date")
            if not dfield:
                continue
            if dfield in text:
                problems.append(f"REFUSED: {form.get('src')} sets `date` field {dfield!r} in "
                                f"`text` too; the signature date follows the signature")
            elif allowed and date:
                text[dfield] = date
    _raise(problems)


def withhold_signatures(spec, why):
    """Strip every `sign` entry; return the ⚑ lines that say what was left blank."""
    flags = []
    for form in spec.get("forms", []):
        for field, who, _sig in _sign_entries(form, []):
            flags.append(f"⚑ SIGNATURE REQUIRED — {form.get('src')} field {field!r} "
                         f"({who}): left blank because {why}. Sign and date by hand.")
        form.pop("sign", None)
    return flags


def preflight(spec):
    """Everything that can be checked without opening a PDF. Returns sig paths."""
    return prepare(spec)[0]


def prepare(spec):
    """preflight(), plus the context fill_form checks against each PDF.

    Returns (resolved sig paths, ctx). ctx carries what fill_form checks against
    the PDF: the signer's delegate, the delegates, the form table, and the ⚑
    lines for signatures withheld under the limit.
    """
    forms = spec["forms"]
    signer_delegate, delegates = check_signer(spec)
    apply_signer_fields(spec)
    allowed, why = signing_allowed(spec, load_limit())
    withheld = [] if allowed else withhold_signatures(spec, why)
    apply_dates(spec, allowed)
    sig_paths = delegate_signature_paths(spec, delegates)
    sigs = check_signatures(forms, sig_paths, spec.get("master_root"))
    check_sources(forms, spec["src_dir"])
    ctx = {"signer_delegate": signer_delegate, "delegates": delegates,
           "table": load_form_table(), "withheld": withheld}
    return sigs, ctx


def _stamp(page, rect, img_path, dx, dy, max_h=22):
    px = fitz.Pixmap(img_path)
    h = min(rect.height * 1.6, max_h)
    w = min(h * px.width / px.height, rect.width)
    h = w * px.height / px.width
    box = fitz.Rect(rect.x0 + dx, rect.y1 - h + dy, rect.x0 + dx + w, rect.y1 + dy)
    page.insert_image(box, filename=img_path, overlay=True)


def _widget_index(doc):
    """{field name: [(page index, widget type, current value)]} for the whole PDF."""
    index = {}
    for pno, page in enumerate(doc):
        for w in (page.widgets() or []):
            index.setdefault(w.field_name, []).append(
                (pno, getattr(w, "field_type_string", "Text"),
                 getattr(w, "field_value", "") or ""))
    return index


def validate_fields(spec, index):
    """Refuse unknown field IDs and wrong types — nothing is guessed onto a form."""
    problems, src = [], spec.get("src", "?")

    def need(names, types, what):
        for name in names:
            if name not in index:
                problems.append(f"REFUSED: {src} has no field {name!r} ({what}). Re-read the "
                                f"blank with inspect_form.py; field IDs are never guessed")
            elif not any(t in types for _p, t, _v in index[name]):
                got = sorted({t for _p, t, _v in index[name]})
                problems.append(f"REFUSED: {src} field {name!r} is {'/'.join(got)}, not "
                                f"{'/'.join(types)} ({what})")

    need(spec.get("text", {}), TEXT_TYPES, "text")
    need(spec.get("checks", {}), ("CheckBox",), "checks")
    need(spec.get("radios", {}), ("RadioButton",), "radios")
    need((spec.get("sign") or {}), SIGN_TYPES, "sign")
    _raise(problems)


def _on(value):
    return str(value).strip().lstrip("/").lower() not in ("", "off", "no", "false", "0")


def check_prefilled(spec, index):
    """Keep the agency's entries. Returns the report lines for what was kept."""
    problems, kept, src = [], [], spec.get("src", "?")
    replace = spec.get("replace_prefilled") or {}
    for name, why in replace.items():
        if not str(why or "").strip():
            problems.append(f"REFUSED: {src} `replace_prefilled` {name!r} gives no reason")
    touched = set(spec.get("text", {})) | set(spec.get("checks", {})) | set(spec.get("radios", {}))
    for name, value in spec.get("text", {}).items():
        current = next((v for _p, _t, v in index.get(name, []) if str(v).strip()), "")
        if current and " ".join(str(current).split()) != " ".join(str(value).split()) \
                and name not in replace:
            problems.append(f"REFUSED: {src} field {name!r} already holds {current!r} (filled "
                            f"by the agency); the spec would write {value!r}. Keep it, or list "
                            f"it in `replace_prefilled` with the rep's reason")
    for name, value in spec.get("checks", {}).items():
        current = any(_on(v) for _p, _t, v in index.get(name, []))
        if current and value not in TRUTHY and name not in replace:
            problems.append(f"REFUSED: {src} checkbox {name!r} is already ticked by the "
                            f"agency; the spec would clear it")
    for name, entries in index.items():
        if name in touched or name in (spec.get("sign") or {}):
            continue
        for _p, t, v in entries:
            if t in TEXT_TYPES and str(v).strip():
                kept.append(f"kept agency value: {src} {name!r} = {str(v).strip()!r}")
                break
    _raise(problems)
    return kept


def check_sign_pages(spec, doc, index, ctx):
    """Every stamp lands on a page that reads as a form whose line it may sign."""
    problems, kind, table = [], spec.get("form"), ctx["table"]
    delegates = ctx["delegates"]
    for field, who, sig in _sign_entries(spec, []):
        d = _delegate_for(who, delegates)
        for pno, _t, _v in index.get(field, []):
            page = _doc_page(doc, pno)
            hits = classify_page(page.get_text() if hasattr(page, "get_text") else "", table)
            where = f"{spec.get('src')} p{pno + 1} field {field!r}"
            if kind == PACKET:
                if len(hits) != 1:
                    problems.append(f"REFUSED: {where} — the page reads as "
                                    f"{', '.join(hits) or 'no known form'}; a signature is "
                                    f"placed only on a page the form table identifies as one "
                                    f"form")
                    continue
                line = table[hits[0]]["line"]
                if line != sig.get("line"):
                    problems.append(f"REFUSED: {where} is on {hits[0]}, whose line is "
                                    f"{line or 'unsigned'}, but the spec says "
                                    f"{sig.get('line')!r}")
            elif hits and hits != [kind]:
                problems.append(f"REFUSED: {where} — the spec says this is {kind}, but the "
                                f"page reads as {', '.join(hits)}")
                continue
            else:
                line = line_for_kind(kind, table)
            if line == DV_OWNER_LINE and (d is None or d["role"] != "dvbe_owner"):
                problems.append(f"REFUSED: {where} is a DV-owner line; only the dvbe_owner's "
                                f"signature goes on it")
            elif line == REP_LINE and (d is None or d is not ctx["signer_delegate"]):
                problems.append(f"REFUSED: {where} is a rep-signed line; only the named "
                                f"signer's own signature goes on it")
            elif line is None:
                problems.append(f"REFUSED: {where} — this form carries no BBS signature")
    _raise(problems)


def _doc_page(doc, pno):
    for i, page in enumerate(doc):
        if i == pno:
            return page
    raise IndexError(pno)


def fill_form(spec, sig_paths, src_dir, out_dir, master_root=None, ctx=None):
    """Fill one form into out_dir. Returns (out_path, [unapplied sign messages], [kept]).

    Validates field IDs and types, keeps the agency's pre-filled values, and
    checks each signature's page before writing anything to the document.
    """
    sig_paths = check_signatures([spec], sig_paths, master_root)
    doc = fitz.open(os.path.join(src_dir, spec["src"]))
    index = _widget_index(doc)
    validate_fields(spec, index)
    kept = check_prefilled(spec, index)
    if ctx is not None:
        check_sign_pages(spec, doc, index, ctx)
    text = spec.get("text", {})
    checks = spec.get("checks", {})
    sizes = spec.get("fontsize", {})

    for page in doc:
        for w in (page.widgets() or []):
            name = w.field_name
            if name in text:
                if str(getattr(w, "field_value", "") or "").strip() and name not in \
                        (spec.get("replace_prefilled") or {}):
                    continue  # same value already there (anything else was refused)
                w.field_value = str(text[name])
                w.text_fontsize = sizes.get(name, 8)
                w.update()
            elif name in checks:
                states = w.button_states() or {}
                ons = [s for s in (states.get("normal") or []) + (states.get("down") or [])
                       if s != "Off"]
                on = ons[0] if ons else "Yes"
                w.field_value = on if checks[name] in TRUTHY else "Off"
                w.update()

    # Radio groups: one field name, several widgets. Write /AS on each widget and
    # /V on the shared parent, otherwise the losing widget can still render filled.
    for name, choice in (spec.get("radios") or {}).items():
        widgets = [(p, w) for p in doc for w in (p.widgets() or []) if w.field_name == name]
        for i, (_p, w) in enumerate(widgets):
            if i == choice["index"]:
                w.field_value = choice["on"]
                w.update()
                doc.xref_set_key(w.xref, "AS", "/" + choice["on"])
                parent = doc.xref_get_key(w.xref, "Parent")
                if parent and parent[0] == "xref":
                    doc.xref_set_key(int(parent[1].split()[0]), "V", "/" + choice["on"])
            else:
                w.field_value = "Off"
                w.update()
                doc.xref_set_key(w.xref, "AS", "/Off")

    unapplied = []
    for name, who, sig in _sign_entries(spec, []):
        img = sig_paths[who]
        stamped = 0
        for page in doc:
            for w in list(page.widgets() or []):
                if w.field_name == name:
                    rect = w.rect
                    try:
                        page.delete_widget(w)
                    except Exception:
                        pass
                    _stamp(page, rect, img, sig.get("dx", 2), sig.get("dy", 0))
                    stamped += 1
        if not stamped:
            unapplied.append(f"⚑ SIGNATURE NOT APPLIED — {who}: {spec['src']} "
                             f"field {name!r} not found")

    out = os.path.join(out_dir, spec["out"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    doc.save(out)
    doc.close()
    return out, unapplied, kept


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    src_dir, out_dir = spec["src_dir"], spec["out_dir"]
    try:
        sigs, ctx = prepare(spec)
    except SignatureMissing as e:
        sys.exit(f"STOP: {e}")
    if fitz is None:
        sys.exit("pymupdf required: python -m pip install pymupdf "
                 "(Mac: python3 -m pip install --user pymupdf, or use a venv)")

    staging = tempfile.mkdtemp(prefix="fill_ca_forms-")
    try:
        unapplied, kept = [], []
        for form in spec["forms"]:
            try:
                _out, missed, form_kept = fill_form(form, sigs, src_dir, staging,
                                                    spec.get("master_root"), ctx)
            except SignatureMissing as e:
                sys.exit(f"STOP: {e}")
            unapplied += missed
            kept += form_kept
        if unapplied:
            print("\n".join(unapplied), file=sys.stderr)
            sys.exit("STOP: a signature line was not signed. " + FIX_HINT)
        os.makedirs(out_dir, exist_ok=True)
        for form in spec["forms"]:
            dest = os.path.join(out_dir, form["out"])
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            shutil.move(os.path.join(staging, form["out"]), dest)
            print("wrote", dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    for line in kept:
        print(line)
    if ctx["withheld"]:
        print("\nSIGNATURES WITHHELD — the packet was written UNSIGNED:")
        print("\n".join(ctx["withheld"]))
        print("\n".join(ctx["withheld"]), file=sys.stderr)
    print("\nNow render every page and look at it — these fields clip silently.")


if __name__ == "__main__":
    main()
