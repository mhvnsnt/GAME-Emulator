from game_emulator.open_source_catalog import (
    get_project,
    redistribution_eligibility,
)
from game_emulator.open_source_catalog_cli import installed_core_matches


def test_quicknes_and_sameboy_are_catalogued_with_conservative_licenses():
    quicknes = get_project("quicknes")
    sameboy = get_project("sameboy")
    scummvm = get_project("scummvm")

    assert quicknes is not None and quicknes.license_label.startswith("GPLv2")
    assert sameboy is not None and sameboy.license_label.startswith("MIT")
    assert scummvm is not None and ".scummvm" in scummvm.notes
    for project_id in ("quicknes", "sameboy", "scummvm"):
        assert redistribution_eligibility(project_id)["eligible"] is False


def test_quicknes_and_sameboy_only_match_exact_local_system_and_extension_metadata():
    inventory = {
        "cores": [
            {
                "file": "quicknes_libretro.so",
                "display_name": "QuickNES",
                "supported_systems": ["Nintendo - Nintendo Entertainment System"],
                "supported_extensions": ["nes"],
                "sha256": "a" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "sameboy_libretro.so",
                "display_name": "SameBoy",
                "supported_systems": ["Nintendo - Game Boy", "Nintendo - Game Boy Color"],
                "supported_extensions": ["gb", "gbc"],
                "sha256": "b" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "wrong_platform_libretro.so",
                "display_name": "mislabelled core",
                "supported_systems": ["Nintendo - Game Boy Advance"],
                "supported_extensions": ["gba"],
                "sha256": "c" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
        ]
    }

    matches = {row["project_id"]: row for row in installed_core_matches(inventory)}
    assert {
        row["core_file"]
        for row in matches["quicknes"]["installed_metadata_matches"]
    } == {"quicknes_libretro.so"}
    assert {
        row["core_file"]
        for row in matches["sameboy"]["installed_metadata_matches"]
    } == {"sameboy_libretro.so"}
    assert "wrong_platform_libretro.so" not in {
        row["core_file"]
        for row in matches["sameboy"]["installed_metadata_matches"]
    }


def test_beetle_psx_accepts_upstream_playstation_bin_metadata():
    inventory = {"cores": [{"file": "mednafen_psx_libretro.so", "display_name": "Sony - PlayStation (Beetle PSX)", "supported_systems": ["PlayStation"], "supported_extensions": ["cue", "toc", "m3u", "ccd", "exe", "pbp", "chd", "bin"], "sha256": "d" * 64, "metadata_present": True, "trust_status": "inventory_only_not_executed"}]}
    matches = installed_core_matches(inventory)
    rows = next(row for row in matches if row["project_id"] == "beetle-psx")["installed_metadata_matches"]
    assert any(row["core_file"] == "mednafen_psx_libretro.so" and row["matched_extension"] == "bin" for row in rows)
