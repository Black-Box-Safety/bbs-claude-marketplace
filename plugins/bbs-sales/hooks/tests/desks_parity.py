#!/usr/bin/env python3
"""scripts/desks.py and scripts/Desks.ps1 must agree on every registry and every path.

Builds one case list (paths to find, registries to load, the registry-path lookup), then:

  * runs it through scripts/desks.py (always) and checks each answer against an expectation
    written here independently of the loader;
  * runs the same list through scripts/Desks.ps1 (under pwsh or powershell, whichever is on PATH)
    and checks the two interpreters agree.

Find cases compare {desk_id, root, start, end} (or null; or a list for find_all). Load cases
compare only "Error is null vs non-null" and the desk ids returned, never the error text.
Python offsets are code points; Desks.ps1 returns native UTF-16 indices (for .Substring), and this harness converts them
to code points, using the path itself, before comparing.

When neither pwsh nor powershell is on PATH the PowerShell half is SKIPPED, not failed,
unless BBS_REQUIRE_PS=1 is set (CI sets it, so CI proves parity rather than skipping it).

Usage:  python3 plugins/bbs-sales/hooks/tests/desks_parity.py
Exit 0 = all pass. Stdlib only. Writes only inside a temp dir it removes.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(PLUGIN, "scripts")
DESKS_PS = os.path.join(SCRIPTS, "Desks.ps1")
DEFAULT_REG = os.path.join(PLUGIN, "references", "desks.json")
TWO_REG = os.path.join(SCRIPTS, "tests", "fixtures", "desks-two.json")
PS = shutil.which("pwsh") or shutil.which("powershell")
REQUIRE_PS = os.environ.get("BBS_REQUIRE_PS") == "1"
PY = sys.executable
SENTINEL = os.path.join("sentinel-dir", "from-env.json")

CA = "ca-state"
ROOT = "All RFQ's by Agency"

BASE_DESK = {
    "desk_id": "x", "kind": "rfq", "roots": ["R"], "deal_depth": [2, 3], "deal_name_rule": "date",
    "rep_min_depth": 2, "guard": {"no_rename": True, "near_duplicate": True, "filled_immutable": True},
    "record_profile": "ca-v2",
}


def desk(did, roots, kind="rfq"):
    d = copy.deepcopy(BASE_DESK)
    d.update(desk_id=did, roots=roots, kind=kind)
    return d


def reg(*desks):
    return {"schema_version": 1, "desks": list(desks)}


def mutated(fn):
    d = copy.deepcopy(BASE_DESK)
    fn(d)
    return reg(d)


def rec(desk_id, root, start, end):
    return {"desk_id": desk_id, "root": root, "start": start, "end": end}


# Registry files written into the temp dir: name -> (bytes or dict, expected (err_null, ids)).
BAD = (False, [CA])
REGISTRIES = {
    "overlap": (reg(desk("ov", ["Bechtel", "Bechtel/sentinel"]), desk("ordr", ["BBS CSU UC"], kind="order")), None),
    "ties": (reg(desk("tie-a", ["Alpha Root"]), desk("tie-b", ["alpha root"]), desk("bs", ["Back\\Slash"])), None),
    "ok_empty_profile": (mutated(lambda d: d.update(record_profile="")), (True, ["x"])),
    "ok_depth_equal": (mutated(lambda d: d.update(deal_depth=[2, 2])), (True, ["x"])),
    "ok_extra_toplevel": (dict(reg(copy.deepcopy(BASE_DESK)), note="extra"), (True, ["x"])),
    "bad_schema_version": (dict(reg(copy.deepcopy(BASE_DESK)), schema_version=2), BAD),
    "bad_empty_desks": (reg(), BAD),
    "bad_extra_key": (mutated(lambda d: d.update(extra=1)), BAD),
    "bad_missing_key": (mutated(lambda d: d.pop("record_profile")), BAD),
    "bad_dup_id": (reg(desk("x", ["A"]), desk("x", ["B"])), BAD),
    "bad_desk_id": (mutated(lambda d: d.update(desk_id="Bad_ID")), BAD),
    "bad_kind": (mutated(lambda d: d.update(kind="quote")), BAD),
    "bad_roots_empty": (mutated(lambda d: d.update(roots=[])), BAD),
    "bad_roots_blank": (mutated(lambda d: d.update(roots=[""])), BAD),
    "bad_depth_bool": (mutated(lambda d: d.update(deal_depth=[True, 3])), BAD),
    "bad_depth_float": (mutated(lambda d: d.update(deal_depth=[2.0, 3])), BAD),
    "bad_depth_reversed": (mutated(lambda d: d.update(deal_depth=[3, 2])), BAD),
    "bad_depth_zero": (mutated(lambda d: d.update(deal_depth=[0, 2])), BAD),
    "bad_rule": (mutated(lambda d: d.update(deal_name_rule="alpha")), BAD),
    "bad_rep_min_bool": (mutated(lambda d: d.update(rep_min_depth=True)), BAD),
    "bad_rep_min_zero": (mutated(lambda d: d.update(rep_min_depth=0)), BAD),
    "bad_guard_missing": (mutated(lambda d: d["guard"].pop("no_rename")), BAD),
    "bad_guard_extra": (mutated(lambda d: d["guard"].update(more=True)), BAD),
    "bad_guard_nonbool": (mutated(lambda d: d["guard"].update(no_rename=1)), BAD),
    "bad_profile_int": (mutated(lambda d: d.update(record_profile=5)), BAD),
    "bad_toplevel_array": ([copy.deepcopy(BASE_DESK)], BAD),
}
RAW_REGISTRIES = {   # name -> bytes
    "bad_invalid_json": b'{"schema_version": 1, "desks": [',
    "bad_empty_file": b"",
    "bad_bom": b"\xef\xbb\xbf" + json.dumps(reg(copy.deepcopy(BASE_DESK))).encode("utf-8"),
    "bad_utf8": b'{"schema_version": 1, "n": "\xff\xfe", "desks": ' + json.dumps([BASE_DESK]).encode("utf-8") + b"}",
}


def build_cases(regs):
    """regs: name -> path. Returns [(id, op, reg_path_or_None, path, expected)]."""
    cases = []

    def find(cid, rname, path, exp):
        cases.append(("find-" + cid, "find", regs[rname], path, exp))

    def find_all(cid, rname, path, exp):
        cases.append(("all-" + cid, "all", regs[rname], path, exp))

    find("case", "default", "/x/all rfq's BY AGENCY/CDCR/Buyer/a.md", rec(CA, ROOT, 3, 22))
    find("backslash", "default", "C:\\Desk\\All RFQ's by Agency\\A\\B\\x.md", rec(CA, ROOT, 8, 27))
    find("outside", "default", "/x/Customers/Bechtel/sentinel/a.md", None)
    p = "/x/Old All RFQ's by Agency backup/All RFQ's by Agency/a.md"
    find("leftmost", "default", p, rec(CA, ROOT, 7, 26))
    find_all("two", "default", p, [rec(CA, ROOT, 7, 26), rec(CA, ROOT, 34, 53)])
    n = "C:/Desk/All RFQ's by Agency/Peñasquitos/Juan Núñez/a.md"
    find("accents", "default", n, rec(CA, ROOT, 8, 27))
    find_all("accents", "default", n, [rec(CA, ROOT, 8, 27)])
    find("kelvin-before", "default", "/x/\u212a/All RFQ's by Agency/a.md", rec(CA, ROOT, 5, 24))
    find("astral-before", "default", "/x/\U0001F600/All RFQ's by Agency/a.md", rec(CA, ROOT, 5, 24))
    find("folder-emoji", "default", "/x/\U0001F4C1/All RFQ's by Agency/a.md", rec(CA, ROOT, 5, 24))
    find_all("folder-emoji", "default", "/x/\U0001F4C1/a/\U0001F4C1/All RFQ's by Agency/a.md", [rec(CA, ROOT, 9, 28)])
    find_all("astral-before", "default", "/x/\U0001F600/All RFQ's by Agency/a.md", [rec(CA, ROOT, 5, 24)])
    find("empty", "default", "", None)
    find_all("empty", "default", "", [])
    find("kelvin-in-root", "two", "/x/Synthetic Des\u212a Root/a", None)
    find("two-lower", "two", "/x/synthetic desk root/a", rec("test-desk", "Synthetic Desk Root", 3, 22))
    both = "/x/Synthetic Desk Root/All RFQ's by Agency/a"
    find("two-both", "two", both, rec("test-desk", "Synthetic Desk Root", 3, 22))
    find_all("two-both", "two", both, [rec("test-desk", "Synthetic Desk Root", 3, 22), rec(CA, ROOT, 23, 42)])
    find("overlap", "overlap", "/C/Bechtel/sentinel/x", rec("ov", "Bechtel/sentinel", 3, 19))
    find_all("overlap", "overlap", "/C/Bechtel/sentinel/x/Bechtel/y",
             [rec("ov", "Bechtel/sentinel", 3, 19), rec("ov", "Bechtel", 22, 29)])
    find("order-desk", "overlap", "/x/BBS CSU UC/a", None)
    find_all("order-desk", "overlap", "/x/BBS CSU UC/a", [])
    find("tie", "ties", "/x/Alpha Root/a", rec("tie-a", "Alpha Root", 3, 13))
    find_all("tie", "ties", "/x/Alpha Root/a", [rec("tie-a", "Alpha Root", 3, 13)])
    find("tie-backslash-path", "ties", "C:\\x\\ALPHA ROOT\\a", rec("tie-a", "Alpha Root", 5, 15))
    find("root-with-backslash", "ties", "/x/back/slash/y", rec("bs", "Back\\Slash", 3, 13))

    for name, (_, exp) in REGISTRIES.items():
        if exp is not None:
            cases.append(("load-" + name, "load", regs[name], None, exp))
    for name in RAW_REGISTRIES:
        cases.append(("load-" + name, "load", regs[name], None, BAD))
    cases.append(("load-default", "load", regs["default"], None, (True, [CA])))
    cases.append(("load-two", "load", regs["two"], None, (True, [CA, "test-desk"])))
    cases.append(("load-missing", "load", regs["missing"], None, BAD))
    cases.append(("regpath-env", "regpath", None, None, SENTINEL))
    cases.append(("regpath-default", "regpath_default", None, None, DEFAULT_REG))
    return cases


PY_DRIVER = r"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
import desks
spec = json.load(open(sys.argv[2], encoding="utf-8"))
out = {}
def r(m):
    return {"desk_id": m.desk["desk_id"], "root": m.root, "start": m.start, "end": m.end}
for c in spec["cases"]:
    op = c["op"]
    if op == "find":
        ds, _ = desks.load(c["reg"])
        m = desks.find(c["path"], ds)
        v = None if m is None else r(m)
    elif op == "all":
        ds, _ = desks.load(c["reg"])
        v = [r(m) for m in desks.find_all(c["path"], ds)]
    elif op == "load":
        ds, err = desks.load(c["reg"])
        v = {"err_null": err is None, "ids": ",".join(d["desk_id"] for d in ds)}
    elif op == "regpath":
        v = desks.registry_path()
    elif op == "regpath_default":
        os.environ.pop("BBS_DESKS_FILE", None)
        v = os.path.normpath(desks.registry_path())
    out[c["id"]] = v
sys.stdout.write(json.dumps(out))
"""

