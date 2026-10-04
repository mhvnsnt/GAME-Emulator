"""Parent-side orchestration for the disposable Libretro worker."""
from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import Any

from .libretro_worker import run_worker


class CoreCrashed(RuntimeError):
    pass


class CoreTimeout(TimeoutError):
    pass


class IsolatedCore:
    def __init__(self, core_path: Path) -> None:
        self.core_path = Path(core_path).expanduser().resolve(strict=True)
        self.parent = None
        self.process = None

    def start(self, timeout: float = 3.0) -> dict[str, Any]:
        ctx = mp.get_context("spawn")
        self.parent, child = ctx.Pipe()
        self.process = ctx.Process(
            target=run_worker, args=(child, str(self.core_path)), daemon=True
        )
        self.process.start()
        child.close()
        if not self.parent.poll(timeout):
            self.close(force=True)
            raise CoreTimeout("worker did not become ready")
        result = self.parent.recv()
        if result.get("status") != "READY":
            self.close(force=True)
            raise CoreCrashed(str(result))
        return result

    def command(self, message: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
        if self.parent is None or self.process is None:
            raise RuntimeError("worker is not started")
        if not self.process.is_alive():
            raise CoreCrashed(f"worker exited with code {self.process.exitcode}")
        self.parent.send(message)
        if not self.parent.poll(timeout):
            if not self.process.is_alive():
                raise CoreCrashed(f"worker crashed; exit code {self.process.exitcode}")
            raise CoreTimeout(f"worker timed out after {timeout}s")
        return self.parent.recv()

    def smoke_one_frame(self, content_path: Path) -> dict[str, Any]:
        loaded = self.command({"cmd": "LOAD", "path": str(content_path)})
        if loaded.get("status") != "LOADED":
            raise RuntimeError(f"core rejected content: {loaded}")
        tick = self.command({"cmd": "TICK"})
        if tick.get("status") != "TICK_COMPLETE":
            raise RuntimeError(f"one-frame tick failed: {tick}")
        if not tick.get("video_fired"):
            raise RuntimeError("retro_run completed without a video refresh callback")
        return tick

    def close(self, force: bool = False) -> None:
        if self.parent is None or self.process is None:
            return
        try:
            if not force and self.process.is_alive():
                self.command({"cmd": "SHUTDOWN"}, timeout=2)
        except (OSError, EOFError, CoreCrashed, CoreTimeout, RuntimeError):
            pass
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(2)
        self.parent.close()
        self.parent = self.process = None


def smoke_test(core_path: Path, content_path: Path, timeout: float = 5.0) -> dict[str, Any]:
    runner = IsolatedCore(core_path)
    try:
        runner.start(timeout=min(timeout, 3.0))
        return runner.smoke_one_frame(content_path)
    finally:
        runner.close()
