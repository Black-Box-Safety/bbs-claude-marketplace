#!/usr/bin/env python3
"""packet_profile.py — load, validate and resolve ca-form-filler packet profiles.

A profile describes one specific bid-packet PDF: how to recognise it, what its
pages hold, and which script fills it. They live in ../references/packets/ and
the contract they follow is documented in that directory's README.md. This
script is the machine-readable half of that contract.

Recognition runs on text extracted from the PDF, never on a filename and never
on a description, because a packet filled against the wrong map is a wrong
number on a binding bid. Where the evidence does not single out one profile this
refuses and says so; it never ranks or scores candidates.

Usage:
    python3 packet_profile.py --list
    python3 packet_profile.py --validate
    python3 packet_profile.py --recognize <text-file|->
    python3 packet_profile.py --recognize-pdf <packet.pdf>

Options:
    --profiles-dir DIR   read profiles from DIR instead of ../references/packets
    --json               machine-readable output

Exit 0 = the command succeeded (for --validate: every profile conforms).
Exit 1 = a failure, including an unresolvable recognition.
Exit 2 = a usage or environment problem.

Stdlib + PyYAML only, matching scripts/check_marketplace.py, so it runs wherever
the plugin is installed. Nothing here imports a PDF library: recognition takes
text, which is what makes it testable without a packet in hand.
"""
import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROFILES_DIR = os.path.join(SKILL_DIR, "references", "packets")

# The one value `rules:` may hold. A profile points at the shared rules; it does
# not carry its own copy and it does not point somewhere else.
RULES_POINTER = "${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md"

STATUSES = ("active", "stub")
FILL_MODES = ("scripted", "path-b")

# Files in the profiles directory that are not profiles.
NOT_A_PROFILE = {"README.md"}

# A profile records field IDs and page numbers. It must not restate a rule that
# ca-form-rules.md owns — that is AGENTS.md invariant 2, and a second copy of a
# signing rule is the copy that goes stale. These patterns are the shapes such a
# restatement takes in prose.
RULE_RESTATEMENT = [
    (re.compile(r"\bcan disqualify\b", re.I),
     "what disqualifies a bid is a rule; cite ca-form-rules.md instead of restating it"),
    (re.compile(r"\bleave (?:it |them |the )?(?:entirely )?blank\b", re.I),
     "what stays blank is a rule; name the fields and cite ca-form-rules.md"),
    (re.compile(r"\bnever varies by rep\b", re.I),
     "why a signer is fixed is a rule; name the signer and cite ca-form-rules.md"),
]


def _collapse(text):
    """Whitespace-collapsed, lower-cased text.

    A PDF text layer breaks lines wherever the layout did, so a marker that is
    one phrase on the page can arrive with a newline through it.
    """
    return " ".join(text.split()).lower()


class Profile(object):
    def __init__(self, path, meta, body):
        self.path = path
        self.meta = meta
        self.body = body
        self.stem = os.path.splitext(os.path.basename(path))[0]

    @property
    def packet_id(self):
        return self.meta.get("packet_id")

    @property
    def status(self):
        return self.meta.get("status")

    @property
    def recognize(self):
        r = self.meta.get("recognize")
        return r if isinstance(r, dict) else {}

    def markers(self, key):
        v = self.recognize.get(key) or []
        return [str(x) for x in v] if isinstance(v, list) else []

    @property
    def all_set(self):
        return frozenset(_collapse(m) for m in self.markers("all"))

    def matches(self, collapsed_text):
        """True if this profile's markers all hold against the packet text."""
        if not all(m in collapsed_text for m in self.all_set):
            return False
        any_markers = [_collapse(m) for m in self.markers("any")]
        if any_markers and not any(m in collapsed_text for m in any_markers):
            return False
        none_markers = [_collapse(m) for m in self.markers("none")]
        if any(m in collapsed_text for m in none_markers):
            return False
        return True


def _split_front_matter(text, path):
    if not text.startswith("---"):
        raise ValueError("no YAML front matter: the file does not open with `---`")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("front matter is not closed by a `---` line")
    raw = text[text.index("\n", 3) + 1:end + 1]
    body = text[end + len("\n---"):].lstrip("\n")
    meta = yaml.safe_load(raw)
    if not isinstance(meta, dict):
        raise ValueError("front matter did not parse as a mapping (quote a value "
                         "containing a colon, or use a >- block scalar)")
    return meta, body


def load_profiles(profiles_dir):
    """Return ([Profile], [error strings]). Every .md that is not README.md."""
    profiles, errors = [], []
    if not os.path.isdir(profiles_dir):
        return profiles, ["profiles directory not found: %s" % profiles_dir]
    for fn in sorted(os.listdir(profiles_dir)):
        if not fn.endswith(".md") or fn in NOT_A_PROFILE:
            continue
        path = os.path.join(profiles_dir, fn)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        try:
            meta, body = _split_front_matter(text, path)
        except (ValueError, yaml.YAMLError) as exc:
            errors.append("%s: %s" % (fn, exc))
            continue
        profiles.append(Profile(path, meta, body))
    return profiles, errors


