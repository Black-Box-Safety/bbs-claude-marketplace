---
description: Discover BBS folders on this computer and request Cursor workspaces for them — named recipes (quote desk, web, admin) or a custom workspace from folders you already have. Writes Desktop launchers with the BBS logo.
argument-hint: "[discover|request|custom]"
---

# /bbs-workspaces

Anyone on the team can request workspaces for **the folders that already exist on
this machine**. Do not guess a path. Do not use another person's home directory.

## 1. Find the script

From a clone of `bbs-claude-marketplace`:

```bash
python3 scripts/bbs-workspaces.py discover
```

If this session is running from the installed plugin, the same file lives two
levels above the plugin root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/../../scripts/bbs-workspaces.py" discover
```

If neither path exists, say so and stop. A plugin install that has not been
updated from `main` will not have this script yet.

**Windows.** A rep bootstrapped by `scripts\bbs-setup.ps1` has `uv`, not `python3`.
Every command below runs the same way with `python3` swapped for the uv form:

```powershell
uv run --no-project --python 3 python scripts\bbs-workspaces.py discover
```

For the default request (every ready workspace plus Desktop launchers),
`scripts\install-desktop-launchers.ps1` finds uv, `py -3`, or a real `python` for you.

## 2. Discover (always first)

Run `discover` (add `--json` if you want the machine-readable form). Show the
user:

- which known BBS folders were found, with the path the script printed
- which named workspaces are **ready** (required folders exist)
- which are **not yet**, and the missing folder ids

Do not invent a substitute path for a miss. If `bbs-quote-bot` is missing,
the web workspace can still be requested — that repo is optional. If
`bbs-shopify` is missing, web is not ready.

## 3. Request

Ask which they want. Default: every named workspace that is ready, plus Desktop
launchers.

```bash
python3 scripts/bbs-workspaces.py request --yes --install-desktop
```

Or a subset: `--ids rep` · `--ids web,admin`

**Custom workspace** — they name folders on this computer that are not a recipe:

```bash
python3 scripts/bbs-workspaces.py request --custom "Field work" \
  --folder /the/path/they/gave --folder /another/path/they/gave \
  --install-desktop
```

Every `--folder` must already exist. If they describe a repo they do not have,
tell them to clone it (web stack: `scripts/bbs-clone-web-stack.sh`) or skip it.
Never create an empty folder to make a workspace look complete.

## 4. Finish

Tell them:

- Filled files live in `~/bbs-workspaces/`
- Mac: **BBS Workspaces** on the Desktop uses the company logo; double-click it
  and pick a workspace
- Windows: `Desktop/BBS Workspaces/Open *.bat`
- Re-run `/bbs-workspaces` when they clone another repo or want a new custom set
- The primary sidebar is pinned **left** in every written workspace. Reload the
  window if it is still on the right.
- Their own Cursor / VS Code **User** settings are left alone unless they ask.
  If they want a folder opened without a workspace to match too, rerun `request`
  with `--pin-user-settings`; it writes `settings.json.bak` beside the file before
  changing it.

If `discover` found nothing, they have not cloned the git repos and OneDrive is
not in the usual place. Point at `workspace/README.md`. Do not fill
`REPLACE-*` by hand unless they refuse the script.
