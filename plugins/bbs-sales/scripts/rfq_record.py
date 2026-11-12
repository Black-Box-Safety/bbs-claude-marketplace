"""RFQ.md run-record model, v2.

Stdlib only. Shared by the skills, the hook and the scanner. The JSON sidecar
is derived from RFQ.md and regenerable; RFQ.md is the record.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

SCHEMA_VERSION = 2

STAGES = ["logged", "sourcing", "priced", "quote built", "packet built",
          "delivered to rep", "sent", "outcome"]
OUTCOMES = ["won", "lost", "no answer", "no bid", "cancelled"]
LINE_STAGES = ["open", "sourcing", "vendor quoted", "priced", "quoted",
               "substituted", "parked", "no bid"]
STRATEGIES = ["NASPO at cost", "BPO price list", "cost plus <n>%", "competitive bid",
              "vendor quote", "substitute offered", "parked", "no bid"]
STRATEGY_COST_PLUS_RE = r"^cost plus \d+(\.\d+)?%$"

HEADER_KEYS_V2 = ["Received", "Buyer", "Agency / institution", "Grainger account",
                  "BC customer", "Ship to", "Due", "Submit via", "Solicitation #",
                  "Vehicle", "Pricing rule", "Rep", "CRM RFQ", "BC quote",
                  "PC quote", "Stage"]

LINES_HEADER = "| # | Item / part # | Description | Qty | UOM | Lane |"
PRICING_HEADER = "| # | Vendor | Vendor ref | Cost | Sell | Strategy | Lead | Line stage | Evidence |"
STATUS_HEADER = "| Stage | Date | Evidence |"


@dataclass
class Line:
    num: int
    part: str
    description: str
    qty: str
    uom: str
    lane: str
    _src: str = field(default="", repr=False, compare=False)
    _sig: tuple = field(default=(), repr=False, compare=False)


@dataclass
class PricingRow:
    num: int
    vendor: str
    vendor_ref: str
    cost: Optional[float]
    sell: Optional[float]
    strategy: str
    lead: str
    line_stage: str
    evidence: str
    raw: dict = field(default_factory=dict)
    _src: str = field(default="", repr=False, compare=False)
    _sig: tuple = field(default=(), repr=False, compare=False)


@dataclass
class StatusRow:
    stage: str
    date: Optional[str]
    evidence: str
    _src: str = field(default="", repr=False, compare=False)
    _sig: tuple = field(default=(), repr=False, compare=False)


@dataclass
class Record:
    title: str
    header: "OrderedDict[str, str]"
    lines: list
    lines_note: str
    pricing: list
    status: list
    sections: "OrderedDict[str, str]"
    newline: str
    order: list = field(default_factory=list, repr=False, compare=False)
    layout: list = field(default_factory=list, repr=False, compare=False)
    chunks: dict = field(default_factory=dict, repr=False, compare=False)
    duplicates: list = field(default_factory=list, repr=False, compare=False)


class RecordError(Exception):
    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


_KEY_RE = re.compile(r"(\*\*([^*:\n]+):\*\*)([ \t]*)")
_SPLIT_RE = re.compile(r"(?<!\\)\|")
_NO_VALUE_RE = re.compile(r"^(\[FLAG:.*\]|\[MISSING.*\]|\[pending\])?$", re.I)


def _cells(line):
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip() for c in _SPLIT_RE.split(inner)]


def _money(cell):
    c = cell.strip()
    if _NO_VALUE_RE.match(c):
        return None
    try:
        return float(c.replace("$", "").replace(",", ""))
    except ValueError:
        return None


def _fmt_money(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return "$%s" % format(v, ",.2f")


def _parse_header_line(line):
    """Return list of tokens [(lead, key, ws, value, trail)] or None if not a key line."""
    ms = list(_KEY_RE.finditer(line))
    if not ms or line[:ms[0].start()].strip():
        return None
    toks = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(line)
        seg = line[m.end():end]
        body = seg.rstrip()
        trail = seg[len(body):]
        lead = line[:m.start()] if i == 0 else ""
        toks.append([lead, m.group(2), m.group(3), body, trail])
    # split on every **Key:** marker mid-line; text between markers is the value
    return toks


def _int(cell, what, problems):
    try:
        return int(cell)
    except ValueError:
        problems.append("%s: row number %r is not an integer" % (what, cell))
        return 0


def _table(chunk_lines, header, what, problems):
    """Split a section body into pre, header, sep, rows, post (all raw lines)."""
    body = chunk_lines[1:]
    hi = next((i for i, l in enumerate(body) if l.startswith("|")), None)
    if hi is None or body[hi].strip() != header:
        problems.append("%s table header missing or malformed; expected %s" % (what, header))
        return None
    if hi + 1 >= len(body) or not body[hi + 1].startswith("|"):
        problems.append("%s table separator row missing" % what)
        return None
    j = hi + 2
    while j < len(body) and body[j].startswith("|"):
        j += 1
    return {"heading": chunk_lines[0], "pre": body[:hi], "header": body[hi],
            "sep": body[hi + 1], "rows": body[hi + 2:j], "post": body[j:]}


def parse(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    problems = []
    ti = next((i for i, l in enumerate(lines) if l.strip()), None)
    if ti is None or not lines[ti].startswith("# "):
        problems.append("title (H1) missing")
        raise RecordError(problems)
    first = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    head_lines = lines[:first]
    title = lines[ti][2:]
    header = OrderedDict()
    layout = []
    for idx, l in enumerate(head_lines):
        if idx <= ti:
            layout.append(("raw", l))
            continue
        toks = _parse_header_line(l)
        if toks is None:
            layout.append(("raw", l))
        else:
            layout.append(("keys", toks))
            for t in toks:
                header[t[1]] = t[3]
    for k in HEADER_KEYS_V2:
        if k not in header:
            problems.append("header key missing: %s" % k)
    # sections
    starts = [i for i in range(first, len(lines)) if lines[i].startswith("## ")]
    order, chunks = [], {}
    sections = OrderedDict()
    out = {"lines": [], "pricing": [], "status": []}
    lines_note = ""
    duplicates = []
    seen_kinds = set()
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(lines)
        chunk = lines[s:e]
        h = chunk[0]
        kind = ("lines" if h.startswith("## Lines (") else "pricing" if re.match(r"## Pricing\s*$", h)
                else "status" if re.match(r"## Status\s*$", h) else None)
        if kind is None or kind in seen_kinds:
            if kind is None:
                key, n = h, 1
                while key in sections:
                    n += 1
                    key = "%s#%d" % (h, n)
            else:
                # duplicate table section: keep verbatim (round trip), validate() reports it
                duplicates.append(h)
                key = "%s#dup%d" % (h, len(duplicates))
            sections[key] = nl.join(chunk)
            order.append(("section", key))
            continue
        seen_kinds.add(kind)
        t = _table(chunk, {"lines": LINES_HEADER, "pricing": PRICING_HEADER,
                           "status": STATUS_HEADER}[kind], kind.title(), problems)
        order.append((kind, h))
        if t is None:
            continue
        chunks[kind] = t
        ncols = {"lines": 6, "pricing": 9, "status": 3}[kind]
        for r in t["rows"]:
            c = _cells(r)
            if len(c) != ncols:
                problems.append("%s row has %d cells, expected %d: %s" % (kind.title(), len(c), ncols, r))
                continue
            if kind == "lines":
                row = Line(_int(c[0], "Lines", problems), c[1], c[2], c[3], c[4], c[5])
                row._sig = (row.num, row.part, row.description, row.qty, row.uom, row.lane)
            elif kind == "pricing":
                row = PricingRow(_int(c[0], "Pricing", problems), c[1], c[2], _money(c[3]),
                                 _money(c[4]), c[5], c[6], c[7], c[8],
                                 raw={"Cost": c[3], "Sell": c[4]})
                row._sig = (row.num, row.vendor, row.vendor_ref, row.cost, row.sell,
                            row.strategy, row.lead, row.line_stage, row.evidence)
            else:
                row = StatusRow(c[0], c[1] or None, c[2])
                row._sig = (row.stage, row.date, row.evidence)
            row._src = r
            out[kind].append(row)
        if kind == "lines":
            lines_note = next((p for p in t["post"] if p.startswith("Source states")), "")
    for k, name in (("lines", "Lines"), ("pricing", "Pricing"), ("status", "Status")):
        if not any(o[0] == k for o in order):
            problems.append("%s section missing" % name)
    if problems:
        raise RecordError(problems)
    return Record(title=title, header=header, lines=out["lines"], lines_note=lines_note,
                  pricing=out["pricing"], status=out["status"], sections=sections,
                  newline=nl, order=order, layout=layout, chunks=chunks,
                  duplicates=duplicates)


_UNESC_PIPE_RE = re.compile(r"(?<!\\)\|")


def _esc_cell(c):
    c = re.sub(r"[\r\n]+", " ", c if isinstance(c, str) else str(c))
    return _UNESC_PIPE_RE.sub(r"\\|", c)


def _atomic_write(path, text, newline=""):
    import tempfile
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".rfq-tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _render_row(row):
    if isinstance(row, Line):
        sig = (row.num, row.part, row.description, row.qty, row.uom, row.lane)
        cols = [str(row.num), row.part, row.description, row.qty, row.uom, row.lane]
    elif isinstance(row, PricingRow):
        sig = (row.num, row.vendor, row.vendor_ref, row.cost, row.sell, row.strategy,
               row.lead, row.line_stage, row.evidence)
        cells = []
        for key, v in (("Cost", row.cost), ("Sell", row.sell)):
            raw = row.raw.get(key)
            if raw is not None and _money(raw) == v:
                cells.append(raw)
            else:
                cells.append("" if v is None else _fmt_money(v))
        cols = [str(row.num), row.vendor, row.vendor_ref, cells[0], cells[1],
                row.strategy, row.lead, row.line_stage, row.evidence]
    else:
        sig = (row.stage, row.date, row.evidence)
        cols = [row.stage, row.date or "", row.evidence]
    if row._src and row._sig == sig:
        return row._src
    cols = [_esc_cell(c) for c in cols]
    return "| " + " | ".join(cols) + " |"


def render(rec):
    nl = rec.newline
    out = []
    keys_used = set()
    for kind, item in rec.layout:
        if kind == "raw":
            out.append(item)
            continue
        parts = []
        for lead, key, ws, _old, trail in item:
            keys_used.add(key)
            parts.append("%s**%s:**%s%s%s" % (lead, key, ws, rec.header.get(key, ""), trail))
        out.append("".join(parts))
    extra = [k for k in HEADER_KEYS_V2 + list(rec.header) if k in rec.header and k not in keys_used]
    seen = set()
    at = len(out)
    while at > 0 and not out[at - 1].strip():
        at -= 1
    new = []
    for k in extra:
        if k not in seen:
            seen.add(k)
            new.append("**%s:** %s" % (k, rec.header[k]))
    out[at:at] = new
    rows = {"lines": rec.lines, "pricing": rec.pricing, "status": rec.status}
    for kind, name in rec.order:
        if kind == "section":
            out.append(rec.sections[name])
            continue
        t = rec.chunks[kind]
        post = list(t["post"])
        if kind == "lines" and rec.lines_note:
            for i, p in enumerate(post):
                if p.startswith("Source states"):
                    post[i] = rec.lines_note
        out.append(nl.join([t["heading"]] + t["pre"] + [t["header"], t["sep"]]
                           + [_render_row(r) for r in rows[kind]] + post))
    return nl.join(out)


# ---- validation, applicability, stage rules -------------------------------

class StageOrderError(Exception):
    pass


class StageConflictError(Exception):
    """A dated stage would get a different date without --correct."""


class StageNotApplicableError(Exception):
    pass


def vehicle_kind(rec):
    v = rec.header.get("Vehicle", "")
    if "NASPO" in v or "Provision Connect" in v:
        return "naspo"
    if "BPO" in v:
        return "bpo"
    return "competitive"


def applicable_stages(rec):
    kind = vehicle_kind(rec)
    if kind == "bpo":
        return ["logged", "priced", "quote built", "sent", "outcome"]
    out = list(STAGES)
    if kind == "naspo" and "- [" not in rec.sections.get("## Forms the buyer requires", ""):
        out.remove("packet built")
    if not any(l.lane == "sourcing" for l in rec.lines):
        out.remove("sourcing")
    return out


def _has_outcome_word(evidence):
    e = evidence.strip().lower()
    return any(e.startswith(w) for w in OUTCOMES)


def current_stage(rec):
    app = applicable_stages(rec)
    best = app[0]
    for row in rec.status:
        if row.stage not in app or not row.date:
            continue
        if row.stage == "outcome" and not _has_outcome_word(row.evidence):
            continue
        if STAGES.index(row.stage) >= STAGES.index(best):
            best = row.stage
    return best


def _strategy_ok(s):
    return s == "" or s in STRATEGIES or re.match(STRATEGY_COST_PLUS_RE, s) is not None


def validate(rec):
    probs = []
    for h in rec.duplicates:
        probs.append("duplicate section %r" % h)
    for r in rec.pricing:
        if not _strategy_ok(r.strategy):
            probs.append("Pricing row %d Strategy %r is not an allowed value" % (r.num, r.strategy))
        if r.line_stage and r.line_stage not in LINE_STAGES:
            probs.append("Pricing row %d Line stage %r is not an allowed value" % (r.num, r.line_stage))
    nums = [l.num for l in rec.lines]
    for r in rec.pricing:
        if r.num not in nums:
            probs.append("Pricing row %d has no matching Lines row" % r.num)
    for i, r in enumerate(rec.status, 1):
        if r.stage not in STAGES:
            probs.append("Status row %d Stage %r is not an allowed value" % (i, r.stage))
    st = rec.header.get("Stage", "")
    if st not in STAGES:
        probs.append("Header Stage %r is not an allowed value" % st)
    return probs


def set_header(rec, key, value):
    if key not in HEADER_KEYS_V2:
        raise KeyError(key)
    rec.header[key] = value


def upsert_pricing(rec, row):
    for i, r in enumerate(rec.pricing):
        if r.num == row.num:
            rec.pricing[i] = row
            return
    rec.pricing.append(row)


# Outcomes that may be recorded with no dated sent row: BBS decided not to quote, or the buyer
# withdrew the solicitation or made no award before a quote went out.
OUTCOMES_WITHOUT_SENT = ("no bid", "cancelled")


def _now_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def pacific_today():
    """Today's date in California. Falls back to UTC-7 (lenient by at most an hour) when the
    machine has no time zone data, as a Windows Python without tzdata can lack it."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    except Exception:
        from datetime import timedelta
        return (datetime.now(timezone.utc) - timedelta(hours=7)).strftime("%Y-%m-%d")


