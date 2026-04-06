from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from psycopg import AsyncConnection
    from .helper import Pool
from psycopg_pool import AsyncConnectionPool
import pytest_asyncio

DSN = "postgresql://admin:admin@localhost:5432/app_test"

type PgPool = AsyncConnectionPool[AsyncConnection]


@pytest_asyncio.fixture(scope="session")
async def pool() -> AsyncIterator[Pool]:
    pool: PgPool = AsyncConnectionPool(DSN)
    await pool.open()
    await pool.wait()
    try:
        yield pool
    finally:
        await pool.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_each(pool: Pool):
    """Setup for each function."""
    async with pool.connection() as conn, conn.cursor() as cur:
        _ = await cur.execute("TRUNCATE events")
        _ = await cur.execute("TRUNCATE states")
        _ = await cur.execute("TRUNCATE todos")
    yield
    async with pool.connection() as conn, conn.cursor() as cur:
        _ = await cur.execute("TRUNCATE events")
        _ = await cur.execute("TRUNCATE states")
        _ = await cur.execute("TRUNCATE todos")
