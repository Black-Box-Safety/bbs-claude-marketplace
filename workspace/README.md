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

- **Windows:** `C:/Users/<you>/Black Box Safety - MASTER`
- **Mac:** `/Users/<you>/Library/CloudStorage/OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER`

Then File → Open Workspace from File. Accept the recommended extensions.

Faster: from a clone of this repo,

```bash
# Mac
./scripts/bbs-clone-web-stack.sh ~/bbs          # site maintainers
./scripts/install-desktop-launchers.sh \
  --onedrive "/Users/<you>/Library/CloudStorage/OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER" \
  --repos ~/bbs

# Windows (PowerShell)
.\scripts\install-desktop-launchers.ps1 -OneDrive "$env:USERPROFILE\Black Box Safety - MASTER" -Repos "$HOME\bbs"
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
