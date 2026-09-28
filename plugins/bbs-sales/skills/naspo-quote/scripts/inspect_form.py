#!/usr/bin/env python3
"""
inspect_form.py — dump every AcroForm field in a PDF with its type, position,
export states, and the printed text immediately to its left.

Field names on state forms rarely match the visible caption ("Text1" is the DVBE
certification line; "Check Box8" is the N/A box). The left-hand text snippet is
what lets you map a name to what a human sees, without opening the PDF.

Usage:
    python inspect_form.py <form.pdf>            # all fields
    python inspect_form.py <form.pdf> --render   # also write page PNGs alongside

Requires: pymupdf
"""
import os
import sys

try:
    import fitz
except ImportError:
    sys.exit("pymupdf required: python -m pip install pymupdf (Mac: python3 -m pip install --user pymupdf, or use a venv)")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    doc = fitz.open(path)
    for pno, page in enumerate(doc, start=1):
        for w in (page.widgets() or []):
            r = w.rect
            band = fitz.Rect(max(0, r.x0 - 240), r.y0 - 5, max(1, r.x0 - 1), r.y1 + 5)
            label = page.get_text("text", clip=band).replace("\n", " ").strip()[-60:]
            states = w.button_states() or ""
            print(f"p{pno} {w.field_name!r:44s} {w.field_type_string:12s} "
                  f"({r.x0:5.0f},{r.y0:5.0f},{r.x1:5.0f},{r.y1:5.0f}) {states} <<{label}>>")
    if "--render" in sys.argv:
        stem = os.path.splitext(path)[0]
        for pno, page in enumerate(doc, start=1):
            out = f"{stem}_p{pno}.png"
            page.get_pixmap(dpi=110).save(out)
            print("rendered", out)


if __name__ == "__main__":
    main()
