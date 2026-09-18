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
Exit 2 = a usage or environment problem: a missing input file, or pdftotext
         absent or failing. Distinct from 1 so a refusal is never mistaken for
         a broken machine, or the reverse.

The recognition commands refuse rather than degrade. A profile directory that
does not parse, or whose `recognize:` block is malformed, cannot be resolved
against: the earlier behaviour dropped the bad file and reported a clean
`no match -> Path B`, which routes a packet that *does* have a verified scripted
fill into the slower hand-mapped path with nobody told. Recognition is only
deterministic if the check that makes it so runs on the path the skill uses.

Stdlib only — no PyYAML, no PDF library. The front matter this reads is a small
fixed shape, parsed below by `parse_front_matter`, so step 1 of Path A never
fails on a rep machine for want of an install. Nothing here imports a PDF
library either: recognition takes text, which is what makes it testable without
a packet in hand.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROFILES_DIR = os.path.join(SKILL_DIR, "references", "packets")

# The one value `rules:` may hold. A profile points at the shared rules; it does
# not carry its own copy and it does not point somewhere else.
RULES_POINTER = "${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md"

STATUSES = ("active", "stub")
FILL_MODES = ("scripted", "path-b")

# Files in the profiles directory that are not profiles.
NOT_A_PROFILE = {"README.md"}


# --------------------------------------------------------------------------
# Front matter
#
# A deliberately small, strict parser for the shape references/packets/README.md
# documents: scalars, `>-` / `|` block scalars, one level of nested mapping,
# block and flow sequences. It is strict on purpose — anything it does not
# recognise raises rather than being guessed at, because a front matter that
# half-parses is how a profile silently acquires the wrong markers.
#
# It replaces a PyYAML dependency. Path A step 1 is now mandatory and runs on a
# rep machine that has `node pdftotext pandoc uv` from bbs-checkup and nothing
# else; an ImportError there would give the rep none of the three documented
# outcomes.
# --------------------------------------------------------------------------

class FrontMatterError(ValueError):
    """The front matter does not parse. Always names the line."""


_INT = re.compile(r"[+-]?\d+$")


def _strip_comment(s):
    """Drop a trailing ` # comment` from an unquoted scalar."""
    if s.startswith("#"):
        return ""
    i = s.find(" #")
    return s[:i].rstrip() if i != -1 else s


def _scalar(raw, line):
    s = raw.strip()
    if not s:
        return None
    if s[0] in "\"'":
        quote = s[0]
        out, i, closed = [], 1, False
        while i < len(s):
            ch = s[i]
            if quote == '"' and ch == "\\" and i + 1 < len(s):
                out.append({"n": "\n", "t": "\t"}.get(s[i + 1], s[i + 1]))
                i += 2
                continue
            if ch == quote:
                closed = True
                i += 1
                break
            out.append(ch)
            i += 1
        if not closed:
            raise FrontMatterError("line %d: unterminated %s quote" % (line, quote))
        rest = s[i:].strip()
        if rest and not rest.startswith("#"):
            raise FrontMatterError("line %d: unexpected text after the quoted "
                                   "value: %r" % (line, rest))
        return "".join(out)
    if s[0] in "[{&*!|>":
        raise FrontMatterError(
            "line %d: %r is not a shape a profile may use. The contract is "
            "scalars, quoted strings, `>-` block scalars and lists; see "
            "references/packets/README.md" % (line, s[0]))
    s = _strip_comment(s)
    if not s:
        return None
    if ": " in s or s.endswith(":"):
        raise FrontMatterError(
            "line %d: the value %r holds an unquoted colon, so it does not parse "
            "as one value. Quote it, or use a >- block scalar" % (line, s))
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~"):
        return None
    if _INT.match(s):
        return int(s)
    return s


