"""Run a one-frame smoke test with a locally installed Libretro core.

No emulator, firmware, or game content is downloaded. The user must provide
an installed core and content they are authorized to use.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from game_emulator.libretro_host import smoke_test


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one frame through a local Libretro core under the strict worker policy"
    )
    parser.add_argument("--core", type=Path, required=True, help="installed Libretro shared library")
    parser.add_argument("--content", type=Path, required=True, help="authorized local game/homebrew test content")
    parser.add_argument(
        "--system-dir",
        type=Path,
        help="optional local firmware/system directory; exposed read-only inside the sandbox",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="worker timeout in seconds")
    args = parser.parse_args()
    try:
        result = smoke_test(
            args.core,
            args.content,
            timeout=args.timeout,
            system_dir=args.system_dir,
        )
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
