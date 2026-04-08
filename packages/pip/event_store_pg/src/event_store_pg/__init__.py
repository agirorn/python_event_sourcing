"""event_store_pg."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from event_sourced.events import (
    TodoInit,
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
            """
            -- SELECT event FROM events WHERE aggregate_id = %s ORDER BY OCC_VERSION

            WITH state AS (
              SELECT jsonb_build_object(
                       'data',       row.state,
                       'name',       'todo_init', -- snapshot
                       'aggregate_id', aggregate_id,
                       'event_id', gen_random_uuid(),
                       'version', 1,
                       'occurred_at', NOW(),
                       'occ_version', occ_version
                     ) AS event,
                     row.aggregate_id AS aggregate_id,
                     row.occ_version  AS occ_version
                FROM (
                       SELECT state, aggregate_id, occ_version, "saved_at"
                         FROM states
                        WHERE aggregate_id = $1
                        LIMIT 1
                     ) as row
            )
            SELECT result.event
              FROM (
                     -- SNAPSHOT ROW (only if state exists)
                     SELECT state.event
                          , state.aggregate_id
                          , state.occ_version
                       FROM state

                     UNION ALL

                     -- EVENTS NEWER THAN THE SNAPSHOT
                     -- Or events with occ_version grater 0 snapshot is missing
                     -- Can occure when snapshots have to be rebuild
                     SELECT events.event
                          , events.aggregate_id
                          , events.occ_version
                       FROM events events
                  LEFT JOIN state ON state.aggregate_id = events.aggregate_id
                      WHERE events.aggregate_id = $1
                        AND events.occ_version > COALESCE(state.occ_version, 0)
                   ) AS result
            ORDER BY occ_version ASC;
            """,
            (aggregate_id,),
        )
        async for (event,) in self.cursor:
            print(f"----------------------------------")  # noqa: T201
            print(f"event: {event}")  # noqa: T201
            print(f"----------------------------------")  # noqa: T201
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
            case TodoInit():
                pass
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
