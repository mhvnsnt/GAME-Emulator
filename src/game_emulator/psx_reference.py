"""PlayStation disc-set validation and local RetroArch reference launching.

This module never downloads, bundles, extracts, or commits commercial game data.
It only inspects owner-selected local CUE/BIN files and can hand the CUE to an
externally installed RetroArch/core for reference playback.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path
import subprocess
from typing import Any


_CUE_FILE_RE = re.compile(r'^\\s*FILE\\s+"([^"]+)"(?:\\s+|$)', re.IGNORECASE)
_CUE_FILE_UNQUOTED_RE = re.compile(r'^\\s*FILE\\s+([^\\s]+)(?:\\s+|$)', re.IGNORECASE)


def parse_cue_references(cue_path: Path) -> list[str]:
    """Return FILE targets from a CUE sheet, preserving order and duplicates."""
    cue_path = cue_path.expanduser().resolve(strict=True)
    if cue_path.suffix.lower() != ".cue":
        raise ValueError("content must be a .cue file")
    references: list[str] = []
    for line_number, raw in enumerate(cue_path.read_text(encoding="utf-8-sig", errors="strict").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("REM", "TITLE", "PERFORMER", "CATALOG", "CDTEXTFILE")):
            continue
        match = _CUE_FILE_RE.match(raw) or _CUE_FILE_UNQUOTED_RE.match(raw)
        if match:
            references.append(match.group(1))
        elif line.upper().startswith("FILE "):
            raise ValueError(f"unsupported FILE syntax at line {line_number}")
    return references


def validate_cue_set(cue_path: Path) -> dict[str, Any]:
    """Validate that every CUE-referenced track stays inside the CUE directory."""
    cue = cue_path.expanduser().resolve(strict=True)
    root = cue.parent
    tracks: list[dict[str, Any]] = []
    for raw_name in parse_cue_references(cue):
        candidate = (root / raw_name).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"CUE references a file outside its directory: {raw_name}") from exc
        if candidate.is_symlink():
            raise ValueError(f"CUE references a symlink track: {raw_name}")
        if not candidate.is_file():
            raise FileNotFoundError(f"CUE track is missing: {raw_name}")
        tracks.append({"name": raw_name, "path": str(candidate), "size_bytes": candidate.stat().st_size})
    if not tracks:
        raise ValueError("CUE contains no FILE tracks")
    return {"cue": str(cue), "tracks": tracks, "track_count": len(tracks)}


def find_retroarch(explicit: str | None = None) -> str | None:
    candidates = [explicit, os.environ.get("RETROARCH"), "retroarch",
                  "/usr/bin/retroarch", "/usr/games/retroarch"]
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate) if "/" not in candidate else candidate
        if path and Path(path).exists():
            return path
    return None


def find_psx_core(explicit: str | None = None) -> str | None:
    candidates = [
        explicit,
        os.environ.get("LIBRETRO_CORE"),
        str(Path.home() / ".config/retroarch/cores/pcsx_rearmed_libretro.so"),
        "/usr/lib/x86_64-linux-gnu/libretro/pcsx_rearmed_libretro.so",
        "/usr/lib/libretro/pcsx_rearmed_libretro.so",
        "/usr/lib/x86_64-linux-gnu/libretro/mednafen_psx_hw_libretro.so",
    ]
    return next((p for p in candidates if p and Path(p).is_file()), None)


def build_retroarch_command(
    cue_path: Path, *, retroarch: str, core: str, config: Path | None = None
) -> list[str]:
    validate_cue_set(cue_path)
    command = [retroarch, "--verbose"]
    if config:
        command += ["--config", str(config)]
    command += ["--libretro", core, str(cue_path.expanduser().resolve())]
    return command


def main() -> None:
    parser = argparse.ArgumentParser(description="Play an authorized local PS1 CUE through external RetroArch")
    parser.add_argument("--cue", type=Path, required=True)
    parser.add_argument("--retroarch")
    parser.add_argument("--core")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = validate_cue_set(args.cue)
    retroarch = find_retroarch(args.retroarch)
    core = find_psx_core(args.core)
    if not retroarch:
        raise SystemExit("RetroArch is not installed; install/provide it externally.")
    if not core:
        raise SystemExit("No external PS1 libretro core found; provide --core.")
    command = build_retroarch_command(args.cue, retroarch=retroarch, core=core, config=args.config)
    print(f"Validated PS1 disc: {manifest['cue']} ({manifest['track_count']} track file(s))")
    print(f"RetroArch: {retroarch}")
    print(f"Core: {core}")
    print("Command:", " ".join(command))
    if not args.dry_run:
        subprocess.run(command, check=False)


if __name__ == "__main__":
    main()
