#!/usr/bin/env python3
"""fill-gate.py and fill-gate.ps1 must agree on every case, and the shells must agree with the lexer.

1. Cases (fill_gate_cases.json): each builds a fake plugin root in a temp folder, with a copy of
   the real launcher, and runs the payload through the Python half (always) and the PowerShell
   half (pwsh or powershell, whichever is on PATH). Checked: the Python decision matches the
   case's expectation; stderr is empty; exit code 0; and, when PowerShell ran, both halves give
   the same decision AND the same reason string.
2. Differential against real shells: for every allowed case, and for a fixed-seed fuzz of
   strings the lexer accepts, `bash --norc --noprofile` (set -f) and `zsh -f` (noglob) must split
   the command into exactly the lexer's words. `zsh -f` skips the user's startup files: the hook
   models the default grammar, not a rep's aliases or options (spec 3.2, "Assumption").
3. hooks.json: the PreToolUse entry runs fill-gate.sh through sh; with stub interpreters on PATH,
   nothing starts for a command without "bbs-fill", and stdin reaches the interpreter intact.
4. updatedInput guard: no hook in plugins/ emits "updatedInput" (spec 3.2). This test folder is
   excluded: it names the key in order to look for it.
5. canon(): Windows drive forms compare equal (Python half; the PowerShell half is covered by V3
   on a Windows machine).

PowerShell missing -> SKIP, unless BBS_REQUIRE_PS=1 (CI). zsh or bash missing -> SKIP, unless
BBS_REQUIRE_SHELLS=1 (CI). Prints the allow table at the end.

Usage: python3 plugins/bbs-sales/hooks/tests/fill_gate_parity.py     Exit 0 = all pass. Stdlib only.
"""
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.dirname(HERE)
SALES = os.path.dirname(HOOKS)
PLUGINS = os.path.dirname(SALES)
LAUNCHER = os.path.join(SALES, "scripts", "bbs-fill")
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"
REQUIRE_SHELLS = os.environ.get("BBS_REQUIRE_SHELLS") == "1"
BASH = shutil.which("bash")
ZSH = shutil.which("zsh")

spec = importlib.util.spec_from_file_location("fill_gate", os.path.join(HOOKS, "fill-gate.py"))
fg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fg)

results = {"pass": 0, "fail": 0}
table = []


def check(ok, name, detail=""):
    if ok:
        results["pass"] += 1
    else:
        results["fail"] += 1
        print("FAIL  " + name + ("  -- " + detail if detail else ""))


def skip(name):
    print("SKIP  " + name)


ROOT_NAMES = {None: "0.16.0", "root-space": "0.16.0 with space",
              "root-nonascii": "0.16.0-caf\u00e9-\U0001D49C"}
STUB = "import sys; print('RAN', sys.argv[1:])\n"


