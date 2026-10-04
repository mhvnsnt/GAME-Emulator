from pathlib import Path

import pytest

import game_emulator.sandbox as sandbox


def test_landlock_strict_policy_rejects_abi_without_udp_restriction(monkeypatch):
    monkeypatch.setattr(sandbox, "_landlock_abi", lambda: (9, (444, 445, 446)))
    with pytest.raises(sandbox.SandboxError, match="ABI >= 10"):
        sandbox._apply_linux_landlock(Path("/core.so"), Path("/game.rom"))


def test_linux_sandbox_report_only_claims_tcp_udp_denial_after_policy_succeeds(
    monkeypatch, tmp_path: Path
):
    core = tmp_path / "core.so"
    content = tmp_path / "game.rom"
    core.write_bytes(b"synthetic core placeholder")
    content.write_bytes(b"synthetic authorized-content placeholder")
    monkeypatch.delenv("GAME_EMULATOR_ALLOW_UNSANDBOXED_CORE", raising=False)
    monkeypatch.setattr(sandbox.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sandbox, "_apply_unix_limits", lambda policy: None)
    monkeypatch.setattr(sandbox, "_apply_linux_landlock", lambda core, game: 10)

    result = sandbox.apply_native_core_sandbox(core, content, sandbox.SandboxPolicy(strict=True))

    assert result["strict"] is True
    assert result["landlock_abi"] == 10
    assert result["network"] == "tcp_udp_denied"
    assert result["scoped_abstract_unix_sockets"] is True
    assert result["scoped_signals"] is True
