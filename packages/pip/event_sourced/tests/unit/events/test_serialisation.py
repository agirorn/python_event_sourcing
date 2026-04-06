"""Test file."""

from event_sourced.events import (
    serialize_event,
    deserialize_event,
    TodoEvent,
    TodoAdded,
    TodoAddedData,
    TodoRemoved,
    NoData,
)
from datetime import datetime, UTC
from uuid import UUID


def compact_json(json_str: str) -> str:
    return "".join(line.strip() for line in json_str.splitlines())


def test_todo_added():
    event: TodoEvent = TodoAdded(
        aggregate_id="todo-1",
        version=1,
        event_id=UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6"),
        occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
        occ_version=1,
        data=TodoAddedData(message="buy milk"),
    )
    expected_json = compact_json("""
        {
            "name":"todo_added",
            "aggregate_id":"todo-1",
            "event_id":"2ea565bd-bf1d-408e-bbc5-c3638d8e06b6",
            "version":1,
            "occurred_at":"2026-04-04T12:00:00Z",
            "occ_version":1,
            "data":{"message":"buy milk"}
        }
    """)
    actual_json = serialize_event(event)
    assert actual_json == expected_json
    assert deserialize_event(actual_json) == event


def test_todo_removed():
    event: TodoEvent = TodoRemoved(
        aggregate_id="todo-1",
        version=2,
        event_id=UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6"),
        occurred_at=datetime(2026, 4, 4, 12, 1, tzinfo=UTC),
        occ_version=1,
        data=NoData(),
    )
    expected_json = compact_json("""
        {
            "name":"todo_removed",
            "aggregate_id":"todo-1",
            "event_id":"2ea565bd-bf1d-408e-bbc5-c3638d8e06b6",
            "version":2,
            "occurred_at":"2026-04-04T12:01:00Z",
            "occ_version":1,
            "data":{}
        }
    """)
    actual_json = serialize_event(event)
    assert actual_json == expected_json
    assert deserialize_event(actual_json) == event


# def test_unknown_event_name_fails() -> None:
#     raw = (
#         '{"name":"nope","aggregate_id":"x","version":1,'
#         '"occurred_at":"2026-04-04T12:00:00+00:00","occ_version":1,"data":{}}'
#     )
#
#     with pytest.raises(ValueError, match="unknown event name"):
#         event_from_json(raw)
