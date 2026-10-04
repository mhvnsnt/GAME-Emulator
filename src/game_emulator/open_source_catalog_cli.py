"""CLI for inspecting upstream projects and locally installed Libretro core metadata.

This tool never downloads, loads, or executes emulator code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from game_emulator.adapters import compatible_cores, inventory_cores
from game_emulator.open_source_catalog import list_projects, redistribution_eligibility

# These are curated targets based on upstream Libretro core documentation.
# Actual local .info metadata remains authoritative: BOTH system and extension
# must match. This table is a discovery aid, not a claim that a core is installed.
LIBRETRO_TARGETS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "mgba": (
        ("Nintendo Game Boy Advance", ("gba",)),
        ("Nintendo Game Boy Color", ("gbc",)),
        ("Nintendo Game Boy", ("gb",)),
    ),
    "gambatte": (
        ("Nintendo Game Boy", ("gb",)),
        ("Nintendo Game Boy Color", ("gbc",)),
        ("Game Boy/Color", ("gb", "gbc")),
    ),
    "beetle-gba": (
        ("Nintendo Game Boy Advance", ("gba", "agb", "bin")),
    ),
    "nestopia": (
        ("Nintendo NES", ("nes", "unf", "unif", "nsf")),
        ("Nintendo Entertainment System", ("nes", "unf", "unif", "nsf")),
        ("Nintendo NES/Famicom", ("nes", "unf", "unif", "nsf")),
        ("Nintendo - Nintendo Entertainment System", ("nes", "unf", "unif", "nsf")),
        ("Nintendo - Family Computer Disk System", ("fds",)),
        ("Nintendo Famicom Disk System", ("fds",)),
    ),
    "fceumm": (
        ("Nintendo NES", ("nes", "unf", "unif")),
        ("Nintendo NES/Famicom", ("nes", "unf", "unif")),
        ("Nintendo - Nintendo Entertainment System", ("nes", "unf", "unif")),
        ("Nintendo - Family Computer Disk System", ("fds",)),
        ("Nintendo Famicom Disk System", ("fds",)),
    ),
    "mesen": (
        ("Nintendo NES", ("nes", "unf", "unif")),
        ("Nintendo NES/Famicom", ("nes", "unf", "unif")),
        ("Nintendo - Nintendo Entertainment System", ("nes", "unf", "unif")),
        ("Nintendo - Family Computer Disk System", ("fds",)),
    ),
    "snes9x": (
        ("Nintendo Super Nintendo Entertainment System", ("sfc", "smc")),
        ("Nintendo SNES/SFC", ("sfc", "smc", "swc", "fig", "bs", "st")),
        ("Nintendo Sufami Turbo", ("st",)),
    ),
    "beetle-bsnes": (
        ("Nintendo Super Nintendo Entertainment System", ("smc", "fig", "bs", "st", "sfc")),
    ),
    "mesen-s": (
        ("Nintendo Super Nintendo Entertainment System", ("sfc", "smc", "fig", "swc", "bs")),
        ("Nintendo Game Boy", ("gb",)),
        ("Nintendo Game Boy Color", ("gbc",)),
    ),
    "flycast": (
        ("Sega - Dreamcast/NAOMI", ("cdi", "gdi", "chd", "cue", "bin", "elf", "zip")),
    ),
    "mesence": (
        ("Nintendo - Nintendo Entertainment System", ("nes", "fds", "unf", "unif")),
        ("Nintendo - Family Computer Disk System", ("fds",)),
        ("Nintendo Super Nintendo Entertainment System", ("sfc", "smc", "swc", "fig", "bs")),
        ("Nintendo Game Boy", ("gb",)),
        ("Nintendo Game Boy Color", ("gbc",)),
        ("Nintendo Game Boy Advance", ("gba",)),
        ("NEC - PC Engine", ("pce", "sgx")),
        ("NEC - PC Engine CD", ("cue",)),
        ("Sega - Master System", ("sms",)),
        ("Sega - Game Gear", ("gg",)),
        ("Bandai - WonderSwan", ("ws",)),
        ("Bandai - WonderSwan Color", ("wsc",)),
    ),
    "beetle-psx": (
        ("Sony PlayStation", ("cue", "ccd", "chd", "pbp", "toc", "m3u")),
    ),
    "beetle-saturn": (
        ("Sega Saturn", ("cue", "toc", "m3u", "ccd", "chd")),
    ),
    "mupen64plus-next": (
        ("Nintendo 64", ("n64", "z64", "v64")),
        ("Nintendo - Nintendo 64", ("n64", "z64", "v64")),
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
