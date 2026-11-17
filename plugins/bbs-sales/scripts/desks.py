"""Desk registry loader. Stdlib only. load() never raises."""
import copy
import json
import os
import re
from typing import NamedTuple

REGISTRY_ENV = "BBS_DESKS_FILE"

# Built-in ca-state profile; must equal the references/desks.json entry (checker enforces).
FALLBACK = [
    {
        "desk_id": "ca-state",
        "kind": "rfq",
        "roots": ["All RFQ's by Agency"],
        "deal_depth": [2, 3],
        "deal_name_rule": "date",
        "rep_min_depth": 2,
        "guard": {"no_rename": True, "near_duplicate": True, "filled_immutable": True},
        "record_profile": "ca-v2",
    }
]

_KEYS = {"desk_id", "kind", "roots", "deal_depth", "deal_name_rule", "rep_min_depth", "guard", "record_profile"}
_GUARD_KEYS = {"no_rename", "near_duplicate", "filled_immutable"}


class Match(NamedTuple):
    desk: dict
    root: str
    start: int
    end: int


def registry_path():
    env = os.environ.get(REGISTRY_ENV)
    if env:
        return env
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "references", "desks.json")


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _check(data):
    """Return an error string naming the offending key, or None."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return "schema_version must be 1"
    desks = data.get("desks")
    if not isinstance(desks, list) or not desks:
        return "desks must be a non-empty list"
    seen = set()
    for d in desks:
        if not isinstance(d, dict):
            return "desks entry must be an object"
        if set(d) != _KEYS:
            return "desk keys must be exactly %s" % sorted(_KEYS)
        did = d["desk_id"]
        if not isinstance(did, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", did):
            return "desk_id invalid: %r" % (did,)
        if did in seen:
            return "desk_id duplicate: %s" % did
        seen.add(did)
        if d["kind"] not in ("rfq", "order"):
            return "kind must be rfq or order in %s" % did
        r = d["roots"]
        if not isinstance(r, list) or not r or not all(isinstance(x, str) and x for x in r):
            return "roots must be a non-empty list of non-empty strings in %s" % did
        dd = d["deal_depth"]
        if not (isinstance(dd, list) and len(dd) == 2 and all(_int(x) for x in dd) and 1 <= dd[0] <= dd[1]):
            return "deal_depth must be [min, max] with 1 <= min <= max in %s" % did
        if d["deal_name_rule"] != "date":
            return "deal_name_rule must be date in %s" % did
        if not _int(d["rep_min_depth"]) or d["rep_min_depth"] < 1:
            return "rep_min_depth must be an int >= 1 in %s" % did
        g = d["guard"]
        if not isinstance(g, dict) or set(g) != _GUARD_KEYS or not all(isinstance(v, bool) for v in g.values()):
            return "guard must hold booleans %s in %s" % (sorted(_GUARD_KEYS), did)
        if not isinstance(d["record_profile"], str):
            return "record_profile must be a string in %s" % did
    return None


def load(path=None):
    p = path or registry_path()
    name = os.path.basename(p)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return copy.deepcopy(FALLBACK), "%s not found (%s); using built-in fallback" % (name, p)
    except (OSError, UnicodeDecodeError) as e:
        return copy.deepcopy(FALLBACK), "%s unreadable (%s): %s; using built-in fallback" % (name, p, type(e).__name__)
    except RecursionError:
        return copy.deepcopy(FALLBACK), "%s invalid JSON (%s): nesting too deep; using built-in fallback" % (name, p)
    except ValueError as e:
        return copy.deepcopy(FALLBACK), "%s invalid JSON (%s): %s; using built-in fallback" % (name, p, str(e).splitlines()[0])
    err = _check(data)
    if err:
        return copy.deepcopy(FALLBACK), "%s schema error (%s): %s; using built-in fallback" % (name, p, err)
    return data["desks"], None


def _matches(path, desks):
    s = path.replace("\\", "/")
    out = []
    for d in desks:
        if d.get("kind") != "rfq":
            continue
        for root in d["roots"]:
            rx = re.compile(re.escape(root.replace("\\", "/")), re.I | re.A)
            for m in rx.finditer(s):
                out.append(Match(d, root, m.start(), m.end()))
    return out


def find(path, desks):
    ms = _matches(path, desks)
    if not ms:
        return None
    return min(ms, key=lambda m: (m.start, -(m.end - m.start)))


def find_all(path, desks):
    ms = sorted(_matches(path, desks), key=lambda m: (m.start, -(m.end - m.start)))
    out, pos = [], 0
    for m in ms:
        if m.start >= pos:
            out.append(m)
            pos = m.end
    return out
