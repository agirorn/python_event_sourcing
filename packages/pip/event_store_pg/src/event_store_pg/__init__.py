"""event_store_pg."""

from typing import TYPE_CHECKING
from collections.abc import Awaitable, Callable

from event_sourced.events import deserialize_event_dict, TodoEvent, TodoAdded, TodoRemoved
from event_sourced.state import State, serialize_state


from event_sourced import EventStore
from event_sourced.events import serialize_event

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from psycopg import AsyncConnection
    from psycopg_pool import AsyncConnectionPool
    from psycopg import AsyncCursor
    from psycopg.rows import TupleRow


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
            _ = await cur.execute(
                "select event from events where aggregate_id = %s order by occ_version",
                (aggregate_id,),
            )
            async for (event,) in cur:
                yield deserialize_event_dict(event)

    async def append(self, state: State, events: list[TodoEvent]) -> None:
        if not events:
            return
        event_rows = [(serialize_event(e),) for e in events]
        async with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            _ = await cur.execute(
                """
                INSERT INTO states (state) VALUES (%s::JSONB)
                ON CONFLICT ON CONSTRAINT states_pkey
                DO UPDATE SET state = excluded.state
                """,
                [serialize_state(state)],
            )
            await cur.executemany(
                "INSERT INTO events (event) VALUES (%s::JSONB)",
                event_rows,
            )
            for pipeline in self.pipelines:
                await pipeline(cur, state, events)


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
