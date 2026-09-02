# Checklist — every check the script runs, and the defect that earned it

`scripts/check_claude_md.py <path>` runs all of these on every `CLAUDE.md` under the path.
FAIL exits non-zero. WARN does not. Nearly every row is a real defect found in a real BBS
file; the "found in" column says where.

## Fails

| Check | Why | Found in |
|---|---|---|
| Line count > 150 | The hard cap. Over it, split and chain | 747947 playbook at 160 |
| `@path` at column one does not resolve | A broken import silently loads nothing | Sentinel tree after a rename |
| Markdown link to a `.md` file does not resolve | Same failure, human-facing | — |
| Inline `@path` (not at column one) | Never loads; looks like it does. The Sentinel tree shipped with every import inline and zero of them resolving | Sentinel root + 2 site files |
| Sandbox path `/mnt/skills`, `/mnt/user-data` | Exists only inside a hosted Claude session; anyone following it on a Mac hits nothing | 747947 tooling section |
| Secret-shaped string (`eyJ…` JWT, `sk-…`, 40+ hex, `password=`, `service_role`) | Never commit secrets | — |
| Placeholder `[TODO]`, `[TBD]`, `[PLACEHOLDER]`, `[Insert…]`, `TODO(` | Generic content is a template someone forgot to fill | — |
| Stale model ID (`claude-opus-4-5`, `claude-3-…`, dated suffix) | Only `claude-opus-4-8`, `claude-sonnet-5`, `claude-haiku-4-5` | `bbs-agent/config.py` |
| MRO LPA written `7-25-52-02.03` or `7-18-51-02.18` | The number is `7-25-51-02.03`; the typo spread to 10 places | `bbs-agent`, a `bbs-ops` spec |
| "SB certified", "SB credit", "5% SB preference" | BBS is not CA SB-certified | `ca-quote-hub/CLAUDE.md` |
| A DVBE *claim* ("as a DVBE", "DVBE-certified", "DVBE credit") in a federal-context file (mentions Bechtel, FAR, DFARS, USACE, federal prime) without SDVOSB on the same line | Cert language follows the channel; DVBE on a federal bid is the wrong credential. A role title ("DVBE veteran owner: Jackson Dalton") or a rule about when not to use it is not a claim and passes | Bechtel quote email, first draft |
| `7-25-51-02.03` cited as a federal vehicle | It is a California LPA | — |

## Warns

| Check | Why | Found in |
|---|---|---|
| No maintenance footer (no "Maintain" heading, "Last verified", or "Owner:") | Only 2 of 8 BBS files had one; the rest rot | 6 of 8 repos |
| Duplicate heading text | Two sections with one name; one is stale | `bbs-bc-mcp-proxy` Base64 bullet twice |
| Root file has child `CLAUDE.md` files it does not import | The chain is decorative | Sentinel root, first version |
| A sub-file does not import `@../CLAUDE.md` | A session started in the subdirectory misses the universal rules | Sentinel site files, first version |
| Stale status banner: "days remaining", "due <past date>", "as of <date >90 days old>" | A READ-FIRST banner advertising a deadline three months gone | 747947 playbook |
| "San Diego, CA" as headquarters | El Cajon is locked | live site copy |
| File under 20 lines | Probably a stub; either fill it or delete it | `ca-quote-hub` intake skill at 25 |

Not checked: em-dash density. The house README standard limits them to genuine asides, but
every strong CLAUDE.md in the fleet uses them freely; a check that warns on `bbs-database`
is measuring the wrong thing.

## Not checked mechanically — review by eye

- Does the first paragraph say what this place does **not** own?
- Is every fact with a system of record a pointer, not a copy?
- Does each gotcha name symptom, cause, and fix?
- Could a new hire copy any command in the file and run it?
- If editing this repo can break another, do both files say so?
- Does any other repo define a skill, script, or command with the same name?
