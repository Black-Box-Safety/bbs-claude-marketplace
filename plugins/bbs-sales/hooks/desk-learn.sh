#!/bin/sh
# desk-learn entry (PostToolUse Bash|Write|Edit|MultiEdit, and Stop): decide in the shell whether
# desk-learn needs to run at all, then run it once (pwsh 7, else Windows PowerShell 5.1, else
# python3), with the hook input passed through unchanged. Always exits 0 and prints only what the
# interpreter prints. It only reminds; nothing here can block or approve.
#
# Why a shell step first: this entry sees every Bash and file write Claude makes, nearly all of them
# nowhere near a customer desk. So:
#   Stop         runs the interpreter only when this session's ledger file exists (desk-learn writes
#                <temp>/bbs-desk-learn/<session>.ledger when it first reminds; the session key is every
#                run of characters other than A-Z a-z 0-9 turned into one "-", ends trimmed:
#                desk-learn.py safe(), desk-learn.ps1 Get-Safe).
#   PostToolUse  runs the interpreter only when the input mentions the tree ("by Agency"), Sentinel,
#                rfq_record, desk_memory or lessons.md, any case. A wrong guess costs one interpreter start,
#                never a reminder.
# With no interpreter at all it prints nothing.

case $0 in */*) H=${0%/*} ;; *) H=. ;; esac
IN=$(cat)

if printf '%s' "$IN" | grep -q -E '"hook_event_name"[[:space:]]*:[[:space:]]*"Stop"'; then
  SID=$(printf '%s' "$IN" | grep -o -E '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1)
  SID=${SID#*:}
  SID=${SID#"${SID%%[!	 ]*}"}
  SID=${SID#\"}
  SID=${SID%\"}
  [ -n "$SID" ] || exit 0
  T=${TMPDIR:-${TEMP:-${TMP:-/tmp}}}
  K=$(printf '%s\n' "$SID" | sed 's/[^A-Za-z0-9][^A-Za-z0-9]*/-/g; s/^-//; s/-$//')
  [ -e "$T/bbs-desk-learn/$K.ledger" ] || exit 0
else
  printf '%s' "$IN" | grep -q -i -E 'by agency|sentinel|rfq_record|desk_memory|lessons\.md' || exit 0
fi

if command -v pwsh >/dev/null 2>&1; then
  printf '%s' "$IN" | pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/desk-learn.ps1"
elif command -v powershell >/dev/null 2>&1; then
  printf '%s' "$IN" | powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/desk-learn.ps1"
elif command -v python3 >/dev/null 2>&1; then
  printf '%s' "$IN" | python3 "$H/desk-learn.py"
fi
exit 0
