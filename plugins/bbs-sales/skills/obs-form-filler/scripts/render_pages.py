#!/usr/bin/env python3
"""Render packet pages to PNGs so the rep can eyeball the fill before sending.

Usage:
    python render_pages.py <packet.pdf> <out_dir> [page ...]

Pages are 1-based; with none given, every page is rendered. Kept here rather
than relying on /mnt/skills/public/pdf so the check works wherever the plugin
is installed.
"""

import os
import sys


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip())
        sys.exit(1)
    pdf_path, out_dir = sys.argv[1], sys.argv[2]
    wanted = [int(a) for a in sys.argv[3:]]

    try:
        import fitz
    except ImportError:
        sys.exit("pymupdf is required: pip install pymupdf")

    doc = fitz.open(pdf_path)
    pages = wanted or list(range(1, doc.page_count + 1))
    for page_no in pages:
        if not 1 <= page_no <= doc.page_count:
            sys.exit(f"page {page_no} is out of range (1-{doc.page_count})")
    os.makedirs(out_dir, exist_ok=True)
    for page_no in pages:
        out = os.path.join(out_dir, f"page-{page_no:02d}.png")
        doc[page_no - 1].get_pixmap(dpi=150).save(out)
        print(out)
    doc.close()


if __name__ == "__main__":
    main()
