"""CLI for inspecting upstream projects and locally installed Libretro core metadata.

This tool never downloads, loads, or executes emulator code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from game_emulator.adapters import compatible_cores, inventory_cores
from game_emulator.open_source_catalog import list_projects, redistribution_eligibility

# Catalog labels are human-facing; these are explicit, conservative bridges to
# the system names commonly emitted by Libretro .info files.
LIBRETRO_SYSTEM_ALIASES: dict[str, tuple[str, ...]] = {
    "mgba": (
        "Nintendo Game Boy Advance",
        "Nintendo Game Boy Color",
        "Nintendo Game Boy",
    ),
    "nestopia": (
        "Nintendo NES",
        "Nintendo Entertainment System",
        "Nintendo Famicom Disk System",
    ),
    "beetle-psx": ("Sony PlayStation",),
}


def installed_core_matches(inventory: dict[str, object]) -> list[dict[str, object]]:
    """Match catalog candidates against installed core .info metadata, not file names."""
    projects = list_projects()
    matches: list[dict[str, object]] = []
    for project in projects:
        project_id = str(project["project_id"])
        systems = LIBRETRO_SYSTEM_ALIASES.get(project_id, ())
        if not systems:
            continue
        project_matches: list[dict[str, object]] = []
        for system in systems:
            for core in compatible_cores(inventory, system=system, extension=_extension_for_system(system)):
                match = {
                    "system": system,
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


def _extension_for_system(system: str) -> str:
    """Use a known representative extension to require system AND extension metadata."""
    return {
        "Nintendo Game Boy Advance": ".gba",
        "Nintendo Game Boy Color": ".gbc",
        "Nintendo Game Boy": ".gb",
        "Nintendo NES": ".nes",
        "Nintendo Entertainment System": ".nes",
        "Nintendo Famicom Disk System": ".fds",
        "Sony PlayStation": ".cue",
    }[system]


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
