#!/usr/bin/env python3
"""check_desk_registry() against temp copies of the bbs-sales files it reads.

Run: python3 scripts/tests/test_check_desk_registry.py   (or python3 -m unittest discover -s scripts/tests)
"""
import glob
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REAL = os.path.join(REPO, "plugins", "bbs-sales")
spec = importlib.util.spec_from_file_location("check_marketplace", os.path.join(REPO, "scripts", "check_marketplace.py"))
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

COPY = (["hooks/*.py", "hooks/*.ps1", "hooks/desk-post.sh", "scripts/desks.py", "scripts/Desks.ps1",
         "scripts/rfq_record.py", "references/desks.json", "skills/desk-remember/scripts/desk_memory.py"])


def run(base):
    findings = []
    cm.check_desk_registry(findings, base)
    return [f for f in findings if f["level"] == "FAIL"]


class DeskRegistryChecker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.base = os.path.join(self.tmp, "bbs-sales")
        for pat in COPY:
            for src in glob.glob(os.path.join(REAL, pat)):
                dst = os.path.join(self.base, os.path.relpath(src, REAL))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)

    def edit(self, rel, fn):
        p = os.path.join(self.base, rel)
        with open(p, encoding="utf-8", newline="") as f:
            t = f.read()
        new = fn(t)
        self.assertNotEqual(t, new, "edit changed nothing in " + rel)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(new)

    def codes(self):
        return {f["code"] for f in run(self.base)}

    def test_real_tree_passes(self):
        self.assertEqual(run(REAL), [])

    def test_stray_literal_fails(self):
        p = os.path.join(self.base, "hooks", "x.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write('ROOT = "All RFQ\'s by Agency"\n')
        fails = run(self.base)
        self.assertEqual([f["code"] for f in fails], ["desk_literal"])
        self.assertIn("hooks/x.py", fails[0]["where"])

    def test_literal_allowed_in_registry_and_loaders(self):
        self.assertEqual(self.codes(), set())  # desks.py/Desks.ps1/desks.json carry it

    def test_mismatched_ps_fallback_fails(self):
        self.edit("scripts/Desks.ps1", lambda t: t.replace('"rep_min_depth":2', '"rep_min_depth":3', 1))
        self.assertEqual(self.codes(), {"desk_fallback_ps"})

    def test_mismatched_py_fallback_fails(self):
        self.edit("scripts/desks.py", lambda t: t.replace('"rep_min_depth": 2,', '"rep_min_depth": 3,', 1))
        self.assertEqual(self.codes(), {"desk_fallback_py"})

    def test_schema_error_fails(self):
        self.edit("references/desks.json", lambda t: t.replace('"kind": "rfq"', '"kind": "bogus"'))
        self.assertIn("desk_registry_schema", self.codes())

    def test_non_strict_json_fails(self):
        self.edit("references/desks.json", lambda t: t.replace("}\n  ]", "},\n  ]"))
        self.assertIn("desk_registry_schema", self.codes())

    def test_root_without_prefilter_token_fails(self):
        def add(t):
            d = json.loads(t)
            d["desks"].append(dict(d["desks"][0], desk_id="other", roots=["Zebra Orders"]))
            return json.dumps(d)
        self.edit("references/desks.json", add)
        self.assertEqual(self.codes(), {"desk_prefilter_root"})

    def test_missing_bracket_form_fails(self):
        self.edit("hooks/desk-post.sh", lambda t: t.replace("[Bb][Yy]\\ [Aa][Gg][Ee][Nn][Cc][Yy]", "NOPE"))
        self.assertEqual(self.codes(), {"desk_prefilter_bracket"})

    def test_marker_token_mismatch_fails(self):
        self.edit("hooks/desk-memory.py", lambda t: t.replace('r"by agency"', 'r"by agent"'))
        self.assertEqual(self.codes(), {"desk_marker_token"})


if __name__ == "__main__":
    unittest.main()
