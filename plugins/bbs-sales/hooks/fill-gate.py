#!/usr/bin/env python3
"""PreToolUse gate for the bbs-fill launcher (Bash). The Python half of fill-gate.ps1.

Prints an "allow" decision only when the whole Bash command is exactly one invocation of this
plugin's own launcher, "<root>/scripts/bbs-fill", on a script that is on the launcher's ALLOWED
list, "<root>/skills/<entry>". Otherwise it prints nothing, which leaves the call to the normal
permission flow exactly as if this hook were absent. It never denies and never asks: refusing
is the launcher's job, and every doubt here ends in a prompt, never in an unvetted run.

Spec: docs/superpowers/specs/2026-11-11-bbs-fill-into-bbs-sales.md, section 3 (RULED 2026-11-11).
Both halves must decide identically on every input (hooks/tests/fill_gate_parity.py); change
both or neither.

The command grammar is a deny-by-default subset shared by bash and zsh, read code point by code
point:
  - words are separated by runs of U+0020;
  - a word is a concatenation of unquoted runs (ASCII [A-Za-z0-9_./:,=+@%-], never starting the
    word with "="), single-quoted runs, and double-quoted runs (no $ ` ! inside, and a backslash
    only where it stays literal);
  - non-ASCII is accepted only inside quotes;
  - every Cc code point, U+2028, U+2029, U+FFFD and any surrogate code point rejects the command.
Anything else (operators, redirects, substitution, expansion, globs, comments, an unterminated
quote) rejects the command.

Stdlib only. Exit 0 always.
"""
import json
import os
import re
import sys

REASON = "bbs-fill: vetted script "
ENTRY = re.compile(r'^"([a-z0-9-]+/scripts/[A-Za-z0-9_.-]+\.(?:py|js))"$')
UNQUOTED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./:,=+@%-")
DQ_ESCAPABLE = set('$`"\\')
TRIM = " \t"   # ALLOWED lines are trimmed of spaces and tabs only, as in fill-gate.ps1
# JSON keys are read by exact name; a key that differs from one of these only by case means no
# decision, matching fill-gate.ps1 (PowerShell's property lookup ignores case).
KEYS_TOP = ("tool_name", "tool_input")
KEYS_INPUT = ("command", "dangerouslyDisableSandbox")


def ascii_fold(s):
    """A-Z to a-z only. Both halves fold the same way; Unicode case rules differ between them."""
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in s)


def case_variant(d, names):
    return any(ascii_fold(k) == ascii_fold(n) and k != n for k in d for n in names)


def bad(cp):
    """Code points that reject the command wherever they appear, quoted or not."""
    # U+FFFD too: PowerShell's JSON reader turns a lone surrogate into it, so both halves refuse it.
    return cp < 0x20 or 0x7F <= cp <= 0x9F or cp in (0x2028, 0x2029, 0xFFFD) or 0xD800 <= cp <= 0xDFFF


def lex(cmd):
    """The command's words after quote removal, or None if it is outside the grammar."""
    cps = [ord(c) for c in cmd]
    n = len(cps)
    words = []
    cur = None
    i = 0
    while i < n:
        cp = cps[i]
        if bad(cp):
            return None
        c = chr(cp)
        if c == " ":
            if cur is not None:
                words.append(cur)
                cur = None
            i += 1
        elif c == "'":
            j = i + 1
            while j < n and cps[j] != 0x27:
                if bad(cps[j]):
                    return None
                j += 1
            if j >= n:
                return None
            cur = (cur or "") + "".join(chr(x) for x in cps[i + 1:j])
            i = j + 1
        elif c == '"':
            j = i + 1
            seg = []
            while True:
                if j >= n:
                    return None
                d = cps[j]
                if d == 0x22:
                    break
                if bad(d) or chr(d) in "$`!":
                    return None
                if d == 0x5C and j + 1 < n and chr(cps[j + 1]) in DQ_ESCAPABLE:
                    return None
                seg.append(chr(d))
                j += 1
            cur = (cur or "") + "".join(seg)
            i = j + 1
        elif c in UNQUOTED:
            if c == "=" and cur is None:
                return None
            cur = (cur or "") + c
            i += 1
        else:
            return None
    if cur is not None:
        words.append(cur)
    return words or None


def canon(path):
    """Separators to "/", "C:\\x" or "C:/x" to "/c/x", duplicate "/" collapsed, a trailing "/"
    dropped. None if any segment is "." or "..". No case or Unicode folding beyond the drive."""
    p = path.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/", p)
    if m:
        p = "/" + m.group(1).lower() + p[2:]
    p = re.sub(r"/+", "/", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    if any(seg in (".", "..") for seg in p.split("/")):
        return None
    return p


def read_allowed(launcher):
    try:
        with open(launcher, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if b"\r" in data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.split("\n")
    try:
        start = next(k for k, l in enumerate(lines) if l.strip(TRIM) == "ALLOWED=(")
    except StopIteration:
        return None
    out = []
    for l in lines[start + 1:]:
        s = l.strip(TRIM)
        if s == ")":
            return out or None
        if not s:
            continue
        m = ENTRY.match(s)
        if not m:
            return None
        out.append(m.group(1))
    return None


def any_link(root, parts):
    """True if the root itself, or any component below it along parts, is a symlink."""
    p = root
    if os.path.islink(p):
        return True
    for part in parts:
        p = os.path.join(p, part)
        if os.path.islink(p):
            return True
    return False


def decide(h):
    if not isinstance(h, dict) or case_variant(h, KEYS_TOP) or h.get("tool_name") != "Bash":
        return None
    ti = h.get("tool_input")
    if not isinstance(ti, dict) or case_variant(ti, KEYS_INPUT):
        return None
    cmd = ti.get("command")
    if not isinstance(cmd, str):
        return None
    dds = ti.get("dangerouslyDisableSandbox")
    if dds is not None and dds is not False:
        return None
    root_env = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not root_env:
        return None
    root_native = root_env.rstrip("/\\") or root_env
    root = canon(root_env)
    if not root:
        return None
    words = lex(cmd)
    if not words or len(words) < 2:
        return None
    w0, w1 = canon(words[0]), canon(words[1])
    if w0 is None or w1 is None or w0 != root + "/scripts/bbs-fill":
        return None
    prefix = root + "/skills/"
    if not w1.startswith(prefix):
        return None
    entry = w1[len(prefix):]
    launcher = os.path.join(root_native, "scripts", "bbs-fill")
    allowed = read_allowed(launcher)
    if not allowed or entry not in allowed:
        return None
    if any_link(root_native, ["scripts", "bbs-fill"]) or any_link(root_native, ["skills"] + entry.split("/")):
        return None
    if not os.path.isfile(launcher) or not os.path.isfile(os.path.join(root_native, "skills", *entry.split("/"))):
        return None
    return entry


def main():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8")
        entry = decide(json.loads(raw)) if raw.strip() else None
    except Exception:
        entry = None
    if entry:
        out = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "allow",
                                      "permissionDecisionReason": REASON + entry}}
        sys.stdout.write(json.dumps(out, separators=(",", ":")))
    sys.exit(0)


if __name__ == "__main__":
    main()