def _flow_seq(raw, line):
    """`[a, b]` on one line. Nested collections are not part of the contract."""
    s = raw.strip()
    i, depth, quote = 0, 0, None
    while i < len(s):
        ch = s[i]
        if quote:
            if quote == '"' and ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                break
        i += 1
    if depth != 0:
        raise FrontMatterError("line %d: the list is never closed by `]`" % line)
    rest = s[i + 1:].strip()
    if rest and not rest.startswith("#"):
        raise FrontMatterError("line %d: unexpected text after the list: %r"
                               % (line, rest))
    items, buf, quote = [], "", None
    for ch in s[1:i]:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf += ch
            continue
        if ch == ",":
            items.append(buf)
            buf = ""
            continue
        buf += ch
    items.append(buf)
    return [_scalar(it, line) for it in items if it.strip()]


def _indent(text):
    return len(text) - len(text.lstrip(" "))


def _skippable(text):
    s = text.strip()
    return not s or s.startswith("#")


def _next_content(lines, i):
    while i < len(lines) and _skippable(lines[i][1]):
        i += 1
    return i


def _block_scalar(lines, i, indent, marker):
    """`>-`, `>`, `|`, `|-` … everything more deeply indented than the key."""
    folded = marker[0] == ">"
    chomp = marker[1:2]
    parts = []
    while i < len(lines):
        text = lines[i][1]
        if text.strip() and _indent(text) <= indent:
            break
        parts.append(text.strip())
        i += 1
    while parts and not parts[-1]:
        parts.pop()
    if folded:
        chunks, run = [], []
        for p in parts:
            if p:
                run.append(p)
            else:
                chunks.append(" ".join(run))
                run = []
        chunks.append(" ".join(run))
        value = "\n".join(chunks)
    else:
        value = "\n".join(parts)
    if chomp != "-":
        value += "\n"
    return value, i


def _sequence(lines, i, indent):
    out = []
    while i < len(lines):
        lineno, text = lines[i]
        if _skippable(text):
            i += 1
            continue
        if _indent(text) < indent:
            break
        if _indent(text) > indent:
            raise FrontMatterError("line %d: this list item is indented further "
                                   "than the one above it" % lineno)
        s = text.strip()
        if not s.startswith("-"):
            break
        item = s[1:].strip()
        if not item:
            raise FrontMatterError("line %d: empty list item" % lineno)
        out.append(_flow_seq(item, lineno) if item.startswith("[")
                   else _scalar(item, lineno))
        i += 1
    return out, i


def _mapping(lines, i, indent):
    out = {}
    while i < len(lines):
        lineno, text = lines[i]
        if _skippable(text):
            i += 1
            continue
        if _indent(text) < indent:
            break
        if _indent(text) > indent:
            raise FrontMatterError("line %d: unexpected indentation; `%s` does "
                                   "not line up with the keys above it"
                                   % (lineno, text.strip()[:40]))
        s = text.strip()
        if s.startswith("- "):
            raise FrontMatterError("line %d: a list item where a `key: value` "
                                   "was expected" % lineno)
        key, sep, rest = s.partition(":")
        key = key.strip()
        if not sep or not key or " " in key:
            raise FrontMatterError("line %d: not a `key: value` line — %r"
                                   % (lineno, s[:60]))
        if key in out:
            raise FrontMatterError("line %d: duplicate key %r; the second one "
                                   "silently wins" % (lineno, key))
        rest = rest.strip()
        i += 1
        if rest in (">", ">-", ">+", "|", "|-", "|+"):
            value, i = _block_scalar(lines, i, indent, rest)
        elif rest.startswith("["):
            value = _flow_seq(rest, lineno)
        elif rest and not rest.startswith("#"):
            value = _scalar(rest, lineno)
        else:
            nxt = _next_content(lines, i)
            if nxt < len(lines) and _indent(lines[nxt][1]) > indent:
                child = _indent(lines[nxt][1])
                if lines[nxt][1].strip().startswith("-"):
                    value, i = _sequence(lines, nxt, child)
                else:
                    value, i = _mapping(lines, nxt, child)
            else:
                value = None
        out[key] = value
    return out, i


