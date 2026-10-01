# bbs-tools

Claude Code only. Ships one executable, `bin/bbs-fill`, which Claude Code puts on the Bash
tool's PATH while the plugin is enabled.

**Why it exists.** Auto mode stopped Kim mid-packet when Claude ran a fill script, and an
allow rule shaped like `Bash(python *…/fill_obs_packet.py *)` would fix that at a price: a
`*` matches anything, so a crafted command could satisfy the rule and run arbitrary Python
past auto mode's safety check. Instead the managed settings allow exactly
`Bash(bbs-fill *)`, and the launcher decides what runs:

- only the scripts on its `ALLOWED` list (the vetted form and quote scripts in `bbs-sales`);
- only from the `bbs-sales` plugin in the same marketplace cache the launcher is installed
  in, after resolving symlinks and `..`;
- with a fixed interpreter (`python`/`python3`, or `node`) and no interpreter options, so
  no argument can become code. Everything after the script path is data.

**Usage** (the skills write this; reps never type it):

```bash
bbs-fill "${CLAUDE_PLUGIN_ROOT}/skills/ca-form-filler/scripts/fill_packet_c.py" packet.pdf inputs.json out.pdf
```

**Why a separate plugin.** claude.ai and Cowork do not install a plugin that has a `bin/`
folder. Keeping `bin/` here leaves `bbs-sales` installable everywhere.

**Changing it.** The name `bbs-fill` is matched by the managed allow rule — never rename
it. Vetting a new script means adding it to `ALLOWED` in a reviewed PR, nothing else.
Tests: `python3 tests/test_bbs_fill.py`.

Owner: Parker Marshall. Last verified 2026-10-01.
