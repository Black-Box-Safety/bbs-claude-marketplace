#!/usr/bin/env python3
"""doctrine.py and doctrine.ps1 must agree byte for byte on every input.

Runs a fixed set of edge-case fixtures through doctrine.py (always) and through
doctrine.ps1 under pwsh or powershell (whichever is on PATH). For each fixture it checks
the python output against an expectation computed here independently, checks stderr is
empty and the exit code is 0, and — when PowerShell ran — checks the two interpreters'
stdout bytes are identical.

When neither pwsh nor powershell is on PATH the PowerShell half is SKIPPED, not failed,
unless BBS_REQUIRE_PS=1 is set (CI sets it, so CI proves parity rather than skipping it).

Usage:  python3 plugins/<plugin>/hooks/tests/parity.py
Exit 0 = all pass. Stdlib only. Never writes inside the plugin; edge cases that need a
mutated doctrine dir (CRLF file, BOM file, missing table) run on a copy in a temp dir.
"""
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.dirname(HERE)
DDIR = os.path.join(HOOKS, "doctrine")
TABLE = json.load(open(os.path.join(DDIR, "subscriptions.json"), encoding="utf-8-sig"))
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"


def expected_text(insert):
    p = os.path.join(DDIR, TABLE["inserts"][insert]["file"])
    return open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")


def glob(n, pat):
    pat = pat.replace("[", "[[]").replace("?", "[?]")
    return fnmatch.fnmatchcase(n.lower(), pat.lower())


def expected_for(event, name, bare=False):
    """bare = the typed-command rule for a name with no colon (the retired injection plugin's own rule):
    bare patterns as is, plugin:suffix by its suffix, plugin:* and plugin:** skipped."""
    seen = []
    for s in TABLE["subscriptions"]:
        if s["insert"] in seen:
            continue
        on = s["on"]
        if not bare or ":" not in on:
            hit = glob(name, on)
        else:
            suffix = on.split(":", 1)[1]
            hit = suffix not in ("*", "**") and glob(name, suffix)
        if hit:
            seen.append(s["insert"])
    if not seen:
        return b""
    ctx = "\n\n".join(expected_text(i) for i in seen)
    return ('{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}'
            % (event, json.dumps(ctx, ensure_ascii=True))).encode("ascii")


def run(cmd, stdin_bytes):
    r = subprocess.run(cmd, input=stdin_bytes, capture_output=True, timeout=60)
    return r.returncode, r.stdout, r.stderr


def py(hooks_dir):
    return [sys.executable, os.path.join(hooks_dir, "doctrine.py")]


def ps(hooks_dir):
    return [PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", os.path.join(hooks_dir, "doctrine.ps1")]


def j(obj):
    return json.dumps(obj).encode("utf-8")


def typed(name, source="plugin", **extra):
    d = {"hook_event_name": "UserPromptExpansion", "expansion_type": "slash_command",
         "command_name": name, "command_args": "x", "command_source": source,
         "prompt": "/%s x" % name}
    d.update(extra)
    return j(d)


exact = [s["on"] for s in TABLE["subscriptions"] if "*" not in s["on"] and ":" in s["on"]]
wild = [s["on"] for s in TABLE["subscriptions"] if "*" in s["on"] and ":" in s["on"]]
bare_pats = [s["on"] for s in TABLE["subscriptions"] if "*" not in s["on"] and ":" not in s["on"]]
first = exact[0]
suffix = first.split(":", 1)[1]

fixtures = [
    # label, stdin bytes, expected python stdout
    ("skill exact match", j({"tool_name": "Skill", "tool_input": {"skill": first}}),
     expected_for("PreToolUse", first)),
    ("combined inserts (exact + plugin:*)",
     j({"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": first}}),
     expected_for("PreToolUse", first)),
    ("case-insensitive", j({"tool_name": "Skill", "tool_input": {"skill": first.upper()}}),
     expected_for("PreToolUse", first)),
    ("wildcard concrete", j({"tool_name": "Skill", "tool_input": {"skill": wild[0].replace("*", "zzz")}}),
     expected_for("PreToolUse", wild[0].replace("*", "zzz"))),
    ("metachars in name under plugin:*",
     j({"tool_name": "Skill", "tool_input": {"skill": wild[0].replace("*", "[a]?*b")}}),
     expected_for("PreToolUse", wild[0].replace("*", "[a]?*b"))),
    ("metachars in unrelated name", j({"tool_name": "Skill", "tool_input": {"skill": "[*]?"}}), b""),
    ("unrelated skill", j({"tool_name": "Skill", "tool_input": {"skill": "unrelated"}}), b""),
    ("bare skill via tool matches whole list only",
     j({"tool_name": "Skill", "tool_input": {"skill": suffix}}), expected_for("PreToolUse", suffix)),
    ("non-Skill tool", j({"tool_name": "Bash", "tool_input": {"command": "ls"}}), b""),
    ("missing tool_input", j({"hook_event_name": "PreToolUse", "tool_name": "Skill"}), b""),
    ("tool_input null", j({"tool_name": "Skill", "tool_input": None}), b""),
    ("tool_input a string", j({"tool_name": "Skill", "tool_input": "x"}), b""),
    ("skill non-string", j({"tool_name": "Skill", "tool_input": {"skill": 42}}), b""),
    ("skill empty", j({"tool_name": "Skill", "tool_input": {"skill": "  "}}), b""),
    ("empty stdin", b"", b""),
    ("whitespace stdin", b"  \n", b""),
    ("garbage stdin", b"{not json", b""),
    ("top-level array", b"[1,2]", b""),
    ("BOM on stdin", b"\xef\xbb\xbf" + j({"tool_name": "Skill", "tool_input": {"skill": first}}),
     expected_for("PreToolUse", first)),
    ("unknown event", j({"hook_event_name": "SessionStart", "command_name": suffix}), b""),
    # Typed commands. Prefixed: whole-pattern match. Bare: the retired plugin's bare-name rule.
    ("typed prefixed", typed(first), expected_for("UserPromptExpansion", first)),
    ("typed bare suffix of an exact subscription", typed(suffix),
     expected_for("UserPromptExpansion", suffix, bare=True)),
    ("typed bare /brainstorming is silent", typed("brainstorming"), b""),
    ("typed bare /bbs-checkup is silent (plugin:* skipped)", typed("bbs-checkup"), b""),
    ("typed bare /ca-rfq is silent (plugin:* skipped)", typed("ca-rfq"), b""),
    ("typed unrelated prefixed", typed("nobody:unrelated", "user"), b""),
    ("typed command_name missing", j({"hook_event_name": "UserPromptExpansion"}), b""),
    ("mcp_prompt named like a skill is silent",
     typed(first, "mcp", expansion_type="mcp_prompt"), b""),
]
assert expected_for("UserPromptExpansion", "bbs-checkup", bare=True) == b""
assert expected_for("UserPromptExpansion", "ca-rfq", bare=True) == b""
if bare_pats:
    # e.g. /bbs-claude-md-forge -> the CLAUDE.md doctrine via the bare pattern, and NOT the
    # grounding doctrine that bbs-foundations:* would have given a prefixed call.
    want = expected_for("UserPromptExpansion", bare_pats[0], bare=True)
    assert want and all(expected_text(i).encode() not in want
                        for i in TABLE["inserts"] if i != next(
                            s["insert"] for s in TABLE["subscriptions"] if s["on"] == bare_pats[0]))
    fixtures.append(("typed bare /%s -> its insert only" % bare_pats[0], typed(bare_pats[0]), want))

