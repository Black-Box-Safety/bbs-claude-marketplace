#!/usr/bin/env python3
"""brand_check - the blocking pre-render gate for BBS marketing pieces.

Reads references/CLAIMS.md and audits a piece for superseded wording, expired
claims, and missing required claims. Exits non-zero on any finding so it can
block a build.
"""
from __future__ import annotations

import datetime as dt
import html
import re
from dataclasses import dataclass, field

REGISTRY_HEADING = "## Registry"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
# Non-breaking spaces an HTML author types as &nbsp;/&#160; and friends. They
# survive entity decoding as literal characters, so fold them to a plain space
# before collapsing runs of whitespace.
_HARD_SPACE = re.compile("[\u00a0\u2007\u202f]")


@dataclass
class Claim:
    id: str
    approved: str
    superseded: list[str] = field(default_factory=list)
    presence: str = "as-used"
    scope: str = "all"
    expires: dt.date | None = None


def _is_separator(cells: list[str]) -> bool:
    return all(set(c) <= set("-: ") and c for c in cells)


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_claims(text: str) -> list[Claim]:
    """Parse the markdown table under the '## Registry' heading."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == REGISTRY_HEADING:
            start = i
            break
    if start is None:
        raise ValueError(f"CLAIMS.md is missing a '{REGISTRY_HEADING}' heading")

    rows: list[list[str]] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = _split_row(stripped)
        if _is_separator(cells):
            continue
        rows.append(cells)

    if not rows:
        raise ValueError("CLAIMS.md registry table is empty")

    header = [c.lower() for c in rows[0]]
    index = {name: header.index(name) for name in header}

    def cell(row: list[str], name: str, default: str = "") -> str:
        pos = index.get(name)
        if pos is None or pos >= len(row):
            return default
        return row[pos]

    claims: list[Claim] = []
    for row in rows[1:]:
        raw_superseded = cell(row, "superseded wording")
        superseded = [s.strip() for s in raw_superseded.split(";") if s.strip()]
        raw_expires = cell(row, "expires")
        expires = dt.date.fromisoformat(raw_expires) if raw_expires else None
        claims.append(
            Claim(
                id=cell(row, "id"),
                approved=cell(row, "approved wording"),
                superseded=superseded,
                presence=cell(row, "presence", "as-used") or "as-used",
                scope=cell(row, "scope", "all") or "all",
                expires=expires,
            )
        )
    return claims


@dataclass
class Finding:
    claim_id: str
    kind: str
    detail: str


def normalize(raw: str, strip_tags: bool = True) -> str:
    """Collapse markup and whitespace so wording matches across HTML tags.

    Entities are decoded first: the CLI audits rendered HTML, where
    'Cert.&nbsp;2009473' is the same claim as 'Cert. 2009473'.
    """
    text = html.unescape(raw)
    text = _HARD_SPACE.sub(" ", text)
    text = _TAG.sub(" ", text) if strip_tags else text
    return _WS.sub(" ", text).strip()


def _in_scope(claim: Claim, scopes: list[str]) -> bool:
    """A claim scoped 'all' always applies. A narrower claim applies only when
    its tags intersect the caller's scopes.

    Note the asymmetry: passing --scope all means "no specific track", NOT
    "every scope". Otherwise a generic audit would demand the agency
    disclaimer on every piece.
    """
    if claim.scope == "all":
        return True
    return bool(set(claim.scope.split()) & set(scopes))


def _longest_matches(wordings: list[str], present) -> list[str]:
    """Matched wordings with the redundant ones dropped.

    Superseded variants on one row often nest — 'headquartered in San Diego'
    is a prefix of 'headquartered in San Diego, CA' — and one offending
    sentence should be one defect, not two. Keep a match only when no other
    match strictly contains it, so the longest variant is what gets reported.
    Registry order is preserved.
    """
    matched: list[tuple[str, str]] = []
    seen: set[str] = set()
    for wording in wordings:
        if not present(wording):
            continue
        key = normalize(wording).casefold()
        if key in seen:
            continue
        seen.add(key)
        matched.append((wording, key))

    return [
        wording
        for wording, key in matched
        if not any(other != key and key in other for other in seen)
    ]


def audit(
    piece: str,
    claims: list[Claim],
    scopes: list[str],
    today: dt.date | None = None,
) -> list[Finding]:
    """Return every finding for a piece. Empty list means the gate passes."""
    today = today or dt.date.today()
    text = normalize(piece)
    haystack = text.casefold()
    findings: list[Finding] = []

    def present(wording: str) -> bool:
        """Case-insensitive containment. Wording is matched as printed, in any
        case, so a capitalized headline cannot slip past the gate.

        Empty wording is never present: '' in text is always True, which would
        make the gate fail open on a blank registry cell.
        """
        needle = normalize(wording)
        if not needle:
            return False
        return needle.casefold() in haystack

    for claim in claims:
        if not _in_scope(claim, scopes):
            continue

        for bad in _longest_matches(claim.superseded, present):
            findings.append(
                Finding(
                    claim_id=claim.id,
                    kind="superseded",
                    detail=(
                        f"found {bad!r}; approved wording is "
                        f"{claim.approved or 'NEEDS CLAIM'}"
                    ),
                )
            )

        approved_present = present(claim.approved)
        if claim.expires and claim.expires < today and approved_present:
            findings.append(
                Finding(
                    claim_id=claim.id,
                    kind="expired",
                    detail=(
                        f"claim expired {claim.expires.isoformat()}; "
                        "re-verify before publishing"
                    ),
                )
            )

        if claim.presence == "required" and not normalize(claim.approved):
            findings.append(
                Finding(
                    claim_id=claim.id,
                    kind="malformed",
                    detail=(
                        "registry row is malformed: presence 'required' with "
                        "no approved wording, so the claim can never be "
                        "checked; fix the row in references/CLAIMS.md"
                    ),
                )
            )
        elif claim.presence == "required" and not approved_present:
            findings.append(
                Finding(
                    claim_id=claim.id,
                    kind="missing",
                    detail=(
                        f"required wording absent for scope {claim.scope!r}: "
                        f"{claim.approved!r}"
                    ),
                )
            )

    # Channel is not a scope tag. Scope stays "all" so a superseded rendering
    # still fails on every piece. What scope cannot express is co-occurrence:
    # the California credential and a federal credential on the same piece.
    california = next(
        (c for c in claims if c.id == "dvbe-cert" and present(c.approved)),
        None,
    )
    federal = next(
        (
            c
            for c in claims
            if c.id in {"sdvosb", "sdvosb-full", "vosb"} and present(c.approved)
            ),
        None,
    )
    if california and federal:
        findings.append(
            Finding(
                claim_id="channel",
                kind="mixed-channel",
                detail=(
                    f"piece carries {california.approved!r} and "
                    f"{federal.approved!r}; a piece carries one channel"
                ),
            )
        )

    return findings


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Audit a marketing piece against the claims registry."
    )
    parser.add_argument("piece", help="path to the rendered piece or content file")
    parser.add_argument(
        "--claims",
        default=str(Path(__file__).resolve().parents[1] / "references" / "CLAIMS.md"),
        help="path to CLAIMS.md",
    )
    parser.add_argument(
        "--scope",
        action="append",
        default=None,
        help="scope tag; repeatable (e.g. --scope mro --scope agency)",
    )
    args = parser.parse_args(argv)

    claims = parse_claims(Path(args.claims).read_text(encoding="utf-8"))
    piece = Path(args.piece).read_text(encoding="utf-8", errors="replace")
    scopes = args.scope or ["all"]

    findings = audit(piece, claims, scopes=scopes)

    if not findings:
        print(f"brand-check PASS  {args.piece}")
        return 0

    print(f"brand-check FAIL  {args.piece}  ({len(findings)} finding(s))")
    for f in findings:
        print(f"  [{f.kind}] {f.claim_id}: {f.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
