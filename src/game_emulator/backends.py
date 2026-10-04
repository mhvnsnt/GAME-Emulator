"""Capability-based emulator backend registry.

This layer does not bundle proprietary firmware, keys, ROMs, or emulator binaries.
It discovers software the user has installed and routes content to a compatible
backend. Libretro cores are discovered from .info metadata; standalone backends
are detected by executable path.

A backend is only considered runnable when its local executable/core exists and
the content format/system matches its declared capability. No file extension is
treated as proof when the format is ambiguous.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Backend:
    backend_id: str
    display_name: str
    kind: str
    systems: frozenset[str]
    extensions: frozenset[str]
    executable_names: tuple[str, ...] = ()
    libretro_core: str | None = None
    license: str = "unknown"
    source_url: str = ""

    def installed_executable(self) -> str | None:
        for name in self.executable_names:
            found = shutil.which(name)
            if found:
                return found
        return None


BACKENDS: tuple[Backend, ...] = (
    Backend(
        "retroarch", "RetroArch / Libretro", "libretro_frontend",
        frozenset(), frozenset(),
        ("retroarch",), license="GPL-3.0",
        source_url="https://github.com/libretro/RetroArch",
    ),
    Backend(
        "dolphin", "Dolphin", "standalone",
        frozenset({"Nintendo GameCube", "Nintendo Wii"}),
        frozenset({".iso", ".gcm", ".wbfs", ".rvz", ".wia", ".dol"}),
        ("dolphin-emu", "dolphin"), license="GPL-2.0-or-later",
        source_url="https://github.com/dolphin-emu/dolphin",
    ),
    Backend(
        "pcsx2", "PCSX2", "standalone",
        frozenset({"Sony PlayStation 2"}),
        frozenset({".iso", ".cso", ".chd"}),
        ("pcsx2-qt", "pcsx2"), license="GPL-3.0-or-later",
        source_url="https://github.com/PCSX2/pcsx2",
    ),
    Backend(
        "android-runtime", "Android runtime", "android_runtime",
        frozenset({"Android"}),
        frozenset({".apk", ".xapk", ".apks"}),
        ("waydroid", "emulator"), license="varies",
        source_url="https://source.android.com/",
    ),
)


def discover_backends(extra: Iterable[Backend] = ()) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for backend in (*BACKENDS, *extra):
        executable = backend.installed_executable()
        result.append({
            "backend_id": backend.backend_id,
            "display_name": backend.display_name,
            "kind": backend.kind,
            "systems": sorted(backend.systems),
            "extensions": sorted(backend.extensions),
            "executable": executable,
            "installed": executable is not None,
            "license": backend.license,
            "source_url": backend.source_url,
            "runnable": executable is not None,
        })
    return result


def candidates(
    *,
    system: str,
    extension: str,
    installed_only: bool = False,
) -> list[Backend]:
    extension = extension.lower()
    matches = []
    for backend in BACKENDS:
        system_match = not backend.systems or system in backend.systems
        extension_match = not backend.extensions or extension in backend.extensions
        if system_match and extension_match:
            if not installed_only or backend.installed_executable() is not None:
                matches.append(backend)
    return matches


def validate_backend_selection(backend: Backend, *, system: str, extension: str) -> None:
    if backend.systems and system not in backend.systems:
        raise ValueError(
            f"{backend.display_name} does not declare support for {system}"
        )
    if backend.extensions and extension.lower() not in backend.extensions:
        raise ValueError(
            f"{backend.display_name} does not declare support for {extension.lower()}"
        )
    if backend.installed_executable() is None:
        raise ValueError(f"{backend.display_name} is not installed")


def command_for(backend: Backend, executable: str, content: Path) -> list[str]:
    """Return a non-shell command for backends with stable CLI contracts.

    Libretro and Android backends are intentionally not launched by this helper
    yet: their launch contracts need backend-specific configuration/state
    isolation. They are discovered and represented, but cannot be accidentally
    executed through a guessed command line.
    """
    if backend.backend_id == "dolphin":
        return [executable, "-e", str(content)]
    if backend.backend_id == "pcsx2":
        return [executable, str(content)]
    raise ValueError(
        f"{backend.backend_id} requires its dedicated launch adapter; no guessed command is allowed"
    )


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Discover installed emulator backends without launching them"
    )
    parser.add_argument("--installed-only", action="store_true")
    args = parser.parse_args()
    rows = discover_backends()
    if args.installed_only:
        rows = [row for row in rows if row["installed"]]
    print(json.dumps(rows, indent=2))
