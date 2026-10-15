#!/usr/bin/env python3
"""Discover BBS folders on this machine and write VS Code workspaces (Cursor opens them too).

Teammates request workspaces from what is actually on disk — never from guessed
paths. Named recipes (quote desk, web, admin) fill in when their folders exist.
Anyone can also ask for a custom workspace of folders they already have.

    python3 scripts/bbs-workspaces.py discover
    python3 scripts/bbs-workspaces.py request --yes --install-desktop
    python3 scripts/bbs-workspaces.py request --custom "Field work" --folder ~/bbs-shopify
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
DEST = HOME / "bbs-workspaces"
DESKTOP_DIR = HOME / "Desktop" / "BBS Workspaces"
DESKTOP_APP = HOME / "Desktop" / "BBS Workspaces.app"
LABELS = {
    "bbs-rep": "Quote Desk",
    "bbs-web": "Web",
    "bbs-admin": "Admin",
}


def marketplace_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    if (here / "workspace" / "catalog.json").is_file():
        return here
    plugin = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin:
        cand = Path(plugin).resolve().parent.parent
        if (cand / "workspace" / "catalog.json").is_file():
            return cand
    for cand in (
        HOME / ".claude" / "plugins" / "marketplaces" / "bbs-claude-marketplace",
        HOME / "bbs-claude-marketplace",
    ):
        if (cand / "workspace" / "catalog.json").is_file():
            return cand
    sys.exit("Cannot find bbs-claude-marketplace (workspace/catalog.json missing).")


def load_catalog(root: Path) -> dict:
    return json.loads((root / "workspace" / "catalog.json").read_text(encoding="utf-8"))


def search_roots(extra: list[str]) -> list[Path]:
    roots = [
        HOME,
        HOME / "bbs",
        HOME / "Documents",
        HOME / "src",
        HOME / "dev",
        HOME / "code",
        HOME / "Projects",
    ]
    cloud = HOME / "Library" / "CloudStorage"
    if cloud.is_dir():
        roots.extend(sorted(cloud.iterdir()))
    for name in ("OneDrive", "OneDrive - Black Box Safety, Inc"):
        p = HOME / name
        if p.is_dir():
            roots.append(p)
    for item in extra:
        p = Path(item).expanduser()
        if p.is_dir():
            roots.append(p)
    out, seen = [], set()
    for r in roots:
        try:
            r = r.resolve()
        except OSError:
            continue
        if r in seen or not r.is_dir():
            continue
        seen.add(r)
        out.append(r)
    return out


def find_named(roots: list[Path], names: list[str]) -> Path | None:
    for root in roots:
        for name in names:
            cand = root / name
            if cand.is_dir():
                return cand
    return None


def find_onedrive_master(roots: list[Path]) -> Path | None:
    marker = "Black Box Safety - MASTER"
    for root in roots:
        direct = root / marker
        if direct.is_dir():
            return direct
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir() and child.name == marker:
                return child
            nested = child / marker
            if nested.is_dir():
                return nested
    return None


def discover(root: Path, repos_override: str | None, onedrive_override: str | None) -> dict[str, str]:
    catalog = load_catalog(root)
    extra = []
    if repos_override:
        extra.append(repos_override)
    if onedrive_override:
        extra.append(onedrive_override)
        extra.append(str(Path(onedrive_override).parent))
    roots = search_roots(extra)
    found: dict[str, str] = {}
    for item in catalog["named"]:
        hit = find_named(roots, item["names"])
        if hit is not None:
            found[item["id"]] = str(hit)
    master = Path(onedrive_override).expanduser() if onedrive_override else find_onedrive_master(roots)
    if master is not None and master.is_dir():
        found["onedrive_master"] = str(master.resolve())
        desk = master / "Customers" / "State of CA Agencies"
        if desk.is_dir():
            found["quote_desk"] = str(desk)
    # The clone that is running this script is the marketplace, even if an older
    # folder also named bbs-claude-marketplace sits in $HOME.
    found["bbs-claude-marketplace"] = str(root)
    return found


def recipe_ready(recipe: dict, found: dict[str, str]) -> tuple[bool, list[str], list[str]]:
    missing_req = [k for k in recipe.get("required", []) if k not in found]
    missing_opt = [k for k in recipe.get("optional", []) if k not in found]
    return not missing_req, missing_req, missing_opt


def resolve_template_path(raw: str, found: dict[str, str], marketplace: Path) -> str | None:
    if raw == "..":
        return found.get("bbs-claude-marketplace") or str(marketplace)
    if raw == "REPLACE-ONEDRIVE-ROOT":
        return found.get("onedrive_master")
    if raw.startswith("REPLACE-ON-FIRST-OPEN"):
        return found.get("quote_desk")
    if raw.startswith("REPLACE-REPOS-ROOT/"):
        name = raw.split("/", 1)[1]
        return found.get(name)
    return None


def apply_left_sidebar(data: dict) -> dict:
    settings = data.setdefault("settings", {})
    settings["workbench.sideBar.location"] = "left"
    settings["workbench.activityBar.location"] = "default"
    return data


def user_editor_settings_paths() -> list[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        support = home / "Library" / "Application Support"
        return [
            support / "Cursor" / "User" / "settings.json",
            support / "Code" / "User" / "settings.json",
        ]
    if sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        return [
            appdata / "Cursor" / "User" / "settings.json",
            appdata / "Code" / "User" / "settings.json",
        ]
    return [
        home / ".config" / "Cursor" / "User" / "settings.json",
        home / ".config" / "Code" / "User" / "settings.json",
    ]


def write_user_settings(path: Path, text: str) -> None:
    """Back up the rep's User settings.json to settings.json.bak, then write it."""
    backup = path.with_name(path.name + ".bak")
    shutil.copy2(path, backup)
    path.write_text(text, encoding="utf-8")
    print(f"pinned left sidebar in {path} (previous copy: {backup})")


