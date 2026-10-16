#!/usr/bin/env python3
"""Offline checks for bc_quote_entry.py: no network, no Business Central, no sign-in.

    python3 test_bc_quote_entry.py

Mirrors test_bc_item_entry.py: the rules the docs name in words (spec-schema.md, quote-rules.md)
are held here, so a wording change the script no longer enforces fails here instead of on a
rep's quote. The gates that need BC take a fake with the three reads they use.
"""
import copy
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc_quote_entry as m  # noqa: E402

UOMS = {"EA", "PK10", "CS"}
# The CONTRACT list as BC-WRITE-SOP-RULES.md section 1 prints it. Change both, or neither.
SOP_CONTRACT_CODES = {"OPEN", "NASPO", "NPPGOV", "GSA", "OMNIA", "EMRKT", "ICPT", "UCOP", "BODYARMOR", "BA-CA",
                      "BA-SRCWL", "WWG-SRCWL", "DODIG", "QB LEGACY", "BBSACCOUNTINGONLY"}


def spec(**over):
    base = {
        "deal": "Example Agency - 30 EA EX-6001 covers",
        "customerNumber": "C00000",
        "externalDocumentNumber": "RFQ EX-6001 01-02-26",
        "contract": "OPEN",
        "book": "ca-state",
        "agency": "DGS",
        "salesperson": "CA STATE TEAM",
        "shipTo": {"shipToName": "Example Agency Training Center", "shipToContact": "Buyer Name",
                   "shipToAddressLine1": "100 Example Road", "shipToAddressLine2": "", "shipToCity": "Sacramento",
                   "shipToState": "CA", "shipToPostCode": "95814", "shipToCountry": "US"},
        "costSource": "Example Distributor quote Q-000001 dated 01/02/2026",
        "pricingBasis": "5.0% over cost with freight folded in",
        "lines": [{"line": 1, "number": "EX-6001", "description": "Example Mfr EX-6001 Aluminized Helmet Cover",
                   "qty": 30, "uom": "EA", "unitCost": 89.50, "unitPrice": 95.50}],
        "quoteTotalExclTax": 2865.00,
        "preparedBy": "Rep Name",
    }
    base.update(over)
    return base


def errors(s, uoms=UOMS):
    _, _, errs, _ = m.validate_spec(s, uoms)
    return errs


class ContractList(unittest.TestCase):
    def test_matches_sop_section_1(self):
        self.assertEqual(set(m.CONTRACT_CODES), SOP_CONTRACT_CODES)

    def test_unknown_code_stops(self):
        self.assertTrue(any("not a CONTRACT code" in e for e in errors(spec(contract="SOURCEWELL"))))
        self.assertTrue(any("not a CONTRACT code" in e for e in errors(spec(contract="open"))))

    def test_every_code_passes(self):
        for code in SOP_CONTRACT_CODES:
            book = "body-armor" if code in m.BODY_ARMOR_CONTRACTS else "ca-state"
            self.assertEqual(errors(spec(contract=code, book=book)), [], code)


