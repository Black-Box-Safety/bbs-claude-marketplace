#!/usr/bin/env python3
"""The working workbook for one RFQ: one row per line, with what was asked for, what is
offered, where the cost came from, the sell price and how it was set.

  create  write a new workbook (refuses to overwrite one that exists)
  set     set named fields on one line of a workbook THIS SCRIPT made (adds the line if new);
          any other spreadsheet is refused and left unchanged
  show    print the lines as JSON, with the extended and margin figures computed here

The workbook is INTERNAL. It holds cost and margin and is never sent to a customer.

Computed columns (extended cost, extended price, margin) are Excel formulas so a rep can edit
a cost or a price and see the result. A workbook written by a script carries no cached
formula results, so `show` never reads those cells: it recomputes from quantity, cost and
price. Needs openpyxl. Exit 0 on success, 2 on a refused request, 1 on an unexpected error.
"""
import argparse
import json
import os
import sys

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.stderr.write("rfq_workbook: openpyxl is not installed. Rerun the BBS setup script.\n")
    sys.exit(2)

# key, column header, width, kind ("in" = typed, "calc" = formula)
COLUMNS = [
    ("line", "Ln", 5, "in"),
    ("qty", "Qty", 7, "in"),
    ("uom", "UOM", 7, "in"),
    ("requested", "Requested item (buyer's words)", 38, "in"),
    ("requested_mfr", "Requested mfr", 18, "in"),
    ("requested_pn", "Requested part no.", 18, "in"),
    ("match", "Match (Exact / Equal / Substitute / No bid)", 16, "in"),
    ("mfr", "Offered mfr", 18, "in"),
    ("sku", "Offered SKU / part no.", 20, "in"),
    ("source", "Source (supplier)", 20, "in"),
    ("source_ref", "Cost source (account + read date, vendor quote no. + date, or URL + date)", 36, "in"),
    ("cost_date", "Cost date", 12, "in"),
    ("cost", "Unit cost", 12, "in"),
    ("ext_cost", "Ext cost", 13, "calc"),
    ("alt_source", "Alternative source", 20, "in"),
    ("alt_cost", "Alt unit cost", 12, "in"),
    ("alt_ref", "Alt source ref", 28, "in"),
    ("price", "Unit price", 12, "in"),
    ("ext_price", "Ext price", 13, "calc"),
    ("margin", "Margin $", 12, "calc"),
    ("margin_pct", "Margin %", 10, "calc"),
    ("pricing_notes", "Pricing notes (how the sell price was set)", 44, "in"),
    ("lead_time", "Lead time", 14, "in"),
    ("origin", "Country of origin (documented only)", 18, "in"),
    ("status", "Line status", 14, "in"),
    ("notes", "Notes", 36, "in"),
]
KEYS = [c[0] for c in COLUMNS]
INPUT_KEYS = [c[0] for c in COLUMNS if c[3] == "in"]
COL = {k: i + 1 for i, k in enumerate(KEYS)}
NUMERIC = {"qty", "cost", "alt_cost", "price"}
MATCHES = ("Exact", "Equal", "Substitute", "No bid")
FORMULA_ROWS = 200
HEADER_FIELDS = [
    "Customer", "Buyer", "Request / solicitation no.", "Channel", "Vehicle or contract",
    "Received", "Due (date, time, zone)", "Ship to", "Grainger account", "Rep",
    "Business Central quote no. (read from BC)", "Deal folder",
    "Margin basis (the band or rule used, and where it came from)",
    "Outcome (won, lost, no answer, no bid, cancelled)",
    "Why, and what to do differently next time",
]
SUPPLIER_HEADERS = ["Supplier", "Contact", "Lines covered", "Asked (date)", "Replied (date)",
                    "Quote no.", "Quote expires", "Terms", "Freight", "Notes"]