fail = 0


def check(label, cond, detail=""):
    global fail
    print(("PASS  " if cond else "FAIL  ") + label + (("  " + detail) if detail and not cond else ""))
    if not cond:
        fail += 1


def exercise(label, hooks_dir, stdin_bytes, want):
    code, out, err = run(py(hooks_dir), stdin_bytes)
    check(f"[py] {label}: exit 0, no stderr", code == 0 and err == b"", f"exit={code} stderr={err[:120]!r}")
    check(f"[py] {label}: output", out == want, f"got={out[:100]!r} want={want[:100]!r}")
    if PS:
        pcode, pout, perr = run(ps(hooks_dir), stdin_bytes)
        check(f"[ps] {label}: exit 0, no stderr", pcode == 0 and perr == b"", f"exit={pcode} stderr={perr[:120]!r}")
        check(f"[parity] {label}: ps == py bytes", pout == out, f"ps={pout[:100]!r} py={out[:100]!r}")


for label, stdin_bytes, want in fixtures:
    exercise(label, HOOKS, stdin_bytes, want)

# Mutated copies: CRLF doctrine file, BOM on the doctrine file, missing table. The copy
# sits under a version-like folder name, as an installed plugin does: nothing may depend
# on the plugin directory's name.
with tempfile.TemporaryDirectory() as tmp:
    hooks = os.path.join(tmp, "1.2.3", "hooks")
    shutil.copytree(HOOKS, hooks, ignore=shutil.ignore_patterns("tests"))
    ins = TABLE["subscriptions"][0]["insert"]
    fpath = os.path.join(hooks, "doctrine", TABLE["inserts"][ins]["file"])
    original = open(fpath, "rb").read()
    open(fpath, "wb").write(original.replace(b"\n", b"\r\n"))
    exercise("CRLF doctrine file normalised to LF", hooks,
             j({"tool_name": "Skill", "tool_input": {"skill": first}}), expected_for("PreToolUse", first))
    open(fpath, "wb").write(b"\xef\xbb\xbf" + original)
    exercise("BOM on doctrine file stripped", hooks,
             j({"tool_name": "Skill", "tool_input": {"skill": first}}), expected_for("PreToolUse", first))
    exercise("typed bare from a version-named plugin dir", hooks,
             typed(suffix), expected_for("UserPromptExpansion", suffix, bare=True))
    open(fpath, "wb").write(original)
    os.remove(os.path.join(hooks, "doctrine", "subscriptions.json"))
    exercise("missing subscriptions.json is silent", hooks,
             j({"tool_name": "Skill", "tool_input": {"skill": first}}), b"")

if not PS:
    if REQUIRE_PS:
        check("PowerShell on PATH (BBS_REQUIRE_PS=1)", False, "neither pwsh nor powershell found")
    else:
        print("SKIP  PowerShell not on PATH: parity with doctrine.ps1 not exercised here")
else:
    print(f"      PowerShell used: {PS}")
print(f"{fail} failure(s)" if fail else "all pass")
sys.exit(1 if fail else 0)
