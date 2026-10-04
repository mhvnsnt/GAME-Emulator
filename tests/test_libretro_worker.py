import os
from pathlib import Path
import pytest
from game_emulator.libretro_host import smoke_test

@pytest.mark.skipif(not os.environ.get("GAME_EMULATOR_TEST_CORE") or not os.environ.get("GAME_EMULATOR_TEST_CONTENT"), reason="requires an installed Libretro core and authorized homebrew/test content")
def test_real_one_frame_smoke():
    result = smoke_test(Path(os.environ["GAME_EMULATOR_TEST_CORE"]), Path(os.environ["GAME_EMULATOR_TEST_CONTENT"]))
    assert result["status"] == "TICK_COMPLETE"
    assert result["video_fired"] is True
