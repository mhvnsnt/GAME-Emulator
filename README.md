# GAME: Emulator

GAME: Emulator is a local-first game library and runtime router, not a claim that one emulator can natively execute every platform. It currently provides safe file intake, backend discovery, Libretro metadata inventory, a typed Libretro worker prototype, strict sandbox gates, and an open-source backend catalog.

## Quick start

Python 3.11+ is required.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```

Run the local dashboard with `game-emulator-ui`, or import from the CLI with `game-emulator import`.

List researched upstream emulator projects without downloading or executing them:

```bash
game-emulator-open-source
game-emulator-open-source --system "Sony PlayStation 2"
game-emulator-open-source --license-review ppsspp
```

Compare installed Libretro core metadata against catalog candidates (metadata only; no native code is loaded):

```bash
game-emulator-open-source --installed-cores ~/.config/retroarch/cores --info ~/.config/retroarch/cores
```

Run a one-frame smoke test with a core and authorized content already on your machine:

```bash
game-emulator-libretro-smoke --core /path/to/installed/core_libretro.so --content /path/to/authorized/homebrew.gba
# Add --system-dir /path/to/your/authorized/firmware when the core needs it.
```

This command does not download content or firmware. It fails closed if the local host cannot establish the strict OS policy and reports the sandbox status only after the worker responds.

Use the actual core and info directories for your installation. The report distinguishes catalog entries from local core files whose `.info` metadata matches a known system and representative extension. A metadata match is not proof of runtime compatibility, successful gameplay, or sandbox containment.

The catalog does not install emulator binaries, download game files, or certify a project for redistribution. Every exact release and its dependencies/assets must be license-reviewed before bundling. See `docs/OPEN-SOURCE-BACKENDS.md`, `docs/ARCHITECTURE.md`, `docs/LIBRETRO-WORKER.md`, and `docs/LIBRETRO-FFI-AND-OPEN-SOURCE.md` for safety boundaries and integration gates.

Only import files you are authorized to use. No ROM/BIOS/key downloading, DRM bypass, archive extraction, or automatic execution is part of this project.

## What "any game" means here

GAME: Emulator is being built as a **game-runtime router and creator platform**, not as a claim that one emulator can natively execute every platform.

- **Libretro route:** many classic consoles, handhelds, arcade systems and engines through installed cores.
- **Standalone route:** dedicated adapters for systems such as GameCube/Wii and PS2.
- **Android route:** APK/APKS/XAPK packages go to an Android runtime adapter; they are not treated as ROMs.
- **Modern-console route:** Switch and newer systems require dedicated native backends and any legally required user-supplied system components.
- **Creator route:** later layers can capture frames/input/state and apply game-specific transformation/mod pipelines without pretending that unrelated ROM formats are interchangeable.

Every route is capability-checked and fail-closed. A filename extension alone never grants permission to execute a file.
