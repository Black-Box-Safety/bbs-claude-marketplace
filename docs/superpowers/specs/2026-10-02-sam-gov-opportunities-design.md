# SAM.gov opportunities skill — design

**Date:** 2026-10-02
**Asked by:** Parker, deferred from the 2026-10-01 team-rollout session ("we will do that
separately"); scope from `docs/SESSION-HANDOFF-2026-10-01.md` §4.1.
**For:** Kim Quezon and Griffin Forsyth.

## The job

Answer one question: **which federal notices are open now for this NAICS code or agency, and
can BBS respond to each one's set-aside?** Read-only. No bid or no-bid call, no outreach, no
registration, no CRM write.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Transport | A stdlib Python script calling `GET https://api.sam.gov/opportunities/v2/search` | The README connector table rules out a server and a 150-tool government bundle. A script keeps the key out of the conversation. Fetching the URL with the web tool would put the key in the transcript. |
| Credential | `SAM_GOV_API_KEY`, set by each person outside Claude | Same row of the README. Never in git, never pasted into chat; the script redacts it from every error. |
| Home | `bbs-sales` | The README connector table files SAM.gov under Sales, and Kim and Griffin install `bbs-sales`. Federal is an exception to the plugin's California framing, and the README says so, as it already does for `bbs-deck-voice`. |
| Request budget | One request per NAICS code; at most 4 per run unless raised | A personal key with no role on an entity is limited to 10 requests a day. One associated with an entity gets 1,000. Sources: GSA's PSC API page and the SAM.gov System Account User Guide, read 2026-10-02. |
| Paging | None; more than 1,000 matches is reported TRUNCATED | The docs call `offset` "the page index" without saying whether it counts pages or records. A wrong guess skips records silently. |
| Notice types | Filtered client-side by `type` text, default solicitation, combined synopsis/solicitation, presolicitation and sources sought | Filtering with `ptype` on the request would cost one request per type. Every excluded notice is counted by type, so a type string that does not match is visible. |
| Open | `active` is Yes, and the response deadline has not passed or none is given | The API's `status` filter is documented "Coming Soon". Undated notices are kept and counted. |
| 404 | A failure (exit 1), not an empty result | The docs say 404 is "No Data found". On 2026-10-02 every request from a cloud container got an empty 404, with or without a key. Calling that "nothing open" would be a plausible wrong answer. |
| Set-aside fit | A code table in the script; each answer points at canon's certification sections | Canon: federally BBS is SDVOSB and a small business. SDVOSB set-asides are eligible. SB set-asides carry a flag to confirm the size standard. VA VOSB set-asides carry a flag, because canon records SDVOSB, not VOSB. A code for a certification BBS does not hold says so. An unknown code is flagged. |
| BBS NAICS codes | Not supplied | They are not in canon or `vendor_profile.json`. The skill asks, or writes `[MISSING — NEEDS INPUT]`. |
| Points of contact | Not printed | They are on the sam.gov page. Leaving them out keeps the output from becoming an outreach list. |

## Checker

`sam-gov` is registered in `scripts/check_marketplace.py` as a `service`, in its own
review-side PR, [Black-Box-Safety/bbs-claude-marketplace#51](https://github.com/Black-Box-Safety/bbs-claude-marketplace/pull/51).

- **Signals:** `SAM_GOV_API_KEY` and `api.sam.gov`. The bare words "SAM.gov" are not a
  signal, because they also name BBS's own registration and UEI.
- **canon:** `None`. Whether canon gets a row for it is Parker's call.

## Not verified

- **No live call has succeeded.** The cloud container's requests were refused at the gateway.
  The first real run on Kim's or Griffin's machine is the acceptance test. The response field
  names come from the documentation's examples.
- **Routing has not been measured.** Two queries were added to `docs/evals/queries-routing.json`,
  and the eval needs Claude auth to run.
