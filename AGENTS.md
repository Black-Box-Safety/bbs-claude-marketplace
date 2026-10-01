# AGENTS.md — the contract every agent in this repo works under

Read by Cursor natively. Claude Code reads it via `@AGENTS.md` in `CLAUDE.md`.

This file holds **facts and invariants** — what is true and what must not break. It does
not hold review posture or build posture; those differ by tool and live in
`.cursor/rules/` and `.claude/agents/` respectively. Two agents that share a stance share
blind spots, and then review is theatre.

`.cursor/rules/bbs-invariants.mdc` is the short always-on injection of the five
invariants for Cursor sessions that do not load this file (the quote-desk workspace).
Keep it a pointer, not a second fact base. Stamp the same file onto the desk root;
do not rewrite it per machine.

---

## What this repo is

The BBS Claude marketplace: five local plugins and a pinned commons, distributing the way
Black Box Safety works to a small team that is not technical. Its output is quotes and
bids sent to California public agencies under a DVBE certification.

**A defect here does not crash. It produces a plausible wrong number on a binding
document, and nobody notices until an agency does.** Every rule below exists because of
that sentence.

## The five invariants

1. **Never invent a fact that belongs to a system of record.** Prices, stock, spend, cert
   numbers, contract numbers, form IDs come from a tool result or a named file. Unknown is
   `[FLAG: why]` or `[MISSING — NEEDS INPUT]`, never a plausible value.
2. **Truth lives in one place.** A fact restated in a second file is a fact that will go
   stale in one of them. Point at the source; never re-key it.
3. **A fact with a checker is inseparable from its checker.** Change both or neither.
   `claude-opus-4-8` survived being superseded because the checker still enforced it.
4. **Fail loudly on a binding document.** A skill that guesses a checkbox, a signer, or a
   form ID is the failure mode this repo exists to prevent.
5. **Humans send.** On Claude Code, managed settings deny the send-class tools. On
   Cursor, `.cursor/rules/bbs-invariants.mdc` is the control — Cursor does not inherit
   that deny list. Documents are produced ready; a person transmits them. Do not add
   send-capable MCP servers to a rep machine.

## Where the load-bearing facts live

| Fact | Home | Never |
|---|---|---|
| BBS form values — legal name, FEIN, permit, certs, signers | `plugins/bbs-sales/references/vendor_profile.json` | Re-keyed into a skill; copied to `~/.bbs/` |
| CA form semantics — who signs, what stays blank | `plugins/bbs-sales/references/ca-form-rules.md` | Restated in a skill. Field **IDs** do stay local — an ID belongs to one PDF |
| Model IDs | `plugins/bbs-foundations/skills/bbs-claude-md-forge/references/models.json` | Hand-edited; it is generated |
| Company-wide canon | `.../references/canonical-facts.md` | Inferred from a neighbouring file |
| Supplier context | `bbs-suppliers` repo, bonded by immutable `slug` | Duplicated here |

**Certifications follow the channel — and so does small-business status.**

- **Federal and primes:** **SDVOSB**, and BBS **is** a small business under SBA size
  standards. Both are claimable; federal small-business language is correct.
- **California state:** **DVBE only** (OSDS cert `2009473`). BBS passed California's SB
  revenue threshold, so BBS is **not** a California small business and the 5% SB
  preference (SCM §1204) is **never** claimed on a California bid. The DVBE incentive
  (SCM §1202) is unaffected and still claimed on competitive solicitations.

Never mixed on one form, and never stated channel-neutrally — "BBS is a small business"
is true federally and false in California, so a sentence that omits the channel is wrong
in one direction or the other. Ruling and reasoning:
`plugins/bbs-foundations/skills/bbs-claude-md-forge/references/canonical-facts.md`,
"Small-business status is channel-dependent" (Parker, in session, 2026-09-22, superseding
the 2026-09-02 ruling).

