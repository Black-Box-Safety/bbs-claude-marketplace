#!/usr/bin/env python3
"""Pins the path-segment boundary in check_claude_md.py (PR #76, Rex's review).

A claude-* run between two path separators skips only the unknown_model FAIL.
A superseded ID stays stale_model, and a known-not-adopted ID stays
unadopted_model, wherever it appears.

    python3 test_check_claude_md.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_claude_md as c  # noqa: E402

MODEL_CODES = {"stale_model", "unadopted_model", "unknown_model", "dated_model"}


def model_codes(line):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "CLAUDE.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
        result = c.check_file(path, [path])
    return sorted(f["code"] for f in result["findings"] if f["code"] in MODEL_CODES)


class PathSegment(unittest.TestCase):
    # Rex's table, with the outcome the narrowed rule must give.
    def test_directory_named_claude_md_is_not_a_model(self):
        self.assertEqual(model_codes("docs/claude-md/generation-plan.md"), [])

    def test_superseded_id_between_separators_stays_stale(self):
        self.assertEqual(model_codes("path a/claude-opus-4-8/ and"), ["stale_model"])
        self.assertEqual(model_codes("see /opt/claude-opus-4-8/run"), ["stale_model"])
        self.assertEqual(model_codes("a/claude-opus-4-8/b"), ["stale_model"])
        self.assertEqual(model_codes(r"a\claude-opus-4-8\b"), ["stale_model"])

    def test_unknown_id_between_separators_is_skipped(self):
        # claude-3-opus is in neither superseded nor known_not_adopted in
        # models.json, so between two separators it reads as a directory name.
        self.assertEqual(model_codes("models/claude-3-opus/x"), [])

    def test_known_not_adopted_between_separators_stays_warn(self):
        self.assertEqual(model_codes("a/claude-fable-5-1/b"), ["unadopted_model"])

    def test_one_sided_separator_is_still_checked(self):
        self.assertEqual(model_codes("anthropic/claude-3-opus"), ["unknown_model"])
        self.assertEqual(model_codes("claude-3-opus/x"), ["unknown_model"])
        self.assertEqual(model_codes("use claude-md here"), ["unknown_model"])

    def test_current_id_between_separators_is_clean(self):
        self.assertEqual(model_codes("a/claude-opus-5/b"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
