from pathlib import Path

from game_emulator.adapters import compatible_cores, inventory_cores


def test_inventory_uses_libretro_database_for_multisystem_info(tmp_path: Path):
    cores = tmp_path / "cores"
    info = tmp_path / "info"
    cores.mkdir()
    info.mkdir()
    (cores / "mesence_libretro.so").write_bytes(b"not executed")
    (info / "mesence_libretro.info").write_text(
        'display_name = "Mesen"
'
        'supported_extensions = "nes|fds|sfc|gb|gbc|gba"
'
        'systemname = "Multi-System"
'
        'database = "Nintendo - Nintendo Entertainment System|'
        'Nintendo - Family Computer Disk System|Nintendo Super Nintendo Entertainment System"
'
        'systemid = "nes"
'
        'license = "GPLv3"
'
        'permissions = ""
',
        encoding="utf-8",
    )

    report = inventory_cores(cores, info)
    core = report["cores"][0]

    assert core["database"] == [
        "Nintendo - Nintendo Entertainment System",
        "Nintendo - Family Computer Disk System",
        "Nintendo Super Nintendo Entertainment System",
    ]
    assert core["license"] == "GPLv3"
    assert compatible_cores(
        report,
        system="Nintendo NES",
        extension="nes",
    ) == []
    assert compatible_cores(
        report,
        system="Nintendo - Nintendo Entertainment System",
        extension="nes",
    )[0]["file"] == "mesence_libretro.so"
