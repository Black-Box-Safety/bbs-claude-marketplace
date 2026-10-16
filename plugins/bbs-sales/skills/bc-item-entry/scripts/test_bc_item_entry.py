#!/usr/bin/env python3
"""Offline checks for bc_item_entry.py: no network, no Business Central, no sign-in.

    python3 test_bc_item_entry.py

Covers the rules the docs name in words, so a wording change in SKILL.md or item-rules.md
that the script no longer enforces fails here instead of on a rep's batch.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc_item_entry as m  # noqa: E402

UOMS = {"EA", "PK10", "CS"}


def spec(**over):
    base = {"vendorNo": "V00000", "vendorName": "Example Vendor", "preparedBy": "Rep Name",
            "source": "Example Vendor quote Q-000001 2026-01-02",
            "items": [{"number": "EX-100", "displayName": "Example EX-100 Widget", "manufacturer": "Example",
                       "baseUoM": "EA", "costPer": "EA", "unitCost": 10.0, "unitPrice": 12.5,
                       "costSource": "Example Vendor quote Q-000001 2026-01-02"}]}
    base.update(over)
    return base


class CostSourceWords(unittest.TestCase):
    """SKILL.md: the script rejects "verbal", "roughly", "estimate" and the like; spec-schema.md adds
    approx and phone. The stems catch every suffix. A vendor called Usual is not a guess."""

    def test_words_the_docs_name_fail(self):
        for s in ("Dana verbal estimate", "roughly 10/08/2026", "estimate from 2026-10-01",
                  "estimated off quote 12345", "approximately quote 12345", "approx. 12345",
                  "Guesstimate 12345", "guessing from 2025 list", "phone quote 12345",
                  "ballpark 12345", "from memory 2026", "about 12345", "last time 2026-01-01",
                  "typical cost 2026", "TBD 12345", "fill in later 12345"):
            self.assertIsNotNone(m.cost_source_problem(s), s)

    def test_documents_pass(self):
        for s in ("Usual Supply Co quote 10234 2026-10-01", "Carr Lane SQ-000123 10/08/2026",
                  "Grainger MCP acct <buying account> 2026-10-14", "Star CSP 0000000000 10/07/2026"):
            self.assertIsNone(m.cost_source_problem(s), s)

    def test_no_number_fails(self):
        self.assertIn("no document number", m.cost_source_problem("Vendor quote"))


class RowRules(unittest.TestCase):
    def errors(self, s):
        _, errs, _, _ = m.validate_rows(s, UOMS)
        return errs

    def test_clean_spec_passes(self):
        self.assertEqual(self.errors(spec()), [])

    def test_item_numbers_are_upper_case(self):
        s = spec(); s["items"][0]["number"] = "ex-100"
        self.assertTrue(any("upper-case" in e for e in self.errors(s)))

    def test_top_level_vendor_needs_a_name(self):
        s = spec(); s["vendorName"] = ""
        self.assertTrue(any("vendorName is blank" in e for e in self.errors(s)))

    def test_row_override_needs_its_own_name(self):
        s = spec(); s["items"][0]["vendorNo"] = "V00001"
        errs = self.errors(s)
        self.assertTrue(any("carries no vendorName" in e for e in errs), errs)
        self.assertTrue(any("no vendorName anywhere" in e for e in errs), errs)

    def test_row_override_with_name_passes(self):
        s = spec(); s["items"][0].update({"vendorNo": "V00001", "vendorName": "Other Vendor"})
        _, errs, _, names = m.validate_rows(s, UOMS)
        self.assertEqual(errs, [])
        self.assertEqual(names["V00001"], {"Other Vendor"})

    def test_vendor_number_without_any_name_fails(self):
        s = spec(); s["vendorNo"] = ""; s["vendorName"] = ""; s["items"][0]["vendorNo"] = "V00001"
        self.assertTrue(any("no vendorName anywhere" in e for e in self.errors(s)))

    def test_price_equal_to_cost_needs_zero_margin_ok(self):
        s = spec(); s["items"][0]["unitPrice"] = 10.0
        self.assertTrue(any("0% margin" in e for e in self.errors(s)))
        s["items"][0]["zeroMarginOk"] = True
        self.assertEqual(self.errors(s), [])

    def test_price_below_cost_fails(self):
        s = spec(); s["items"][0]["unitPrice"] = 9.0
        self.assertTrue(any("below unitCost" in e for e in self.errors(s)))

    def test_zero_cost_fails_without_included_with(self):
        s = spec(); s["items"][0]["unitCost"] = 0
        self.assertTrue(any("greater than 0" in e for e in self.errors(s)))


class ConnectionFile(unittest.TestCase):
    def write(self, data):
        fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd)
        json.dump(data, open(path, "w")); self.addCleanup(os.remove, path)
        return path

    GOOD = {"tenantId": "00000000-0000-0000-0000-000000000000", "clientId": "11111111-1111-1111-1111-111111111111",
            "environment": "Sandbox", "companyId": "22222222-2222-2222-2222-222222222222"}

    def test_good_file_loads(self):
        self.assertEqual(m.read_connection_file(self.write(self.GOOD))["environment"], "Sandbox")

    def test_extra_key_stops(self):
        with self.assertRaises(SystemExit):
            m.read_connection_file(self.write({**self.GOOD, "clientSecret": "x"}))

    def test_bad_guid_stops(self):
        with self.assertRaises(SystemExit):
            m.read_connection_file(self.write({**self.GOOD, "tenantId": "not-a-guid"}))

    def test_shipped_file_is_valid(self):
        self.assertTrue(os.path.isfile(m.CONNECTION_FILE))
        self.assertEqual(sorted(m.read_connection_file(m.CONNECTION_FILE)), sorted(m.CONNECTION_KEYS))


class AuthMode(unittest.TestCase):
    def setUp(self):
        self.saved = os.environ.pop("BBS_BC_AUTH", None)

    def tearDown(self):
        if self.saved is not None:
            os.environ["BBS_BC_AUTH"] = self.saved
        else:
            os.environ.pop("BBS_BC_AUTH", None)

    def test_secret_alone_never_switches_mode(self):
        self.assertEqual(m.auth_mode("a-secret"), "delegated")

    def test_flag_without_secret_stops(self):
        os.environ["BBS_BC_AUTH"] = "app-only"
        with self.assertRaises(SystemExit):
            m.auth_mode(None)

    def test_flag_with_secret_is_app_only(self):
        os.environ["BBS_BC_AUTH"] = "app-only"
        self.assertEqual(m.auth_mode("a-secret"), "app-only")


class ErrorTable(unittest.TestCase):
    def test_codes_explained(self):
        for code in ("AADSTS65001", "AADSTS90094", "AADSTS50020", "AADSTS700016", "AADSTS53003", "expired_token"):
            self.assertTrue(m.explain_error(f"error {code} blah").startswith(code), code)
        self.assertIn("401", m.explain_error("", 401))
        self.assertIn("403", m.explain_error("", 403))
        self.assertEqual(m.explain_error("nothing known", 500), "")


class PipHint(unittest.TestCase):
    def test_hint_names_this_interpreter(self):
        self.assertTrue(m.PIP_HINT.startswith(sys.executable))
        self.assertIn("msal msal-extensions", m.PIP_HINT)


if __name__ == "__main__":
    unittest.main(verbosity=1)
