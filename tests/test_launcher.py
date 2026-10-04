import hashlib
import sqlite3
from pathlib import Path

import pytest

from game_emulator.launcher import launch_game


def make_library(tmp_path: Path):
    library = tmp_path / "library"
    files = library / "files" / "Nintendo Game Boy Advance" / "aa"
    files.mkdir(parents=True)
    content = files / ("a" * 64 + ".gba")
    payload = b"synthetic-game-fixture"
    content.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    content.rename(files / (digest + ".gba"))
    content = files / (digest + ".gba")
    with sqlite3.connect(library / "library.sqlite3") as db:
        db.execute("""CREATE TABLE games (
            sha256 TEXT PRIMARY KEY, filename TEXT NOT NULL, extension TEXT NOT NULL,
            system TEXT NOT NULL, size_bytes INTEGER NOT NULL, stored_path TEXT NOT NULL,
            source_path TEXT NOT NULL, source_label TEXT NOT NULL, rights_basis TEXT NOT NULL,
            imported_at TEXT NOT NULL
        )""")
        db.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            digest, "demo.gba", ".gba", "Nintendo Game Boy Advance", len(payload),
            str(content), "/source/demo.gba", "synthetic test", "fixture only", "2026-10-04T00:00:00Z"
        ))
    return library, digest, content


def test_dry_run_builds_argument_list_without_launching(tmp_path: Path):
    library, digest, content = make_library(tmp_path)
    frontend = tmp_path / "retroarch"
    frontend.write_text("synthetic executable placeholder", encoding="utf-8")
    frontend.chmod(frontend.stat().st_mode | 0o111)
    core = tmp_path / "core.so"
    core.write_bytes(b"synthetic core placeholder")

    result = launch_game(library, digest, frontend=str(frontend), core=core, dry_run=True)

    assert result["status"] == "command_ready"
    assert result["command"] == [str(frontend.resolve()), "-L", str(core.resolve()), str(content)]
    assert result["dry_run"] is True


def test_rejects_unknown_hash(tmp_path: Path):
    library, _, _ = make_library(tmp_path)
    frontend = tmp_path / "retroarch"
    frontend.write_text("placeholder", encoding="utf-8")
    core = tmp_path / "core.so"
    core.write_bytes(b"placeholder")
    with pytest.raises(ValueError, match="not found"):
        launch_game(library, "0" * 64, frontend=str(frontend), core=core, dry_run=True)


def test_ambiguous_disc_needs_explicit_system_confirmation(tmp_path: Path):
    library, digest, _content = make_library(tmp_path)
    with sqlite3.connect(library / "library.sqlite3") as db:
        db.execute("UPDATE games SET system = ? WHERE sha256 = ?",
                   ("Disc image (system needs confirmation)", digest))
    frontend = tmp_path / "retroarch"
    frontend.write_text("placeholder", encoding="utf-8")
    frontend.chmod(frontend.stat().st_mode | 0o111)
    core = tmp_path / "core.so"
    core.write_bytes(b"placeholder")
    with pytest.raises(ValueError, match="ambiguous system"):
        launch_game(library, digest, frontend=str(frontend), core=core, dry_run=True)
    result = launch_game(library, digest, frontend=str(frontend), core=core,
                         system_override="Sony PlayStation 2", dry_run=True)
    assert result["system"] == "Sony PlayStation 2"
