# Claims Registry

Every factual assertion on a published piece comes from this table, worded exactly as the
`approved wording` column states. `brand-check` reads this file and fails a build on any
superseded wording, any expired claim, or any missing required claim.

- **presence `required`** — the approved wording MUST appear on a piece in scope
- **presence `as-used`** — the wording is optional, but if the claim is made it must match
- **scope `all`** — applies to every piece; otherwise space-separated tags, matched against
  the `--scope` values passed to brand-check (e.g. `mro`, `public-safety`, `agency`)

## Registry

| id | approved wording | superseded wording | presence | scope | evidence | owner | verified | expires |
|---|---|---|---|---|---|---|---|---|
| dvbe-cert | CA DVBE Cert. 2009473 | CA SB/DVBE Cert. 2009473; certified DVBE No. 2009473; California-registered DVBE; CA DVBE #2009473; California SB/DVBE: 2009473; CA SB/DVBE | as-used | all | DGS certification 2009473 | Joey | 2026-08-13 | 2027-06-30 |
| sdvosb | SDVOSB | VA CVE Verified SDVOSB; VA CVE Verified; VA-verified SDVOSB | as-used | all | SBA VetCert, active 11/16/2022, renews 05/16/2028 (`sources/SBA_BBS_SDVOSB_EXP_05_16_2028.pdf`) | Joey | 2026-08-13 | 2028-05-16 |
| sdvosb-full | SBA-certified Service-Disabled Veteran-Owned Small Business | | as-used | all | Same SBA VetCert record. Use when spelling the credential out | Joey | 2026-08-13 | 2028-05-16 |
| vosb | SBA-certified Veteran-Owned Small Business | | as-used | all | SBA VetCert, active 11/16/2022, renews 05/16/2028. Held but not currently claimed on any piece | Joey | 2026-08-13 | 2028-05-16 |
| uei | FRK5MJD35GN5 | | as-used | all | SAM.gov Unique Entity ID | Joey | 2026-08-13 | 2028-05-16 |
| body-armor-contract | 1-23-84-07 | 1-23-87-04 | as-used | public-safety | CA DGS statewide body armor LPA | Joey | 2026-08-13 | 2027-06-30 |
| hq-city | El Cajon | headquartered in San Diego; headquartered in San Diego, CA | as-used | all | Confirmed by Joey 2026-08-13. San Diego is the county, El Cajon the city | Joey | 2026-08-13 | 2028-08-13 |
| address | 1950 Cordell Ct., Ste 103, El Cajon, CA 92020 | | as-used | all | Confirmed by Joey 2026-08-13 | Joey | 2026-08-13 | 2028-08-13 |
| contact-phone | (619) 967-9812 | (619) 499-7943 | as-used | all | Confirmed by Joey 2026-08-13 as the published number. Resolves pending decision 3. The retired number is on printed brochures and the website; both need updating | Joey | 2026-08-13 | 2027-08-13 |
| person-president | Jackson Dalton, President | | as-used | all | Supplied by Joey 2026-08-13 | Joey | 2026-08-13 | 2027-08-13 |
| cred-csp | Certified Safety Professional | | as-used | all | Held by Jackson Dalton. Issued by the Board of Certified Safety Professionals, and verifiable in the BCSP registry. An individual credential, never written as a company certification | Joey | 2026-08-13 | 2027-08-13 |
| cred-mph | Master of Public Health | | as-used | all | Held by Jackson Dalton. Supplied by Joey 2026-08-13 | Joey | 2026-08-13 | 2027-08-13 |
| quote-tool-url | campus-supply.blackboxsafety.com | uci-supply.blackboxsafety.com | as-used | mro | Renamed 2026-08-13. The original host carried the agency name, which COMPLIANCE §1.2 bars in a domain. Registered as superseded so the old host cannot reappear on a piece | Joey | 2026-08-13 | 2026-11-13 |
| contact-email | joey@blackboxsafety.com | jackson@blackboxsafety.com; sales@blackboxsafety.com; info@blackboxsafety.com; graingercsu@blackboxsafety.com | as-used | all | Confirmed by Joey 2026-08-13 | Joey | 2026-08-13 | 2027-08-13 |
| csu-agreement | C-CSUCO-00001768 | | as-used | mro | CSU Grainger Agreement | Joey | 2026-08-13 | 2027-06-30 |
| grainger-role | Grainger Authorized Tier 1 Diverse Reseller | Authorized Grainger Reseller | as-used | mro | Grainger Distributor Alliance | Joey | 2026-08-13 | 2027-06-30 |
| sourcewell-mro | 091422-WWG | | as-used | mro | Sourcewell Grainger Facility MRO | Joey | 2026-08-13 | 2027-06-30 |
| sourcewell-armor | 091924-BBS | | as-used | public-safety | Sourcewell body armor solutions | Joey | 2026-08-13 | 2027-06-30 |
| naspo | 7-25-51-02.03 | | as-used | mro | NASPO ValuePoint LPA | Joey | 2026-08-13 | 2027-06-30 |
| omnia | 2018-000207 | | as-used | mro | OMNIA Partners | Joey | 2026-08-13 | 2027-06-30 |
| nppgov | PS25650 | | as-used | public-safety | NPPGov | Joey | 2026-08-13 | 2027-06-30 |
| agency-disclaimer | Black Box Safety is an independent supplier. This offer is not sponsored by, affiliated with, or endorsed by | | required | agency | shopify-retail-upsell/context/product-marketing.md | Griffin | 2026-08-13 | 2027-08-13 |
| service-account-manager | A higher education account manager works with your departments and your procurement office directly. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13: an account manager specializing in higher education who bridges laterally between campuses and vertically across roles. Final wording not yet signed off | Joey | 2026-08-13 | 2026-11-13 |
| service-second-team | Your campus keeps the account team it has and gains ours. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13: adding BBS should read as doubling the support a campus receives, not replacing it. Written as addition, never as a count of the agency's own staff, which BBS cannot assert | Joey | 2026-08-13 | 2026-11-13 |
| service-education | Black Box Safety specializes in California public higher education. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13, "education specialization" as the differentiation pillar. Final wording not yet signed off. Naming a specific campus stays blocked by pending decision 8 | Joey | 2026-08-13 | 2026-11-13 |
| service-training | Black Box Safety staff deliver safety and fall protection training on site, led by a Certified Safety Professional. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13 confirmed BBS staff deliver, not manufacturer reps. The credential is Jackson Dalton's, so the line says "led by," never that the company is certified. Never write this as an offer of a meal, per COMPLIANCE §4.3 | Joey | 2026-08-13 | 2026-11-13 |
| service-toolbox | Training sessions and toolbox talks are scheduled with the department. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13, "training lunches, safety tailgates." The meal is deliberately absent: COMPLIANCE §4.3 bars offering meals to agency personnel on a piece. The training is the value and prints on its own | Joey | 2026-08-13 | 2026-11-13 |
| service-kitting | Black Box Safety builds custom kits and site-specific configurations to match how a department works. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13, "ability to custom fit solutions and agility to execute." Final wording not yet signed off | Joey | 2026-08-13 | 2026-11-13 |
| service-quote-tool | Black Box Safety provides a catalog navigation and quoting tool, available to accounts we onboard. | | as-used | mro | **PLACEHOLDER wording.** Joey 2026-08-13: pilot or limited release, so availability is scoped to onboarded accounts rather than stated generally. The tool has no registered name. Re-verify before any piece states it more broadly | Joey | 2026-08-13 | 2026-11-13 |
| ps-category | Black Box Safety supplies body armor, plates, carriers, and duty gear as a specialty. | | as-used | public-safety | **PLACEHOLDER wording.** Joey 2026-08-13, "subject matter expertise in body armor and tactical supplies." Follows the public-safety pillar one wording in MESSAGING §2. Final wording not yet signed off | Joey | 2026-08-13 | 2026-11-13 |
| ps-sizing | Black Box Safety handles sizing and fit for issued equipment. | | as-used | public-safety | **PLACEHOLDER wording.** Joey 2026-08-13, "sizings." Deliberately a service claim, not a coverage claim: cuts, size ranges, and female or TRUFIT coverage remain unregistered and cannot print. An equipment-unit piece needs those rows first | Joey | 2026-08-13 | 2026-11-13 |
| ps-demos | Black Box Safety brings product demonstrations on site. | | as-used | public-safety | **PLACEHOLDER wording.** Joey 2026-08-13, "product demos." COMPLIANCE §4.3: a demonstration is not sample retention. Never offer gear to keep, and never to the person deciding the award | Joey | 2026-08-13 | 2026-11-13 |
| ps-quote-tool | Black Box Safety provides a tactical catalog navigation and quoting tool, available to accounts we onboard. | | as-used | public-safety | **PLACEHOLDER wording.** Joey 2026-08-13: a second tool, separate from the MRO one. **Its host has no registry row**, so no URL prints for this tool. Same domain rule applies when one is chosen: no agency name | Joey | 2026-08-13 | 2026-11-13 |
| service-reporting | Black Box Safety reports your spend back to your office for supplier diversity reporting. | | as-used | mro public-safety | **PLACEHOLDER wording.** Joey 2026-08-13. States the mechanism only, never goal attainment, per COMPLIANCE §2.4. Final wording not yet signed off | Joey | 2026-08-13 | 2026-11-13 |

