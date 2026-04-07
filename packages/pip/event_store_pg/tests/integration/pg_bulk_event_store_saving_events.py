"""tests."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conftest import PgPool
from uuid import UUID

import pytest
from psycopg.errors import UniqueViolation

from event_store_pg import PgBulkEventStore

from .helper import new_state, todo_added_event, todo_removed_event


@pytest.mark.asyncio
async def test_saving_events(pool: PgPool) -> None:
    async with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        store = PgBulkEventStore(cur)
        await store.append(new_state(), [todo_added_event(), todo_removed_event()])
        events = [e async for e in store.load_stream("todo-1")]
        assert events == [todo_added_event(), todo_removed_event()]


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
