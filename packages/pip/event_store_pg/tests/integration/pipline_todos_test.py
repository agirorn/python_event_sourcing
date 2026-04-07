from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conftest import PgPool

from psycopg.rows import dict_row
import pytest
from event_store_pg import PgEventStore, todos_pipline
from .helper import new_state, todo_added_event, todo_removed_event


@pytest.mark.asyncio
async def test_saving_events(pool: PgPool) -> None:
    store = PgEventStore(pool, [todos_pipline])
    await store.append(new_state(), [todo_added_event()])
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        _ = await cur.execute("select id, message, deleted from todos")
        rows = [row async for row in cur]
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == "todo-1"
        assert row["message"] == "buy milk"
        assert not row["deleted"]
    await store.append(new_state(), [todo_removed_event()])
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        _ = await cur.execute("select id, message, deleted from todos")
        rows = [row async for row in cur]
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == "todo-1"
        assert row["message"] == "buy milk"
        assert row["deleted"]
