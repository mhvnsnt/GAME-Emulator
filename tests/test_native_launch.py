from pathlib import Path

import pytest

from game_emulator.native_launch import LaunchSandboxError, SandboxLauncher, launch_sandboxed


def test_native_launch_wraps_command_with_explicit_boundary():
    sandbox = SandboxLauncher("/usr/bin/bwrap", ("--die-with-parent",))
    result = launch_sandboxed(
        ["/usr/bin/retroarch", "-L", "/cores/core.so", "game.rom"],
        cwd=Path("/tmp"),
        sandbox=sandbox,
        dry_run=True,
    )
    assert result["sandboxed"] is True
    assert result["command"] == [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--",
        "/usr/bin/retroarch",
        "-L",
        "/cores/core.so",
        "game.rom",
    ]


def test_native_launch_fails_closed_without_wrapper(monkeypatch, tmp_path):
    monkeypatch.delenv("GAME_EMULATOR_SANDBOX_LAUNCHER", raising=False)
    with pytest.raises(LaunchSandboxError, match="native launch refused"):
        launch_sandboxed(["/usr/bin/retroarch"], cwd=tmp_path, dry_run=True)


def test_missing_wrapper_is_rejected(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(LaunchSandboxError, match="not found"):
        SandboxLauncher.from_spec("definitely-not-installed")
