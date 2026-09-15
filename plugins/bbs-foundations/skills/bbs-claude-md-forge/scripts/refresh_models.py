#!/usr/bin/env python3
"""
refresh_models.py — keep references/models.json current from the Anthropic Models API.

The model list used to be hand-maintained in two places and went stale in both, with the
checker still telling authors to write the superseded ID. This script makes the list a
derived artifact instead: it asks the API what exists and rewrites the file.

Usage:
    python3 refresh_models.py            # rewrite models.json if anything changed
    python3 refresh_models.py --check    # change nothing; exit 1 if it is out of date
    python3 refresh_models.py --dry-run  # print the new file, write nothing

Exit codes:
    0  already current (or written successfully)
    1  out of date (--check), or the file was rewritten (so CI can open a PR)
    2  could not reach the API — models.json is left exactly as it was

Auth: the SDK resolves credentials itself — ANTHROPIC_API_KEY, or a profile from
`ant auth login`. An unset ANTHROPIC_API_KEY does not mean there are no credentials.

Deliberately does NOT decide which models BBS adopts. It refreshes what exists and which
ID is newest per family; `known_not_adopted` and the roles stay under human control,
because "should BBS pay Fable-tier prices" is not a question an API answers.
"""

import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_JSON = os.path.join(os.path.dirname(HERE), "references", "models.json")

# BBS runs three tiers. Anything else the API returns is recorded, never auto-adopted.
ADOPTED_FAMILIES = ("opus", "sonnet", "haiku")
DATED = re.compile(r"-20\d{6}$")
FAMILY = re.compile(r"^claude-([a-z]+)-")


def fetch_models():
    """Return [(id, created_at)] for every model the account can see, newest first."""
    try:
        import anthropic
    except ImportError:
        sys.exit("The anthropic SDK is required: pip install anthropic")

    client = anthropic.Anthropic()
    models = []
    for m in client.models.list():
        created = getattr(m, "created_at", None)
        models.append((m.id, str(created) if created else ""))
    if not models:
        sys.exit(2)
    # Newest first. created_at sorts correctly as an ISO string; ties keep API order.
    return sorted(models, key=lambda pair: pair[1], reverse=True)


def current_by_family(models):
    """Newest undated ID per adopted family.

    Undated on purpose: a dated snapshot is a pin, not the ID BBS should be writing.
    """
    current = {}
    for model_id, _created in models:
        if DATED.search(model_id):
            continue
        match = FAMILY.match(model_id)
        if not match:
            continue
        family = match.group(1)
        if family in ADOPTED_FAMILIES and family not in current:
            current[family] = model_id
    return current


def build(existing, models):
    """Return the refreshed document, preserving every human-owned field."""
    new = json.loads(json.dumps(existing))  # deep copy
    current = current_by_family(models)

    missing = [f for f in ADOPTED_FAMILIES if f not in current]
    if missing:
        # Never half-write the list: a family the API didn't return means something
        # changed that a human should look at, not that BBS should drop a tier.
        sys.exit(f"the API returned no undated model for: {', '.join(missing)}. "
                 f"models.json left unchanged — check the API response by hand.")

    superseded = dict(new.get("superseded", {}))
    live = {mid for mid, _ in models}
    for model_id, _created in models:
        if DATED.search(model_id):
            continue
        match = FAMILY.match(model_id)
        if not match:
            continue
        family = match.group(1)
        if family in ADOPTED_FAMILIES and model_id != current[family]:
            superseded[model_id] = current[family]
    # Keep retired IDs that the API no longer lists — someone may still have one written
    # down, and that is exactly when the checker needs to recognise it.
    for old, replacement in new.get("superseded", {}).items():
        if old not in live:
            superseded[old] = replacement

    new["current"] = {f: current[f] for f in ADOPTED_FAMILIES}
    new["superseded"] = dict(sorted(superseded.items()))
    new["_meta"]["generated_at"] = dt.date.today().isoformat()
    new["_meta"]["generated_by"] = "scripts/refresh_models.py (GET /v1/models)"
    return new


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if out of date; write nothing")
    ap.add_argument("--dry-run", action="store_true", help="print the result; write nothing")
    args = ap.parse_args()

    with open(MODELS_JSON) as f:
        existing = json.load(f)

    new = build(existing, fetch_models())

    # generated_at always moves; compare the parts that carry meaning.
    def meaningful(doc):
        return {k: v for k, v in doc.items() if k != "_meta"}

    if meaningful(new) == meaningful(existing):
        print(f"models.json is current: {', '.join(sorted(new['current'].values()))}")
        return 0

    before = existing.get("current", {})
    print("Model list changed:")
    for family in ADOPTED_FAMILIES:
        was, now = before.get(family), new["current"][family]
        print(f"  {family:<7} {was} -> {now}" if was != now else f"  {family:<7} {now} (unchanged)")

    if args.check:
        print("\nOut of date. Run without --check to rewrite.")
        return 1
    if args.dry_run:
        print("\n" + json.dumps(new, indent=2))
        return 1

    with open(MODELS_JSON, "w") as f:
        json.dump(new, f, indent=2)
        f.write("\n")
    print(f"\nRewrote {MODELS_JSON}")
    print("Now update the prose that quotes it: references/canonical-facts.md and README.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
