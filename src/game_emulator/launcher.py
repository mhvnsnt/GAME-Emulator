"""Explicit launch handoff to an installed RetroArch/libretro runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any


def get_game(library: Path, sha256: str) -> dict[str, Any]:
    root = library.expanduser().resolve(strict=True)
    database = root / "library.sqlite3"
    if not database.is_file():
        raise ValueError("library catalog does not exist")
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM games WHERE sha256 = ?", (sha256.lower(),)).fetchone()
    if row is None:
        raise ValueError("SHA-256 was not found in this library")
    game = dict(row)
    stored_path = Path(game["stored_path"])
    if stored_path.is_symlink():
        raise ValueError("cataloged content may not be a symbolic link")
    content = stored_path.resolve(strict=True)
    allowed_root = (root / "files").resolve(strict=True)
    if content != allowed_root and allowed_root not in content.parents:
        raise ValueError("catalog entry points outside the library files directory")
    if not content.is_file() or content.is_symlink():
        raise ValueError("cataloged content is not a regular file")
    digest = hashlib.sha256()
    with content.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != sha256.lower():
        raise ValueError("stored file hash no longer matches the catalog")
    game["stored_path"] = str(content)
    return game


def build_command(frontend: str, core: Path, content: Path) -> list[str]:
    return [frontend, "-L", str(core), str(content)]


def launch_game(
    library: Path, sha256: str, *, frontend: str, core: Path,
    system_override: str | None = None, dry_run: bool = False,
) -> dict[str, Any]:
    game = get_game(library, sha256)
    system = system_override.strip() if system_override else game["system"]
    if (
        ("needs confirmation" in system.lower() or "needs confirmation" in game["system"].lower())
        and not system_override
    ):
        raise ValueError("ambiguous system: supply --system to confirm the target console")
    resolved_frontend = shutil.which(frontend)
    if resolved_frontend is None and Path(frontend).is_file():
        resolved_frontend = str(Path(frontend).resolve())
    if resolved_frontend is None:
        raise ValueError("RetroArch executable was not found; install it or pass its full path")
    core_path = core.expanduser().resolve(strict=True)
    if not core_path.is_file():
        raise ValueError("libretro core must be a file")
    content = Path(game["stored_path"])
    command = build_command(resolved_frontend, core_path, content)
    result: dict[str, Any] = {
        "system": system,
        "filename": game["filename"],
        "sha256": game["sha256"],
        "command": command,
        "dry_run": dry_run,
        "status": "command_ready",
    }
    if not dry_run:
        process = subprocess.Popen(command, shell=False, cwd=str(Path(library).expanduser().resolve()))
        result.update({"status": "launched", "pid": process.pid})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicitly launch a cataloged file using installed RetroArch")
    parser.add_argument("--library", type=Path, default=Path.home() / "GAME-Emulator-Library")
    parser.add_argument("--sha256", required=True, help="hash shown by game-emulator list")
    parser.add_argument("--core", type=Path, required=True, help="installed libretro core shared library")
    parser.add_argument("--frontend", default="retroarch", help="RetroArch executable or full path")
    parser.add_argument("--system", help="explicitly confirm/override an ambiguous system label")
    parser.add_argument("--dry-run", action="store_true", help="validate paths and print the launch command")
    args = parser.parse_args()
    try:
        print(json.dumps(launch_game(args.library, args.sha256, frontend=args.frontend,
                                     core=args.core, system_override=args.system,
                                     dry_run=args.dry_run), indent=2))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