def parse_front_matter(raw, first_line=1):
    """Parse the front-matter block into a dict. Raises FrontMatterError."""
    lines = []
    for n, text in enumerate(raw.splitlines()):
        if "\t" in text[:len(text) - len(text.lstrip())]:
            raise FrontMatterError("line %d: indented with a tab; YAML front "
                                   "matter must use spaces" % (n + first_line))
        lines.append((n + first_line, text))
    meta, i = _mapping(lines, 0, 0)
    i = _next_content(lines, i)
    if i < len(lines):
        raise FrontMatterError("line %d: trailing content the front matter "
                               "contract has no shape for" % lines[i][0])
    return meta


# --------------------------------------------------------------------------
# Rule restatement
# --------------------------------------------------------------------------

# A profile records field IDs and page numbers. It must not restate a rule that
# ca-form-rules.md owns — that is AGENTS.md invariant 2, and a second copy of a
# signing rule is the copy that goes stale. These patterns are the shapes such a
# restatement takes in prose. Markdown emphasis is allowed to sit inside them
# ("**Rep signs** the bidder lines"), which is how the OBS profile's own
# paraphrase escaped the first version of this list.
RULE_RESTATEMENT = [
    (re.compile(r"\bcan disqualify\b", re.I),
     "what disqualifies a bid is a rule; cite ca-form-rules.md instead of restating it"),
    (re.compile(r"\bleave (?:it |them |the )?(?:entirely )?blank\b", re.I),
     "what stays blank is a rule; name the fields and cite ca-form-rules.md"),
    (re.compile(r"\b(?:intentionally|deliberately) left blank\b", re.I),
     "what stays blank is a rule; name the fields and page, and cite ca-form-rules.md"),
    (re.compile(r"\bnever varies by rep\b", re.I),
     "why a signer is fixed is a rule; name the signer and cite ca-form-rules.md"),
    (re.compile(r"\btwo[-\s]signer rule\b", re.I),
     "the two-signer rule is ca-form-rules.md's; the page table's signer column "
     "names the signer, and that is all a profile may say about it"),
    (re.compile(r"\bsigns?[*_\s]+the\b[^.\n]{0,48}\blines?\b", re.I),
     "which lines a person signs is a rule; the page table's signer column names "
     "the signer per page, and ca-form-rules.md owns the rest"),
    (re.compile(r"\btied to (?:the |who )?own(?:s|er|ership)\b", re.I),
     "why a signer is who they are is a rule; cite ca-form-rules.md"),
    (re.compile(r"\b(?:not|rather than|never) (?:to )?who quoted\b", re.I),
     "why a signer is who they are is a rule; cite ca-form-rules.md"),
]

# A line that names a bad value in order to warn about it is correct content,
# not a defect — AGENTS.md requires every check here to know the difference, or
# the checker flags its own fixes and gets ignored. README.md tells an author to
# write exactly such a warning ("put it in ca-form-rules.md instead and cite
# it"), so without this the only fix available to them is deleting the warning.
#
# Deliberately a local copy of scripts/check_marketplace.py's shape rather than
# an import: that script is not shipped inside the plugin, and a skill whose
# validator only runs from a repo checkout is a validator a rep never runs.
COUNTER_EXAMPLE = re.compile(
    r"(\bca-form-rules\.md|\bnever\b|\bcounter-example|\brather than\b|"
    r"\binstead\b|\bbelongs? in\b|\blives? (?:once )?in\b|\bowns?\b|\bowned by\b|"
    r"\bcite[sd]?\b|\bcitation\b|\bis a rule\b|\bare rules\b|"
    r"\b(?:do not|don't|does not|doesn't|must not|cannot|can't)\s+"
    r"(?:write|restate|copy|repeat|put|state|re-?key|duplicate|record|carry|say))",
    re.I)

CONTEXT_LINES = 2
PROXIMITY = 200


