#!/usr/bin/env python3
"""test_check_items.py — the BPO list constants are checked, not believed.

Run it:
    python3 test_check_items.py

check_items.py names the bundled list's fiscal year in BPO_LIST_* constants
typed by hand. These tests show that a list swapped without its constants (or
the reverse) stops the run with exit 1 rather than answering under the wrong
year. Stdlib only, no pytest.
"""
import io
import os
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_items as ci  # noqa: E402

REAL = {k: getattr(ci, k) for k in
        ("BPO_LIST_FY", "BPO_LIST_SOURCE", "BPO_LIST_VALID_FROM", "BPO_LIST_VALID_TO")}


def _with(**over):
    for k, v in over.items():
        setattr(ci, k, v)


def _restore():
    _with(**REAL)


def _run_main():
    """Run main() on one item; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    argv = sys.argv
    sys.argv = ["check_items.py", "102WZ8"]
    code = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            ci.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = argv
    return code, out.getvalue(), err.getvalue()


def test_bundled_constants_agree_with_the_bundled_files():
    assert ci.constants_problem() is None, ci.constants_problem()
    code, out, _ = _run_main()
    assert code == 0 and out.startswith("Checked against: DGS BPO item list"), (code, out)


def test_missing_source_file_exits_1():
    _with(BPO_LIST_FY="FY26-27", BPO_LIST_SOURCE="Final_BPO_Item_List_26-27.xlsx",
          BPO_LIST_VALID_FROM=date(2026, 7, 1), BPO_LIST_VALID_TO=date(2027, 6, 30))
    try:
        assert "not in assets/" in ci.constants_problem()
        code, out, err = _run_main()
        assert code == 1 and out == "" and "no answer given" in err, (code, out, err)
    finally:
        _restore()


def test_source_without_the_fy_token_exits_1():
    _with(BPO_LIST_FY="FY26-27", BPO_LIST_VALID_FROM=date(2026, 7, 1),
          BPO_LIST_VALID_TO=date(2027, 6, 30))  # source still names 25-26
    try:
        assert "fiscal-year token 26-27" in ci.constants_problem()
        assert _run_main()[0] == 1
    finally:
        _restore()


def test_dates_not_matching_the_fy_exit_1():
    _with(BPO_LIST_VALID_TO=date(2027, 6, 30))
    try:
        assert "not the California fiscal year" in ci.constants_problem()
        assert _run_main()[0] == 1
    finally:
        _restore()


def test_malformed_fy_exits_1():
    _with(BPO_LIST_FY="2025-2026")
    try:
        assert "not of the form" in ci.constants_problem()
        assert _run_main()[0] == 1
    finally:
        _restore()


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
        except Exception:
            failed.append(name)
            print("FAIL %s" % name)
            traceback.print_exc()
        else:
            print("ok   %s" % name)
    print("\n%d/%d passed" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
