#!/usr/bin/env bash
# Thin wrapper. Prefer: python3 scripts/bbs-workspaces.py request --yes --install-desktop
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ONEDRIVE=""
REPOS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --onedrive) ONEDRIVE="${2:-}"; shift 2 ;;
    --repos) REPOS="${2:-}"; shift 2 ;;
    --dest) DEST="${2:-}"; shift 2 ;;
    -h|--help)
      python3 "$ROOT/scripts/bbs-workspaces.py" --help
      exit 0
      ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done
args=(request --yes --install-desktop)
[[ -n "$ONEDRIVE" ]] && args+=(--onedrive "$ONEDRIVE")
[[ -n "$REPOS" ]] && args+=(--repos "$REPOS")
[[ -n "${DEST:-}" ]] && args+=(--dest "$DEST")
exec python3 "$ROOT/scripts/bbs-workspaces.py" "${args[@]}"