def _collapse_indexed(s):
    """Whitespace-collapsed copy of s, plus an orig index -> collapsed index map."""
    out, pos, prev_space = [], [0] * (len(s) + 1), False
    for i, ch in enumerate(s):
        pos[i] = len(out)
        if ch.isspace():
            if not prev_space:
                out.append(" ")
            prev_space = True
        else:
            out.append(ch)
            prev_space = False
    pos[len(s)] = len(out)
    return "".join(out), pos


def is_counter_example(text, pos):
    """True if the match sits in prose that is warning about the value.

    A few lines either side, whitespace-collapsed because the qualifying phrase
    routinely wraps, and the phrase must land within PROXIMITY characters of the
    match so a qualifier from an unrelated sentence does not exempt it.
    """
    lines = text.splitlines(keepends=True)
    idx = text[:pos].count("\n")
    lo = max(0, idx - CONTEXT_LINES)
    hi = min(len(lines), idx + CONTEXT_LINES + 1)
    start = sum(len(ln) for ln in lines[:lo])
    window = text[start:start + sum(len(ln) for ln in lines[lo:hi])]
    collapsed, cmap = _collapse_indexed(window)
    here = cmap[min(max(pos - start, 0), len(window))]
    for m in COUNTER_EXAMPLE.finditer(collapsed):
        if m.end() <= here:
            dist = here - m.end()
        elif m.start() >= here:
            dist = m.start() - here
        else:
            dist = 0
        if dist <= PROXIMITY:
            return True
    return False


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
        raise FrontMatterError("no YAML front matter: the file does not open with `---`")
    end = text.find("\n---", 3)
    if end == -1:
        raise FrontMatterError("front matter is not closed by a `---` line")
    opens = text.index("\n", 3) + 1
    raw = text[opens:end + 1]
    body = text[end + len("\n---"):].lstrip("\n")
    meta = parse_front_matter(raw, first_line=text[:opens].count("\n") + 1)
    if not isinstance(meta, dict) or not meta:
        raise FrontMatterError("front matter did not parse as a mapping (quote a "
                               "value containing a colon, or use a >- block scalar)")
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
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            meta, body = _split_front_matter(text, path)
        except (OSError, ValueError) as exc:
            errors.append("%s: %s" % (fn, exc))
            continue
        profiles.append(Profile(path, meta, body))
    return profiles, errors


def recognition_faults(profile):
    """Faults that make one profile unsafe to resolve a real packet against.

    Split out of validate() because recognize() runs it too. The guard has to
    sit on the path the skill actually uses: a malformed `recognize:` block —
    `all: "MARKER"`, a scalar where a one-element list belongs, the ordinary
    YAML slip — reads as *no* markers, and an `all()` over no markers is True
    for every packet. Checking that only under --validate left the one control
    that makes routing deterministic off the path SKILL.md tells anyone to run.
    """
    faults = []
    fn = os.path.basename(profile.path)

    def fail(msg):
        faults.append("%s: %s" % (fn, msg))

    if profile.status not in STATUSES:
        fail("status must be one of %s, got %r" % (list(STATUSES), profile.status))
    raw = profile.meta.get("recognize")
    if not isinstance(raw, dict):
        fail("no recognize: block; it must be a mapping of all/any/none")
        return faults
    for key in raw:
        if key not in ("all", "any", "none"):
            fail("unknown recognize key %r (all/any/none). A misspelled key is "
                 "read as no markers at all" % key)
    for key in ("all", "any", "none"):
        v = raw.get(key)
        if v is None:
            continue
        if not isinstance(v, list):
            fail("recognize.%s must be a list, got %s. A bare string reads as no "
                 "markers, which makes an active profile match every packet"
                 % (key, type(v).__name__))
            continue
        for m in v:
            if not str(m).strip():
                fail("recognize.%s holds an empty marker" % key)

    if profile.status == "stub":
        if profile.all_set or profile.markers("any") or profile.markers("none"):
            fail("status is stub but it declares recognition markers. A stub "
                 "must never be able to match — clear the markers or make it "
                 "active once they are read from a real packet")
    elif profile.status == "active" and not profile.all_set:
        fail("status is active but recognize.all is empty, so it would match "
             "every packet. An active profile needs at least one grounded marker")
    return faults