PS_DRIVER = r"""
$ErrorActionPreference = 'Stop'
. $env:BBS_DESKS_PS
$utf8 = New-Object System.Text.UTF8Encoding($false)
$spec = [System.IO.File]::ReadAllText($env:BBS_SPEC, $utf8) | ConvertFrom-Json
function RecJson($m) {
  return (@{ desk_id = $m.Desk.desk_id; root = $m.Root; start = $m.Start; end = $m.End } | ConvertTo-Json -Compress)
}
foreach ($c in @($spec.cases)) {
  $op = $c.op
  if ($op -eq 'find') {
    $d = Get-BbsDesks -Path $c.reg
    $m = Find-BbsDeskRoot -Path $c.path -Desks $d.Desks
    if ($null -eq $m) { $json = 'null' } else { $json = RecJson $m }
  } elseif ($op -eq 'all') {
    $d = Get-BbsDesks -Path $c.reg
    $parts = @()
    foreach ($m in @(Find-BbsDeskRootAll -Path $c.path -Desks $d.Desks)) { $parts += (RecJson $m) }
    $json = '[' + ($parts -join ',') + ']'
  } elseif ($op -eq 'load') {
    $d = Get-BbsDesks -Path $c.reg
    $ids = @()
    foreach ($x in @($d.Desks)) { $ids += $x.desk_id }
    $json = (@{ err_null = ($null -eq $d.Error); ids = ($ids -join ',') } | ConvertTo-Json -Compress)
  } elseif ($op -eq 'regpath') {
    $json = ConvertTo-Json (Get-BbsDeskRegistryPath)
  } else {
    Remove-Item Env:BBS_DESKS_FILE -ErrorAction SilentlyContinue
    $json = ConvertTo-Json (Get-BbsDeskRegistryPath)
  }
  [Console]::Out.Write($c.id + "`t" + $json + "`n")
}
"""


