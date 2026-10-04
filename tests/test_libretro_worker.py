import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from game_emulator import libretro_worker
from game_emulator.libretro_host import smoke_test


@pytest.mark.skipif(
    not os.environ.get("GAME_EMULATOR_TEST_CORE")
    or not os.environ.get("GAME_EMULATOR_TEST_CONTENT"),
    reason="requires an installed Libretro core and authorized homebrew/test content",
)
def test_real_one_frame_smoke():
    result = smoke_test(
        Path(os.environ["GAME_EMULATOR_TEST_CORE"]),
        Path(os.environ["GAME_EMULATOR_TEST_CONTENT"]),
    )
    assert result["status"] == "TICK_COMPLETE"
    assert result["video_fired"] is True


def test_worker_system_directory_is_explicit_and_must_be_real_directory(tmp_path):
    core = tmp_path / "fake-core.so"
    core.write_bytes(b"not-a-library")
    system_dir = tmp_path / "system"
    system_dir.mkdir()

    worker = libretro_worker.LibretroWorker(str(core), str(system_dir))
    assert worker.system_dir == system_dir.resolve()

    file_path = tmp_path / "not-a-directory"
    file_path.write_text("not a directory", encoding="utf-8")
    with pytest.raises(libretro_worker.WorkerError, match="must be a directory"):
        libretro_worker.LibretroWorker(str(core), str(file_path))

    symlink = tmp_path / "system-link"
    symlink.symlink_to(system_dir, target_is_directory=True)
    with pytest.raises(libretro_worker.WorkerError, match="symbolic link"):
        libretro_worker.LibretroWorker(str(core), str(symlink))


def test_native_load_is_after_sandbox(monkeypatch, tmp_path):
    core = tmp_path / "fake-core.so"
    content = tmp_path / "test.rom"
    core.write_bytes(b"not-a-library")
    content.write_bytes(b"test")

    def deny(*args, **kwargs):
        raise libretro_worker.WorkerError("sandbox denied")

    monkeypatch.setattr(libretro_worker, "apply_native_core_sandbox", deny)
    monkeypatch.setattr(
        libretro_worker.ctypes,
        "CDLL",
        lambda *args, **kwargs: pytest.fail("native library loaded before sandbox"),
    )

    worker = libretro_worker.LibretroWorker(str(core))
    with pytest.raises(libretro_worker.WorkerError, match="sandbox denied"):
        worker.load(str(content))


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux Landlock")
def test_linux_sandbox_denies_host_file_write_and_tcp(tmp_path):
    content = tmp_path / "authorized.rom"
    content.write_bytes(b"test")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        tcp_port = listener.getsockname()[1]

        code = f"""
import socket
from pathlib import Path
from game_emulator.sandbox import apply_native_core_sandbox

content = Path({str(content)!r})
info = apply_native_core_sandbox(Path({sys.executable!r}), content)
assert info["strict"] is True
assert info["landlock"] is True
assert info["network"] == "socket_syscalls_denied_by_process_wide_seccomp_and_tcp_by_landlock"

try:
    Path("/etc/passwd").read_bytes()
except PermissionError:
    pass
else:
    raise SystemExit("host file remained readable")

try:
    (content.parent / "sandbox-write-probe").write_text("must be denied")
except PermissionError:
    pass
else:
    raise SystemExit("sandbox allowed a host filesystem write")

try:
    socket.create_connection(("127.0.0.1", {tcp_port}), timeout=0.25)
except OSError:
    pass
else:
    raise SystemExit("sandbox allowed a TCP connection")
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0 and (
        "Operation not permitted" in result.stderr
        or "Landlock ABI >= 8" in result.stderr
    ):
        pytest.skip(
            "CI host cannot demonstrate the required thread-synchronized Landlock/seccomp policy; strict worker fails closed"
        )
    assert result.returncode == 0, result.stderr + result.stdout
