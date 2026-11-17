#!/usr/bin/env python3
"""Offline checks for bc_quote_pdf.py: no network, no Business Central, no sign-in.

    python3 test_bc_quote_pdf.py

Mirrors test_bc_quote_entry.py. The rules the docstring names in words are held here: the release
gate, the file name, GET only, and the reuse of the sibling's connection. BC is a fake with the
three reads the script uses.
"""
import argparse
import ast
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc_quote_pdf as m  # noqa: E402

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bc_quote_pdf.py")
QID = "11111111-2222-3333-4444-555555555555"
PDF = b"%PDF-1.7\n" + b"x" * 5000


def slurp(path):
    with open(path, "rb") as fh:
        return fh.read()


def quote(**over):
    base = {"id": QID, "number": "SQ-105183", "status": "Sent", "customerNumber": "C00000",
            "customerName": "Example Agency, Training Center", "externalDocumentNumber": "RFQ EX-6001",
            "totalAmountExcludingTax": 2865.0, "totalTaxAmount": 222.04, "totalAmountIncludingTax": 3087.04}
    base.update(over)
    return base


class FakeBC:
    """What cmd_fetch uses from ReadOnlyBC. Records every URL it was asked for."""
    q = quote()
    doc_status, doc_body = 200, {"id": "d", "parentId": QID, "parentType": "Sales Quote"}
    content_status, content, ctype = 200, PDF, "application/pdf"
    urls = []
    api = "https://api.example/v2.0/companies(c)"

    def __init__(self, account=None):
        FakeBC.urls = []

    def quote_by_number(self, sq):
        FakeBC.urls.append(("lookup", sq))
        return FakeBC.q

    def get(self, url):
        FakeBC.urls.append(("get", url))
        return FakeBC.doc_status, FakeBC.doc_body

    def get_bytes(self, url):
        FakeBC.urls.append(("bytes", url))
        return FakeBC.content_status, FakeBC.content, FakeBC.ctype


def run_fetch(folder, number="SQ-105183", confirmed=None, institution=None, **fake):
    for k, v in fake.items():
        setattr(FakeBC, k, v)
    args = argparse.Namespace(number=number, out=folder, institution=institution,
                              released_confirmed_by=confirmed, account=None)
    out = io.StringIO()
    code = None
    with mock.patch.object(m, "ReadOnlyBC", FakeBC), contextlib.redirect_stdout(out):
        try:
            m.cmd_fetch(args)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue()


class Names(unittest.TestCase):
    def test_normalize(self):
        for t in ("SQ-105183", "sq-105183", "SQ 105183", "SQ105183", " 105183 "):
            self.assertEqual(m.normalize_sq(t), "SQ-105183")
        for t in ("", "SQ-", "SQ-12", "SO-105183", "105183; rm", "SQ-105183/../x", None):
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stdout(io.StringIO()):
                    m.normalize_sq(t)

    def test_file_name(self):
        with tempfile.TemporaryDirectory() as d:
            p = m.target_path(d, "Example Agency, Training Center", "SQ-105183")
            self.assertEqual(os.path.basename(p), "Example_Agency_Training_Center_Quote_SQ-105183.pdf")
            self.assertEqual(os.path.dirname(p), d)
            self.assertEqual(os.path.basename(m.target_path(d, "CDCR/../x", "SQ-1000")), "CDCR_x_Quote_SQ-1000.pdf")

    def test_folder_must_exist_and_is_never_created(self):
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "Califonria Women's Facility (123)")
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
                m.target_path(missing, "X", "SQ-1000")
            self.assertFalse(os.path.exists(missing))

    def test_no_institution_stops(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
                m.target_path(d, "  ,, ", "SQ-1000")


class ReleaseGate(unittest.TestCase):
    def test_sent_and_accepted_pass(self):
        for s in ("Sent", "Accepted"):
            self.assertTrue(m.release_gate(quote(status=s))[0])

    def test_draft_refused_and_says_why(self):
        ok, notes = m.release_gate(quote(status="Draft"))
        self.assertFalse(ok)
        self.assertIn("no tax", " ".join(notes))
        self.assertIn("--released-confirmed-by", " ".join(notes))

    def test_draft_passes_only_on_a_named_rep(self):
        self.assertTrue(m.release_gate(quote(status="Draft"), "Parker Marshall")[0])
        for blank in ("", "   ", None):
            self.assertFalse(m.release_gate(quote(status="Draft"), blank)[0])

    def test_expired_and_unknown_refused_even_with_a_name(self):
        self.assertFalse(m.release_gate(quote(status="Expired"), "Parker")[0])
        self.assertFalse(m.release_gate(quote(status="Wobbly"), "Parker")[0])
        self.assertFalse(m.release_gate(quote(status=None), "Parker")[0])


class Fetch(unittest.TestCase):
    def setUp(self):
        FakeBC.q, FakeBC.doc_status = quote(), 200
        FakeBC.doc_body = {"id": "d", "parentId": QID, "parentType": "Sales Quote"}
        FakeBC.content_status, FakeBC.content, FakeBC.ctype = 200, PDF, "application/pdf"

    def test_saves_the_pdf_and_prints_path_and_size(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            path = os.path.join(d, "Example_Agency_Training_Center_Quote_SQ-105183.pdf")
            self.assertIsNone(code, out)
            self.assertEqual(slurp(path), PDF)
            self.assertIn(f"[saved] {path} ({len(PDF)} bytes)", out)
            self.assertIn("DVBE 2009473 only", out)
            self.assertIn("A person sends", out)
            self.assertEqual(os.listdir(d), [os.path.basename(path)])

    def test_uses_exactly_the_documented_navigation(self):
        with tempfile.TemporaryDirectory() as d:
            run_fetch(d)
        urls = [u for kind, u in FakeBC.urls if kind != "lookup"]
        self.assertEqual(urls, [f"{FakeBC.api}/salesQuotes({QID})/pdfDocument",
                                f"{FakeBC.api}/salesQuotes({QID})/pdfDocument/pdfDocumentContent"])

    def test_institution_flag_overrides_the_customer_name(self):
        with tempfile.TemporaryDirectory() as d:
            code, _ = run_fetch(d, institution="CMC")
            self.assertIsNone(code)
            self.assertEqual(os.listdir(d), ["CMC_Quote_SQ-105183.pdf"])

    def test_draft_writes_nothing_and_never_asks_for_the_pdf(self):
        FakeBC.q = quote(status="Draft")
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("no tax", out)
            self.assertEqual(os.listdir(d), [])
        self.assertFalse([k for k, _ in FakeBC.urls if k == "bytes"])

    def test_draft_with_a_named_rep_is_fetched(self):
        FakeBC.q = quote(status="Draft")
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d, confirmed="Parker Marshall")
            self.assertIsNone(code, out)
            self.assertIn("Parker Marshall", out)

    def test_zero_tax_is_flagged(self):
        FakeBC.q = quote(totalTaxAmount=0)
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertIsNone(code)
            self.assertIn("FLAG: BC shows no tax", out)

    def test_unknown_quote_stops(self):
        FakeBC.q = None
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("no sales quote SQ-105183", out)

    def test_pdfdocument_missing_stops_without_another_path(self):
        FakeBC.doc_status, FakeBC.doc_body = 404, {"error": {"code": "BadRequest_NotFound"}}
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("No other path is tried", out)
            self.assertEqual(os.listdir(d), [])
        self.assertEqual(len([1 for k, _ in FakeBC.urls if k != "lookup"]), 1)

    def test_pdfdocument_for_another_parent_refused(self):
        FakeBC.doc_body = {"id": "d", "parentId": "99999999-0000-0000-0000-000000000000"}
        with tempfile.TemporaryDirectory() as d:
            code, _ = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertEqual(os.listdir(d), [])

    def test_not_a_pdf_is_not_saved(self):
        FakeBC.content, FakeBC.ctype = b'{"error": "x"}', "application/json"
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("not a PDF", out)
            self.assertEqual(os.listdir(d), [])

    def test_content_error_status_stops(self):
        FakeBC.content_status, FakeBC.content = 500, b"boom"
        with tempfile.TemporaryDirectory() as d:
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("HTTP 500", out)
            self.assertEqual(os.listdir(d), [])

    def test_existing_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "Example_Agency_Training_Center_Quote_SQ-105183.pdf")
            with open(path, "wb") as fh:
                fh.write(b"mine")
            code, out = run_fetch(d)
            self.assertEqual(code, 1)
            self.assertIn("not overwritten", out)
            self.assertEqual(slurp(path), b"mine")


