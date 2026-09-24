# Packet profiles — the contract

A **profile** describes one specific PDF that BBS receives as a bound bid packet: how to
recognise it, what each page holds, which AcroForm field IDs are irregular, and which
script fills it. `ca-form-filler`'s Path A reads this directory; adding a packet means
adding a file here and changing nothing else.

Profiles exist instead of one skill per packet. Sibling skills compete on their
`description:`, which is probabilistic — it can silently pick the wrong one, and a packet
filled against the wrong map is a wrong number on a binding bid. A profile routes on text
found in the PDF, which is deterministic.

## What a profile owns, and what it must not

| In the profile | In `${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md` |
|---|---|
| AcroForm field IDs, page numbers, annotation coordinates | Who signs which line |
| Recognition markers and where they were read from | What the State fills and must stay blank |
| Which script fills it, which pages to verify | Which certification language applies |

A field **ID** belongs to one PDF, so it stays here: the same STD 204 has different
internal names inside a bound packet than as a standalone download. A **rule** belongs to
the form whoever fills it, so it lives once in `ca-form-rules.md` and this file points at
it. If you are about to write a signing rule or a leave-blank rule into a profile, put it
in `ca-form-rules.md` instead and cite it.

## Front matter

```yaml
---
packet_id: obs-4007b          # required · must equal the filename stem
title: "CDCR RFQ Packet: B"   # required · the packet's human name
revision: "Rev. 08/2025"      # required · the revision this map was built against
status: active                # required · active | stub
recognize:                    # required
  all:  ["..."]               #   every marker must appear in the PDF text
  any:  ["..."]               #   optional · at least one must appear
  none: ["..."]               #   optional · none may appear
recognition_source: ...       # required · where these markers were read from
extends: <packet_id>          # optional · declares this a specialisation
fill:                         # required
  mode: scripted              #   scripted | path-b
  script: scripts/....py      #   required when scripted · relative to the skill dir
  inputs_template: ...        #   optional · relative to the skill dir
  verify_script: ...          #   optional
  verify_pages: [2, 12]       #   optional · the pages that carry the risk
rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md   # required, verbatim
---
```

**Quote any value holding a colon**, or use a `>-` block scalar — `title: CDCR RFQ
Packet: B` is two things to a YAML parser and neither of them is a title. This is the
same rule AGENTS.md states for a skill's `description:`, and it bites the same way one
level down: the profile does not parse, and the packet it describes loses its scripted
fill. The resolver refuses rather than routing around the missing file, and
`--validate` names the line.

The front matter is parsed in `packet_profile.py` rather than by PyYAML, so Path A's
first step needs nothing installed on a rep machine. It accepts exactly the shapes above
— scalars, quoted strings, `>-` block scalars, `key:` mappings and lists, inline or
dashed — and **raises on anything else** rather than guessing at it. If a profile needs a
shape that is not here, add it to the parser deliberately; do not discover that it
half-parsed.

The body below the front matter is the human page map: a page/form/what-is-filled/signer
table, the annotation coordinates if the packet has flat lines, the irregular field names,
and where on this PDF the State's own fields sit. The signer column names the signer; it
does not restate why — `ca-form-rules.md` owns that.

## `status: stub`

A packet BBS is known to receive but has no verified map for. Every packet-specific value
is `[MISSING — NEEDS INPUT]`, and a stub declares no recognition markers.

**A stub is inert.** The resolver filters on `status: active` before it evaluates any
marker, so a stub can never route a real PDF into a fill path nobody has verified. It
exists to record what is missing and who it is waiting on, which is the honest state — an
invented marker or an invented field ID would be worse than no profile at all.

## How recognition resolves

On text extracted from the PDF itself. Never on the filename, never on what the rep
called it:

0. **Check the profile set conforms first.** Every profile — stubs included — has its
   `recognize:` block and `status:` checked before a single marker is evaluated, and a
   profile that will not parse at all stops the resolution too. Both are a **refusal**,
   not a fallthrough. The contract's claim is that routing is deterministic rather than
   probabilistic, so the check that makes it so runs here, on the path the skill uses,
   and not only under `--validate`. The slip this catches is the ordinary one:
   `all: "MARKER"`, a scalar where a one-element list belongs, reads as *no* markers, and
   a profile with no required markers matches every PDF in existence.
1. `pdftotext <packet>.pdf -`.
2. Evaluate every `active` profile: all of `all` present, at least one of `any` present
   when `any` is non-empty, none of `none` present. Case-insensitive, on whitespace-
   collapsed text — a PDF text layer breaks lines wherever the layout did.
3. **One match** → that profile.
4. **Several matches** → the one whose `all` set is a strict superset of every other
   match's. That is how a general packet and a site-specific specialisation of it resolve.
   If no candidate subsumes all the others the resolver **refuses** and names them; it
   does not score or rank, because a ranked guess between two binding-document maps is
   the failure this design exists to prevent.
5. **No match** → Path B, the general map-and-fill path. The safe default.

### Recognition is not the safety boundary

A wrong match cannot quietly produce a wrong packet. The fill script validates every
field ID, its type and its page against the PDF in hand and refuses to write when one is
unknown — so a mismatched profile yields no output file, not a bad one. Recognition
proposes; field validation authorises.

### Markers must be grounded

Every marker is a string someone read out of the actual PDF, or out of a repo file that
recorded it from the PDF. `recognition_source` says which, and says so honestly when the
strings were carried over from an earlier map rather than re-read from a rendered packet.

Do not write a marker because it looks like something the form probably says. A plausible
marker that matches the wrong document is the one way this design fails quietly.

## Tools

```bash
SKILL_DIR=<the folder containing SKILL.md>
python3 "$SKILL_DIR/scripts/packet_profile.py" --list
python3 "$SKILL_DIR/scripts/packet_profile.py" --validate
python3 "$SKILL_DIR/scripts/packet_profile.py" --recognize-pdf <packet.pdf>
python3 "$SKILL_DIR/scripts/test_packet_profiles.py"
```

`--validate` is the machine-readable half of this document, and
`scripts/check_marketplace.py` shells out to it, so a profile that breaks this contract
fails the repo's structural gate rather than only a command someone remembers to run.
`test_packet_profiles.py` demonstrates that a third profile resolves with `SKILL.md`
unchanged.

Exit codes: `0` success, `1` a failure or a refusal, `2` a missing input file or a
`pdftotext` that is absent or broken. A refusal is never reported as a broken machine,
and a broken machine is never reported as a refusal.
