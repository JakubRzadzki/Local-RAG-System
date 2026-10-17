"""Fixtures for tests that need a real PostgreSQL with pgvector.

The tests use a separate ``rag_test`` database and are skipped when Postgres is not
reachable, so ``uv run pytest`` keeps working without Docker.
"""

import asyncio
import os
import sys
from collections.abc import AsyncIterator

import psycopg
import pytest
from psycopg_pool import AsyncConnectionPool

from local_rag_system.config import Settings
from local_rag_system.database import create_pool, ensure_extension, init_schema

# psycopg's async mode cannot use the ProactorEventLoop (the Windows default).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ADMIN_URL = os.environ.get(
    "RAG_TEST_ADMIN_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
)
TEST_URL = os.environ.get(
    "RAG_TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag_test"
)


async def _prepare_database() -> None:
    async with await psycopg.AsyncConnection.connect(ADMIN_URL, autocommit=True) as conn:
        cur = await conn.execute("SELECT 1 FROM pg_database WHERE datname = 'rag_test'")
        if await cur.fetchone() is None:
            await conn.execute("CREATE DATABASE rag_test")
        # Force index use so the HNSW behaviour is exercised even on tiny tables.
        await conn.execute("ALTER DATABASE rag_test SET enable_seqscan = off")


@pytest.fixture
async def pool() -> AsyncIterator[AsyncConnectionPool]:
    settings = Settings(database_url=TEST_URL)
    try:
        await _prepare_database()
    except psycopg.OperationalError:
        pytest.skip("Postgres with pgvector is not reachable")
    await ensure_extension(settings)
    connection_pool = create_pool(settings)
    await connection_pool.open()
    await init_schema(connection_pool, settings)
    yield connection_pool
    async with connection_pool.connection() as conn:
        await conn.execute("TRUNCATE chunks, documents RESTART IDENTITY CASCADE")
    await connection_pool.close()
