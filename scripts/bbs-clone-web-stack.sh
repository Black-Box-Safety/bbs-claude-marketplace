#!/usr/bin/env bash
# Clone the git repos the BBS Web workspace expects into one parent folder.
#
#   ./scripts/bbs-clone-web-stack.sh [DEST]
#   DEST defaults to ~/bbs
#
# Org repos clone for anyone with Black-Box-Safety access. Quote-bot and
# customer-bots still live on a personal account; if clone fails, the script
# says so and continues.
#
# Clones use https, so git asks for credentials the first time. Sign in once with
# `gh auth login` (or let Git Credential Manager prompt) and it remembers.
set -u

DEST="${1:-$HOME/bbs}"
ORG="https://github.com/Black-Box-Safety"
PERSONAL="https://github.com/pjm3wv"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found. Install Git, then rerun." >&2
  exit 1
fi

mkdir -p "$DEST"
echo "Cloning into $DEST"
echo ""

clone_one() {
  local url="$1" name="$2" required="$3"
  local dir="$DEST/$name"
  if [[ -d "$dir/.git" ]]; then
    printf '[ok]      %s already present\n' "$name"
    return 0
  fi
  printf '[clone]   %s\n' "$name"
  if git clone "$url/$name.git" "$dir"; then
    return 0
  fi
  if [[ "$required" == "required" ]]; then
    echo "error: could not clone $name from $url (need org access)." >&2
    return 1
  fi
  if [[ "$url" == "$PERSONAL" ]]; then
    echo "skipped: $name is still on pjm3wv ($url/$name); ask Parker for access."
  else
    echo "skipped: $name clone failed ($url/$name); check org access, credentials, or network."
  fi
  return 0
}

failed=0
clone_one "$ORG" "bbs-shopify" required || failed=1
clone_one "$ORG" "bbs-database" required || failed=1
clone_one "$PERSONAL" "bbs-quote-bot" optional || true
clone_one "$PERSONAL" "bbs-customer-bots" optional || true
clone_one "$ORG" "bbs-sales-vault" optional || true
clone_one "$ORG" "bbs-suppliers" optional || true

echo ""
echo "Next: fill the workspace files (or run scripts/install-desktop-launchers.sh)."
echo "  REPLACE-REPOS-ROOT  ->  $DEST"
echo "  REPLACE-ONEDRIVE-ROOT / REPLACE-ON-FIRST-OPEN  ->  your OneDrive MASTER folder"
echo ""
echo "Then open workspace/bbs-web.code-workspace from a clone of bbs-claude-marketplace."
exit $failed
