"""tests."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conftest import PgPool
    from event_sourced.events import TodoEvent
from uuid import UUID

import pytest
from event_sourced.events import TodoInit
from event_sourced.state import State
from psycopg.errors import UniqueViolation

from event_store_pg import PgBulkEventStore

from .helper import new_state, todo_added_event, todo_removed_event


@pytest.mark.asyncio
async def test_saving_events(pool: PgPool) -> None:
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        await store.append(new_state(), [todo_added_event(), todo_removed_event()])
        store = None
    async with pool.connection() as conn, conn.cursor() as cur:
        _ = await cur.execute("TRUNCATE states")
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        events = store.load_stream("todo-1")
        events = [e async for e in events]
        assert len(events) == 2
        assert events == [todo_added_event(), todo_removed_event()]


@pytest.mark.asyncio
async def test_saving_events_and_up_to_date_state(pool: PgPool) -> None:
    state = State()
    state.aggregate_id = "todo-1"
    state.occ_version = 2
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        await store.append(state, [todo_added_event(), todo_removed_event()])
        store = None
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        events = store.load_stream("todo-1")
        events = [e async for e in events]
        assert len(events) == 1
        event = events[0]
        assert type(event) is TodoInit
        assert event.data == state


@pytest.mark.asyncio
async def test_saving_bulk_events(pool: PgPool) -> None:
    event_1 = todo_added_event(event_id=UUID("5a48af7e-565c-402e-afe1-0ceedbe89ee2"), occ_version=1)
    event_2 = todo_removed_event(
        event_id=UUID("6fa020e7-da8f-4e40-a7e2-aea0bf86021f"), occ_version=2
    )
    event_3 = todo_added_event(event_id=UUID("638237ec-ab65-4133-bbf3-7aaf4ed87187"), occ_version=3)
    event_4 = todo_removed_event(
        event_id=UUID("28b09023-0b90-424e-b65e-e49f18032a6c"), occ_version=4
    )
    events_1: list[TodoEvent] = [event_1, event_2]
    events_2: list[TodoEvent] = [event_3, event_4]
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        await store.append(new_state(), events_1)
        await store.append(new_state(), events_2)
        store = None
    async with pool.connection() as conn, conn.cursor() as cur:
        _ = await cur.execute("TRUNCATE states")
    async with pool.connection() as conn, conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        # async with pool.connection() as conn, conn.cursor() as cur:
        events = [e async for e in store.load_stream("todo-1")]
        assert len(events) == 4
        assert events == [event_1, event_2, event_3, event_4]


@pytest.mark.asyncio
async def test_duplicate_event_ids(pool: PgPool) -> None:
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        event_id = UUID("2ea565bd-bf1d-408e-bbc5-c3638d8e06b6")
        duplicate_key = 'duplicate key value violates unique constraint "events_event_id_key"'
        with pytest.raises(UniqueViolation, match=duplicate_key):
            await store.append(
                new_state(),
                [
                    todo_added_event(event_id=event_id, occ_version=1),
                    todo_added_event(event_id=event_id, occ_version=2),
                ],
            )


@pytest.mark.asyncio
async def test_duplicate_occ_versions(pool: PgPool) -> None:
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        duplicate_key = (
            'duplicate key value violates unique constraint "events_aggregate_id_occ_version_key"'
        )
        with pytest.raises(UniqueViolation, match=duplicate_key):
            await store.append(
                new_state(),
                [
                    todo_added_event(occ_version=1),
                    todo_added_event(occ_version=1),
                ],
            )
