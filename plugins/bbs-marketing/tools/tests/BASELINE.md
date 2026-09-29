# brand-check baselines — real BBS pieces

Each section records what `brand_check` reports on a piece BBS actually produced,
and what every finding means. These are proof the gate catches real errors, not
synthetic ones.

## Body Tactical brochure (shipped)

Date: 2026-08-13

Proof that `brand_check` catches real, already-printed errors. The source is the
brochure BBS actually shipped: `brand/sources/BBS_Body_Tactical_Brochure_250306_R1.pdf`
(rev 250306_R1). Reproduce with:

```
pdftotext "brand/sources/BBS_Body_Tactical_Brochure_250306_R1.pdf" /tmp/tactical.txt
python3 tools/brand_check.py /tmp/tactical.txt --scope public-safety
```

### Output (exit code 1)

```
brand-check FAIL  /tmp/tactical.txt  (3 finding(s))
  [superseded] body-armor-contract: found '1-23-87-04'; approved wording is '1-23-84-07'
  [superseded] hq-city: found 'headquartered in San Diego, CA'; approved wording is 'El Cajon'
  [superseded] contact-email: found 'jackson@blackboxsafety.com'; approved wording is 'joey@blackboxsafety.com'
```

Re-verified 2026-08-13 after the overlap fix. This block previously read 4 findings:
`hq-city` reported twice, because `headquartered in San Diego` is a prefix of
`headquartered in San Diego, CA` and both matched the same sentence. Overlapping
variants within one claim now collapse to the longest match, so the count equals the
number of distinct defects: 3. The defects themselves are unchanged.

### What each finding means

- **`body-armor-contract` — `1-23-87-04`** — digit transposition of the real DGS statewide
  body armor contract `1-23-84-07`. The brochure prints it BOTH ways: correctly on p1
  (twice) and transposed in the p2 section heading "California STATEWIDE CONTRACT
  1-23-87-04 for Body Armor". A wrong contract number on a public-agency piece is a
  procurement defect, not a typo.
- **`hq-city` — "headquartered in San Diego, CA"** — BBS is headquartered in El Cajon.
  San Diego is the county, El Cajon the city.
- **`contact-email` — `jackson@blackboxsafety.com`** — a stale contact address in both
  page footers. The approved contact is `joey@blackboxsafety.com`.

### Notes on this baseline

- **`sdvosb` does NOT fire here, and that is correct.** The `VA CVE Verified SDVOSB`
  wording lives on the LADWP leave-behind (see the Open section of `references/CLAIMS.md`
  and the next section of this file), which is not among the source PDFs in this repo.
  This brochure never makes an SDVOSB claim in extractable text, so there is nothing to
  supersede. Do not "fix" the tool to make this finding appear here.
- **`agency-disclaimer` is out of scope for this run.** Adding `--scope agency` raises a
  fourth finding, `[missing] agency-disclaimer`, because the required disclaimer never
  reached print. It stays silent under `--scope public-safety` by design: a claim scoped
  to a narrow track is only required when the caller names that track.
- Text is extracted with `pdftotext` (poppler). Anything set as artwork rather than live
  text — badge lockups, logo lettering — is invisible to this gate.

## LADWP leave-behind (2026-07)

Date: 2026-08-13

The piece that motivated the `sdvosb` row. It is HTML, not PDF, and lives outside this
repo, so the Body Tactical baseline never exercised it. Reproduce with:

```
python3 tools/brand_check.py \
  "../claude-marketing/joey-marketing/campaigns/projects/2026-07-ladwp-grainger-leavebehind/brochure.template.html" \
  --scope mro --scope agency
```

(The path above is relative to this repo; the run below used the absolute OneDrive path.)

### Output (exit code 1)

```
brand-check FAIL  .../2026-07-ladwp-grainger-leavebehind/brochure.template.html  (3 finding(s))
  [superseded] dvbe-cert: found 'CA SB/DVBE Cert. 2009473'; approved wording is 'CA DVBE Cert. 2009473'
  [superseded] sdvosb: found 'VA CVE Verified SDVOSB'; approved wording is 'SDVOSB'
  [missing] agency-disclaimer: required wording absent for scope 'agency': 'Black Box Safety is an independent supplier. This offer is not sponsored by, affiliated with, or endorsed by'
```

### What each finding means

- **`sdvosb` — "VA CVE Verified SDVOSB"** — wrong on two counts. VA's Center for
  Verification and Evaluation stopped certifying veteran-owned businesses in January
  2023, so the piece prints a defunct authority; and it credits the wrong agency for a
  certification BBS genuinely holds. The SBA VetCert record (active 11/16/2022, renews
  05/16/2028) is the evidence. Approved wording is plain `SDVOSB`, or
  `SBA-certified Service-Disabled Veteran-Owned Small Business` spelled out. This line
  is set in the legal strip on BOTH pages of the piece.
- **`dvbe-cert` — "CA SB/DVBE Cert. 2009473"** — the certification number is right, the
  rendering is not. DGS certifies BBS as a DVBE; folding `SB/` into the label implies a
  Small Business certification that this number does not carry. Approved wording is
  `CA DVBE Cert. 2009473`. Also on both pages, and split across `<b>` tags in the
  source — the gate matches through the markup.
- **`agency-disclaimer` — missing** — the independent-supplier disclaimer required on
  every `agency`-scoped piece never made it onto this leave-behind. This is the finding
  the whole registry was built to prevent, and it is a `missing`, not a `superseded`:
  nothing wrong is printed, the required thing is simply absent.

### Notes on this baseline

- **This run is why `sdvosb` exists in the registry.** It fires here and nowhere else in
  the pinned sources.
- **The `sdvosb` row also reported twice before the overlap fix.** `VA CVE Verified` is a
  prefix of `VA CVE Verified SDVOSB`; the pre-fix tool printed both and called it 4
  findings. There are 3 defects.
- **Scope selection matters.** `--scope mro` is what pulls in the Grainger-track claims;
  `--scope agency` is what makes the disclaimer required. Running this piece with neither
  flag reports only the two superseded wordings.
- This is the HTML template, not a rendered PDF. Entities and tags are decoded and
  stripped before matching, so the audit reflects what a reader would see.
