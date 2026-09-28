#!/usr/bin/env python3
"""test_packet_profiles.py — the packet-profile contract, executed.

Run it:
    python3 test_packet_profiles.py

The load-bearing case is `test_third_profile_needs_no_skill_md_change`. The slice
that introduced profiles was required to show that adding a third packet takes no
edit to SKILL.md, so that claim is a test rather than a sentence: it writes a
third profile at test time, resolves a packet onto it, and asserts SKILL.md's
sha256 is byte-identical before and after and never mentions the new packet.

Everything here runs on text fixtures. **No real California form PDF exists in
this repo**, so nothing below has been run against a rendered packet — these
tests cover the contract and the resolver, not whether a marker really appears
in a packet's text layer. That verification needs a blank packet in hand.

Stdlib only, no pytest, so it runs wherever the plugin is installed.
"""
import hashlib
import io
import os
import shutil
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packet_profile import (  # noqa: E402
    Ambiguous, FrontMatterError, Malformed, SKILL_DIR, DEFAULT_PROFILES_DIR,
    load_profiles, parse_front_matter, recognize, validate,
    main as cli,   # aliased: this module has a main() of its own
)

SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")

# Text as `pdftotext` would hand it over: markers split across lines by the
# page layout, so a resolver that matched on raw substrings would miss them.
OBS_PACKET_TEXT = """
                       STATE OF CALIFORNIA
     DEPARTMENT OF CORRECTIONS AND REHABILITATION
              Request For Quote (RFQ) Packet
                            - B
                        OBS 4007(B)
                        Rev. 08/2025
...
OBS Line-Item Cost Worksheet
"""

UNRELATED_PACKET_TEXT = """
STATE OF CALIFORNIA - DEPARTMENT OF GENERAL SERVICES
PAYEE DATA RECORD  STD 204
DARFUR CONTRACTING ACT CERTIFICATION
"""


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _profile(packet_id, status="active", all_markers=(), extends=None, extra=""):
    lines = ["---", "packet_id: %s" % packet_id,
             'title: "test fixture %s"' % packet_id,
             'revision: "test"', "status: %s" % status]
    if extends:
        lines.append("extends: %s" % extends)
    lines.append("recognize:")
    lines.append("  all:%s" % ("" if all_markers else " []"))
    for m in all_markers:
        lines.append('    - "%s"' % m)
    lines += ["recognition_source: test fixture, not a real packet",
              "fill:",
              "  mode: %s" % ("scripted" if status == "active" else "path-b")]
    if status == "active":
        lines.append("  script: scripts/fill_obs_packet.py")
    lines += ["rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md",
              "---", "", "# test fixture", extra, ""]
    return "\n".join(lines)


def _sandbox(tmp, *files):
    """A profiles dir holding the shipped profiles plus whatever is passed in."""
    d = os.path.join(tmp, "packets")
    shutil.copytree(DEFAULT_PROFILES_DIR, d)
    for name, text in files:
        io.open(os.path.join(d, name), "w", encoding="utf-8").write(text)
    return d


# --------------------------------------------------------------------------
# The shipped profiles
# --------------------------------------------------------------------------

def test_shipped_profiles_conform():
    failures = validate(DEFAULT_PROFILES_DIR)
    assert not failures, "shipped profiles fail the contract:\n  " + "\n  ".join(failures)


def test_obs_packet_resolves_to_the_obs_profile():
    profiles, errors = load_profiles(DEFAULT_PROFILES_DIR)
    assert not errors, errors
    match = recognize(OBS_PACKET_TEXT, profiles)
    assert match is not None, "OBS packet text matched no profile"
    assert match.packet_id == "obs-4007b", match.packet_id
    fill = match.meta["fill"]
    assert fill["script"] == "scripts/fill_obs_packet.py", fill
    assert fill["verify_pages"] == [2, 12, 16, 21, 24], fill


def test_unknown_packet_falls_through_to_path_b():
    profiles, _ = load_profiles(DEFAULT_PROFILES_DIR)
    assert recognize(UNRELATED_PACKET_TEXT, profiles) is None


def test_stubs_are_inert():
    """A stub must never match, whatever the packet says."""
    profiles, _ = load_profiles(DEFAULT_PROFILES_DIR)
    stubs = [p for p in profiles if p.status == "stub"]
    assert stubs, "expected at least one stub profile"
    for text in (OBS_PACKET_TEXT, UNRELATED_PACKET_TEXT, "", "DSH Atascadero"):
        try:
            match = recognize(text, profiles)
        except Ambiguous as exc:
            raise AssertionError("a stub took part in a match: %s" % exc)
        assert match is None or match.status == "active", match.packet_id


