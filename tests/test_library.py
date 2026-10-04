import hashlib
from pathlib import Path

import pytest

from game_emulator.library import import_library, infer_system, list_games


def test_import_classifies_hashes_and_copies_without_modifying_source(tmp_path: Path):
    source = tmp_path / "incoming" / "GBA"
    source.mkdir(parents=True)
    game = source / "demo.gba"
    payload = b"synthetic-only-fixture"
    game.write_bytes(payload)
    library = tmp_path / "library"

    result = import_library(source.parent, library, rights_basis="synthetic test fixture")

    assert result["imported"] == 1
    assert result["duplicates"] == 0
    assert game.read_bytes() == payload
    entry = list_games(library)[0]
    assert entry["system"] == "Nintendo Game Boy Advance"
    assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
    assert Path(entry["stored_path"]).read_bytes() == payload


def test_import_deduplicates_same_bytes_across_folders(tmp_path: Path):
    source = tmp_path / "source"
    (source / "GBA").mkdir(parents=True)
    (source / "backup" / "GBA").mkdir(parents=True)
    (source / "GBA" / "one.gba").write_bytes(b"same")
    (source / "backup" / "GBA" / "copy.gba").write_bytes(b"same")

    result = import_library(source, tmp_path / "library", rights_basis="synthetic fixture")

    assert result["imported"] == 1
    assert result["duplicates"] == 1
    assert len(list_games(tmp_path / "library")) == 1


def test_shared_iso_extension_does_not_guess_console(tmp_path: Path):
    assert infer_system(tmp_path / "disc.iso") == "Disc image (system needs confirmation)"
    assert infer_system(tmp_path / "PS2" / "disc.iso") == "Sony PlayStation 2"


def test_requires_rights_basis_and_source_not_inside_library(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError, match="rights_basis"):
        import_library(source, tmp_path / "library", rights_basis=" ")
    library = source / "library"
    with pytest.raises(ValueError, match="contain one another"):
        import_library(source, library, rights_basis="test")


def test_import_ignores_unsupported_files_and_symlinks(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text("not a game", encoding="utf-8")
    (source / "fake.exe").write_bytes(b"not supported")
    result = import_library(source, tmp_path / "library", rights_basis="test fixture")
    assert result["imported"] == 0
    assert result["rejected"] == 0