COMP_HEADERS = ["Ln", "Item compared", "Seller", "Unit price", "Price UOM",
                "Source (URL, or SCPRS PO no. + date)", "Date read", "Same item? (Exact / Close)",
                "Caveat"]
BANNER = "INTERNAL WORKING FILE. Holds cost and margin. Never send to a customer."


class Refused(Exception):
    pass


def _letter(key):
    return get_column_letter(COL[key])


def _formulas(row):
    q, c, p = "%s%d" % (_letter("qty"), row), "%s%d" % (_letter("cost"), row), "%s%d" % (_letter("price"), row)
    ec, ep = "%s%d" % (_letter("ext_cost"), row), "%s%d" % (_letter("ext_price"), row)
    m = "%s%d" % (_letter("margin"), row)
    return {
        "ext_cost": '=IF(OR(%s="",%s=""),"",%s*%s)' % (q, c, q, c),
        "ext_price": '=IF(OR(%s="",%s=""),"",%s*%s)' % (q, p, q, p),
        "margin": '=IF(OR(%s="",%s=""),"",%s-%s)' % (ec, ep, ep, ec),
        "margin_pct": '=IF(OR(%s="",%s="",%s=0),"",%s/%s)' % (m, ep, ep, m, ep),
    }


def _coerce(key, value):
    if value is None or value == "":
        return None
    if key in NUMERIC or key == "line":
        try:
            n = float(value)
        except (TypeError, ValueError):
            raise Refused("%s must be a number, got %r" % (key, value))
        if n < 0:
            raise Refused("%s cannot be negative" % key)
        if key == "line" and (n < 1 or n != int(n)):
            raise Refused("line must be a whole number, 1 or more, got %r" % value)
        return int(n) if key == "line" or (key == "qty" and n == int(n)) else n
    if key == "match" and value not in MATCHES:
        raise Refused("match must be one of: %s" % ", ".join(MATCHES))
    return str(value)


def _check_line(fields):
    unknown = [k for k in fields if k not in INPUT_KEYS]
    if unknown:
        raise Refused("unknown or computed field(s): %s. Fields: %s"
                      % (", ".join(sorted(unknown)), ", ".join(INPUT_KEYS)))
    return {k: _coerce(k, v) for k, v in fields.items()}


# A number is only as good as what it rests on: (the number, what must accompany it, the words)
PAIRS = (
    ("cost", "source_ref", "a cost needs its source (source_ref)"),
    ("alt_cost", "alt_ref", "an alternative cost needs its source (alt_ref)"),
    ("price", "pricing_notes", "a price needs a pricing note saying how it was set (pricing_notes)"),
)


def _require_pairs(line, values):
    """values is the COMPLETE line as it will be written. Refuse a number without its basis."""
    for num_key, basis_key, words in PAIRS:
        if values.get(num_key) not in (None, "") and not str(values.get(basis_key) or "").strip():
            raise Refused("line %s: %s" % (line, words))


def _require_xlsx(path):
    if not str(path).lower().endswith(".xlsx"):
        raise Refused("the workbook must be an .xlsx file, got %r" % os.path.basename(str(path)))


def _require_ours(wb, path):
    """Only a workbook this script made is ever rewritten: the banner and the exact headers."""
    ok = ("RFQ" in wb.sheetnames and "Lines" in wb.sheetnames
          and wb["RFQ"]["A1"].value == BANNER
          and all(wb["Lines"].cell(row=1, column=COL[k]).value == title for k, title, _w, _kind in COLUMNS))
    if not ok:
        raise Refused("%s was not made by this script (banner or Lines headers differ); "
                      "it is not changed. Use `create` for a new workbook." % path)


def _write_line(ws, row, fields):
    for k, v in fields.items():
        ws.cell(row=row, column=COL[k], value=v)


def _line_rows(ws):
    rows = {}
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=COL["line"]).value
        if v not in (None, ""):
            try:
                rows[int(v)] = r
            except (TypeError, ValueError):
                continue
    return rows


