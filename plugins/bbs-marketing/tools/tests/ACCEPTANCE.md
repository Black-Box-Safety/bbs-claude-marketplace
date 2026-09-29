# Cold-agent acceptance tests

Phase 1 is not done until an agent with no conversation context can be dropped into this
folder and use it correctly. These are those tests. Re-run them whenever `CLAUDE.md`,
`references/tracks/ROUTING.md`, or the track files change.

Run date: 2026-08-13. All three pass.

**If test 1 or 2 ever fails, the fix is `CLAUDE.md` and the routing files, not the test.**

---

## Test 1 — MRO routing

**Prompt.** A fresh agent, no context, dropped into `bbs-marketing/`: *"I need a one-pager for
Sonoma State's procurement office."* Do not build anything. Report the track and why, the files
read to decide, the claims that would go on the piece, and what the gate requires before a PDF
is handed over.

**Pass criteria.** Selects `mro-procurement` unaided · cites `references/tracks/ROUTING.md` · draws
claims only from `references/CLAIMS.md` · names `brand_check.py` as blocking.

**Result: PASS on all four.**

The agent chose `mro-procurement` and gave the right reason, citing ROUTING.md's test of who uses
the item and which vehicle pays, and noting the argument is about how the purchase is transacted.
It ruled out a bridge piece against ROUTING.md's three conditions and set scopes `mro` + `agency`.
It read ROUTING.md, both the MRO track file and CLAIMS.md, plus AUDIENCES, COMPLIANCE, MESSAGING,
and ASSETS.

Every fact it proposed came from the registry verbatim, and it declined the unregistered ones by
name: the DVBE goal percentage, the phone number and web address, the Grainger scale figures, and
any named peer campus. It caught that public-safety vehicle numbers on an MRO piece are a gate
failure, and that Grainger may not be described as fulfilling the order.

Beyond the pass criteria it found three live blockers unprompted: the piece is Tier B because BBS
has not published to Sonoma State before, no Sonoma mark may appear because there is no ASSETS row,
and the missing Roboto weights block any Grainger co-brand build. It also flagged, correctly, that
the two facts which would make the piece land hardest with a procurement officer are both
unregistered, and that registering them is worth more than anything in the layout.

---

## Test 2 — Public-safety routing

**Prompt.** Same setup: *"Make a body armor sell sheet for a county sheriff's equipment unit."*

**Pass criteria.** Selects `public-safety` · cites the charcoal / condensed / tactical dress ·
uses contract `1-23-84-07` · does **not** reach for the Grainger co-brand lockup.

**Result: PASS on all four.**

The agent chose `public-safety` on both of ROUTING.md's tests and picked the track's one-page
agency sell-sheet pattern, with the charcoal ground and Barlow Condensed display face. It set
scopes `public-safety` + `agency`.

It used `1-23-84-07` and explicitly identified `1-23-87-04` as the transposition printed on page 2
of the shipped Body Tactical brochure, which is the exact error the gate was built to catch. It
added Sourcewell `091924-BBS` and NPPGov `PS25650`, and refused the GSA number for having no
registry row.

On marks it refused the entire Grainger set for two independent reasons: the co-brand is MRO-only
and would read as a facilities vendor selling armor, and every one of those rows is unconfirmed in
ASSETS.md. It also refused the unconfirmed credential badges, suggesting the DGS number be set as
live text instead, and refused the sheriff's seal outright. The only third-party mark it accepted
was `dvbe.png`, the one row with a confirmed approval.

It raised the NIJ certification gap as the blocker worth fixing before building rather than
shipping around, which is the right call: it is the strongest proof an equipment unit responds to
and it has no registry row.

---

## Test 3 — Adversarial claim

A piece carrying three known-bad facts must fail the gate with all three named.

```
printf '<p>Black Box Safety is a VA CVE Verified SDVOSB, headquartered in San Diego, CA. Contact sales@blackboxsafety.com</p>' > /tmp/adversarial.html
python3 tools/brand_check.py /tmp/adversarial.html --scope public-safety
```

**Result: PASS.** Three findings, exit code 1, as specified.

```
brand-check FAIL  /tmp/adversarial.html  (3 finding(s))
  [superseded] sdvosb: found 'VA CVE Verified SDVOSB'; approved wording is 'SDVOSB'
  [superseded] hq-city: found 'headquartered in San Diego, CA'; approved wording is 'El Cajon'
  [superseded] contact-email: found 'sales@blackboxsafety.com'; approved wording is 'joey@blackboxsafety.com'
exit code: 1
```

---

## Known limitation found during this run

`references/CLAIMS.md` fails its own gate with 12 findings, because the registry necessarily contains
every superseded wording it polices. This is a false positive, not a defect in the registry, but
it means `brand/*.md` cannot be gated as a glob without excluding the registry by hand. Carried
into Phase 2 as a tool change: `brand_check` should skip its own registry file.

`references/AUDIENCES.md` failed for a related reason and was fixed rather than excluded. It had
reproduced two superseded strings verbatim while warning readers against them; it now refers to
them descriptively and points at the registry for the approved wording.
