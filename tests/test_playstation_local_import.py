from pathlib import Path

from game_emulator.library import infer_system, import_library


def test_explicit_playstation_override_classifies_shared_disc_extensions():
    assert infer_system(Path("Tekken 3/SLUS_004.02.BIN"), "Sony PlayStation") == "Sony PlayStation"
    assert infer_system(Path("Tekken 3/game.cue"), "ps1") == "Sony PlayStation"


def test_import_can_explicitly_classify_ps1_bin_and_cue(tmp_path: Path):
    source = tmp_path / "Tekken 3"
    source.mkdir()
    (source / "Tekken 3.cue").write_text('FILE "Tekken 3.bin" BINARY\n', encoding="utf-8")
    (source / "Tekken 3.bin").write_bytes(b"authorized-test-fixture")
    library = tmp_path / "library"

    result = import_library(
        source,
        library,
        rights_basis="test fixture supplied by the user",
        system_override="Sony PlayStation",
    )

    assert result["imported"] == 2
    assert not result["errors"]

    import sqlite3
    with sqlite3.connect(library / "library.sqlite3") as db:
        systems = {row[0] for row in db.execute("SELECT DISTINCT system FROM games")}
    assert systems == {"Sony PlayStation"}
