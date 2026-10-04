"""Explicit process-launch boundary for native emulator backends.

Native emulator binaries are not trusted merely because they are installed locally.
This module refuses a real launch unless the caller supplies an external OS sandbox
launcher. Platform-specific profiles own the actual isolation policy; we never guess
a sandbox command.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class LaunchSandboxError(RuntimeError):
    """Raised when a native launch has no explicit OS sandbox boundary."""


@dataclass(frozen=True)
class SandboxLauncher:
    executable: str
    prefix_args: tuple[str, ...] = ()
    separator: str = "--"

    @classmethod
    def from_spec(cls, spec: str) -> "SandboxLauncher":
        parts = shlex.split(spec)
        if not parts:
            raise LaunchSandboxError("sandbox launcher specification is empty")
        executable = parts[0]
        resolved = shutil.which(executable)
        if resolved is None and Path(executable).is_file():
            resolved = str(Path(executable).resolve())
        if resolved is None:
            raise LaunchSandboxError(
                f"explicit sandbox launcher was not found: {executable}"
            )
        return cls(resolved, tuple(parts[1:]))

    def wrap(self, command: list[str]) -> list[str]:
        if not command:
            raise LaunchSandboxError("native launch command is empty")
        return [self.executable, *self.prefix_args, self.separator, *command]


def sandbox_launcher_from_environment() -> SandboxLauncher:
    spec = os.environ.get("GAME_EMULATOR_SANDBOX_LAUNCHER")
    if not spec:
        raise LaunchSandboxError(
            "native launch refused: set GAME_EMULATOR_SANDBOX_LAUNCHER "
            "to an explicit OS sandbox wrapper"
        )
    return SandboxLauncher.from_spec(spec)


def launch_sandboxed(
    command: list[str],
    *,
    cwd: Path,
    sandbox: SandboxLauncher | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    wrapper = sandbox or sandbox_launcher_from_environment()
    wrapped = wrapper.wrap(command)
    result: dict[str, object] = {
        "command": wrapped,
        "sandboxed": True,
        "dry_run": dry_run,
    }
    if not dry_run:
        process = subprocess.Popen(wrapped, shell=False, cwd=str(cwd))
        result.update({"status": "launched", "pid": process.pid})
    else:
        result["status"] = "command_ready"
    return result
