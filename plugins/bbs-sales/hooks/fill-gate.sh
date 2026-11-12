#!/bin/sh
# PreToolUse entry (Bash) for the bbs-fill launcher: decide in the shell whether fill-gate needs
# to run at all, then run it once (pwsh 7, else Windows PowerShell 5.1, else python3), with the
# hook input passed through unchanged. Always exits 0 and prints only what the interpreter prints.
#
# Why a shell step first: this entry sees every Bash call Claude makes. A command that does not
# mention bbs-fill cannot be approved by fill-gate, so it ends here without starting an
# interpreter. This step can only skip the hook, never approve: a miss costs a prompt.
# With no interpreter at all it prints nothing, so the call goes to the normal permission flow.
# Spec: docs/superpowers/specs/2026-11-11-bbs-fill-into-bbs-sales.md, section 3.7.

case $0 in */*) H=${0%/*} ;; *) H=. ;; esac
IN=$(cat)

case $IN in
  *bbs-fill*) ;;
  *) exit 0 ;;
esac

if command -v pwsh >/dev/null 2>&1; then
  printf '%s' "$IN" | pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/fill-gate.ps1"
elif command -v powershell >/dev/null 2>&1; then
  printf '%s' "$IN" | powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/fill-gate.ps1"
elif command -v python3 >/dev/null 2>&1; then
  printf '%s' "$IN" | python3 "$H/fill-gate.py"
fi
exit 0
