#!/usr/bin/env python3
"""desk-learn.py and desk-learn.ps1 must print the same thing for every input, and the hook
must only ever remind.

Builds a synthetic CA tree and Sentinel tree in a temp dir and runs one scripted session through the
Python hook (always) and the PowerShell hook (pwsh or powershell, whichever is on PATH), each with
its own temp dir so one interpreter's once-per-session markers never silence the other. Every step's
Python output is checked against an expectation written here; when PowerShell ran, the two outputs
are compared parsed (key order and escaping differ between 5.1 and 7).

Also checks: the reminder is fixed text that quotes no file content; it never blocks (exit 0, no
stderr, no "decision" on a PostToolUse reply); the Stop backstop speaks once, defaults to a message,
and resumes the turn only when BBS_DESK_LEARN_STOP=continue and stop_hook_active is not set; the shell
entry (hooks/desk-learn.sh) starts no interpreter for input that is nowhere near a desk; hooks.json
wires both events.

Without PowerShell the parity half is SKIPPED, not failed, unless BBS_REQUIRE_PS=1 (CI sets it).

Usage:  python3 plugins/bbs-sales/hooks/tests/desk_learn_parity.py
Exit 0 = all pass. Stdlib only. Writes only inside a temp dir it removes.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.dirname(HERE)
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"
PY = sys.executable
PY_CMD = [PY, os.path.join(HOOKS, "desk-learn.py")]
PS_CMD = [PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
          os.path.join(HOOKS, "desk-learn.ps1")] if PS else None

# The reminder, written here independently of the scripts (spec section 8, verbatim).
REMINDER = ("Key change: {event} in {folder}. Close the loop: ask the rep one question. Is there anything "
            "about this buyer or site to remember? If so, run `desk-remember` with their words. Did this "
            "deal teach a lesson? If so, propose one `lessons.md` line and append it on their yes.")
STOP_MESSAGE_START = "bbs-sales: key changes were made this session"
STOP_REASON_START = "Key changes were made this session and nothing was captured or closed."

fails = 0
skipped_ps = False
_runs = [0]


def check(ok, name, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  " + str(detail)[:600]))
    if not ok:
        fails += 1


def fresh_env(root, extra=None):
    _runs[0] += 1
    t = os.path.join(root, "tmp%d" % _runs[0])
    os.makedirs(t)
    env = dict(os.environ)
    env.pop("BBS_DESK_LEARN_STOP", None)
    env.update({"TMPDIR": t, "TEMP": t, "TMP": t})
    env.update(extra or {})
    return env


def run(cmd, payload, env):
    p = subprocess.run(cmd, input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=120, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace").replace("\r\n", "\n"), p.stderr.decode("utf-8", "replace")


def put(path, text="x", age=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    if age is not None:
        t = time.time() - age
        os.utime(path, (t, t))


def rfq(stage):
    return "# RFQ - Pat Example\n\n**Received:** 2026-11-02 via email\n**Stage:** %s\n\n## Lines\n" % stage


def state(stage):
    return json.dumps({"stage": stage, "schema": 2})


def ctx(out):
    if not out.strip():
        return None
    j = json.loads(out)
    return j["hookSpecificOutput"]["additionalContext"] if "hookSpecificOutput" in j else j


def post(tool, sid="s1", **inp):
    return {"hook_event_name": "PostToolUse", "session_id": sid, "tool_name": tool, "tool_input": inp}


def stop(sid="s1", active=False):
    return {"hook_event_name": "Stop", "session_id": sid, "stop_hook_active": active}


def main():
    global skipped_ps
    root = tempfile.mkdtemp(prefix="bbs-desk-learn-")
    try:
        ca = os.path.join(root, "Customers", "State of CA Agencies", "All RFQ's by Agency", "CDCR (ALL)",
                          "CAL - Calipatria State Prison - 887895116")
        joe = os.path.join(ca, "Joe Ketner")
        ann = os.path.join(ca, "Ann Other")
        sen = os.path.join(root, "Customers", "Bechtel", "sentinel")
        rfp = os.path.join(sen, "utah-sentinel", "rfp-825025-pig-spill")
        deals = {k: os.path.join(joe, "Gloves " + k) for k in ("11.3.26", "11.4.26", "11.5.26", "11.6.26", "11.9.26", "11.10.26")}
        # RFQ.md fixtures on disk: the hook reads the Stage header after the write.
        put(os.path.join(deals["11.3.26"], "RFQ.md"), rfq("priced"))
        put(os.path.join(deals["11.4.26"], "RFQ.md"), rfq("sent"))
        put(os.path.join(deals["11.5.26"], "RFQ.md"), rfq("outcome"))
        put(os.path.join(deals["11.5.26"], "rfq-state.json"), state("outcome"), age=3600)   # already outcome: not a move
        put(os.path.join(deals["11.6.26"], "RFQ.md"), rfq("outcome"))
        put(os.path.join(deals["11.6.26"], "rfq-state.json"), state("sent"), age=3600)      # sent -> outcome: a move
        put(os.path.join(deals["11.9.26"], "RFQ.md"), rfq("sent"))
        put(os.path.join(deals["11.9.26"], "rfq-state.json"), state("sent"), age=0)         # compiled a moment ago by rfq-record
        put(os.path.join(joe, "quote-log.md"), "| Date | Item |\n|---|---|\n")
        put(os.path.join(sen, "learning", "quote-log.md"), "| Date | RFQ |\n|---|---|\n")

        row = "| 2026-11-16 | Gloves | SQ-900001 | NASPO | won |"
        sentinel_row = "| 2026-11-16 | 835823 | VSFB | won |"
        banner = "> **Status (2026-11-16): SENT.** Quote out."

        steps = [
            # (label, payload, expected: None for silence, else (event words, folder))
            ("RFQ.md at priced is silent", post("Write", file_path=os.path.join(deals["11.3.26"], "RFQ.md"), content="x"), None),
            ("RFQ.md moved to sent (no state yet)", post("Write", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), content="x"),
             ("RFQ stage moved to sent", "Gloves 11.4.26")),
            ("the same move again is silent (once per deal per event per session)",
             post("Edit", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), old_string="a", new_string="b"), None),
            ("RFQ.md already outcome in rfq-state.json is not a move", post("Write", file_path=os.path.join(deals["11.5.26"], "RFQ.md"), content="x"), None),
            ("RFQ.md sent -> outcome is a move", post("Write", file_path=os.path.join(deals["11.6.26"], "RFQ.md"), content="x"),
             ("RFQ stage moved to outcome", "Gloves 11.6.26")),
            ("a state file compiled a moment ago does not hide the move", post("Edit", file_path=os.path.join(deals["11.9.26"], "RFQ.md"), old_string="a", new_string="b"),
             ("RFQ stage moved to sent", "Gloves 11.9.26")),
            ("rfq_record.py set-stage sent",
             post("Bash", command='python3 "/x/scripts/rfq_record.py" set-stage "%s/RFQ.md" sent --date 2026-11-16 --evidence "to buyer"' % deals["11.10.26"]),
             ("RFQ stage moved to sent", "Gloves 11.10.26")),
            ("rfq_record.py set-stage priced is silent",
             post("Bash", command='python3 /x/scripts/rfq_record.py set-stage "%s/RFQ.md" priced --date 2026-11-16 --evidence "x"' % deals["11.10.26"]), None),
            ("quote-log row added", post("Edit", file_path=os.path.join(joe, "quote-log.md"), old_string="|---|---|", new_string="|---|---|\n" + row),
             ("quote-log row added or Outcome set", "Joe Ketner")),
            ("quote-log edit with no table row is silent", post("Edit", file_path=os.path.join(ann, "quote-log.md"), old_string="a", new_string="a note"), None),
            ("quote-log append by Bash", post("Bash", command="echo '%s' >> \"%s/quote-log.md\"" % (row, ann)),
             ("quote-log row added or Outcome set", "Ann Other")),
            ("MultiEdit on a quote-log with a row", post("MultiEdit", file_path=os.path.join(ann, "other", "quote-log.md"),
                                                          edits=[{"old_string": "a", "new_string": "z"}, {"old_string": "b", "new_string": row}]),
             ("quote-log row added or Outcome set", "other")),
            ("new file in FILLED/", post("Write", file_path=os.path.join(deals["11.3.26"], "FILLED", "BBS_STD204.pdf"), content="x"),
             ("new file in FILLED/", "Gloves 11.3.26")),
            ("bbs-fill writing into FILLED/",
             post("Bash", command='"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/naspo-quote/scripts/fill.py" --out "%s/FILLED/a.pdf"' % deals["11.4.26"]),
             ("new file in FILLED/", "Gloves 11.4.26")),
            ("a PO file written in a deal folder", post("Write", file_path=os.path.join(deals["11.3.26"], "PO 4500123.md"), content="x"),
             ("PO, award or NOA file written", "Gloves 11.3.26")),
            ("an ordinary file is silent", post("Write", file_path=os.path.join(deals["11.3.26"], "notes.md"), content="x"), None),
            ("a name that only contains the letters po is silent", post("Write", file_path=os.path.join(deals["11.3.26"], "Posture.md"), content="x"), None),
            ("an award file in a Sentinel RFP folder", post("Write", file_path=os.path.join(rfp, "Award-Notice.md"), content="x"),
             ("PO, award or NOA file written", "rfp-825025-pig-spill")),
            ("Sentinel quote-log appended", post("Edit", file_path=os.path.join(sen, "learning", "quote-log.md"), old_string="|---|---|", new_string="|---|---|\n" + sentinel_row),
             ("Sentinel quote-log appended", "learning")),
            ("RFP CLAUDE.md banner edited", post("Edit", file_path=os.path.join(rfp, "CLAUDE.md"), old_string="a", new_string=banner),
             ("RFP status banner edited", "rfp-825025-pig-spill")),
            ("RFP CLAUDE.md edit with no banner is silent", post("Edit", file_path=os.path.join(sen, "utah-sentinel", "rfp-2", "CLAUDE.md"), old_string="a", new_string="b"), None),
            ("a site-level CLAUDE.md with a banner line is silent", post("Edit", file_path=os.path.join(sen, "utah-sentinel", "CLAUDE.md"), old_string="a", new_string=banner), None),
            ("a file nowhere near a desk is silent", post("Write", file_path=os.path.join(root, "elsewhere", "PO 1.md"), content="x"), None),
            ("a Bash call nowhere near a desk is silent", post("Bash", command="ls -la"), None),
            ("a tool that is not a write is silent", post("Read", file_path=os.path.join(deals["11.3.26"], "RFQ.md")), None),
        ]

        # ---- one scripted session through each interpreter -------------------------------------
        def session(cmd, env):
            return [run(cmd, p, env) for _, p, _ in steps]

        py_env = fresh_env(root)
        py_res = session(PY_CMD, py_env)
        ps_res = None
        if PS_CMD:
            ps_res = session(PS_CMD, fresh_env(root))
        for i, (label, payload, expect) in enumerate(steps):
            rc, out, err = py_res[i]
            got = ctx(out)
            if expect is None:
                ok = got is None
            else:
                want = REMINDER.format(event=expect[0], folder=expect[1])
                ok = isinstance(got, str) and got == want
            check(rc == 0 and err == "" and ok, "python: " + label, "%r %r %r" % (rc, err, got))
            check(not out.strip() or "decision" not in json.loads(out), "reminds only: " + label)
            if ps_res is not None:
                prc, pout, perr = ps_res[i]
                same = prc == 0 and perr == "" and ctx(pout) == got
                check(same, "powershell agrees: " + label, "%r %r %r" % (prc, perr, ctx(pout)))
        if not PS_CMD:
            skipped_ps = True
            msg = "PowerShell parity SKIPPED: neither pwsh nor powershell is on PATH"
            if REQUIRE_PS:
                check(False, msg)
            else:
                print("SKIP  " + msg)

        # ---- the reminder quotes no file content -------------------------------------------------
        secret = "SECRET-PRICE-$99.99-ACCT-888123456"
        rc, out, err = run(PY_CMD, post("Edit", sid="s-priv", file_path=os.path.join(joe, "Priv Deal 11.12.26", "quote-log.md"),
                                        old_string="a", new_string=row + " " + secret), fresh_env(root))
        check(rc == 0 and err == "" and "SECRET" not in out and "99.99" not in out and "888123456" not in out and "SQ-900001" not in out,
              "the reminder quotes none of the written content", out)

        # ---- the Stop backstop -------------------------------------------------------------------
        def stop_session(name, extra_env, script, cmd):
            env = fresh_env(root, extra_env)
            outs = []
            for kind, payload in script:
                outs.append((kind, run(cmd, payload, env)))
            return outs

        def stop_cases(cmd, label):
            key_change = post("Write", sid="st", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), content="x")
            no_ledger = run(cmd, stop("st"), fresh_env(root))
            check(no_ledger[0] == 0 and not no_ledger[1].strip() and no_ledger[2] == "", label + " Stop with no key change is silent", no_ledger)

            o = stop_session("msg", None, [("k", key_change), ("s1", stop("st")), ("s2", stop("st"))], cmd)
            j = ctx(o[1][1][1])
            check(o[1][1][0] == 0 and isinstance(j, dict) and set(j) == {"systemMessage"} and j["systemMessage"].startswith(STOP_MESSAGE_START),
                  label + " Stop defaults to a message only (no decision, no resume)", o[1][1])
            check(not o[2][1][1].strip(), label + " Stop speaks once per session", o[2][1])

            o = stop_session("cap", None, [("k", key_change),
                                           ("c", post("Bash", sid="st", command='"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/desk-remember/scripts/desk_memory.py" add --at "x" --level 1')),
                                           ("s", stop("st"))], cmd)
            check(not o[2][1][1].strip(), label + " a desk_memory add after the key change clears it: Stop is silent", o[2][1])

            o = stop_session("none", None, [("k", key_change),
                                            ("c", post("Bash", sid="st", command='"${CLAUDE_PLUGIN_ROOT}/scripts/bbs-fill" "${CLAUDE_PLUGIN_ROOT}/skills/desk-remember/scripts/desk_memory.py" close --none --at "x" --author "A B"')),
                                            ("s", stop("st"))], cmd)
            check(not o[2][1][1].strip(), label + " close --none clears it: Stop is silent", o[2][1])

            o = stop_session("late", None, [("c", post("Bash", sid="st", command="desk_memory.py add --at x")), ("k", key_change), ("s", stop("st"))], cmd)
            check(bool(o[2][1][1].strip()), label + " a capture BEFORE the key change does not clear it", o[2][1])

            o = stop_session("lessons", None, [("k", key_change),
                                               ("c", post("Write", sid="st", file_path=os.path.join(root, "Customers", "State of CA Agencies", "learning", "lessons.md"), content="- x")),
                                               ("s", stop("st"))], cmd)
            check(not o[2][1][1].strip(), label + " a write to learning/lessons.md clears it", o[2][1])

            o = stop_session("cont", {"BBS_DESK_LEARN_STOP": "continue"}, [("k", key_change), ("s1", stop("st", active=True)), ("s2", stop("st")), ("s3", stop("st"))], cmd)
            check(not o[1][1][1].strip(), label + " continue mode never resumes a turn that is already a continuation (stop_hook_active)", o[1][1])
            j = ctx(o[2][1][1])
            check(isinstance(j, dict) and j.get("decision") == "block" and j.get("reason", "").startswith(STOP_REASON_START),
                  label + " continue mode resumes the turn with the fixed reason", o[2][1])
            check(not o[3][1][1].strip(), label + " continue mode resumes at most once", o[3][1])

            o = stop_session("other", {"BBS_DESK_LEARN_STOP": "banana"}, [("k", key_change), ("s", stop("st"))], cmd)
            j = ctx(o[1][1][1])
            check(isinstance(j, dict) and set(j) == {"systemMessage"}, label + " any value but continue stays message-only", o[1][1])

        stop_cases(PY_CMD, "python:")
        if PS_CMD:
            stop_cases(PS_CMD, "powershell:")

        # ---- fails open ---------------------------------------------------------------------------
        for raw in (b"", b"not json", b"[1,2]", b'{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":"x"}'):
            for cmd in [PY_CMD] + ([PS_CMD] if PS_CMD else []):
                p = subprocess.run(cmd, input=raw, capture_output=True, timeout=120, env=fresh_env(root))
                check(p.returncode == 0 and not p.stdout.strip() and not p.stderr.strip(),
                      "silent on unreadable input %r (%s)" % (raw[:20], "ps" if cmd is PS_CMD else "py"))

        # ---- source facts -------------------------------------------------------------------------
        py_src = open(os.path.join(HOOKS, "desk-learn.py"), encoding="utf-8").read()
        ps_src = open(os.path.join(HOOKS, "desk-learn.ps1"), encoding="utf-8").read()
        check(all(ord(c) < 128 for c in ps_src), "desk-learn.ps1 is ASCII (Windows PowerShell 5.1 reads it as ANSI)")
        check("sys.exit(1)" not in py_src and "exit 2" not in ps_src and "sys.exit(2)" not in py_src and "stderr" not in py_src.replace("never a write to a customer folder, never stderr", ""),
              "desk-learn never exits non-zero and never writes stderr")
        for ev in ("RFQ stage moved to sent", "RFQ stage moved to outcome", "quote-log row added or Outcome set", "new file in FILLED/",
                   "PO, award or NOA file written", "Sentinel quote-log appended", "RFP status banner edited"):
            check(ev in py_src and ev in ps_src, "both halves carry the event wording: " + ev)
        for name, a, b in (("STAGE_RE", r"^\*\*Stage:\*\*[ \t]*(.+?)[ \t]*\r?$", "STAGE_RE"),):
            check(("'(?m)" + a + "'") in ps_src and a in py_src, "both halves carry the same " + name)
        check('BBS_DESK_LEARN_STOP' in py_src and 'BBS_DESK_LEARN_STOP' in ps_src, "both halves read the one Stop switch")
        check(re.search(r'mode == "continue"', py_src) and "-eq 'continue'" in ps_src, "the only value that resumes a turn is 'continue', in both halves")

        # ---- hooks.json ----------------------------------------------------------------------------
        with open(os.path.join(HOOKS, "hooks.json"), encoding="utf-8") as fh:
            hj = json.load(fh)
        post_entries = [g for g in hj["hooks"]["PostToolUse"] if any("desk-learn.sh" in h["command"] for h in g["hooks"])]
        check(len(post_entries) == 1 and set(post_entries[0]["matcher"].split("|")) == {"Bash", "Write", "Edit", "MultiEdit"},
              "hooks.json: one PostToolUse entry runs desk-learn.sh on Bash|Write|Edit|MultiEdit")
        stop_entries = [g for g in hj["hooks"].get("Stop", []) if any("desk-learn.sh" in h["command"] for h in g["hooks"])]
        check(len(stop_entries) == 1, "hooks.json: one Stop entry runs desk-learn.sh")
        check("BBS_DESK_LEARN_STOP" in hj["description"] and "message-only" in hj["description"] and "desk_learn_parity.py" in hj["description"],
              "hooks.json description names the Stop switch, its default and the parity test")
        check(not any("desk-learn" in h["command"] and "exit 2" in h["command"] for g in hj["hooks"]["PostToolUse"] for h in g["hooks"]),
              "no desk-learn entry can exit 2")

        # ---- the shell entry starts no interpreter for input nowhere near a desk ------------------
        sh = shutil.which("sh")
        if not sh:
            print("SKIP  desk-learn.sh: no sh")
        else:
            stub = os.path.join(root, "stubbin")
            os.makedirs(stub)
            log = os.path.join(root, "stub.log")
            for name in ("pwsh", "powershell", "python3"):
                with open(os.path.join(stub, name), "w") as fh:
                    fh.write('#!/bin/sh\nprintf "%%s " "%s" >> "%s"\ncat >> "%s"\nprintf "\\n" >> "%s"\n' % (name, log, log, log))
                os.chmod(os.path.join(stub, name), 0o755)
            base_path = os.pathsep.join(p for p in ("/usr/bin", "/bin") if os.path.isdir(p))

            def entry(payload, env_extra=None):
                env = fresh_env(root, env_extra)
                env["PATH"] = stub + os.pathsep + base_path
                if os.path.exists(log):
                    os.remove(log)
                p = subprocess.run([sh, os.path.join(HOOKS, "desk-learn.sh")], input=json.dumps(payload).encode("utf-8"),
                                   capture_output=True, timeout=60, env=env)
                ran = os.path.exists(log) and bool(open(log).read().strip())
                return p.returncode, ran, env, (open(log).read() if ran else "")

            rc, ran, _, _ = entry(post("Write", file_path="/home/u/notes.md", content="hello"))
            check(rc == 0 and not ran, "desk-learn.sh: a write nowhere near a desk starts no interpreter")
            rc, ran, _, _ = entry(post("Bash", command="ls -la"))
            check(rc == 0 and not ran, "desk-learn.sh: an ordinary Bash call starts no interpreter")
            rc, ran, _, seen = entry(post("Write", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), content="x"))
            check(rc == 0 and ran and "pwsh" in seen and '"tool_name"' in seen,
                  "desk-learn.sh: a desk write reaches the first interpreter with stdin intact", seen)
            rc, ran, _, _ = entry(post("Bash", command="python3 rfq_record.py set-stage x sent"))
            check(rc == 0 and ran, "desk-learn.sh: an rfq_record call reaches the interpreter")
            rc, ran, _, _ = entry(post("Write", file_path=os.path.join(root, "Customers", "Bechtel", "SENTINEL", "learning", "quote-log.md"), content="x"))
            check(rc == 0 and ran, "desk-learn.sh: Sentinel paths reach the interpreter, any case")
            rc, ran, _, _ = entry(stop("never-reminded"))
            check(rc == 0 and not ran, "desk-learn.sh: Stop with no ledger starts no interpreter")
            # With a ledger: the key is the session id with every run of other characters as one "-".
            env = fresh_env(root)
            env["PATH"] = stub + os.pathsep + base_path
            os.makedirs(os.path.join(env["TMPDIR"], "bbs-desk-learn"))
            open(os.path.join(env["TMPDIR"], "bbs-desk-learn", "ab-12-x.ledger"), "w").write("K\tx\ty\n")
            if os.path.exists(log):
                os.remove(log)
            p = subprocess.run([sh, os.path.join(HOOKS, "desk-learn.sh")], input=json.dumps(stop("ab:12//x")).encode("utf-8"),
                               capture_output=True, timeout=60, env=env)
            check(p.returncode == 0 and os.path.exists(log), "desk-learn.sh: Stop with this session's ledger reaches the interpreter (same session key as the hook)")
            # And the real hook agrees on that key: a reminder under that session id writes <key>.ledger.
            env2 = fresh_env(root)
            run(PY_CMD, post("Write", sid="ab:12//x", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), content="x"), env2)
            check(os.path.exists(os.path.join(env2["TMPDIR"], "bbs-desk-learn", "ab-12-x.ledger")), "the Python hook names the ledger the shell looks for")
            if PS_CMD:
                env3 = fresh_env(root)
                run(PS_CMD, post("Write", sid="ab:12//x", file_path=os.path.join(deals["11.4.26"], "RFQ.md"), content="x"), env3)
                check(os.path.exists(os.path.join(env3["TMPDIR"], "bbs-desk-learn", "ab-12-x.ledger")), "the PowerShell hook names the same ledger")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("\nall pass" if fails == 0 else "\n%d FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
