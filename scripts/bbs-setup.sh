#!/usr/bin/env bash
# Black Box Safety rep-machine bootstrap (macOS). Installs the command-line
# tools Claude Code and Cursor lean on to read RFQs.
#
# Idempotent: skips anything already installed. Safe to rerun.
#
#   ./scripts/bbs-setup.sh
#   ./scripts/bbs-setup.sh --dry-run
set -u

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]]; then
  DRY_RUN=1
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is for macOS. On Windows use scripts/bbs-setup.ps1." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it from https://brew.sh, then rerun this script." >&2
  exit 1
fi

echo "BBS rep-machine bootstrap (macOS)$( [[ $DRY_RUN -eq 1 ]] && echo ' (dry run - nothing will be installed)' )"
echo ""

failed=()

already_formula() {
  brew list --formula --versions "$1" >/dev/null 2>&1
}

already_cask() {
  brew list --cask --versions "$1" >/dev/null 2>&1
}

install_formula() {
  local name="$1" why="$2"
  if already_formula "$name"; then
    printf '[ok]      %s\n' "$name"
    return
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "$name" "$why"
    return
  fi
  printf '[install] %-22s %s\n' "$name" "$why"
  if ! brew install "$name"; then
    echo "warning: brew install failed for $name. Install it by hand later; nothing else here depends on it." >&2
    failed+=("$name")
  fi
}

install_cask() {
  local name="$1" why="$2" app_path="${3:-}"
  if already_cask "$name" || { [[ -n "$app_path" ]] && [[ -d "$app_path" ]]; }; then
    printf '[ok]      %s\n' "$name"
    return
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "$name (cask)" "$why"
    return
  fi
  printf '[install] %-22s %s\n' "$name (cask)" "$why"
  if ! brew install --cask "$name"; then
    echo "warning: brew cask install failed for $name. Install it by hand later; nothing else here depends on it." >&2
    failed+=("$name")
  fi
}

# Mirror of scripts/bbs-setup.ps1, plus LibreOffice (document-skills and
# bbs-quote-builder call soffice).
install_formula git        "Claude Code hooks and git for the marketplace clone"
install_formula node       "superpowers-chrome browsing skill needs Node"
install_cask    google-chrome "the browser Claude drives for product research" "/Applications/Google Chrome.app"
install_formula poppler    "pdftotext/pdfinfo: RFQ PDFs become text before Claude reads them"
install_formula tesseract  "OCR for scanned RFQs and faxed worksheets"
install_formula pandoc     "Word attachments to markdown"
install_formula uv         "Python runtime for form-fill and document-skills scripts, zero config"
install_formula duckdb     "query price lists and SCPRS exports instead of reading them whole"
install_formula jq         "JSON plumbing for scripts and hooks"
install_cask    libreoffice "soffice: quote-builder PDF export and document-skills conversion" "/Applications/LibreOffice.app"

echo ""
if [[ ${#failed[@]} -gt 0 ]]; then
  echo "Finished with ${#failed[@]} item(s) to install by hand: ${failed[*]}"
else
  echo "Done."
fi
echo "Quit and reopen Cursor or VS Code so PATH picks up the new tools, then run /bbs-checkup in the Claude Code panel."
