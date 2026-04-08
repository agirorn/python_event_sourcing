from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import AsyncConnection
from datetime import UTC, datetime
from uuid import UUID

from event_sourced.events import NoData, TodoAdded, TodoAddedData, TodoInit, TodoRemoved
from event_sourced.state import State
from psycopg_pool import AsyncConnectionPool

type Pool = AsyncConnectionPool[AsyncConnection]


def new_state() -> State:
    state = State()
    state.aggregate_id = "todo-1"
    return state


def todo_init_event(
    event_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> TodoInit:
    if not event_id:
        event_id = UUID("81d618bd-1b67-4727-9926-249032042668")

    if not occurred_at:
        occurred_at = datetime(2026, 4, 4, 12, 0, tzinfo=UTC)
    state = State()
    state.occ_version = 2
    state.aggregate_id = "todo-1"
    return TodoInit(
        aggregate_id="todo-1",
        event_id=event_id,
        version=1,
        occurred_at=occurred_at,
        occ_version=2,
        data=state,
    )


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


def todo_removed_event(
    event_id: UUID | None = None,
    occ_version: int = 2,
) -> TodoRemoved:
    if not event_id:
        event_id = UUID("1086ada8-9000-4a1f-b621-1a322d21b71c")
    return TodoRemoved(
        aggregate_id="todo-1",
        event_id=event_id,
        version=1,
        occurred_at=datetime(2026, 4, 4, 12, 1, tzinfo=UTC),
        occ_version=occ_version,
        data=NoData(),
    )