class HeaderRules(unittest.TestCase):
    def test_clean_spec_passes(self):
        header, lines, errs, warns = m.validate_spec(spec(), UOMS)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])
        self.assertEqual(header["total"], 2865.0)
        self.assertEqual(lines[0]["extPrice"], 2865.0)
        self.assertAlmostEqual(lines[0]["gm"], 6.28, places=2)

    def test_required_fields(self):
        for k in m.TOP_REQUIRED:
            s = spec(); del s[k]
            self.assertTrue(any(e.startswith(f"{k} is required") for e in errors(s)), k)

    def test_external_document_number_length(self):
        self.assertTrue(any("limit 35" in e for e in errors(spec(externalDocumentNumber="X" * 36))))
        self.assertEqual(errors(spec(externalDocumentNumber="X" * 35)), [])
        self.assertTrue(any("is required" in e for e in errors(spec(externalDocumentNumber=""))))
        self.assertTrue(any("trailing spaces" in e for e in errors(spec(externalDocumentNumber="RFQ 1 "))))

    def test_book_values(self):
        self.assertTrue(any("book 'federal' must be one of" in e for e in errors(spec(book="federal"))))
        for b in m.BOOKS:
            s = spec(book=b)
            if b == "body-armor":
                s["contract"] = "BA-CA"
            if b == "higher-ed":
                s["agency"], s["salesperson"] = "CSU", "JMAGLIATO"
            self.assertEqual(errors(s), [], b)

    def test_codes_are_upper_case(self):
        self.assertTrue(any("upper-case" in e for e in errors(spec(customerNumber="c00000"))))
        self.assertTrue(any("upper-case" in e for e in errors(spec(salesperson="ca state team"))))

    def test_ship_to_unknown_key_stops(self):
        s = spec(); s["shipTo"]["shipToPhone"] = "555-0100"
        self.assertTrue(any("shipTo carries ['shipToPhone']" in e for e in errors(s)))

    def test_ship_to_required_fields(self):
        for k in m.SHIP_TO_REQUIRED:
            s = spec(); s["shipTo"][k] = ""
            self.assertTrue(any(f"shipTo.{k} is required" in e for e in errors(s)), k)

    def test_ship_to_state_is_two_letters(self):
        s = spec(); s["shipTo"]["shipToState"] = "California"
        self.assertTrue(any("two-letter" in e for e in errors(s)))

    def test_cost_source_guess_words_fail(self):
        for src in ("Dana verbal estimate", "roughly 10/08/2026", "ballpark 12345", "Vendor quote"):
            self.assertTrue(any(e.startswith("costSource") for e in errors(spec(costSource=src))), src)

    def test_unknown_top_level_key_warns_only(self):
        _, _, errs, warns = m.validate_spec(spec(approvedBy="free text", notes="x"), UOMS)
        self.assertEqual(errs, [])
        self.assertTrue(any("'notes'" in w for w in warns))
        self.assertFalse(any("approvedBy" in w for w in warns))


class LineRules(unittest.TestCase):
    def line(self, **over):
        s = spec(); s["lines"][0].update(over)
        if "unitPrice" in over or "qty" in over:
            s["quoteTotalExclTax"] = round(s["lines"][0]["qty"] * s["lines"][0]["unitPrice"], 2)
        return s

    def test_description_limit_and_ascii(self):
        self.assertTrue(any("limit 100" in e for e in errors(self.line(description="X" * 101))))
        self.assertEqual(errors(self.line(description="X" * 100)), [])
        self.assertTrue(any("non-ASCII" in e for e in errors(self.line(description="Cover — special order"))))
        self.assertTrue(any("description is required" in e for e in errors(self.line(description=""))))

    def test_item_number_upper_case(self):
        self.assertTrue(any("upper-case" in e for e in errors(self.line(number="phx 6001"))))
        self.assertEqual(errors(self.line(number="PHX 6001")), [])

    def test_zero_price_stops(self):
        self.assertTrue(any("unitPrice must be a number greater than 0" in e for e in errors(self.line(unitPrice=0))))

    def test_price_below_cost_stops(self):
        self.assertTrue(any("below unitCost" in e for e in errors(self.line(unitPrice=80.0))))

    def test_price_equal_cost_needs_zero_margin_ok(self):
        s = self.line(unitPrice=89.50)
        self.assertTrue(any("0% margin" in e for e in errors(s)))
        s["lines"][0]["zeroMarginOk"] = True
        self.assertEqual(errors(s), [])
        s = self.line(unitPrice=89.50); s["zeroMarginOk"] = True   # the NASPO shape: spec-level
        _, lines, errs, _ = m.validate_spec(s, UOMS)
        self.assertEqual(errs, [])
        self.assertTrue(lines[0]["atCost"])

    def test_cost_required(self):
        self.assertTrue(any("unitCost must be a number greater than 0" in e for e in errors(self.line(unitCost=0))))
        s = spec(); del s["lines"][0]["unitCost"]
        self.assertTrue(any("unitCost must be" in e for e in errors(s)))

    def test_qty_and_uom(self):
        self.assertTrue(any("qty must be" in e for e in errors(self.line(qty=0))))
        self.assertTrue(any("not a unit of measure in BC" in e for e in errors(self.line(uom="DZ"))))
        self.assertTrue(any("uom is required" in e for e in errors(self.line(uom=""))))

    def test_line_numbers_positive_and_unique(self):
        s = spec(); s["lines"].append(dict(s["lines"][0])); s["quoteTotalExclTax"] = 5730.0
        self.assertTrue(any("line 1 is duplicated" in e for e in errors(s)))
        self.assertTrue(any("positive integer" in e for e in errors(self.line(line=0))))
        self.assertTrue(any("positive integer" in e for e in errors(self.line(line="1"))))

    def test_lines_must_sum_to_total(self):
        self.assertTrue(any("lines sum to 2,865.00 but quoteTotalExclTax is 2,900.00" in e
                            for e in errors(spec(quoteTotalExclTax=2900.0))))

    def test_multiline_total_rounding(self):
        s = spec()
        s["lines"] = [{"line": 1, "number": "A", "description": "A", "qty": 3, "uom": "EA", "unitCost": 1.0, "unitPrice": 1.11},
                      {"line": 2, "number": "B", "description": "B", "qty": 7, "uom": "EA", "unitCost": 2.0, "unitPrice": 2.22}]
        s["quoteTotalExclTax"] = round(3 * 1.11 + 7 * 2.22, 2)
        self.assertEqual(errors(s), [])


