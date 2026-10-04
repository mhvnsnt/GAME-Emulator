"""Parent-side orchestration for the disposable Libretro worker."""
from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import Any

from .ipc_protocol import IPCProtocolError, receive_message, send_message
from .libretro_worker import run_worker


class CoreCrashed(RuntimeError):
    pass


class CoreTimeout(TimeoutError):
    pass


class IsolatedCore:
    def __init__(self, core_path: Path, system_dir: Path | None = None) -> None:
        self.core_path = Path(core_path).expanduser().resolve(strict=True)
        self.system_dir: Path | None = None
        if system_dir is not None:
            raw_system_dir = Path(system_dir).expanduser()
            if raw_system_dir.is_symlink():
                raise ValueError("system directory may not be a symbolic link")
            resolved_system_dir = raw_system_dir.resolve(strict=True)
            if not resolved_system_dir.is_dir():
                raise ValueError("system directory must be a directory")
            self.system_dir = resolved_system_dir
        self.parent = None
        self.process = None

    def start(self, timeout: float = 3.0) -> dict[str, Any]:
        ctx = mp.get_context("spawn")
        self.parent, child = ctx.Pipe()
        self.process = ctx.Process(
            target=run_worker,
            args=(
                child,
                str(self.core_path),
                str(self.system_dir) if self.system_dir else None,
            ),
            daemon=True
        )
        self.process.start()
        child.close()
        if not self.parent.poll(timeout):
            self.close(force=True)
            raise CoreTimeout("worker did not become ready")
        try:
            result = receive_message(self.parent)
        except (EOFError, OSError, IPCProtocolError) as exc:
            self.close(force=True)
            raise CoreCrashed("worker returned an invalid startup message") from exc
        if result.get("status") != "READY":
            self.close(force=True)
            raise CoreCrashed(str(result))
        return result

    def command(self, message: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
        if self.parent is None or self.process is None:
            raise RuntimeError("worker is not started")
        if not self.process.is_alive():
            raise CoreCrashed(f"worker exited with code {self.process.exitcode}")
        send_message(self.parent, message)
        if not self.parent.poll(timeout):
            if not self.process.is_alive():
                raise CoreCrashed(f"worker crashed; exit code {self.process.exitcode}")
            raise CoreTimeout(f"worker timed out after {timeout}s")
        try:
            return receive_message(self.parent)
        except (EOFError, OSError, IPCProtocolError) as exc:
            self.close(force=True)
            raise CoreCrashed("worker returned an invalid IPC message") from exc

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


def smoke_test(
    core_path: Path,
    content_path: Path,
    timeout: float = 5.0,
    system_dir: Path | None = None,
) -> dict[str, Any]:
    runner = IsolatedCore(core_path, system_dir)
    try:
        runner.start(timeout=min(timeout, 3.0))
        return runner.smoke_one_frame(content_path)
    finally:
        runner.close()
