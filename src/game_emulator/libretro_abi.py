"""Small audited ctypes declaration layer for the Libretro C ABI."""
from __future__ import annotations

import ctypes

retro_video_refresh_t = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t
)
retro_audio_sample_t = ctypes.CFUNCTYPE(None, ctypes.c_int16, ctypes.c_int16)
retro_audio_sample_batch_t = ctypes.CFUNCTYPE(
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t
)
retro_input_poll_t = ctypes.CFUNCTYPE(None)
retro_input_state_t = ctypes.CFUNCTYPE(
    ctypes.c_int16, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
)
retro_environment_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)

RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_PIXEL_FORMAT_0RGB1555 = 0
RETRO_PIXEL_FORMAT_XRGB8888 = 1
RETRO_PIXEL_FORMAT_RGB565 = 2


class retro_game_info(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("meta", ctypes.c_char_p),
    ]


class LibretroCallbacks:
    """Own callback objects so ctypes cannot garbage-collect active callbacks."""

    def __init__(self) -> None:
        self.frame_rendered = False
        self.last_video = None
        self.audio_samples = 0
        self.cb_env = retro_environment_t(self.environment)
        self.cb_video = retro_video_refresh_t(self.video_refresh)
        self.cb_audio = retro_audio_sample_t(self.audio_sample)
        self.cb_audio_batch = retro_audio_sample_batch_t(self.audio_sample_batch)
        self.cb_input_poll = retro_input_poll_t(self.input_poll)
        self.cb_input_state = retro_input_state_t(self.input_state)

    def environment(self, command: int, data: int | None) -> bool:
        if command == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            if not data:
                return False
            fmt = ctypes.cast(data, ctypes.POINTER(ctypes.c_int)).contents.value
            return fmt in (
                RETRO_PIXEL_FORMAT_0RGB1555,
                RETRO_PIXEL_FORMAT_XRGB8888,
                RETRO_PIXEL_FORMAT_RGB565,
            )
        return False

    def video_refresh(self, data: int, width: int, height: int, pitch: int) -> None:
        self.frame_rendered = True
        self.last_video = {
            "width": int(width),
            "height": int(height),
            "pitch": int(pitch),
            "has_data": bool(data),
        }

    def audio_sample(self, left: int, right: int) -> None:
        self.audio_samples += 1

    def audio_sample_batch(self, data: int, frames: int) -> int:
        self.audio_samples += int(frames)
        return int(frames)

    def input_poll(self) -> None:
        return None

    def input_state(self, port: int, device: int, index: int, ident: int) -> int:
        return 0