def validate(profiles_dir):
    """Return a list of failure strings. Empty means every profile conforms."""
    profiles, failures = load_profiles(profiles_dir)
    failures = list(failures)
    by_id = {}

    for p in profiles:
        fn = os.path.basename(p.path)

        def fail(msg):
            failures.append("%s: %s" % (fn, msg))

        if not p.packet_id:
            fail("no packet_id")
        elif p.packet_id != p.stem:
            fail("packet_id %r != filename stem %r; the resolver and every "
                 "cross-reference key on the id" % (p.packet_id, p.stem))
        else:
            if p.packet_id in by_id:
                fail("duplicate packet_id %r" % p.packet_id)
            by_id[p.packet_id] = p

        for key in ("title", "revision", "recognition_source"):
            if not str(p.meta.get(key) or "").strip():
                fail("no %s" % key)

        if p.status not in STATUSES:
            fail("status must be one of %s, got %r" % (list(STATUSES), p.status))

        if p.meta.get("rules") != RULES_POINTER:
            fail("rules: must be exactly %r — a profile points at the shared rules, "
                 "it does not carry a copy and it does not point elsewhere"
                 % RULES_POINTER)

        if not isinstance(p.meta.get("recognize"), dict):
            fail("no recognize: block")
        else:
            for key in p.recognize:
                if key not in ("all", "any", "none"):
                    fail("unknown recognize key %r (all/any/none)" % key)
            for key in ("all", "any", "none"):
                v = p.recognize.get(key)
                if v is not None and not isinstance(v, list):
                    fail("recognize.%s must be a list" % key)
                for m in p.markers(key):
                    if not m.strip():
                        fail("recognize.%s holds an empty marker" % key)

        # A stub is inert by construction, not by convention.
        if p.status == "stub":
            if p.all_set or p.markers("any") or p.markers("none"):
                fail("status is stub but it declares recognition markers. A stub "
                     "must never be able to match — clear the markers or make it "
                     "active once they are read from a real packet")
        elif p.status == "active" and not p.all_set:
            fail("status is active but recognize.all is empty, so it would match "
                 "every packet. An active profile needs at least one grounded marker")

        fill = p.meta.get("fill")
        if not isinstance(fill, dict):
            fail("no fill: block")
        else:
            mode = fill.get("mode")
            if mode not in FILL_MODES:
                fail("fill.mode must be one of %s, got %r" % (list(FILL_MODES), mode))
            if mode == "scripted":
                for key in ("script", "inputs_template", "verify_script"):
                    relpath = fill.get(key)
                    if key == "script" and not relpath:
                        fail("fill.mode is scripted but there is no fill.script")
                    if relpath and not os.path.isfile(
                            os.path.join(SKILL_DIR, str(relpath))):
                        fail("fill.%s points at %r, which is not in the skill"
                             % (key, relpath))
            elif p.status == "active" and mode == "path-b":
                fail("an active profile with fill.mode path-b adds nothing the "
                     "no-match fallthrough does not already do")
            pages = fill.get("verify_pages")
            if pages is not None and not (isinstance(pages, list) and
                                          all(isinstance(n, int) for n in pages)):
                fail("fill.verify_pages must be a list of integers")

        for pat, why in RULE_RESTATEMENT:
            m = pat.search(p.body)
            if m:
                line = p.body[:m.start()].count("\n") + 1
                fail("body line %d restates a shared rule (%r) — %s"
                     % (line, m.group(0), why))

    # extends: must name a real profile, must not cycle, and once both ends are
    # active the specialisation has to be true rather than merely declared.
    for p in profiles:
        parent_id = p.meta.get("extends")
        if parent_id is None:
            continue
        fn = os.path.basename(p.path)
        if parent_id == p.packet_id:
            failures.append("%s: extends itself" % fn)
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            failures.append("%s: extends %r, which is not a profile here"
                            % (fn, parent_id))
            continue
        if parent.meta.get("extends") == p.packet_id:
            failures.append("%s: extends %r, which extends it back"
                            % (fn, parent_id))
            continue
        if p.status == "active" and parent.status == "active":
            if not (p.all_set > parent.all_set):
                failures.append(
                    "%s: extends %r but its recognize.all is not a strict superset "
                    "of it, so the two cannot resolve deterministically when both "
                    "match. Either widen this profile's markers or drop extends:"
                    % (fn, parent_id))
    return failures


