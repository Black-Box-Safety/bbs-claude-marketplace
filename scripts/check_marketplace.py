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
    """Return ({name: {plugin, dir, meta, body}}, duplicates) for every SKILL.md.

    Keyed on the bare folder name because that is what skill-bus subscriptions and
    cross-references use. That makes a name reused in two plugins a silent data
    loss — the second load overwrote the first and the first vanished from every
    check — so collisions are collected and reported rather than swallowed.
    """
    out, dupes = {}, []
    if not os.path.isdir(PLUGINS):
        return out, dupes
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
            entry = {"plugin": plugin, "dir": os.path.join(sdir, name),
                     "path": path, "meta": meta, "body": body, "folder": name}
            if name in out:
                dupes.append((name, out[name]["plugin"], plugin))
                continue          # keep the first; never silently replace it
            out[name] = entry
    return out, dupes


def check(findings):
    def F(code, where, msg):
        findings.append({"level": "FAIL", "code": code, "where": where, "msg": msg})

    def W(code, where, msg):
        findings.append({"level": "WARN", "code": code, "where": where, "msg": msg})

    skills, dupes = load_skills()
    for name, first, second in dupes:
        F("duplicate_skill_name", f"plugins/{second}/skills/{name}/SKILL.md",
          f"skill folder {name!r} also exists in {first!r}. Skills are keyed on the bare "
          f"name — skill-bus matches on plugin:skill and cross-references name it — so one "
          f"of the two disappears from every check. Rename one, or finish the move")
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

    # --- 7. Every skill declares the external systems it needs ----------------
    check_dependencies(findings, skills)

    # --- 8. skill-bus subscriptions resolve to a real plugin:skill ------------
    check_skill_bus(findings, skills)

    # --- 9. marketplace.json lists the plugins that exist ---------------------
    check_marketplace_manifest(findings)

    # --- 10. Counts written down match what is on disk ------------------------
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


