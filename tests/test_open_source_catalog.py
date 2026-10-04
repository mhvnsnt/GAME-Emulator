from game_emulator.open_source_catalog import (
    get_project,
    list_projects,
    redistribution_eligibility,
)


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