def _style_header(ws, ncols):
    fill = PatternFill("solid", fgColor="1F2937")
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"


def create(out, header, lines):
    _require_xlsx(out)
    if os.path.exists(out):
        raise Refused("%s already exists. It is edited in place; use `set` to change a line." % out)
    folder = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(folder):
        raise Refused("folder does not exist: %s" % folder)
    checked = [_check_line(dict(l)) for l in lines]
    seen = set()
    for i, l in enumerate(checked, 1):
        l.setdefault("line", i)
        if l["line"] in seen:
            raise Refused("line %s appears twice" % l["line"])
        seen.add(l["line"])
        _require_pairs(l["line"], l)

    wb = Workbook()
    info = wb.active
    info.title = "RFQ"
    info["A1"] = BANNER
    info["A1"].font = Font(bold=True, color="B91C1C")
    for i, name in enumerate(HEADER_FIELDS, 3):
        info.cell(row=i, column=1, value=name).font = Font(bold=True)
        info.cell(row=i, column=2, value=header.get(name))
    base = 3 + len(HEADER_FIELDS) + 1
    info.cell(row=base, column=1, value="Open questions for the buyer").font = Font(bold=True)
    log = base + 7
    info.cell(row=log, column=1, value="Activity log (newest at bottom)").font = Font(bold=True)
    for c, h in enumerate(["Date", "Who", "What happened", "Result", "Ref (file, quote no., email)"], 1):
        info.cell(row=log + 1, column=c, value=h).font = Font(bold=True)
    info.column_dimensions["A"].width = 40
    info.column_dimensions["B"].width = 50
    for col in "CDE":
        info.column_dimensions[col].width = 28

    ws = wb.create_sheet("Lines")
    for k, title, width, _kind in COLUMNS:
        ws.cell(row=1, column=COL[k], value=title)
        ws.column_dimensions[_letter(k)].width = width
    _style_header(ws, len(COLUMNS))
    ws.row_dimensions[1].height = 45
    calc_fill = PatternFill("solid", fgColor="F3F4F6")
    for r in range(2, FORMULA_ROWS + 2):
        for k, f in _formulas(r).items():
            cell = ws.cell(row=r, column=COL[k], value=f)
            cell.fill = calc_fill
        for k in ("cost", "ext_cost", "alt_cost", "price", "ext_price", "margin"):
            ws.cell(row=r, column=COL[k]).number_format = '"$"#,##0.00'
        ws.cell(row=r, column=COL["margin_pct"]).number_format = "0.0%"
    for i, l in enumerate(sorted(checked, key=lambda d: d["line"])):
        _write_line(ws, 2 + i, l)

    for title, headers in (("Suppliers", SUPPLIER_HEADERS), ("Comps", COMP_HEADERS)):
        s = wb.create_sheet(title)
        for c, h in enumerate(headers, 1):
            s.cell(row=1, column=c, value=h)
            s.column_dimensions[get_column_letter(c)].width = 22
        _style_header(s, len(headers))
    wb.save(out)
    return len(checked)


def set_line(path, line, fields):
    _require_xlsx(path)
    if line < 1:
        raise Refused("line must be 1 or more, got %s" % line)
    if not os.path.isfile(path):
        raise Refused("no workbook at %s. Use `create` first." % path)
    if not fields:
        raise Refused("nothing to set")
    checked = _check_line(dict(fields))
    checked.pop("line", None)
    wb = load_workbook(path)
    _require_ours(wb, path)
    ws = wb["Lines"]
    rows = _line_rows(ws)
    if line in rows:
        row, added = rows[line], False
    else:
        row = (max(rows.values()) + 1) if rows else 2
        if row > FORMULA_ROWS + 1:
            raise Refused("more than %d lines; split the request" % FORMULA_ROWS)
        ws.cell(row=row, column=COL["line"], value=line)
        added = True
    merged = {k: ws.cell(row=row, column=COL[k]).value for k in INPUT_KEYS}
    merged.update(checked)
    _require_pairs(line, merged)
    _write_line(ws, row, checked)
    try:
        wb.save(path)
    except PermissionError:
        raise Refused("%s is open in Excel or locked by OneDrive. Close it and run this again." % path)
    return added