def _extends_cycle(profile, by_id):
    """The chain of packet_ids if extends: closes a loop, else None.

    Self-reference and a direct a->b->a were the only two the first version
    caught, while the comment claimed "must not cycle"; a->b->c->a validated
    clean and then looped whoever walked it.
    """
    seen, chain, cur = set(), [], profile
    while cur is not None:
        if cur.packet_id in seen:
            return chain + [cur.packet_id]
        seen.add(cur.packet_id)
        chain.append(cur.packet_id)
        cur = by_id.get(cur.meta.get("extends"))
    return None


def validate(profiles_dir):
    """Return a list of failure strings. Empty means every profile conforms."""
    profiles, failures = load_profiles(profiles_dir)
    failures = list(failures)
    by_id = {}

    # Indexed first and separately from the stem check: folded into its `else`,
    # the duplicate guard could never fire, because two files in one directory
    # cannot share a stem and packet_id had already been forced to equal it.
    for p in profiles:
        if not p.packet_id:
            continue
        if p.packet_id in by_id:
            failures.append("%s: duplicate packet_id %r, already declared by %s"
                            % (os.path.basename(p.path), p.packet_id,
                               os.path.basename(by_id[p.packet_id].path)))
            continue
        by_id[p.packet_id] = p

    for p in profiles:
        fn = os.path.basename(p.path)

        def fail(msg):
            failures.append("%s: %s" % (fn, msg))

        if not p.packet_id:
            fail("no packet_id")
        elif p.packet_id != p.stem:
            fail("packet_id %r != filename stem %r; the resolver and every "
                 "cross-reference key on the id" % (p.packet_id, p.stem))

        for key in ("title", "revision", "recognition_source"):
            if not str(p.meta.get(key) or "").strip():
                fail("no %s" % key)

        if p.meta.get("rules") != RULES_POINTER:
            fail("rules: must be exactly %r — a profile points at the shared rules, "
                 "it does not carry a copy and it does not point elsewhere"
                 % RULES_POINTER)

        failures.extend(recognition_faults(p))

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
            for m in pat.finditer(p.body):
                if is_counter_example(p.body, m.start()):
                    continue
                line = p.body[:m.start()].count("\n") + 1
                fail("body line %d restates a shared rule (%r) — %s"
                     % (line, m.group(0), why))
                break

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
        cycle = _extends_cycle(p, by_id)
        if cycle:
            failures.append("%s: extends: closes a cycle (%s). A specialisation "
                            "chain has to end somewhere" % (fn, " -> ".join(cycle)))
            continue
        if p.status == "active" and parent.status == "active":
            if not (p.all_set > parent.all_set):
                failures.append(
                    "%s: extends %r but its recognize.all is not a strict superset "
                    "of it, so the two cannot resolve deterministically when both "
                    "match. Either widen this profile's markers or drop extends:"
                    % (fn, parent_id))
    return failures


class Refusal(Exception):
    """Recognition will not answer. Never a guess, never a silent fallthrough."""
    reason = "refused"

    def __init__(self, message, details=()):
        self.details = list(details)
        Exception.__init__(self, message)


class Ambiguous(Refusal):
    reason = "ambiguous"

    def __init__(self, candidates):
        self.candidates = candidates
        ids = sorted(c.packet_id for c in candidates)
        Refusal.__init__(self, "several profiles match and none subsumes the rest: "
                               + ", ".join(ids), ids)


class Malformed(Refusal):
    reason = "malformed-profiles"

    def __init__(self, faults):
        Refusal.__init__(self, "the profile set does not conform, so no resolution "
                               "from it can be trusted", faults)


