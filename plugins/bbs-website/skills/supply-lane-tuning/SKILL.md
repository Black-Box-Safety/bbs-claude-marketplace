---
name: supply-lane-tuning
description: Tune the BBS Supply channel (Grainger MRO resale; internal track "supply", pricing vehicle NASPO MRO LPA) of the BBS quote bot — system prompt, product surfacing, sourcing/pricing guardrails, voice, and cost. Use whenever the ask is about the Supply lane's chat behavior — "it shows too many products", "limit the options", "recommend one", "the Grainger chat isn't smooth", pricing/facility rules, "make it cheaper to run", or aligning the model with the channel's goals. Covers where the tuning levers live, the grounding rules, and how to verify with the scripted eval.
---
> **BBS Website pipeline — stage: Quote bot.** See `site-wiring-map` for how this fits the whole flow.

# Supply Lane Tuning — BBS Quote Bot

Sibling of `le-lane-tuning` (BBS Direct). This one is the **BBS Supply** channel:
Grainger MRO resale, sourced live from the Grainger MCP connector, priced under the
NASPO MRO LPA. Buyers are CA state agencies (default facility = Cal Fire Sac HQ).

## The goal you are tuning toward

Move a buyer from need → **accurate quote** in as few turns as possible, surfacing **few
options, one recommendation**, at **no markup**, on the **right facility account** — cheaply.
The channel resells ~1.5M Grainger SKUs, so restraint is the whole game: never bury the
buyer (or the token budget) under a wall of cards.

## The tuning levers (change the right one)

| Symptom | Lever | File |
|---|---|---|
| Too many product cards on screen | **Display cap** `GRAINGER_MAX_CARDS` (currently 5) | `src/lib/graingerResult.js` |
| Bot lists/enumerates instead of recommending one | "SURFACE FEW, RECOMMEND ONE" + product-request rules | `src/lib/systemPrompt.js` (Supply block) |
| Restates SKUs/prices already on the cards | "NEVER repeat product details" rule | `src/lib/systemPrompt.js` |
| Wrong facility priced / no account named | "ALWAYS PRICE THE RIGHT FACILITY" (enabled account IDs) | `src/lib/systemPrompt.js` |
| Searches when given an item number (or vice-versa) | "INTAKE ROUTES THE TOOL" | `src/lib/systemPrompt.js` |
| Interrogates the buyer / too many questions | "NARROW WITH ONE QUESTION, ONLY WHEN AMBIGUOUS" | `src/lib/systemPrompt.js` |
| Replies cut off / too long | `max_tokens` (Supply = 1536) in `callClaude()` | `src/components/BBSQuoteFormsBot.jsx` |
| Cost too high | Model routing (`MODELS.fast`→escalate to `.specialist`); trim what re-rides in history | `src/components/BBSQuoteFormsBot.jsx` |
| Tone / anti-AI voice / plain-text | "HOW TO TALK" + "DON'T SOUND LIKE AI" (shared block) | `src/lib/systemPrompt.js` |

**The system prompt is now a pure, testable module** — `buildSystemPrompt({ VP, contract,
isHaiku })` in `src/lib/systemPrompt.js`. `callClaude` calls it; the eval + unit tests import
it. Edit the prompt THERE, not inline in the component.

## How the Supply lane actually runs (so you tune the right thing)

- **Live source = the Grainger MCP connector**, injected server-side by `api/anthropic.js`
  (`injectGraingerMcp`, beta `mcp-client-2025-11-20`) when the client sets `graingerMcp:true`.
  Anthropic executes `grainger_search` / `grainger_price` / `grainger_availability`; the
  results arrive as `mcp_tool_result` blocks and are mapped to cards by `mapGraingerResult`.
- **The display cap is code, not vibes.** `mapGraingerResult` slices to `GRAINGER_MAX_CARDS`
  (5). The MODEL still receives **every** returned row in its tool result — so capping the
  display never hides a match from its reasoning; it just controls what the buyer sees.
  Change the number in ONE place (`graingerResult.js`) and the test + eval track it.
