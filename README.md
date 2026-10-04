# GAME: Emulator

A local-first intake and library manager for game files you are authorized to use.

## Current scope

This repository starts with the local import/catalog pipeline migrated from the temporary Bannon staging branch. It is **not yet a full emulator frontend**. Native Libretro FFI, isolated core execution, real test-ROM smoke tests, and reversible mod overlays remain gated follow-up work.

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

See `docs/ARCHITECTURE.md` and `docs/LIBRETRO-FFI-AND-OPEN-SOURCE.md` for the safety boundaries and next integration gates.

Only import files you are authorized to use. No ROM/BIOS/key downloading, DRM bypass, archive extraction, or automatic execution is part of this project.
