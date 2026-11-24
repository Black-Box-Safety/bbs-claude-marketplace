"""Tests for rfq_workbook.py. Run: python3 -m pytest plugins/bbs-sales/skills/rfq-workbook/scripts"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rfq_workbook as w  # noqa: E402

LINES = [
    {"qty": 12, "uom": "EA", "requested": "Hard hat, white", "match": "Exact", "mfr": "MSA",
     "sku": "475358", "source": "Grainger", "source_ref": "acct on file, read 2026-11-24",
     "cost": 10.5, "price": 10.5, "pricing_notes": "NASPO at cost"},
    {"qty": 3, "uom": "CS", "requested": "Nitrile gloves L"},
]


def test_create_show_and_totals(tmp_path):
    out = str(tmp_path / "WORKING.xlsx")
    assert w.create(out, {"Customer": "Test agency"}, LINES) == 2
    data = w.show(out)
    assert data["totals"] == {"lines": 2, "ext_cost": 126.0, "ext_price": 126.0, "lines_with_gaps": 1}
    assert data["lines"][0]["margin"] == 0.0
    assert data["lines"][1]["gaps"] == ["not priced"]


def test_create_refuses_to_overwrite(tmp_path):
    out = str(tmp_path / "WORKING.xlsx")
    w.create(out, {}, [])
    with pytest.raises(w.Refused):
        w.create(out, {}, [])


def test_cost_needs_source_and_price_needs_note(tmp_path):
    out = str(tmp_path / "WORKING.xlsx")
    w.create(out, {}, LINES)
    with pytest.raises(w.Refused):
        w.set_line(out, 2, {"cost": "4.25"})
    w.set_line(out, 2, {"cost": "4.25", "source_ref": "vendor quote Q-1, 2026-11-24"})
    with pytest.raises(w.Refused):
        w.set_line(out, 2, {"price": "5.00"})
    w.set_line(out, 2, {"price": "5.00", "pricing_notes": "cost plus 15%, matched last order"})
    line2 = w.show(out)["lines"][1]
    assert line2["ext_cost"] == 12.75 and line2["ext_price"] == 15.0 and line2["gaps"] == []


def test_set_adds_a_new_line_and_rejects_bad_fields(tmp_path):
    out = str(tmp_path / "WORKING.xlsx")
    w.create(out, {}, LINES)
    assert w.set_line(out, 3, {"requested": "Safety glasses", "qty": "40"}) is True
    assert len(w.show(out)["lines"]) == 3
    with pytest.raises(w.Refused):
        w.set_line(out, 3, {"margin": "5"})
    with pytest.raises(w.Refused):
        w.set_line(out, 3, {"match": "Close enough"})
    with pytest.raises(w.Refused):
        w.set_line(out, 3, {"cost": "-1", "source_ref": "x"})


def test_cli_roundtrip(tmp_path, capsys):
    out = str(tmp_path / "WORKING.xlsx")
    lines = tmp_path / "lines.json"
    lines.write_text(json.dumps(LINES), encoding="utf-8")
    assert w.main(["create", "--out", out, "--lines-json", str(lines), "--header", "Customer=Test"]) == 0
    assert w.main(["create", "--out", out]) == 2
    assert w.main(["show", "--file", out]) == 0
    assert '"lines": 2' in capsys.readouterr().out