# ---------------------------------------------------------------------------
# External systems a skill can depend on, and how to *prove* it uses one.
#
# Signals are ENUMERATED IDENTIFIERS, never brand names. That is the whole
# lesson of this check. Two scans of these same 27 skills, differing only in
# regex phrasing, disagreed by five skills (20 vs 25) because they scanned for
# "Business Central" and "Grainger" — words that name a record or a part number
# at least as often as they name a system:
#
#   dgs-bpo-item-check   says "Grainger part number" six times and tells you
#                        "Do not search the web, do not check Grainger.com".
#   rfq-item-extract     parses "Grainger cart" PDFs with no connector at all.
#   le-lane-tuning       cites "Business Central purchase spend" as provenance
#                        for a list it reads out of the bbs-suppliers repo.
#
# A prefix is no better: bbs-pricelist-import contains `bc_sync_queue` and
# `bc_vendor_no`, which are SUPABASE COLUMN NAMES. A `bc_*` pattern invents a
# Business Central dependency on a skill that never touches it. So the Business
# Central signal is the ten real tool names, written out.
#
# A brand name is admissible only where the brand has no other sense in this
# domain — Firecrawl, Sirv and CData Connect AI name nothing but themselves.
#
# Fields:
#   kind      what a rep has to install: mcp | connector | service | cli |
#             python-package. Lives HERE, once, and never in a skill's
#             frontmatter — the kind of a system is a property of the system,
#             and restating it in twelve skills is invariant 2 broken twelve
#             times.
#   signals   patterns that prove use.
#   canon     the string that must appear in canonical-facts.md's "Systems of
#             record" table. That table is the authority for what BBS's systems
#             are called, so the registry is bonded to it: rename a system in
#             canon without touching this and the checker FAILs. None means the
#             system is not in canon yet, which is reported, not invented.
#   bootstrap the winget id scripts/bbs-setup.ps1 installs it under, for cli
#             entries. None means a rep who ran the bootstrap does not have it.
EXTERNAL_SYSTEMS = {
    # --- systems of record and connectors ---------------------------------
    "business-central": {
        "kind": "mcp", "canon": "Business Central",
        "signals": [r"\bbc_(?:customer_snapshot|describe_entity|find_customer|find_item|"
                    r"get_company_info|get_sales_document|list_entity_sets|"
                    r"list_open_sales_orders|list_unpaid_invoices|query_entity)\b"],
    },
    # A second, separate path to the same company data: a proxy exposing BC's
    # OData pages as ListXxx_PAGnnnnn. so-search and bbs-po-status use it and
    # the bc_* MCP not at all. Flattening the two into "Business Central" would
    # tell a rep to install the wrong one, which reads as authoritative and is
    # worse than saying nothing. Anchored on the PAG suffix so it cannot match
    # the repo NAME bbs-bc-mcp-proxy, which the forge quotes as an example.
    "bc-mcp-proxy": {
        "kind": "mcp", "canon": None,
        "signals": [r"\b\w*_PAG\d{5}\b", r"\bbc-mcp-proxy:"],
    },
    # And a third: CData Connect AI over catalog Dynamics365BusinessCentral1.
    "cdata-connect": {
        "kind": "connector", "canon": None,
        "signals": [r"\bCData Connect AI\b", r"\bDynamics365BusinessCentral1\b"],
    },
    "grainger": {
        "kind": "mcp", "canon": "Grainger MCP",
        # Tool names only. "Grainger MCP" reads as a dependency in
        # rfq-item-extract, which names it solely to say that `grainger-pricing`
        # is the skill that prices the list it just extracted.
        "signals": [r"\bgrainger_(?:accounts|availability|price|resolve_part|search|xref)\b"],
    },
    "supabase": {
        "kind": "mcp", "canon": "Supabase",
        # Tool names and credential names only. "Supabase Postgres" and
        # "Supabase project" are prose: site-wiring-map uses both while
        # invoking nothing, and supply-lane-tuning names the DB it is
        # describing, not one it opens.
        "signals": [r"\b(?:execute_sql|apply_migration|list_migrations|"
                    r"generate_typescript_types|deploy_edge_function)\b",
                    r"\bSUPABASE_(?:URL|SERVICE_KEY|DB_PASSWORD|ANON_KEY)\b"],
    },
    "shopify": {
        "kind": "mcp", "canon": "Shopify",
        "signals": [r"\bShopify MCP\b",
                    r"\bSHOPIFY_(?:ADMIN_API_TOKEN|STORE_DOMAIN)\b",
                    r"\bgraphql_(?:query|mutation|schema)\b"],
    },
    "microsoft-365": {
        "kind": "connector", "canon": "SharePoint",
        # Lowercase tool names, so the word "Outlook" in vendor-quote-email's
        # "Copy for Outlook" clipboard button is not read as a mailbox call.
        "signals": [r"\b(?:outlook|sharepoint|teams)_[a-z_]+\b",
                    r"\bchat_message_search\b", r"\bM365 tools\b"],
    },
    "ca-procurement-intel": {
        "kind": "mcp", "canon": "ca-procurement-intel",
        "signals": [r"\b(?:explore_sql|market_spend_summary|market_purchase_lines|"
                    r"market_last_sales|market_product_search)\b",
                    r"\bplay_[a-z_]+\b"],
    },
    "firecrawl": {
        "kind": "mcp", "canon": None,
        # Not the bare word: site-wiring-map's map of the three repos says
        # "Firecrawl enrichment" as a description of what bbs-database contains.
        "signals": [r"\bfirecrawl_[a-z_]+\b", r"\bFIRECRAWL_KEY\b", r"\bFirecrawl MCP\b"],
    },
    "sirv": {
        "kind": "service", "canon": None,
        # Likewise: "the Sirv image CDN" in a repo map is a description.
        "signals": [r"\bSIRV_[A-Z_]+\b", r"\bsirv\.com\b"],
    },

    # --- command-line tools ------------------------------------------------
    "python3": {
        "kind": "cli", "canon": None, "bootstrap": "astral-sh.uv",
        "signals": [r"\bpython3? [\"'$]", r"\bpython3?\s+\S*\.py\b"],
    },
    "node": {
        "kind": "cli", "canon": None, "bootstrap": "OpenJS.NodeJS.LTS",
        "signals": [r"\bnode\s+\S*\.(?:js|mjs)\b", r"\bnpm (?:install|run|ci)\b"],
    },
    # Not in bbs-setup.ps1. bbs-quote-builder converts its docx to the PDF it
    # promises to deliver with `soffice --headless`, so a rep who ran the
    # bootstrap and nothing else cannot finish a quote. cli_not_bootstrapped
    # exists to say so out loud.
    "libreoffice": {
        "kind": "cli", "canon": None, "bootstrap": None,
        "signals": [r"\bsoffice\b", r"\blibreoffice\b"],
    },
    "shopify-cli": {
        "kind": "cli", "canon": None, "bootstrap": None,
        "signals": [r"\bshopify (?:theme|app) [a-z]+"],
    },
    "vercel-cli": {
        "kind": "cli", "canon": None, "bootstrap": None,
        "signals": [r"\bvercel (?:deploy|link|env|--prod)\b"],
    },

    # --- python packages ---------------------------------------------------
    # Named because their absence is the actual failure a rep hits: python3 is
    # present and the script still dies on import.
    "pypdf": {"kind": "python-package", "canon": None,
              "signals": [r"^\s*(?:import|from) pypdf\b"]},
    "pymupdf": {"kind": "python-package", "canon": None,
                "signals": [r"^\s*(?:import|from) fitz\b", r"\bPyMuPDF\b"]},
    "anthropic": {"kind": "python-package", "canon": None,
                  "signals": [r"^\s*(?:import|from) anthropic\b"]},
}

