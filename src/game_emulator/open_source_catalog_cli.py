"""CLI for inspecting upstream projects and locally installed Libretro core metadata.

This tool never downloads, loads, or executes emulator code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from game_emulator.adapters import compatible_cores, inventory_cores
from game_emulator.open_source_catalog import list_projects, redistribution_eligibility

# Explicit aliases bridge human-facing catalog labels to names emitted by
# Libretro .info files. A match requires BOTH system and at least one known
# extension; a core's filename is never treated as proof of compatibility.
LIBRETRO_TARGETS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "mgba": (
        ("Nintendo Game Boy Advance", ("gba",)),
        ("Nintendo Game Boy Color", ("gbc",)),
        ("Nintendo Game Boy", ("gb",)),
    ),
    "nestopia": (
        ("Nintendo NES", ("nes", "unf", "unif", "nsf")),
        ("Nintendo Entertainment System", ("nes", "unf", "unif", "nsf")),
        ("Nintendo Famicom Disk System", ("fds",)),
    ),
    "beetle-psx": (
        ("Sony PlayStation", ("cue", "ccd", "chd", "pbp", "toc", "m3u")),
    ),
}


def installed_core_matches(inventory: dict[str, object]) -> list[dict[str, object]]:
    """Match catalog candidates against installed core .info metadata, not file names."""
    matches: list[dict[str, object]] = []
    for project in list_projects():
        project_id = str(project["project_id"])
        targets = LIBRETRO_TARGETS.get(project_id, ())
        project_matches: list[dict[str, object]] = []
        for system, extensions in targets:
            for extension in extensions:
                for core in compatible_cores(inventory, system=system, extension=extension):
                    match = {
                        "system": system,
                        "matched_extension": extension,
                        "core_file": core.get("file"),
                        "display_name": core.get("display_name"),
                        "supported_extensions": core.get("supported_extensions", []),
                        "sha256": core.get("sha256"),
                        "metadata_present": core.get("metadata_present", False),
                        "trust_status": core.get("trust_status", "unknown"),
                    }
                    if match not in project_matches:
                        project_matches.append(match)
        if project_matches:
            matches.append({
                "project_id": project_id,
                "display_name": project["display_name"],
                "installed_metadata_matches": project_matches,
                "warning": "Metadata match only; runtime compatibility and sandboxing are not certified.",
            })
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List upstream emulator projects and optionally match installed Libretro metadata"
    )
    parser.add_argument("--system", action="append", default=[], help="exact system label; may be repeated")
    parser.add_argument("--license-review", metavar="PROJECT_ID", help="show conservative redistribution review status")
    parser.add_argument("--installed-cores", type=Path, help="directory of installed .dll/.so/.dylib core files")
    parser.add_argument("--info", type=Path, help="directory of matching Libretro .info metadata")
    args = parser.parse_args()
    if args.license_review:
        result = redistribution_eligibility(args.license_review)
    else:
        projects = list_projects(systems=set(args.system) if args.system else None)
        result: dict[str, object] = {"projects": projects}
        if args.installed_cores:
            inventory = inventory_cores(args.installed_cores, args.info)
            result["core_inventory"] = inventory
            result["installed_metadata_matches"] = installed_core_matches(inventory)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
