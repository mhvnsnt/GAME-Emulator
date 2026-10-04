"""Provenance-gated local intake; never executes or extracts imported files."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

LOG = logging.getLogger("game_emulator.intake")
ALLOWED_EXTENSIONS = {
    ".gba", ".gbc", ".gb", ".nes", ".fds", ".sfc", ".smc", ".n64", ".z64",
    ".v64", ".iso", ".bin", ".cue", ".chd", ".cso", ".pbp", ".3ds", ".nds",
    ".gcm", ".wbfs", ".wud", ".wux", ".nsp", ".xci", ".xiso", ".xex", ".xbe",
    ".god", ".pkg", ".rap", ".ird", ".cia", ".cxi", ".dol", ".wad", ".elf", ".app", ".tik",
}
REQUIRED_PROVENANCE = ("source", "rights_basis", "acquired_at")
DEFAULT_MAX_BYTES = 8 * 1024 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_provenance(path: Path) -> dict[str, Any]:
    sidecar = path.with_name(path.name + ".provenance.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("provenance sidecar must contain a JSON object")
    missing = [key for key in REQUIRED_PROVENANCE if not str(data.get(key, "")).strip()]
    if missing:
        raise ValueError("missing provenance fields: " + ", ".join(missing))
    return {key: str(data[key]).strip() for key in REQUIRED_PROVENANCE} | {
        "notes": str(data.get("notes", "")).strip()
    }


def catalog_file(path: Path, report_path: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("symbolic links are not accepted")
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError("only regular, non-symlink files are accepted")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"unsupported extension: {path.suffix or '(none)'}")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("empty files are not accepted")
    if size > max_bytes:
        raise ValueError(f"file exceeds configured size limit ({max_bytes} bytes)")
    provenance = load_provenance(path)
    record = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": size,
        "sha256": sha256_file(path),
        "provenance": provenance,
        "status": "cataloged_pending_review",
        "analysis_performed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


class IntakeHandler(FileSystemEventHandler):
    def __init__(self, inbox: Path, report: Path, max_bytes: int) -> None:
        self.inbox = inbox.resolve()
        self.report = report
        self.max_bytes = max_bytes
        self.seen: set[str] = set()

    def _process(self, raw_path: str) -> None:
        path = Path(raw_path)
        try:
            resolved = path.resolve(strict=True)
            if resolved.parent != self.inbox or not resolved.is_file():
                return
            first_size = resolved.stat().st_size
            time.sleep(0.35)
            if not resolved.exists() or resolved.stat().st_size != first_size:
                LOG.info("Skipping file while copy is changing: %s", resolved.name)
                return
            identity = str(resolved)
            if identity in self.seen:
                return
            record = catalog_file(resolved, self.report, self.max_bytes)
            self.seen.add(identity)
            LOG.info("Cataloged %s sha256=%s", record["filename"], record["sha256"])
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            LOG.warning("Rejected %s: %s", path.name, exc)

    def _process_event_path(self, raw_path: str) -> None:
        event_path = Path(raw_path)
        if event_path.name.endswith(".provenance.json"):
            # A sidecar may arrive after its file; retry cataloging the paired file.
            target_name = event_path.name.removesuffix(".provenance.json")
            self._process(str(event_path.with_name(target_name)))
        else:
            self._process(raw_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._process_event_path(str(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._process_event_path(str(event.dest_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Catalog local files; never execute them")
    parser.add_argument("--root", type=Path, default=Path("imports"))
    parser.add_argument("--report", type=Path, default=Path("reports/import-manifest.jsonl"))
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--once", action="store_true", help="scan inbox once, then exit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    inbox = args.root / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    handler = IntakeHandler(inbox, args.report, args.max_bytes)
    if args.once:
        for path in sorted(inbox.iterdir()):
            if path.is_file() and not path.name.endswith(".provenance.json"):
                handler._process(str(path))
        return
    observer = Observer()
    observer.schedule(handler, str(inbox), recursive=False)
    observer.start()
    LOG.info("Watching local import inbox: %s", inbox.resolve())
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
