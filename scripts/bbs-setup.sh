#!/usr/bin/env bash
# Black Box Safety rep-machine bootstrap (macOS). Installs the command-line
# tools Claude Code and Cursor lean on to read RFQs, the Python and Node
# libraries the document skills import, and every BBS plugin.
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

# The VS Code extension and the Desktop app bundle their own Claude; this script needs the
# `claude` command itself, so it installs the cask only when nothing answers to that name.
if command -v claude >/dev/null 2>&1; then
  printf '[ok]      %s\n' "claude-code"
else
  install_cask claude-code "the \`claude\` command this script installs the BBS plugins with"
fi

# Installed is not the same as on PATH. The libreoffice cask links eight of LibreOffice's
# helper programs into Homebrew's bin and not soffice, the one the skills call.
BREW_BIN="$(brew --prefix)/bin"
SOFFICE_APP="/Applications/LibreOffice.app/Contents/MacOS/soffice"
if command -v soffice >/dev/null 2>&1; then
  printf '[ok]      %-22s %s\n' "soffice" "$(command -v soffice)"
elif [[ ! -x "$SOFFICE_APP" ]]; then
  [[ $DRY_RUN -eq 1 ]] || { echo "[missing] soffice                LibreOffice did not install - see the lines above"; failed+=("soffice"); }
elif [[ $DRY_RUN -eq 1 ]]; then
  printf '[would]   %-22s %s\n' "soffice" "link into $BREW_BIN"
else
  printf '[path]    %-22s %s\n' "soffice" "link into $BREW_BIN"
  ln -sf "$SOFFICE_APP" "$BREW_BIN/soffice" || failed+=("soffice")
fi

# Python libraries the form-fill, quote and reconciliation scripts import, for the python3 the
# skills call. Homebrew's Python refuses a plain pip install (PEP 668), so retry the --user
# install with the flag it names; a --user install never touches Homebrew's own packages. On a
# Mac without the command-line tools, /usr/bin/python3 is a stub that only offers to install them.
PY_PACKAGES="pypdf pymupdf openpyxl"
if ! python3 -c 'import sys' >/dev/null 2>&1; then
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "python packages" "$PY_PACKAGES after python3 works"
  else
    echo "[missing] python3                run: xcode-select --install   then run this script again"
    failed+=("python3")
  fi
elif python3 -c 'import pypdf, fitz, openpyxl' >/dev/null 2>&1; then
  printf '[ok]      %s\n' "$PY_PACKAGES"
elif [[ $DRY_RUN -eq 1 ]]; then
  printf '[would]   %-22s %s\n' "python packages" "$PY_PACKAGES"
else
  printf '[install] %-22s %s\n' "python packages" "$PY_PACKAGES"
  # shellcheck disable=SC2086
  python3 -m pip install --user --quiet $PY_PACKAGES >/dev/null 2>&1 ||
    python3 -m pip install --user --quiet --break-system-packages $PY_PACKAGES >/dev/null 2>&1 ||
    { echo "warning: pip could not install $PY_PACKAGES; the form-fill scripts print the exact command when first run." >&2
      failed+=("python packages"); }
fi

