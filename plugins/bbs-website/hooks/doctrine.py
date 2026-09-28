#!/usr/bin/env python3
"""Inject BBS doctrine before a subscribed skill runs — the python3 twin of doctrine.ps1.

Same events, same table, same output bytes (tests/parity.py proves it):
  PreToolUse (matcher "Skill")  — tool_input.skill is the name.
  UserPromptExpansion           — command_name is the name, usually bare, sometimes
                                  "plugin:name".
Runs on a machine with python3 and no PowerShell (a Mac before `brew install
powershell`). Stdlib only. Always exit 0, never write a file, never print to stderr:
a hook error must never block a skill. The doctrine files are the truth; this script
re-keys nothing.
"""
import fnmatch
import json
import os
import sys


def main():
    try:
        sys.stdin.reconfigure(encoding="utf-8-sig", errors="replace")
    except (AttributeError, ValueError):
        pass
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return
    raw = raw.lstrip("﻿")
    h = json.loads(raw)
    if not isinstance(h, dict):
        return

    event = h.get("hook_event_name")
    if not event:
        if h.get("tool_name") == "Skill":
            event = "PreToolUse"
        else:
            return
    if event == "PreToolUse":
        if h.get("tool_name") != "Skill":
            return
        ti = h.get("tool_input")
        name = ti.get("skill") if isinstance(ti, dict) else None
    elif event == "UserPromptExpansion":
        name = h.get("command_name")
    else:
        return
    if not isinstance(name, str) or not name.strip():
        return

    here = os.path.dirname(os.path.abspath(__file__))
    ddir = os.path.join(here, "doctrine")
    with open(os.path.join(ddir, "subscriptions.json"), encoding="utf-8-sig") as fh:
        table = json.load(fh)
    subs = table.get("subscriptions") or []

    # A tool call arrives fully qualified. A typed command arrives bare and does not say
    # which plugin it came from, so it is also tried under this plugin's own prefix and
    # under each local plugin prefix the table lists in bare_prefixes (the checker proves
    # each is a real plugin). Not under every prefix the table mentions: claudeforge:*
    # would then fire on every bare name.
    candidates = [name]
    if event == "UserPromptExpansion" and ":" not in name:
        prefixes = [os.path.basename(os.path.dirname(here))]
        for p in table.get("bare_prefixes") or []:
            if p and str(p) not in prefixes:
                prefixes.append(str(p))
        candidates += [f"{p}:{name}" for p in prefixes]

    def matches(n, pattern):
        # Only * is a wildcard in a subscription pattern; case-insensitive like -like.
        p = pattern.replace("[", "[[]").replace("?", "[?]")
        return fnmatch.fnmatchcase(n.lower(), p.lower())

    matched = []
    for sub in subs:
        insert, on = sub.get("insert"), sub.get("on")
        if not insert or not on or insert in matched:
            continue
        if any(matches(c, str(on)) for c in candidates):
            matched.append(insert)
    if not matched:
        return

    parts = []
    inserts = table.get("inserts") or {}
    for ins in matched:
        spec = inserts.get(ins) or {}
        fn = spec.get("file") if isinstance(spec, dict) else None
        if not fn:
            continue
        path = os.path.join(ddir, fn)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
        # An autocrlf checkout would otherwise inject \r; the file's own bytes are LF.
        parts.append(text.replace("\r\n", "\n"))
    if not parts:
        return

    context = "\n\n".join(parts)
    out = ('{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}'
           % (event, json.dumps(context, ensure_ascii=True)))
    sys.stdout.write(out)
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 — fail open, silently
        pass
    sys.exit(0)