DEP_KEYS = ("requires", "degrades-without")

# canonical-facts.md is where this registry's `canon` anchors are checked, so
# scanning it for undeclared dependencies is circular: it names `execute_sql`
# and `shopify theme list` as company canon, not as instructions to
# bbs-claude-md-forge, which merely hosts the file.
DEP_SCAN_EXEMPT = ("references/canonical-facts.md",)


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
    if not os.path.isfile(FORM_RULES):
        return
    with open(FORM_RULES, encoding="utf-8") as fh:
        rules = fh.read()
    form_re = re.compile(r"\b(?:GSPD-05-\d{3}|STD \d{3,4}|OBS \d{4})\b")
    known = set(re.findall(r"\b(?:GSPD-05-\d{3}|STD \d{3,4}|OBS \d{4}|DGS PD \d+|"
                           r"CalRecycle \d+|CV[- ]?012)\b", rules))
    # Scan every plugin markdown file, not just ca-form-filler's. The form IDs are
    # a shared fact and they are quoted wherever BBS describes a bid packet — the two
    # `STD 1000` survivors of the OBS 1000 fix were in plugins/bbs-website/agents/,
    # which this check could not see. A checker whose scope is narrower than the fact
    # it guards is invariant 3 broken from the other end.
    seen_paths = set()
    for path in sorted(walk(PLUGINS, (".md",))):
        if is_archive(path) or is_narrative(path):
            continue
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
            # Both branches FAIL. The earlier code had the second as a WARN,
            # which was unreachable: `near` is empty only for a family with no
            # documented member, and all three families form_re can match
            # (GSPD-05, STD, OBS) already have one. Making it reachable means
            # loosening the near-miss test, and that test is what caught the two
            # `STD 1000` survivors of the OBS 1000 fix — loosening a control on a
            # binding document is Parker's call, not a checker's. What is fixed
            # here is the message: an undocumented form was being told it was "a
            # near-miss of STD 204, STD 205" when it is not one, and a checker
            # that says something untrue about a bid gets ignored.
            typo = sorted(k for k in near if _one_edit_apart(form, k))
            if typo:
                findings.append({"level": "FAIL", "code": "unknown_form_id",
                                 "where": f"{rel(path)}:{line}",
                                 "msg": f"names {form!r}, which is not in ca-form-rules.md "
                                        f"and is one character from {', '.join(typo)}. "
                                        f"A wrong form ID goes onto a binding bid"})
            else:
                findings.append({"level": "FAIL", "code": "unknown_form_id",
                                 "where": f"{rel(path)}:{line}",
                                 "msg": f"names {form!r}, which is not in ca-form-rules.md. "
                                        f"Documented {family} forms are {', '.join(near)}. "
                                        f"Either it is wrong, or it is real and belongs in "
                                        f"ca-form-rules.md so the signing and leave-blank "
                                        f"rules live in one place. A wrong form ID goes onto "
                                        f"a binding bid"
                                        if near else
                                        f"names {form!r}, which is not in ca-form-rules.md"})


def _one_edit_apart(a, b):
    """True if a and b differ by a single substitution, insertion or deletion.

    Distinguishes a slip of the finger (GSPD-05-106 for GSPD-05-105) from a form
    that is simply not documented yet, so the finding can say which it is.
    """
    if a == b:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if abs(len(a) - len(b)) != 1:
        return False
    lo, hi = (a, b) if len(a) < len(b) else (b, a)
    i = 0
    while i < len(lo) and lo[i] == hi[i]:
        i += 1
    return lo[i:] == hi[i + 1:]


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


def _dep_files(skill):
    """Every file a skill carries, because the dependency is not always in SKILL.md.

    bbs-order-reconciliation's real bc_* calls live in references/tool-recipes.md
    and grainger-promo-page's in scripts/units_from_bc.py. A scan narrower than
    the skill would pass both while the rep's job fails.
    """
    out, seen = [], set()
    for path in sorted(walk(skill["dir"], (".md", ".py", ".js", ".mjs", ".json", ".ps1"))):
        r = rel(path)
        if any(r.endswith(x) for x in DEP_SCAN_EXEMPT):
            continue
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        out.append(path)
    return out


