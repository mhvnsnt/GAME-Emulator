"""Curated upstream catalog for backend discovery and license-aware intake.

This module contains project metadata only. It does not download, bundle, or run
emulators, cores, firmware, BIOS files, keys, or game content. License labels are
conservative project-level references and must be rechecked against the exact
version/artifact before redistribution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class OpenSourceProject:
    project_id: str
    display_name: str
    systems: tuple[str, ...]
    integration_kind: str
    upstream_url: str
    license_label: str
    status: str
    notes: str


PROJECTS: tuple[OpenSourceProject, ...] = (
    OpenSourceProject(
        "retroarch", "RetroArch", ("multi-system frontend",), "frontend",
        "https://github.com/libretro/RetroArch", "GPL-3.0-only", "catalogued",
        "Frontend only; a compatible installed core is required.",
    ),
    OpenSourceProject(
        "dolphin", "Dolphin", ("Nintendo GameCube", "Nintendo Wii"), "standalone",
        "https://github.com/dolphin-emu/dolphin", "GPL-2.0-or-later", "catalogued",
        "Requires user-supplied authorized content and any required system files.",
    ),
    OpenSourceProject(
        "pcsx2", "PCSX2", ("Sony PlayStation 2",), "standalone",
        "https://github.com/PCSX2/pcsx2", "GPL-3.0-or-later", "catalogued",
        "Firmware is not bundled or downloaded by this project.",
    ),
    OpenSourceProject(
        "ppsspp", "PPSSPP", ("Sony PlayStation Portable",), "standalone",
        "https://github.com/hrydgard/ppsspp", "GPL-2.0-or-later", "catalogued",
        "Do not infer that every file extension or platform build is supported.",
    ),
    OpenSourceProject(
        "azahar", "Azahar", ("Nintendo 3DS",), "standalone_or_libretro",
        "https://github.com/azahar-emu/azahar", "GPL-2.0-or-later", "catalogued",
        "Current standalone command-line launch remains unverified and disabled.",
    ),
    OpenSourceProject(
        "mgba", "mGBA", ("Nintendo Game Boy", "Nintendo Game Boy Color", "Nintendo Game Boy Advance"), "libretro_or_standalone",
        "https://github.com/mgba-emu/mgba", "MPL-2.0", "upstream_candidate",
        "Match installed core .info system and extension metadata; recheck exact release license.",
    ),
    OpenSourceProject(
        "nestopia", "Nestopia UE", ("Nintendo NES",), "libretro_core",
        "https://github.com/libretro/nestopia", "GPL-2.0-or-later", "upstream_candidate",
        "Core must be installed locally and its .info metadata must match the target.",
    ),
    OpenSourceProject(
        "beetle-psx", "Beetle PSX", ("Sony PlayStation",), "libretro_core",
        "https://github.com/libretro/beetle-psx-libretro", "GPL-2.0-or-later", "upstream_candidate",
        "Core must be installed locally; required firmware is never supplied here.",
    ),
    OpenSourceProject(
        "snes9x", "Snes9x", ("Nintendo Super Nintendo Entertainment System",), "libretro_or_standalone",
        "https://github.com/snes9xgit/snes9x", "Snes9x", "upstream_candidate",
        "Libretro's current core license inventory lists Snes9x as non-commercial; do not redistribute without permission.",
    ),
    OpenSourceProject(
        "gambatte", "Gambatte", ("Nintendo Game Boy", "Nintendo Game Boy Color"), "libretro_core",
        "https://github.com/libretro/gambatte-libretro", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Candidate coverage is metadata-driven; no core binary is bundled.",
    ),
    OpenSourceProject(
        "fceumm", "FCEUmm", ("Nintendo NES",), "libretro_core",
        "https://github.com/libretro/libretro-fceumm", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Candidate coverage is metadata-driven; FDS extension support must match installed .info metadata.",
    ),
    OpenSourceProject(
        "quicknes", "QuickNES", ("Nintendo NES",), "libretro_core",
        "https://github.com/libretro/QuickNES_Core", "GPLv2 (Libretro core docs)", "upstream_candidate",
        "Official Libretro docs list .nes content; local system and extension metadata must both match.",
    ),
    OpenSourceProject(
        "sameboy", "SameBoy", ("Nintendo Game Boy", "Nintendo Game Boy Color"), "libretro_core",
        "https://github.com/libretro/SameBoy", "MIT (Libretro core docs)", "upstream_candidate",
        "Official Libretro docs list .gb and .gbc; exact release dependencies still need review.",
    ),
    OpenSourceProject(
        "scummvm", "ScummVM", ("classic adventure game engines",), "libretro_core_or_standalone",
        "https://github.com/scummvm/scummvm", "GPLv2 (Libretro core docs; verify exact build)", "upstream_candidate",
        "Libretro core uses .scummvm launch-hook files and user-supplied game data; not a generic ROM core.",
    ),
    OpenSourceProject(
        "mesen", "Mesen", ("Nintendo NES",), "libretro_core",
        "https://github.com/SourMesen/Mesen", "GPLv3 (verify exact revision)", "upstream_candidate",
        "Core may support additional systems; only explicit system/extension metadata is matched.",
    ),
    OpenSourceProject(
        "mupen64plus-next", "Mupen64Plus-Next", ("Nintendo 64",), "libretro_core",
        "https://github.com/libretro/mupen64plus-libretro-nx", "GPL (verify exact revision)", "upstream_candidate",
        "N64 content support varies by core build and extension metadata.",
    ),
    OpenSourceProject(
        "beetle-saturn", "Beetle Saturn", ("Sega Saturn",), "libretro_core",
        "https://github.com/libretro-mirrors/beetle-saturn-libretro", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Disc formats and firmware requirements must be checked against installed metadata and official docs.",
    ),
    OpenSourceProject(
        "beetle-gba", "Beetle GBA", ("Nintendo Game Boy Advance",), "libretro_core",
        "https://github.com/libretro/beetle-gba-libretro", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Official Libretro docs list .gba, .agb, and .bin; firmware needs are build/options dependent.",
    ),
    OpenSourceProject(
        "beetle-bsnes", "Beetle bsnes", ("Nintendo Super Nintendo Entertainment System",), "libretro_core",
        "https://github.com/libretro/beetle-bsnes-libretro", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Legacy core candidate; match local system and extension metadata before offering it.",
    ),
    OpenSourceProject(
        "mesen-s", "Mesen-S", ("Nintendo Super Nintendo Entertainment System", "Nintendo Game Boy", "Nintendo Game Boy Color"), "libretro_core",
        "https://github.com/SourMesen/Mesen", "GPLv3 (verify exact revision)", "upstream_candidate",
        "Official Libretro docs list SNES/SFC, Game Boy, and Game Boy Color coverage.",
    ),
    OpenSourceProject(
        "flycast", "Flycast", ("Sega Dreamcast / NAOMI",), "libretro_core",
        "https://github.com/flyinghead/flycast", "GPLv2 (verify exact revision)", "upstream_candidate",
        "Official Libretro docs list Dreamcast/NAOMI/Atomiswave; match local extensions and system metadata.",
    ),
    OpenSourceProject(
        "mesence", "MesenCE", (
            "Nintendo NES", "Nintendo Famicom Disk System",
            "Nintendo Super Nintendo Entertainment System", "Nintendo Game Boy",
            "Nintendo Game Boy Color", "Nintendo Game Boy Advance",
            "NEC PC Engine", "NEC PC Engine CD", "Sega Master System",
            "Sega Game Gear", "Bandai WonderSwan", "Bandai WonderSwan Color",
        ), "libretro_core",
        "https://github.com/libretro/Mesen", "GPL-3.0-only (verify exact revision)", "upstream_candidate",
        "Multi-system Mesen port; exact installed .info system/extension metadata remains authoritative.",
    ),
)


def list_projects(*, systems: set[str] | None = None) -> list[dict[str, object]]:
    """Return metadata-only project records, optionally filtered by exact system."""
    rows = []
    for project in PROJECTS:
        if systems is not None and not systems.intersection(project.systems):
            continue
        rows.append(asdict(project))
    return rows


def get_project(project_id: str) -> OpenSourceProject | None:
    """Find a catalog entry by its stable ID; unknown IDs return None."""
    normalized = project_id.strip().casefold()
    return next((p for p in PROJECTS if p.project_id == normalized), None)


def redistribution_eligibility(project_id: str) -> dict[str, str | bool]:
    """Catalog membership never substitutes for exact-release license review."""
    project = get_project(project_id)
    if project is None:
        return {"eligible": False, "status": "unknown_project", "reason": "No verified catalog record."}
    return {
        "eligible": False,
        "status": "manual_license_review_required",
        "reason": (
            f"Catalog license is {project.license_label}; verify the exact release, "
            "dependencies, assets, and license notices before redistribution."
        ),
    }
