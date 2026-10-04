"""CLI for inspecting the metadata-only open-source backend catalog."""
from __future__ import annotations

import argparse
import json

from game_emulator.open_source_catalog import list_projects, redistribution_eligibility


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List upstream emulator projects without downloading or executing them"
    )
    parser.add_argument("--system", action="append", default=[], help="exact system label; may be repeated")
    parser.add_argument("--license-review", metavar="PROJECT_ID", help="show conservative redistribution review status")
    args = parser.parse_args()
    if args.license_review:
        result = redistribution_eligibility(args.license_review)
    else:
        result = list_projects(systems=set(args.system) if args.system else None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
