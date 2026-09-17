# Rep workspace

`bbs-rep.code-workspace` is the standard VS Code **and Cursor** entry point for the quote
desk. Same file either way.

**First open (once per machine):** the editor will say the folder path is missing. Open the
file (File → Open File), replace `REPLACE-ON-FIRST-OPEN` with your OneDrive root, save,
then File → Open Workspace from File. Check Finder or File Explorer for the exact synced
name — do not guess.

Usual shapes (the middle folder name varies by how OneDrive was installed):

- **Windows:** `C:/Users/<you>/Black Box Safety - MASTER`
- **Mac:** `/Users/<you>/Library/CloudStorage/OneDrive-BlackBoxSafety,Inc/Black Box Safety - MASTER`

Full walk-through: `docs/REP-SETUP.md` (VS Code on Windows) or `docs/CURSOR-SETUP.md`
(Cursor, including Mac). Screenshots will be pinned in the Teams sales channel.

Four extensions are recommended on open — accept them (Claude Code, PDF viewer, Excel
viewer, file icons). Nothing else. Format-on-save stays off so customer RFQs are not
rewritten; `FILLED/` stays searchable on purpose.

The desk folder's `CLAUDE.md` (stamped from `workspace/DESK-CLAUDE-template.md`) is what
makes Claude sessions in this workspace know the folder rules, the landmines, and the
precedent-first habit. Cursor also needs `.cursor/rules/bbs-invariants.mdc` at the desk
root — Parker stamps that from this repo as part of first-deployment.
