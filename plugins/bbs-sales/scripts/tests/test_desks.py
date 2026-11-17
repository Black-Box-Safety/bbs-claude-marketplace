import os
import sys
import tempfile
import unittest

# Run from anywhere, including CI's `python3 -m unittest discover -s plugins/bbs-sales/scripts/tests`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import desks as desks_mod  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def inline(*specs):
    base = desks_mod.FALLBACK[0]
    out = []
    for i, (kind, roots) in enumerate(specs):
        d = dict(base)
        d.update(desk_id="d%d" % i, kind=kind, roots=roots)
        out.append(d)
    return out


class TestLoad(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.pop(desks_mod.REGISTRY_ENV, None)

    def tearDown(self):
        os.environ.pop(desks_mod.REGISTRY_ENV, None)
        if self._old is not None:
            os.environ[desks_mod.REGISTRY_ENV] = self._old

    def test_default_registry_has_ca_state(self):
        desks, err = desks_mod.load()
        self.assertIsNone(err)
        self.assertEqual([d["desk_id"] for d in desks], ["ca-state"])
        self.assertEqual(desks[0]["roots"], ["All RFQ's by Agency"])

    def test_fallback_equals_registry(self):
        desks, _ = desks_mod.load()
        self.assertEqual(desks_mod.FALLBACK, desks)

    def test_fallback_is_a_copy(self):
        desks, err = desks_mod.load("/no/such/desks.json")
        desks[0]["roots"].append("x")
        self.assertEqual(desks_mod.FALLBACK[0]["roots"], ["All RFQ's by Agency"])

    def test_env_override(self):
        os.environ[desks_mod.REGISTRY_ENV] = os.path.join(FIX, "desks-two.json")
        desks, err = desks_mod.load()
        self.assertIsNone(err)
        self.assertEqual([d["desk_id"] for d in desks], ["ca-state", "test-desk"])

    def _tmp(self, text):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "desks.json")
        with open(p, "w") as f:
            f.write(text)
        return p

    def test_load_invalid_json_falls_back(self):
        bad = self._tmp('{"desks": [')
        desks, err = desks_mod.load(bad)
        self.assertEqual(desks, desks_mod.FALLBACK)
        self.assertIn("desks.json", err)
        self.assertNotIn("\n", err)

    def test_load_missing_file_falls_back(self):
        desks, err = desks_mod.load("/no/such/dir/desks.json")
        self.assertEqual(desks, desks_mod.FALLBACK)
        self.assertIn("desks.json", err)
        self.assertIn("not found", err)

    def test_load_schema_error_falls_back(self):
        import json
        with open(os.path.join(FIX, "desks-two.json")) as f:
            data = json.load(f)
        data["desks"][0]["kind"] = "deal"
        p = self._tmp(json.dumps(data))
        desks, err = desks_mod.load(p)
        self.assertEqual(desks, desks_mod.FALLBACK)
        self.assertIn("desks.json", err)
        self.assertIn("kind", err)

    def test_load_duplicate_id_and_extra_key_fall_back(self):
        import json
        with open(os.path.join(FIX, "desks-two.json")) as f:
            data = json.load(f)
        data["desks"][1]["desk_id"] = "ca-state"
        _, err = desks_mod.load(self._tmp(json.dumps(data)))
        self.assertIn("desk_id", err)
        with open(os.path.join(FIX, "desks-two.json")) as f:
            data = json.load(f)
        data["desks"][0]["extra"] = 1
        _, err = desks_mod.load(self._tmp(json.dumps(data)))
        self.assertIn("keys", err)


class TestFind(unittest.TestCase):
    def setUp(self):
        self.desks = desks_mod.FALLBACK

    def test_find_case_insensitive(self):
        m = desks_mod.find("/x/all rfq's BY AGENCY/CDCR/Buyer/a.md", self.desks)
        self.assertEqual((m.desk["desk_id"], m.root, m.start), ("ca-state", "All RFQ's by Agency", 3))

    def test_find_backslash_path(self):
        m = desks_mod.find("C:\\Desk\\All RFQ's by Agency\\A\\B\\x.md", self.desks)
        self.assertEqual(m.start, 8)

    def test_find_none_outside(self):
        self.assertIsNone(desks_mod.find("/x/Customers/Bechtel/sentinel/a.md", self.desks))

    def test_find_leftmost(self):
        p = "/x/Old All RFQ's by Agency backup/All RFQ's by Agency/a.md"
        self.assertEqual(desks_mod.find(p, self.desks).start, 7)

    def test_find_all_two_occurrences(self):
        p = "/x/Old All RFQ's by Agency backup/All RFQ's by Agency/a.md"
        self.assertEqual([m.start for m in desks_mod.find_all(p, self.desks)], [7, 34])

    def test_find_overlap_prefers_longest(self):
        reg = inline(("rfq", ["Bechtel", "Bechtel/sentinel"]))
        self.assertEqual(desks_mod.find("/C/Bechtel/sentinel/x", reg).root, "Bechtel/sentinel")

    def test_find_all_overlap_keeps_longest_then_continues(self):
        reg = inline(("rfq", ["Bechtel", "Bechtel/sentinel"]))
        ms = desks_mod.find_all("/C/Bechtel/sentinel/x/Bechtel/y", reg)
        self.assertEqual([(m.root, m.start) for m in ms], [("Bechtel/sentinel", 3), ("Bechtel", 22)])

    def test_order_desks_never_match(self):
        reg = inline(("order", ["BBS CSU UC"]))
        self.assertIsNone(desks_mod.find("/x/BBS CSU UC/a", reg))
        self.assertEqual(desks_mod.find_all("/x/BBS CSU UC/a", reg), [])


if __name__ == "__main__":
    unittest.main()
