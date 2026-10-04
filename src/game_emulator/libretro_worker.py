"""Disposable Libretro core worker.

This process is the native-code trust boundary. The parent must never ctypes.CDLL
an untrusted core. A worker crash is reported by process exit, not propagated to
the parent Python interpreter.
"""
from __future__ import annotations
import ctypes
import os
import sys
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any
from .libretro_abi import LibretroCallbacks, retro_game_info

class WorkerError(RuntimeError): pass

class LibretroWorker:
    def __init__(self, core_path: str) -> None:
        self.core_path = str(Path(core_path).expanduser().resolve(strict=True))
        self.callbacks = LibretroCallbacks()
        self.core = None

    def load(self, content_path: str) -> bool:
        if self.core is None:
            self.core = ctypes.CDLL(self.core_path)
            required = (
                "retro_set_environment", "retro_set_video_refresh",
                "retro_set_audio_sample", "retro_set_audio_sample_batch",
                "retro_set_input_poll", "retro_set_input_state",
                "retro_init", "retro_load_game", "retro_run",
                "retro_unload_game", "retro_deinit",
            )
            missing = [name for name in required if not hasattr(self.core, name)]
            if missing:
                raise WorkerError("core missing required symbols: " + ", ".join(missing))
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
        self.core.retro_run()
        return {"video_fired": self.callbacks.frame_rendered, "video": self.callbacks.last_video}

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
                    conn.send({"status": "ERROR", "error": type(exc).__name__ + ": " + str(exc)})
            elif command == "TICK":
                try:
                    result = worker.tick()
                    conn.send({"status": "TICK_COMPLETE", **result})
                except Exception as exc:
                    conn.send({"status": "ERROR", "error": type(exc).__name__ + ": " + str(exc)})
            elif command == "SHUTDOWN":
                worker.shutdown()
                conn.send({"status": "SHUTDOWN"})
                return
            else:
                conn.send({"status": "ERROR", "error": "unknown command"})
    except (EOFError, BrokenPipeError):
        return
    finally:
        try:
            conn.close()
        except OSError:
            pass

def main() -> None:
    import argparse
    from multiprocessing import Pipe, Process
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", required=True)
    args = parser.parse_args()
    parent, child = Pipe()
    process = Process(target=run_worker, args=(child, args.core), daemon=True)
    process.start()
    child.close()
    try:
        print(parent.recv())
        while True:
            line = sys.stdin.readline()
            if not line: break
            parent.send(__import__("json").loads(line))
            print(__import__("json").dumps(parent.recv()), flush=True)
    finally:
        if process.is_alive():
            process.terminate()
        process.join(2)