## Open

- **`sdvosb` resolved 2026-08-13.** Joey supplied the SBA VetCert record: Black Box Safety, Inc.
  holds **active** Service-Disabled Veteran-Owned and Veteran-Owned certifications from the U.S.
  Small Business Administration, entered 11/16/2022, renewing 05/16/2028, UEI `FRK5MJD35GN5`.

  The `VA CVE Verified SDVOSB` wording printed on the LADWP leave-behind is wrong on two counts:
  VA's Center for Verification and Evaluation stopped certifying veteran-owned businesses in
  January 2023, and it credits the wrong agency for a certification BBS actually holds.
  Superseded matching catches it regardless of expiry date.

- **`vosb` is held but unclaimed.** BBS is separately certified Veteran-Owned and no current piece
  says so. Worth considering on federal-facing material.

- **`body-armor-contract`** — `1-23-87-04` appears as a section heading on Body Tactical p2 and is
  a digit transposition. `1-23-84-07` is confirmed correct and appears on both p1 and the LE/MRO
  brochure's DGS badge.

- **The seven `service-*` rows are placeholders and expire 2026-11-13.** They were added 2026-08-13
  for the UC Irvine capability one-pager, whose whole job is differentiation, and the registry
  carried no service wording at all. Joey supplied the concepts; the wording in the table is the
  writer's operationalization of them, not Joey's words. Two consequences: the piece is Tier B and
  cannot distribute until Joey signs the final wording, and no other piece should cite these rows
  until then. The short expiry is deliberate, so a stale placeholder fails the gate rather than
  quietly shipping on a later piece.

  These are the registry's first service claims, added after `AUDIENCES.md` retired "call our sales
  team, we will answer 24/7" as ungoverned. Three carry specific risk:

  - `service-training` asserts that BBS staff deliver the training. Joey confirmed this 2026-08-13.
    **No trainer credential is registered.** A competent-person or authorized-trainer credential
    would be the hardest fact available to the MRO track and it has no row. Get one.
  - `service-toolbox` deliberately drops the meal from Joey's "training lunches." `COMPLIANCE.md`
    §4.3 bars offering meals to procurement or equipment-unit personnel on any piece. The training
    is the value; the lunch is a gift-reporting problem for the buyer.
  - `service-quote-tool` is scoped to onboarded accounts because the tool is in pilot. If it reaches
    general release, that is a new verified date, not a quiet rewording.