def run_py(spec_path, env):
    p = subprocess.run([PY, "-c", PY_DRIVER, SCRIPTS, spec_path], capture_output=True, timeout=120, env=env)
    if p.returncode != 0:
        raise RuntimeError("python driver failed: " + p.stderr.decode("utf-8", "replace"))
    return json.loads(p.stdout.decode("utf-8"))


def run_ps(spec_path, driver_path, env):
    env = dict(env)
    env.update(BBS_SPEC=spec_path, BBS_DESKS_PS=DESKS_PS)
    p = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", driver_path],
                       capture_output=True, timeout=300, env=env)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0:
        raise RuntimeError("powershell driver failed (exit %d): %s%s" % (p.returncode, p.stderr.decode("utf-8", "replace"), out[-500:]))
    res = {}
    for line in out.replace("\r\n", "\n").split("\n"):
        if line.strip():
            cid, js = line.split("\t", 1)
            res[cid] = json.loads(js)
    return res


def cp(path, i):
    """UTF-16 index -> code-point index within path."""
    return len(path.encode("utf-16-le")[:2 * i].decode("utf-16-le"))


def ps_to_cp(op, v, path):
    if op == "find" and v is not None:
        return dict(v, start=cp(path, v["start"]), end=cp(path, v["end"]))
    if op == "all":
        return [dict(m, start=cp(path, m["start"]), end=cp(path, m["end"])) for m in v]
    return v


