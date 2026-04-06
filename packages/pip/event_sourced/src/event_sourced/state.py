"""The aggregate state."""

from typing import Any
import msgspec


class State(msgspec.Struct):
    aggregate_id: str = ""
    created: bool = False
    occ_version: int = 0


def serialize_state(event: State) -> str:
    """Serialize state."""
    return msgspec.json.encode(event).decode("utf-8")


def deserialize_state(raw: bytes | str) -> State:
    """Deserialize state."""
    return msgspec.json.decode(raw, type=State)


def deserialize_state_dict(raw: dict[str, Any]) -> State:
    """Deserialize state dict from the database."""
    return msgspec.convert(raw, type=State)