# --------------------------------------------------------------------------
# The contract's failure modes
# --------------------------------------------------------------------------

def test_stub_declaring_markers_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("bad.md", _profile("bad", status="stub",
                                              all_markers=["ANYTHING"])))
        failures = validate(d)
        assert any("stub but it declares recognition markers" in f for f in failures), \
            failures


def test_active_profile_with_no_markers_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("greedy.md", _profile("greedy", all_markers=[])))
        failures = validate(d)
        assert any("recognize.all is empty" in f for f in failures), failures


def test_packet_id_must_match_filename():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("named-one.md", _profile("named-two", all_markers=["X"])))
        failures = validate(d)
        assert any("!= filename stem" in f for f in failures), failures


def test_rules_pointer_must_be_the_shared_file():
    with tempfile.TemporaryDirectory() as tmp:
        text = _profile("local", all_markers=["X"]).replace(
            "rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md",
            "rules: ./my-own-rules.md")
        d = _sandbox(tmp, ("local.md", text))
        failures = validate(d)
        assert any("points at the shared rules" in f for f in failures), failures


def test_body_restating_a_shared_rule_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        text = _profile("restater", all_markers=["X"],
                        extra="A missing CalRecycle 74 can disqualify the bid.")
        d = _sandbox(tmp, ("restater.md", text))
        failures = validate(d)
        assert any("restates a shared rule" in f for f in failures), failures


def test_ambiguous_match_refuses_rather_than_picking():
    """Two unrelated profiles matching one packet is a refusal, not a ranking."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp,
                     ("rival-a.md", _profile("rival-a", all_markers=["OBS 4007(B)"])),
                     ("rival-b.md", _profile("rival-b",
                                             all_markers=["Line-Item Cost Worksheet"])))
        profiles, _ = load_profiles(d)
        try:
            match = recognize(OBS_PACKET_TEXT, profiles)
        except Ambiguous as exc:
            ids = set(exc.candidates[i].packet_id for i in range(len(exc.candidates)))
            assert {"rival-a", "rival-b", "obs-4007b"} <= ids, ids
            return
        raise AssertionError("resolver picked %r instead of refusing" % match.packet_id)


def test_specialisation_beats_the_general_profile():
    """A strict superset of markers wins deterministically — no scoring."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp,
                     ("gen.md", _profile("gen", all_markers=["Request For Quote"])),
                     ("spec.md", _profile("spec", extends="gen",
                                          all_markers=["Request For Quote",
                                                       "OBS 4007(B)"])))
        profiles, _ = load_profiles(d)
        assert not validate(d), validate(d)
        # obs-4007b also matches this text, and does not subsume `spec`, so the
        # fixture is checked on its own two profiles.
        pair = [p for p in profiles if p.packet_id in ("gen", "spec")]
        assert recognize(OBS_PACKET_TEXT, pair).packet_id == "spec"


def test_declared_specialisation_must_actually_subsume():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp,
                     ("gen.md", _profile("gen", all_markers=["Request For Quote"])),
                     ("spec.md", _profile("spec", extends="gen",
                                          all_markers=["OBS 4007(B)"])))
        failures = validate(d)
        assert any("not a strict superset" in f for f in failures), failures


def test_extends_must_name_a_real_profile():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("orphan.md", _profile("orphan", all_markers=["X"],
                                                 extends="nobody")))
        failures = validate(d)
        assert any("which is not a profile here" in f for f in failures), failures


# --------------------------------------------------------------------------
# The guard sits on the path the skill uses, not only under --validate
# --------------------------------------------------------------------------

GREEDY = """---
packet_id: greedy
title: the ordinary YAML slip
revision: "test"
status: active
recognize:
  all: "SOME MARKER"
recognition_source: test fixture, not a real packet
fill:
  mode: scripted
  script: scripts/fill_obs_packet.py
rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md
---

# greedy
"""


