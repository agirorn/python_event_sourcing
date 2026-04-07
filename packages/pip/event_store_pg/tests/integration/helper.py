from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from event_sourced.events import TodoAddedData, TodoAdded, TodoRemoved, NoData
from event_sourced.state import State

from datetime import datetime, UTC
from uuid import UUID

type Pool = AsyncConnectionPool[AsyncConnection]


def new_state() -> State:
    state = State()
    state.aggregate_id = "todo-1"
    return state


def todo_added_event(
    event_id: UUID | None = None,
    occ_version: int = 1,
) -> TodoAdded:
    if not event_id:
        event_id = UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6")

    return TodoAdded(
        aggregate_id="todo-1",
        event_id=event_id,
        version=1,
        occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
        occ_version=occ_version,
        data=TodoAddedData(message="buy milk"),
    )


def todo_removed_event() -> TodoRemoved:
    return TodoRemoved(
        aggregate_id="todo-1",
        event_id=UUID("1086ada8-9000-4a1f-b621-1a322d21b71c"),
        version=1,
        occurred_at=datetime(2026, 4, 4, 12, 1, tzinfo=UTC),
        occ_version=2,
        data=NoData(),
    )
