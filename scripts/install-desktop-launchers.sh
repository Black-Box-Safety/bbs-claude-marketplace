#!/usr/bin/env bash
# Write machine-local workspace copies and a Desktop launcher folder.
#
#   ./scripts/install-desktop-launchers.sh \
#     --onedrive "/Users/<you>/Library/CloudStorage/OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER" \
#     --repos "$HOME/bbs"
#
# Does not modify the templates in workspace/. Filled copies go to ~/bbs-workspaces/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ONEDRIVE=""
REPOS=""
DEST="${HOME}/bbs-workspaces"
DESKTOP="${HOME}/Desktop/BBS Workspaces"

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \?//'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --onedrive) ONEDRIVE="${2:-}"; shift 2 ;;
    --repos) REPOS="${2:-}"; shift 2 ;;
    --dest) DEST="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

if [[ -z "$ONEDRIVE" || -z "$REPOS" ]]; then
  echo "Both --onedrive and --repos are required." >&2
  usage
fi

# Trim trailing slashes so joins do not double.
ONEDRIVE="${ONEDRIVE%/}"
REPOS="${REPOS%/}"

if [[ "$ONEDRIVE" == *REPLACE-* || "$REPOS" == *REPLACE-* ]]; then
  echo "Pass real paths, not the REPLACE-* tokens." >&2
  exit 1
fi

mkdir -p "$DEST" "$DESKTOP"

fill() {
  local src="$1" out="$2"
  # Use python so paths with spaces and commas (OneDrive) are not sed-special.
  python3 - "$src" "$out" "$ONEDRIVE" "$REPOS" "$ROOT" <<'PY'
import pathlib, sys
src, out, onedrive, repos, marketplace = sys.argv[1:]
text = pathlib.Path(src).read_text(encoding="utf-8")
# Quote desk uses this token for the OneDrive root.
text = text.replace("REPLACE-ON-FIRST-OPEN", onedrive)
text = text.replace("REPLACE-ONEDRIVE-ROOT", onedrive)
text = text.replace("REPLACE-REPOS-ROOT", repos)
pathlib.Path(out).write_text(text, encoding="utf-8")
PY
}

fill "$ROOT/workspace/bbs-rep.code-workspace" "$DEST/bbs-rep.code-workspace"
fill "$ROOT/workspace/bbs-web.code-workspace" "$DEST/bbs-web.code-workspace"
fill "$ROOT/workspace/bbs-admin.code-workspace" "$DEST/bbs-admin.code-workspace"

write_command() {
  local name="$1" target="$2"
  local file="$DESKTOP/Open ${name}.command"
  local quoted
  quoted="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$target")"
  cat > "$file" <<EOF
#!/bin/zsh
open -a "Cursor" $quoted 2>/dev/null || open -a "Visual Studio Code" $quoted
EOF
  chmod +x "$file"
}

write_command "Quote Desk" "$DEST/bbs-rep.code-workspace"
write_command "Web" "$DEST/bbs-web.code-workspace"
write_command "Admin" "$DEST/bbs-admin.code-workspace"

cat > "$DESKTOP/README.txt" <<EOF
BBS Cursor workspaces
=====================

Double-click "Choose a workspace.app" (Mac) or an Open *.command file.

  Quote Desk   California state agency folders
  Web          storefront, catalog, quote bot, agency tenants
  Admin        document store, marketplace, vault, suppliers

Filled workspace files live in: $DEST
Templates (do not edit these for a path): $ROOT/workspace
EOF

python3 - "$DEST" "$DESKTOP/Catalog.html" <<'PY'
from pathlib import Path
import sys
dest, out = sys.argv[1:]
cards = [
    ("BBS Quote Desk", "California state agency quote desk.", f"{dest}/bbs-rep.code-workspace"),
    ("BBS Web", "Storefront, catalog, production quote bot, agency tenants.", f"{dest}/bbs-web.code-workspace"),
    ("BBS Admin", "Document store, marketplace, sales vault, suppliers.", f"{dest}/bbs-admin.code-workspace"),
]
items = []
for title, blurb, path in cards:
    href = "cursor://file" + path
    items.append(f"""      <article>
        <h2>{title}</h2>
        <p>{blurb}</p>
        <a class="btn" href="{href}">Open in Cursor</a>
      </article>""")
html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>BBS Workspaces</title>
  <style>
    body { margin: 0; font-family: "Avenir Next", "Segoe UI", sans-serif;
           background: #051c2c; color: #f4f1ea; padding: 48px 24px; }
    main { max-width: 880px; margin: 0 auto; }
    h1 { font-size: 1.75rem; }
    .gold { color: #b19800; }
    .grid { display: grid; gap: 16px; }
    @media (min-width: 720px) { .grid { grid-template-columns: 1fr 1fr; } }
    article { background: #0a2a3d; border: 1px solid rgba(177,152,0,.35);
              border-radius: 8px; padding: 20px; }
    a.btn { display: inline-block; margin-top: 12px; background: #b19800;
            color: #051c2c; text-decoration: none; font-weight: 700;
            padding: 8px 14px; border-radius: 4px; }
  </style>
</head>
<body>
  <main>
    <h1>BBS <span class="gold">Workspaces</span></h1>
    <p>If a button does nothing, double-click the matching Open ….command file in this folder.</p>
    <div class="grid">
""" + "\n".join(items) + """
    </div>
  </main>
</body>
</html>
"""
Path(out).write_text(html, encoding="utf-8")
PY

if [[ "$(uname -s)" == "Darwin" ]]; then
  APPLESCRIPT="$(mktemp -t bbs-workspaces).applescript"
  cat > "$APPLESCRIPT" <<EOF
set workspaceNames to {"BBS Quote Desk — CA agencies", "BBS Web — storefront, catalog, bots", "BBS Admin — docs, marketplace, vault"}
set workspaceFiles to {"$DEST/bbs-rep.code-workspace", "$DEST/bbs-web.code-workspace", "$DEST/bbs-admin.code-workspace"}
set chosen to choose from list workspaceNames with title "BBS Workspaces" with prompt "Open a workspace in Cursor:" default items {item 1 of workspaceNames} OK button name "Open"
if chosen is false then return
set chosenName to item 1 of chosen
repeat with i from 1 to count of workspaceNames
	if item i of workspaceNames is chosenName then
		set targetFile to item i of workspaceFiles
		exit repeat
	end if
end repeat
do shell script "open -a " & quoted form of "Cursor" & " " & quoted form of targetFile & " || open -a " & quoted form of "Visual Studio Code" & " " & quoted form of targetFile
EOF
  osacompile -o "$DESKTOP/Choose a workspace.app" "$APPLESCRIPT" >/dev/null
  rm -f "$APPLESCRIPT"
  # Also put the chooser on the Desktop itself for one-click access.
  rm -rf "${HOME}/Desktop/BBS Workspaces.app"
  cp -R "$DESKTOP/Choose a workspace.app" "${HOME}/Desktop/BBS Workspaces.app"
fi

echo "Wrote filled workspaces to $DEST"
echo "Wrote Desktop launchers to $DESKTOP"
if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "Chooser app: $HOME/Desktop/BBS Workspaces.app"
  open "$DESKTOP"
fi
echo "Open a workspace once and confirm the folders exist. Missing git clones: scripts/bbs-clone-web-stack.sh $REPOS"