- **Agency names in domains and product names, decided 2026-08-13.** The quoting tool was first
  proposed as `uci-supply.blackboxsafety.com`, and naming it after UC Irvine's mascot was raised as
  an option. `COMPLIANCE.md` §1.2 bars an agency name in a domain, a product name, or a code name,
  and a university mascot is a separately licensed trademark of the Regents. Both were declined:
  the host is now `campus-supply.blackboxsafety.com`, with the original registered as superseded so
  it cannot reappear on a piece, and no BBS product carries an agency's name or mascot. The rule
  generalizes. A per-campus subdomain is a good instinct and the neutral form keeps it: one host,
  many campuses, no borrowed marks.

- **Four `ps-*` rows added 2026-08-13 for the UC Irvine bridge piece.** Same placeholder status and
  same 2026-11-13 expiry as the `service-*` rows. Two notes that outlive this piece:

  - `ps-sizing` is a *service* claim, not a *coverage* claim, and the distinction is load-bearing.
    `AUDIENCES.md` records that the equipment-unit buyer says no when sizing coverage is vague, so
    "we handle sizing and fit" is all that can be said until cuts, size ranges, and female or
    TRUFIT coverage carry rows. Do not stretch this row to cover a spec grid.
  - `ps-quote-tool` prints with no URL. The MRO tool has a registered host and this one does not.
    When a host is chosen it inherits the domain rule decided 2026-08-13: no agency name, no
    mascot, no borrowed marks.

  Still unregistered and still blocking anything aimed at an equipment unit: NIJ certification
  wording, the DGS LPA piggyback mechanism, and the authorized-brand roster's re-verification.

