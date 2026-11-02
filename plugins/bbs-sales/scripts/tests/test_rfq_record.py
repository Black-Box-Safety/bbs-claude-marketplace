import json
import os
import re
import tempfile
import unittest

import rfq_record


FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(name):
    with open(os.path.join(FIX, name), newline="") as f:
        return f.read()


class TestEnums(unittest.TestCase):
    def test_enums_are_the_spec_strings(self):
        self.assertEqual(rfq_record.STAGES, ["logged","sourcing","priced","quote built","packet built","delivered to rep","sent","outcome"])
        self.assertEqual(rfq_record.OUTCOMES, ["won","lost","no answer","no bid"])
        self.assertEqual(rfq_record.PRICING_HEADER, "| # | Vendor | Vendor ref | Cost | Sell | Strategy | Lead | Line stage | Evidence |")
        self.assertEqual(rfq_record.HEADER_KEYS_V2[-5:], ["Rep","CRM RFQ","BC quote","PC quote","Stage"])

    def test_constants(self):
        rx = re.compile(rfq_record.STRATEGY_COST_PLUS_RE)
        self.assertTrue(rx.match("cost plus 20%"))
        self.assertFalse(rx.match("cost plus x"))
        self.assertEqual(rfq_record.LINE_STAGES, ["open","sourcing","vendor quoted","priced","quoted","substituted","parked","no bid"])
        self.assertEqual(len(rfq_record.HEADER_KEYS_V2), 16)
        a = rfq_record.PricingRow(1,"","",None,None,"","","","")
        b = rfq_record.PricingRow(2,"","",None,None,"","","","")
        self.assertEqual(a.raw, {})
        a.raw["Cost"] = "x"
        self.assertEqual(b.raw, {})


