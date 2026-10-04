"""Non-pickle IPC for the untrusted native-core worker boundary.

The worker loads untrusted native code. Never use Connection.send()/recv(), which
pickle Python objects and would let a compromised worker execute code in the host
when the host unpickles its response. Messages are bounded UTF-8 JSON objects.
"""
from __future__ import annotations

import json
from multiprocessing.connection import Connection
from typing import Any

MAX_MESSAGE_BYTES = 1_048_576


class IPCProtocolError(ValueError):
    """A worker message is oversized, malformed, or not a JSON object."""


def encode_message(message: dict[str, Any]) -> bytes:
    if not isinstance(message, dict):
        raise IPCProtocolError("IPC message must be an object")
    try:
        encoded = json.dumps(
            message, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IPCProtocolError(f"IPC message is not JSON-safe: {exc}") from exc
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise IPCProtocolError("IPC message exceeds size limit")
    return encoded


def decode_message(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_MESSAGE_BYTES:
        raise IPCProtocolError("IPC message exceeds size limit")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IPCProtocolError("IPC message is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise IPCProtocolError("IPC message must decode to an object")
    return decoded


def send_message(connection: Connection, message: dict[str, Any]) -> None:
    connection.send_bytes(encode_message(message))


def receive_message(connection: Connection) -> dict[str, Any]:
    try:
        payload = connection.recv_bytes(maxlength=MAX_MESSAGE_BYTES)
    except OSError as exc:
        raise IPCProtocolError("IPC message could not be read within size limit") from exc
    return decode_message(payload)
