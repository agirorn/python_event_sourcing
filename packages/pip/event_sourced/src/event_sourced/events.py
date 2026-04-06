"""Doing this and that."""

from __future__ import annotations
from typing import Any

import msgspec

from datetime import datetime  # noqa: TC003 This is a false positive
from typing import Annotated

from uuid import UUID  # noqa: TC003 This is a false positive


class EventBase(msgspec.Struct, tag_field="name"):
    aggregate_id: str
    event_id: UUID
    version: int
    # occurred_at: datetime
    occurred_at: Annotated[datetime, msgspec.Meta(tz=True)]
    occ_version: int


class NoData(msgspec.Struct):
    pass


class TodoAddedData(msgspec.Struct):
    message: str = ""


class TodoAdded(EventBase, tag="todo_added"):
    data: TodoAddedData
    # event_id: UUID = msgspec.field(default_factory=uuid4)


class TodoRemoved(EventBase, tag="todo_removed"):
    data: NoData
    # event_id: UUID = msgspec.field(default_factory=uuid4)


TodoEvent = TodoAdded | TodoRemoved


def serialize_event(event: TodoEvent) -> str:
    """Serialize event."""
    return msgspec.json.encode(event).decode("utf-8")


def deserialize_event(raw: bytes | str) -> TodoEvent:
    """Deserialize event."""
    return msgspec.json.decode(raw, type=TodoEvent)


def deserialize_event_dict(raw: dict[str, Any]) -> TodoEvent:
    """Deserialize event dict from the database."""
    return msgspec.convert(raw, type=TodoEvent)
