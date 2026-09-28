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

Spec shape (see references/form-field-maps.md for the field names per form):

{
  "src_dir":  "/path/to/folder/with/blank/forms",
  "out_dir":  "/path/to/output",
  "master_root": "/path/to/Black Box Safety - MASTER",
  "signer": { "name": "Parker Marshall", "title": "Sales Manager",
              "email": "parker@blackboxsafety.com" },
  "signatures": { "parker":  "MASTER/Customers/.../parker-signature.png",
                  "jackson": "MASTER/Jackson Dalton Signature/Copy of JACKSON_SIG.png" },
  "forms": [
    {
      "src": "CalRecycle- Form 74 (01-2023).pdf",
      "out": "BBS_CalRecycle74_AGENCY_20260827.pdf",
      "text":   { "State Agency": "CDCR - CMC" },
      "checks": { "Check Box3": true },
      "radios": { "YNagent": {"index": 0, "on": "1"} },
      "sign":   { "Signature": {"who": "parker", "dx": 2, "dy": 0} },
      # on a DV-owner declaration (DGS PD 843, CV 012, STD 204):
      #   "sign": { "Signature": {"who": "jackson", "line": "dv_owner"} }
      "fontsize": { "Descriptions L1": 6.5 }
    }
  ]
}

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

* signature paths — copy `signature_image` from the vendor profile as-is. A
  path starting `MASTER/` is joined onto `master_root` here, so nobody builds an
  absolute path by hand. `master_root` is the synced `Black Box Safety - MASTER`
  library folder (on a Teams-site sync its name carries a "… - " prefix). A
  `MASTER/` path with no `master_root` stops the run. Absolute paths also work.

* signer — the rep names who signs the rep-signed lines (CalRecycle 74, Darfur,
  OBS 4007(B) bidder) on every run; the spec carries it as `signer` and there
  is no default. `check_signer()` runs first: no signer stops the run
  ([MISSING — NEEDS INPUT]); a signer whose email is not exactly one address on
  BBS's domain (from the vendor profile's `contact.email`) is REFUSED, checked
  before the name. Every `sign` entry's `who` must be a signature delegate
  (`signature_delegation` in the vendor profile: a role, or that person's email
  local part — "parker", "jackson"). An entry marked `"line": "dv_owner"` must
  be the dvbe_owner delegate and is allowed whoever the signer is — those
  declarations are always Jackson's. Any other entry is a rep-signed line: its
  delegate must BE the signer (email or recorded alias, and name). So a
  non-delegate signer can have no `sign` entry on a rep-signed line — fill the
  print name and title, leave signature and date blank, and flag
  "⚑ SIGNATURE REQUIRED". Rule: ca-form-rules.md, "Rep-signed lines".

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

VENDOR_PROFILE = os.path.join(
    os.environ.get("CLAUDE_PLUGIN_ROOT")
    or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
    "references", "vendor_profile.json")
DV_OWNER_LINE = "dv_owner"


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
    authorized_representatives entry, so a delegate's identity is written once.
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
                          "aliases": [a.lower() for a in r.get("aliases") or []]})
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


def check_signer(spec, profile_path=None):
    """Refuse a spec whose signer or signature use breaks the rep-signed-lines rule.

    Returns the signer's delegate entry, or None for a non-delegate BBS signer.
    Raises SignatureMissing (nothing written) on: no signer; a signer not on
    BBS's domain (checked before the name); a `sign` entry whose `who` is not a
    delegate; a `dv_owner` entry that is not the dvbe_owner; a rep-signed-line
    entry whose delegate is not the named signer.
    """
    domain, delegates = load_delegation(profile_path)
    signer = spec.get("signer") or {}
    name = " ".join(str(signer.get("name", "")).split())
    email = str(signer.get("email", "")).strip().lower()
    if not name and not email:
        raise SignatureMissing("[MISSING — NEEDS INPUT] `signer`: the rep names who signs "
                               "the rep-signed lines (CalRecycle 74, Darfur, OBS 4007(B) "
                               "bidder); there is no default. Nothing was written.")
    if not email:
        raise SignatureMissing(f"[MISSING — NEEDS INPUT] signer email for {name}: it is how "
                               f"the signer is confirmed as a BBS employee. Nothing was written.")
    if email.count("@") != 1 or email.split("@")[1] != domain:
        raise SignatureMissing(f"REFUSED: the signer must be a BBS employee (an @{domain} "
                               f"address); {name or '(no name)'} <{email}> is not. "
                               f"Customers, agencies and third parties never sign BBS's "
                               f"lines. Nothing was written.")
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
        for field, who, sig in _sign_entries(form, []):
            where = f"{form.get('src', '?')} field {field!r}"
            d = _delegate_for(who, delegates)
            if d is None:
                problems.append(f"REFUSED: `who` {who!r} ({where}) is not a signature "
                                f"delegate; only delegates' signatures are applied")
            elif sig.get("line") == DV_OWNER_LINE:
                if d["role"] != "dvbe_owner":
                    problems.append(f"REFUSED: {where} is marked a DV-owner line, which only "
                                    f"the dvbe_owner signs, not {d['name']}")
            elif d is not signer_delegate:
                problems.append(f"REFUSED: {d['name']}'s signature on {where}, but the signer "
                                f"the rep named is {name} <{email}>"
                                + (f" — {why}" if why else "")
                                + ". A delegate's signature is never applied to someone "
                                  "else's line: leave it blank for a hand signature and flag "
                                  "⚑ SIGNATURE REQUIRED")
    if problems:
        raise SignatureMissing("\n".join(dict.fromkeys(problems)) + "\nNothing was written.")
    return signer_delegate


def preflight(spec):
    """Everything that can be checked without opening a PDF. Returns resolved sig paths."""
    forms = spec["forms"]
    check_signer(spec)
    sigs = check_signatures(forms, spec.get("signatures", {}), spec.get("master_root"))
    check_sources(forms, spec["src_dir"])
    return sigs


def _stamp(page, rect, img_path, dx, dy, max_h=22):
    px = fitz.Pixmap(img_path)
    h = min(rect.height * 1.6, max_h)
    w = min(h * px.width / px.height, rect.width)
    h = w * px.height / px.width
    box = fitz.Rect(rect.x0 + dx, rect.y1 - h + dy, rect.x0 + dx + w, rect.y1 + dy)
    page.insert_image(box, filename=img_path, overlay=True)


def fill_form(spec, sig_paths, src_dir, out_dir, master_root=None):
    """Fill one form into out_dir. Returns (out_path, [unapplied sign messages])."""
    sig_paths = check_signatures([spec], sig_paths, master_root)
    doc = fitz.open(os.path.join(src_dir, spec["src"]))
    text = spec.get("text", {})
    checks = spec.get("checks", {})
    sizes = spec.get("fontsize", {})

    for page in doc:
        for w in (page.widgets() or []):
            name = w.field_name
            if name in text:
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
    return out, unapplied


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    src_dir, out_dir = spec["src_dir"], spec["out_dir"]
    try:
        sigs = preflight(spec)
    except SignatureMissing as e:
        sys.exit(f"STOP: {e}")
    if fitz is None:
        sys.exit("pymupdf required: python -m pip install pymupdf "
                 "(Mac: python3 -m pip install --user pymupdf, or use a venv)")

    staging = tempfile.mkdtemp(prefix="fill_ca_forms-")
    try:
        unapplied = []
        for form in spec["forms"]:
            _out, missed = fill_form(form, sigs, src_dir, staging)
            unapplied += missed
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
    print("\nNow render every page and look at it — these fields clip silently.")


if __name__ == "__main__":
    main()