def recognize(text, profiles):
    """Return the matching active Profile, or None for the Path B fallthrough.

    Raises Malformed when any profile's recognition block breaks the contract,
    and Ambiguous when several profiles match and no candidate's `all` set is a
    strict superset of every other's. Refusing is the point: choosing between
    two binding-document maps on anything less than the evidence is the failure
    this whole design exists to prevent.

    Every profile is checked, not only the active ones. A stub's `status:` is
    itself part of what makes it inert, so a stub that does not conform is not
    evidence that it is safely ignored.
    """
    faults = []
    for p in profiles:
        faults.extend(recognition_faults(p))
    if faults:
        raise Malformed(faults)
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


class Environment(Exception):
    """A broken machine or a missing input — exit 2, never confusable with a refusal."""


def pdf_text(path):
    try:
        out = subprocess.run(["pdftotext", path, "-"], capture_output=True, check=True)
    except FileNotFoundError:
        raise Environment("pdftotext not found. It ships with Poppler; install "
                          "poppler-utils (Linux), poppler (macOS brew), or the "
                          "Poppler binaries the rep setup script installs on Windows.")
    except subprocess.CalledProcessError as exc:
        raise Environment("pdftotext failed on %s: %s"
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


REFUSAL_ADVICE = {
    "ambiguous":
        "Two maps cannot both be right for one PDF. Fix the markers so one "
        "profile subsumes the other, or so only one matches — do not pick.",
    "malformed-profiles":
        "Fix the profile, then re-run. Do not fall back to Path B to get moving: "
        "a packet that has a verified scripted fill would be hand-mapped instead, "
        "which is the slower and more error-prone path, and nobody would be told.",
    "unreadable-profiles":
        "A profile that does not parse is not a profile that does not apply. Fix "
        "the front matter — an unquoted colon is the usual cause — and re-run.",
}


def _refuse(reason, message, details, as_json):
    """Print a refusal the same way whatever caused it. Always exit 1."""
    advice = REFUSAL_ADVICE[reason]
    if as_json:
        print(json.dumps({"match": None, "action": "refused", "reason": reason,
                          "why": message, "details": list(details),
                          "advice": advice}, indent=2))
    print("REFUSED: %s" % message, file=sys.stderr)
    for d in details:
        print("  - %s" % d, file=sys.stderr)
    print(advice, file=sys.stderr)
    return 1


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

    if args.list:
        rows = [(p.packet_id or "?", p.status or "?",
                 ((p.meta.get("fill") or {}).get("mode") or "?"),
                 ", ".join(p.markers("all")) or "(none)") for p in profiles]
        print("%-18s%-9s%-10s%s" % ("PACKET", "STATUS", "FILL", "REQUIRED MARKERS"))
        for r in rows:
            print("%-18s%-9s%-10s%s" % r)
        for e in errors:
            print("unreadable profile — %s" % e, file=sys.stderr)
        return 1 if errors else 0

    # A profile that will not parse is dropped from the set, and a resolution
    # against the remainder is a resolution against a set nobody authored. It
    # used to report a clean `no match -> Path B` and exit 0.
    if errors:
        return _refuse("unreadable-profiles",
                       "%d profile(s) in %s do not parse, so the profile set is "
                       "incomplete" % (len(errors), args.profiles_dir),
                       errors, args.json)

    try:
        if args.recognize_pdf:
            text = pdf_text(args.recognize_pdf)
        elif args.recognize == "-":
            text = sys.stdin.read()
        else:
            try:
                with open(args.recognize, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError as exc:
                raise Environment("cannot read %s: %s" % (args.recognize, exc.strerror))
    except Environment as env:
        print("ERROR: %s" % env, file=sys.stderr)
        return 2

    try:
        match = recognize(text, profiles)
    except Refusal as ref:
        return _refuse(ref.reason, str(ref), ref.details, args.json)
    _report(match, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
