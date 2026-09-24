---
packet_id: dsh-atascadero
title: "[MISSING — NEEDS INPUT] DSH Atascadero bid packet"
revision: "[MISSING — NEEDS INPUT]"
status: stub
extends: dsh-general
recognize:
  all: []
recognition_source: >-
  None. No DSH Atascadero packet PDF is committed to this repo and none was available to
  the session that created this file. Markers must come from a real packet before this
  profile can go active.
fill:
  mode: path-b
rules: ${CLAUDE_PLUGIN_ROOT}/references/ca-form-rules.md
---

# DSH Atascadero bid packet — placeholder, not a working profile

**This profile is a `stub` and is inert**, on the same terms as `dsh-general.md`: no
markers, never matched, DSH Atascadero packets go to Path B today.

It exists separately because a site-specific packet is the case the resolver's
specialisation rule is for, and because the steward's slice names it.

## What `extends: dsh-general` means

A declaration that this packet is the general DSH packet plus site-specific content, and
an assertion the validator enforces once both profiles are active: this profile's `all`
markers must be a **strict superset** of `dsh-general`'s. That is what makes the two
resolve deterministically when a real Atascadero packet matches both — the superset wins,
and there is no scoring or ranking anywhere in the decision.

If Atascadero's packet turns out **not** to contain the general packet's markers, the two
are different documents and this one should not extend the other. Drop `extends:` and
give it its own marker set rather than weakening `dsh-general`'s to make the relationship
hold.

## What is missing

The same list as `dsh-general.md`, plus whatever distinguishes the Atascadero packet from
the general one — which is itself `[MISSING — NEEDS INPUT]` until both are in hand. Note
that the site's Grainger account (`887895144`, in
`${CLAUDE_PLUGIN_ROOT}/skills/naspo-quote/references/agency-registry.md`) is a pricing
fact, not a recognition marker; do not use it as one.
