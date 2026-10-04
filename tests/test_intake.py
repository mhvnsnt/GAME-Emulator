import hashlib
import json
from pathlib import Path

import pytest

from game_emulator.watcher import catalog_file


def write_sidecar(path: Path, payload: dict) -> None:
    path.with_name(path.name + ".provenance.json").write_text(json.dumps(payload), encoding="utf-8")


def valid_provenance() -> dict:
    return {
        "source": "local synthetic test fixture",
        "rights_basis": "test-only fixture",
        "acquired_at": "2026-10-04",
        "notes": "not a commercial game file",
    }


def test_catalog_records_hash_and_never_analyzes(tmp_path: Path) -> None:
    source = tmp_path / "fixture.gba"
    payload = b"synthetic-test-data"
    source.write_bytes(payload)
    write_sidecar(source, valid_provenance())
    report = tmp_path / "reports" / "manifest.jsonl"

    record = catalog_file(source, report)

    assert record["sha256"] == hashlib.sha256(payload).hexdigest()
    assert record["analysis_performed"] is False
    assert record["status"] == "cataloged_pending_review"
    assert json.loads(report.read_text(encoding="utf-8").splitlines()[0])["filename"] == "fixture.gba"


def test_rejects_missing_provenance(tmp_path: Path) -> None:
    source = tmp_path / "fixture.nes"
    source.write_bytes(b"test")
    with pytest.raises(FileNotFoundError):
        catalog_file(source, tmp_path / "manifest.jsonl")


def test_rejects_unknown_extension(tmp_path: Path) -> None:
    source = tmp_path / "payload.exe"
    source.write_bytes(b"test")
    write_sidecar(source, valid_provenance())
    with pytest.raises(ValueError, match="unsupported extension"):
        catalog_file(source, tmp_path / "manifest.jsonl")


def test_rejects_oversized_file(tmp_path: Path) -> None:
    source = tmp_path / "fixture.gba"
    source.write_bytes(b"12345")
    write_sidecar(source, valid_provenance())
    with pytest.raises(ValueError, match="size limit"):
        catalog_file(source, tmp_path / "manifest.jsonl", max_bytes=4)


def test_rejects_missing_rights_basis(tmp_path: Path) -> None:
    source = tmp_path / "fixture.gba"
    source.write_bytes(b"test")
    write_sidecar(source, {"source": "local", "acquired_at": "2026-10-04"})
    with pytest.raises(ValueError, match="rights_basis"):
        catalog_file(source, tmp_path / "manifest.jsonl")
