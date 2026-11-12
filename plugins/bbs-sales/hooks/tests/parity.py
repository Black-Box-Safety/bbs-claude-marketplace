#!/usr/bin/env python3
"""guard-tree.py / guard-tree.ps1 and desk-context.py / desk-context.ps1 must agree on every input;
rfq-record-hook.ps1 must give its python3 notice and nothing else.

Builds the same fixture tree run-tests.ps1 uses, in a temp dir, and runs every case through
the Python scripts (always) and the PowerShell scripts (under pwsh or powershell, whichever
is on PATH). For each case it checks the Python result against an expectation written here
independently, checks stderr is empty and the exit code is 0, and, when PowerShell ran,
checks the two interpreters agree:

  * guard-tree: the parsed decision (allow / deny) AND the deny reason string are equal.
    The JSON is compared parsed, not byte for byte, because PowerShell's ConvertTo-Json
    orders hashtable keys arbitrarily and escapes quotes differently between 5.1 and 7.
  * desk-context: stdout is equal after CRLF -> LF and trailing-newline normalisation. The
    PostToolUse JSON is compared as bytes; BBS_TODAY pins "today" and every run gets its own temp
    dir, so one interpreter's once-per-session marker never silences the other.

  * rfq-record-hook: not a twin. The Python half is the only validator; the PowerShell half must
    return the "needs python3; this edit was not checked" notice for an RFQ.md under the tree and
    stay silent otherwise. hooks.json must run python3 first.

When neither pwsh nor powershell is on PATH the PowerShell half is SKIPPED, not failed,
unless BBS_REQUIRE_PS=1 is set (CI sets it, so CI proves parity rather than skipping it).

Usage:  python3 plugins/bbs-sales/hooks/tests/parity.py
Exit 0 = all pass. Stdlib only. Writes only inside a temp dir it removes.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.dirname(HERE)
FIXTURES = os.path.join(os.path.dirname(HOOKS), "scripts", "tests", "fixtures")
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"
PY = sys.executable
# What rfq-record-hook.ps1 must say, written here independently of the script.
RFQ_PS_NOTICE = ("bbs-sales: RFQ record check needs python3; this edit was not checked. Install Python 3 "
                 "(rerun the bootstrap) so RFQ.md is validated and rfq-state.json is written.")


TODAY = "2026-10-30"
_runs = [0]
_scratch = [None]


def fresh_env():
    """An env with a new temp dir (markers live there) and today pinned."""
    _runs[0] += 1
    t = os.path.join(_scratch[0], "tmp%d" % _runs[0])
    os.makedirs(t)
    env = dict(os.environ)
    env.update({"TMPDIR": t, "TEMP": t, "TMP": t, "BBS_TODAY": TODAY})
    return env


def run(cmd, payload, env=None):
    p = subprocess.run(cmd, input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=120, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def run_py(script, payload, env=None):
    return run([PY, os.path.join(HOOKS, script + ".py")], payload, env)


def run_ps(script, payload, env=None):
    return run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                os.path.join(HOOKS, script + ".ps1")], payload, env)


def added_context(out):
    """additionalContext from a PostToolUse reply, '' when silent."""
    if not out.strip():
        return ""
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


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
    _scratch[0] = os.path.join(root, "scratch")
    os.makedirs(_scratch[0])
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

        # CA-shaped fixtures. Three levels (agency > institution > buyer) with a dated deal folder,
        # a quote-log in mixed date styles and order, bullet and table FLAGS, non-ASCII text.
        joe = os.path.join(tree, "CDCR (ALL)", "CAL - Calipatria State Prison - 887895116", "Joe Ketner")
        write(os.path.join(joe, "CLAUDE.md"), ["# Joe Ketner"])
        write(os.path.join(joe, "quote-log.md"), [
            "# Quote log - Joe Ketner",
            "",
            "| Date | Item | Quote # | Vehicle | Value | Outcome |",
            "|---|---|---|---|---|---|",
            "| 9.14.26 | V-belts x14 lines | 900021 | competitive OBS 4007(A) | $3,668.70 | priced, awaiting signature |",
            "| 10.7.26 | Refrigerants R-410A | SQ-105100 | competitive OBS 4007(B) | $23,981.10 | packet signed, not sent |",
            "| 2026-03-04 | Nitrile gloves | SQ-1001 | NASPO | 2400 | won |",
            "| 7.13.23 | Gloves | SQ-0001 | NASPO | 100 | sent |",
            "| 6.1.26 | Widgets | SQ-2002 | NASPO | 50 | `lost` - price |",
            "| 8.1.26 | Boxes | - | NASPO | 10 | [FLAG: no SQ on file] |",
            "| 9.1.26 | Boxes \u00d74 \u2014 blue | SQ-3003 | NASPO | 20 | no answer - no order in BC |",
            "| 8.15.26 | Rope | SQ-6006 | NASPO | 15 | no bid - out of scope |",
            "| 8.20.26 | Cones | SQ-7007 | NASPO | 12 | cancelled - solicitation withdrawn |",
            "| 13.40.26 | Bad date row | SQ-4004 | NASPO | 5 | sent |",
            "| - | Undated row | SQ-5005 | NASPO | 5 | sent |",
            "",
            "Rows above 9.14.26 predate this log."])
        write(os.path.join(joe, "FLAGS.md"), [
            "# FLAGS - Joe Ketner",
            "",
            "| Date | What happened | Status |",
            "|---|---|---|",
            "| 2026-10-23 | worksheet rows overwritten | open - Parker to triage |",
            "| 10.2.26 | old radio bug | closed 10.3.26 - fixed |",
            "",
            "- 9.20.26 bullet flag one",
            "- undated bullet flag",
            "- [x] done bullet flag",
            "* ~~struck bullet flag~~"])
        os.makedirs(os.path.join(joe, "9.14.26"))
        write(os.path.join(joe, "Gloves 7.13.23", "quote.xlsx"), ["x"])
        write(os.path.join(joe, "9.14.26", "packet", "form.pdf"), ["x"])
        # Two levels (agency > buyer), no CLAUDE.md, only recent rows.
        kelly = os.path.join(tree, "CARB - Air Resource Board - 888161763", "Kelly Peng")
        write(os.path.join(kelly, "quote-log.md"), [
            "| Date | Item | Quote # | Vehicle | Value | Outcome |",
            "|---|---|---|---|---|---|",
            "| 10.12.26 | Office supplies | [pending] | OPEN | [pending] | logged |",
            "| 10.28.26 | Office supplies SCHQ | SQ-105283 | OPEN | 190.76 | logged |"])
        write(os.path.join(kelly, "FLAGS.md"), ["| Date | What | Status |", "|---|---|---|", "| 2026-10-27 | bad SQ number | open |"])
        write(os.path.join(kelly, "10.12.26", "SacHQ", "10.26 refresh", "quote.pdf"), ["x"])
        # Two levels, buyer folder exists with no files at all.
        newb = os.path.join(tree, "DWR - Water Resources", "New Buyer")
        write(os.path.join(newb, "10.30.26", "rfq.pdf"), ["x"])
        # An institution folder (buyers one level down) with a stray deal folder at its own level.
        inst = os.path.join(tree, "CDCR (ALL)", "CMF - California Medical Facility")
        write(os.path.join(inst, "Some Buyer", "CLAUDE.md"), ["# Some Buyer"])
        write(os.path.join(inst, "8.11.26", "batteries.pdf"), ["x"])
        write(os.path.join(joe, "AIU-21", "form.pdf"), ["x"])
        write(os.path.join(tree, ".remember", "Hidden Buyer", "1.1.26", "x.txt"), ["x"])

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

        def post(path, sid="s1", tool="Write", **extra):
            p = {"hook_event_name": "PostToolUse", "tool_name": tool, "session_id": sid, "tool_input": {"file_path": path}}
            p.update(extra)
            return p

        def at(*parts):
            return os.path.join(*parts)

        joe_deal = at(joe, "9.14.26", "packet", "form.pdf")
        joe_ctx_start = start(joe)

        def has_all(*needles):
            return lambda c: all(n in c for n in needles)

        def lacks_all(*needles):
            return lambda c: not any(n in c for n in needles)

        def before(a, b):
            return lambda c: a in c and b in c and c.index(a) < c.index(b)

        # (name, payload, predicate on the added context). Each runs in a fresh temp dir.
        writes = [
            ("first write names the buyer files", post(joe_deal),
             has_all("BUYER DESK -- first write in 9.14.26 for CDCR (ALL)/CAL - Calipatria State Prison - 887895116/Joe Ketner",
                     "CLAUDE.md --", "quote-log.md --", "FLAGS.md --")),
            ("first write: nothing missing", post(joe_deal), lacks_all("MISSING:")),
            ("first write: precedent newest first", post(joe_deal), before("| 10.7.26 |", "| 9.14.26 |")),
            ("first write: older precedent after newer", post(joe_deal), before("| 9.14.26 |", "| 2026-03-04 |")),
            ("first write: non-ASCII row survives", post(joe_deal), has_all("Boxes \u00d74 \u2014 blue")),
            ("first write: closes two stale rows, oldest first", post(joe_deal),
             lambda c: "OUTCOMES TO CLOSE -- 2 quote-log rows older than 30 days" in c
             and before("| 7.13.23 | Gloves", "| 9.14.26 | V-belts")(c.split("OUTCOMES TO CLOSE", 1)[1])),
            ("first write: final, flagged, recent, bad-date and undated rows not listed", post(joe_deal),
             lambda c: all(x not in c.split("OUTCOMES TO CLOSE", 1)[1].split("Business Central", 1)[0]
                           for x in ("SQ-1001", "SQ-2002", "no SQ on file", "SQ-105100", "SQ-3003", "SQ-4004", "SQ-5005",
                                     "SQ-6006", "SQ-7007"))),
            ("first write: close-out names every final outcome", post(joe_deal),
             has_all("no final outcome (won / lost / no answer / no bid / cancelled)")),
            ("first write: close-out rules present", post(joe_deal),
             has_all("never a guess", "900-series draft number", "ruling from Parker")),
            ("first write: flags incl. bullets, closed dropped", post(joe_deal),
             lambda c: all(x in c for x in ("worksheet rows overwritten", "bullet flag one", "undated bullet flag"))
             and not any(x in c for x in ("old radio bug", "done bullet flag", "struck bullet flag"))),
            ("edit in a dated deal folder with a space", post(at(joe, "Gloves 7.13.23", "quote.xlsx"), tool="Edit"), has_all("first write in Gloves 7.13.23")),
            ("two-level agency: buyer files found, CLAUDE.md missing", post(at(kelly, "10.12.26", "SacHQ", "10.26 refresh", "quote.pdf")),
             lambda c: "for CARB - Air Resource Board - 888161763/Kelly Peng" in c and "MISSING: CLAUDE.md -- create from" in c
             and "OUTCOMES TO CLOSE" not in c and before("| 10.28.26 |", "| 10.12.26 |")(c) and "bad SQ number" in c),
            ("two-level agency: every buyer file missing", post(at(newb, "10.30.26", "rfq.pdf")),
             has_all("MISSING: CLAUDE.md, quote-log.md, FLAGS.md", "for DWR - Water Resources/New Buyer")),
            ("no session id still speaks", {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": joe_deal}},
             has_all("BUYER DESK")),
            ("silent: institution folder with its own stray deal", post(at(inst, "8.11.26", "batteries.pdf")), lambda c: c == ""),
            ("silent: deal folder without a date", post(at(joe, "AIU-21", "form.pdf")), lambda c: c == ""),
            ("silent: hidden folder", post(at(tree, ".remember", "Hidden Buyer", "1.1.26", "x.txt")), lambda c: c == ""),
            ("silent: file directly in the buyer folder", post(at(joe, "quote-log.md")), lambda c: c == ""),
            ("silent: file in the deal folder's parent chain only (FILLED)", post(at(joe, "FILLED", "x.pdf")), lambda c: c == ""),
            ("silent: deal folder at agency level", post(at(tree, "CARB - Air Resource Board - 888161763", "10.12.26", "x.pdf")), lambda c: c == ""),
            ("silent: outside the tree", post(at(outside, "9.14.26", "x.pdf")), lambda c: c == ""),
            ("silent: no file_path", {"hook_event_name": "PostToolUse", "session_id": "s1", "tool_input": {}}, lambda c: c == ""),
            ("silent: tool_input missing", {"hook_event_name": "PostToolUse", "session_id": "s1"}, lambda c: c == ""),
        ]
        sessions = [
            ("session start: newest first, mixed date styles", joe_ctx_start,
             lambda o: o.index("| 10.7.26 |") < o.index("| 9.14.26 |") < o.index("| 2026-03-04 |") < o.index("| 7.13.23 |")),
            ("session start: bullets and table flags, closed dropped", joe_ctx_start,
             lambda o: "bullet flag one" in o and "worksheet rows overwritten" in o and "old radio bug" not in o and "done bullet" not in o),
            ("session start: no close-out list", joe_ctx_start, lambda o: "OUTCOMES TO CLOSE" not in o),
            ("session start: two-level buyer", start(kelly), lambda o: "| 10.28.26 |" in o and "bad SQ number" in o),
        ]

        def check(ok, name, detail=""):
            nonlocal fails
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  {detail}"))
            if not ok:
                fails += 1

        # One source for the final outcomes: rfq_record.OUTCOMES. Both desk-context twins must match it.
        sys.path.insert(0, os.path.join(os.path.dirname(HOOKS), "scripts"))
        import rfq_record
        sys.path.insert(0, HOOKS)
        import importlib.util
        spec = importlib.util.spec_from_file_location("desk_context", os.path.join(HOOKS, "desk-context.py"))
        dc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dc)
        check(list(dc.FINAL_OUTCOMES) == rfq_record.OUTCOMES, "outcomes: desk-context.py matches rfq_record.OUTCOMES",
              f"py={list(dc.FINAL_OUTCOMES)} canon={rfq_record.OUTCOMES}")
        with open(os.path.join(HOOKS, "desk-context.ps1"), encoding="utf-8") as fh:
            m = re.search(r"^\$FINAL_OUTCOMES = @\((.*)\)\s*$", fh.read(), re.M)
        ps_list = re.findall(r"'([^']*)'", m.group(1)) if m else None
        check(ps_list == rfq_record.OUTCOMES, "outcomes: desk-context.ps1 matches rfq_record.OUTCOMES",
              f"ps={ps_list} canon={rfq_record.OUTCOMES}")
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
        for name, payload, pred in sessions:
            rc, out, err = run_py("desk-context", payload, fresh_env())
            o = ctx_norm(out)
            check(rc == 0 and err == "" and pred(o), name, f"py rc={rc} out={o[:200]!r} err={err.strip()!r}")
            if PS:
                prc, pout, perr = run_ps("desk-context", payload, fresh_env())
                check(prc == 0 and perr == "" and ctx_norm(pout) == o, name + " [parity]",
                      f"ps rc={prc} ps={ctx_norm(pout)[:200]!r} py={o[:200]!r} err={perr.strip()[:200]!r}")
        for name, payload, pred in writes:
            rc, out, err = run_py("desk-context", payload, fresh_env())
            c = added_context(out) if rc == 0 else ""
            check(rc == 0 and err == "" and pred(c), name, f"py rc={rc} ctx={c[:300]!r} err={err.strip()!r}")
            if PS:
                prc, pout, perr = run_ps("desk-context", payload, fresh_env())
                check(prc == 0 and perr == "" and pout.replace("\r\n", "\n").rstrip("\n") == out.replace("\r\n", "\n").rstrip("\n"),
                      name + " [parity]", f"ps rc={prc} ps={pout[:200]!r} py={out[:200]!r} err={perr.strip()[:200]!r}")
        # Once per buyer per session: the second write is silent, another buyer or session still speaks.
        for label, runner in (("py", run_py), ("ps", run_ps)):
            if label == "ps" and not PS:
                continue
            env = fresh_env()
            first = added_context(runner("desk-context", post(joe_deal, sid="once"), env)[1])
            again = added_context(runner("desk-context", post(at(joe, "Gloves 7.13.23", "quote.xlsx"), sid="once"), env)[1])
            other_buyer = added_context(runner("desk-context", post(at(kelly, "10.12.26", "SacHQ", "10.26 refresh", "quote.pdf"), sid="once"), env)[1])
            other_session = added_context(runner("desk-context", post(joe_deal, sid="twice"), env)[1])
            check(first != "" and again == "" and other_buyer != "" and other_session != "",
                  f"once per buyer per session [{label}]",
                  f"first={bool(first)} again={bool(again)} other_buyer={bool(other_buyer)} other_session={bool(other_session)}")
        # rfq-record-hook: ONE validator. The Python half validates and compiles rfq-state.json.
        # The PowerShell half (hooks.json runs it only when python3 is missing) validates nothing:
        # for an RFQ.md under the tree it must return exactly RFQ_PS_NOTICE, exit 0, empty stderr and
        # no sidecar, whatever the record says; for any other path it must be silent. It is NOT
        # compared against the Python decision, because it does not make one.
        # The sidecar is checked for existence only (generated_at is not deterministic).
        hooks_cfg = json.load(open(os.path.join(HOOKS, "hooks.json"), encoding="utf-8"))
        rec_cmds = [h["command"] for e in hooks_cfg["hooks"]["PostToolUse"] for h in e["hooks"]
                    if "rfq-record-hook" in h["command"]]
        check(len(rec_cmds) == 1 and rec_cmds[0].startswith("python3 ")
              and rec_cmds[0].index("rfq-record-hook.py") < rec_cmds[0].index("rfq-record-hook.ps1"),
              "rfq-record hooks.json runs python3 first", repr(rec_cmds)[:300])
        def fixture(name):
            with open(os.path.join(FIXTURES, name), encoding="utf-8", newline="") as fh:
                return fh.read()

        good = fixture("v2_naspo_full.md")
        bad = good.replace("| sent |", "| Sent |", 1)
        assert bad != good
        deal = os.path.join(tree, "CMD - 880000001", "Pat Example", "widgets 10.27.26")
        other = os.path.join(root, "Customers", "Bechtel", "x")
        os.makedirs(deal)
        os.makedirs(other)
        # (name, file content, file_path as sent in the hook JSON, expected exit, sidecar written, first-line check)
        deal_rfq = os.path.join(deal, "RFQ.md")
        # NOTE: on POSIX the backslash path is just an odd file name; the case passes only because
        # both halves read the same file we create at that name. Real Windows paths are the target.
        bs_path = deal_rfq.replace("/", "\\")
        rfq_cases = [
            ("rfq-record valid_v2", good, deal_rfq, 0, True, None),
            ("rfq-record bad_status_enum", bad, deal_rfq, 2, False, "bbs-sales rfq-record: 1 problem(s) in RFQ.md"),
            ("rfq-record not_an_rfq_path", bad, os.path.join(other, "RFQ.md"), 0, False, None),
            ("rfq-record windows_backslash_path", bad, bs_path, 2, False, "bbs-sales rfq-record: 1 problem(s) in RFQ.md"),
            ("rfq-record bad_header_stage", good.replace("**Stage:** delivered to rep", "**Stage:** Sent", 1), deal_rfq, 2, False, "bbs-sales rfq-record: 1 problem(s) in RFQ.md"),
            ("rfq-record v1_record", fixture("v1_cmd_hvac.md"), deal_rfq, 0, False, None),
            ("rfq-record legacy_no_status_section", re.sub(r"\*\*Stage:\*\*[^\n]*\n", "", good[:good.index("## Status")]), deal_rfq, 0, False, None),
            ("rfq-record v2_with_stage_but_broken_status", good.replace("| Stage | Date | Evidence |", "| Stage | When | Evidence |", 1), deal_rfq, 2, False, "bbs-sales rfq-record: 1 problem(s) in RFQ.md"),
            ("rfq-record v2_quotes_v1_header", good.replace("## Flags\n", "## Flags\n\nThe old header was `| Stage | State | Date |` in v1.\n", 1), deal_rfq, 0, True, None),
        ]
        for name, content, fpath, want_rc, want_state, want_first in rfq_cases:
            payload = {"hook_event_name": "PostToolUse", "tool_name": "Write",
                       "tool_input": {"file_path": fpath, "content": content}}
            # Backslash paths are not real files on this OS: write the content at the forward-slash
            # location the hook will resolve (the hook opens the path it was given, so a Windows-style
            # path only works here when the OS treats it as a file name; skip the open by mirroring).
            real = deal_rfq if fpath == bs_path else fpath
            for stale in (os.path.join(os.path.dirname(real), "rfq-state.json"), os.path.join(deal, "rfq-state.json")):
                if os.path.exists(stale):
                    os.remove(stale)
            os.makedirs(os.path.dirname(real), exist_ok=True)
            with open(real, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
            if fpath == bs_path and os.sep == "/":
                # On POSIX the backslash string is a single odd file name; create it so the hook can read it.
                with open(fpath, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
            rc, out, err = run_py("rfq-record-hook", payload)
            state = os.path.exists(os.path.join(os.path.dirname(real), "rfq-state.json"))
            first = err.split("\n", 1)[0].strip()
            is_v1 = name.endswith(("v1_record", "legacy_no_status_section"))
            ok = rc == want_rc and (out == "" or is_v1) and state == want_state
            if is_v1:
                ok = ok and "legacy format" in json.loads(out)["systemMessage"] and "migrate" in json.loads(out)["systemMessage"]
            ok = ok and ((err == "") if want_rc == 0 else (first == want_first))
            check(ok, name, f"py rc={rc} state={state} out={out[:80]!r} err={err[:200]!r}")
            if PS:
                for stale in (os.path.join(deal, "rfq-state.json"),):
                    if os.path.exists(stale):
                        os.remove(stale)
                prc, pout, perr = run_ps("rfq-record-hook", payload)
                pstate = os.path.exists(os.path.join(deal, "rfq-state.json"))
                in_tree = fpath != os.path.join(other, "RFQ.md")
                if in_tree:
                    try:
                        pmsg = json.loads(pout)["systemMessage"]
                    except (ValueError, KeyError, TypeError):
                        pmsg = None
                    pok = prc == 0 and perr.strip() == "" and not pstate and pmsg == RFQ_PS_NOTICE
                else:
                    pok = prc == 0 and perr.strip() == "" and not pstate and pout.strip() == ""
                check(pok, name + " [ps notice]", f"ps rc={prc} state={pstate} out={pout[:200]!r} err={perr[:200]!r}")
            if fpath == bs_path and os.sep == "/" and os.path.exists(fpath):
                os.remove(fpath)
        # Garbage on stdin: both halves stay silent and exit 0.
        for script in ("guard-tree", "desk-context", "rfq-record-hook"):
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
