"""PostgreSQL connection pool and schema management."""

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from local_rag_system.config import Settings


async def _configure(conn: psycopg.AsyncConnection) -> None:
    await register_vector_async(conn)


async def ensure_extension(settings: Settings) -> None:
    """Create the ``vector`` extension; it must exist before the pool registers the type."""
    async with await psycopg.AsyncConnection.connect(
        settings.database_url, autocommit=True
    ) as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")


def create_pool(settings: Settings) -> AsyncConnectionPool:
    """Build an (unopened) async connection pool."""
    return AsyncConnectionPool(
        settings.database_url,
        min_size=1,
        max_size=10,
        configure=_configure,
        open=False,
    )


async def init_schema(pool: AsyncConnectionPool, settings: Settings) -> None:
    """Create tables and indexes; additive ALTERs keep older databases working."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )"""
        )
        for column in (
            "content_type TEXT NOT NULL DEFAULT 'text/plain'",
            "size_bytes INT NOT NULL DEFAULT 0",
            "chunk_count INT NOT NULL DEFAULT 0",
            "chunk_size INT NOT NULL DEFAULT 800",
            "chunk_overlap INT NOT NULL DEFAULT 100",
        ):
            await conn.execute(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS {column}")

        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INT NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR({settings.embedding_dim}) NOT NULL
            )"""
        )
        await conn.execute("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS page INT")
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks USING hnsw (embedding vector_cosine_ops)"""
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id)"
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )"""
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )"""
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS messages_conversation_idx "
            "ON messages (conversation_id, id)"
        )