def build(tmp, setup):
    """<tmp>/cache/m/bbs-sales/<name>/{scripts/bbs-fill, skills/...}; returns (env_root, extra placeholders)."""
    base = os.path.join(tmp, "cache", "m", "bbs-sales")
    name = ROOT_NAMES.get(setup, "0.16.0")
    real_root = os.path.join(base, name)
    os.makedirs(os.path.join(real_root, "scripts"))
    shutil.copy2(LAUNCHER, os.path.join(real_root, "scripts", "bbs-fill"))
    for rel in ("ca-form-filler/scripts/fill_obs_packet.py", "ca-form-filler/scripts/packet_profile.py",
                "ca-form-filler/scripts/test_fill_obs_packet.py"):
        p = os.path.join(real_root, "skills", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(STUB)
    root = real_root
    launcher = os.path.join(real_root, "scripts", "bbs-fill")
    extra = {}
    if setup == "other-version":
        other = os.path.join(base, "0.15.1")
        shutil.copytree(real_root, other)
        extra["R2"] = other
    elif setup == "link-skill":
        d = os.path.join(real_root, "skills", "ca-form-filler")
        os.rename(d, d + "-real")
        os.symlink(d + "-real", d)
    elif setup == "link-launcher":
        os.rename(launcher, launcher + "-real")
        os.symlink(launcher + "-real", launcher)
    elif setup == "link-scripts":
        d = os.path.join(real_root, "scripts")
        os.rename(d, d + "-real")
        os.symlink(d + "-real", d)
    elif setup == "link-root":
        root = os.path.join(base, "via-link")
        os.symlink(real_root, root)
    elif setup in ("crlf", "bad-entry-dotdot", "bad-entry-shape", "close-zwsp"):
        with open(launcher, "rb") as fh:
            data = fh.read()
        if setup == "crlf":
            data = data.replace(b"\n", b"\r\n")
        elif setup == "bad-entry-dotdot":
            data = data.replace(b'ALLOWED=(\n', b'ALLOWED=(\n  "../x/scripts/evil.py"\n', 1)
        elif setup == "close-zwsp":
            i = data.index(b"ALLOWED=(")
            j = data.index(b"\n)\n", i)
            data = data[:j] + "\n)\u200b\n".encode("utf-8") + data[j + 3:]
        else:
            data = data.replace(b'ALLOWED=(\n', b'ALLOWED=(\n  "ca-form-filler/fill.py"\n', 1)
        with open(launcher, "wb") as fh:
            fh.write(data)
    return root, extra


def fill(template, root, extra):
    sub = {"R": root, "L": root + "/scripts/bbs-fill",
           "S": root + "/skills/ca-form-filler/scripts/fill_obs_packet.py",
           "P": root + "/skills/ca-form-filler/scripts/packet_profile.py",
           "U": root + "/skills/ca-form-filler/scripts/test_fill_obs_packet.py",
           "Lcase": root.replace("bbs-sales", "BBS-SALES") + "/scripts/bbs-fill",
           "Lnfd": unicodedata.normalize("NFD", root) + "/scripts/bbs-fill"}
    sub.update(extra)
    return re.sub(r"\{(L|S|P|U|R|R2|Lcase|Lnfd)\}", lambda m: sub[m.group(1)], template)


def run(cmd, data, env):
    p = subprocess.run(cmd, input=data, capture_output=True, timeout=120, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def decision(out):
    out = out.strip()
    if not out:
        return "none", ""
    try:
        h = json.loads(out)["hookSpecificOutput"]
        return h["permissionDecision"], h.get("permissionDecisionReason", "")
    except Exception:
        return "garbage:" + out[:80], ""


def run_cases():
    with open(os.path.join(HERE, "fill_gate_cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    if not PS:
        (check(False, "PowerShell half", "BBS_REQUIRE_PS=1 and no pwsh/powershell on PATH")
         if REQUIRE_PS else skip("PowerShell half of every case (no pwsh/powershell)"))
    allowed_cmds = []
    for c in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root, extra = build(tmp, c.get("setup"))
            cmd = fill(c["cmd"], root, extra)
            payload = {"tool_name": c.get("tool", "Bash"), "tool_input": dict({"command": cmd}, **c.get("input", {}))}
            if "dup_ti_as" in c:
                payload[c["dup_ti_as"]] = dict(payload["tool_input"])
            data = (fill(c["raw"], root, extra) if "raw" in c else json.dumps(payload)).encode("utf-8", "surrogatepass")
            env = dict(os.environ)
            env.pop("CLAUDE_PLUGIN_ROOT", None)
            er = c.get("env_root", "{R}")
            if er is not None:
                env["CLAUDE_PLUGIN_ROOT"] = fill(er, root, extra)
            code, out, err = run([sys.executable, os.path.join(HOOKS, "fill-gate.py")], data, env)
            d, reason = decision(out)
            check(code == 0 and not err, c["id"] + " (py) exit 0, no stderr", repr((code, err[:200])))
            check(d == c["expect"], c["id"] + " (py) " + c["why"], "got " + d)
            if d == "allow":
                check(reason == "bbs-fill: vetted script " + ("ca-form-filler/scripts/packet_profile.py" if "{P}" in c["cmd"] else "ca-form-filler/scripts/fill_obs_packet.py"),
                      c["id"] + " (py) reason", reason)
                allowed_cmds.append((c["id"], cmd))
            table.append((c["id"], d, reason or "-"))
            if PS:
                pcode, pout, perr = run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                         "-File", os.path.join(HOOKS, "fill-gate.ps1")], data, env)
                pd, preason = decision(pout)
                check(pcode == 0 and not perr.strip(), c["id"] + " (ps) exit 0, no stderr", repr((pcode, perr[:300])))
                why = ""
                if (pd, preason) != (d, reason):
                    denv = dict(env, BBS_FILL_GATE_DEBUG="1")
                    why = run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                               "-File", os.path.join(HOOKS, "fill-gate.ps1")], data, denv)[2].strip()
                check((pd, preason) == (d, reason), c["id"] + " parity", "py=%r ps=%r %s" % ((d, reason), (pd, preason), why))
    return allowed_cmds


def shell_words(shell, cmd):
    if shell == "bash":
        argv = [BASH, "--norc", "--noprofile", "-c", "set -f; printf '%s\\0' " + cmd]
    else:
        argv = [ZSH, "-f", "-c", "setopt noglob; printf '%s\\0' " + cmd]
    p = subprocess.run(argv, capture_output=True, timeout=30)
    if p.returncode != 0:
        return None
    parts = p.stdout.decode("utf-8", "surrogateescape").split("\0")
    return parts[:-1]


