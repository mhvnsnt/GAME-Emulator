from pathlib import Path

from game_emulator.adapters import inventory_cores, parse_info


def test_inventory_hashes_core_and_reads_info_without_loading_it(tmp_path: Path):
    cores = tmp_path / "cores"
    info_dir = tmp_path / "info"
    cores.mkdir()
    info_dir.mkdir()
    (cores / "mgba_libretro.so").write_bytes(b"synthetic native-library bytes")
    (cores / "ignore.txt").write_text("not a core", encoding="utf-8")
    (info_dir / "mgba_libretro.info").write_text(
        'display_name = "mGBA"\n'
        'corename = "mGBA"\n'
        'supported_extensions = "gba|gbc|gb"\n'
        'supported_systems = "Nintendo - Game Boy Advance|Nintendo - Game Boy Color"\n'
        'firmware0_path = "gba_bios.bin"\n',
        encoding="utf-8",
    )

    result = inventory_cores(cores, info_dir)

    assert result["core_count"] == 1
    core = result["cores"][0]
    assert core["display_name"] == "mGBA"
    assert core["supported_extensions"] == ["gba", "gbc", "gb"]
    assert core["metadata_present"] is True
    assert core["native_code_loaded"] is False
    assert core["trust_status"] == "inventory_only_not_executed"
    assert len(core["sha256"]) == 64
    assert "gba_bios.bin" in core["firmware"]


def test_parse_info_handles_comments_and_missing_metadata(tmp_path: Path):
    info = tmp_path / "test.info"
    info.write_text('# comment\nkey = "value"\nempty = ""\n', encoding="utf-8")
    assert parse_info(info) == {"key": "value", "empty": ""}
    assert parse_info(tmp_path / "missing.info") == {}


def test_inventory_rejects_missing_core_directory(tmp_path: Path):
    try:
        inventory_cores(tmp_path / "missing")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing core directory should fail")