class Ambiguous(Exception):
    def __init__(self, candidates):
        self.candidates = candidates
        Exception.__init__(self, "several profiles match and none subsumes the rest: "
                                 + ", ".join(sorted(c.packet_id for c in candidates)))


def recognize(text, profiles):
    """Return the matching active Profile, or None for the Path B fallthrough.

    Raises Ambiguous when several profiles match and no candidate's `all` set is
    a strict superset of every other's. Refusing is the point: choosing between
    two binding-document maps on anything less than the evidence is the failure
    this whole design exists to prevent.
    """
    collapsed = _collapse(text)
    hits = [p for p in profiles if p.status == "active" and p.matches(collapsed)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    winners = [a for a in hits
               if all(a is b or a.all_set > b.all_set for b in hits)]
    if len(winners) == 1:
        return winners[0]
    raise Ambiguous(hits)


def pdf_text(path):
    try:
        out = subprocess.run(["pdftotext", path, "-"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit("pdftotext not found. It ships with Poppler; install poppler-utils "
                 "(Linux), poppler (macOS brew), or the Poppler binaries the rep "
                 "setup script installs on Windows.")
    except subprocess.CalledProcessError as exc:
        sys.exit("pdftotext failed on %s: %s"
                 % (path, (exc.stderr or b"").decode("utf-8", "replace").strip()))
    return out.stdout.decode("utf-8", "replace")


def _shortest_path(path):
    """Skill-relative when the profile lives in the skill, absolute otherwise."""
    rel = os.path.relpath(path, SKILL_DIR)
    return path if rel.startswith(os.pardir) else rel


def _report(profile, as_json):
    if profile is None:
        payload = {"match": None,
                   "action": "path-b",
                   "why": "no active profile recognised this packet; use Path B, "
                          "the general map-and-fill path"}
    else:
        fill = profile.meta.get("fill") or {}
        payload = {"match": profile.packet_id,
                   "action": fill.get("mode"),
                   "title": profile.meta.get("title"),
                   "revision": profile.meta.get("revision"),
                   "profile": _shortest_path(profile.path),
                   "script": fill.get("script"),
                   "inputs_template": fill.get("inputs_template"),
                   "verify_script": fill.get("verify_script"),
                   "verify_pages": fill.get("verify_pages")}
    if as_json:
        print(json.dumps(payload, indent=2))
    elif profile is None:
        print("no match -> Path B (general map-and-fill)")
        print(payload["why"])
    else:
        print("match: %s — %s (%s)" % (payload["match"], payload["title"],
                                       payload["revision"]))
        print("profile: %s" % payload["profile"])
        print("fill:    %s" % (payload["script"] or payload["action"]))
        if payload.get("verify_pages"):
            print("verify:  %s pages %s" % (payload["verify_script"],
                                            " ".join(str(n) for n in
                                                     payload["verify_pages"])))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list profiles and their status")
    g.add_argument("--validate", action="store_true",
                   help="check every profile against the contract")
    g.add_argument("--recognize", metavar="TEXTFILE",
                   help="resolve against extracted packet text ('-' for stdin)")
    g.add_argument("--recognize-pdf", metavar="PDF",
                   help="pdftotext the packet, then resolve")
    ap.add_argument("--profiles-dir", default=DEFAULT_PROFILES_DIR)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.validate:
        failures = validate(args.profiles_dir)
        if args.json:
            print(json.dumps({"ok": not failures, "failures": failures}, indent=2))
        else:
            for f in failures:
                print("FAIL %s" % f)
            n, _ = load_profiles(args.profiles_dir)
            print("%d profile(s) · %d failure(s)" % (len(n), len(failures)))
        return 1 if failures else 0

    profiles, errors = load_profiles(args.profiles_dir)
    for e in errors:
        print("unreadable profile — %s" % e, file=sys.stderr)

    if args.list:
        rows = [(p.packet_id or "?", p.status or "?",
                 ((p.meta.get("fill") or {}).get("mode") or "?"),
                 ", ".join(p.markers("all")) or "(none)") for p in profiles]
        print("%-18s%-9s%-10s%s" % ("PACKET", "STATUS", "FILL", "REQUIRED MARKERS"))
        for r in rows:
            print("%-18s%-9s%-10s%s" % r)
        if errors:
            return 1
        return 0

    if args.recognize_pdf:
        text = pdf_text(args.recognize_pdf)
    elif args.recognize == "-":
        text = sys.stdin.read()
    else:
        with open(args.recognize, encoding="utf-8", errors="replace") as fh:
            text = fh.read()

    try:
        match = recognize(text, profiles)
    except Ambiguous as amb:
        print("REFUSED: %s" % amb, file=sys.stderr)
        print("Two maps cannot both be right for one PDF. Fix the markers so one "
              "profile subsumes the other, or so only one matches — do not pick.",
              file=sys.stderr)
        return 1
    _report(match, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
