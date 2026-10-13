# Learnings ledger — `docs/LEARNINGS.md`

The layer between rules (`CLAUDE.md`, standards, role docs) and state (handoffs, the board). It holds
what a session *learned*: the pattern that worked, the assumption the data corrected, the alternative
considered and parked, the process miss. Without it that knowledge dies with the session.

## Rules (the block at the top of the file)
1. **Read at start, append at end.** Every owner reads its lane's section and the cross-cutting section
   at session start, and appends one dated, lane-tagged entry at session end. The steward writes the
   governance entries.
2. **Append, never rewrite.** A superseded learning gets a strikethrough and a pointer to what replaced
   it. The wrong turns are half the value.
3. **Concrete or nothing.** Name the file, the number, the cardinality. A vague entry is worse than none.
4. **One canonical file** in the home repo for cross-cutting and governance learnings; a repo may keep
   its own `docs/LEARNINGS.md` for surface-specific entries.

## Entry shape
```markdown
## <Lane or "Cross-cutting">

### L-<nnn> · <one-line lesson, stated as a rule> (<date>, <owner>)
<Two to six lines: what happened, what the evidence was, what to do differently. file:line where it applies.>
```
