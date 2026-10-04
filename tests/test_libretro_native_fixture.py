from pathlib import Path
import shutil
import subprocess

import pytest

from game_emulator.libretro_host import smoke_test


FIXTURE = Path(__file__).parent / "fixtures" / "minimal_libretro_core.c"


@pytest.mark.skipif(
    shutil.which("cc") is None and shutil.which("gcc") is None,
    reason="requires a C compiler for the deterministic native fixture",
)
def test_real_native_fixture_runs_one_frame(monkeypatch, tmp_path: Path):
    compiler = shutil.which("cc") or shutil.which("gcc")
    core = tmp_path / "minimal_libretro_core.so"
    content = tmp_path / "authorized.test"
    content.write_bytes(b"deterministic test content")

    subprocess.run(
        [compiler, "-shared", "-fPIC", "-O2", str(FIXTURE), "-o", str(core)],
        check=True,
        capture_output=True,
        text=True,
    )

    # This test deliberately isolates ctypes/IPC/core ABI behavior from the
    # host kernel's optional Landlock/seccomp capabilities. The strict OS
    # containment path has its own fail-closed tests.
    monkeypatch.setattr(
        "game_emulator.libretro_worker.apply_native_core_sandbox",
        lambda *args, **kwargs: {
            "platform": "test",
            "strict": True,
            "fixture": True,
        },
    )

    result = smoke_test(core, content)
    assert result["status"] == "TICK_COMPLETE"
    assert result["video_fired"] is True
    assert result["video"]["width"] == 1
    assert result["video"]["height"] == 1
    assert result["sandbox"]["fixture"] is True
