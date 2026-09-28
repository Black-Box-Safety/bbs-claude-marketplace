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
  "signatures": { "parker": "/abs/path/parker-signature.png",
                  "jackson": "/abs/path/JACKSON_SIG.png" },
  "forms": [
    {
      "src": "CalRecycle- Form 74 (01-2023).pdf",
      "out": "BBS_CalRecycle74_AGENCY_20260827.pdf",
      "text":   { "State Agency": "CDCR - CMC" },
      "checks": { "Check Box3": true },
      "radios": { "YNagent": {"index": 0, "on": "1"} },
      "sign":   { "Signature": {"who": "parker", "dx": 2, "dy": 0} },
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

* missing signature images stop the run — every `sign` entry in every form is
  checked by `check_signatures()` before any PDF is opened. A signer with no
  path in `signatures`, or a path with no file behind it, exits naming the
  signer and the path. Nothing is written, so no half-signed packet exists
  (AGENTS.md invariant 4). The fix is the path, or dropping that `sign` entry
  so the line is left unsigned for the rep.

Requires: pymupdf
"""
import json
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:  # checked in main(); check_signatures() needs no fitz
    fitz = None

TRUTHY = {True, "true", "yes", "on", "x", "1", "checked"}


class SignatureMissing(Exception):
    """A form asks for a signature whose image cannot be found."""


def check_signatures(forms, sig_paths):
    """Raise SignatureMissing unless every signer any form asks for has a real file.

    Runs before any PDF is opened. Before this check, a signer absent from
    `signatures` died with a bare KeyError, and a path with no file died inside
    fitz.Pixmap after the widget was already deleted — in both cases after the
    earlier forms of the packet had already been written, signed.
    """
    problems = []
    for form in forms:
        for field, sig in (form.get("sign") or {}).items():
            who = sig.get("who")
            path = (sig_paths or {}).get(who)
            where = f"{form.get('src', '?')} field {field!r}"
            if not path:
                problems.append(f"signature image for {who} not given in the spec's "
                                f"`signatures` ({where})")
            elif not os.path.isfile(path):
                problems.append(f"signature image for {who} not found at {path} ({where})")
    if problems:
        raise SignatureMissing(
            "\n".join(dict.fromkeys(problems))
            + "\nFix the path or leave the line unsigned for the rep "
              "(drop that `sign` entry). Nothing was written.")


def _stamp(page, rect, img_path, dx, dy, max_h=22):
    px = fitz.Pixmap(img_path)
    h = min(rect.height * 1.6, max_h)
    w = min(h * px.width / px.height, rect.width)
    h = w * px.height / px.width
    box = fitz.Rect(rect.x0 + dx, rect.y1 - h + dy, rect.x0 + dx + w, rect.y1 + dy)
    page.insert_image(box, filename=img_path, overlay=True)


def fill_form(spec, sig_paths, src_dir, out_dir):
    check_signatures([spec], sig_paths)
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

    for name, sig in (spec.get("sign") or {}).items():
        img = sig_paths[sig["who"]]
        for page in doc:
            for w in (page.widgets() or []):
                if w.field_name == name:
                    rect = w.rect
                    try:
                        page.delete_widget(w)
                    except Exception:
                        pass
                    _stamp(page, rect, img, sig.get("dx", 2), sig.get("dy", 0))

    out = os.path.join(out_dir, spec["out"])
    doc.save(out)
    doc.close()
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    src_dir, out_dir = spec["src_dir"], spec["out_dir"]
    sigs = spec.get("signatures", {})
    try:
        check_signatures(spec["forms"], sigs)
    except SignatureMissing as e:
        sys.exit(f"STOP: {e}")
    if fitz is None:
        sys.exit("pymupdf required: pip install pymupdf --break-system-packages -q")
    os.makedirs(out_dir, exist_ok=True)
    for form in spec["forms"]:
        print("wrote", fill_form(form, sigs, src_dir, out_dir))
    print("\nNow render every page and look at it — these fields clip silently.")


if __name__ == "__main__":
    main()