def pin_user_editor_sidebar() -> None:
    """Keep the primary sidebar on the left in Cursor / VS Code User settings.

    Opt-in only (request --pin-user-settings): this edits the rep's own User
    settings, not a BBS file, so it never runs by default and always leaves a
    settings.json.bak beside the file before changing it.
    """
    for path in user_editor_settings_paths():
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            updated = raw
            for key, value in (
                ("workbench.sideBar.location", "left"),
                ("workbench.activityBar.location", "default"),
            ):
                pattern = rf'"{re.escape(key)}"\s*:\s*"[^"]*"'
                replacement = f'"{key}": "{value}"'
                if re.search(pattern, updated):
                    updated = re.sub(pattern, replacement, updated, count=1)
                else:
                    updated = re.sub(
                        r"\{",
                        "{\n    " + replacement + ",",
                        updated,
                        count=1,
                    )
            if updated != raw:
                write_user_settings(path, updated)
            continue
        if not isinstance(data, dict):
            continue
        changed = False
        for key, value in (
            ("workbench.sideBar.location", "left"),
            ("workbench.activityBar.location", "default"),
        ):
            if data.get(key) != value:
                data[key] = value
                changed = True
        apply = list(data.get("workbench.settings.applyToAllProfiles") or [])
        for key in ("workbench.sideBar.location", "workbench.activityBar.location"):
            if key not in apply:
                apply.append(key)
                changed = True
        if apply:
            data["workbench.settings.applyToAllProfiles"] = apply
        if not changed:
            continue
        write_user_settings(path, json.dumps(data, indent=4) + "\n")


def write_recipe(root: Path, recipe: dict, found: dict[str, str], dest: Path) -> Path | None:
    template = root / "workspace" / recipe["template"]
    data = json.loads(template.read_text(encoding="utf-8"))
    folders = []
    for folder in data.get("folders", []):
        resolved = resolve_template_path(folder["path"], found, root)
        if resolved is None:
            continue
        entry = dict(folder)
        entry["path"] = resolved
        folders.append(entry)
    required_ids = set(recipe.get("required", []))
    # Drop the workspace if a required folder did not resolve into the file.
    if required_ids and not folders:
        return None
    data["folders"] = folders
    apply_left_sidebar(data)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / recipe["template"]
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return out


