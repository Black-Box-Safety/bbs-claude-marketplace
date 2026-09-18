#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the BBS Claude marketplace.
#
# The base image already ships Python 3.12, PyYAML, Node 22, and git, which is
# all that scripts/check_marketplace.py and the CLAUDE.md checker need. This
# script adds the third-party libraries the per-skill scripts import (pypdf and
# PyMuPDF for the CA form packets, the Anthropic SDK for model refresh) and the
# Claude Code CLI that `claude plugin validate` runs. Everything here is safe to
# run repeatedly.
set -euo pipefail

echo "==> Python skill-script dependencies"
# --break-system-packages: install into the user site on the PEP 668 base image.
python3 -m pip install --user --break-system-packages --upgrade \
  "pyyaml==6.0.1" \
  "pypdf==5.1.0" \
  "PyMuPDF==1.24.14" \
  "anthropic==0.39.0"

echo "==> Claude Code CLI (for 'claude plugin validate')"
# The image's global npm prefix is not writable, so keep the CLI in a
# user-owned prefix. Pass the prefix through the environment for this one
# command rather than `npm config set` — a persisted prefix in ~/.npmrc
# conflicts with the image's nvm and prints a warning on every login shell.
NPM_CONFIG_PREFIX="$HOME/.npm-global" npm install -g @anthropic-ai/claude-code

BASHRC="$HOME/.bashrc"
LINE='export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"'
if ! grep -qF "$LINE" "$BASHRC" 2>/dev/null; then
  echo "$LINE" >> "$BASHRC"
fi
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

echo "==> Versions"
python3 --version
python3 -c "import yaml, pypdf, fitz, anthropic; print('pyyaml', yaml.__version__, '| pypdf', pypdf.__version__, '| pymupdf', fitz.__version__, '| anthropic', anthropic.__version__)"
claude --version

echo "==> Bootstrap complete"
