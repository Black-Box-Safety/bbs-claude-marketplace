#!/usr/bin/env python3
"""guard-tree.py / guard-tree.ps1 and desk-context.py / desk-context.ps1 must agree on every input.

Builds the same fixture tree run-tests.ps1 uses, in a temp dir, and runs every case through
the Python scripts (always) and the PowerShell scripts (under pwsh or powershell, whichever
is on PATH). For each case it checks the Python result against an expectation written here
independently, checks stderr is empty and the exit code is 0, and, when PowerShell ran,
checks the two interpreters agree:

  * guard-tree: the parsed decision (allow / deny) AND the deny reason string are equal.
    The JSON is compared parsed, not byte for byte, because PowerShell's ConvertTo-Json
    orders hashtable keys arbitrarily and escapes quotes differently between 5.1 and 7.
  * desk-context: stdout is equal after CRLF -> LF and trailing-newline normalisation.

When neither pwsh nor powershell is on PATH the PowerShell half is SKIPPED, not failed,
unless BBS_REQUIRE_PS=1 is set (CI sets it, so CI proves parity rather than skipping it).

Usage:  python3 plugins/bbs-sales/hooks/tests/parity.py
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
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"
PY = sys.executable


def run(cmd, payload):
    p = subprocess.run(cmd, input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=120)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def run_py(script, payload):
    return run([PY, os.path.join(HOOKS, script + ".py")], payload)


def run_ps(script, payload):
    return run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                os.path.join(HOOKS, script + ".ps1")], payload)


def decision(out):
    if not out.strip():
        return ("allow", "")
    d = json.loads(out)["hookSpecificOutput"]
    return (d["permissionDecision"], d["permissionDecisionReason"])


def ctx_norm(out):
    return out.replace("\r\n", "\n").rstrip("\n")


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root = tempfile.mkdtemp(prefix="bbs-hook-parity-")
    fails = 0
    try:
        tree = os.path.join(root, "All RFQ's by Agency")
        cdcr = os.path.join(tree, "CDCR (ALL)")
        mcsp = os.path.join(cdcr, "Mule Creek State Prison")
        filled = os.path.join(mcsp, "FILLED")
        os.makedirs(filled)
        os.makedirs(os.path.join(tree, "Cal Trans (ALL)"))
        os.makedirs(os.path.join(tree, ".CDTFA"))   # hidden: not a sibling to either half
        write(os.path.join(filled, "packet-b.pdf"), ["x"])
        write(os.path.join(mcsp, "quote-log.md"), [
            "| Date | Item | Quote# | Vehicle | Value | Outcome |",
            "|---|---|---|---|---|---|",
            "| 2026-03-04 | Nitrile gloves | SQ-1001 | NASPO | 2400 | won |"])
        write(os.path.join(mcsp, "FLAGS.md"), [
            "| Date | Skill/step | What happened | Caught before send? | Fixed by |",
            "|---|---|---|---|---|",
            "| 2026-09-15 | naspo-quote | wrong solicitation # | yes | (Parker: triage) |"])
        # A folder outside the desk tree that happens to carry its own quote-log.md.
        outside = os.path.join(root, "not-the-desk")
        write(os.path.join(outside, "quote-log.md"), ["| 2026-04-01 | Decoy row | SQ-9999 | - | 0 | - |"])
        # A deeper folder under the buyer, to prove the walk-up finds the buyer's files.
        deeper = os.path.join(mcsp, "2026", "RFQ-77")
        os.makedirs(deeper)
        packet = os.path.join(filled, "packet-b.pdf")
        sep = os.sep

        def pre(tool, **inp):
            return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}

        def start(cwd):
            return {"hook_event_name": "SessionStart", "source": "startup", "cwd": cwd}

        guard = [
            ("bash mv inside tree denied", pre("Bash", command=f'mv "{cdcr}" "{tree}{sep}CDCR"'), "deny"),
            ("bash mv elsewhere allowed", pre("Bash", command="mv a.txt b.txt"), "allow"),
            ("overwrite FILLED denied", pre("Write", file_path=packet, content="y"), "deny"),
            ("new FILLED file allowed", pre("Write", file_path=os.path.join(filled, "packet-c.pdf"), content="y"), "allow"),
            ("near-duplicate agency folder denied", pre("Bash", command=f'mkdir "{tree}{sep}CalTrans"'), "deny"),
            ("near-duplicate buyer via Write denied", pre("Write", file_path=os.path.join(cdcr, "Mule Creek Prison", "CLAUDE.md"), content="x"), "deny"),
            ("new distinct buyer allowed", pre("Write", file_path=os.path.join(cdcr, "Folsom State Prison", "CLAUDE.md"), content="x"), "allow"),
            ("edit quote-log allowed", pre("Edit", file_path=os.path.join(mcsp, "quote-log.md"), old_string="a", new_string="b"), "allow"),
            ("powershell rename inside tree denied", pre("PowerShell", command=f'Rename-Item "{cdcr}" \'CDCR\''), "deny"),
            ("bash rm of FILLED packet denied", pre("Bash", command=f'rm "{packet}"'), "deny"),
            ("bash cat of FILLED packet allowed", pre("Bash", command=f'cat "{packet}"'), "allow"),
            ("bash redirect FROM FILLED elsewhere allowed", pre("Bash", command=f'pdftotext "{packet}" > "{root}{sep}out.txt"'), "allow"),
            ("bash redirect INTO FILLED denied", pre("Bash", command=f'echo y > "{packet}"'), "deny"),
            ("bash cp ONTO FILLED packet denied", pre("Bash", command=f'cp "{root}{sep}new.pdf" "{packet}"'), "deny"),
            ("bash cp OUT of FILLED allowed", pre("Bash", command=f'cp "{packet}" "{root}{sep}copy.pdf"'), "allow"),
            ("powershell Set-Content onto FILLED denied", pre("PowerShell", command=f'Set-Content -Path "{packet}" -Value y'), "deny"),
            ("bash tee onto FILLED denied", pre("Bash", command=f'echo y | tee "{packet}"'), "deny"),
            ("acronym typo agency folder denied", pre("Bash", command=f'mkdir "{tree}{sep}CDRC (ALL)"'), "deny"),
            ("hidden folder is not a sibling", pre("Bash", command=f'mkdir "{tree}{sep}CDTFA"'), "allow"),
            ("lower-case tool name still guarded", pre("bash", command=f'mv "{cdcr}" "{tree}{sep}CDCR"'), "deny"),
            ("notebook path under FILLED denied", pre("NotebookEdit", notebook_path=packet), "deny"),
            ("empty tool_input allowed", {"hook_event_name": "PreToolUse", "tool_name": "Bash"}, "allow"),
            ("unknown tool allowed", pre("Read", file_path=packet), "allow"),
        ]
        ctx = [
            ("session context has precedent and flags", start(mcsp),
             lambda o: "PRECEDENT" in o and "SQ-1001" in o and "OPEN FLAGS" in o and "wrong solicitation" in o),
            ("session context found from a deeper folder", start(deeper), lambda o: "SQ-1001" in o),
            ("session context silent outside tree", start(root), lambda o: o == ""),
            ("session context silent outside tree with quote-log", start(outside), lambda o: o == ""),
            ("session context silent for a missing cwd", start(os.path.join(tree, "nope")), lambda o: o == ""),
        ]

        def check(ok, name, detail=""):
            nonlocal fails
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  {detail}"))
            if not ok:
                fails += 1

        for name, payload, want in guard:
            rc, out, err = run_py("guard-tree", payload)
            got = decision(out)
            check(rc == 0 and err == "" and got[0] == want, name, f"py rc={rc} got={got[0]!r} err={err.strip()!r}")
            if PS:
                prc, pout, perr = run_ps("guard-tree", payload)
                pgot = decision(pout)
                check(prc == 0 and perr == "" and pgot == got, name + " [parity]",
                      f"ps rc={prc} ps={pgot!r} py={got!r} err={perr.strip()[:200]!r}")
        for name, payload, pred in ctx:
            rc, out, err = run_py("desk-context", payload)
            o = ctx_norm(out)
            check(rc == 0 and err == "" and pred(o), name, f"py rc={rc} out={o[:120]!r} err={err.strip()!r}")
            if PS:
                prc, pout, perr = run_ps("desk-context", payload)
                check(prc == 0 and perr == "" and ctx_norm(pout) == o, name + " [parity]",
                      f"ps rc={prc} ps={ctx_norm(pout)[:120]!r} py={o[:120]!r} err={perr.strip()[:200]!r}")
        # Garbage on stdin: both halves stay silent and exit 0.
        for script in ("guard-tree", "desk-context"):
            for raw in (b"", b"not json", b"[1,2]"):
                p = subprocess.run([PY, os.path.join(HOOKS, script + ".py")], input=raw, capture_output=True)
                check(p.returncode == 0 and p.stdout == b"" and p.stderr == b"", f"{script} silent on {raw!r}")
                if PS:
                    q = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                                        os.path.join(HOOKS, script + ".ps1")], input=raw, capture_output=True)
                    check(q.returncode == 0 and q.stdout.strip() == b"" and q.stderr == b"",
                          f"{script} silent on {raw!r} [parity]", f"rc={q.returncode} out={q.stdout[:80]!r} err={q.stderr[:120]!r}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if not PS:
        msg = "PowerShell parity SKIPPED: neither pwsh nor powershell is on PATH"
        if REQUIRE_PS:
            print("FAIL  " + msg + " and BBS_REQUIRE_PS=1")
            fails += 1
        else:
            print("SKIP  " + msg)
    else:
        print(f"parity checked against {PS}")
    print("\nall pass" if fails == 0 else f"\n{fails} FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