def test_a_scalar_where_a_marker_list_belongs_refuses_recognition():
    """`all: "MARKER"` is no markers at all, and no markers matches everything.

    --validate caught this from the start. recognize() did not, and --validate
    is not what SKILL.md tells anyone to run, so the one control that makes
    routing deterministic sat off the path the skill uses.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("greedy.md", GREEDY))
        profiles, errors = load_profiles(d)
        assert not errors, errors
        try:
            match = recognize(UNRELATED_PACKET_TEXT, profiles)
        except Malformed as exc:
            assert any("must be a list" in f for f in exc.details), exc.details
            return
        raise AssertionError("an unrelated STD 204 resolved to %r" % match.packet_id)


def test_recognize_exits_1_on_a_malformed_profile():
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("greedy.md", GREEDY))
        text = os.path.join(tmp, "packet.txt")
        io.open(text, "w", encoding="utf-8").write(UNRELATED_PACKET_TEXT)
        assert cli(["--profiles-dir", d, "--recognize", text]) == 1


def test_an_unparseable_profile_refuses_rather_than_reporting_no_match():
    """The OBS packet must not be hand-mapped because its profile lost a quote.

    An unquoted colon in `title:` used to drop the file, leave `no match ->
    Path B` on stdout and exit 0 — routing the one packet with a verified
    scripted fill into the slower, more error-prone path with nobody told.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp)
        broken = os.path.join(d, "obs-4007b.md")
        was = io.open(broken, encoding="utf-8").read()
        io.open(broken, "w", encoding="utf-8").write(was.replace(
            'title: CDCR "Request For Quote (RFQ) Packet – B", OBS 4007(B)',
            "title: CDCR Request For Quote: Packet B, OBS 4007(B)"))

        profiles, errors = load_profiles(d)
        assert errors and "obs-4007b.md" in errors[0], errors
        assert recognize(OBS_PACKET_TEXT, profiles) is None, (
            "the fixture is wrong: the remaining profiles should not match, "
            "which is exactly why a clean `no match` was so misleading")

        text = os.path.join(tmp, "packet.txt")
        io.open(text, "w", encoding="utf-8").write(OBS_PACKET_TEXT)
        assert cli(["--profiles-dir", d, "--recognize", text]) == 1


def test_a_missing_text_file_is_an_environment_error_not_a_refusal():
    """Exit 2 is reserved for a broken machine; 1 must stay unambiguous."""
    assert cli(["--recognize", os.path.join(SKILL_DIR, "no-such-file.txt")]) == 2


def test_extends_cycle_longer_than_two_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "cycle")
        os.makedirs(d)
        for this, parent in (("a", "b"), ("b", "c"), ("c", "a")):
            io.open(os.path.join(d, "%s.md" % this), "w", encoding="utf-8").write(
                _profile(this, status="stub", extends=parent))
        failures = validate(d)
        assert any("closes a cycle" in f for f in failures), failures


def test_duplicate_packet_id_is_reachable():
    """The guard used to sit in the else: of `packet_id != stem`, where two
    files in one directory can never both land."""
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "dupes")
        os.makedirs(d)
        for fn in ("one.md", "two.md"):
            io.open(os.path.join(d, fn), "w", encoding="utf-8").write(
                _profile("shared", all_markers=["X"]))
        failures = validate(d)
        assert any("duplicate packet_id" in f for f in failures), failures


def test_a_warning_about_a_rule_is_not_a_restatement():
    """README tells an author to write this sentence; it must not FAIL.

    Without counter-example awareness the only fix available to them is
    deleting the warning, which AGENTS.md names as the way a checker gets
    ignored.
    """
    warning = ('Do not write "leave it blank" into this profile — that is a '
               "rule and it belongs in ca-form-rules.md.")
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("warner.md", _profile("warner", all_markers=["X"],
                                                 extra=warning)))
        failures = validate(d)
        assert not failures, failures


def test_the_obs_signer_paraphrase_would_now_be_caught():
    """The exact prose this profile shipped with, which the first validator missed."""
    paraphrase = (
        "## The two-signer rule (most important)\n\n"
        "- **Rep signs** the bidder/certification lines (OBS 4007(B), Darfur).\n"
        "- **Jackson Dalton signs** the ownership lines. These are tied to "
        "ownership of the certified DVBE, not to who quoted.\n")
    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("paraphraser.md", _profile("paraphraser",
                                                      all_markers=["X"],
                                                      extra=paraphrase)))
        failures = validate(d)
        assert any("restates a shared rule" in f for f in failures), failures


# --------------------------------------------------------------------------
# Front matter, parsed without PyYAML
# --------------------------------------------------------------------------

