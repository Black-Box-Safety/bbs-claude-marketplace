import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

def slurp(path):
    with open(path) as f:
        return f.read()


HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
SCRIPT = os.path.join(os.path.dirname(HERE), "rfq_record.py")


def run_cli(args):
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)


class CliBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.rfq = self.copy("v2_competitive_sourcing.md", "a")
        self.sidecar = os.path.join(os.path.dirname(self.rfq), "rfq-state.json")
        self.v1 = self.copy("v1_cmd_hvac.md", "b")

    def copy(self, name, sub):
        d = os.path.join(self.tmp, sub)
        os.makedirs(d)
        dst = os.path.join(d, "RFQ.md")
        shutil.copy(os.path.join(FIX, name), dst)
        return dst


class TestCli(CliBase):
    def test_validate_ok_and_broken(self):
        rc = run_cli(["validate", self.rfq])
        self.assertEqual((rc.returncode, rc.stdout, rc.stderr), (0, "", ""))
        bad = self.copy("broken_pricing_enum.md", "c")
        rc = run_cli(["validate", bad])
        self.assertEqual(rc.returncode, 2)
        self.assertTrue(rc.stderr.strip())

    def test_missing_file_exit_1(self):
        rc = run_cli(["current-stage", os.path.join(self.tmp, "nope.md")])
        self.assertEqual(rc.returncode, 1)
        self.assertEqual(len(rc.stderr.strip().splitlines()), 1)

    def test_current_stage_and_compile(self):
        rc = run_cli(["current-stage", self.rfq])
        self.assertEqual((rc.returncode, rc.stdout.strip()), (0, "sourcing"))
        rc = run_cli(["compile", self.rfq])
        self.assertEqual(rc.returncode, 0)
        self.assertEqual(rc.stdout.strip(), self.sidecar)
        self.assertEqual(json.loads(slurp(self.sidecar))["stage"], "sourcing")
        out = os.path.join(self.tmp, "x.json")
        rc = run_cli(["compile", self.rfq, "-o", out])
        self.assertEqual(rc.returncode, 0)
        self.assertTrue(os.path.exists(out))

    def test_set_stage_cli_updates_record_and_sidecar(self):
        rc = run_cli(["set-stage", self.rfq, "priced", "--date", "2026-10-28", "--evidence", "Grainger MCP 880000001 2026-10-28"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("| priced | 2026-10-28 | Grainger MCP 880000001 2026-10-28 |", slurp(self.rfq))
        self.assertEqual(json.loads(slurp(self.sidecar))["stage"], "priced")

    def test_set_stage_cli_refuses_backward(self):
        rc = run_cli(["set-stage", self.rfq, "quote built", "--date", "2026-10-28", "--evidence", "SQ-100001"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        rc = run_cli(["set-stage", self.rfq, "priced", "--date", "2026-10-29", "--evidence", "x"])
        self.assertEqual(rc.returncode, 1)
        self.assertIn("backward", rc.stderr)
        rc = run_cli(["set-stage", self.rfq, "priced", "--date", "2026-10-29", "--evidence", "x", "--force"])
        self.assertEqual(rc.returncode, 0, rc.stderr)

    def test_pipes_quotes_newlines_round_trip(self):
        ev = 'a | b "q"\nline2'
        rc = run_cli(["set-stage", self.rfq, "quote built", "--date", "2026-11-01", "--evidence", ev])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn('| quote built | 2026-11-01 | a \\| b "q" line2 |', slurp(self.rfq))
        self.assertEqual(run_cli(["validate", self.rfq]).returncode, 0)
        self.assertEqual(run_cli(["current-stage", self.rfq]).stdout.strip(), "quote built")
        rc = run_cli(["upsert-pricing", self.rfq, "--json", json.dumps({"num": 2, "vendor": "A|B", "line_stage": "open"})])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("| 2 | A\\|B |", slurp(self.rfq))
        self.assertEqual(run_cli(["validate", self.rfq]).returncode, 0)

    def test_flag_and_string_costs(self):
        row = {"num": 2, "cost": "[FLAG: vendor silent]", "sell": "42.1", "line_stage": "open"}
        rc = run_cli(["upsert-pricing", self.rfq, "--json", json.dumps(row)])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        t = slurp(self.rfq)
        self.assertIn("[FLAG: vendor silent] | $42.10 |", t)
        self.assertEqual(run_cli(["validate", self.rfq]).returncode, 0)
        before = slurp(self.rfq)
        rc = run_cli(["upsert-pricing", self.rfq, "--json", json.dumps({"num": 2, "cost": "abc"})])
        self.assertEqual(rc.returncode, 1)
        self.assertIn("cost", rc.stderr)
        self.assertEqual(len(rc.stderr.strip().splitlines()), 1)
        self.assertEqual(slurp(self.rfq), before)

    def test_set_header_newline_folded(self):
        rc = run_cli(["set-header", self.rfq, "BC quote", "SQ-1\nSQ-2"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("**BC quote:** SQ-1 SQ-2", slurp(self.rfq))
        self.assertEqual(run_cli(["validate", self.rfq]).returncode, 0)

    def test_atomic_failure_leaves_original(self):
        sys.path.insert(0, os.path.dirname(HERE))
        import rfq_record
        before = slurp(self.rfq)
        orig = os.replace
        def boom(*a, **k):
            raise OSError("simulated")
        rfq_record.os.replace = boom
        try:
            rec = rfq_record.parse(before)
            with self.assertRaises(OSError):
                rfq_record._save(rec, self.rfq)
        finally:
            rfq_record.os.replace = orig
        self.assertEqual(slurp(self.rfq), before)
        self.assertEqual([f for f in os.listdir(os.path.dirname(self.rfq)) if f.startswith(".rfq-tmp")], [])

    def test_set_header(self):
        rc = run_cli(["set-header", self.rfq, "BC quote", "SQ-900002"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("**BC quote:** SQ-900002", slurp(self.rfq))
        rc = run_cli(["set-header", self.rfq, "Nonsense", "x"])
        self.assertEqual(rc.returncode, 1)

    def test_upsert_pricing_cli(self):
        row = {"num": 2, "vendor": "Acme Valve", "vendor_ref": "QuoteCB0000024667.pdf", "cost": 310.0, "sell": 372.0, "strategy": "cost plus 20%", "lead": "5 days", "line_stage": "vendor quoted", "evidence": "QuoteCB0000024667.pdf"}
        rc = run_cli(["upsert-pricing", self.rfq, "--json", json.dumps(row)])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("| 2 | Acme Valve |", slurp(self.rfq))
        self.assertTrue(os.path.exists(self.sidecar))

    def test_upsert_pricing_invalid_not_written(self):
        before = slurp(self.rfq)
        row = {"num": 2, "strategy": "made up", "line_stage": "open"}
        rc = run_cli(["upsert-pricing", self.rfq, "--json", json.dumps(row)])
        self.assertEqual(rc.returncode, 1)
        self.assertEqual(slurp(self.rfq), before)
        self.assertFalse(os.path.exists(self.sidecar))

    def test_migrate_cli_dry_run_writes_nothing(self):
        v1 = self.copy("v1_improvised_rows.md", "d")
        before = slurp(v1)
        rc = run_cli(["migrate", v1, "--dry-run"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertEqual(slurp(v1), before)
        self.assertIn("would convert cleanly", rc.stdout)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(v1), "rfq-state.json")))

    def test_migrate_dry_run_reports_problems_with_exit_2(self):
        # A v1 record whose body repeats a section heading cannot render to a valid v2 record.
        bad = self.copy("v1_cmd_hvac.md", "e")
        txt = slurp(bad) + "\n## Status\n\n| Stage | State | Date |\n|---|---|---|\n| Logged | done | 10.27.26 |\n"
        self.assertNotEqual(txt, slurp(bad))
        with open(bad, "w") as f:
            f.write(txt)
        rc = run_cli(["migrate", bad, "--dry-run"])
        self.assertEqual(rc.returncode, 2, rc.stdout + rc.stderr)
        self.assertNotIn("would convert cleanly", rc.stdout)
        self.assertEqual(slurp(bad), txt)

    def test_migrate_dry_run_unparseable_exits_2_would_not_convert(self):
        bad = self.copy("v1_cmd_hvac.md", "f")
        with open(bad, "w") as f:
            f.write("no title here\n\n## Status\n\n| Stage | State | Date |\n")
        rc = run_cli(["migrate", bad, "--dry-run"])
        self.assertEqual(rc.returncode, 2, rc.stdout + rc.stderr)
        self.assertIn("would not convert:", rc.stdout)

    def test_migrate_writes_then_refuses_v2(self):
        rc = run_cli(["migrate", self.v1, "--rep", "Kim Quezon"])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.assertIn("**Stage:**", slurp(self.v1))
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(self.v1), "rfq-state.json")))
        self.assertEqual(run_cli(["validate", self.v1]).returncode, 0)
        rc = run_cli(["migrate", self.v1])
        self.assertEqual(rc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
