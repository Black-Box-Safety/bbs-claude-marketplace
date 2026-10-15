# Maintainer guide — reviewing and maintaining this marketplace

For whoever maintains this repo and audits work done in it, human or agent.

This marketplace is not a codebase. Its output is quotes and bids that go to California
public agencies under a DVBE certification. A bug here does not crash — it produces a
plausible wrong number on a binding document, and nobody notices until an agency does.
Review accordingly: **the dangerous defects are the silent ones.**

---

## 1. Run the checks first

```bash
python3 scripts/check_marketplace.py          # structural invariants, exit 1 on FAIL
python3 plugins/bbs-foundations/skills/bbs-claude-md-forge/scripts/check_claude_md.py .
```

`check_marketplace.py` covers the failure modes that produce no error at runtime:

| Check | The silent failure it catches |
|---|---|
| `frontmatter_unparseable` | An unquoted colon in `description:` — the skill never loads at all |
| `name_folder_mismatch` | The doctrine hooks match on `plugin:skill`; a mismatch stops doctrine firing |
| `description_truncated` | Over 1,024 chars, the tail is dropped at selection time — usually the "Do NOT use for" clause |
| `dangling_skill_ref` | A skill points at one that was merged away; a rep follows a dead pointer |
| `nonportable_path` | `/mnt/skills/`, `/Users/<someone>/`, `~/.bbs/` — works for the author, fails for everyone |
| `stale_model_id` | Read from `models.json`, so the checker cannot itself go stale |
| `unknown_form_id` | A form ID not in `ca-form-rules.md` — this is the one that reaches a bid |
| `vendor_profile_key_missing` | A field map reading a key that does not exist, so the field fills with nothing |
| `doctrine_sub_dangling` | A doctrine subscription (`hooks/doctrine/subscriptions.json`) naming a skill or command that is gone — the doctrine silently never fires |
| `doctrine_hook_drift` | The two plugins' copies of `hooks/doctrine.ps1` or `hooks/doctrine.py` differ — one matcher was fixed and the other was not |
| `retired_plugin_ref` | A live file names the retired injection plugin outside a sentence saying it is retired — an instruction to run something that no longer exists |

It is **counter-example aware**: prose that names a bad value in order to warn about it
("earlier revisions said GSPD-05-106, which is not a form BBS files") is correct content,
not a defect. If you add a check, add that awareness too — a checker that flags its own
fixes gets ignored, which is worse than no checker.

`WARN description_near_limit` is worth acting on. A description within 5% of the limit has
no room for the next "do NOT use" clause someone adds.

---

## 2. What these checks cannot tell you

**Skill triggering is not verifiable from the repo.** `docs/evals/` measures which skill
wins when several compete, but it shells out to `claude -p` and needs a working Claude
Code install with Anthropic auth. Without that you cannot reproduce any routing number in
a PR — treat those claims as unverified-by-you and say so rather than passing them through.

If you do have Claude auth:

```bash
cd docs/evals
python3 build_skills_json.py
python3 discriminate.py --skills skills.json --queries queries-routing.json \
    --runs 5 --workers 4 --anonymize --out /tmp/r.json
```

Two traps, both documented in `docs/evals/README.md`:

- **`--anonymize` is the run that means something.** Without it the stub names match the
  skill names and the name carries the routing signal, so everything passes and you learn
  nothing.
- **A cluster of `__none__` is throttling, not a regression.** Re-run the affected queries
  alone at `--workers 2` before believing a failure. A real routing defect fails as *the
  wrong skill name* and reproduces in isolation.

**Also not verifiable from the repo:** anything behind an MCP connector (Business Central,
Grainger, SCPRS, Supabase, Shopify), and anything about account-synced skills, which live
in Parker's claude.ai account rather than in git.

---

## 3. Reviewing a Claude-authored PR

Claude is good at producing internally consistent, confident prose. That is exactly the
failure mode to review for. The questions that pay:

1. **Is every factual claim sourced, or is it inferred from a neighbouring file?** This
   repo has been burned both ways on the same fact. A session once read "BBS is NOT
   SB-certified" out of a storefront doctrine file whose scope it had not checked and
   propagated it as a company-wide fact; a later session reversed it on the same kind of
   evidence. The conclusion is now settled — see below — but note what the failure was in
   both directions: **a certification claim taken from whichever file happened to be
   open, without a channel and without a source.** Canonical facts come from
   `bbs-foundations`, and cert/contract numbers ultimately from primary sources.
   A certification claim with no channel on it is not sourced, even when it is true
   somewhere.

   The settled fact, for reference: federally BBS **is** a small business and SDVOSB; in
   California BBS is **DVBE only** and not a small business, having passed the state SB
   revenue threshold. Parker, in session, 2026-09-22, superseding 2026-09-02. Reasoning
   lives in `canonical-facts.md`, "Small-business status is channel-dependent" — do not
   re-litigate it from this paragraph.