**Signatures.** Counsel has given the team broad discretion to sign for each other on any
form in the quoting process when the quote is under $250,000 (Parker, in session,
2026-10-01, superseding the Parker-and-Jackson delegation of 2026-09-16), so packets are
produced signed. Who the team is, how the limit is measured and which lines stay Jackson's
are recorded once, in `plugins/bbs-sales/references/ca-form-rules.md`, "Delegated
signatures", and `vendor_profile.json` `signature_delegation`. The rule is **the right
signer on the right line** — never a customer's or a third party's signature, and never a
line whose signer you cannot determine. The customer-facing storefront bot is *not* covered
by that delegation and signs nothing.

## Terms that mean two things

| Term | The two senses |
|---|---|
| **punchout** | (1) The standard procurement pattern — an agency's eProcurement system links out to a supplier's catalog. Live and correct; `grainger-promo-page` uses it. (2) BBS's own retired pricing path at `b2b.blackboxsafety.com`. **Retired** — Grainger pricing comes from the Grainger MCP. Never "fix" sense (1) into the MCP wording. |

## Verify before you assert

```bash
python3 scripts/check_marketplace.py         # structural invariants; exit 1 on FAIL
python3 scripts/check_marketplace.py --requirements   # what each skill needs installed
```

It catches what fails silently: a skill that never loads, a description truncated through
its own "do NOT use" clause, a pointer to a merged-away skill or a retired slash
command, a path that resolves only
on the author's machine, a stale model ID, a form ID that is not in the rules, a
vendor-profile key that does not exist, an external system a skill uses without declaring,
a drifted README badge count, and a file read mid-run that points at something only this repo
has (`docs/`, `AGENTS.md`, or a path above `${CLAUDE_PLUGIN_ROOT}`), which on a rep's machine
reads as a missing file.

It runs on every pull request via `.github/workflows/check-marketplace.yml` and **a FAIL
fails the check** (ruled 2026-09-18). Require the `invariants` job in branch protection so
the merge button follows it.

It is **counter-example aware** — prose naming a bad value in order to warn about it is
correct content. If you add a check, add that awareness, or the checker will flag its own
fixes and get ignored.

**What it cannot tell you:** skill triggering (`docs/evals/` needs Claude auth to
reproduce), anything behind an MCP connector, and anything about account-synced skills,
which live in Parker's claude.ai account and not in git.

That second limit bounds the dependency check too. It proves a **floor**, not a ceiling:
it can show that a skill naming `grainger_price` must declare `grainger`, and it cannot
show that a skill which only says "look it up in Business Central" needs anything at all.
Which is why `requires:` is mandatory rather than inferred — see the working rule below.

## Working rules

- **Branch, PR, review, merge.** Never commit to `main`. A PR is merged only after review
  by an agent that did not write it.
- **Pin, never vendor**, anything from Anthropic or a third party — a vendored copy stops
  receiving upstream fixes.
- **Portable paths only.** `${CLAUDE_PLUGIN_ROOT}` and `$SKILL_DIR`. Never `/mnt/skills/`,
  `/Users/<someone>/`, or a per-machine dotfile copy.
- **Every skill declares what it needs**, in its own frontmatter: `requires:` for systems
  the job cannot complete without, `degrades-without:` for ones it says are unavailable and
  carries on. Both name systems, never kinds — the kind of a system lives once, in the
  checker's registry, and `--requirements` prints it. A skill that needs nothing writes
  `requires: []`; an omitted key is a FAIL, because to a rep it reads the same as an
  oversight. Declare the system, not the brand name a paragraph happens to mention.
- **Quote a `description:` containing a colon**, or use a `>-` block scalar. An unquoted
  colon means the skill never loads at all.
- **Keep a skill description under 1024 characters.** Past that it is truncated at
  selection time, usually through the "do NOT use for" clause.
- **Credentials stay out of git** — API keys, buying account numbers, signature images.
  FEIN and seller's permit are committed deliberately; this repo is private and
  BBS-specific.

## When the work is a skill

Per-customer variation belongs **inside** a skill as a profile, not beside it as a sibling.
Siblings compete on descriptions, which is probabilistic and can silently pick wrong.
Profiles route on document content, which is deterministic. Merge on the **job**, not on
the input: `dgs-bpo-item-check` and `grainger-pricing` take the same list of part numbers
and answer different questions, so they stay apart.

---

Owner: Parker Marshall. Last verified 2026-10-01.
