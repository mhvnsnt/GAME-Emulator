import multiprocessing as mp
import pickle

import pytest

from game_emulator.ipc_protocol import (
    IPCProtocolError,
    decode_message,
    encode_message,
    receive_message,
    send_message,
)


def test_ipc_uses_json_bytes_over_pipe():
    parent, child = mp.Pipe()
    try:
        send_message(parent, {"cmd": "TICK", "count": 3})
        assert receive_message(child) == {"cmd": "TICK", "count": 3}
        send_message(child, {"status": "TICK_COMPLETE", "video_fired": True})
        assert receive_message(parent) == {
            "status": "TICK_COMPLETE",
            "video_fired": True,
        }
    finally:
        parent.close()
        child.close()


def test_pickle_payload_is_rejected_as_invalid_json():
    payload = pickle.dumps({"status": "READY"})
    with pytest.raises(IPCProtocolError, match="valid UTF-8 JSON"):
        decode_message(payload)


def test_ipc_messages_are_bounded_and_must_be_objects():
    with pytest.raises(IPCProtocolError, match="size limit"):
        encode_message({"payload": "x" * (1024 * 1024)})
    with pytest.raises(IPCProtocolError, match="must be an object"):
        encode_message(["not", "an", "object"])  # type: ignore[arg-type]
    with pytest.raises(IPCProtocolError, match="must decode to an object"):
        decode_message(b"[]")
