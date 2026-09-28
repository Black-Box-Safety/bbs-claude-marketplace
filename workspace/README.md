# Workspaces

Three Cursor / VS Code entry points. Same files on Mac and Windows. A plugin install
does **not** open a folder for you — grab the file from this directory (or let
`scripts/install-desktop-launchers.sh` copy a filled-in version to your Desktop).

| File | Who | Opens |
|---|---|---|
| [`bbs-rep.code-workspace`](bbs-rep.code-workspace) | Every quoting rep | `Customers/State of CA Agencies` |
| [`bbs-web.code-workspace`](bbs-web.code-workspace) | Site maintainers (Parker, Griffin) | Shopify, catalog database, production quote bot, agency tenant bots |
| [`bbs-admin.code-workspace`](bbs-admin.code-workspace) | Admin | Document store + this marketplace clone + sales vault + suppliers |

## First open (once per machine)

The editor will say a folder path is missing. That is expected. Placeholders in these
files are tokens, not paths:

| Token | Replace with |
|---|---|
| `REPLACE-ON-FIRST-OPEN` | Your OneDrive root (quote desk only) |
| `REPLACE-ONEDRIVE-ROOT` | The same OneDrive root (admin document store) |
| `REPLACE-REPOS-ROOT` | The folder that holds your `bbs-*` git clones |

Usual OneDrive shapes (the middle folder name varies by how OneDrive was installed):

- **Windows:** `C:/Users/<you>/Black Box Safety - MASTER`, or for a Teams-site sync
  `C:/Users/<you>/OneDrive - Black Box Safety, Inc/Blackbox Safety Team Site - Black Box Safety - MASTER`
  (check File Explorer for the exact synced name on your machine)
- **Mac:** `/Users/<you>/Library/CloudStorage/OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER`

Then File → Open Workspace from File. Accept the recommended extensions. Full walk-through:
`docs/REP-SETUP.md` / `docs/CURSOR-SETUP.md` (screenshots will be pinned in the Teams sales
channel).

Every BBS workspace pins the primary sidebar on the **left**
(`workbench.sideBar.location: left`). Put the same two keys in Cursor / VS Code
**User** settings so a folder opened without a workspace file still matches:

```json
"workbench.sideBar.location": "left",
"workbench.activityBar.location": "default"
```

Faster: from a clone of this repo, in Claude Code run **`/bbs-workspaces`**. It discovers
the BBS folders that already exist on **your** computer and writes only those workspaces,
then puts a logo'd launcher on the Desktop. Same thing from a terminal:

```bash
# Mac / Windows
python3 scripts/bbs-workspaces.py discover
python3 scripts/bbs-workspaces.py request --yes --install-desktop
```

A custom workspace from folders you already have:

```bash
python3 scripts/bbs-workspaces.py request --custom "Field work" --folder ~/bbs-shopify --install-desktop
```

That writes filled copies under `~/bbs-workspaces/` and a **BBS Workspaces** folder on
the Desktop. Drag the folder to the Dock (Mac) or pin it (Windows). Double-click
**Choose a workspace** (Mac) or an `Open *.bat` (Windows).

Do not edit the copy under `~/.claude/plugins/marketplaces/` — `/plugin marketplace update`
overwrites it. Clone this repo (or copy the `workspace/` files out) and substitute there.

## Quote desk (`bbs-rep`)

Format-on-save stays off so customer RFQs are not rewritten; `FILLED/` stays searchable
on purpose. Full walk-through: [`docs/REP-SETUP.md`](../docs/REP-SETUP.md) (VS Code on
Windows) or [`docs/CURSOR-SETUP.md`](../docs/CURSOR-SETUP.md) (Cursor, including Mac).

The desk folder's `CLAUDE.md` (stamped from `DESK-CLAUDE-template.md`) is what makes
Claude sessions know the folder rules. Cursor also needs `.cursor/rules/bbs-invariants.mdc`
at the desk root — Parker stamps that from this repo as part of first-deployment.

## Web (`bbs-web`)

Four git clones in one window. Product truth is `bbs-database`; Shopify renders it;
`bbs-quote-bot` is the production iteration-1 bot; `bbs-customer-bots` is the multi-tenant
Gear Assistant (`<agency>.blackboxsafety.com`). A database change does not appear on the
storefront until sync runs, and does not reach the bot until a `gen-*.mjs` regen is
committed. Read `site-wiring-map` after you open this.

**Access today:** `bbs-shopify` and `bbs-database` live in the `Black-Box-Safety` GitHub
org. `bbs-quote-bot` and `bbs-customer-bots` still live on a personal account
(`pjm3wv`). A teammate who is not a collaborator there will clone two of four folders
and the workspace will look broken. Until those two move into the org, Parker grants
access; `scripts/bbs-clone-web-stack.sh` prints that instead of failing silently.

`bbs-shopify-sync` on a maintainer laptop is a second checkout of `bbs-shopify`, not a
separate repo. Do not add it as a fifth folder.

## Admin (`bbs-admin`)

The marketplace folder is `..` relative to this file, so it only works if you open the
workspace from a **git clone** of `bbs-claude-marketplace`, not from the plugin cache.
Sales vault and suppliers are org repos; clone them next to the web stack under
`REPLACE-REPOS-ROOT`.