- **`cred-csp` and `cred-mph` are individual credentials, not company certifications.** They belong
  to Jackson Dalton. A piece may say training is led by a Certified Safety Professional; no piece
  may say Black Box Safety is one. The distinction is the same one that governs DVBE and SDVOSB:
  state the mechanism, never inflate the holder.

- **`agency-disclaimer`** is absent from both shipped print pieces. It was defined as
  non-negotiable in the retail kit and never reached print. This is the finding that motivated
  the whole registry.

## Pending decisions — facts the brand files need but the registry cannot yet govern

Surfaced 2026-08-13 by the distillation of `core.md` and both track files. Each is a real fact
the writers needed and correctly refused to invent; each appears in those files as a
`NEEDS CLAIM` marker. **A piece cannot print any of these until the row exists.**

| # | Fact needed | Why it matters | Conflict found |
|---|---|---|---|
| 1 | The **3% DVBE goal** figure | The entire MRO wedge turns on it. The wedge is currently written without a number | none — simply unregistered |
| 2 | **NIJ certification** wording for armor, plates, carriers | The public-safety track's central technical proof | none — simply unregistered |
| 3 | ~~**Public phone number**~~ | **RESOLVED 2026-08-13.** `(619) 967-9812` is the published number and now carries a registry row; `(619) 499-7943` is registered as superseded. Brochures and the website still print the retired number and need updating | closed |
| 4 | **Web address** | Needed in every contact block | `blackboxsafety.com` in sources, unregistered. Note `quote-tool-url` registers one subdomain only and is not a general web address |
| 5 | **GSA contract** `47QSWA23D000Y` | Appears in the retail context file; a federal vehicle with no registry row | unregistered; federal claims carry their own rules |
| 6 | **NASPO number** | Registry says `7-25-51-02.03` | Branding Guide business card prints `CA LPA: 7-18-51-02.18`. Stale, or a different vehicle? |
| 7 | **Grainger scale figures** (1.5M products, 280+ branches, ~97% next-day, 17+ DCs, 1000+ manufacturers) | Printed as authority claims | Grainger's numbers, they drift, and they need re-check dates |
| 8 | **Fresno State** as named peer precedent | The strongest social proof the MRO track has | unregistered |
| 9 | **Authorized brand roster** | Captured in full in the public-safety track | asserted from a March 2025 source with no re-verify date |
| 10 | **Founder story** — name, branch, service-connected injury | The veteran-owned identity rests on it | source is `BBS Company Profile (1).pdf`, dated 06/2020 |
| 11 | **Tagline** "Keeping you safe on the job" | appears only in that same 2020 source | currency unknown |

### Claims deliberately NOT added as superseded wording

- **`Service-Disabled Veteran-Owned Small Business` without the `SBA-certified` prefix** (as printed
  on the Branding Guide business card). It cannot be added as a superseded string because it is a
  substring of the approved `sdvosb-full` wording — adding it would fail every *correct* use.
  Catching this needs a rule the gate does not have, not another row.

- **`Nationally Established Certified Disabled Veteran Business Enterprise`** (Body Tactical p1
  headline). DVBE is a California state certification, so "nationally established" is at best
  ambiguous. Not carried into any brand file. Needs Joey's call on whether it is defensible before
  it is either registered or added as superseded.

### Other unresolved source conflicts

- **Typography.** `BBS Branding Guide.pdf` specifies Univers LT Std throughout. `BBS Company
  Profile (1).pdf` specifies Oswald Bold headline with "Universe Roman" body and a five-color
  archetype palette that appears nowhere else. Neither matches what actually ships — the built
  pieces use Roboto (Grainger's face) and Barlow Condensed. The distillation resolved in favor of
  the Branding Guide, but the guide may simply be stale.

- **Logo clear-space and minimum-size values** in `core.md` are prescriptive design decisions made
  during distillation, not sourced from any document. They need Joey's approval or replacement.

- **`bbs-logo-black.png`** is an approved rendering per the Branding Guide but exists as no file
  anywhere in the asset library.

- **Accessibility, computed not sourced:** gold `#B19800` on navy `#051C2C` measures 6.0:1 and
  passes AA; gold on white measures 2.9:1 and fails. `core.md` restricts gold on light grounds to
  display sizes on that basis.