class TestParseRender(unittest.TestCase):
    def test_parse_v2_naspo_full(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        self.assertEqual(rec.header["Vehicle"], "NASPO ValuePoint MRO LPA 7-25-51-02.03")
        self.assertEqual(rec.header["Stage"], "delivered to rep")
        self.assertEqual(rec.header["BC customer"], "C-EXAMPLE")
        self.assertEqual(len(rec.lines), 3); self.assertEqual(rec.lines[0].lane, "grainger")
        self.assertEqual(rec.pricing[0].strategy, "NASPO at cost"); self.assertEqual(rec.pricing[0].cost, 42.10)
        self.assertEqual(rec.pricing[2].cost, 1250.0)
        self.assertEqual([s.stage for s in rec.status], rfq_record.STAGES)
        self.assertEqual(rec.status[0].date, "2026-10-27")
        self.assertIsNone(rec.status[-1].date)
        self.assertEqual(rec.lines_note, "Source states 3 lines; 3 captured.")
        self.assertIn("## Flags", rec.sections)

    def test_round_trip_is_byte_identical(self):
        for name in ("v2_naspo_full.md", "v2_competitive_sourcing.md"):
            text = read_fixture(name)
            self.assertEqual(rfq_record.render(rfq_record.parse(text)), text, name)

    def test_trailing_newline_state_preserved(self):
        text = read_fixture("v2_naspo_full.md")
        for t in (text.rstrip("\n"), text.rstrip("\n") + "\n", text.rstrip("\n") + "\n\n\n"):
            self.assertEqual(rfq_record.render(rfq_record.parse(t)), t)

    def test_crlf_round_trip(self):
        text = read_fixture("v2_naspo_full.md").replace("\n", "\r\n")
        rec = rfq_record.parse(text)
        self.assertEqual(rec.newline, "\r\n")
        self.assertEqual(rfq_record.render(rec), text)

    def test_header_with_pipes_and_bold(self):
        text = read_fixture("v2_naspo_full.md").replace(
            "**Buyer:** Pat Example · pat.example@agency.ca.gov · (000) 000-0000",
            "**Buyer:** Pat Example | **Requisitioner** | pat.example@agency.ca.gov")
        rec = rfq_record.parse(text)
        self.assertEqual(rec.header["Buyer"], "Pat Example | **Requisitioner** | pat.example@agency.ca.gov")
        self.assertEqual(len(rec.lines), 3)
        self.assertEqual(rfq_record.render(rec), text)

    def test_flag_cost_parses_to_none(self):
        rec = rfq_record.parse(read_fixture("v2_competitive_sourcing.md"))
        row = [r for r in rec.pricing if r.line_stage == "vendor quoted"][0]
        self.assertIsNone(row.cost); self.assertIn("[FLAG:", rfq_record.render(rec))
        self.assertEqual(row.raw["Cost"], "[FLAG: vendor has not replied]")
        self.assertEqual(rec.pricing[2].cost, None)
        self.assertEqual(rec.pricing[3].cost, 9.5)
        self.assertIn("barricade \\| folding", rec.lines[2].description)

    def test_edit_rerenders_only_changed_row(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        rec.pricing[0].cost = 40.0
        rec.header["Stage"] = "sent"
        out = rfq_record.render(rec)
        self.assertIn("| 1 | Grainger | 1AAA1 | $40.00 | $42.10 |", out)
        self.assertIn("**Stage:** sent", out)
        self.assertIn("| $1,250.00 | $1,250.00 |", out)

    def test_duplicate_section_headings_round_trip(self):
        text = read_fixture("v2_naspo_full.md").replace(
            "## Flags\n", "## Notes\n\nfirst body\n\n## Flags\n", 1).replace(
            "## Status\n", "## Notes\n\nsecond body\n\n## Status\n", 1)
        rec = rfq_record.parse(text)
        self.assertEqual(rfq_record.render(rec), text)
        self.assertIn("first body", rec.sections["## Notes"])
        self.assertIn("second body", rec.sections["## Notes#2"])
        self.assertLess(text.index("first body"), text.index("second body"))

    def test_missing_status_header_is_a_record_error(self):
        text = read_fixture("v2_naspo_full.md").replace("| Stage | Date | Evidence |", "| Stage | State | Date |")
        with self.assertRaises(rfq_record.RecordError) as cm: rfq_record.parse(text)
        self.assertTrue(any("Status" in p for p in cm.exception.problems))

    def test_missing_title_and_header_key(self):
        with self.assertRaises(rfq_record.RecordError) as cm:
            rfq_record.parse("no title\n")
        self.assertTrue(any("title" in p for p in cm.exception.problems))
        text = read_fixture("v2_naspo_full.md").replace("**Rep:** Kim Quezon\n", "")
        with self.assertRaises(rfq_record.RecordError) as cm:
            rfq_record.parse(text)
        self.assertTrue(any("Rep" in p for p in cm.exception.problems))


class TestValidationAndStages(unittest.TestCase):
    def test_validate_rejects_enum_misspellings(self):
        rec = rfq_record.parse(read_fixture("broken_pricing_enum.md"))
        problems = rfq_record.validate(rec)
        self.assertEqual(len(problems), 2)
        self.assertIn("Pricing row 1 Strategy 'at cost'", problems[0])
        self.assertIn("Line stage 'Priced'", problems[1])

    def test_valid_fixtures_have_no_problems(self):
        for n in ("v2_naspo_full.md", "v2_bpo.md", "v2_competitive_sourcing.md"):
            self.assertEqual(rfq_record.validate(rfq_record.parse(read_fixture(n))), [], n)

    def test_duplicate_sections_reported_and_round_trip(self):
        t = read_fixture("v2_naspo_full.md")
        for head in ("## Pricing", "## Status", "## Lines ("):
            i = t.index(head)
            j = t.find("\n## ", i + 3)
            j = len(t) if j < 0 else j + 1
            dup = t[i:j]
            if not dup.endswith("\n"):
                dup += "\n"
            text = t[:j] + ("" if t[:j].endswith("\n") else "\n") + "\n" + dup + t[j:]
            rec = rfq_record.parse(text)
            self.assertEqual(len(rec.lines), 3)
            self.assertEqual(len(rec.pricing), 3)
            probs = rfq_record.validate(rec)
            self.assertEqual(len(probs), 1, head)
            self.assertIn("duplicate section", probs[0])
            self.assertEqual(rfq_record.render(rec), text)

    def test_vehicle_kind(self):
        self.assertEqual(rfq_record.vehicle_kind(rfq_record.parse(read_fixture("v2_naspo_full.md"))), "naspo")
        self.assertEqual(rfq_record.vehicle_kind(rfq_record.parse(read_fixture("v2_bpo.md"))), "bpo")
        self.assertEqual(rfq_record.vehicle_kind(rfq_record.parse(read_fixture("v2_competitive_sourcing.md"))), "competitive")

    def test_applicable_stages_per_vehicle(self):
        naspo = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        bpo = rfq_record.parse(read_fixture("v2_bpo.md"))
        comp = rfq_record.parse(read_fixture("v2_competitive_sourcing.md"))
        self.assertEqual(rfq_record.applicable_stages(naspo), ["logged","priced","quote built","packet built","delivered to rep","sent","outcome"])
        self.assertEqual(rfq_record.applicable_stages(bpo), ["logged","priced","quote built","sent","outcome"])
        self.assertEqual(rfq_record.applicable_stages(comp), rfq_record.STAGES)

    def test_set_stage_never_moves_backward(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        with self.assertRaises(rfq_record.StageOrderError): rfq_record.set_stage(rec, "priced", "2026-10-30", "x")
        rfq_record.set_stage(rec, "priced", "2026-10-30", "corrected per rep 2026-10-30", force=True)
        rfq_record.set_stage(rec, "sent", "2026-10-30", "CRM RFQ-005593 submitted date")
        self.assertEqual(rfq_record.current_stage(rec), "sent"); self.assertEqual(rec.header["Stage"], "sent")

    def test_outcome_needs_an_outcome_word(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        with self.assertRaises(ValueError): rfq_record.set_stage(rec, "outcome", "2026-11-01", "buyer said thanks")
        rfq_record.set_stage(rec, "outcome", "2026-11-01", "won: BC order SO-100233")
        self.assertEqual(rfq_record.current_stage(rec), "outcome")

    def test_packet_built_not_applicable_on_bpo(self):
        rec = rfq_record.parse(read_fixture("v2_bpo.md"))
        with self.assertRaises(rfq_record.StageNotApplicableError): rfq_record.set_stage(rec, "packet built", "2026-10-30", "x")

    def test_non_applicable_rows_render_blank_and_stay_parseable(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        blank = next(r for r in rec.status if r.stage == "sourcing")
        blank.date, blank.evidence = None, ""
        rfq_record.set_stage(rec, "sent", "2026-10-30", "emailed")
        out = rfq_record.render(rec)
        self.assertIn("| sourcing |  | n/a |", out)
        rec2 = rfq_record.parse(out)
        self.assertEqual(rec2.header["Stage"], "sent")
        self.assertEqual(rfq_record.current_stage(rec2), "sent")
        self.assertEqual(rfq_record.validate(rec2), [])

    def test_dated_non_applicable_row_survives_set_stage(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        row = next(r for r in rec.status if r.stage == "sourcing")
        row.date, row.evidence = "2026-10-28", "asked vendor for one non-Grainger line"
        rfq_record.set_stage(rec, "sent", "2026-10-30", "emailed")
        row = next(r for r in rec.status if r.stage == "sourcing")
        self.assertEqual((row.date, row.evidence), ("2026-10-28", "asked vendor for one non-Grainger line"))

    def test_v1_header_quoted_in_prose_is_not_v1(self):
        src = read_fixture("v2_naspo_full.md").replace(
            "## Flags\n", "## Flags\n\nOld header was `| Stage | State | Date |`.\n", 1)
        self.assertFalse(rfq_record.is_v1(src))
        self.assertTrue(rfq_record.is_v1(read_fixture("v1_cmd_hvac.md")))

    def test_legacy_without_status_section_is_v1_but_broken_v2_is_not(self):
        good = read_fixture("v2_naspo_full.md")
        import re
        legacy = re.sub(r"\*\*Stage:\*\*[^\n]*\n", "", good[:good.index("## Status")])
        self.assertTrue(rfq_record.is_legacy(legacy))
        self.assertTrue(rfq_record.is_v1(legacy))
        broken = good.replace("| Stage | Date | Evidence |", "| Stage | When | Evidence |", 1)
        self.assertFalse(rfq_record.is_v1(broken))
        with self.assertRaises(rfq_record.RecordError): rfq_record.parse(broken)

    def test_pricing_notes_section_is_not_the_pricing_table(self):
        src = read_fixture("v2_naspo_full.md").replace(
            "## Flags\n", "## Pricing notes\n\nGrainger prices read 2026-10-28.\n\n## Flags\n", 1)
        rec = rfq_record.parse(src)
        self.assertEqual(len(rec.pricing), 3)
        self.assertIn("## Pricing notes", rfq_record.render(rec))
        self.assertEqual(rfq_record.validate(rec), [])

    def test_header_and_pricing_helpers(self):
        rec = rfq_record.parse(read_fixture("v2_naspo_full.md"))
        rfq_record.set_header(rec, "Rep", "Aanya Samarasinghe")
        self.assertIn("**Rep:** Aanya Samarasinghe", rfq_record.render(rec))
        with self.assertRaises(KeyError): rfq_record.set_header(rec, "Nope", "x")
        rfq_record.upsert_pricing(rec, rfq_record.PricingRow(2,"Grainger","2BBB2",19.0,19.0,"NASPO at cost","in stock","priced","x"))
        rfq_record.upsert_pricing(rec, rfq_record.PricingRow(4,"V","r",1.0,None,"","","open",""))
        self.assertEqual(len(rec.pricing), 4)
        self.assertEqual(rec.pricing[1].cost, 19.0)


class TestMigrate(unittest.TestCase):
    def test_migrate_cmd_hvac_keeps_every_prose_section(self):
        rec, notes = rfq_record.migrate_v1(read_fixture("v1_cmd_hvac.md"), rep="Kim Quezon")
        self.assertIn("Gap report", " ".join(rec.sections.keys()))
        self.assertEqual(rec.header["Rep"], "Kim Quezon")
        self.assertEqual(rec.header["CRM RFQ"], "[not recorded]")
        priced = [s for s in rec.status if s.stage == "priced"][0]
        self.assertEqual(priced.date, "2026-10-27")
        self.assertIn("Grainger live, at cost", priced.evidence)
        self.assertEqual(rfq_record.current_stage(rec), "packet built")
        self.assertEqual(rec.header["Stage"], "packet built")
        self.assertEqual(rfq_record.validate(rec), [])
        self.assertEqual(len(rec.pricing), 2)
        self.assertEqual(rec.pricing[0].strategy, "NASPO at cost")
        self.assertEqual(len(rec.lines), 2)

    def test_migrate_keeps_improvised_rows(self):
        rec, notes = rfq_record.migrate_v1(read_fixture("v1_improvised_rows.md"))
        self.assertEqual([s.stage for s in rec.status], rfq_record.STAGES)
        self.assertTrue(any("Status notes" in k for k in rec.sections))
        self.assertTrue(any("Vendor cost" in n for n in notes))
        self.assertTrue(rec.lines[0].part.startswith("1ABC2 (mfr "))
        self.assertEqual(rec.lines[1].part, "MFR-200")
        self.assertEqual(rfq_record.validate(rec), [])
        self.assertEqual([p.vendor for p in rec.pricing], ["Grainger", "[sourcing]"])
        q = [s for s in rec.status if s.stage == "quote built"][0]
        self.assertIsNone(q.date)
        self.assertIn("[FLAG: date unparsed: sometime]", q.evidence)
        self.assertIn("Vendor cost: received, $9.10 10.22.26", "\n".join(rec.sections.values()))

    def test_migrate_with_duplicate_sections(self):
        src = read_fixture("v1_improvised_rows.md") + "\n## Flags\n\n- a\n\n## Flags\n\n- b\n"
        rec, _ = rfq_record.migrate_v1(src)
        self.assertEqual(len(rec.lines), 2)

    def test_migrate_is_idempotent(self):
        rec, _ = rfq_record.migrate_v1(read_fixture("v1_cmd_hvac.md"))
        text = rfq_record.render(rec)
        self.assertFalse(rfq_record.is_v1(text))
        self.assertTrue(rfq_record.is_v1(read_fixture("v1_cmd_hvac.md")))
        self.assertEqual(rfq_record.render(rfq_record.parse(text)), text)


if __name__ == "__main__":
    unittest.main()


class TestStateSidecar(unittest.TestCase):
    def test_parse_date_variants(self):
        for raw, want in [("2026-10-29","2026-10-29"),("10.27.26","2026-10-27"),("10/29/2026 2:00PM Pacific","2026-10-29"),("10.27.2026","2026-10-27"),("[pending]",None),("",None),("Q4",None)]:
            self.assertEqual(rfq_record.parse_date(raw), want, raw)

    def test_to_state_shape(self):
        rec = rfq_record.parse(read_fixture("v2_competitive_sourcing.md"))
        st = rfq_record.to_state(rec, "CMD - 880000001/Pat Example/widgets 10.27.26")
        self.assertEqual(st["schema_version"], 2); self.assertEqual(st["vehicle_kind"], "competitive")
        self.assertEqual(st["lines_total"], 4); self.assertEqual(st["lines_open"], 2); self.assertEqual(st["lines_priced"], 2)
        self.assertIsNone([p for p in st["pricing"] if p["line_stage"] == "vendor quoted"][0]["cost"])
        self.assertEqual(st["header"]["CRM RFQ"], "[not in CRM]")
        self.assertEqual(st["flags"], ["Sign artwork not provided [MISSING — NEEDS INPUT]"])
        self.assertTrue(st["generated_at"].endswith("Z"))

    def test_write_state_beside_record(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "RFQ.md"); open(p, "w").write(read_fixture("v2_naspo_full.md"))
            out = rfq_record.write_state(rfq_record.parse(open(p).read()), p)
            self.assertEqual(os.path.basename(out), "rfq-state.json")
            self.assertEqual(json.load(open(out))["stage"], "delivered to rep")
