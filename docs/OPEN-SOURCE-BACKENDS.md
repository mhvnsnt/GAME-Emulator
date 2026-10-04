# Open-source backend intake

GAME: Emulator treats emulator projects as external backends. We do not copy their
ROMs, BIOS files, keys, firmware, or proprietary game content into this repository.

## Curated upstream catalog

`src/game_emulator/open_source_catalog.py` records upstream project URLs, target
systems, integration type, conservative license labels, and intake notes. It is
metadata only: it downloads nothing, installs nothing, and executes no native code.
The catalog's `upstream_candidate` status means "research/integration candidate",
not "installed", "runnable", or "certified".

| Backend/project | Coverage | License recorded | Integration status |
|---|---|---|---|
| RetroArch | Multi-system frontend | GPL-3.0-only | Catalogued; requires a compatible core |
| Dolphin | GameCube / Wii | GPL-2.0-or-later | Catalogued; launcher/security work remains |
| PCSX2 | PlayStation 2 | GPL-3.0-or-later | Catalogued; launcher/security work remains |
| PPSSPP | PSP | GPL-2.0-or-later | Catalogued; launcher/security work remains |
| Azahar | Nintendo 3DS | GPL-2.0-or-later | Catalogued; current CLI launch intentionally disabled |
| mGBA | Game Boy / Game Boy Color / Game Boy Advance | MPL-2.0 | Upstream candidate; requires installed core/metadata |
| Nestopia UE | NES | GPL-2.0-or-later | Upstream candidate; requires installed core/metadata |
| Beetle PSX | PlayStation | GPL-2.0-or-later | Upstream candidate; requires installed core/metadata |
| Snes9x | Super Nintendo | Non-commercial in Libretro core inventory | Upstream candidate; redistribution requires permission review |\n| Gambatte | Game Boy / Game Boy Color | GPLv2 (verify exact revision) | Upstream candidate; local metadata required |\n| FCEUmm | NES / Famicom | GPLv2 (verify exact revision) | Upstream candidate; local metadata required |\n| Mesen | NES / Famicom | GPLv3 (verify exact revision) | Upstream candidate; local metadata required |\n| Mupen64Plus-Next | Nintendo 64 | Verify exact revision | Upstream candidate; local metadata required |\n| Beetle Saturn | Sega Saturn | GPLv2 (verify exact revision) | Upstream candidate; local metadata required |
| Beetle GBA | Game Boy Advance | GPLv2 (verify exact revision) | Upstream candidate; local metadata required |
| Beetle bsnes | Super Nintendo | GPLv2 (verify exact revision) | Upstream candidate; local metadata required |
| Mesen-S | SNES / Game Boy / Game Boy Color | GPLv3 (verify exact revision) | Upstream candidate; local metadata required |
| Flycast | Dreamcast / NAOMI | GPLv2 | Upstream candidate; local metadata required |
| MesenCE | NES / FDS / SNES / GB / GBC / GBA / PC Engine / Master System / Game Gear / WonderSwan | GPLv3 (verify exact revision) | Upstream candidate; local metadata required |
| Android runtime | APK/APKS/XAPK | Runtime-dependent | Package detection only; no host execution |

The upstream Libretro core catalog lists many more systems and cores, but a catalog
entry is not proof of a compatible installed binary. Official references:

- [Libretro core list](https://docs.libretro.com/guides/core-list/)
- [Libretro license inventory, including non-commercial entries](https://docs.libretro.com/development/licenses/)
- [RetroArch upstream](https://github.com/libretro/RetroArch)
- [mGBA upstream](https://github.com/mgba-emu/mgba)
- [Nestopia UE upstream](https://github.com/libretro/nestopia)
- [Beetle PSX upstream](https://github.com/libretro/beetle-psx-libretro)
- [Official MesenCE Libretro documentation](https://docs.libretro.com/library/mesen2/)
- [Official Flycast Libretro documentation](https://docs.libretro.com/library/flycast/)
- [Official Beetle GBA Libretro documentation](https://docs.libretro.com/library/beetle_gba/)
- [Official Beetle bsnes Libretro documentation](https://docs.libretro.com/library/beetle_bsnes/)
- [Official Mesen-S Libretro documentation](https://docs.libretro.com/library/mesen-s/)

## License and provenance gate

The catalog intentionally marks every project as **not cleared for redistribution**
until a human reviews the exact release, its dependencies, bundled assets, notices,
and license terms. A project-level license label can be incomplete or can differ
from the license of a particular binary, dependency, or asset. Some projects in the
wider Libretro ecosystem are explicitly non-commercial; do not vendor or package
those into a commercial product without separate permission. Unknown or custom
license identifiers are not treated as permissive licenses.

## Integration rule

For every new backend:

1. verify the upstream project and current license;
2. record its supported systems and input/content formats;
3. detect an installed runtime without executing it;
4. match the installed core's metadata against both system and extension;
5. define a deterministic non-shell launch contract;
6. put the runtime behind a verified OS sandbox policy before execution;
7. add synthetic adapter tests;
8. add an opt-in real smoke test using only locally installed, authorized content;
9. never download proprietary BIOS, firmware, keys, ROMs, ISOs, APKs, or game data.

## Modern platforms

A platform being recognized by the file intake layer does **not** mean an emulator
exists in this repository for it. Switch, newer Xbox generations, and newer
PlayStation generations require separate native backends and may require user-
supplied system components. They will be added only after an upstream backend is
verified and its execution contract can be sandboxed.

This distinction is intentional: "recognized", "supported by a backend", and
"verified runnable on this machine" are three different states.


## Linux containment gate

The Libretro worker's strict Landlock path now requires ABI 10 before it reports
TCP/UDP network denial. Older Landlock versions may restrict TCP while leaving UDP
available, so they fail closed instead of being labeled as network-isolated.
The worker also applies process resource limits and `no_new_privs`; this is not a
claim that all host interfaces are unavailable. CI's mocked policy tests validate
the fail-closed decision and reported status, not actual kernel containment. A real
containment test must run in a host where Landlock is permitted and demonstrate
blocked filesystem writes and network access before native launch can be certified.
