#!/bin/sh
# PostToolUse entry for the quote desk (Read|Write|Edit|MultiEdit): decide in the shell whether
# desk-context needs to run at all, then run it once (pwsh 7, else Windows PowerShell 5.1, else
# python3), with the hook input passed through unchanged. Always exits 0.
#
# Why a shell step first: the matcher includes Read (desk memory's first touch), and Claude
# reads files all day, most of them nowhere near the desk. Starting an interpreter for each one
# costs hundreds of milliseconds. So:
#   1. Only the values of "file_path", "session_id" and "tool_name" are read (one grep over the
#      input), never the whole input. A session whose cwd is inside the tree, or a Read of a file
#      whose text says "by agency", is not a desk touch.
#   2. A path that does not name the tree ("by Agency", any case) exits here.
#   3. A Read in a folder desk-memory has already handled this session exits here: desk-memory
#      writes <temp>/bbs-desk-memory/<session>--dir--<folder key> once it has, and this checks for
#      that file. The key is the folder below "by Agency", every run of characters other than
#      A-Z a-z 0-9 turned into one "-", with any "-" at either end dropped (desk-memory.py
#      dir_marker, desk-memory.ps1 Get-DirMarker: change all three together). A Write or Edit
#      always runs, because desk-context's first-write reminder is about writes.
# A marker this cannot find (another temp folder, a path with non-ASCII characters) only means
# the interpreter runs and decides; it never hides a note.
# Tested by hooks/tests/desk_memory_parity.py (check_entry).

case $0 in */*) H=${0%/*} ;; *) H=. ;; esac
IN=$(cat)

FP= SID= TOOL=
F=$(printf '%s' "$IN" | grep -o -E '"(file_path|session_id|tool_name)"[[:space:]]*:[[:space:]]*"[^"]*"')
while IFS= read -r l; do
  v=${l#*:}
  v=${v#"${v%%[!	 ]*}"}
  v=${v#\"}
  v=${v%\"}
  case "$l" in
    '"file_path"'*) [ -n "$FP" ] || FP=$v ;;
    '"session_id"'*) [ -n "$SID" ] || SID=$v ;;
    '"tool_name"'*) [ -n "$TOOL" ] || TOOL=$v ;;
  esac
done <<EOF
$F
EOF

case "$FP" in
  *[Bb][Yy]\ [Aa][Gg][Ee][Nn][Cc][Yy]*) ;;
  *) exit 0 ;;
esac

if [ "$TOOL" = Read ] && [ -n "$SID" ]; then
  T=${TMPDIR:-${TEMP:-${TMP:-/tmp}}}
  rest=${FP#*[Bb][Yy]\ [Aa][Gg][Ee][Nn][Cc][Yy]}
  dir=${rest%[\\/]*}
  K=$(printf '%s\n%s\n' "$SID" "$dir" | sed 's/[^A-Za-z0-9][^A-Za-z0-9]*/-/g; 2s/^-//; 2s/-$//')
  { IFS= read -r S; IFS= read -r D; } <<EOF
$K
EOF
  [ -e "$T/bbs-desk-memory/$S--dir--$D" ] && exit 0
fi

if command -v pwsh >/dev/null 2>&1; then
  printf '%s' "$IN" | pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/desk-context.ps1"
elif command -v powershell >/dev/null 2>&1; then
  printf '%s' "$IN" | powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$H/desk-context.ps1"
elif command -v python3 >/dev/null 2>&1; then
  printf '%s' "$IN" | python3 "$H/desk-context.py"
fi
exit 0