class GetOnly(unittest.TestCase):
    """No write to Business Central is possible from this file, and the tests hold that."""
    FORBIDDEN_METHODS = {"POST", "PATCH", "PUT", "DELETE", "MERGE"}

    def tree(self):
        with open(SRC, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_no_write_verb_anywhere_in_the_code(self):
        for node in ast.walk(self.tree()):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotIn(node.value.strip().upper(), self.FORBIDDEN_METHODS, node.value)

    def test_no_write_call_anywhere(self):
        calls = set()
        for node in ast.walk(self.tree()):
            if isinstance(node, ast.Call):
                f = node.func
                calls.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
        for name in ("post", "patch", "put", "delete", "http"):
            self.assertNotIn(name, calls)

    def test_every_request_is_built_as_get(self):
        found = []
        for node in ast.walk(self.tree()):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "Request":
                kws = {k.arg: k.value for k in node.keywords}
                self.assertIn("method", kws)
                self.assertEqual(ast.literal_eval(kws["method"]), "GET")
                self.assertNotIn("data", kws)
                found.append(node)
        self.assertEqual(len(found), 1)

    def test_sibling_write_helpers_are_switched_off(self):
        with self.assertRaises(RuntimeError):
            m.ReadOnlyBC.post(None, "https://x", {})
        with self.assertRaises(RuntimeError):
            m.ReadOnlyBC.patch(None, "https://x", "etag", {})

    def test_the_only_file_opened_for_writing_is_the_pdf(self):
        modes = []
        for node in ast.walk(self.tree()):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "open":
                modes.append(ast.literal_eval(node.args[1]))
        self.assertEqual(modes, ["xb"])


class Reuse(unittest.TestCase):
    def test_imports_the_sibling(self):
        self.assertTrue(m.item.CONNECTION_FILE.replace("\\", "/").endswith("bc-item-entry/references/bc-connection.json"))
        self.assertTrue(issubclass(m.ReadOnlyBC, m.item.BC))
        self.assertIs(m.explain_error, m.item.explain_error)
        self.assertIs(m.http_fail, m.item.http_fail)

    def test_no_connection_file_or_secret_of_its_own(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(m.__file__)))
        self.assertFalse(os.path.exists(os.path.join(here, "references", "bc-connection.json")))
        with open(SRC, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("BC_CLIENT_SECRET", text)
        self.assertNotIn("token_app_only", text)

    def test_app_only_is_refused_before_any_sign_in(self):
        with mock.patch.dict(os.environ, {"BBS_BC_AUTH": "app-only"}):
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
                m.ReadOnlyBC()


if __name__ == "__main__":
    unittest.main(verbosity=1)
