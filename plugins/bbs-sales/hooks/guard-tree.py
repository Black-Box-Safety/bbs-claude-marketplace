#!/usr/bin/env python3
"""PreToolUse guard for the BBS quote-desk folder tree ("All RFQ's by Agency").

The Python half of guard-tree.ps1: same rules, same deny reasons, same decisions on
every input, so a Mac without PowerShell gets the same guard a Windows machine does.
hooks/tests/parity.py proves the two agree. Change both or neither (invariant 3).

Reads the hook JSON on stdin. Silent (exit 0, no output) = allow.
Deny = JSON with hookSpecificOutput.permissionDecision = "deny" and a reason Claude can relay.

Rules (from workspace/DESK-CLAUDE-template.md landmines):
  1. Never rename or move anything inside the tree -- folder names carry account numbers.
  2. Never create a buyer/agency folder whose name is a near-duplicate of a sibling.
  3. Files under FILLED/ are submitted packets: never overwrite one.

Stdlib only. Fails open on unreadable input, like the PowerShell version.
"""
import json
import os
import re
import sys

TREE = "All RFQ's by Agency"
# PowerShell's -match is case-insensitive by default; every pattern below was written for
# it, so they all run with IGNORECASE here. The one exception is noted where it occurs.
I = re.IGNORECASE


def deny(reason):
    out = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                  "permissionDecision": "deny",
                                  "permissionDecisionReason": reason}}
    sys.stdout.write(json.dumps(out, separators=(",", ":")))
    sys.exit(0)


def normalize(name):
    n = name.lower().replace("(all)", "")
    return re.sub(r"[^a-z0-9]", "", n)


def tokens(name):
    """Word tokens, so "Mule Creek Prison" and "Mule Creek State Prison" can be compared."""
    n = name.lower().replace("(all)", " ")
    return [t for t in re.sub(r"[^a-z0-9]", " ", n).split() if t]


def levenshtein(a, b):
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[len(b)]


def is_transposition(a, b):
    """One swapped adjacent pair ("cdrc" for "cdcr"). Plain Levenshtein scores a transposition
    2, and loosening the short-name threshold to 2 would collide real siblings like CDPH and
    CDCR, so the swap is checked on its own."""
    if len(a) != len(b) or len(a) < 2:
        return False
    diff = [k for k in range(len(a)) if a[k] != b[k]]
    if len(diff) != 2 or diff[1] - diff[0] != 1:
        return False
    return a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]


def is_near_duplicate(new, existing):
    """Two folder names are near-duplicates when one is a typo of the other, or when one names
    the same buyer with a word dropped or added ("Mule Creek Prison" vs "Mule Creek State
    Prison")."""
    want, have = normalize(new), normalize(existing)
    if not want or not have:
        return False
    if want == have:
        return True
    if len(want) >= 6 and levenshtein(want, have) <= 2:
        return True
    # Agency acronyms (CDCR, CALPIA) are too short for the rule above: one wrong or swapped
    # letter there is a typo, not a different buyer.
    if 4 <= len(want) <= 5 and 4 <= len(have) <= 5:
        if levenshtein(want, have) <= 1 or is_transposition(want, have):
            return True
    want_t, have_t = tokens(new), tokens(existing)
    if len(want_t) >= 2 and len(have_t) >= 2:
        shared = [t for t in want_t if t in have_t]
        if len(shared) >= 2 and (len(shared) == len(want_t) or len(shared) == len(have_t)):
            return True
    return False


