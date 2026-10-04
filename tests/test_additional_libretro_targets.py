from game_emulator.open_source_catalog import get_project
from game_emulator.open_source_catalog_cli import installed_core_matches


def test_quicknes_and_sameboy_are_catalogued_with_conservative_licenses():
    quicknes = get_project("quicknes")
    sameboy = get_project("sameboy")
    scummvm = get_project("scummvm")

    assert quicknes is not None and quicknes.license_label.startswith("GPLv2")
    assert sameboy is not None and sameboy.license_label.startswith("MIT")
    assert scummvm is not None and ".scummvm" in scummvm.notes
    assert all(
        not __import__("game_emulator.open_source_catalog", fromlist=["redistribution_eligibility"])
        .redistribution_eligibility(project_id)["eligible"]
        for project_id in ("quicknes", "sameboy", "scummvm")
    )


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
    assert "wrong_platform" not in {
        row["core_file"]
        for row in matches["sameboy"]["installed_metadata_matches"]
    }
