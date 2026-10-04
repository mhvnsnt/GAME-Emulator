"""Disposable Libretro core worker."""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

from .libretro_abi import (
    LibretroCallbacks,
    retro_audio_sample_batch_t,
    retro_audio_sample_t,
    retro_environment_t,
    retro_game_info,
    retro_input_poll_t,
    retro_input_state_t,
    retro_video_refresh_t,
)


class WorkerError(RuntimeError):
    pass


class LibretroWorker:
    def __init__(self, core_path: str) -> None:
        self.core_path = str(Path(core_path).expanduser().resolve(strict=True))
        self.callbacks = LibretroCallbacks()
        self.core = None
        self._content_path_bytes = None

    def load(self, content_path: str) -> bool:
        if self.core is None:
            self.core = ctypes.CDLL(self.core_path)
            required = (
                "retro_set_environment",
                "retro_set_video_refresh",
                "retro_set_audio_sample",
                "retro_set_audio_sample_batch",
                "retro_set_input_poll",
                "retro_set_input_state",
                "retro_init",
                "retro_load_game",
                "retro_run",
                "retro_unload_game",
                "retro_deinit",
            )
            missing = [name for name in required if not hasattr(self.core, name)]
            if missing:
                raise WorkerError("core missing required symbols: " + ", ".join(missing))

            self.core.retro_set_environment.argtypes = [retro_environment_t]
            self.core.retro_set_environment.restype = None
            self.core.retro_set_video_refresh.argtypes = [retro_video_refresh_t]
            self.core.retro_set_video_refresh.restype = None
            self.core.retro_set_audio_sample.argtypes = [retro_audio_sample_t]
            self.core.retro_set_audio_sample.restype = None
            self.core.retro_set_audio_sample_batch.argtypes = [retro_audio_sample_batch_t]
            self.core.retro_set_audio_sample_batch.restype = None
            self.core.retro_set_input_poll.argtypes = [retro_input_poll_t]
            self.core.retro_set_input_poll.restype = None
            self.core.retro_set_input_state.argtypes = [retro_input_state_t]
            self.core.retro_set_input_state.restype = None
            self.core.retro_init.argtypes = []
            self.core.retro_init.restype = None
            self.core.retro_load_game.argtypes = [ctypes.POINTER(retro_game_info)]
            self.core.retro_load_game.restype = ctypes.c_bool
            self.core.retro_run.argtypes = []
            self.core.retro_run.restype = None
            self.core.retro_unload_game.argtypes = []
            self.core.retro_unload_game.restype = None
            self.core.retro_deinit.argtypes = []
            self.core.retro_deinit.restype = None

            self.core.retro_set_environment(self.callbacks.cb_env)
            self.core.retro_set_video_refresh(self.callbacks.cb_video)
            self.core.retro_set_audio_sample(self.callbacks.cb_audio)
            self.core.retro_set_audio_sample_batch(self.callbacks.cb_audio_batch)
            self.core.retro_set_input_poll(self.callbacks.cb_input_poll)
            self.core.retro_set_input_state(self.callbacks.cb_input_state)
            self.core.retro_init()

        path_bytes = str(Path(content_path).expanduser().resolve(strict=True)).encode()
        self._content_path_bytes = path_bytes
        info = retro_game_info(path=path_bytes, data=None, size=0, meta=None)
        return bool(self.core.retro_load_game(ctypes.byref(info)))

    def tick(self) -> dict[str, Any]:
        if self.core is None:
            raise WorkerError("core is not loaded")
        self.callbacks.frame_rendered = False
        self.callbacks.last_video = None
        self.core.retro_run()
        return {
            "video_fired": self.callbacks.frame_rendered,
            "video": self.callbacks.last_video,
        }

    def shutdown(self) -> None:
        if self.core is None:
            return
        try:
            self.core.retro_unload_game()
        finally:
            self.core.retro_deinit()
            self.core = None


def run_worker(conn: Connection, core_path: str) -> None:
    worker = LibretroWorker(core_path)
    try:
        conn.send({"status": "READY"})
        while True:
            message = conn.recv()
            command = message.get("cmd")
            if command == "LOAD":
                try:
                    ok = worker.load(message["path"])
                    conn.send({"status": "LOADED" if ok else "FAILED"})
                except Exception as exc:
                    conn.send(
                        {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
                    )
            elif command == "TICK":
                try:
                    result = worker.tick()
                    conn.send({"status": "TICK_COMPLETE", **result})
                except Exception as exc:
                    conn.send(
                        {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
                    )
            elif command == "SHUTDOWN":
                worker.shutdown()
                conn.send({"status": "SHUTDOWN"})
                return
            else:
                conn.send({"status": "ERROR", "error": "unknown command"})
    except (EOFError, BrokenPipeError):
        return
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a disposable Libretro core worker")
    parser.add_argument("--core", required=True)
    args = parser.parse_args()
    from multiprocessing import Pipe, Process

    parent, child = Pipe()
    process = Process(target=run_worker, args=(child, args.core), daemon=True)
    process.start()
    child.close()
    try:
        print(json.dumps(parent.recv()))
        for line in sys.stdin:
            parent.send(json.loads(line))
            print(json.dumps(parent.recv()), flush=True)
    finally:
        if process.is_alive():
            process.terminate()
        process.join(2)


if __name__ == "__main__":
    main()
