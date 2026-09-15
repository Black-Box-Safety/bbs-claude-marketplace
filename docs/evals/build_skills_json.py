#!/usr/bin/env python3
"""Regenerate skills.json — the field of descriptions the eval competes.

The field must be everything the person has installed, not one plugin: a skill
cannot lose to a sibling that is not in the room. For a sales rep that is all of
bbs-sales plus bbs-deck-voice, which lives in bbs-foundations.

Run from this directory: python3 build_skills_json.py
"""
import json
import pathlib

import yaml

FIELD = [("bbs-sales", None), ("bbs-foundations", {"bbs-deck-voice"})]
HERE = pathlib.Path(__file__).resolve().parent
PLUGINS = HERE.parent.parent / "plugins"


def main():
    out = {}
    for plugin, only in FIELD:
        for d in sorted((PLUGINS / plugin / "skills").iterdir()):
            if only is not None and d.name not in only:
                continue
            meta = yaml.safe_load((d / "SKILL.md").read_text().split("---", 2)[1])
            if meta["name"] != d.name:
                raise SystemExit(f"{d}: frontmatter name {meta['name']!r} != folder name")
            out[meta["name"]] = " ".join(meta["description"].split())
    (HERE / "skills.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"skills.json: {len(out)} skills")


if __name__ == "__main__":
    main()