def write_custom(name: str, folders: list[str], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-") or "custom"
    entries = []
    for folder in folders:
        p = Path(folder).expanduser().resolve()
        if not p.is_dir():
            sys.exit(f"Not a folder on this machine: {folder}")
        entries.append({"name": p.name, "path": str(p)})
    data = apply_left_sidebar(
        {
            "folders": entries,
            "settings": {
                "window.title": f"{name} — ${{activeEditorShort}}",
            },
        }
    )
    out = dest / f"bbs-{slug}.code-workspace"
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return out


def quote_sh(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def write_unix_command(name: str, target: Path, desktop: Path) -> None:
    quoted = quote_sh(str(target))
    path = desktop / f"Open {name}.command"
    path.write_text(
        f"#!/bin/zsh\nopen -a 'Visual Studio Code' {quoted} 2>/dev/null || open -a Cursor {quoted}\n",
        encoding="utf-8",
        newline="\n",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_windows_bat(name: str, target: Path, desktop: Path) -> None:
    bat = desktop / f"Open {name}.bat"
    bat.write_text(
        "@echo off\n"
        f'where code >nul 2>&1 && start "" code "{target}" && exit /b 0\n'
        f'where cursor >nul 2>&1 && start "" cursor "{target}" && exit /b 0\n'
        f'start "" "{target}"\n',
        encoding="ascii",
        newline="\r\n",
    )


def set_mac_icon(png: Path, target: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="bbs-set-icon-") as tmp:
        _set_mac_icon(png, target, Path(tmp) / "bbs-set-icon.applescript")


def _set_mac_icon(png: Path, target: Path, dest_tmp_script: Path) -> None:
    dest_tmp_script.write_text(
        "use framework \"AppKit\"\n"
        "use scripting additions\n"
        "on run argv\n"
        "  set imgPath to item 1 of argv\n"
        "  set targetPath to item 2 of argv\n"
        "  set img to current application's NSImage's alloc's initWithContentsOfFile:imgPath\n"
        "  if img is missing value then error \"icon png did not load\"\n"
        "  set ok to current application's NSWorkspace's sharedWorkspace()'s "
        "setIcon:img forFile:targetPath options:0\n"
        "  if (ok as boolean) is false then error \"setIcon failed\"\n"
        "end run\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        ["osascript", str(dest_tmp_script), str(png), str(target)],
        check=True,
        capture_output=True,
        text=True,
    )


def applescript_list(items: list[str]) -> str:
    inner = ", ".join('"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"' for s in items)
    return "{" + inner + "}"


def label_for(ws: Path) -> str:
    return LABELS.get(ws.stem, ws.stem.replace("bbs-", "").replace("-", " ").title())


def make_icns(png: Path, icns: Path) -> None:
    iconset = icns.with_suffix(".iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    for size in (16, 32, 64, 128, 256, 512, 1024):
        out = iconset / f"icon_{size}x{size}.png"
        subprocess.run(
            ["sips", "-z", str(size), str(size), str(png), "--out", str(out)],
            check=True,
            capture_output=True,
        )
        if size <= 512:
            out2 = iconset / f"icon_{size}x{size}@2x.png"
            subprocess.run(
                ["sips", "-z", str(size * 2), str(size * 2), str(png), "--out", str(out2)],
                check=True,
                capture_output=True,
            )
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)],
        check=True,
        capture_output=True,
    )
    shutil.rmtree(iconset)


def compile_chooser(dest: Path, desktop: Path, icon: Path | None, pairs: list[tuple[str, Path]]) -> None:
    names = [n for n, _ in pairs]
    files = [str(p) for _, p in pairs]
    applescript = (
        f"set workspaceNames to {applescript_list(names)}\n"
        f"set workspaceFiles to {applescript_list(files)}\n"
        "if (count of workspaceNames) is 0 then\n"
        "  display alert \"No BBS workspaces yet\" message "
        "\"Run /bbs-workspaces in Claude Code.\"\n"
        "  return\n"
        "end if\n"
        "set chosen to choose from list workspaceNames with title \"BBS Workspaces\" "
        "with prompt \"Open a workspace:\" default items "
        "{item 1 of workspaceNames} OK button name \"Open\"\n"
        "if chosen is false then return\n"
        "set chosenName to item 1 of chosen\n"
        "repeat with i from 1 to count of workspaceNames\n"
        "  if item i of workspaceNames is chosenName then\n"
        "    set targetFile to item i of workspaceFiles\n"
        "    exit repeat\n"
        "  end if\n"
        "end repeat\n"
        "do shell script \"open -a \" & quoted form of \"Visual Studio Code\" & \" \" & "
        "quoted form of targetFile & \" || open -a Cursor \" & quoted form of targetFile\n"
    )
    tmp = dest / "_chooser.applescript"
    tmp.write_text(applescript, encoding="utf-8", newline="\n")
    app = desktop / "Choose a workspace.app"
    if app.exists():
        shutil.rmtree(app)
    subprocess.run(["osacompile", "-o", str(app), str(tmp)], check=True, capture_output=True)
    tmp.unlink(missing_ok=True)
    icns = dest / "bbs-workspace.icns"
    if icon and icon.is_file() and shutil.which("iconutil") and shutil.which("sips"):
        make_icns(icon, icns)
        applet_icns = app / "Contents" / "Resources" / "applet.icns"
        if icns.is_file() and applet_icns.parent.is_dir():
            shutil.copy2(icns, applet_icns)
    if icon and icon.is_file():
        set_mac_icon(icon, app)
    if DESKTOP_APP.exists():
        shutil.rmtree(DESKTOP_APP)
    shutil.copytree(app, DESKTOP_APP)
    if icon and icon.is_file():
        set_mac_icon(icon, DESKTOP_APP)
        set_mac_icon(icon, desktop)


def install_desktop(root: Path, dest: Path, written: list[tuple[str, Path]]) -> None:
    desktop = DESKTOP_DIR
    desktop.mkdir(parents=True, exist_ok=True)
    icon = root / "workspace" / "assets" / "bbs-workspace-icon.png"
    pairs = []
    for ws in sorted(dest.glob("*.code-workspace")):
        pairs.append((label_for(ws), ws))
    for name, path in pairs or written:
        if sys.platform == "darwin":
            write_unix_command(name, path, desktop)
        else:
            write_windows_bat(name, path, desktop)
    (desktop / "README.txt").write_text(
        "BBS workspaces\n"
        "==============\n\n"
        "Mac: double-click BBS Workspaces.app on the Desktop, or Choose a workspace.app here.\n"
        "Windows: double-click an Open *.bat file.\n\n"
        f"Filled workspace files: {dest}\n"
        "To add another workspace from folders on this computer:\n"
        "  /bbs-workspaces\n",
        encoding="utf-8",
    )
    if sys.platform == "darwin":
        compile_chooser(dest, desktop, icon if icon.is_file() else None, pairs or written)
        subprocess.run(["open", str(desktop)], check=False)


def cmd_discover(args: argparse.Namespace) -> None:
    root = marketplace_root()
    found = discover(root, args.repos, args.onedrive)
    catalog = load_catalog(root)
    payload = {"found": found, "recipes": []}
    for recipe in catalog["recipes"]:
        ready, missing_req, missing_opt = recipe_ready(recipe, found)
        payload["recipes"].append({
            "id": recipe["id"],
            "name": recipe["name"],
            "use": recipe["use"],
            "ready": ready,
            "missing_required": missing_req,
            "missing_optional": missing_opt,
        })
    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    print("Folders on this machine")
    if not found:
        print("  (none of the known BBS folders)")
    for key, path in sorted(found.items()):
        print(f"  {key:24} {path}")
    print("\nNamed workspaces")
    for rec in payload["recipes"]:
        mark = "ready" if rec["ready"] else "not yet — missing " + ", ".join(rec["missing_required"])
        extra = f" (optional missing: {', '.join(rec['missing_optional'])})" if rec["missing_optional"] else ""
        print(f"  {rec['id']:8} {rec['name']:18} {mark}{extra}")
    print("\nRequest what is ready:")
    print("  python3 scripts/bbs-workspaces.py request --yes --install-desktop")
    print("Or a custom workspace from folders you already have:")
    print("  python3 scripts/bbs-workspaces.py request --custom \"Name\" --folder /path")


def cmd_request(args: argparse.Namespace) -> None:
    root = marketplace_root()
    dest = Path(args.dest).expanduser() if args.dest else DEST
    found = discover(root, args.repos, args.onedrive)
    catalog = load_catalog(root)
    written: list[tuple[str, Path]] = []

    if args.custom:
        if not args.folder:
            sys.exit("--custom needs one or more --folder paths that exist on this computer.")
        out = write_custom(args.custom, args.folder, dest)
        written.append((args.custom, out))
        print(f"wrote {out}")
    else:
        wanted = args.ids.split(",") if args.ids else [r["id"] for r in catalog["recipes"]]
        wanted = [w.strip() for w in wanted if w.strip()]
        recipes = {r["id"]: r for r in catalog["recipes"]}
        for rid in wanted:
            recipe = recipes.get(rid)
            if recipe is None:
                sys.exit(f"Unknown workspace id {rid!r}. Known: {', '.join(recipes)}")
            ready, missing, _opt = recipe_ready(recipe, found)
            if not ready:
                print(f"skip {rid}: this machine does not have {', '.join(missing)}")
                continue
            if not args.yes and not args.ids:
                # Non-interactive default is --yes when Claude runs the command;
                # humans passing no flags still get every ready recipe.
                pass
            out = write_recipe(root, recipe, found, dest)
            if out is None:
                print(f"skip {rid}: template did not resolve")
                continue
            written.append((recipe["name"].replace("BBS ", ""), out))
            print(f"wrote {out}")

    if not written:
        sys.exit("Nothing to write. Run discover, clone the missing repos, or pass --custom --folder.")
    if args.pin_user_settings:
        pin_user_editor_sidebar()
    if args.install_desktop:
        install_desktop(root, dest, written)
        print(f"Desktop launchers: {DESKTOP_DIR}")
        if sys.platform == "darwin":
            print(f"Chooser app: {DESKTOP_APP}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onedrive", help="Override OneDrive MASTER path if discovery misses it")
    parser.add_argument("--repos", help="Extra directory to search for bbs-* clones")
    parser.add_argument("--dest", help=f"Where to write filled workspaces (default {DEST})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_disc = sub.add_parser("discover", help="List BBS folders on this machine")
    p_disc.add_argument("--json", action="store_true")
    p_disc.set_defaults(func=cmd_discover)

    p_req = sub.add_parser("request", help="Write workspaces from folders that exist here")
    p_req.add_argument("--yes", action="store_true", help="Write every named workspace that is ready")
    p_req.add_argument("--ids", help="Comma-separated recipe ids (rep,web,admin)")
    p_req.add_argument("--custom", help="Name of a custom workspace")
    p_req.add_argument("--folder", action="append", default=[], help="Folder to include (repeatable)")
    p_req.add_argument("--install-desktop", action="store_true")
    p_req.add_argument(
        "--pin-user-settings",
        action="store_true",
        help="Also pin the sidebar left in your own Cursor / VS Code User settings.json "
        "(writes settings.json.bak first). Off by default.",
    )
    p_req.set_defaults(func=cmd_request)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