def run_differential(allowed_cmds):
    shells = [s for s, path in (("bash", BASH), ("zsh", ZSH)) if path]
    for s, path in (("bash", BASH), ("zsh", ZSH)):
        if not path:
            (check(False, s + " differential", "BBS_REQUIRE_SHELLS=1 and no " + s)
             if REQUIRE_SHELLS else skip(s + " differential (not installed)"))
    for cid, cmd in allowed_cmds:
        want = fg.lex(cmd)
        for s in shells:
            got = shell_words(s, cmd)
            check(got == want, "differential %s: %s" % (s, cid), "shell=%r lexer=%r" % (got, want))
    # Fixed-seed fuzz over strings the lexer accepts.
    rng = random.Random(20261111)
    alphabet = list("ab/._-=:,+@% ") + ["'", '"', "\\", "$", ";", "&", "|", "*", "~", "#", "!", "\n", "\u00e9",
                                        "\U0001D49C", "e\u0301", "=", "  "]
    accepted = 0
    for _ in range(3000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 14)))
        words = fg.lex(s)
        if words is None:
            continue
        accepted += 1
        for sh in shells:
            got = shell_words(sh, s)
            check(got == words, "fuzz %s: %r" % (sh, s), "shell=%r lexer=%r" % (got, words))
    check(accepted >= 100, "fuzz accepted enough strings to mean something", str(accepted))
    print("      fuzz: %d accepted strings checked against %s" % (accepted, ", ".join(shells) or "no shell"))


def run_entry():
    with open(os.path.join(HOOKS, "hooks.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    cmds = [(g, hk["command"]) for g in data["hooks"]["PreToolUse"] for hk in g.get("hooks", [])]
    ours = [(g, c) for g, c in cmds if "fill-gate.sh" in c]
    check(len(ours) == 1, "PreToolUse: exactly one entry runs fill-gate.sh", repr(cmds))
    if not ours:
        return
    g, cmd = ours[0]
    check(g.get("matcher") == "Bash", "fill-gate matcher is exactly Bash", g.get("matcher", ""))
    sh = shutil.which("sh")
    if not sh:
        skip("hooks.json entry: no sh")
        return
    with tempfile.TemporaryDirectory() as tmp:
        stub = os.path.join(tmp, "stubbin")
        os.makedirs(stub)
        log = os.path.join(tmp, "stub.log")
        for name in ("pwsh", "powershell", "python3"):
            p = os.path.join(stub, name)
            with open(p, "w") as fh:
                fh.write('#!/bin/sh\n{ printf "%%s|" "%s"; cat; printf "\\n"; } >> "%s"\n' % (name, log))
            os.chmod(p, 0o755)
        env = {"PATH": stub + os.pathsep + "/usr/bin:/bin", "CLAUDE_PLUGIN_ROOT": SALES}
        line = cmd.replace("${CLAUDE_PLUGIN_ROOT}", SALES)
        quiet = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        subprocess.run([sh, "-c", line], input=quiet.encode(), env=env, timeout=30)
        check(not os.path.exists(log), "no interpreter starts for a command without bbs-fill")
        loud = json.dumps({"tool_name": "Bash", "tool_input": {"command": "\"/x/scripts/bbs-fill\" \"y\" 'a b'"}})
        subprocess.run([sh, "-c", line], input=loud.encode(), env=env, timeout=30)
        got = open(log).read() if os.path.exists(log) else ""
        check(got == "pwsh|" + loud + "\n", "a bbs-fill command reaches the first interpreter, stdin intact", repr(got))


def run_updated_input_guard():
    hits = []
    for dirpath, dirs, files in os.walk(PLUGINS):
        if os.path.abspath(dirpath).startswith(HERE):
            continue
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for f in files:
            if not f.endswith((".py", ".ps1", ".sh", ".js", ".json", ".ts")):
                continue
            fp = os.path.join(dirpath, f)
            try:
                text = open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if re.search(r"""["']?updatedInput["']?\s*[:=]""", text):
                hits.append(os.path.relpath(fp, PLUGINS))
    check(not hits, "no hook in plugins/ emits updatedInput (spec 3.2 assumption)", repr(hits))


def run_canon():
    check(fg.canon("D:\\Quotes\\x") == fg.canon("d:/Quotes/x") == "/d/Quotes/x", "canon: drive forms")
    check(fg.canon("/d/Quotes/x/") == "/d/Quotes/x", "canon: Git Bash form, trailing /")
    check(fg.canon("/a//b") == "/a/b", "canon: duplicate /")
    check(fg.canon("/a/./b") is None and fg.canon("/a/../b") is None, "canon: . and .. refused")
    check(fg.canon("/A/b") != fg.canon("/a/b"), "canon: no case folding beyond the drive")


def main():
    allowed = run_cases()
    run_differential(allowed)
    run_entry()
    run_updated_input_guard()
    run_canon()
    print("\nWhat fill-gate allows (case, decision, reason):")
    for cid, d, reason in table:
        if d == "allow":
            print("  %-22s %-6s %s" % (cid, d, reason))
    print("  (%d other cases: no decision)" % sum(1 for _, d, _ in table if d != "allow"))
    print("\n%d PASS, %d FAIL" % (results["pass"], results["fail"]))
    sys.exit(1 if results["fail"] else 0)


if __name__ == "__main__":
    main()
