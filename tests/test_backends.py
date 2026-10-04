from game_emulator.backends import Backend, candidates, command_for, discover_backends


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


def test_standalone_command_is_explicit():
    backend = Backend(
        "test", "Test", "standalone",
        frozenset({"Test System"}), frozenset({".bin"}),
        license="MIT",
    )
    assert command_for(backend, "/usr/bin/test-emulator", __import__("pathlib").Path("game.bin")) == [
        "/usr/bin/test-emulator",
        "-e",
        "game.bin",
    ]


def test_ppsspp_and_azahar_are_declared_for_their_systems():
    psp = {b.backend_id for b in candidates(system="Sony PlayStation Portable", extension=".iso")}
    three_ds = {b.backend_id for b in candidates(system="Nintendo 3DS", extension=".3ds")}
    assert "ppsspp" in psp
    assert "pcsx2" not in psp
    assert "azahar" in three_ds
    assert "dolphin" not in three_ds
