from game_emulator.open_source_catalog import (
    get_project,
    list_projects,
    redistribution_eligibility,
)
from game_emulator.open_source_catalog_cli import installed_core_matches


def test_catalog_entries_have_upstream_and_license_provenance():
    projects = list_projects()
    assert len(projects) >= 8
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
