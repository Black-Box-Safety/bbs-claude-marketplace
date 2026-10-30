#!/usr/bin/env python3
"""customer-folder.py and customer-folder.ps1 must agree byte for byte on every input.

Builds a fixture MASTER/Customers tree in a temp dir and runs one ordered sequence of
cases through customer-folder.py (always) and through customer-folder.ps1 under pwsh or
powershell (whichever is on PATH). The sequence is ordered because the once-per-session
marker makes a case depend on the ones before it; each interpreter gets its own fresh
TMPDIR, so the two never see each other's markers. For each case it checks the python
output against an expectation computed here independently, checks stderr is empty and
the exit code is 0, and — when PowerShell ran — checks the two interpreters' stdout bytes
are identical.

When neither pwsh nor powershell is on PATH the PowerShell half is SKIPPED, not failed,
unless BBS_REQUIRE_PS=1 is set (CI sets it, so CI proves parity rather than skipping it).

Usage:  python3 plugins/bbs-foundations/hooks/tests/customer_folder_parity.py
Exit 0 = all pass. Stdlib only. Writes only inside a temp dir it removes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.dirname(HERE)
TEXTS = os.path.join(HOOKS, "customer-folder")
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"


def text(fname, name, target):
    t = open(os.path.join(TEXTS, fname), encoding="utf-8-sig").read()
    t = t.replace("\r\n", "\n").rstrip("\n")
    return t.replace("{name}", name).replace("{target}", target)


def out(event, ctx):
    return ('{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}'
            % (event, json.dumps(ctx, ensure_ascii=True))).encode("ascii")


def j(obj):
    return json.dumps(obj).encode("utf-8")


def start(cwd, sid="sess-1"):
    d = {"hook_event_name": "SessionStart", "source": "startup", "cwd": cwd}
    if sid is not None:
        d["session_id"] = sid
    return j(d)


def post(path, sid="sess-1", key="file_path", tool="Write"):
    d = {"hook_event_name": "PostToolUse", "tool_name": tool, "tool_input": {key: path}}
    if sid is not None:
        d["session_id"] = sid
    return j(d)


def build(root):
    master = os.path.join(root, "Black Box Safety - MASTER")
    cust = os.path.join(master, "Customers")
    win = os.path.join(root, "Blackbox Safety Team Site - Black Box Safety - MASTER", "Customers")
    p = {
        "master": master,
        "cust": cust,
        "acme": os.path.join(cust, "Acme"),
        "acme_rfq": os.path.join(cust, "Acme", "RFQ 10.21.26"),
        "beta": os.path.join(cust, "Beta"),
        "beta_deep": os.path.join(cust, "Beta", "Call 2", "Specs"),
        "gamma": os.path.join(cust, "Gamma"),
        "gamma_site": os.path.join(cust, "Gamma", "site"),
        "gamma_rfq": os.path.join(cust, "Gamma", "site", "rfq 1"),
        "gamma_other": os.path.join(cust, "Gamma", "other"),
        "odd": os.path.join(cust, "Café [Peña] Dept's"),
        "hidden": os.path.join(cust, ".claude", "x"),
        "decoy": os.path.join(root, "Elsewhere", "Customers", "Acme"),
        "delta": os.path.join(win, "Delta", "PO 7"),
        "delta_root": os.path.join(win, "Delta"),
    }
    for k in ("acme_rfq", "beta_deep", "gamma_rfq", "gamma_other", "odd", "hidden", "decoy", "delta"):
        os.makedirs(p[k])
    for f in (os.path.join(p["beta"], "CLAUDE.md"), os.path.join(p["gamma_site"], "CLAUDE.md"),
              os.path.join(cust, "loose.md")):
        open(f, "w").close()
    return p


def cases(p):
    acme_t = os.path.join(p["acme"], "CLAUDE.md")
    beta_md = os.path.join(p["beta"], "CLAUDE.md")
    site_md = os.path.join(p["gamma_site"], "CLAUDE.md")
    miss = lambda ev, root: out(ev, text("missing.md", os.path.basename(root),
                                         os.path.join(root, "CLAUDE.md")))
    pres = lambda found: out("SessionStart", text("present.md", "", found))
    a_file = os.path.join(p["acme_rfq"], "quote.md")
    return [
        # label, stdin, expected stdout. Order matters: the marker cases follow the ones that set it.
        ("session start in a customer with no CLAUDE.md", start(p["acme_rfq"]), miss("SessionStart", p["acme"])),
        ("write in the same customer, same session: once only", post(a_file), b""),
        ("session start again (compaction) still speaks", start(p["acme_rfq"]), miss("SessionStart", p["acme"])),
        ("write, a new session", post(a_file, sid="sess-2"), miss("PostToolUse", p["acme"])),
        ("write, no session_id: no marker, speaks", post(a_file, sid=None), miss("PostToolUse", p["acme"])),
        ("write, no session_id again: speaks again", post(a_file, sid=None), miss("PostToolUse", p["acme"])),
        ("notebook_path is read", post(os.path.join(p["acme"], "n.ipynb"), sid="sess-3",
                                       key="notebook_path", tool="NotebookEdit"), miss("PostToolUse", p["acme"])),
        ("session start in the customer root itself", start(p["acme"], sid="sess-4"), miss("SessionStart", p["acme"])),
        ("session start deep under a CLAUDE.md: present", start(p["beta_deep"]), pres(beta_md)),
        ("trailing separator on cwd", start(p["beta_deep"] + os.sep), pres(beta_md)),
        ("write under a CLAUDE.md is silent", post(os.path.join(p["beta_deep"], "s.pdf")), b""),
        ("nearest CLAUDE.md wins (site file)", start(p["gamma_rfq"]), pres(site_md)),
        ("sibling without one: missing at the customer root", post(os.path.join(p["gamma_other"], "x.md")),
         miss("PostToolUse", p["gamma"])),
        ("non-ASCII, brackets and an apostrophe in the name", start(p["odd"]), miss("SessionStart", p["odd"])),
        ("Windows-shaped MASTER folder name", start(p["delta"]), miss("SessionStart", p["delta_root"])),
        ("Customers itself is silent", start(p["cust"]), b""),
        ("MASTER root is silent", start(p["master"]), b""),
        ("a file sitting in Customers is silent", post(os.path.join(p["cust"], "loose.md")), b""),
        ("hidden folder is silent", start(p["hidden"]), b""),
        ("Customers not under MASTER is silent", start(p["decoy"]), b""),
        ("write the CLAUDE.md itself: silent once it exists", None, b""),   # filled in below
        ("after it exists, session start is present", start(p["acme_rfq"]), pres(acme_t)),
        ("unknown event", j({"hook_event_name": "Stop", "cwd": p["acme_rfq"]}), b""),
        ("cwd not a string", j({"hook_event_name": "SessionStart", "cwd": 42}), b""),
        ("tool_input null", j({"hook_event_name": "PostToolUse", "tool_input": None}), b""),
        ("tool_input a string", j({"hook_event_name": "PostToolUse", "tool_input": "x"}), b""),
        ("file_path blank", post("  "), b""),
        ("empty stdin", b"", b""),
        ("whitespace stdin", b"  \n", b""),
        ("garbage stdin", b"{not json", b""),
        ("top-level array", b"[1,2]", b""),
        ("BOM on stdin", b"\xef\xbb\xbf" + start(p["gamma_rfq"]), pres(site_md)),
    ]


def run(cmd, stdin_bytes, env):
    r = subprocess.run(cmd, input=stdin_bytes, capture_output=True, timeout=60, env=env)
    return r.returncode, r.stdout, r.stderr


def sequence(cmd, p, tmpdir):
    """Run every case in order under one interpreter; the CLAUDE.md step creates the file."""
    env = dict(os.environ, TMPDIR=tmpdir, TEMP=tmpdir, TMP=tmpdir)
    acme_md = os.path.join(p["acme"], "CLAUDE.md")
    results = []
    for label, stdin_bytes, want in cases(p):
        if stdin_bytes is None:
            open(acme_md, "w").close()
            stdin_bytes = post(acme_md, sid="sess-9")
        results.append((label, want) + run(cmd, stdin_bytes, env))
    os.remove(acme_md)
    return results


fail = 0


def check(label, cond, detail=""):
    global fail
    print(("PASS  " if cond else "FAIL  ") + label + (("  " + detail) if detail and not cond else ""))
    if not cond:
        fail += 1


root = tempfile.mkdtemp(prefix="bbs-customer-folder-")
try:
    p = build(os.path.join(root, "tree"))
    os.makedirs(os.path.join(root, "tmp-py"))
    py_res = sequence([sys.executable, os.path.join(HOOKS, "customer-folder.py")], p,
                      os.path.join(root, "tmp-py"))
    for label, want, code, o, err in py_res:
        check(f"[py] {label}: exit 0, no stderr", code == 0 and err == b"", f"exit={code} stderr={err[:160]!r}")
        check(f"[py] {label}: output", o == want, f"got={o[:120]!r} want={want[:120]!r}")
    if PS:
        os.makedirs(os.path.join(root, "tmp-ps"))
        ps_res = sequence([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                           os.path.join(HOOKS, "customer-folder.ps1")], p, os.path.join(root, "tmp-ps"))
        for (label, _w, _c, py_out, _e), (_l, _w2, code, o, err) in zip(py_res, ps_res):
            check(f"[ps] {label}: exit 0, no stderr", code == 0 and err == b"", f"exit={code} stderr={err[:160]!r}")
            check(f"[parity] {label}: ps == py bytes", o == py_out, f"ps={o[:120]!r} py={py_out[:120]!r}")
finally:
    shutil.rmtree(root, ignore_errors=True)

if not PS:
    if REQUIRE_PS:
        check("PowerShell on PATH (BBS_REQUIRE_PS=1)", False, "neither pwsh nor powershell found")
    else:
        print("SKIP  PowerShell not on PATH: parity with customer-folder.ps1 not exercised here")
else:
    print(f"      PowerShell used: {PS}")
print(f"{fail} failure(s)" if fail else "all pass")
sys.exit(1 if fail else 0)
