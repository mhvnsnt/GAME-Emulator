# Open-source backend intake

GAME: Emulator treats emulator projects as external backends. We do not copy their
ROMs, BIOS files, keys, firmware, or proprietary game content into this repository.

| Backend | Coverage | License | Integration |
|---|---|---|---|
| RetroArch / Libretro | Broad multi-system core ecosystem | RetroArch GPL-3.0; Libretro API MIT | Installed-core inventory + isolated ctypes worker |
| Dolphin | GameCube / Wii | GPL-2.0-or-later | Capability registry; dedicated launcher next |
| PCSX2 | PlayStation 2 | GPL-3.0-or-later | Capability registry; dedicated launcher next |
| Android runtime | APK/APKS/XAPK | Runtime-dependent | Package detection; Android launch adapter next |

The Libretro core catalog already includes examples for PlayStation, GameCube/Wii,
Xbox, PSP, Dreamcast, Nintendo handhelds/consoles and many other systems. Core
selection remains metadata- and installation-driven.

## Integration rule

For every new backend:

1. verify the upstream project and current license;
2. record its supported systems and input/content formats;
3. detect an installed runtime without executing it;
4. define a deterministic non-shell launch contract;
5. put the runtime behind the appropriate OS sandbox boundary;
6. add a synthetic adapter test;
7. add an opt-in real smoke test using only locally installed, authorized content;
8. never download proprietary BIOS, firmware, keys, ROMs, ISOs, APKs, or game data.

## Modern platforms

A platform being recognized by the file intake layer does **not** mean an emulator
exists in this repository for it. Switch, newer Xbox generations, and newer
PlayStation generations require separate native backends and may require user-
supplied system components. They will be added only after an upstream backend is
verified and its execution contract can be sandboxed.

This distinction is intentional: "recognized", "supported by a backend", and
"verified runnable on this machine" are three different states.