class Owner(unittest.TestCase):
    """Whose quote it is. Parker, in session, 2026-10-16: Parker holds no accounts on the state book, so a
    state quote carries Kim's code for her 18 agencies and Aanya's for every other state agency."""

    KIM_18 = {"CDCR", "CHP", "CAL FIRE", "CMD", "CDFW", "CAL OES", "DOJ", "DPR", "DWR", "DCC", "CCC", "ABC", "DOC",
              "SWRCB", "OIG", "POST", "CHRB", "CGCC"}

    def owner_errors(self, **over):
        return [e for e in errors(spec(**over)) if "salesperson" in e or "book" in e or "agency" in e or "CONTRACT" in e]

    def test_kim_has_eighteen_agencies(self):
        self.assertEqual(set(m.KIM_AGENCIES), self.KIM_18)
        self.assertEqual(len(m.KIM_AGENCIES), 18)

    def test_codes(self):
        self.assertEqual(m.KIM_CODE, "KQUEZON")
        self.assertEqual(m.AANYA_CODE, "CA STATE TEAM")
        self.assertEqual(m.HIGHER_ED_CODES, {"JMAGLIATO", "UNIVERSITY"})

    def test_kim_agency_needs_kim_code(self):
        for agency in self.KIM_18:
            self.assertEqual(self.owner_errors(agency=agency, salesperson="KQUEZON"), [], agency)
            errs = self.owner_errors(agency=agency, salesperson="CA STATE TEAM")
            self.assertTrue(any("Kim Quezon's agencies" in e and "KQUEZON" in e for e in errs), agency)

    def test_aliases_resolve(self):
        for alias, key in (("CalFire", "CAL FIRE"), ("Cal Fire", "CAL FIRE"), ("Fish & Wildlife", "CDFW"),
                           ("Department of Water Resources", "DWR"), ("State Water Board", "SWRCB"), ("CWB", "SWRCB"),
                           ("Cal OES", "CAL OES"), ("Highway Patrol", "CHP"), ("dgs", "DGS"), ("Caltrans", "CALTRANS"),
                           ("California State University", "CSU")):
            self.assertEqual(m.normalize_agency(alias), key, alias)

    def test_other_state_agency_is_aanya(self):
        for agency in ("DGS", "Caltrans", "DSH", "CalVet", "DMV", "CDFA", "CARB", "DTSC", "CalRecycle"):
            self.assertEqual(self.owner_errors(agency=agency, salesperson="CA STATE TEAM"), [], agency)
            errs = self.owner_errors(agency=agency, salesperson="KQUEZON")
            self.assertTrue(any("Aanya Samarasinghe's" in e for e in errs), agency)

    def test_parker_never_on_a_state_quote(self):
        errs = self.owner_errors(agency="DGS", salesperson="PMARSHALL")
        self.assertTrue(any("Parker holds no accounts on the state book" in e for e in errs))
        errs = self.owner_errors(agency="CAL FIRE", salesperson="PMARSHALL")
        self.assertTrue(any("KQUEZON" in e for e in errs))

    def test_atwater_spec_shape_is_the_defect(self):
        """The CAL FIRE Atwater quote of 2026-10-16 went out as CA STATE TEAM; CAL FIRE is Kim's."""
        errs = self.owner_errors(agency="CAL FIRE", salesperson="CA STATE TEAM")
        self.assertTrue(any("never carry the CA STATE TEAM bucket" in e for e in errs))

    def test_agency_required_on_state_book(self):
        s = spec(); del s["agency"]
        self.assertTrue(any("needs agency" in e for e in errors(s)))

    def test_higher_ed_is_joey(self):
        errs = self.owner_errors(agency="CSU", salesperson="CA STATE TEAM")
        self.assertTrue(any("Joey Magliato's book" in e and "higher-ed" in e for e in errs))
        self.assertEqual(self.owner_errors(book="higher-ed", agency="UC", salesperson="UNIVERSITY"), [])
        self.assertEqual(self.owner_errors(book="higher-ed", agency="CSU", salesperson="JMAGLIATO"), [])
        errs = self.owner_errors(book="higher-ed", agency="CSU", salesperson="KQUEZON")
        self.assertTrue(any("JMAGLIATO or UNIVERSITY" in e for e in errs))
        errs = self.owner_errors(book="higher-ed", agency="DGS", salesperson="JMAGLIATO")
        self.assertTrue(any("CSU or UC only" in e for e in errs))

    def test_body_armor_is_parker_and_outside_the_book(self):
        errs = self.owner_errors(agency="CHP", contract="BA-CA", salesperson="KQUEZON")
        self.assertTrue(any("outside the Kim/Aanya state book; set book: body-armor" in e for e in errs))
        self.assertEqual(self.owner_errors(book="body-armor", contract="BA-CA", salesperson="BA-CF"), [])
        self.assertEqual(self.owner_errors(book="body-armor", contract="BODYARMOR", salesperson="PMARSHALL"), [])
        errs = self.owner_errors(book="body-armor", contract="OPEN", salesperson="PMARSHALL")
        self.assertTrue(any("needs a body-armor CONTRACT" in e for e in errs))

    def test_other_book_is_not_gated(self):
        s = spec(book="other", salesperson="PMARSHALL"); del s["agency"]
        self.assertEqual(errors(s), [])
        header, _, _, _ = m.validate_spec(s, UOMS)
        self.assertIn("outside the California state book", header["owner"])

    def test_owner_text_on_the_sheet(self):
        header, _, errs, _ = m.validate_spec(spec(agency="CAL FIRE", salesperson="KQUEZON"), UOMS)
        self.assertEqual(errs, [])
        self.assertEqual(header["owner"], "CA state / CAL FIRE -> Kim Quezon (KQUEZON)")

    def header(self, **over):
        h, _, errs, _ = m.validate_spec(spec(**over), UOMS)
        self.assertEqual(errs, [])
        return h

    def test_customer_dimension_cross_check(self):
        kim = self.header(agency="CAL FIRE", salesperson="KQUEZON")
        note, err = m.dimension_conflict("CALFIRE", kim)
        self.assertIsNone(err); self.assertIn("agrees", note)
        note, err = m.dimension_conflict("DSH", kim)
        self.assertIn("DSH (DSH, Aanya Samarasinghe's)", err)
        note, err = m.dimension_conflict("CSU", kim)
        self.assertIn("Joey Magliato's book", err)
        note, err = m.dimension_conflict("AGNCY", kim)
        self.assertIsNone(err); self.assertIn("does not name one agency", note)
        note, err = m.dimension_conflict("", kim)
        self.assertIsNone(err); self.assertIn("[FLAG", note)
        aanya = self.header(agency="DSH", salesperson="CA STATE TEAM")
        note, err = m.dimension_conflict("DCR", aanya)
        self.assertIn("Kim Quezon's", err)
        note, err = m.dimension_conflict("DGS", aanya)   # both Aanya's: a different agency, same owner, passes
        self.assertIsNone(err)
        joey = self.header(book="higher-ed", agency="CSU", salesperson="JMAGLIATO")
        note, err = m.dimension_conflict("DGS", joey)
        self.assertIn("a state agency, not CSU or UC", err)
        other = self.header(book="other", salesperson="PMARSHALL")
        self.assertIsNone(m.dimension_conflict("DCR", other)[1])


