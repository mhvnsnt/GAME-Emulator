"""Local-first game-file ingestion, system classification, hashing and deduplication."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Extensions are cataloged as opaque files. This module never unpacks or executes them.
EXTENSIONS: dict[str, str] = {
    ".gba": "Nintendo Game Boy Advance", ".gbc": "Nintendo Game Boy Color",
    ".gb": "Nintendo Game Boy", ".nes": "Nintendo NES", ".fds": "Nintendo Famicom Disk System",
    ".sfc": "Nintendo SNES", ".smc": "Nintendo SNES", ".n64": "Nintendo 64",
    ".z64": "Nintendo 64", ".v64": "Nintendo 64", ".nds": "Nintendo DS",
    ".3ds": "Nintendo 3DS", ".cia": "Nintendo 3DS", ".cxi": "Nintendo 3DS",
    ".gcm": "Nintendo GameCube", ".wbfs": "Nintendo Wii", ".wud": "Nintendo Wii U",
    ".wux": "Nintendo Wii U", ".nsp": "Nintendo Switch", ".xci": "Nintendo Switch",
    ".dol": "Nintendo GameCube / Wii executable", ".wad": "Nintendo Wii / WiiWare",
    ".iso": "Disc image (system needs confirmation)", ".bin": "Disc/binary image (system needs confirmation)",
    ".cue": "Disc image descriptor", ".chd": "Compressed disc image",
    ".cso": "Compressed PlayStation Portable disc", ".pbp": "PlayStation Portable package",
    ".pkg": "Console package (system needs confirmation)", ".rap": "PlayStation 3 license file",
    ".ird": "PlayStation 3 disc metadata", ".xiso": "Original Xbox disc image",
    ".xbe": "Original Xbox executable", ".xex": "Xbox 360 executable",
    ".god": "Xbox 360 Games on Demand package", ".elf": "Console executable (system needs confirmation)",
    ".app": "Console application (system needs confirmation)", ".tik": "Console ticket (system needs confirmation)",
}
SYSTEM_ALIASES = {
    "gba": "Nintendo Game Boy Advance", "gameboy advance": "Nintendo Game Boy Advance",
    "gbc": "Nintendo Game Boy Color", "gameboy color": "Nintendo Game Boy Color",
    "game boy": "Nintendo Game Boy", "gameboy": "Nintendo Game Boy",
    "nes": "Nintendo NES", "famicom": "Nintendo NES", "snes": "Nintendo SNES",
    "super nintendo": "Nintendo SNES", "n64": "Nintendo 64", "nintendo 64": "Nintendo 64",
    "gamecube": "Nintendo GameCube", "game cube": "Nintendo GameCube", "gc": "Nintendo GameCube",
    "wii": "Nintendo Wii", "wiiu": "Nintendo Wii U", "wii u": "Nintendo Wii U",
    "switch": "Nintendo Switch", "nintendo switch": "Nintendo Switch", "nds": "Nintendo DS",
    "ds": "Nintendo DS", "3ds": "Nintendo 3DS",
    "ps1": "Sony PlayStation", "psx": "Sony PlayStation", "playstation 1": "Sony PlayStation",
    "playstation": "Sony PlayStation", "sony playstation": "Sony PlayStation", "psone": "Sony PlayStation", "ps2": "Sony PlayStation 2", "playstation 2": "Sony PlayStation 2",
    "ps3": "Sony PlayStation 3", "playstation 3": "Sony PlayStation 3",
    "psp": "Sony PlayStation Portable", "ps vita": "Sony PlayStation Vita",
    "xbox": "Microsoft Xbox", "original xbox": "Microsoft Xbox", "xbox 360": "Microsoft Xbox 360",
    "xbox one": "Microsoft Xbox One", "xbox series": "Microsoft Xbox Series",
    "3do": "3DO", "dreamcast": "Sega Dreamcast", "saturn": "Sega Saturn",
    "genesis": "Sega Genesis / Mega Drive", "megadrive": "Sega Genesis / Mega Drive",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_system(path: Path, explicit_system: str | None = None) -> str:
    """Classify content without guessing when an extension is shared by multiple systems."""
    if explicit_system and explicit_system.strip():
        normalized = " ".join(explicit_system.lower().replace("_", " ").replace("-", " ").split())
        return SYSTEM_ALIASES.get(normalized, explicit_system.strip())
    for part in reversed(path.parts[:-1]):
        normalized = " ".join(part.lower().replace("_", " ").replace("-", " ").split())
        for alias, system in sorted(SYSTEM_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            if normalized == alias or alias in normalized:
                return system
    return EXTENSIONS.get(path.suffix.lower(), "Unsupported / review")


def _connect(database: Path) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS games (
            sha256 TEXT PRIMARY KEY, filename TEXT NOT NULL, extension TEXT NOT NULL,
            system TEXT NOT NULL, size_bytes INTEGER NOT NULL, stored_path TEXT NOT NULL,
            source_path TEXT NOT NULL, source_label TEXT NOT NULL, rights_basis TEXT NOT NULL,
            imported_at TEXT NOT NULL
        )
    """)
    connection.commit()
    return connection


