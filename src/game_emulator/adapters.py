"""Inventory installed Libretro cores without loading or executing native libraries."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

CORE_SUFFIXES = {".dll", ".so", ".dylib"}


def _normalize_system(value: str) -> str:
    """Normalize Libretro vendor separators without broad fuzzy matching."""
    return " ".join(value.replace("-", " ").split()).casefold()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_info(path: Path) -> dict[str, str]:
    """Parse the simple key = "value" subset used by Libretro .info metadata."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _pipe_values(info: dict[str, str], key: str) -> list[str]:
    return [x.strip() for x in info.get(key, "").split("|") if x.strip()]


def _supported_systems(info: dict[str, str]) -> list[str]:
    """Use explicit database entries as well as systemname.

    Libretro .info files commonly put the actual database/system mapping in
    'database', while 'systemname' may be a single display label. Keep both,
    because multi-system cores can legitimately advertise several databases.
    """
    values = _pipe_values(info, "database") + _pipe_values(info, "systemname")
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _normalize_system(value)
        if normalized not in seen:
            seen.add(normalized)
            result.append(value)
    return result


def compatible_cores(
    inventory: dict[str, Any],
    *,
    system: str,
    extension: str,
) -> list[dict[str, Any]]:
    """Return installed cores matching both system and extension metadata."""
    normalized_extension = extension.lower().lstrip(".")
    matches: list[dict[str, Any]] = []
    for core in inventory.get("cores", []):
        systems = set(core.get("supported_systems", []))
        extensions = {
            str(value).lower().lstrip(".")
            for value in core.get("supported_extensions", [])
        }
        normalized_system = _normalize_system(system)
        system_match = any(
            normalized_system == _normalize_system(value) for value in systems
        )
        extension_match = normalized_extension in extensions
        if system_match and extension_match:
            matches.append(core)
    return matches


def inventory_cores(core_dir: Path, info_dir: Path | None = None) -> dict[str, Any]:
    """Hash and describe installed core files; never dlopen or run them."""
    root = core_dir.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("core_dir must be a directory")
    metadata_root = (info_dir or root).expanduser().resolve()
    if not metadata_root.is_dir():
        raise ValueError("info_dir must be a directory")
    entries: list[dict[str, Any]] = []
    for core in sorted(root.iterdir()):
        if core.is_symlink() or not core.is_file() or core.suffix.lower() not in CORE_SUFFIXES:
            continue
        info_path = metadata_root / (core.stem + ".info")
        info = parse_info(info_path)
        entries.append({
            "file": core.name,
            "path": str(core.resolve()),
            "sha256": sha256_file(core),
            "size_bytes": core.stat().st_size,
            "info_file": str(info_path) if info else None,
            "display_name": info.get("display_name", core.stem),
            "corename": info.get("corename", ""),
            "supported_extensions": _pipe_values(info, "supported_extensions"),
            "supported_systems": _supported_systems(info),
            "system_id": info.get("systemid", ""),
            "database": _pipe_values(info, "database"),
            "license": info.get("license", ""),
            "permissions": info.get("permissions", ""),
            "firmware": sorted({
                value for key, value in info.items()
                if key.startswith("firmware") and key.endswith(("_path", "_desc")) and value
            }),
            "metadata_present": bool(info),
            "native_code_loaded": False,
            "trust_status": "inventory_only_not_executed",
        })
    return {
        "host_platform": platform.platform(),
        "architecture": platform.machine(),
        "core_directory": str(root),
        "core_count": len(entries),
        "cores": entries,
        "warning": (
            "File presence and .info metadata do not prove runtime compatibility. "
            "Native cores were not loaded or executed."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory installed Libretro cores without loading them"
    )
    parser.add_argument(
        "--cores", type=Path, required=True,
        help="directory containing installed .dll/.so/.dylib cores",
    )
    parser.add_argument(
        "--info", type=Path, help="directory containing matching Libretro .info metadata"
    )
    parser.add_argument("--output", type=Path, help="optional JSON report destination")
    args = parser.parse_args()
    try:
        report = inventory_cores(args.cores, args.info)
        rendered = json.dumps(report, indent=2)
        if args.output:
            args.output.expanduser().write_text(rendered + "\n", encoding="utf-8")
            print(f"Wrote core inventory: {args.output}")
        else:
            print(rendered)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
