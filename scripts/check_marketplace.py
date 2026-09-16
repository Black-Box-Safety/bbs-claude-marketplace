#!/usr/bin/env python3
"""check_marketplace.py — structural invariants for the BBS marketplace.

Written for whoever maintains this repo, human or agent. It checks the things
that fail *silently*: a skill that never loads, a description truncated through
its own guardrail, a cross-reference to a skill that no longer exists, a path
that only resolves on one person's machine, a model ID that went stale.

None of these throw an error at runtime. They just quietly produce a wrong
answer on a bid.

Usage:
    python3 scripts/check_marketplace.py [--json]

Exit 0 = no FAIL. Exit 1 = at least one FAIL. WARN never changes the exit code.

Deliberately stdlib + PyYAML only, so it runs anywhere the repo is cloned.
Model IDs are read from the forge's references/models.json rather than being
copied here — a checker carrying its own copy of a fact is a second source of
truth waiting to drift.
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
MODELS_JSON = os.path.join(PLUGINS, "bbs-foundations", "skills", "bbs-claude-md-forge",
                           "references", "models.json")
FORM_RULES = os.path.join(PLUGINS, "bbs-sales", "references", "ca-form-rules.md")
VENDOR_PROFILE = os.path.join(PLUGINS, "bbs-sales", "references", "vendor_profile.json")

DESC_LIMIT = 1024

# Paths that resolve on one machine or only inside a hosted Claude session.
# ${CLAUDE_PLUGIN_ROOT} and $SKILL_DIR are the portable forms.
NONPORTABLE = [
    (re.compile(r"/mnt/skills/"), "sandbox path; exists only inside a Claude session"),
    (re.compile(r"/Users/[A-Za-z0-9._-]+/"), "absolute path to one person's home directory"),
    (re.compile(r"[Cc]:\\\\?Users\\\\?"), "absolute Windows path to one person's profile"),
    (re.compile(r"~/\.bbs/vendor_profile\.json"), "per-machine copy of the vendor profile; "
     "read ${CLAUDE_PLUGIN_ROOT}/references/vendor_profile.json instead"),
]

# Documentation that records history rather than instructing a skill.
ARCHIVE_DIRS = ("docs/superpowers/", "docs/assessments/", "docs/evals/results-")

# Session and cutover records. Their job is to describe defects — naming a bad
# path or a retired skill is the content, not a bug. Exempted from the scans
# that look for those, consistently, rather than by piling special-case words
# into the counter-example regex.
NARRATIVE = ("HANDOFF.md", "docs/SESSION-HANDOFF")


def is_narrative(path):
    r = rel(path)
    return r == "HANDOFF.md" or r.startswith("docs/SESSION-HANDOFF")

# A line that names a bad value in order to warn about it is correct content, not
# a defect. Without this the checker flags its own fixes and gets ignored, which
# is worse than having no checker.
#
# Bare "not" used to be in this list and it defeated every scan that calls here:
# "The rep does not need to attach the worksheet" two lines above a stale model
# ID silently exempted the ID. An ordinary negation is not a warning about the
# value beside it. "do not" / "don't" now have to be negating a verb of *use*
# ("do not write", "don't copy"), which is what a real counter-example says.
COUNTER_EXAMPLE = re.compile(
    r"\b(never|no longer|stale|superseded|retired|deprecated|counter-example|"
    r"earlier revisions?|used to|rather than|instead of|which is how|avoid|became|"
    r"flag it|wrong|replaced?|exists only|exists to prevent|prevent|"
    # Vocabulary this repo's own cutover records use to name a dead thing.
    r"merged (?:away|into)|orphans?|contradictions?|contradictory|"
    r"(?:do not|don't|does not|doesn't|cannot|can't)\s+"
    r"(?:use|write|call|follow|ship|copy|cite|reference|point|route|read|run|"
    r"substitute|search|check|guess|apply|resolve|exist|works?)"
    r")\b", re.I)

CONTEXT_LINES = 2
# How far the qualifying phrase may sit from the value it is warning about,
# measured in whitespace-collapsed characters. The ±2-line window on its own
# was too generous: any qualifying word anywhere in a 5-line neighbourhood
# exempted the match. The warning has to be near the thing it warns about.
PROXIMITY = 200


def _collapse(s):
    """Whitespace-collapsed copy of s, plus orig index -> collapsed index."""
    out = []
    pos = [0] * (len(s) + 1)
    prev_space = False
    for i, ch in enumerate(s):
        pos[i] = len(out)
        if ch.isspace():
            if not prev_space:
                out.append(" ")
            prev_space = True
        else:
            out.append(ch)
            prev_space = False
    pos[len(s)] = len(out)
    return "".join(out), pos


def is_counter_example(text, pos):
    """True if the match sits in prose that is warning about the value.

    Looks at a few lines either side with whitespace collapsed, because the
    qualifying phrase routinely wraps ("Earlier revisions of this skill called\n
    a wrapper under /mnt/skills/...") and a line-at-a-time check misses it.
    The phrase must also land within PROXIMITY characters of the match, so a
    qualifier belonging to an unrelated sentence elsewhere in the window does
    not exempt it.
    """
    lines = text.splitlines(keepends=True)
    idx = text[:pos].count("\n")
    lo = max(0, idx - CONTEXT_LINES)
    hi = min(len(lines), idx + CONTEXT_LINES + 1)
    start = sum(len(ln) for ln in lines[:lo])
    window = text[start:start + sum(len(ln) for ln in lines[lo:hi])]
    collapsed, cmap = _collapse(window)
    here = cmap[min(max(pos - start, 0), len(window))]
    for m in COUNTER_EXAMPLE.finditer(collapsed):
        if m.end() <= here:
            dist = here - m.end()
        elif m.start() >= here:
            dist = m.start() - here
        else:
            dist = 0
        if dist <= PROXIMITY:
            return True
    return False


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def is_archive(path):
    r = rel(path)
    return any(r.startswith(a) for a in ARCHIVE_DIRS)


def walk(root, suffixes):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       {".git", "node_modules", "__pycache__", ".venv", "venv"}]
        for fn in filenames:
            if fn.endswith(suffixes):
                yield os.path.join(dirpath, fn)


def load_skills():
    """Return {name: {plugin, dir, meta, body}} for every SKILL.md."""
    out = {}
    if not os.path.isdir(PLUGINS):
        return out
    for plugin in sorted(os.listdir(PLUGINS)):
        sdir = os.path.join(PLUGINS, plugin, "skills")
        if not os.path.isdir(sdir):
            continue
        for name in sorted(os.listdir(sdir)):
            path = os.path.join(sdir, name, "SKILL.md")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            parts = text.split("---", 2)
            meta, body = {}, text
            if len(parts) >= 3:
                try:
                    loaded = yaml.safe_load(parts[1])
                except yaml.YAMLError as exc:
                    loaded = {"__yaml_error__": str(exc)}
                if loaded is None:
                    loaded = {}
                elif not isinstance(loaded, dict):
                    # There is no frontmatter block at all: the split landed on
                    # two `---` horizontal rules in the body, so safe_load was
                    # handed ordinary markdown and returned a str (or a list).
                    # Record it rather than letting the first meta.get() abort
                    # the run over every other skill.
                    loaded = {"__not_mapping__": type(loaded).__name__}
                meta = loaded
                body = parts[2]
            out[name] = {"plugin": plugin, "dir": os.path.join(sdir, name),
                         "path": path, "meta": meta, "body": body, "folder": name}
    return out


def check(findings):
    def F(code, where, msg):
        findings.append({"level": "FAIL", "code": code, "where": where, "msg": msg})

    def W(code, where, msg):
        findings.append({"level": "WARN", "code": code, "where": where, "msg": msg})

    skills = load_skills()
    if not skills:
        F("no_skills", "plugins/", "no SKILL.md found; is this the marketplace root?")
        return skills

    # --- 1. Every skill loads, and its description survives selection ----------
    for name, s in skills.items():
        where = rel(s["path"])
        meta = s["meta"]
        if "__not_mapping__" in meta:
            F("no_name", where,
              f"no YAML frontmatter: the leading `---` block is missing, so the "
              f"text between the first two `---` parsed as {meta['__not_mapping__']}, "
              f"not a mapping. The skill has no name: and never loads")
            continue
        if "__yaml_error__" in meta:
            F("frontmatter_unparseable", where,
              f"YAML will not parse, so the skill never loads: {meta['__yaml_error__']}. "
              f"Quote a description containing a colon, or use a >- block scalar")
            continue
        if not meta.get("name"):
            F("no_name", where, "frontmatter has no name:")
        elif meta["name"] != s["folder"]:
            F("name_folder_mismatch", where,
              f"frontmatter name {meta['name']!r} != folder {s['folder']!r}; "
              f"skill-bus matches subscriptions on plugin:skill, so this silently "
              f"stops doctrine firing")
        desc = " ".join((meta.get("description") or "").split())
        if not desc:
            F("no_description", where, "no description:; a skill is selected by it")
        elif len(desc) > DESC_LIMIT:
            over = len(desc) - DESC_LIMIT
            tail = desc[DESC_LIMIT:][:60]
            F("description_truncated", where,
              f"description is {len(desc)} chars, {over} over the {DESC_LIMIT} limit. "
              f"Everything past the limit is dropped at selection time, starting: {tail!r}")
        elif len(desc) > DESC_LIMIT * 0.95:
            W("description_near_limit", where,
              f"description is {len(desc)} chars, within 5% of the {DESC_LIMIT} limit")

    # --- 2. Nothing still points at a retired skill or a replaced practice ------
    # Scanned repo-wide, not just in skills: a rep is far more likely to read a
    # README or a runbook than a SKILL.md, and a doc describing the old way is a
    # contradictory instruction, not a stale comment.
    known = set(skills)
    for path in walk(ROOT, (".md", ".json", ".py")):
        r = rel(path)
        if is_archive(path) or r.startswith("scripts/check_marketplace.py"):
            continue
        if is_narrative(path):
            continue          # session records; they describe what changed
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in re.finditer(r"`?\b([a-z][a-z0-9]*(?:-[a-z0-9]+){1,4})\b`?", text):
            token = m.group(1)
            if token in RETIRED_SKILLS and token not in known:
                if is_counter_example(text, m.start()):
                    continue
                line = text[:m.start()].count("\n") + 1
                F("retired_skill_ref", f"{r}:{line}",
                  f"points at `{token}`, which no longer exists — "
                  f"{RETIRED_SKILLS[token]}")
        for pat, truth in SUPERSEDED_PRACTICE:
            for m in pat.finditer(text):
                if is_counter_example(text, m.start()):
                    continue
                line = text[:m.start()].count("\n") + 1
                F("superseded_practice", f"{r}:{line}",
                  f"{m.group(0)!r} describes a replaced practice — {truth}")

    # --- 3. Portability -------------------------------------------------------
    for path in walk(ROOT, (".md", ".py", ".json", ".js")):
        if (is_archive(path) or is_narrative(path)
                or rel(path).startswith("scripts/check_marketplace.py")):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for pat, msg in NONPORTABLE:
            for m in pat.finditer(text):
                if is_counter_example(text, m.start()):
                    continue
                line = text[:m.start()].count("\n") + 1
                F("nonportable_path", f"{rel(path)}:{line}", f"{m.group(0)!r} — {msg}")

    # --- 4. Model IDs ---------------------------------------------------------
    current, superseded = load_models(findings)
    if current:
        stale_re = re.compile("|".join(re.escape(s) for s in superseded)) if superseded else None
        for path in walk(ROOT, (".md", ".json", ".py")):
            if is_archive(path) or rel(path) == "scripts/check_marketplace.py":
                continue
            r = rel(path)
            # The forge's own reference files name superseded IDs deliberately,
            # as counter-examples.
            if r.endswith(("canonical-facts.md", "checklist.md", "models.json",
                           "check_claude_md.py", "refresh_models.py")):
                continue
            if is_narrative(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            if stale_re:
                for m in stale_re.finditer(text):
                    if is_counter_example(text, m.start()):
                        continue
                    line = text[:m.start()].count("\n") + 1
                    F("stale_model_id", f"{r}:{line}",
                      f"{m.group(0)} is superseded; current is {' / '.join(sorted(current))}")

    # --- 5. Form IDs referenced by the form skill exist in the shared rules ----
    check_form_ids(findings, skills)

    # --- 6. Vendor-profile keys referenced actually exist ----------------------
    check_vendor_profile_keys(findings, skills)

    # --- 7. skill-bus subscriptions resolve to a real plugin:skill ------------
    check_skill_bus(findings, skills)

    # --- 8. marketplace.json lists the plugins that exist ---------------------
    check_marketplace_manifest(findings)

    # --- 9. Counts written down match what is on disk -------------------------
    check_counts(findings, skills)

    return skills


# Practices this repo replaced. A live file still describing the old one is not a
# typo — it is a second, contradictory instruction that a rep or an agent may
# follow. Each entry is (pattern, what is true now).
SUPERSEDED_PRACTICE = [
    # Only the unambiguous endpoint. "punchout" on its own is a standard
    # procurement term — a buyer's eProcurement system linking out to a
    # supplier's catalog, cart returning by cXML — and BBS uses it in that
    # sense in grainger-promo-page. Flagging the bare word would fight correct
    # content, and a check that cannot tell two meanings apart should not guess.
    (re.compile(r"\bb2b\.blackboxsafety\.com\b", re.I),
     "BBS's own Grainger punch-out at this endpoint is retired; pricing goes "
     "through the Grainger MCP (grainger-pricing). This does not apply to "
     "punchout catalogs in the general procurement sense"),
]

# Skills removed by consolidation, and where their job went. A reference to one
# of these in a live file is a dangling pointer a rep will follow.
RETIRED_SKILLS = {
    "grainger-cart-info": "merged into rfq-item-extract",
    "grainger-screenshot": "merged into rfq-item-extract",
    "dwr-pdf-info": "merged into rfq-item-extract",
    "obs-form-filler": "merged into ca-form-filler as its OBS 4007(B) path",
    "bbs-b2b-pricing": "replaced by grainger-pricing on the Grainger MCP",
}


def load_models(findings):
    try:
        with open(MODELS_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        findings.append({"level": "WARN", "code": "no_models_json",
                         "where": rel(MODELS_JSON),
                         "msg": f"cannot read model list ({exc}); model-ID check skipped"})
        return set(), set()
    current = set(data.get("current", {}).values())
    sup = data.get("superseded", {})
    superseded = set(sup.keys()) if isinstance(sup, dict) else set(sup)
    return current, superseded


def check_form_ids(findings, skills):
    """Form IDs named by the form skill are checked against the shared rules.

    A near-miss of a documented ID is a FAIL — that is the failure that reaches a
    binding bid (GSPD-05-106 for GSPD-05-105, STD 1000 for OBS 1000). A form that
    is real but simply undocumented in ca-form-rules.md is a WARN against the
    rules file, not the skill.
    """
    s = skills.get("ca-form-filler")
    if not s or not os.path.isfile(FORM_RULES):
        return
    with open(FORM_RULES, encoding="utf-8") as fh:
        rules = fh.read()
    form_re = re.compile(r"\b(?:GSPD-05-\d{3}|STD \d{3,4}|OBS \d{4})\b")
    known = set(re.findall(r"\b(?:GSPD-05-\d{3}|STD \d{3,4}|OBS \d{4}|DGS PD \d+|"
                           r"CalRecycle \d+|CV[- ]?012)\b", rules))
    seen_paths = set()
    for path in [s["path"]] + sorted(walk(s["dir"], (".md",))):
        real = os.path.realpath(path)
        if real in seen_paths:
            continue
        seen_paths.add(real)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in form_re.finditer(text):
            form = m.group(0)
            if form in known or is_counter_example(text, m.start()):
                continue
            line = text[:m.start()].count("\n") + 1
            family = form.rsplit("-", 1)[0] if form.startswith("GSPD") else form.split()[0]
            near = sorted(k for k in known if k.startswith(family))
            if near:
                findings.append({"level": "FAIL", "code": "unknown_form_id",
                                 "where": f"{rel(path)}:{line}",
                                 "msg": f"names {form!r}, which is not in ca-form-rules.md "
                                        f"and looks like a near-miss of {', '.join(near)}. "
                                        f"A wrong form ID goes onto a binding bid"})
            else:
                findings.append({"level": "WARN", "code": "form_id_undocumented",
                                 "where": f"{rel(path)}:{line}",
                                 "msg": f"{form} is used here but not documented in "
                                        f"ca-form-rules.md; add it there so the signing "
                                        f"and leave-blank rules live in one place"})


def check_vendor_profile_keys(findings, skills):
    """Dotted vendor-profile keys quoted in a skill must exist in the profile.

    ca-form-filler's field maps referenced dvbe_details.*, rep.full_name,
    cuf_statement, broker_or_agent and uses_genai — none of which exist, so
    those fields silently filled with nothing.
    """
    try:
        with open(VENDOR_PROFILE, encoding="utf-8") as fh:
            vp = json.load(fh)
    except (OSError, ValueError):
        return

    def keys(d, pre=""):
        out = set()
        for k, v in d.items():
            p = f"{pre}{k}"
            out.add(p)
            if isinstance(v, dict):
                out |= keys(v, p + ".")
            if isinstance(v, list) and v and isinstance(v[0], dict):
                out |= {f"{p}.{ik}" for ik in v[0]}
        return out

    have = keys(vp)
    top = {k.split(".")[0] for k in have}
    pat = re.compile(r"`(" + "|".join(sorted(map(re.escape, top))) + r")((?:\.[a-z_]+)+)`")
    for name, s in skills.items():
        files = [s["path"]] + list(walk(s["dir"], (".md",)))
        for path in files:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            for m in pat.finditer(text):
                key = m.group(1) + m.group(2)
                probe = key.replace("[]", "")
                if probe in have:
                    continue
                # allow one level of list-element addressing
                if any(h.startswith(probe.rsplit(".", 1)[0]) for h in have) and probe in have:
                    continue
                if probe not in have:
                    line = text[:m.start()].count("\n") + 1
                    findings.append({"level": "FAIL", "code": "vendor_profile_key_missing",
                                     "where": f"{rel(path)}:{line}",
                                     "msg": f"`{key}` is not in vendor_profile.json; "
                                            f"the field will fill with nothing"})


def check_skill_bus(findings, skills):
    """Every skill-bus subscription must name a skill that exists."""
    for path in walk(PLUGINS, ("skill-bus.json", "hooks.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            findings.append({"level": "FAIL", "code": "hook_unparseable",
                             "where": rel(path), "msg": str(exc)})
            continue
        for sub in (data.get("subscriptions") or []):
            target = sub.get("on", "")
            if ":" not in target:
                continue
            plugin, _, skill = target.partition(":")
            if skill in ("*", ""):
                continue
            local_plugins = {d for d in os.listdir(PLUGINS)
                             if os.path.isdir(os.path.join(PLUGINS, d))}
            if plugin not in local_plugins:
                continue          # pinned external plugin; not ours to resolve
            s = skills.get(skill)
            if s is None:
                # A subscription may legitimately target a command rather than a skill.
                cmd = os.path.join(PLUGINS, plugin, "commands", f"{skill}.md")
                if os.path.isfile(cmd):
                    continue
                findings.append({"level": "FAIL", "code": "skill_bus_dangling",
                                 "where": rel(path),
                                 "msg": f"subscribes to {target!r}, but {plugin!r} has no "
                                        f"skill or command named {skill!r}; doctrine "
                                        f"silently never fires"})
            elif s["plugin"] != plugin:
                findings.append({"level": "FAIL", "code": "skill_bus_wrong_plugin",
                                 "where": rel(path),
                                 "msg": f"subscribes to {target!r}, but {skill!r} lives in "
                                        f"{s['plugin']!r}; the match is on plugin:skill"})


def check_counts(findings, skills):
    """A skill count written into a README badge is a fact, and facts drift.

    Every one of these was wrong at some point: the sales badge said 14 after the
    consolidation left 10, and the foundations badge said 1 when it had 2.
    """
    actual = {}
    for plugin in sorted(os.listdir(PLUGINS)):
        sdir = os.path.join(PLUGINS, plugin, "skills")
        if os.path.isdir(sdir):
            actual[plugin] = len([d for d in os.listdir(sdir)
                                  if os.path.isfile(os.path.join(sdir, d, "SKILL.md"))])
    badge = re.compile(r"badge/skills-(\d+)-")
    for plugin, n in actual.items():
        readme = os.path.join(PLUGINS, plugin, "README.md")
        if not os.path.isfile(readme):
            continue
        with open(readme, encoding="utf-8") as fh:
            text = fh.read()
        for m in badge.finditer(text):
            claimed = int(m.group(1))
            if claimed != n:
                line = text[:m.start()].count("\n") + 1
                findings.append({"level": "FAIL", "code": "skill_count_wrong",
                                 "where": f"{rel(readme)}:{line}",
                                 "msg": f"badge claims {claimed} skills; {plugin} has {n}"})


def check_marketplace_manifest(findings):
    manifest = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    try:
        with open(manifest, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        findings.append({"level": "FAIL", "code": "manifest_unparseable",
                         "where": rel(manifest), "msg": str(exc)})
        return
    listed = set()
    for p in data.get("plugins", []):
        src = p.get("source") or ""
        if isinstance(src, str) and src.startswith("./plugins/"):
            listed.add(src.rsplit("/", 1)[-1])
        elif p.get("name"):
            listed.add(p["name"])
    on_disk = {d for d in os.listdir(PLUGINS)
               if os.path.isdir(os.path.join(PLUGINS, d))}
    for missing in sorted(on_disk - listed):
        findings.append({"level": "WARN", "code": "plugin_not_listed",
                         "where": rel(manifest),
                         "msg": f"plugins/{missing} exists but is not in marketplace.json"})


def main():
    ap = argparse.ArgumentParser(description="BBS marketplace structural checks")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    findings = []
    skills = check(findings)
    fails = [f for f in findings if f["level"] == "FAIL"]
    warns = [f for f in findings if f["level"] == "WARN"]

    if args.json:
        print(json.dumps({"skills": len(skills), "findings": findings,
                          "fails": len(fails), "warns": len(warns)}, indent=2))
    else:
        for f in findings:
            print(f"{f['level']:4} {f['code']:<28} {f['where']}\n       {f['msg']}")
        print(f"\n{len(skills)} skill(s) · {len(fails)} FAIL · {len(warns)} WARN")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