2. **Does a measurement claim name its conditions?** "It routes correctly" is not a
   finding. Runs per query, named or anonymized, and the actual distribution are.

3. **Did it change a fact and its checker together?** When a canonical fact has a checker,
   the checker is part of the fact. Changing one and not the other is how
   `claude-opus-4-8` stayed enforced after it was superseded.

4. **Did a fix reach its propagation sites?** Fixing `canonical-facts.md` is the easy half.
   The value also lives in `plugins/*/hooks/doctrine/*.md` (injected into every subscribed skill run) and
   `docs/bbs-managed-settings.json` (the CLAUDE.md pushed to every machine). Grep the whole
   repo for the old value before accepting "fixed".

5. **On a binding document, does the skill fail loudly?** A skill that guesses a checkbox,
   a cert number or a form ID rather than refusing is the defect this repo exists to
   prevent. `[FLAG: why]` and `[MISSING — NEEDS INPUT]` are correct outputs.

6. **Did a consolidation lose anything?** Merged skills are recoverable from git:
   ```bash
   git show <commit>^:plugins/bbs-sales/skills/<old-skill>/SKILL.md
   ```
   Diff the old content against the new skill and its `references/` and confirm the
   domain detail survived — edge cases and field quirks are the parts that quietly vanish.

---

## 4. Standing maintenance

| When | What |
|---|---|
| Every PR | `check_marketplace.py` clean; `WARN` triaged, not ignored |
| Before adding a skill | Run `docs/evals/` routing; add queries for the new skill **and** one that should go to a sibling |
| After editing any description | Re-run the anonymized routing eval; descriptions are the routing table |
| When a model ships | `refresh_models.py` opens a PR for `models.json`; update the two prose copies it names |
| Quarterly | Re-verify `REGISTRY.md` statuses and the cert expiries in `vendor_profile.json` against primary sources |

**Two rules that are not negotiable here.** Never vendor Anthropic's own skills — pin
them, as `document-skills` is pinned; a vendored copy stops receiving upstream fixes.
And never let a skill carry a second copy of a fact that lives in
`references/vendor_profile.json` or `references/ca-form-rules.md`; that is how a cert
expiry goes stale in one place while bids go out from another.

---

## 5. Where the load-bearing facts live

| Fact | Home | Never |
|---|---|---|
| BBS form values — legal name, FEIN, permit, certs, signers | `plugins/bbs-sales/references/vendor_profile.json` | Re-keyed into a skill, or copied to `~/.bbs/` |
| CA form semantics — who signs, what stays blank | `plugins/bbs-sales/references/ca-form-rules.md` | Restated in a skill (field **IDs** do stay local — a field ID belongs to one PDF) |
| Model IDs | `plugins/bbs-foundations/.../references/models.json` | Hand-edited; it is generated |
| Company-wide canon | `plugins/bbs-foundations/.../references/canonical-facts.md` | Inferred from a neighbouring file |
| Certifications by channel | SDVOSB + small business federal · DVBE only (OSDS 2009473) California, no SB preference | Mixed on one form; stated without naming the channel |

---

## 6. Known-open, as of 2026-09-15

Picked up by whoever works here next.

- **The personal-copy cutover is the highest open risk**, and it is outside this repo.
  Five account-synced skills now contradict what replaced them. `HANDOFF.md` has the
  confirmed mechanism and the order. Nothing in git can fix it.
- **`grainger-pricing` was written from the Grainger MCP's tool schemas, not from a live
  call.** The workflow and the two pricing rules come from the tool descriptions; no
  `grainger_price` call was ever executed against a real account. Verify `account.sellRule`
  really comes back, and that the account-resolution step behaves as written, before a rep
  relies on it.
- **`bbs-quote-builder` prices a line tagged `source: "grainger"` at cost only when the
  spec says so** (`pricing.graingerAtCost: true`, or method `at-cost`); `false` sends it
  through the method; saying neither is an error. Which channel is at cost is canon's
  "Grainger sell rule, by channel" (`canonical-facts.md`). The rule only reaches tagged lines: an
  untagged Grainger line is priced by the method. The mitigation is prose —
  `grainger-pricing` names the tag, and the builder's step 9 checks the echoed Grainger
  count against the lines priced through `grainger-pricing`.
- **`ca-form-filler` Path B claims the OBS inspector reads any CA form PDF.** Inherited
  from the pre-merge skill and never tested against a non-OBS packet.
- **The OBS 4007(B) path has never been run against a real Rev. 08/2025 packet** —
  open item 7, pre-existing. Synthetic stubs only.
- **One routing ruling is open**: whether a fresh "agency emailed asking us to quote"
  belongs to `ca-rfq-intake` or `naspo-quote`. Left unresolved on purpose; see
  `docs/evals/queries-ambiguous.json`.

---

Owner: Parker. Last verified 2026-09-15.
