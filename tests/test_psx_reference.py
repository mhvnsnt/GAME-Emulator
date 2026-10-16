from pathlib import Path

import pytest

from game_emulator.psx_reference import build_retroarch_command, validate_cue_set


def test_validate_cue_set_resolves_local_tracks(tmp_path: Path):
    cue = tmp_path / "Tekken 3 (USA).cue"
    track = tmp_path / "Tekken 3 (USA).bin"
    track.write_bytes(b"fixture")
    cue.write_text('FILE "Tekken 3 (USA).bin" BINARY\nTRACK 01 MODE2/2352\nINDEX 01 00:00:00\n')
    result = validate_cue_set(cue)
    assert result["track_count"] == 1
    assert result["tracks"][0]["path"] == str(track.resolve())


def test_validate_cue_set_rejects_path_escape(tmp_path: Path):
    cue = tmp_path / "game.cue"
    cue.write_text('FILE "../outside.bin" BINARY\n')
    with pytest.raises(ValueError, match="outside"):
        validate_cue_set(cue)


def test_build_command_validates_before_launch(tmp_path: Path):
    cue = tmp_path / "game.cue"
    track = tmp_path / "game.bin"
    track.write_bytes(b"fixture")
    cue.write_text('FILE "game.bin" BINARY\nTRACK 01 MODE2/2352\nINDEX 01 00:00:00\n')
    command = build_retroarch_command(cue, retroarch="/usr/bin/retroarch", core="/tmp/pcsx_rearmed_libretro.so")
    assert command[-1] == str(cue.resolve())
    assert command[:4] == ["/usr/bin/retroarch", "--verbose", "--libretro", "/tmp/pcsx_rearmed_libretro.so"]
