# ca-form-filler packet profiles — plan

**Date:** 2026-09-16 · **Spec:** `docs/superpowers/specs/2026-09-16-ca-form-filler-packet-profiles-design.md`
· **Branch:** `claude/slice-3-packet-profiles`

---

## Steps

1. **`references/packets/README.md`** — the profile contract, in the directory a profile
   author is already looking at. Front-matter fields, resolution order, the grounding
   rule, the profile/rules split.

2. **Migrate OBS 4007(B).** `git mv references/packet-obs-4007b.md
   references/packets/obs-4007b.md`, add conforming front matter, keep the body. No fill
   behaviour changes: the script never read this file.
   - Recognition markers come from strings this repo already records as belonging to the
     packet's text layer — `packet-obs-4007b.md`'s own title line and the sub-form names
     in its page table. `recognition_source` says so and says they were not re-verified
     against a rendered PDF.

3. **`scripts/packet_profile.py`** — loader, validator, resolver. Stdlib + PyYAML, no PDF
   dependency: it takes extracted text, so it is testable without a packet.
   - `--list`, `--validate`, `--recognize <textfile|->`, `--recognize-pdf <pdf>`.
   - Refuses on ambiguity rather than ranking.

4. **`references/packets/dsh-general.md`, `dsh-atascadero.md`** — `status: stub`. Every
   packet-specific value `[MISSING — NEEDS INPUT]`. `dsh-atascadero` carries
   `extends: dsh-general` so the specialisation path in the resolver is exercised by a
   shipped file. **These are placeholders, not working profiles** — the DSH source
   material is Aanya's, and that is slice 4.

5. **`scripts/test_packet_profiles.py`** — the demonstration. Validates shipped profiles,
   resolves OBS text, checks stubs are inert, checks Path B fallthrough, checks ambiguity
   refusal and specialisation, and writes a **third** profile at test time into a temp
   profiles dir, asserting it resolves while `SKILL.md`'s sha256 is unchanged.

6. **`SKILL.md`** — Path A becomes "recognise the packet, load its profile, fill". No
   packet named in the prose except as the worked example, no profile filename hard-coded
   in the steps. `description:` untouched.

7. **`references/field-maps.md`** — repoint the two `packet-obs-4007b.md` references.

8. **`scripts/fill_obs_packet.py`** — one string only: the failure message points at
   `references/field_map.md`, which does not exist, and the right target is the packet
   profile, not the standalone-forms map. Nothing else in this file is touched.

## Verification

```bash
python3 scripts/check_marketplace.py
python3 plugins/bbs-foundations/skills/bbs-claude-md-forge/scripts/check_claude_md.py "$PWD"
python3 plugins/bbs-sales/skills/ca-form-filler/scripts/packet_profile.py --validate
python3 plugins/bbs-sales/skills/ca-form-filler/scripts/test_packet_profiles.py
git diff main -- plugins/bbs-sales/skills/ca-form-filler/scripts/fill_obs_packet.py
```

The last one is the negative-scope check: the diff must be the single string above, and
`git diff main` must show no change to line 138's `/Off`.

## Risks

- **A marker matches the wrong PDF.** Mitigated by the field-ID validation in the fill
  script, which refuses rather than writing. Recognition is a candidate, not an
  authorisation.
- **A stub becomes live by accident.** The resolver filters on `status: active` before
  evaluating markers, and the validator fails a stub that declares markers.
- **Nothing is tested against a real packet.** Unmitigated and stated in the PR. No CA
  form PDF exists in this repo.
