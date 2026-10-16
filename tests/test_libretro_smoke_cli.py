import json
import sys
from pathlib import Path

from game_emulator import libretro_smoke_cli


def test_smoke_cli_passes_explicit_system_directory(monkeypatch, capsys, tmp_path: Path):
    core = tmp_path / "core.so"
    content = tmp_path / "authorized.gba"
    system_dir = tmp_path / "system"
    core.write_bytes(b"placeholder")
    content.write_bytes(b"authorized homebrew placeholder")
    system_dir.mkdir()
    captured: dict[str, object] = {}

    def fake_smoke(core_path, content_path, *, timeout, system_dir):
        captured.update(
            core_path=core_path,
            content_path=content_path,
            timeout=timeout,
            system_dir=system_dir,
        )
        return {
            "status": "TICK_COMPLETE",
            "video_fired": True,
            "sandbox": {"strict": True, "network": "test-policy"},
        }

    monkeypatch.setattr(libretro_smoke_cli, "smoke_test", fake_smoke)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "game-emulator-libretro-smoke",
            "--core",
            str(core),
            "--content",
            str(content),
            "--system-dir",
            str(system_dir),
        ],
    )
    libretro_smoke_cli.main()

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "TICK_COMPLETE"
    assert result["sandbox"]["strict"] is True
    assert captured["system_dir"] == system_dir
    assert captured["core_path"] == core
    assert captured["content_path"] == content
    assert captured["timeout"] == 5.0