- **Model routing is already Haiku-first.** Every turn starts on `MODELS.fast`
  (`claude-haiku-4-5`); Haiku handles clear lookups and calls `escalate_to_specialist` to
  hand judgment calls to `MODELS.specialist` (Sonnet). Prompt edits must hold up on BOTH —
  check the `isHaiku` branch. This is the main cost dial: the more Haiku can finish alone,
  the cheaper the lane.

## Grounding rules (non-negotiable)

- **PRICING IS THE PRICE — no markup, ever.** Grainger prod `unitPrice` = BBS cost = the CA
  customer's price (BBS is paid via the contract rebate). The prompt says it; don't add a
  margin instruction anywhere.
- **Sandbox pricing must never reach a quote.** `mapGraingerResult` refuses any non-`prod`
  (or `sandbox`/`priceWarning`) row IN CODE, and the prompt's SANDBOX GUARD backs it. Keep
  both — the code guard is the real one.
- **Facility = pricing basis.** Only the enabled accounts price correctly (CMC 887895111,
  Calipatria 887895116, Porterville 887895140, Cal Fire Sac HQ 887895160 = default). If the
  bot prices the default, it must say which account it used.
- **Keep the prompt cache-safe.** `buildSystemPrompt` output is the frozen, cached prefix;
  per-turn state (quote, bid details) rides the LAST message via `buildCachedMessages`.
  Never interpolate per-turn data into the builder, or every turn pays full input price.
- **Don't invent Grainger facts.** The bot narrates from the returned rows; it never makes
  up specs, stock, or lead times it wasn't given.

## Behavior checklist (what the eval scores)

- [ ] **Few options, one pick.** ≤5 cards (code), and the reply leads with ONE recommendation
      (or, when ambiguous, ONE narrowing question) — never an enumerated menu.
- [ ] **Names ≤3 alternatives**, only when they're genuine tradeoffs.
- [ ] **Never restates SKUs / prices / spec dumps** the cards already show.
- [ ] **Routes intake correctly:** item number → `grainger_price` (no search); category/brand
      → `grainger_search`; vague → broaden before giving up.
- [ ] **Asks at most one question**, using real values from the results ("16 oz or 32 oz?").
- [ ] **Prices the right facility** and says which account when it defaulted.
- [ ] **Voice:** plain text, no markdown, no em dashes, one next step toward the quote.

## How to verify (before merging)

1. `npm test` — runs `systemPrompt.test.js` (prompt-contract lint: the rules are still IN
   the prompt) + `graingerResult.test.js` (the 5-card cap) offline. Must be green.
2. `npm run eval:supply` — the **scripted eval** (`src/lib/supplyLane.eval.test.js`). Needs
   `ANTHROPIC_API_KEY` in `.env`. Runs canned Grainger conversations through the real Supply
   prompt + Haiku with MOCKED tool results (deterministic, no live Grainger / rate limit),
   grades each with an LLM judge, prints a scorecard, and fails any scenario under 5/7.
   Add a scenario to `SCENARIOS` whenever you fix a new failure mode — that's how the eval
   grows teeth. It grades **narration** (the mock feeds a known result set); the display cap
   and sandbox refusal are covered by the offline unit tests.
3. For real end-to-end (live Grainger MCP), drive the UI with the local harness per
   `src/components/CLAUDE.md` → Testing. The deployed `*.vercel.app` is egress-blocked from
   the sandbox; local works.
4. Update the nearest CLAUDE.md + the root Changelog in the same PR (living-doc rule).

## Watch-outs

- **Search recall is the known bottleneck** (not display). If the right item isn't in the
  Grainger result set at all, no prompt/cap change fixes that — it's a `grainger-api` search
  problem. Capping display to 5 assumes the gateway returns rows best-first.
- The Supply lane shares the product-request + voice blocks with BBS Direct. A shared-block
  edit hits both lanes — run `le-lane-tuning`'s checks too when you touch shared text.
