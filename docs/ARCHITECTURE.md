# Architecture and boundaries

## Implemented local flow

```text
User selects local source folder
  -> recursive scan / extension allowlist / size and symlink checks
  -> SHA-256 source fingerprint and stability check
  -> classify by known extension and parent-folder labels
  -> copy to content-addressed library
  -> hash verification of stored copy
  -> SQLite metadata + deduplication
  -> local loopback dashboard / CLI catalog
```

The source remains unchanged. The app never unpacks archives, executes imported content, downloads missing firmware, or sends game files to GitHub/cloud services. The local dashboard binds to loopback only and is not a general-purpose file server.

## System identification

Extensions are hints, not proof. Shared extensions such as ISO/BIN/PKG/ELF remain ambiguous unless the directory label supplies a clear system. A later metadata adapter can offer likely matches but should retain confidence and never silently assert a guess as fact.

## Integration stages

1. Continuous folder/removable-drive watcher with safe handling of partially copied files.
2. Metadata adapters with opt-in network access to legitimate catalog sources.
3. Capability registry for installed emulator frontends/cores, licenses, system coverage and firmware prerequisites.
4. Expand the explicit RetroArch launch handoff into the capability-tested backend registry in `src/game_emulator/backends.py`; Libretro `.info` metadata is matched against system + extension before a core can be selected.
5. Add dedicated launch adapters for standalone open-source backends (Dolphin/PCSX2/PPSSPP) and Android runtimes; each adapter must declare its exact CLI/API contract instead of guessing.
6. Add Switch/modern-console backends only when a maintained, legally redistributable emulator/runtime and its required user-supplied system components are explicitly installed.
7. Save/state isolation, controller mapping, frame transport and runtime test evidence.
8. Reversible per-game mod profiles, load order, conflict detection and rollback. Mixing must be format/game-specific; unrelated console binaries cannot be generically blended.
9. Optional isolated analysis adapters with explicit invocation, audit logs, and resource ceilings.

## Native execution gate

Native emulator processes and Libretro cores are untrusted code. The Libretro worker's process separation is crash containment, not by itself a security sandbox. Likewise, a configured command wrapper is not evidence that filesystem, network, process, and resource restrictions are enforced.

`native_launch.py` currently permits command previews only. Real native launch is intentionally refused until a platform-specific OS sandbox profile is implemented and tested. Linux strict worker mode must fail closed if the required Landlock policy cannot be installed; Windows Job Objects are resource/process controls, not AppContainer filesystem/network isolation; macOS must not claim Seatbelt/App Sandbox isolation before a verified launch-time profile exists. Never report `sandboxed: true` merely because a wrapper executable was configured.

A future launch profile must have tests that demonstrate denied host-file access, denied network access, bounded resource use, child-process policy, clean shutdown, and correct access to only the intended runtime/content paths. CI running inside a container that blocks a security primitive is not proof that the primitive works.

## Analysis tools

Ghidra and radare2 are optional, separately invoked analysis tools—not default intake steps. AssetStudio is not a universal package extractor. Playwright tests this app's UI. Browser automation must not defeat anti-bot protections or fetch protected binaries. Do not automatically translate proprietary decompiler output into a substitute implementation.

## Threat model

Treat filenames, imported content, emulator binaries, and native cores as untrusted. Never shell-interpolate filenames. Do not expose the library to the web server or network. Keep reports free of file contents and secrets. Do not execute native content until a verified OS containment policy is active. Process separation alone is not sufficient.

## Emulator coverage model

The goal is broad *backend orchestration*, not one magical emulator binary. Libretro exposes a large catalog of cores across Nintendo, PlayStation, Sega, arcade, PC and other systems, but a core must actually be installed and its metadata must declare the target system/format before this project can select it.

Standalone systems use dedicated adapters. Dolphin covers GameCube/Wii; PCSX2 covers PS2; PPSSPP covers PSP. Android APK/APKS/XAPK files are package artifacts, not console ROMs, so they require an Android runtime/VM adapter rather than being sent to a Libretro core. Switch and other modern platforms likewise require a compatible native backend plus whatever system components that backend legitimately requires.

This project will not download copyrighted games, console firmware, decryption keys, BIOS dumps, or proprietary runtime components. It can index and route user-supplied files that the user is authorized to use.

## Open-source backend sources

The registry records upstream projects and licenses rather than silently vendoring or modifying their binaries:

- RetroArch / Libretro: GPL-3.0 frontend; Libretro API is MIT.
- Dolphin: GPL-2.0-or-later.
- PCSX2: GPL-3.0-or-later.
- PPSSPP: GPL-2.0-or-later.
- Azahar: GPL-2.0-or-later.

The registry is deliberately extensible so additional open-source backends can be added with a capability manifest and isolated launcher. Backend declaration or command preview does not mean runtime execution has been certified.