class FakeBC:
    """The reads the gates use, with canned answers."""

    def __init__(self, customers=None, items=None, quotes=None, dimension=""):
        self.customers, self.items_, self.quotes = customers or {}, items or {}, quotes or []
        self.dimension = dimension

    def customer_dimension(self, cust, code="CUSTOMER"):
        return self.dimension

    def customer(self, number):
        return self.customers.get(number)

    def item(self, number):
        return self.items_.get(number)

    def quotes_with_ext_doc(self, ext):
        return [q for q in self.quotes if q.get("externalDocumentNumber") == ext]


def good_item(number="EX-6001", **over):
    d = {"number": number, "displayName": "Example Mfr EX-6001", "type": "Inventory", "blocked": False,
         "unitCost": 89.5, "unitPrice": 0}
    d.update(over)
    return d


class Gates(unittest.TestCase):
    def setUp(self):
        self.header, self.lines, errs, _ = m.validate_spec(spec(), UOMS)
        self.assertEqual(errs, [])
        self.cust = {"number": "C00000", "displayName": "Example Agency", "blocked": " ", "paymentTermsId": "pt-1",
                     "shipmentMethodId": "sm-1", "city": "Sacramento", "state": "CA"}

    def test_customer_missing_or_blocked(self):
        rec, errs = m.customer_gate(FakeBC(), self.header)
        self.assertIsNone(rec)
        self.assertTrue(any("does not exist" in e for e in errs))
        _, errs = m.customer_gate(FakeBC({"C00000": {**self.cust, "blocked": "All"}}), self.header)
        self.assertTrue(any("is blocked: All" in e for e in errs))
        _, errs = m.customer_gate(FakeBC({"C00000": self.cust}), self.header)
        self.assertEqual(errs, [])

    def test_missing_item_stops_with_item_entry_instruction(self):
        _, errs, _ = m.item_gate(FakeBC(items={}), self.lines)
        self.assertEqual(len(errs), 1)
        self.assertIn("enter it through bc-item-entry", errs[0])

    def test_item_type_and_blocked(self):
        _, errs, _ = m.item_gate(FakeBC(items={"EX-6001": good_item(type="Non_x002D_Inventory")}), self.lines)
        self.assertTrue(any("type Non-Inventory, not Inventory" in e for e in errs))
        _, errs, _ = m.item_gate(FakeBC(items={"EX-6001": good_item(blocked=True)}), self.lines)
        self.assertTrue(any("is blocked" in e for e in errs))

    def test_card_cost_difference_is_a_note_not_a_stop(self):
        cards, errs, notes = m.item_gate(FakeBC(items={"EX-6001": good_item(unitCost=0)}), self.lines)
        self.assertEqual(errs, [])
        self.assertTrue(any("card cost 0.00 differs" in n for n in notes))
        self.assertIn("EX-6001", cards)

    def test_duplicate_external_document_number_stops(self):
        bc = FakeBC(quotes=[{"number": "SQ-100001", "status": "Draft", "customerNumber": "C00000",
                             "documentDate": "2026-01-01", "externalDocumentNumber": "RFQ EX-6001 01-02-26"}])
        errs = m.dup_gate(bc, self.header)
        self.assertEqual(len(errs), 1)
        self.assertIn("SQ-100001", errs[0])
        self.assertEqual(m.dup_gate(FakeBC(), self.header), [])

    def test_header_gate_pure(self):
        h = {"customerNumber": "C00000", "paymentTermsId": "pt-1", "shipmentMethodId": "sm-1",
             "shortcutDimension1Code": "OPEN", "salesperson": "CA STATE TEAM",
             "externalDocumentNumber": "RFQ EX-6001 01-02-26", **spec()["shipTo"]}
        self.assertTrue(all(ok for _, ok in m.header_gate(h, self.cust, self.header)))
        bad = dict(h, shipToCity="Corinne", shipToState="UT")
        failed = [n for n, ok in m.header_gate(bad, self.cust, self.header) if not ok]
        self.assertEqual(len(failed), 1)
        self.assertTrue(failed[0].startswith("ship-to"))
        failed = [n for n, ok in m.header_gate(dict(h, paymentTermsId="pt-2"), self.cust, self.header) if not ok]
        self.assertEqual(failed, ["payment terms = customer card"])

    def test_verify_lines_pure(self):
        doc = {"totalAmountExcludingTax": 2865.0,
               "salesQuoteLines": [{"sequence": 10000, "lineObjectNumber": "EX-6001", "unitPrice": 95.5, "quantity": 30,
                                    "unitOfMeasureCode": "EA", "description": self.lines[0]["description"],
                                    "amountExcludingTax": 2865.0}]}
        checks, mism = m.verify_lines(doc, self.lines, 2865.0)
        self.assertTrue(all(ok for _, ok in checks), checks)
        self.assertEqual(mism, [])
        doc2 = copy.deepcopy(doc); doc2["salesQuoteLines"][0]["unitPrice"] = 95.0
        checks, mism = m.verify_lines(doc2, self.lines, 2865.0)
        self.assertEqual(mism, [1])
        self.assertFalse(all(ok for _, ok in checks))