# npm libraries: bbs-quote-builder builds the quote .docx with docx, the pptx skill decks with
# pptxgenjs. Node's require() never looks in the global folder on its own, so NODE_PATH points
# there. VS Code on a Mac reads the login shell's environment at launch, hence ~/.zprofile.
if command -v npm >/dev/null 2>&1; then
  for pkg in docx pptxgenjs; do
    if npm ls -g "$pkg" >/dev/null 2>&1; then
      printf '[ok]      %s (npm global)\n' "$pkg"
    elif [[ $DRY_RUN -eq 1 ]]; then
      printf '[would]   %-22s %s\n' "$pkg" "npm install -g"
    else
      printf '[install] %-22s %s\n' "$pkg" "npm install -g"
      npm install -g "$pkg" >/dev/null 2>&1 || failed+=("$pkg")
    fi
  done
  NPM_ROOT="$(npm root -g 2>/dev/null)"
  NODE_LINE="export NODE_PATH=\"$NPM_ROOT\${NODE_PATH:+:\$NODE_PATH}\""
  if [[ -n "$NPM_ROOT" ]] && grep -qsF "$NODE_LINE" "$HOME/.zprofile"; then
    printf '[ok]      NODE_PATH includes %s\n' "$NPM_ROOT"
  elif [[ -z "$NPM_ROOT" ]]; then
    failed+=("NODE_PATH")
  elif [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "NODE_PATH" "add $NPM_ROOT in ~/.zprofile"
  else
    printf '[install] %-22s %s\n' "NODE_PATH" "add $NPM_ROOT in ~/.zprofile"
    printf '\n# BBS bootstrap: let node find the global docx/pptxgenjs\n%s\n' "$NODE_LINE" >> "$HOME/.zprofile"
  fi
fi

# The BBS plugins. Managed settings enable them and Claude Code installs them at session start,
# in the background, so a failed install is just an absent plugin. Installing from here shows
# Claude Code's own error. The list is every plugin in the marketplace's own marketplace.json -
# everyone gets every plugin (MANAGED-SETTINGS.md) - less any bbs-managed-settings.json sets to
# false, so nothing is copied into this script. A clone gets 120 s by default; give the
# installs below ten minutes. Claude Code's own later installs and updates get the same value
# from the managed settings' `env` (bbs-managed-settings.json, 2026-10-01), its one home, so
# the copy earlier versions of this script saved in ~/.zprofile is removed.
MARKETPLACE="bbs-claude-marketplace"
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000
TIMEOUT_LINE="export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000"
if grep -qsF "$TIMEOUT_LINE" "$HOME/.zprofile"; then
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS" "remove the saved copy from ~/.zprofile (managed settings set it)"
  else
    printf '[remove]  %-22s %s\n' "CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS" "saved copy in ~/.zprofile; managed settings set it now"
    grep -vF -e "$TIMEOUT_LINE" -e "# BBS bootstrap: give plugin clones ten minutes, not 120 s" \
      "$HOME/.zprofile" > "$HOME/.zprofile.bbs-tmp" && mv "$HOME/.zprofile.bbs-tmp" "$HOME/.zprofile"
  fi
fi
if ! command -v claude >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "BBS plugins" "after claude and jq are on PATH"
  else
    echo "[later]   the BBS plugins need claude and jq on PATH: open a new terminal and run this script again."
    failed+=("BBS plugins")
  fi
else
  mkt_dir() {
    claude plugin marketplace list --json 2>/dev/null |
      jq -r --arg m "$MARKETPLACE" '.[] | select(.name == $m) | .installLocation' 2>/dev/null
  }
  MKT_DIR="$(mkt_dir)"
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[would]   %-22s %s\n' "$MARKETPLACE" "$([[ -n "$MKT_DIR" ]] && echo update || echo add), then install every plugin in it"
  else
    if [[ -n "$MKT_DIR" ]]; then
      out="$(claude plugin marketplace update "$MARKETPLACE" 2>&1)"
    else
      out="$(claude plugin marketplace add "Black-Box-Safety/$MARKETPLACE" 2>&1)"
    fi || { echo "warning: could not add or update the $MARKETPLACE marketplace:" >&2
            printf '%s\n' "$out" | tail -n 5 | sed 's/^/          /' >&2
            failed+=("$MARKETPLACE marketplace"); }
    MKT_DIR="$(mkt_dir)"
    CATALOG="$MKT_DIR/.claude-plugin/marketplace.json"
    POLICY="$MKT_DIR/plugins/bbs-foundations/docs/bbs-managed-settings.json"
    if [[ -z "$MKT_DIR" || ! -f "$CATALOG" ]]; then
      echo "warning: the marketplace is not on this machine, so the plugin list cannot be read. Send this window to Parker." >&2
      failed+=("BBS plugins")
    else
      HAVE="$(claude plugin list --json 2>/dev/null |
        jq -r '.[] | select((.errors // []) | length == 0) | "\(.id)\t\(.installPath)"' 2>/dev/null)"
      BLOCKED=""
      [[ -f "$POLICY" ]] && BLOCKED="$(jq -r '.enabledPlugins | to_entries[] | select(.value == false) | .key' "$POLICY")"
      for id in $(jq -r --arg m "@$MARKETPLACE" '.plugins[].name + $m' "$CATALOG"); do
        if printf '%s\n' "$BLOCKED" | grep -qxF "$id"; then
          continue
        fi
        path="$(printf '%s\n' "$HAVE" | awk -F'\t' -v id="$id" '$1 == id { print $2; exit }')"
        if [[ -n "$path" && -d "$path" ]]; then
          printf '[ok]      %s\n' "$id"
          continue
        fi
        printf '[install] %s\n' "$id"
        if ! out="$(claude plugin install "$id" --scope user 2>&1)"; then
          echo "warning: $id did not install. Claude Code said:" >&2
          printf '%s\n' "$out" | tail -n 5 | sed 's/^/          /' >&2
          failed+=("$id")
        fi
      done
    fi
  fi
fi

echo ""
if [[ ${#failed[@]} -gt 0 ]]; then
  echo "Finished with ${#failed[@]} item(s) to install by hand: ${failed[*]}"
else
  echo "Done."
fi
echo "Quit Cursor or VS Code and the Claude Desktop app completely (Cmd+Q), reopen, then run /bbs-checkup in the Claude Code panel."
