"""Vector storage and similarity search over document chunks."""

from collections.abc import Sequence

import numpy as np
from psycopg_pool import AsyncConnectionPool

from local_rag_system.repositories.records import NewChunk, RetrievedChunk


class ChunkRepository:
    """Reads and writes the ``chunks`` table using pgvector."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def add_many(self, document_id: int, chunks: Sequence[NewChunk]) -> None:
        rows = [
            (document_id, c.chunk_index, c.content, c.page, np.array(c.embedding)) for c in chunks
        ]
        async with self._pool.connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                    INSERT INTO chunks (document_id, chunk_index, content, page, embedding)
                    VALUES (%s, %s, %s, %s, %s)""",
                rows,
            )

    async def search(
        self,
        embedding: list[float],
        top_k: int,
        document_ids: Sequence[int] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the ``top_k`` chunks closest to ``embedding`` by cosine similarity."""
        query_vec = np.array(embedding)
        sql = """
            SELECT c.id, c.document_id, d.filename, c.chunk_index, c.page, c.content,
                   1 - (c.embedding <=> %s) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE (%s::int[] IS NULL OR c.document_id = ANY(%s::int[]))
            ORDER BY c.embedding <=> %s
            LIMIT %s"""
        ids = list(document_ids) if document_ids else None
        async with self._pool.connection() as conn:
            cur = await conn.execute(sql, (query_vec, ids, ids, query_vec, top_k))
            rows = await cur.fetchall()
        return [
            RetrievedChunk(
                chunk_id=r[0],
                document_id=r[1],
                filename=r[2],
                chunk_index=r[3],
                page=r[4],
                content=r[5],
                score=float(r[6]),
            )
            for r in rows
        ]