def _outcome_word(evidence):
    e = evidence.strip().lower()
    return next((w for w in OUTCOMES if e.startswith(w)), None)


def set_stage(rec, stage, date, evidence, force=False, by=None, correct=None, today=None):
    """Write one Status row. Write-time checks (dashboard-folder sync design, section 6.1):

    - same stage, same date: no change; new evidence is appended, never replaces the old;
    - same stage, different date: refused (StageConflictError) unless `correct` names the reason,
      and then the old date stays in the Evidence cell beside who corrected it and when;
    - outcome needs a dated sent row, except `no bid` and `cancelled`;
    - a sent date is not before Received and not after today in California;
    - a stage below the current one may only fill its own empty date, not after the date of any
      higher dated stage (a date fill); anything else backward needs `force`, which is recorded;
    - `force` and `correct` need `by`, the person the change is for.
    """
    if stage not in STAGES:
        raise ValueError("unknown stage %r" % stage)
    app = applicable_stages(rec)
    if stage not in app:
        raise StageNotApplicableError("%s does not apply to this %s record" % (stage, vehicle_kind(rec)))
    if stage == "outcome" and not _has_outcome_word(evidence):
        raise ValueError("outcome evidence must start with one of %s" % ", ".join(OUTCOMES))
    if (force or correct) and not (by or "").strip():
        raise ValueError("--force and --correct need --by <person>")
    today = today or pacific_today()
    if stage == "sent":
        received = parse_date(rec.header.get("Received", ""))
        if received and date < received:
            raise ValueError("sent date %s is before Received %s" % (date, received))
        if date > today:
            raise ValueError("sent date %s is after today (%s, California)" % (date, today))
    if stage == "outcome" and _outcome_word(evidence) not in OUTCOMES_WITHOUT_SENT:
        sent = next((r for r in rec.status if r.stage == "sent" and r.date), None)
        if sent is None:
            raise ValueError("outcome %r needs a dated sent row first (only %s may be recorded without one)"
                             % (_outcome_word(evidence), " and ".join(OUTCOMES_WITHOUT_SENT)))
    row = next((r for r in rec.status if r.stage == stage), None)
    stamp = _now_stamp()
    if row is not None and row.date:
        if row.date == date:
            if evidence and evidence not in row.evidence:
                row.evidence = (row.evidence + "; " + evidence) if row.evidence else evidence
            rec.header["Stage"] = current_stage(rec)
            return
        if not correct:
            raise StageConflictError("%s is already dated %s; a different date needs --correct \"<reason>\""
                                     % (stage, row.date))
        if STAGES.index(stage) < STAGES.index(current_stage(rec)) and not force:
            raise StageOrderError("%s is behind current stage %s" % (stage, current_stage(rec)))
        note = "corrected from %s to %s by %s %s: %s" % (row.date, date, by.strip(), stamp, correct.strip())
        row.date = date
        row.evidence = "; ".join(x for x in (row.evidence, evidence, note) if x)
        rec.header["Stage"] = current_stage(rec)
        return
    cur = current_stage(rec)
    if STAGES.index(stage) < STAGES.index(cur):
        higher = [r.date for r in rec.status
                  if r.date and r.stage in app and STAGES.index(r.stage) > STAGES.index(stage)]
        if higher and date <= min(higher):
            pass  # a date fill: the row is empty and the date does not pass any later stage
        elif not force:
            raise StageOrderError("%s is behind current stage %s" % (stage, cur))
        else:
            evidence = "%s [forced by %s %s from %s]" % (evidence, by.strip(), stamp, cur)
    if row is None:
        row = StatusRow(stage, date, evidence)
        rec.status.append(row)
    else:
        row.date, row.evidence = date, evidence
    for r in rec.status:
        if r.stage not in app and not r.date and not r.evidence:
            r.evidence = "n/a"
    rec.header["Stage"] = current_stage(rec)


