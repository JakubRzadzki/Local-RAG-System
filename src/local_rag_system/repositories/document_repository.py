"""Persistence of document metadata."""

from psycopg.rows import class_row
from psycopg_pool import AsyncConnectionPool

from local_rag_system.repositories.records import DocumentRecord

_COLUMNS = (
    "id, filename, content_type, size_bytes, chunk_count, chunk_size, chunk_overlap, created_at"
)


class DocumentRepository:
    """CRUD operations on the ``documents`` table."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def create(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        chunk_size: int,
        chunk_overlap: int,
    ) -> DocumentRecord:
        query = f"""
            INSERT INTO documents (filename, content_type, size_bytes, chunk_size, chunk_overlap)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {_COLUMNS}"""
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(DocumentRecord))
            await cur.execute(
                query, (filename, content_type, size_bytes, chunk_size, chunk_overlap)
            )
            record = await cur.fetchone()
        assert record is not None
        return record

    async def set_chunk_count(self, document_id: int, chunk_count: int) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(
                "UPDATE documents SET chunk_count = %s WHERE id = %s",
                (chunk_count, document_id),
            )

    async def list_all(self) -> list[DocumentRecord]:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(DocumentRecord))
            await cur.execute(f"SELECT {_COLUMNS} FROM documents ORDER BY created_at DESC")
            return await cur.fetchall()

    async def get(self, document_id: int) -> DocumentRecord | None:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(DocumentRecord))
            await cur.execute(f"SELECT {_COLUMNS} FROM documents WHERE id = %s", (document_id,))
            return await cur.fetchone()

    async def delete(self, document_id: int) -> bool:
        """Delete a document (chunks cascade). Returns whether a row was removed."""
        async with self._pool.connection() as conn:
            cur = await conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            return cur.rowcount > 0
