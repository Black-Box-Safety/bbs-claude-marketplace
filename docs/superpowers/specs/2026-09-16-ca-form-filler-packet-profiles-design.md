# ca-form-filler packet profiles — design

**Date:** 2026-09-16 · **Slice:** `docs/STEWARD.md` §3 · **Status:** implemented on
`claude/slice-3-packet-profiles`

---

## Problem

`ca-form-filler` Path A is one hard-coded packet. "Is this the CDCR OBS 4007(B)?" is a
judgement the model makes from prose in `SKILL.md`, and the packet's page map lives in a
single sibling file named after that one packet. A second packet — DSH sends its own —
has nowhere to go inside the skill.

The tempting alternative is a sibling skill per packet. `AGENTS.md` rules that out, and
the reason is the whole point of this slice:

> Siblings compete on descriptions, which is probabilistic and can silently pick wrong.
> Profiles route on document content, which is deterministic.

A sibling skill picked wrong produces a filled packet against the wrong map. On a binding
bid that is the exact failure this repo exists to prevent.

## What a profile is

A file under `references/packets/<packet_id>.md` describing **one specific PDF**: how to
recognise it, what its pages hold, which field IDs are irregular, and which script fills
it. YAML front matter is the machine-readable part; the body is the human page map.

A profile owns what belongs to a PDF. It must **not** own what belongs to the forms:

| Belongs in the profile | Belongs in `${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md` |
|---|---|
| AcroForm field IDs, page numbers, annotation coordinates | Who signs which line |
| Recognition markers and their provenance | What the State fills and must stay blank |
| Which script fills the packet, which pages to verify | Which certification language applies |

That split is `AGENTS.md` invariant 2 applied to this skill: an ID belongs to one PDF, a
rule belongs to every skill that fills the form. A profile that restates a signing rule
is a second copy that will go stale.

## Front-matter contract

```yaml
packet_id: obs-4007b          # required; must equal the filename stem
title: ...                    # required; human name of the packet
revision: "Rev. 08/2025"      # required; the revision the map was built against
status: active | stub         # required; only `active` is eligible to match
recognize:                    # required
  all:  ["..."]               # every marker must be present in the PDF text
  any:  ["..."]               # optional; at least one must be present
  none: ["..."]               # optional; none may be present
recognition_source: ...       # required; where the markers were read from
extends: <packet_id>          # optional; declares this a specialisation
fill:                         # required
  mode: scripted | path-b
  script: ...                 # required when mode is scripted, relative to the skill dir
  inputs_template: ...        # optional
  verify_script: ...          # optional
  verify_pages: [...]         # optional
rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md   # required, and this value
```

`status: stub` is the honest state for a packet BBS knows it receives but has no verified
map for. A stub is **inert**: it is validated, listed and never matched, so a stub can
never route a real PDF into an unverified fill.

## How recognition resolves

Deterministic, on text extracted from the PDF itself — never on a filename, never on a
description:

1. `pdftotext <packet>.pdf -` gives the text.
2. Each `active` profile is evaluated: every `all` marker present, at least one `any`
   marker present if `any` is non-empty, no `none` marker present. Matching is
   case-insensitive on whitespace-collapsed text, because a PDF text layer breaks lines
   wherever the layout did.
3. **Exactly one match** → that profile.
4. **Several matches** → the one whose `all` set is a strict superset of every other
   match's wins. A general packet and its site-specific specialisation resolve this way
   and only this way. If no match subsumes all the others, the resolver **refuses** and
   names the candidates. It does not score, rank or guess.
5. **No match** → Path B, the general map-and-fill path. This is the safe default and the
   behaviour every non-OBS PDF gets today.

### Recognition is not the safety boundary

A mis-recognition cannot silently produce a wrong packet, because the fill script
validates every field ID, its type and its page against the PDF in hand and refuses to
write when any of them is unknown. Recognition picks a candidate; the field-ID validation
is what authorises the write. Both must agree or nothing is produced.

### Markers must be grounded

Every marker is a string someone read out of the actual PDF or out of a repo file that
recorded it from the PDF, and `recognition_source` says which. Invented markers are the
one way this design could fail quietly — a plausible-looking marker that happens to match
the wrong document. `AGENTS.md` invariant 1 covers this: unknown is `[MISSING — NEEDS
INPUT]`, never a plausible value. A profile with no grounded markers is a `stub`.

## Adding a profile

Drop a conforming file in `references/packets/`. Nothing else. `SKILL.md` names no
profile and no packet-specific fact, the resolver globs the directory, and the validator
checks the new file against the contract. `scripts/test_packet_profiles.py` demonstrates
this against a third profile written at test time.

## Out of scope, and deliberately unchanged

- **`fill_obs_packet.py`'s field values.** The migration moves documentation, not fill
  logic. In particular the OBS 4007(B) Small Business checkbox stays `/Off` at
  `scripts/fill_obs_packet.py:138`, byte for byte — it is an open certification question
  for Parker, not a defect to fix in a refactor.
- **DGS PD 843 "Name of DVBE".** Path A writes `short_name`; `references/field-maps.md`
  says `legal_name`. Recorded as an open conflict in both places and left that way.
  *(Later: ruled by Parker 2026-09-18 and confirmed 2026-09-28, "do legal name". Both
  paths now write `business_identity.legal_name`; `ca-form-rules.md` is the home.)*
- `vendor_profile.json`, `ca-form-rules.md`, `scripts/check_marketplace.py`, skill
  `description:` fields.

## What this design does not verify

No real CA form PDF is available in this repo or to the session that wrote this. The
contract, the resolver and the validator are tested against text fixtures. Nothing here
has been run against a rendered packet.
