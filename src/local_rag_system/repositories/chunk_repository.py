"""Vector storage and similarity search over document chunks."""

from collections.abc import Sequence

import numpy as np
from psycopg_pool import AsyncConnectionPool

from local_rag_system.repositories.records import ChunkPreview, NewChunk, RetrievedChunk


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
        """Return the ``top_k`` chunks closest to ``embedding`` by cosine similarity.

        Without a document filter the HNSW index answers the query. With a filter the
        matching chunks are selected *first* (``MATERIALIZED``) and then ranked exactly:
        an HNSW scan applies ``WHERE`` only after it has produced its ~``ef_search``
        candidates, so a filter on a small document could otherwise return nothing.
        """
        query_vec = np.array(embedding)
        if document_ids:
            sql = self._FILTERED_SQL
            params: tuple[object, ...] = (list(document_ids), query_vec, query_vec, top_k)
        else:
            sql = self._UNFILTERED_SQL
            params = (query_vec, query_vec, top_k)
        async with self._pool.connection() as conn:
            cur = await conn.execute(sql, params)
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

    _UNFILTERED_SQL = """
        SELECT c.id, c.document_id, d.filename, c.chunk_index, c.page, c.content,
               1 - (c.embedding <=> %s) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> %s
        LIMIT %s"""

    _FILTERED_SQL = """
        WITH candidates AS MATERIALIZED (
            SELECT id, document_id, chunk_index, page, content, embedding
            FROM chunks
            WHERE document_id = ANY(%s::int[])
        )
        SELECT c.id, c.document_id, d.filename, c.chunk_index, c.page, c.content,
               1 - (c.embedding <=> %s) AS score
        FROM candidates c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> %s
        LIMIT %s"""

    async def list_by_document(self, document_id: int) -> list[ChunkPreview]:
        """Return all chunks of a document in reading order."""
        async with self._pool.connection() as conn:
            cur = await conn.execute(
                "SELECT chunk_index, page, content FROM chunks "
                "WHERE document_id = %s ORDER BY chunk_index",
                (document_id,),
            )
            rows = await cur.fetchall()
        return [ChunkPreview(chunk_index=r[0], page=r[1], content=r[2]) for r in rows]