def _declared(meta, key):
    """(values, error) for one dependency key. Absent is not the same as empty."""
    if key not in meta:
        return None, None
    v = meta[key]
    if v is None:
        return [], None
    if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
        return None, f"{key}: must be a list of system ids, got {type(v).__name__}"
    return [x.strip() for x in v], None


def check_dependencies(findings, skills):
    """Every skill declares the external systems it needs, and use implies a declaration.

    Two directions, and they do different jobs:

    * `requires:` is MANDATORY. The completeness this check delivers comes from
      the key being required, not from the scanner being clever — a skill that
      says "look it up in Business Central" in prose and never names a tool is
      invisible to any scanner, so the five skills that need nothing write
      `requires: []` as a reviewed assertion rather than leaving a hole that
      reads the same as an oversight.
    * `undeclared_dependency` is a FLOOR, not a ceiling. It proves only what an
      enumerated identifier can prove, and it is the half a reviewer can trust
      without re-reading 27 skills.

    Over-declaration is a WARN: a rep installing one connector too many is the
    safe direction, and the unsafe one is the bid that stops halfway.
    """
    compiled = {sid: [re.compile(p, re.M) for p in spec["signals"]]
                for sid, spec in EXTERNAL_SYSTEMS.items()}
    # Declarations that no enumerated identifier can corroborate. Saying so is the
    # honest half of this check — but as one WARN each they were sixteen lines of
    # identical prose that buried the four findings a reader has to act on, which is
    # how a checker gets ignored. Collected and reported once.
    uncorroborated = []

    for name, s in sorted(skills.items()):
        meta, where = s["meta"], rel(s["path"])
        if "__yaml_error__" in meta or "__not_mapping__" in meta:
            continue          # already reported; frontmatter never parsed

        declared, bad = {}, False
        for key in DEP_KEYS:
            vals, err = _declared(meta, key)
            if err:
                findings.append({"level": "FAIL", "code": "requires_malformed",
                                 "where": where, "msg": err})
                bad = True
            elif vals is None and key == "requires":
                findings.append({"level": "FAIL", "code": "missing_requires",
                                 "where": where,
                                 "msg": "no requires: key. Every skill declares the external "
                                        "systems it needs so a rep can tell before installing "
                                        "whether the job will run. A skill that needs nothing "
                                        "writes `requires: []` — an omitted key and a declared "
                                        "empty one read the same to a rep and must not"})
                bad = True
            else:
                declared[key] = vals or []
        if bad:
            continue

        all_declared = set(declared["requires"]) | set(declared.get("degrades-without") or [])
        for sid in sorted(all_declared):
            if sid not in EXTERNAL_SYSTEMS:
                near = sorted(k for k in EXTERNAL_SYSTEMS if k.split("-")[0] == sid.split("-")[0])
                findings.append({"level": "FAIL", "code": "unknown_dependency_id",
                                 "where": where,
                                 "msg": f"declares {sid!r}, which is not a known system. "
                                        f"A typo declares nothing and reads as a declaration"
                                        + (f". Did you mean {', '.join(near)}?" if near else "")})

        # --- use implies declaration -------------------------------------
        found = {}
        for path in _dep_files(s):
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            for sid, pats in compiled.items():
                for pat in pats:
                    for m in pat.finditer(text):
                        # Prose naming a system in order to warn about it is
                        # correct content, not a dependency. bbs-quote-builder's
                        # "Do NOT use this skill to pull existing quote records
                        # out of Business Central" must not read as a Business
                        # Central dependency.
                        if is_counter_example(text, m.start()):
                            continue
                        found.setdefault(sid, (rel(path), text[:m.start()].count("\n") + 1,
                                               m.group(0)))
                        break
                    if sid in found:
                        break

        for sid, (fpath, line, tok) in sorted(found.items()):
            if sid in all_declared:
                continue
            kind = EXTERNAL_SYSTEMS[sid]["kind"]
            findings.append({"level": "FAIL", "code": "undeclared_dependency",
                             "where": f"{fpath}:{line}",
                             "msg": f"uses {tok!r}, so this skill needs the {sid!r} {kind}, "
                                    f"but {name!r} does not declare it. Add {sid!r} to "
                                    f"requires: (or to degrades-without: if the skill still "
                                    f"completes without it). Undeclared, a rep finds out when "
                                    f"the job stops"})

        # A declared python package implies the interpreter: price-list-cleaner
        # tells Claude to extract with `fitz` and never shells out to `python x.py`,
        # so python3 is corroborated by pymupdf rather than needing its own proof.
        if any(EXTERNAL_SYSTEMS.get(x, {}).get("kind") == "python-package" and x in found
               for x in all_declared):
            found.setdefault("python3", ("(implied by a declared python package)", 0, ""))

        for sid in sorted(all_declared):
            if sid in EXTERNAL_SYSTEMS and sid not in found:
                uncorroborated.append(f"{name}:{sid}")

        for sid in sorted(all_declared):
            spec = EXTERNAL_SYSTEMS.get(sid)
            if spec and spec["kind"] == "cli" and spec.get("bootstrap") is None:
                findings.append({"level": "WARN", "code": "cli_not_bootstrapped",
                                 "where": where,
                                 "msg": f"needs the {sid!r} command line tool, which "
                                        f"scripts/bbs-setup.ps1 does not install. A rep who ran "
                                        f"the bootstrap and nothing else cannot finish this job"})

    if uncorroborated:
        hit = sorted({u.split(":")[0] for u in uncorroborated})
        findings.append({"level": "WARN", "code": "dependencies_uncorroborated",
                         "where": "plugins/",
                         "msg": f"{len(uncorroborated)} declaration(s) across {len(hit)} skill(s) "
                                f"are not corroborated by any identifier in the skill. They are "
                                f"read from prose by a human, not machine-checked, and a reviewer "
                                f"should treat them as assertions: "
                                f"{', '.join(uncorroborated)}. Over-declaring is the safe "
                                f"direction, so this never FAILs"})

    check_dependency_registry(findings)


