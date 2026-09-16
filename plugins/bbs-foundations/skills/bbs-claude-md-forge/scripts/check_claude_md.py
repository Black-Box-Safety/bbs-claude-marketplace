#!/usr/bin/env python3
"""
check_claude_md.py — the BBS CLAUDE.md checker (stdlib only).

Walks every CLAUDE.md under a path and applies the checks in references/checklist.md:
the 150-line cap, @-import and markdown-link resolution, inline @-imports, sandbox paths,
secret-shaped strings, placeholders, stale model IDs, canonical-fact drift (MRO LPA,
"SB certified", DVBE in a federal-context file), maintenance footer, duplicate headings,
chain completeness, and stale status banners.

Usage:
    python3 check_claude_md.py <path> [--json]

Exit 0 = no FAIL. Exit 1 = at least one FAIL. WARN never changes the exit code.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

CAP = 150
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", ".claude-plugin"}

# Model IDs come from references/models.json — the same file canonical-facts.md quotes and
# scripts/refresh_models.py rewrites from the API. The list used to live here as a regex,
# which is how it went stale while still being enforced: the checker passed the superseded
# ID and told authors to write it. A checker that carries its own copy of a fact is a
# second source of truth waiting to drift.
MODELS_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "references", "models.json")
# `\b` matches after a hyphen, so `bbs-claude-md-forge` yielded the "model ID"
# `claude-md-forge` and any file naming that path FAILed as unknown_model. The
# lookbehind refuses a match that starts inside a longer hyphenated identifier.
# There is deliberately no trailing lookahead: `claude-3-…` ends on a hyphen, and
# `(?![\w-])` would drop that whole stale family. The greedy tail already runs to
# the end of the hyphenated run, so a real ID is never cut short.
ANY_CLAUDE_ID = re.compile(r"(?<![\w-])claude-[a-z0-9]+(?:-[a-z0-9]+)*\b")
DATE_SUFFIXED = re.compile(r"\bclaude-[a-z0-9-]+-20\d{6}\b")


def load_models():
    """Return (current, superseded, known_not_adopted). Missing file is fatal:
    silently skipping the model check is how a stale ID ships."""
    try:
        with open(MODELS_JSON) as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        sys.exit(f"cannot read {MODELS_JSON}: {exc}\n"
                 f"It is the source of truth for model IDs; the checker will not run without it.")
    return (set(data["current"].values()),
            data.get("superseded", {}),
            set(data.get("known_not_adopted", {})))


CURRENT_MODELS, SUPERSEDED_MODELS, KNOWN_NOT_ADOPTED = load_models()

FEDERAL_MARKERS = re.compile(r"\b(Bechtel|USACE|DFARS|FAR 52\.|federal prime|Centerra|UCOR|Northrop)\b", re.I)
# A DVBE *claim* — leading with the credential — not a role title ("DVBE veteran owner")
# and not a rule about when not to use it ("Never use DVBE here").
DVBE_CLAIM = re.compile(
    r"\b(as an? DVBE|we are an? DVBE|our DVBE|an? DVBE (distributor|reseller|supplier|business|firm|vendor)"
    r"|DVBE[- ]certified|certified DVBE|DVBE (credit|participation|goal|incentive|preference|status|set-?aside))\b",
    re.I,
)
SDVOSB_LINE = re.compile(r"\bSDVOSB\b")

FAIL_PATTERNS = [
    ("sandbox_path", re.compile(r"/mnt/(skills|user-data)\b"),
     "sandbox path from a hosted Claude session; does not exist on this machine"),
    ("secret", re.compile(r"(eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}|\bsk-[A-Za-z0-9]{20,}|\b[0-9a-f]{40,}\b|password\s*=\s*\S+|service_role[\"'\s:=]+[A-Za-z0-9._-]{16,})"),
     "secret-shaped string; never commit secrets"),
    ("placeholder", re.compile(r"\[(TODO|TBD|PLACEHOLDER|Insert[^\]]*|Add[^\]]*)\]|\bTODO\("),
     "placeholder content left from a template"),
    ("wrong_mro_lpa", re.compile(r"7-25-52-02\.03|7-18-51-02\.18"),
     "MRO LPA is 7-25-51-02.03"),
    # No SB-preference check: BBS holds OSDS SB/DVBE 2009473 and the 5% preference applies
    # on competitive solicitations (SCM §1204). Where it belongs is a reviewer's judgment.
]

WARN_PATTERNS = [
    ("stale_banner", re.compile(r"\bdays remaining\b", re.I), "status banner with a countdown; verify it is still true"),
    ("hq_san_diego", re.compile(r"(headquarter\w*|HQ)[^.\n]{0,40}San Diego", re.I), "HQ is El Cajon, CA"),
]

IMPORT_LINE = re.compile(r"^@(\S+)\s*$")
INLINE_IMPORT = re.compile(r"(?<!^)(?<![`\w/.\-@])@((?:\.\./|\./)?[\w./-]*CLAUDE\.md)")
MD_LINK = re.compile(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")
HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
FOOTER = re.compile(r"(^#{1,6}\s+Maintain|Last verified|\*?Owner:|\*?Maintainer:)", re.I | re.M)
DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")


def find_files(root):
    if os.path.isfile(root):
        return [root]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if "CLAUDE.md" in filenames:
            out.append(os.path.join(dirpath, "CLAUDE.md"))
    return sorted(out)


def check_file(path, all_files):
    findings = []
    F = lambda code, line, msg: findings.append({"level": "FAIL", "code": code, "line": line, "msg": msg})
    W = lambda code, line, msg: findings.append({"level": "WARN", "code": code, "line": line, "msg": msg})

    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    lines = text.splitlines()
    d = os.path.dirname(path)
    n = len(lines)

    if n > CAP:
        F("over_cap", n, f"{n} lines; hard cap is {CAP} — split into a sub-file and chain it")
    if n < 20:
        W("too_short", n, f"{n} lines; probably a stub")

    in_code = False
    imports = []
    headings = {}
    federal_file = bool(FEDERAL_MARKERS.search(text))
    for i, raw in enumerate(lines, 1):
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        m = IMPORT_LINE.match(raw)
        if m:
            target = m.group(1)
            imports.append(target)
            if not os.path.exists(os.path.normpath(os.path.join(d, target))):
                F("broken_import", i, f"@{target} does not resolve")
        else:
            for im in INLINE_IMPORT.finditer(raw):
                # skip backticked or quoted references (documentation, not import)
                seg = raw[max(0, im.start() - 1): im.start()]
                if seg in ("`", "'", '"'):
                    continue
                F("inline_import", i, f"@{im.group(1)} is inline; imports load only at column one")

        for lm in MD_LINK.finditer(raw):
            target = lm.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(d, target))):
                F("broken_link", i, f"link target {target} does not resolve")

        for code, pat, msg in FAIL_PATTERNS:
            if pat.search(raw):
                F(code, i, msg)

        for dated in DATE_SUFFIXED.findall(raw):
            base = re.sub(r"-20\d{6}$", "", dated)
            F("dated_model", i,
              f"{dated} — model IDs carry no date suffix; write {base}")
        for found in ANY_CLAUDE_ID.findall(raw):
            if DATE_SUFFIXED.match(found) or found in CURRENT_MODELS:
                continue
            if found in SUPERSEDED_MODELS:
                F("stale_model", i,
                  f"{found} is superseded; use {SUPERSEDED_MODELS[found]}")
            elif found in KNOWN_NOT_ADOPTED:
                W("unadopted_model", i,
                  f"{found} is a real model BBS has not adopted; current set is "
                  f"{' / '.join(sorted(CURRENT_MODELS))}")
            else:
                F("unknown_model", i,
                  f"{found} is not a known model ID; current set is "
                  f"{' / '.join(sorted(CURRENT_MODELS))}")
        for code, pat, msg in WARN_PATTERNS:
            if pat.search(raw):
                W(code, i, msg)

        if federal_file and DVBE_CLAIM.search(raw) and not SDVOSB_LINE.search(raw):
            # a rule *about* DVBE ("never claim DVBE credit here") is not a claim
            if not re.search(r"\b(never|not|do not|don't|wrong|only|local|state[- ]only)\b", raw, re.I):
                F("dvbe_in_federal", i, "DVBE claim in a federal-context file without SDVOSB; cert language follows the channel")

        hm = HEADING.match(raw)
        if hm:
            key = hm.group(1).strip().lower()
            if key in headings:
                W("dup_heading", i, f"duplicate heading '{hm.group(1)}' (first at line {headings[key]})")
            else:
                headings[key] = i

    if not FOOTER.search(text):
        W("no_footer", n, "no maintenance footer (Owner / Last verified / Maintaining this file)")

    # stale dates in banner-like context
    for i, raw in enumerate(lines[:25], 1):
        if re.search(r"\b(due|deadline|as of|remaining)\b", raw, re.I):
            for dm in DATE.finditer(raw):
                try:
                    when = dt.date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                except ValueError:
                    continue
                if (dt.date.today() - when).days > 90:
                    W("stale_banner", i, f"date {when} in a status line is over 90 days old")

    # chain completeness
    children = [f for f in all_files if f != path and f.startswith(d + os.sep)]
    direct_children = [f for f in children if os.path.dirname(os.path.dirname(f)) == d]
    for child in direct_children:
        rel = os.path.relpath(child, d)
        if rel not in imports and rel.replace(os.sep, "/") not in imports:
            W("unchained_child", 0, f"child {rel} exists but is not imported at column one (ok if deliberately read-on-demand)")
    # abspath first: for a file reached as ./CLAUDE.md, d is "." and dirname(".")
    # is "", so the root file was compared against itself and warned that it did
    # not import its own parent.
    parent = os.path.join(os.path.dirname(os.path.abspath(d)), "CLAUDE.md")
    if os.path.exists(parent) and os.path.abspath(parent) in {os.path.abspath(f) for f in all_files}:
        if not any(t in ("../CLAUDE.md", "..\\CLAUDE.md") for t in imports):
            W("no_parent_import", 0, "sub-file does not import @../CLAUDE.md; a session started here misses the universal rules")

    return {"file": path, "lines": n, "findings": findings}


def main():
    ap = argparse.ArgumentParser(description="BBS CLAUDE.md checker")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = find_files(args.path)
    if not files:
        print(f"no CLAUDE.md found under {args.path}", file=sys.stderr)
        sys.exit(2)

    results = [check_file(f, files) for f in files]
    fails = sum(1 for r in results for x in r["findings"] if x["level"] == "FAIL")
    warns = sum(1 for r in results for x in r["findings"] if x["level"] == "WARN")

    if args.json:
        print(json.dumps({"files": results, "fails": fails, "warns": warns}, indent=2))
    else:
        for r in results:
            status = "FAIL" if any(x["level"] == "FAIL" for x in r["findings"]) else ("warn" if r["findings"] else "ok")
            print(f"{status:4}  {r['lines']:4} lines  {r['file']}")
            for x in r["findings"]:
                loc = f":{x['line']}" if x["line"] else ""
                print(f"        {x['level']:4} {x['code']:<18}{loc:<6} {x['msg']}")
        print(f"\n{len(results)} file(s) · {fails} FAIL · {warns} WARN")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
