---
packet_id: dsh-general
title: "[MISSING — NEEDS INPUT] Department of State Hospitals bid packet"
revision: "[MISSING — NEEDS INPUT]"
status: stub
recognize:
  all: []
recognition_source: >-
  None. No DSH packet PDF is committed to this repo and none was available to the session
  that created this file, so there is no text to read markers out of. Markers must come
  from a real packet before this profile can go active.
fill:
  mode: path-b
rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md
---

# DSH bid packet — placeholder, not a working profile

**This profile is a `stub` and is inert.** It declares no recognition markers, so the
resolver never matches it and every DSH packet goes to Path B — the general
map-and-fill path — exactly as it does today. Nothing about DSH handling changes
because this file exists.

It is here to record what is missing, and to hold the shape a real profile will take.

## What is missing

Everything specific to the packet. None of it may be guessed: a page number, a field ID
or a signer invented here would reach a binding bid.

| Needed | Status |
|---|---|
| A blank DSH packet PDF, or `pdftotext` output from one | `[MISSING — NEEDS INPUT]` |
| Recognition markers read from that text | `[MISSING — NEEDS INPUT]` |
| Packet revision | `[MISSING — NEEDS INPUT]` |
| Page → sub-form map | `[MISSING — NEEDS INPUT]` |
| AcroForm field IDs, and whether the packet is fillable or flat | `[MISSING — NEEDS INPUT]` |
| Flat company-name lines and their coordinates, if any | `[MISSING — NEEDS INPUT]` |
| Which sub-forms it carries, so `ca-form-rules.md` can be checked for each signer | `[MISSING — NEEDS INPUT]` |

## Who it is waiting on

Aanya's DSH iterations, which the maintainers are folding in. They are not in this plugin
and there is nothing on this machine to look up for them. Until one of them arrives with a
real packet attached, this stays a stub, and DSH packets go to Path B, as above.

## Before setting `status: active`

1. Fill every row above from the packet itself, never from a neighbouring packet.
2. Take the signer for each sub-form from
   `${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md`. Where that file assigns no signer
   for a form this packet contains, flag `⚑ SIGNATURE REQUIRED` — do not infer one from
   the OBS packet, which is a different solicitation from a different department.
3. Check the markers do not also match `obs-4007b` — run
   `packet_profile.py --recognize` against both packets' text.
4. `packet_profile.py --validate` must pass.
