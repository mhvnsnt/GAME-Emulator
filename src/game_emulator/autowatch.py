"""Continuously import newly copied files from a user-selected local folder."""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from game_emulator.library import EXTENSIONS, import_library

LOG = logging.getLogger("game_emulator.autowatch")


class AutoImportHandler(FileSystemEventHandler):
    def __init__(self, library: Path, rights_basis: str, source_label: str, max_bytes: int):
        self.library = library.resolve()
        self.rights_basis = rights_basis
        self.source_label = source_label
        self.max_bytes = max_bytes
        self.seen: dict[str, tuple[int, int]] = {}

    def _consider(self, raw_path: str) -> None:
        path = Path(raw_path)
        try:
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                return
            resolved = path.resolve(strict=True)
            first = resolved.stat()
            time.sleep(0.8)  # give ordinary file copies a chance to finish
            if not resolved.exists():
                return
            second = resolved.stat()
            signature = (second.st_size, second.st_mtime_ns)
            if (first.st_size, first.st_mtime_ns) != signature or second.st_size == 0:
                LOG.info("Copy still changing; will retry on the next filesystem event: %s", resolved.name)
                return
            if self.seen.get(str(resolved)) == signature:
                return
            # Import only this file's containing folder; content hashes deduplicate prior imports.
            result = import_library(
                resolved.parent, self.library, rights_basis=self.rights_basis,
                source_label=self.source_label, max_bytes=self.max_bytes,
            )
            self.seen[str(resolved)] = signature
            LOG.info("Folder event processed for %s: %s", resolved.name, result)
        except (OSError, ValueError) as exc:
            LOG.warning("Auto-import rejected %s: %s", path.name, exc)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(str(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(str(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(str(event.dest_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a local folder and automatically import game files")
    parser.add_argument("--source", type=Path, required=True, help="existing folder to watch recursively")
    parser.add_argument("--library", type=Path, default=Path.home() / "GAME-Emulator-Library")
    parser.add_argument("--rights-basis", required=True, help="why files in this source are authorized")
    parser.add_argument("--source-label", default="user-selected watched folder")
    parser.add_argument("--max-bytes", type=int, default=64 * 1024**3)
    args = parser.parse_args()
    source = args.source.expanduser().resolve(strict=True)
    if not source.is_dir():
        parser.error("--source must be a directory")
    library = args.library.expanduser().resolve()
    if library == source or source in library.parents or library in source.parents:
        parser.error("source and library folders must not contain one another")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    initial = import_library(source, library, rights_basis=args.rights_basis,
                             source_label=args.source_label, max_bytes=args.max_bytes)
    LOG.info("Initial scan complete: %s", initial)
    handler = AutoImportHandler(library, args.rights_basis, args.source_label, args.max_bytes)
    for existing in source.rglob("*"):
        try:
            if not existing.is_symlink() and existing.is_file() and existing.suffix.lower() in EXTENSIONS:
                stat = existing.stat()
                handler.seen[str(existing.resolve())] = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            continue
    observer = Observer()
    observer.schedule(handler, str(source), recursive=True)
    observer.start()
    LOG.info("Watching %s; imported files are copied to %s", source, library)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
