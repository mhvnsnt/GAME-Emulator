import ctypes

from game_emulator.libretro_abi import (
    RETRO_PIXEL_FORMAT_XRGB8888,
    LibretroCallbacks,
)


def test_callbacks_are_owned_and_pixel_format_negotiates():
    cb = LibretroCallbacks()
    value = ctypes.c_int(RETRO_PIXEL_FORMAT_XRGB8888)
    assert cb.cb_env(10, ctypes.addressof(value)) is True
    assert cb.cb_env(10, 0) is False
    cb.cb_video(0, 320, 240, 1280)
    assert cb.frame_rendered is True
    assert cb.last_video == {
        "width": 320,
        "height": 240,
        "pitch": 1280,
        "has_data": False,
    }
