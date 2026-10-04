import os
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
def test_linux_sandbox_denies_host_file(tmp_path):
    content = tmp_path / "authorized.rom"
    content.write_bytes(b"test")

    code = f"""
from pathlib import Path
from game_emulator.sandbox import apply_native_core_sandbox

info = apply_native_core_sandbox(Path({sys.executable!r}), Path({str(content)!r}))
assert info["strict"] is True
assert info["landlock"] is True
assert info["network"] == "denied"

try:
    Path("/etc/passwd").read_bytes()
except PermissionError:
    pass
else:
    raise SystemExit("host file remained readable")
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
    if result.returncode != 0 and "Operation not permitted" in result.stderr:\n        pytest.skip("CI container forbids Landlock enforcement; strict worker still fails closed")\n    assert result.returncode == 0, result.stderr + result.stdout
