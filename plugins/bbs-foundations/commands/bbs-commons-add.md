---
description: Evaluate an external Claude plugin or skill and, if it passes the bar, pin it into the BBS marketplace the commons way — never a user-level copy. Runs the docs/COMMONS.md lifecycle end to end and stops at a PR.
argument-hint: "[repo-url or owner/repo]"
---

# /bbs-commons-add

Run in the `bbs-claude-marketplace` repo. This is the **only** approved way to add an
outside tool. The rules live in `docs/COMMONS.md` and the curator posture in
`.claude/agents/commons-curator.md` — this command is the order and the gates, not a second
copy of them. A candidate from an awesome-list is a source, never an install path: **do not
copy it into a user-level skills directory** — that is what produced this company's shadowed
personal skills.

Candidate: `$1` (ask for the upstream repo if not given).

1. **Evaluate — three hard filters, then fit.** Reject on any: needs a per-machine API key;
   non-permissive license; no independent maintained upstream to pin. Then judge the
   **whole tree** — because a marketplace `skills:` list is additive, not restrictive, every
   skill, command, hook and agent in the upstream ships. Name what a BBS rep would actually
   use it for. Microsoft 365, not Google. If it is developer-aimed, it is **maintainer-tier**
   (available, not fleet-enabled), like `superpowers`.

2. **Read the whole tree before pinning.** Shallow-clone and list it:
   ```bash
   git clone -q --filter=blob:none --no-checkout --depth 1 "<url>" /tmp/commons-probe
   git -C /tmp/commons-probe ls-tree -r --name-only HEAD
   ```
   Flag every hook (read `hooks/hooks.json`, not only `plugin.json`) and any command that
   downloads-and-runs code from outside the pin — that is a rejection or a named, accepted
   risk, never silent.

3. **Pin — a pin is a fact from a system of record, read or not written.** Prefer a commit
   SHA. If pinning a tag, record the **peeled commit**, not the tag object:
   ```bash
   git ls-remote "<url>" "refs/tags/<tag>" "refs/tags/<tag>^{}" | tail -1 | cut -f1
   ```
   State the release model and cadence: rolling (no tags) → monthly; tagged → quarterly;
   multi-train → monthly.

4. **Validate.**
   ```bash
   python3 scripts/check_marketplace.py                 # must exit 0
   claude plugin validate . --strict                    # if the CLI is present; else say so
   ```

5. **Document, do not duplicate.** Add the pinned entry to
   `.claude-plugin/marketplace.json`. Add a roster row (fleet) or a Maintainer-tier row
   (owner only) plus a provenance row to `docs/COMMONS.md` — pin, verified date, peeled
   commit, license, and the honest attribution if the name implies an author who did not
   write it. If the count changes, fix the README badge in the same PR so no fact drifts.

6. **Decide the plane.** Fleet-enable only rep-appropriate tools, by adding the plugin to
   `enabledPlugins` in `plugins/bbs-foundations/docs/bbs-managed-settings.json` — and note
   that it reaches machines only when Parker re-pastes managed settings (account-side).
   Leave maintainer-tier tools out of `enabledPlugins`.

7. **Stop at a PR.** Open it; an agent that did not write it reviews. **Escalate, do not
   decide:** whether the tool is fleet or maintainer-tier, whether an accepted risk is worth
   it, and anything that changes managed settings are Parker's calls. Nothing is committed to
   `main`, and nothing is enabled fleet-wide, by this command alone.
