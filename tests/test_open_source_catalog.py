from game_emulator.open_source_catalog import (
    get_project,
    list_projects,
    redistribution_eligibility,
)
from game_emulator.open_source_catalog_cli import installed_core_matches


def test_catalog_entries_have_upstream_and_license_provenance():
    projects = list_projects()
    assert len(projects) >= 19
    assert all(row["upstream_url"].startswith("https://") for row in projects)
    assert all(row["license_spdx"] for row in projects)
    assert all(row["status"] in {"catalogued", "upstream_candidate"} for row in projects)


def test_exact_system_filter_does_not_fuzzy_match():
    assert [p["project_id"] for p in list_projects(systems={"Sony PlayStation 2"})] == ["pcsx2"]
    assert list_projects(systems={"Nintendo Switch"}) == []


def test_unknown_project_never_clears_redistribution():
    result = redistribution_eligibility("not-a-real-project")
    assert result["eligible"] is False
    assert result["status"] == "unknown_project"


def test_known_project_requires_exact_release_license_review():
    assert get_project("PPSSPP") is not None
    result = redistribution_eligibility("ppsspp")
    assert result["eligible"] is False
    assert result["status"] == "manual_license_review_required"


def test_installed_core_matches_require_system_and_extension_metadata():
    inventory = {
        "cores": [
            {
                "file": "mgba_libretro.so",
                "display_name": "mGBA",
                "supported_systems": ["Nintendo - Game Boy Advance"],
                "supported_extensions": ["gba", "gbc", "gb"],
                "sha256": "a" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "fake_psx_core.so",
                "display_name": "Fake PSX",
                "supported_systems": ["Sony - PlayStation"],
                "supported_extensions": ["iso"],
                "sha256": "b" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "no_metadata_core.so",
                "display_name": "Unknown",
                "supported_systems": [],
                "supported_extensions": [],
                "sha256": "c" * 64,
                "metadata_present": False,
                "trust_status": "inventory_only_not_executed",
            },
        ]
    }
    matches = installed_core_matches(inventory)
    mgba = next(row for row in matches if row["project_id"] == "mgba")
    assert [row["core_file"] for row in mgba["installed_metadata_matches"]] == ["mgba_libretro.so"]
    assert all(row["project_id"] != "beetle-psx" for row in matches)
    assert all(row["project_id"] != "nestopia" for row in matches)


def test_expanded_catalog_maps_snes_and_saturn_only_with_matching_extensions():
    inventory = {
        "cores": [
            {
                "file": "snes9x_libretro.so",
                "display_name": "Snes9x",
                "supported_systems": ["Nintendo - SNES/SFC"],
                "supported_extensions": ["smc", "sfc", "swc", "fig", "bs", "st"],
                "sha256": "d" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "beetle_saturn_libretro.so",
                "display_name": "Beetle Saturn",
                "supported_systems": ["Sega - Saturn"],
                "supported_extensions": ["cue", "toc", "m3u", "ccd", "chd"],
                "sha256": "e" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "wrong_extension_libretro.so",
                "display_name": "Wrong extension",
                "supported_systems": ["Sega - Saturn"],
                "supported_extensions": ["iso"],
                "sha256": "f" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
        ]
    }
    matches = installed_core_matches(inventory)
    snes = next(row for row in matches if row["project_id"] == "snes9x")
    saturn = next(row for row in matches if row["project_id"] == "beetle-saturn")
    assert {m["core_file"] for m in snes["installed_metadata_matches"]} == {"snes9x_libretro.so"}
    assert {m["core_file"] for m in saturn["installed_metadata_matches"]} == {"beetle_saturn_libretro.so"}
    assert all(m["core_file"] != "wrong_extension_libretro.so" for m in saturn["installed_metadata_matches"])
    assert all(m["trust_status"] == "inventory_only_not_executed" for m in saturn["installed_metadata_matches"])



def test_gba_and_dreamcast_candidates_use_upstream_extensions():
    inventory = {
        "cores": [
            {
                "file": "beetle_gba_libretro.so",
                "display_name": "Beetle GBA",
                "supported_systems": ["Nintendo - Game Boy Advance"],
                "supported_extensions": ["gba", "agb", "bin"],
                "sha256": "1" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "flycast_libretro.so",
                "display_name": "Flycast",
                "supported_systems": ["Sega - Dreamcast/NAOMI"],
                "supported_extensions": ["cdi", "gdi", "chd", "cue", "bin", "elf", "zip"],
                "sha256": "2" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
            {
                "file": "wrong_platform_libretro.so",
                "display_name": "Wrong platform",
                "supported_systems": ["Sega - Dreamcast/NAOMI"],
                "supported_extensions": ["gba"],
                "sha256": "3" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            },
        ]
    }
    matches = installed_core_matches(inventory)
    gba = next(row for row in matches if row["project_id"] == "beetle-gba")
    flycast = next(row for row in matches if row["project_id"] == "flycast")
    assert {m["core_file"] for m in gba["installed_metadata_matches"]} == {"beetle_gba_libretro.so"}
    assert {m["core_file"] for m in flycast["installed_metadata_matches"]} == {"flycast_libretro.so"}
    assert all(m["core_file"] != "wrong_platform_libretro.so" for m in flycast["installed_metadata_matches"])



def test_mesence_multi_system_matching_still_uses_local_metadata():
    inventory = {
        "cores": [
            {
                "file": "mesence_libretro.so",
                "display_name": "MesenCE",
                "supported_systems": [
                    "Nintendo - Nintendo Entertainment System",
                    "Nintendo - Game Boy Advance",
                ],
                "supported_extensions": ["nes", "fds", "unf", "unif", "gba"],
                "sha256": "4" * 64,
                "metadata_present": True,
                "trust_status": "inventory_only_not_executed",
            }
        ]
    }
    matches = installed_core_matches(inventory)
    mesence = next(row for row in matches if row["project_id"] == "mesence")
    assert {m["core_file"] for m in mesence["installed_metadata_matches"]} == {
        "mesence_libretro.so"
    }
    assert {m["system"] for m in mesence["installed_metadata_matches"]} >= {
        "Nintendo - Nintendo Entertainment System",
        "Nintendo Game Boy Advance",
    }
