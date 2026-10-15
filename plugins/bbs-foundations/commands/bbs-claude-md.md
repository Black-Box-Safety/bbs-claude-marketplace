---
description: Create, audit, or sync CLAUDE.md files the BBS way — run the deterministic checker, apply the bbs-claude-md-forge doctrine and templates, then hand the cap and chain repair to claudeforge if it is installed. Works on a code repo, a plugin, a data vault, or a customer folder on OneDrive.
argument-hint: "[init | audit | sync] [path]"
---

# /bbs-claude-md

Run the `bbs-claude-md-forge` skill on the path given (default: the working directory).
The steps below are the shape of the run; the skill carries the rules.

1. **Decide the kind of place.** Look before asking: git repo with code → `code-repo`;
   OneDrive tree of RFQs and POs → `customer-folder`; `plugins/<name>/` → `plugin`;
   private markdown records → `data-vault`. Say which and why in one line.

2. **Check what is already there.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/bbs-claude-md-forge/scripts/check_claude_md.py" "${1:-.}"
   ```
   `python` is what `scripts/bbs-setup.ps1` installs on Windows; Mac: type `python3` instead.
   Report every FAIL with its file:line before touching anything. A FAIL on canonical
   facts (LPA number, SB claim, DVBE in a federal file) is a fact error, not a style
   error; fix the fact.

3. **`init`** — no CLAUDE.md yet. Read the folder the way the skill says: siblings,
   systems of record, forms, buyers, naming quirks. Draft from the matching template in
   `references/templates.md`, inherit the doctrine groups that apply, and stop under 150
   lines. If sub-folders deserve their own file, write them and chain with `@path` at
   column one. Show the draft; do not write it until the user says go.

4. **`audit`** — CLAUDE.md exists. Read it against `references/canonical-facts.md` and
   `references/checklist.md`. List: what is wrong (facts), what is stale (dates, paths,
   deadlines), what is missing (identity paragraph, footer, chain), what is over the cap.
   Propose targeted edits as diffs. Do not rewrite a file that is mostly right.

5. **`sync`** — after edits. Re-run the checker until zero FAIL. If the `claudeforge`
   plugin is installed, run `/sync-claude-md` for cap enforcement and chain repair and
   `claude-md-link-check` for import resolution; if it is not installed, say so in one
   line and rely on the checker — it already covers what matters. Never install anything
   on the user's behalf.

6. **Finish.** State the final line count per file, the FAIL count (must be zero), the
   WARN count with each warning named, and any fact you corrected in a *different* file
   because this one disagreed with the canonical reference. Nothing committed; the user
   reviews and commits.

Do not write a README here — that is `github-standards`. Do not draft customer email — that
is `parker-voice`. If the folder is public on GitHub, read `references/bbs-doctrine.md`
rule 11 before writing a single account number.