def import_library(
    source: Path, library: Path, *, rights_basis: str, source_label: str = "user-selected local folder",
    max_bytes: int = 64 * 1024**3,
    system_override: str | None = None,
) -> dict[str, Any]:
    """Recursively import supported files into a content-addressed library, without modifying sources."""
    source = source.expanduser().resolve(strict=True)
    library = library.expanduser().resolve()
    if not source.is_dir():
        raise ValueError("source must be a directory")
    if not rights_basis.strip():
        raise ValueError("rights_basis must describe why you are authorized to use this batch")
    if library == source or source in library.parents or library in source.parents:
        raise ValueError("source and library folders must not contain one another")
    library.mkdir(parents=True, exist_ok=True)
    database = library / "library.sqlite3"
    counts = {"imported": 0, "duplicates": 0, "rejected": 0, "errors": []}
    with _connect(database) as connection:
        for candidate in sorted(source.rglob("*")):
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                extension = candidate.suffix.lower()
                if extension not in EXTENSIONS:
                    continue
                size = candidate.stat().st_size
                if size <= 0 or size > max_bytes:
                    raise ValueError(f"empty file or exceeds size limit ({max_bytes} bytes)")
                before = candidate.stat()
                digest = sha256_file(candidate)
                after = candidate.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError("source changed while hashing; retry after copy finishes")
                existing = connection.execute("SELECT stored_path FROM games WHERE sha256=?", (digest,)).fetchone()
                if existing:
                    counts["duplicates"] += 1
                    continue
                system = infer_system(candidate, system_override)
                relative = Path(system.replace("/", "-")) / digest[:2] / f"{digest}{extension}"
                destination = library / "files" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Copy to a temporary file then atomically publish it; never execute or unpack content.
                fd, temp_name = tempfile.mkstemp(prefix=".incoming-", dir=destination.parent)
                os.close(fd)
                temp_path = Path(temp_name)
                try:
                    shutil.copyfile(candidate, temp_path)
                    if sha256_file(temp_path) != digest:
                        raise OSError("copy hash differs from source hash")
                    os.replace(temp_path, destination)
                finally:
                    temp_path.unlink(missing_ok=True)
                record = (
                    digest, candidate.name, extension, system, size, str(destination),
                    str(candidate), source_label.strip(), rights_basis.strip(),
                    datetime.now(UTC).isoformat(),
                )
                try:
                    connection.execute(
                        "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", record
                    )
                    connection.commit()
                except sqlite3.IntegrityError:
                    destination.unlink(missing_ok=True)
                    counts["duplicates"] += 1
                    continue
                counts["imported"] += 1
            except (OSError, ValueError) as exc:
                counts["rejected"] += 1
                counts["errors"].append({"path": str(candidate), "reason": str(exc)})
    return counts


def list_games(library: Path) -> list[dict[str, Any]]:
    database = library.expanduser().resolve() / "library.sqlite3"
    if not database.exists():
        return []
    with _connect(database) as connection:
        rows = connection.execute(
            "SELECT sha256, filename, extension, system, size_bytes, stored_path, source_label, imported_at "
            "FROM games ORDER BY system, filename COLLATE NOCASE"
        ).fetchall()
        return [dict(row) for row in rows]


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Import and deduplicate local game files")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("import", help="recursively import a user-selected folder")
    ingest.add_argument("--source", type=Path, required=True)
    ingest.add_argument("--library", type=Path, default=Path.home() / "GAME-Emulator-Library")
    ingest.add_argument("--rights-basis", required=True, help="one-time declaration for this import batch")
    ingest.add_argument("--source-label", default="user-selected local folder")
    ingest.add_argument("--max-bytes", type=int, default=64 * 1024**3)
    ingest.add_argument("--system", help="explicitly identify the console when the extension is ambiguous")
    catalog = sub.add_parser("list", help="list files already in the library")
    catalog.add_argument("--library", type=Path, default=Path.home() / "GAME-Emulator-Library")
    args = parser.parse_args()
    if args.command == "import":
        print(json.dumps(import_library(args.source, args.library, rights_basis=args.rights_basis,
                                        source_label=args.source_label, max_bytes=args.max_bytes, system_override=args.system), indent=2))
    else:
        print(json.dumps(list_games(args.library), indent=2))


if __name__ == "__main__":
    main()