def check_dependency_registry(findings):
    """The registry is bonded to canon, so it cannot quietly become a third source of truth.

    canonical-facts.md's "Systems of record" table is the authority for what BBS's
    systems are called. Every registry entry claiming an anchor there must still
    find it (invariant 3, from the checker's side). An entry with no anchor is
    reported rather than invented — adding a row to company canon is Parker's,
    not a checker's.
    """
    canon_path = os.path.join(PLUGINS, "bbs-foundations", "skills", "bbs-claude-md-forge",
                              "references", "canonical-facts.md")
    try:
        with open(canon_path, encoding="utf-8") as fh:
            canon = fh.read()
    except OSError:
        return
    for sid, spec in sorted(EXTERNAL_SYSTEMS.items()):
        anchor = spec.get("canon")
        if anchor is None:
            if spec["kind"] in ("mcp", "connector", "service"):
                findings.append({"level": "WARN", "code": "system_not_in_canon",
                                 "where": rel(canon_path),
                                 "msg": f"skills depend on the {sid!r} {spec['kind']}, but it is "
                                        f"not in the Systems of record table. Canon is the "
                                        f"authority for what BBS's systems are called; adding a "
                                        f"row to it is Parker's call, not a checker's"})
            continue
        if anchor not in canon:
            findings.append({"level": "FAIL", "code": "dependency_registry_drift",
                             "where": rel(canon_path),
                             "msg": f"the dependency registry anchors {sid!r} on {anchor!r}, "
                                    f"which no longer appears here. A fact with a checker is "
                                    f"inseparable from its checker — change both or neither"})


def requirements_table(skills):
    """The 'can I run this?' view, derived at read time and never stored twice."""
    rows = []
    for name, s in sorted(skills.items()):
        meta = s["meta"]
        req = meta.get("requires") if isinstance(meta.get("requires"), list) else []
        opt = (meta.get("degrades-without")
               if isinstance(meta.get("degrades-without"), list) else [])

        def fmt(ids):
            return ", ".join(f"{i} ({EXTERNAL_SYSTEMS[i]['kind']})"
                             if i in EXTERNAL_SYSTEMS else f"{i} (UNKNOWN)"
                             for i in ids) or "—"
        rows.append((s["plugin"], name, fmt(req), fmt(opt)))
    return sorted(rows)


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
    ap.add_argument("--requirements", action="store_true",
                    help="print what each skill needs installed, and exit")
    args = ap.parse_args()

    if args.requirements:
        skills, _ = load_skills()
        rows = requirements_table(skills)
        w = max(len(r[1]) for r in rows) if rows else 10
        plugin = None
        for pl, name, req, opt in rows:
            if pl != plugin:
                plugin, _ = pl, print(f"\n{pl}")
            print(f"  {name:<{w}}  requires: {req}")
            if opt != "\u2014":
                print(f"  {'':<{w}}  degrades without: {opt}")
        print(f"\n{len(rows)} skill(s). Kinds: mcp/connector/service are installed per "
              f"account;\ncli and python-package are installed on the machine "
              f"(scripts/bbs-setup.ps1).")
        sys.exit(0)

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