def near_duplicate(path):
    """Given an absolute path inside the tree, find the first directory segment that does not
    exist yet and compare it against its existing siblings. Returns the offending existing
    path or None."""
    idx = path.lower().find(TREE.lower())
    if idx < 0:
        return None
    root_dir = path[:idx + len(TREE)]
    rest = path[idx + len(TREE):].strip("\\/")
    if not rest:
        return None
    parent = root_dir
    for seg in re.split(r"[\\/]", rest):
        candidate = os.path.join(parent, seg)
        if os.path.exists(candidate):
            parent = candidate
            continue
        # seg is new. Is it a directory-ish segment? Treat as folder unless it has a file extension.
        if re.search(r"\.[A-Za-z0-9]{1,5}$", seg):
            return None
        if not os.path.exists(parent):
            return None
        try:
            sibs = [e for e in os.scandir(parent) if e.is_dir()]
        except OSError:
            return None
        for sib in sibs:
            if is_near_duplicate(seg, sib.name):
                return sib.path
        return None   # first new segment is distinct; deeper segments are its children
    return None


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return 0
    try:
        h = json.loads(raw)
    except ValueError:
        return 0
    if not isinstance(h, dict):
        return 0
    tool = str(h.get("tool_name") or "")
    inp = h.get("tool_input") or {}
    if not isinstance(inp, dict):
        inp = {}

    if tool.lower() in ("bash", "powershell"):
        cmd = str(inp.get("command") or "")
        if not cmd:
            return 0
        if TREE.lower() not in cmd.lower():
            return 0
        if re.search(r"(^|[\s;&|(])(mv|ren|rename|Rename-Item|Move-Item|git\s+mv)\b", cmd, I):
            deny(f"Blocked: renaming or moving inside '{TREE}' is never allowed -- folder names "
                 f"carry Grainger account numbers and buyer identity (desk CLAUDE.md landmine 4). "
                 f"If a folder is truly misnamed, tell Parker.")
        filled = re.search(r"[\\/]FILLED[\\/]", cmd, I) is not None
        # Deletes anywhere near a FILLED path, or a redirect whose TARGET is inside FILLED.
        # Reading a packet (cat, pdftotext ... > elsewhere) stays allowed.
        if filled and re.search(r"(^|[\s;&|(])(rm|del|Remove-Item)\b", cmd, I):
            deny("Blocked: files under FILLED/ are submitted packets and immutable. Do not delete "
                 "them; save a new version alongside (e.g. -v2).")
        if re.search(r'>{1,2}\s*("[^"]*[\\/]FILLED[\\/]|[^\s"|;&]*[\\/]FILLED[\\/])', cmd, I):
            deny("Blocked: redirecting output into FILLED/ would overwrite a submitted packet. "
                 "Write the new file alongside it (e.g. -v2).")
        # Write-only cmdlets and tee: a FILLED path anywhere in the command is the target.
        if filled and re.search(r"(^|[\s;&|(])(Set-Content|Add-Content|Out-File|tee)\b", cmd, I):
            deny("Blocked: writing into FILLED/ would overwrite a submitted packet. Write the new "
                 "file alongside it (e.g. -v2).")
        # Copies: the LAST path token is the destination. Copying a packet OUT of FILLED is fine.
        if re.search(r"(^|[\s;&|(])(cp|copy|Copy-Item|Move-Item|mv)\b", cmd, I):
            toks = [m.group(0).strip('"') for m in re.finditer(r'"[^"]+"|\S+', cmd)]
            paths = [t for t in toks if re.search(r"[\\/]", t) and not t.startswith("-")]
            dest = paths[-1] if paths else None
            if dest and re.search(r"[\\/]FILLED[\\/]", dest, I):
                deny("Blocked: copying onto FILLED/ would overwrite a submitted packet. Copy to a "
                     "new name alongside it (e.g. -v2).")
        if re.search(r"(^|[\s;&|(])(mkdir|md|New-Item)\b", cmd, I):
            # [regex]::Match in the PowerShell version is case-SENSITIVE, unlike -match, so the
            # quoted form is matched exactly here too; the unquoted fallback is -like, which is not.
            m = re.search(r'"([^"]*' + re.escape(TREE) + r'[^"]*)"', cmd)
            if m:
                target = m.group(1)
            else:
                target = next((t for t in re.split(r"\s+", cmd) if TREE.lower() in t.lower()), None)
            if target:
                dup = near_duplicate(target)
                if dup:
                    deny(f"Blocked: '{target}' is a near-duplicate of the existing folder '{dup}'. "
                         f"Duplicate buyer folders hide precedent (landmine 1). Use the existing "
                         f"folder, or ask Parker if this is genuinely a different buyer.")
        return 0

    if tool.lower() in ("write", "edit", "multiedit", "notebookedit"):
        p = str(inp.get("file_path") or "") or str(inp.get("notebook_path") or "")
        if not p:
            return 0
        if TREE.lower() not in p.lower():
            return 0
        if re.search(r"[\\/]FILLED[\\/]", p, I) and os.path.exists(p):
            deny(f"Blocked: '{p}' is a submitted packet under FILLED/ and is immutable. Save a new "
                 f"version alongside it (e.g. add -v2) instead of overwriting.")
        dup = near_duplicate(p)
        if dup:
            deny(f"Blocked: this path would create a folder that near-duplicates '{dup}'. Duplicate "
                 f"buyer folders hide precedent (landmine 1). Write into the existing folder, or ask "
                 f"Parker if this is genuinely a different buyer.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