def test_front_matter_parses_the_documented_shapes():
    meta = parse_front_matter(
        'packet_id: demo\n'
        'title: "a: colon, quoted"\n'
        'revision: Rev. 08/2025      # trailing comment\n'
        'status: active\n'
        'recognize:\n'
        '  all:\n'
        '    - "one"\n'
        '    - two\n'
        '  none: []\n'
        'recognition_source: >-\n'
        '  folded over\n'
        '  two lines\n'
        'fill:\n'
        '  mode: scripted\n'
        '  verify_pages: [2, 12, 16]\n')
    assert meta["title"] == "a: colon, quoted", meta["title"]
    assert meta["revision"] == "Rev. 08/2025", meta["revision"]
    assert meta["recognize"] == {"all": ["one", "two"], "none": []}, meta["recognize"]
    assert meta["recognition_source"] == "folded over two lines"
    assert meta["fill"]["verify_pages"] == [2, 12, 16], meta["fill"]


def test_front_matter_refuses_an_unquoted_colon():
    try:
        parse_front_matter("title: CDCR Request For Quote: Packet B\n")
    except FrontMatterError as exc:
        assert "unquoted colon" in str(exc), exc
        return
    raise AssertionError("an unquoted colon parsed as something")


def test_front_matter_agrees_with_pyyaml_on_every_shipped_profile():
    """Belt and braces while both parsers are around. Skipped without PyYAML.

    The stdlib parser exists so Path A step 1 needs nothing installed; this
    asserts it did not change what the shipped profiles mean while doing so.
    """
    try:
        import yaml
    except ImportError:
        return
    for p in sorted(os.listdir(DEFAULT_PROFILES_DIR)):
        if not p.endswith(".md") or p == "README.md":
            continue
        text = io.open(os.path.join(DEFAULT_PROFILES_DIR, p), encoding="utf-8").read()
        raw = text[text.index("\n", 3) + 1:text.find("\n---", 3) + 1]
        assert parse_front_matter(raw) == yaml.safe_load(raw), p


# --------------------------------------------------------------------------
# The done condition
# --------------------------------------------------------------------------

def test_third_profile_needs_no_skill_md_change():
    """Adding a packet is one file in references/packets/ and nothing else.

    Asserted three ways: SKILL.md is byte-identical across the whole exercise,
    it never names the new packet, and the resolver still routes a packet onto
    it — including the fill script and verify pages the skill would then run.
    """
    before = _sha256(SKILL_MD)
    skill_text = io.open(SKILL_MD, encoding="utf-8").read()

    third = _profile("dsh-metro-fixture", all_markers=["DSH-METRO-FIXTURE-MARKER"])
    packet_text = "STATE OF CALIFORNIA\nDSH-METRO-FIXTURE-MARKER\nbid packet\n"

    with tempfile.TemporaryDirectory() as tmp:
        d = _sandbox(tmp, ("dsh-metro-fixture.md", third))

        failures = validate(d)
        assert not failures, failures

        profiles, errors = load_profiles(d)
        assert not errors, errors
        assert len(profiles) == 4, [p.packet_id for p in profiles]

        match = recognize(packet_text, profiles)
        assert match is not None and match.packet_id == "dsh-metro-fixture", match
        assert match.meta["fill"]["script"] == "scripts/fill_obs_packet.py"

        # The packets that already worked still work, unchanged.
        assert recognize(OBS_PACKET_TEXT, profiles).packet_id == "obs-4007b"
        assert recognize(UNRELATED_PACKET_TEXT, profiles) is None

    assert "dsh-metro-fixture" not in skill_text, \
        "SKILL.md names the new packet; the profile set is not self-describing"
    assert _sha256(SKILL_MD) == before, "SKILL.md changed during the test"


def test_skill_md_hard_codes_no_profile_filename():
    """SKILL.md may name the worked example in prose, never a profile path."""
    skill_text = io.open(SKILL_MD, encoding="utf-8").read()
    for p, _ in [(x, None) for x in load_profiles(DEFAULT_PROFILES_DIR)[0]]:
        assert "packets/%s.md" % p.packet_id not in skill_text, (
            "SKILL.md hard-codes references/packets/%s.md; the profile set is "
            "discovered, not listed" % p.packet_id)


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
    if failed:
        print("\nNOTE: these are text fixtures. No real CA form PDF is available "
              "here, so none of this is evidence about a rendered packet.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