class Approval(unittest.TestCase):
    def write(self, data):
        fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd)
        with open(path, "w") as fh:
            json.dump(data, fh)
        self.addCleanup(os.remove, path)
        return path

    def args(self, path, token, who):
        return types.SimpleNamespace(spec=path, approve=token, approved_by=who, account=None)

    def test_token_mismatch_stops_before_bc(self):
        path = self.write(spec())
        with self.assertRaises(SystemExit):
            m.approval_gate(self.args(path, "000000000000", "Rep Name"), m.load_spec(path))
        with self.assertRaises(SystemExit):   # commit itself stops there too, no BC construction
            m.cmd_commit(self.args(path, "000000000000", "Rep Name"))

    def test_token_changes_with_the_spec(self):
        path = self.write(spec())
        t1 = m.spec_token(path)
        with open(path, "w") as fh:
            json.dump(spec(quoteTotalExclTax=2866.0), fh)
        self.assertNotEqual(t1, m.spec_token(path))

    def test_name_must_match_prepared_by(self):
        path = self.write(spec()); token = m.spec_token(path)
        with self.assertRaises(SystemExit):
            m.approval_gate(self.args(path, token, "Someone Else"), m.load_spec(path))
        with self.assertRaises(SystemExit):
            m.approval_gate(self.args(path, token, "me"), m.load_spec(path))
        who, t = m.approval_gate(self.args(path, token, "rep name"), m.load_spec(path))
        self.assertEqual((who, t), ("rep name", token))


class Reuse(unittest.TestCase):
    """The connection file, cache and error table are the sibling's; nothing is copied."""

    def test_imports_the_sibling(self):
        self.assertTrue(os.path.isfile(m.item.CONNECTION_FILE))
        self.assertTrue(m.item.CONNECTION_FILE.replace("\\", "/").endswith("bc-item-entry/references/bc-connection.json"))
        self.assertTrue(issubclass(m.QuoteBC, m.item.BC))
        self.assertIs(m.explain_error, m.item.explain_error)
        self.assertIs(m.cost_source_problem, m.item.cost_source_problem)

    def test_no_connection_file_of_its_own(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(m.__file__)))
        self.assertFalse(os.path.exists(os.path.join(here, "references", "bc-connection.json")))

    def test_fixed_values(self):
        self.assertEqual(m.DROPSHIP_ID, "006fd057-c685-ef11-ac23-6045bdecc5e4")
        self.assertNotIn("validUntilDate", json.dumps([m.TOP_KNOWN, m.LINE_KNOWN]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