def show(path):
    _require_xlsx(path)
    if not os.path.isfile(path):
        raise Refused("no workbook at %s" % path)
    wb = load_workbook(path)
    _require_ours(wb, path)
    ws = wb["Lines"]
    out = []
    for line, row in sorted(_line_rows(ws).items()):
        rec = {k: ws.cell(row=row, column=COL[k]).value for k in INPUT_KEYS}
        qty, cost, price = rec.get("qty"), rec.get("cost"), rec.get("price")
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        rec["ext_cost"] = round(qty * cost, 2) if num(qty) and num(cost) else None
        rec["ext_price"] = round(qty * price, 2) if num(qty) and num(price) else None
        if rec["ext_cost"] is not None and rec["ext_price"] is not None:
            rec["margin"] = round(rec["ext_price"] - rec["ext_cost"], 2)
            rec["margin_pct"] = round(rec["margin"] / rec["ext_price"], 4) if rec["ext_price"] else None
        else:
            rec["margin"] = rec["margin_pct"] = None
        gaps = []
        if num(cost) and not rec.get("source_ref"):
            gaps.append("cost has no source")
        if num(rec.get("alt_cost")) and not rec.get("alt_ref"):
            gaps.append("alternative cost has no source")
        if num(price) and not rec.get("pricing_notes"):
            gaps.append("price has no pricing note")
        if not num(price) and rec.get("match") != "No bid":
            gaps.append("not priced")
        rec["gaps"] = gaps
        out.append(rec)
    totals = {
        "lines": len(out),
        "ext_cost": round(sum(r["ext_cost"] or 0 for r in out), 2),
        "ext_price": round(sum(r["ext_price"] or 0 for r in out), 2),
        "lines_with_gaps": sum(1 for r in out if r["gaps"]),
    }
    return {"file": path, "totals": totals, "lines": out}


def _pairs(items):
    fields = {}
    for it in items or []:
        if "=" not in it:
            raise Refused("expected key=value, got %r" % it)
        k, v = it.split("=", 1)
        fields[k.strip()] = v
    return fields


def main(argv=None):
    ap = argparse.ArgumentParser(description="The working workbook for one RFQ (internal).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--out", required=True)
    c.add_argument("--lines-json", help="file holding a JSON list of line objects")
    c.add_argument("--header", action="append", help='"Field=value", repeatable; fields: ' + "; ".join(HEADER_FIELDS))
    s = sub.add_parser("set")
    s.add_argument("--file", required=True)
    s.add_argument("--line", required=True, type=int)
    s.add_argument("--field", action="append", help="key=value, repeatable; keys: " + ", ".join(INPUT_KEYS))
    w = sub.add_parser("show")
    w.add_argument("--file", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "create":
            header = _pairs(a.header)
            bad = [k for k in header if k not in HEADER_FIELDS]
            if bad:
                raise Refused("unknown header field(s): %s" % ", ".join(bad))
            lines = []
            if a.lines_json:
                with open(a.lines_json, "rb") as fh:
                    lines = json.loads(fh.read().decode("utf-8-sig"))
                if not isinstance(lines, list):
                    raise Refused("--lines-json must hold a JSON list")
            n = create(a.out, header, lines)
            print("created %s with %d line(s)" % (a.out, n))
        elif a.cmd == "set":
            added = set_line(a.file, a.line, _pairs(a.field))
            print("%s line %d in %s" % ("added" if added else "updated", a.line, a.file))
        else:
            print(json.dumps(show(a.file), indent=1, default=str))
    except Refused as e:
        sys.stderr.write("rfq_workbook: REFUSED - %s\nNothing was written.\n" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
