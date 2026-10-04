"""Explicit process-launch boundary for native emulator backends.

A configured wrapper is not proof of a sandbox: arbitrary commands can be no-ops
or can leave host access unrestricted. Until a platform-specific policy is
implemented and verified, this module supports command previews only and refuses
real native launches. Never infer containment from multiprocessing or a wrapper
name alone.
"""
from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path


class LaunchSandboxError(RuntimeError):
    """Raised when a native launch has no verified OS sandbox policy."""


@dataclass(frozen=True)
class SandboxLauncher:
    """A syntactically resolved wrapper command; not a security attestation."""

    executable: str
    prefix_args: tuple[str, ...] = ()
    separator: str = "--"

    @classmethod
    def from_spec(cls, spec: str) -> SandboxLauncher:
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
            "native launch refused: no explicit OS sandbox wrapper is configured"
        )
    return SandboxLauncher.from_spec(spec)


def launch_sandboxed(
    command: list[str],
    *,
    cwd: Path,
    sandbox: SandboxLauncher | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Preview a wrapped command; refuse execution until policy enforcement exists.

    The current generic wrapper contract does not prove that the wrapper applies
    filesystem, network, process, and resource restrictions. Dry-runs are useful
    for inspecting argv, but a real launch would be misleadingly unsafe here.
    """
    wrapper = sandbox or sandbox_launcher_from_environment()
    wrapped = wrapper.wrap(command)
    result: dict[str, object] = {
        "command": wrapped,
        "sandboxed": False,
        "sandbox_wrapper_configured": True,
        "security_status": "unverified-policy",
        "dry_run": dry_run,
    }
    if not dry_run:
        raise LaunchSandboxError(
            "native launch refused: wrapper command is not a verified OS sandbox policy; "
            "platform-specific containment must be implemented first"
        )
    result["status"] = "command_preview_only"
    return result