def norm(op, v):
    """Python-side shape of a load result for comparison with an expectation tuple."""
    if op == "load":
        return (v["err_null"], [i for i in v["ids"].split(",") if i])
    if op == "regpath_default":
        return os.path.normpath(v)
    return v


def main():
    root = tempfile.mkdtemp(prefix="bbs-desks-parity-")
    fails = 0
    try:
        regs = {"default": DEFAULT_REG, "two": TWO_REG, "missing": os.path.join(root, "no-such-file.json")}
        for name, (data, _) in REGISTRIES.items():
            regs[name] = os.path.join(root, name + ".json")
            with open(regs[name], "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        for name, raw in RAW_REGISTRIES.items():
            regs[name] = os.path.join(root, name + ".json")
            with open(regs[name], "wb") as fh:
                fh.write(raw)
        cases = build_cases(regs)
        spec_path = os.path.join(root, "spec.json")
        with open(spec_path, "w", encoding="utf-8") as fh:
            json.dump({"cases": [{"id": c[0], "op": c[1], "reg": c[2], "path": c[3]} for c in cases]}, fh)
        env = dict(os.environ)
        env["BBS_DESKS_FILE"] = SENTINEL

        py_out = run_py(spec_path, env)
        py_fail = 0
        for cid, op, _, _, exp in cases:
            got = norm(op, py_out[cid])
            if got != exp:
                py_fail += 1
                print("FAIL python %s: expected %r, got %r" % (cid, exp, got))
        fails += py_fail
        print("python half: %d cases, %d failed" % (len(cases), py_fail))

        if not PS:
            if REQUIRE_PS:
                print("FAIL powershell half: neither pwsh nor powershell on PATH and BBS_REQUIRE_PS=1")
                fails += 1
            else:
                print("powershell half SKIPPED: neither pwsh nor powershell on PATH (set BBS_REQUIRE_PS=1 to fail instead)")
        elif not os.path.isfile(DESKS_PS):
            print("FAIL powershell half: %s does not exist" % DESKS_PS)
            fails += 1
        else:
            driver_path = os.path.join(root, "driver.ps1")
            with open(driver_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(PS_DRIVER)
            try:
                ps_out = run_ps(spec_path, driver_path, env)
            except RuntimeError as e:
                print("FAIL powershell half: %s" % e)
                fails += 1
            else:
                ps_fail = 0
                for cid, op, _, cpath, _ in cases:
                    if cid in ps_out:
                        ps_out[cid] = ps_to_cp(op, ps_out[cid], cpath)
                    if cid not in ps_out:
                        ps_fail += 1
                        print("FAIL powershell %s: no output" % cid)
                    elif norm(op, ps_out[cid]) != norm(op, py_out[cid]):
                        ps_fail += 1
                        print("FAIL parity %s: python %r, powershell %r" % (cid, py_out[cid], ps_out[cid]))
                fails += ps_fail
                print("powershell half (%s): %d cases, %d differ from python" % (os.path.basename(PS), len(cases), ps_fail))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("all pass" if not fails else "%d FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
