# GAME: Emulator

A local-first intake and library manager for game files you are authorized to use.

## Current scope

This repository starts with the local import/catalog pipeline migrated from the temporary Bannon staging branch. It is **not yet a finished universal emulator**. The repository now has typed Libretro FFI, an isolated worker, OS sandbox gating, metadata-driven core matching, and a capability registry for installed standalone backends. Real emulator execution remains gated by installed/authorized runtime components and platform-specific launch adapters.

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

See `docs/ARCHITECTURE.md`, `docs/LIBRETRO-WORKER.md`, and `docs/LIBRETRO-FFI-AND-OPEN-SOURCE.md` for the safety boundaries and integration gates.

Only import files you are authorized to use. No ROM/BIOS/key downloading, DRM bypass, archive extraction, or automatic execution is part of this project.


## What "any game" means here

GAME: Emulator is being built as a **game-runtime router and creator platform**, not as a claim that one emulator can natively execute every platform.

- **Libretro route:** many classic consoles, handhelds, arcade systems and engines through installed cores.
- **Standalone route:** dedicated adapters for systems such as GameCube/Wii and PS2.
- **Android route:** APK/APKS/XAPK packages go to an Android runtime adapter; they are not treated as ROMs.
- **Modern-console route:** Switch and newer systems require dedicated native backends and any legally required user-supplied system components.
- **Creator route:** later layers can capture frames/input/state and apply game-specific transformation/mod pipelines without pretending that unrelated ROM formats are interchangeable.

Every route is capability-checked and fail-closed. A filename extension alone never grants permission to execute a file.
