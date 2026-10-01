#!/usr/bin/env python3
"""test_bbs_fill.py — the launcher runs vetted scripts and nothing else.

Run it:
    python3 test_bbs_fill.py

`Bash(bbs-fill *)` is allowed in managed settings, so every way of getting
bbs-fill to run something other than a vetted script is a way past auto mode.
Each test builds a fake plugin cache in a temp folder and tries one.
Needs bash. Stdlib only.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.join(os.path.dirname(HERE), "bin", "bbs-fill")
STUB = "import sys; print('RAN', sys.argv[1:])\n"


def _cache(tmp, market="bbs-claude-marketplace"):
    """<tmp>/cache/<market>/{bbs-tools/0.1.0/bin/bbs-fill, bbs-sales/abc123/skills/...}"""
    base = os.path.join(tmp, "cache", market)
    bin_dir = os.path.join(base, "bbs-tools", "0.1.0", "bin")
    os.makedirs(bin_dir)
    shutil.copy2(LAUNCHER, os.path.join(bin_dir, "bbs-fill"))
    sales = os.path.join(base, "bbs-sales", "abc123", "skills")
    for rel in ("ca-form-filler/scripts/fill_obs_packet.py",
                "ca-form-filler/scripts/test_fill_obs_packet.py",
                "naspo-quote/scripts/fill_ca_forms.py"):
        path = os.path.join(sales, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(STUB)
    return os.path.join(bin_dir, "bbs-fill"), sales


def _run(launcher, *args):
    p = subprocess.run(["bash", launcher, *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def _refused(launcher, *args):
    code, out = _run(launcher, *args)
    assert code == 64 and "REFUSED" in out and "RAN" not in out, (code, out)
    return out


def test_vetted_script_runs_and_arguments_stay_data():
    with tempfile.TemporaryDirectory() as t:
        bf, sales = _cache(t)
        script = os.path.join(sales, "ca-form-filler/scripts/fill_obs_packet.py")
        code, out = _run(bf, script, "-c", "import os", "in.pdf")
        assert code == 0 and "RAN ['-c', 'import os', 'in.pdf']" in out, (code, out)


def test_unvetted_file_in_the_same_folder_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, sales = _cache(t)
        out = _refused(bf, os.path.join(sales, "ca-form-filler/scripts/test_fill_obs_packet.py"))
        assert "not a vetted script" in out, out


def test_same_name_outside_the_marketplace_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, _sales = _cache(t)
        evil = os.path.join(t, "evil", "bbs-sales", "x", "skills", "ca-form-filler",
                            "scripts", "fill_obs_packet.py")
        os.makedirs(os.path.dirname(evil))
        with open(evil, "w") as fh:
            fh.write(STUB)
        out = _refused(bf, evil)
        assert "not inside this marketplace" in out, out


def test_another_marketplace_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, _sales = _cache(t)
        _bf2, other = _cache(t, market="someone-elses-marketplace")
        _refused(bf, os.path.join(other, "ca-form-filler/scripts/fill_obs_packet.py"))


def test_dotdot_escape_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, sales = _cache(t)
        evil = os.path.join(t, "evil.py")
        with open(evil, "w") as fh:
            fh.write(STUB)
        sneaky = os.path.join(sales, "ca-form-filler/scripts/../../../../../../evil.py")
        _refused(bf, sneaky)


def test_symlink_out_of_the_cache_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, sales = _cache(t)
        evil = os.path.join(t, "evil.py")
        with open(evil, "w") as fh:
            fh.write(STUB)
        link = os.path.join(sales, "naspo-quote/scripts/fill_ca_forms.py")
        os.remove(link)
        os.symlink(evil, link)
        _refused(bf, link)


def test_an_option_first_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, _sales = _cache(t)
        for first in ("-c", "--version", "-"):
            _refused(bf, first, "print(1)")


def test_no_arguments_is_refused():
    with tempfile.TemporaryDirectory() as t:
        bf, _sales = _cache(t)
        _refused(bf)


def test_allowed_list_names_only_scripts_that_exist_in_bbs_sales():
    sales = os.path.join(os.path.dirname(os.path.dirname(HERE)), "bbs-sales", "skills")
    with open(LAUNCHER) as fh:
        text = fh.read()
    block = text[text.index("ALLOWED=("):text.index(")", text.index("ALLOWED=("))]
    names = [l.strip().strip('"') for l in block.splitlines()[1:] if l.strip()]
    assert names, block
    for rel in names:
        assert os.path.isfile(os.path.join(sales, rel)), rel
        assert "/test_" not in rel, rel


def main():
    if not shutil.which("bash"):
        print("SKIP: bash not found")
        return
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