# ---- dates, state sidecar --------------------------------------------------

_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")
_US_RE = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{4}|\d{2})(?!\d)")


def parse_date(text):
    t = (text or "").strip()
    m = _ISO_RE.match(t)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _US_RE.match(t)
        if not m:
            return None
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(3)) == 2:
            y += 2000
    try:
        return datetime(y, mo, d).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _flags(rec):
    body = None
    for k, v in rec.sections.items():
        if re.sub(r"#(dup)?\d+$", "", k).strip() == "## Flags":
            body = v
            break
    if body is None:
        return []
    return [l[2:].strip() for l in body.splitlines() if l.startswith("- ")]


def _line_dict(l):
    return {"num": l.num, "part": l.part, "description": l.description,
            "qty": l.qty, "uom": l.uom, "lane": l.lane}


def _pricing_dict(p):
    return {"num": p.num, "vendor": p.vendor, "vendor_ref": p.vendor_ref,
            "cost": p.cost, "sell": p.sell, "strategy": p.strategy, "lead": p.lead,
            "line_stage": p.line_stage, "evidence": p.evidence}


def to_state(rec, deal_path):
    stage = current_stage(rec)
    srow = next((r for r in rec.status if r.stage == stage), None)
    return {
        "schema_version": SCHEMA_VERSION,
        "deal_path": deal_path,
        "title": rec.title,
        "header": {k: rec.header.get(k) for k in HEADER_KEYS_V2},
        "vehicle_kind": vehicle_kind(rec),
        "stage": stage,
        "stage_date": srow.date if srow else None,
        "applicable_stages": applicable_stages(rec),
        "status": [{"stage": r.stage, "date": r.date, "evidence": r.evidence} for r in rec.status],
        "lines": [_line_dict(l) for l in rec.lines],
        "pricing": [_pricing_dict(p) for p in rec.pricing],
        "lines_total": len(rec.lines),
        "lines_priced": sum(1 for p in rec.pricing if p.line_stage in ("priced", "quoted")),
        "lines_open": sum(1 for p in rec.pricing if p.line_stage in ("open", "sourcing", "vendor quoted")),
        "flags": _flags(rec),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_state(rec, rfq_md_path, deal_path=""):
    out = os.path.join(os.path.dirname(os.path.abspath(rfq_md_path)), "rfq-state.json")
    text = json.dumps(to_state(rec, deal_path), indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    _atomic_write(out, text, "\n")
    return out


# ---- v1 -> v2 migration ----------------------------------------------------

V1_STATUS_MAP = {"logged": "logged", "priced": "priced", "packet built": "packet built",
                 "sent": "sent", "outcome": "outcome",
                 "sourcing": "sourcing", "vendor outreach": "sourcing",
                 "vendor cost": "sourcing", "vendor": "sourcing",
                 "quote built": "quote built", "quote pdf": "quote built",
                 "quote": "quote built", "bc": "quote built"}
V1_STATUS_HEADER = "| Stage | State | Date |"


def _status_section(text):
    """Body of the exact `## Status` section, or None."""
    m = re.search(r"^## Status[ \t]*\r?$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    n = re.search(r"^## ", rest, re.M)
    return rest[:n.start()] if n else rest


def is_legacy(text):
    """True when the text is not v2-shaped: no **Stage:** header line and no v2 Status table."""
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    if any("**Stage:**" in l for l in lines[:first]):
        return False
    sec = _status_section(text)
    return not (sec is not None and any(l.strip() == STATUS_HEADER for l in sec.splitlines()))


def is_v1(text):
    sec = _status_section(text)
    if sec is not None and any(l.strip() == V1_STATUS_HEADER for l in sec.splitlines()):
        return True
    return is_legacy(text)


def _find(L, pred, start=0):
    return next((i for i in range(start, len(L)) if pred(L[i])), None)


def _table_span(L, sec):
    """(header_idx, end_idx) of the first table in the section starting at sec."""
    nxt = _find(L, lambda l: l.startswith("## "), sec + 1)
    nxt = len(L) if nxt is None else nxt
    hi = _find(L, lambda l: l.startswith("|"), sec + 1)
    if hi is None or hi >= nxt:
        return None, nxt
    j = hi
    while j < len(L) and L[j].startswith("|"):
        j += 1
    return (hi, j), nxt


_LINES_ALIAS_RE = re.compile(r"^## Lines?(?: items?)?(?: requested)?(?=[\s(\u2014\u2013:-]|$)")
_SEP_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")
_ITEM_DIRECT = ("item / part #", "buyer item #", "item #")
_GRAINGER_COLS = ("grainger #", "grainger item", "grainger item #")
_MFR_COLS = ("model #", "mfr part", "mfr pn", "mfg part", "mfg pn", "mpn", "part #")
_PLAIN_NAMES = ("#", "item / part #", "description", "qty", "uom", "lane")


def _role(h):
    h = h.strip().lower()
    if h in ("#", "line", "ln", "line #"):
        return "num"
    if h in _ITEM_DIRECT or h.startswith("item #"):
        return "item"
    if h in _GRAINGER_COLS:
        return "gr"
    if h in _MFR_COLS:
        return "mfr"
    if re.match(r"^(rfq )?description\b", h):
        return "desc"
    if h in ("qty", "quantity"):
        return "qty"
    if h in ("uom", "unit", "unit of measure", "units"):
        return "uom"
    if h.startswith("lane"):
        return "lane"
    return None


def _normalize_lines(L, notes):
    """Rewrite the Lines section in place to the canonical heading and table.

    Returns (heading index or None, [(row number, lane)]). Raises RecordError when
    there is no Lines table at all. Anything that does not map to a canonical column
    is kept verbatim, with the original heading and table, in ## Original Lines table.
    """
    ls = _find(L, lambda l: l.startswith("## Lines ("))
    alias = False
    if ls is None:
        ls = _find(L, lambda l: _LINES_ALIAS_RE.match(l))
        alias = ls is not None
    if ls is None:
        raise RecordError(["no Lines table"])
    span, nxt = _table_span(L, ls)
    if not span:
        raise RecordError(["no Lines table"])
    hi, end = span
    hc = _cells(L[hi])
    canon = _cells(LINES_HEADER)
    seq = hi + 1 < end and _SEP_RE.match(L[hi + 1])
    rows_raw = L[hi + 2:end] if seq else []
    ints = all(re.fullmatch(r"\d+", c[0]) for c in map(_cells, rows_raw) if c)
    if not alias and hc == canon and ints:
        return ls, _lane_pairs(rows_raw)
    cells = [_cells(r) for r in rows_raw]
    _MONEY = re.compile(r"\$|\d,\d{3}|\d\.\d{2}\b")

    def _col_ok(r, i, h):
        if any(len(c) != len(hc) for c in cells):
            return True
        col = [c[i] for c in cells]
        if r == "num":
            return all(re.fullmatch(r"\d+|S\d+", v, re.I) for v in col)
        if r == "uom" and h.strip().lower() == "unit":
            return not any(_MONEY.search(v) for v in col)
        return True

    roles = {}
    for i, h in enumerate(hc):
        r = _role(h)
        if r and r not in roles and _col_ok(r, i, h):
            roles[r] = i
    recognised = ("desc" in roles or "item" in roles or "gr" in roles or "mfr" in roles)
    if not seq or not recognised or any(len(c) != len(hc) for c in cells):
        if alias:
            raise RecordError(["no Lines table"])
        return ls, _lane_pairs(rows_raw)
    flag = lambda what: "[FLAG: %s not in the v1 table]" % what
    used = set()
    for k in ("num", "desc", "qty", "uom", "lane"):
        if k in roles:
            used.add(roles[k])
    if "item" in roles:
        used.add(roles["item"])
    else:
        used.update(roles[k] for k in ("gr", "mfr") if k in roles)
    extras = [hc[i] for i in range(len(hc)) if i not in used]
    nums, relabeled = [], False
    if "num" in roles and all(re.fullmatch(r"\d+", c[roles["num"]]) for c in cells):
        nums = [int(c[roles["num"]]) for c in cells]
    else:
        nums = list(range(1, len(cells) + 1))
        relabeled = True
    out, pairs = [], []
    for n, c in zip(nums, cells):
        get = lambda k: c[roles[k]] if k in roles else None
        if "item" in roles:
            part = get("item")
        elif "gr" in roles or "mfr" in roles:
            g, m = get("gr") or "", get("mfr") or ""
            part = "%s (mfr %s)" % (g, m) if g and m else (g or m)
        else:
            part = flag("item / part #")
        desc = get("desc") if "desc" in roles else flag("description")
        qty = get("qty") if "qty" in roles else flag("Qty")
        uom = get("uom") if "uom" in roles else flag("UOM")
        lane = get("lane") if "lane" in roles else flag("Lane")
        out.append("| %d | %s | %s | %s | %s | %s |" % (n, part, desc, qty, uom, lane))
        pairs.append((n, lane))
    if "item" not in roles and "gr" in roles and "mfr" in roles:
        notes.append("Lines: merged %s and %s into Item / part # as '<Grainger #> (mfr <Model #>)'"
                     % (hc[roles["mfr"]], hc[roles["gr"]]))
    elif "item" not in roles and ("gr" in roles or "mfr" in roles):
        notes.append("Lines: column %r used as Item / part #" % hc[roles.get("gr", roles.get("mfr"))])
    for k, name in (("item", "Item / part #"), ("desc", "Description"), ("qty", "Qty"),
                    ("uom", "UOM"), ("lane", "Lane"), ("num", "#")):
        if k in roles and hc[roles[k]].lower() != name.lower():
            notes.append("Lines: column %r mapped to %s" % (hc[roles[k]], name))
    for k, name in (("uom", "UOM"), ("lane", "Lane"), ("qty", "Qty"), ("desc", "Description")):
        if k not in roles:
            notes.append("Lines: no %s column in the v1 table; every row marked [FLAG]" % name)
    if "item" not in roles and "gr" not in roles and "mfr" not in roles:
        notes.append("Lines: no item / part # column in the v1 table; every row marked [FLAG]")
    if relabeled:
        notes.append("Lines: row numbers %s; assigned 1..%d in order, original labels kept in ## Original Lines table"
                     % ("missing or not integer labels" if "num" not in roles else "not all integers", len(cells)))
    if extras:
        notes.append("Lines: columns not in the v2 table kept in ## Original Lines table: %s" % ", ".join(extras))
    heading = L[ls]
    new_heading = heading
    if alias or "(" not in heading:
        new_heading = "## Lines (%d item%s)" % (len(out), "" if len(out) == 1 else "s")
        notes.append("Lines heading %r rewritten as %r" % (heading, new_heading))
    orig_table = L[hi:end]
    lossless = (not extras and not relabeled and new_heading == heading
                and all(h.lower() in _PLAIN_NAMES for h in hc))
    L[hi:end] = [LINES_HEADER, "|---|---|---|---|---|---|"] + out
    L[ls] = new_heading
    if not lossless:
        _, nxt = _table_span(L, ls)
        block = ["## Original Lines table", ""]
        if new_heading != heading:
            block += ["Original heading: %s" % heading, ""]
        block += orig_table + [""]
        if nxt > 0 and L[nxt - 1].strip():
            block.insert(0, "")
        L[nxt:nxt] = block
        notes.append("Original Lines table kept verbatim in ## Original Lines table")
    return ls, pairs


def _lane_pairs(rows):
    pairs = []
    for r in rows:
        c = _cells(r)
        if len(c) == 6:
            try:
                pairs.append((int(c[0]), c[5]))
            except ValueError:
                pass
    return pairs


def _park_original_pricing(L, notes):
    """Rename a Pricing section that is not the canonical table, so no text is lost
    and the parser sees only the canonical ## Pricing."""
    for i, l in enumerate(L):
        if not l.startswith("## Pricing"):
            continue
        span, _ = _table_span(L, i)
        exact = l.strip() == "## Pricing"
        if exact and span and L[span[0]].strip() == PRICING_HEADER:
            continue
        if exact or span:
            L[i] = "## Original Pricing" + l[len("## Pricing"):]
            notes.append("Pricing section %r is not the v2 table; kept verbatim as %r" % (l, L[i]))


def migrate_v1(text, rep=None):
    nl = "\r\n" if "\r\n" in text else "\n"
    L = text.split(nl)
    notes = []
    # --- status (bottom of file first so earlier indexes stay valid) ---
    srows, extra = {}, []
    st = _find(L, lambda l: re.match(r"## Status\s*$", l))
    if st is not None:
        span, _ = _table_span(L, st)
        if span:
            hi, end = span
            hc = [c.lower() for c in _cells(L[hi])]
            ci = {"stage": hc.index("stage") if "stage" in hc else 0,
                  "state": hc.index("state") if "state" in hc else (hc.index("evidence") if "evidence" in hc else 1),
                  "date": hc.index("date") if "date" in hc else 2}
            for r in L[hi + 2:end]:
                c = _cells(r)
                if len(c) < 3:
                    c += [""] * (3 - len(c))
                name, state, date = c[ci["stage"]], c[ci["state"]], c[ci["date"]]
                tgt = V1_STATUS_MAP.get(name.strip().lower())
                if tgt is None:
                    extra.append("- %s: %s %s" % (name, state, date))
                    notes.append("Status row %r has no v2 stage; kept verbatim in ## Status notes" % name)
                    continue
                if tgt in srows:
                    extra.append("- %s: %s %s" % (name, state, date))
                    notes.append("Status row %r maps to %r which an earlier row already filled; kept verbatim in ## Status notes" % (name, tgt))
                    continue
                if name.strip().lower() != tgt:
                    notes.append("Status row %r mapped to stage %r" % (name, tgt))
                nd = parse_date(date)
                ev = state
                if state.strip() and date.strip() and nd is None:
                    ev = "%s [FLAG: date unparsed: %s]" % (state, date)
                    notes.append("Status row %r: date %r not parseable; Date left empty, flagged in Evidence" % (name, date))
                srows[tgt] = (nd, ev)
            new = [STATUS_HEADER, "|---|---|---|"]
            for g in STAGES:
                d, e = srows.get(g, (None, ""))
                new.append("| %s | %s | %s |" % (g, d or "", e))
            L[hi:end] = new
    if st is not None and not _table_span(L, st)[0]:
        # an exact `## Status` with no table (checklist or prose): keep it under a new name
        L[st] = "## Original Status"
        notes.append("Status section had no table; kept verbatim as ## Original Status and added the v2 table")
        st = None
    if st is None:
        recv = ""
        for l in L:
            if l.startswith("## "):
                break
            m = re.search(r"\*\*Received:\*\*[ \t]*(.*?)\s*(?:\*\*|$)", l)
            if m:
                recv = m.group(1)
                break
        rd = parse_date(recv)
        if rd:
            logged = "| logged | %s | from **Received:** header; v1 had no Status table |" % rd
            notes.append("No Status table; added the v2 one with logged dated %s from **Received:**" % rd)
        else:
            logged = "| logged |  | [FLAG: v1 had no Status table and **Received:** has no parseable date] |"
            notes.append("No Status table; added the v2 one, logged left empty and flagged (Received not parseable)")
        L += ["", "## Status", ""] + [STATUS_HEADER, "|---|---|---|", logged] + \
             ["| %s |  |  |" % g for g in STAGES[1:]] + [""]
    if extra:
        while L and L[-1] == "":
            L.pop()
        L += ["", "## Status notes", ""] + extra + [""]
    # --- lines ---
    ls, lines = _normalize_lines(L, notes)
    # --- header ---
    first = _find(L, lambda l: l.startswith("## "))
    first = len(L) if first is None else first
    present = set()
    for l in L[:first]:
        for m in _KEY_RE.finditer(l):
            present.add(m.group(2))
    add = []
    for k in HEADER_KEYS_V2:
        if k in present:
            continue
        v = rep if (k == "Rep" and rep) else "[not recorded]"
        add.append("**%s:** %s" % (k, v))
        notes.append("Header key %s added as %s" % (k, v))
    at = first
    while at > 0 and not L[at - 1].strip():
        at -= 1
    L[at:at] = add
    first += len(add)
    veh = ""
    for l in L[:first]:
        m = re.search(r"\*\*Vehicle:\*\*[ \t]*(.*?)\s*(?:\*\*|$)", l)
        if m:
            veh = m.group(1)
    naspo = "NASPO" in veh or "Provision Connect" in veh
    # --- pricing ---
    _park_original_pricing(L, notes)
    if not any(re.match(r"## Pricing\s*$", l) for l in L) and lines and ls is not None:
        ls2 = _find(L, lambda l: l.startswith("## Lines ("))
        nxt = _find(L, lambda l: l.startswith("## "), ls2 + 1)
        nxt = len(L) if nxt is None else nxt
        P = ["## Pricing", "", PRICING_HEADER, "|---|---|---|---|---|---|---|---|---|"]
        for n, lane in lines:
            ven = "Grainger" if lane == "grainger" else "[sourcing]" if lane == "sourcing" else ""
            P.append("| %d | %s |  |  |  | %s |  | open |  |" % (n, ven, "NASPO at cost" if naspo else ""))
        if nxt > 0 and L[nxt - 1].strip():
            P.insert(0, "")
        L[nxt:nxt] = P + [""]
        notes.append("Added an empty ## Pricing table with one open row per line")
    rec = parse(nl.join(L))
    app = applicable_stages(rec)
    for r in rec.status:
        if r.stage not in app and not r.date and not r.evidence:
            r.evidence = "n/a"
        elif r.stage not in app:
            notes.append("Stage %r does not apply to this record but v1 had data for it; kept" % r.stage)
    rec.header["Stage"] = current_stage(rec)
    return rec, notes


# ---- command line ----------------------------------------------------------

class _CliError(Exception):
    pass


def _read(path):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return f.read()
    except OSError as e:
        raise _CliError("cannot read %s: %s" % (path, e.strerror or e))


def _deal_path(path):
    p = os.path.abspath(path)
    return p if "All RFQ's by Agency/" in p.replace(os.sep, "/") else ""


# A OneDrive conflict copy of RFQ.md is named RFQ-<machine>.md; a machine name starts with a letter.
CONFLICT_COPY = re.compile(r"^RFQ-(?![0-9]).+\.md$", re.I)


def conflict_copies(path):
    d = os.path.dirname(os.path.abspath(path))
    try:
        return sorted(f for f in os.listdir(d) if CONFLICT_COPY.match(f))
    except OSError:
        return []


def _save(rec, path):
    """Re-validate, write the record, then the sidecar. Returns the sidecar path."""
    copies = conflict_copies(path)
    if copies:
        raise _CliError("refusing to write while a OneDrive conflict copy of RFQ.md exists (%s); "
                        "merge it into RFQ.md by hand and delete it, then run this again" % ", ".join(copies))
    probs = validate(rec)
    if probs:
        raise _CliError("refusing to write, record would be invalid: " + "; ".join(probs))
    text = render(rec)
    try:
        again = parse(text)
    except RecordError as e:
        raise _CliError("refusing to write, rendered record does not re-parse: " + "; ".join(e.problems))
    probs = validate(again)
    if probs:
        raise _CliError("refusing to write, rendered record is invalid: " + "; ".join(probs))
    _atomic_write(path, text)
    return write_state(rec, path, _deal_path(path))


def _load_v2(path):
    text = _read(path)
    if is_v1(text):
        raise _CliError("%s is a v1 record; run migrate first" % path)
    try:
        return parse(text)
    except RecordError as e:
        raise _CliError("; ".join(e.problems))


def _build_parser():
    ap = argparse.ArgumentParser(prog="rfq_record.py", description="RFQ.md v2 record tool")
    sub = ap.add_subparsers(dest="cmd")
    sub.required = True
    for name in ("validate", "compile", "current-stage"):
        sp = sub.add_parser(name)
        sp.add_argument("rfq")
        if name == "compile":
            sp.add_argument("-o", dest="out")
    sp = sub.add_parser("set-stage")
    sp.add_argument("rfq")
    sp.add_argument("stage")
    sp.add_argument("--date", required=True)
    sp.add_argument("--evidence", required=True)
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--by", help="the person this change is for; required with --force or --correct")
    sp.add_argument("--correct", metavar="REASON", help="change an already-dated stage, keeping the old date in Evidence")
    sp = sub.add_parser("set-header")
    sp.add_argument("rfq")
    sp.add_argument("key")
    sp.add_argument("value")
    sp = sub.add_parser("upsert-pricing")
    sp.add_argument("rfq")
    sp.add_argument("--json", required=True, dest="row")
    sp = sub.add_parser("migrate")
    sp.add_argument("rfq")
    sp.add_argument("--rep")
    sp.add_argument("--dry-run", action="store_true")
    return ap


def _run(a):
    if a.cmd == "validate":
        text = _read(a.rfq)
        if is_v1(text):
            print("v1 record: migrate before validating", file=sys.stderr)
            return 2
        try:
            probs = validate(parse(text))
        except RecordError as e:
            probs = e.problems
        for p in probs:
            print(p, file=sys.stderr)
        return 2 if probs else 0
    if a.cmd == "current-stage":
        print(current_stage(_load_v2(a.rfq)))
        return 0
    if a.cmd == "compile":
        rec = _load_v2(a.rfq)
        out = write_state(rec, a.rfq, _deal_path(a.rfq))
        if a.out:
            os.replace(out, a.out)
            out = a.out
        print(out)
        return 0
    if a.cmd == "set-stage":
        rec = _load_v2(a.rfq)
        d = parse_date(a.date)
        if d is None:
            raise _CliError("bad date %r (use YYYY-MM-DD)" % a.date)
        try:
            set_stage(rec, a.stage, d, a.evidence, force=a.force, by=a.by, correct=a.correct)
        except StageOrderError as e:
            raise _CliError("backward stage move refused: %s (use --force --by <person> to override)" % e)
        except StageConflictError as e:
            raise _CliError("conflict: %s" % e)
        except (StageNotApplicableError, ValueError) as e:
            raise _CliError(str(e))
        _save(rec, a.rfq)
        return 0
    if a.cmd == "set-header":
        rec = _load_v2(a.rfq)
        try:
            set_header(rec, a.key, re.sub(r"[\r\n]+", " ", a.value).strip())
        except KeyError:
            raise _CliError("unknown header key %r" % a.key)
        _save(rec, a.rfq)
        return 0
    if a.cmd == "upsert-pricing":
        rec = _load_v2(a.rfq)
        try:
            d = json.loads(a.row)
            raw = {}
            money = {}
            for k, key in (("cost", "Cost"), ("sell", "Sell")):
                v = d.get(k)
                if isinstance(v, bool) or not (v is None or isinstance(v, (int, float, str))):
                    raise ValueError("%s must be a number or a [FLAG...] string" % k)
                if isinstance(v, str):
                    if v.startswith("[FLAG") or v.startswith("[MISSING"):
                        raw[key] = v
                        v = None
                    else:
                        try:
                            v = float(v.replace("$", "").replace(",", ""))
                        except ValueError:
                            raise ValueError("%s %r is not a number or a [FLAG...] string" % (k, v))
                money[k] = v
            row = PricingRow(
                num=int(d["num"]), vendor=d.get("vendor", ""), vendor_ref=d.get("vendor_ref", ""),
                cost=money["cost"], sell=money["sell"], raw=raw, strategy=d.get("strategy", ""),
                lead=d.get("lead", ""), line_stage=d.get("line_stage", ""), evidence=d.get("evidence", ""))
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise _CliError("bad --json row: %s" % e)
        upsert_pricing(rec, row)
        _save(rec, a.rfq)
        return 0
    if a.cmd == "migrate":
        text = _read(a.rfq)
        if not is_v1(text):
            raise _CliError("%s is already a v2 record" % a.rfq)
        try:
            rec, notes = migrate_v1(text, rep=a.rep)
        except RecordError as e:
            if a.dry_run:
                print("would not convert:")
                for q in e.problems:
                    print(q)
                return 2
            raise
        if a.dry_run:
            try:
                probs = validate(parse(render(rec)))
            except RecordError as e:
                probs = list(e.problems)
            if probs:
                for q in probs:
                    print(q)
                return 2
            for n in notes:
                print(n)
            print("would convert cleanly")
            return 0
        for n in notes:
            print(n)
        _save(rec, a.rfq)
        return 0
    raise _CliError("unknown command")


def main(argv=None):
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as e:
        return 1 if e.code else 0
    try:
        return _run(args)
    except _CliError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:  # any other failure: one line, exit 1
        print("%s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
