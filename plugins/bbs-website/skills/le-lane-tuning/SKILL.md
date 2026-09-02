---
name: le-lane-tuning
description: Tune the BBS Direct channel (law-enforcement, manufacturer-direct; internal track "direct", formerly "nppgov") of the BBS quote bot — system prompt, advisor knowledge, brand recommendations, voice, and search behavior. Use whenever the ask is about the bot's chat behavior, tone, product suggestions, preferred manufacturers, "the chatting isn't smooth", "it's not recommending the right brands", or aligning the model with the channel's goals. Covers where the tuning levers live, the grounding rules, and how to verify a change.
---
> **BBS Website pipeline — stage: Quote bot.** See `site-wiring-map` for how this fits the whole flow.

# LE Lane Tuning — BBS Quote Bot

## The goal you are tuning toward

Move a law-enforcement buyer from "I need something" to a **completed quote** with minimal
friction and **zero dead-ends**, while helping them **understand what BBS sells** and get the
right products **for their mission**. Every model turn ends with ONE clear next step that
exists on screen. Full statement of intent: `docs/superpowers/2026-06-29-model-ux-alignment-brief.md`
— read it before any behavior change; where the model and the UI could tell different
stories, they must tell the same one.

## The tuning levers (change the right one)

| Symptom | Lever | File |
|---|---|---|
| Tone, flow, turn structure, dead-ends | System prompt in `callClaude()` | `src/components/BBSQuoteFormsBot.jsx` |
| Wrong brand recommended / not suggesting BBS's best suppliers | Preferred-manufacturers section + bought-together pairs | `src/knowledge/advisor-playbook.md` (hand-edited) |
| Customer's word for a product doesn't find it | Alias list ("What customers call things") | `src/knowledge/advisor-playbook.md` |
| Bot doesn't know a category/brand exists | Regenerate the indexes — never hand-edit them | `scripts/gen-category-index.mjs`, `scripts/gen-manufacturer-index.mjs` |
| Right product ranks below its accessories | Search ranking (Voyage rerank tier) | `api/products/search.js` (see `api/CLAUDE.md`) |
| Replies cut off / too long | `max_tokens` (currently 450) in `callClaude()` | `src/components/BBSQuoteFormsBot.jsx` |

## Grounding rules (non-negotiable)

- **Preferred brands = BBS's best suppliers, verified.** The list in the advisor playbook is
  grounded in supplier tier / Business Central purchase spend (the `bbs-suppliers` repo
  manifest, `index.md`) cross-checked against the brands featured on the live
  **blackboxsafety.com**. Never add a category→brand pair from intuition; cite the source and
  date it in the playbook's Provenance note. Corporate families matter (Point Blank owns
  First Tactical, Gould & Goodrich, Paraclete; Avon owns Team Wendy).
- **A preference is only real if the catalog carries it.** Before adding a brand to the
  playbook or to `BRAND_PREFERENCES` in `api/products/search.js` (the card-order boost —
  keep the two in sync), verify the manufacturer+category pair has rows in the
  `product_contract_prices` view (read-only SQL). A supplier can be top-tier and still
  absent from the direct LE catalog (Gould & Goodrich), or present under a different brand
  name (Point Blank body armor sells as Paraclete). Recommending an unfindable brand is a
  dead-end.
- **Never let the bot invent facts.** Brand/spec claims must come from the manufacturer
  index, `get_manufacturer`, or the playbook. If a fact is unknown, the playbook stays silent.
- **Frame preference as service, not promotion.** These brands are suggested because BBS's
  direct relationships mean the best pricing, availability, and support — a solicitation's
  named spec or brand always wins over the preference list.
- **Keep the prompt cache-safe.** The system prompt + tools are a frozen, cached prefix;
  volatile per-turn state (quote, customer info) rides the LAST message via
  `buildCachedMessages`. Never interpolate anything that changes per turn into the system
  prompt, or every turn pays full input cost.
- **Both models, one voice.** Haiku handles clear lookups and escalates judgment calls to
  Sonnet (`escalate_to_specialist`); prompt changes apply to both — check the `isHaiku`
  branches when editing.

## Behavior checklist (test the tuned model against this)

From the alignment brief — a change isn't done until the bot:

- [ ] Opens around the buyer's **need**, never contract eligibility; NPPGov (the pricing
      vehicle under BBS Direct) is a pricing basis, not a restriction.
- [ ] **Anti-bounce:** reassures an unsure buyer and keeps momentum; specialist hand-off is
      a continuation, never an exit.
- [ ] **Searches before saying "no match"** — including unfamiliar words and marketing names
      (check the alias list catches it).
- [ ] Leads with the **preferred manufacturer** for the category (e.g. Avon for CBRN,
      Point Blank for body armor), alternatives second.
- [ ] Recommends **ONE** pick in 1–3 short sentences; never re-lists what the cards show.
- [ ] Suggests ONE genuinely-fitting adjacent item (bought-together pairs), then lets the
      buyer steer.
- [ ] Reads `CURRENT QUOTE` every turn; respects button-added items; never re-adds,
      contradicts quantities, or claims an empty quote.
- [ ] Uses **device-agnostic UI language** ("your quote", "the Quote tab") — never "click
      the sidebar".
- [ ] Ends every turn with one next step that exists on screen.
- [ ] Sounds like Parker: plain words, contractions, no AI filler, **no em dashes**, one
      exclamation point max, closes helpfully.

## How to verify (before merging)

1. `npm run build` — the knowledge files are compiled into the bundle; a broken import
   fails here.
2. Drive the real UI with the local harness (real Supabase data) per
   `src/components/CLAUDE.md` → Testing. Run at least these conversations on BBS Direct:
   - Mission request: "outfit a new patrol officer" → right category set, preferred brands lead.
   - Alias: "20 rifletechs" → searches, finds the Team Wendy RIFLETECH.
   - Brand preference: "need gas masks for the team" → Avon first, not MIRA.
   - Quote-state: add an item via + Add, then ask "what's in my quote?" → acknowledges it.
   - Vague ask on Haiku → escalates instead of guessing.
3. Score each transcript against the behavior checklist above.
4. Update the nearest CLAUDE.md + the root Changelog in the same PR (living-doc rule).

## When supplier priorities change

Parker confirms a new preferred brand or a tier changes in `bbs-suppliers`: update the
preferred-manufacturers section of `advisor-playbook.md` (with provenance + date), add any
new customer-facing aliases, regenerate the manufacturer index if the Supabase
`manufacturers` table changed, and re-run the brand-preference checks above.
