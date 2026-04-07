"""event_store_pg."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from event_sourced.events import (
    TodoAdded,
    TodoEvent,
    TodoRemoved,
    deserialize_event_dict,
    serialize_event,
)
from event_sourced.state import State, serialize_state

from event_sourced import EventStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from psycopg import AsyncConnection, AsyncCursor
    from psycopg.rows import TupleRow
    from psycopg_pool import AsyncConnectionPool


type Pool = AsyncConnectionPool[AsyncConnection]
type Cursor = AsyncCursor[TupleRow]
type Pipelines = list[Pipeline]

Pipeline = Callable[[Cursor, State, list[TodoEvent]], Awaitable[None]]


class PgEventStore(EventStore):
    pool: Pool
    pipelines: Pipelines

    def __init__(self, pool: Pool, pipelines: Pipelines | None = None) -> None:
        self.pool = pool
        self.pipelines = pipelines or []
        self._streams: dict[str, list[TodoEvent]] = {}

    async def load_stream(self, aggregate_id: str) -> AsyncIterator[TodoEvent]:
        async with self.pool.connection() as conn, conn.cursor() as cur:
            events = PgBulkEventStore(cur, pipelines=self.pipelines).load_stream(aggregate_id)
            async for event in events:
                yield event

    async def append(self, state: State, events: list[TodoEvent]) -> None:
        async with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            await PgBulkEventStore(cur, pipelines=self.pipelines).append(state, events)


class PgBulkEventStore(EventStore):
    cursor: Cursor
    pipelines: Pipelines

    def __init__(self, cursor: Cursor, pipelines: Pipelines | None = None) -> None:
        self.cursor = cursor
        self.pipelines = pipelines or []
        self._streams: dict[str, list[TodoEvent]] = {}

    async def load_stream(self, aggregate_id: str) -> AsyncIterator[TodoEvent]:
        _ = await self.cursor.execute(
            "select event from events where aggregate_id = %s order by occ_version",
            (aggregate_id,),
        )
        async for (event,) in self.cursor:
            yield deserialize_event_dict(event)

    async def append(self, state: State, events: list[TodoEvent]) -> None:
        if not events:
            return
        event_rows = [(serialize_event(e),) for e in events]
        _ = await self.cursor.execute(
            """
            INSERT INTO states (state) VALUES (%s::JSONB)
            ON CONFLICT ON CONSTRAINT states_pkey
            DO UPDATE SET state = excluded.state
            """,
            [serialize_state(state)],
        )
        await self.cursor.executemany(
            "INSERT INTO events (event) VALUES (%s::JSONB)",
            event_rows,
        )
        for pipeline in self.pipelines:
            await pipeline(self.cursor, state, events)


async def todos_pipline(cur: Cursor, state: State, events: list[TodoEvent]) -> None:
    """Updxates the todos table."""
    for event in events:
        match event:
            case TodoAdded():
                _ = await cur.execute(
                    "INSERT INTO todos (id, message) VALUES (%s, %s)",
                    [state.aggregate_id, event.data.message],
                )
            case TodoRemoved():
                _ = await cur.execute(
                    """
                        UPDATE todos
                        SET deleted = true
                        WHERE id = %s
                    """,
                    [state.aggregate_id],
                )
