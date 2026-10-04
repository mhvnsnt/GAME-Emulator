from game_emulator.backends import candidates, command_for, discover_backends


def test_backend_registry_does_not_claim_uninstalled_runtime_is_runnable(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    rows = discover_backends()
    assert rows
    assert all(row["installed"] is False for row in rows)
    assert all(row["runnable"] is False for row in rows)


def test_candidates_are_capability_based():
    matches = candidates(system="Nintendo GameCube", extension=".iso")
    ids = {backend.backend_id for backend in matches}
    assert "dolphin" in ids
    assert "pcsx2" not in ids


def test_dolphin_command_is_explicit():
    backend = next(backend for backend in candidates(system="Nintendo GameCube", extension=".iso") if backend.backend_id == "dolphin")
    assert command_for(backend, "/usr/bin/dolphin-emu", __import__("pathlib").Path("game.iso")) == [
        "/usr/bin/dolphin-emu",
        "-e",
        "game.iso",
    ]


def test_ppsspp_and_azahar_are_declared_for_their_systems():
    psp = {b.backend_id for b in candidates(system="Sony PlayStation Portable", extension=".iso")}
    three_ds = {b.backend_id for b in candidates(system="Nintendo 3DS", extension=".3ds")}
    assert "ppsspp" in psp
    assert "pcsx2" not in psp
    assert "azahar" in three_ds
    assert "dolphin" not in three_ds
\n\ndef test_ppsspp_command_is_explicit():\n    backend = next(backend for backend in candidates(system="Sony PlayStation Portable", extension=".iso") if backend.backend_id == "ppsspp")\n    assert command_for(backend, "/usr/bin/ppsspp", __import__("pathlib").Path("game.iso")) == [\n        "/usr/bin/ppsspp",\n        "game.iso",\n    ]\n\n\ndef test_azahar_stays_unlaunched_until_its_cli_contract_is_verified():\n    backend = next(backend for backend in candidates(system="Nintendo 3DS", extension=".3ds") if backend.backend_id == "azahar")\n    import pytest\n    with pytest.raises(ValueError, match="dedicated launch adapter"):\n        command_for(backend, "/usr/bin/azahar", __import__("pathlib").Path("game.3ds"))\n