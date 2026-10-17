"""Persistence of document metadata."""

from collections.abc import Sequence

from psycopg.errors import UniqueViolation
from psycopg.rows import class_row
from psycopg_pool import AsyncConnectionPool

from local_rag_system.exceptions import DuplicateDocumentError
from local_rag_system.repositories.chunk_repository import INSERT_CHUNK, chunk_rows
from local_rag_system.repositories.records import DocumentRecord, NewChunk

_COLUMNS = (
    "id, filename, content_type, size_bytes, chunk_count, chunk_size, chunk_overlap, created_at"
)


class DocumentRepository:
    """CRUD operations on the ``documents`` table."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def create_with_chunks(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        chunk_size: int,
        chunk_overlap: int,
        content_hash: str,
        chunks: Sequence[NewChunk],
    ) -> DocumentRecord:
        """Insert a document and all its chunks in one transaction.

        Raises:
            DuplicateDocumentError: if a document with the same content hash exists.
        """
        query = f"""
            INSERT INTO documents (filename, content_type, size_bytes, chunk_count,
                                   chunk_size, chunk_overlap, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING {_COLUMNS}"""
        try:
            async with self._pool.connection() as conn:
                cur = conn.cursor(row_factory=class_row(DocumentRecord))
                await cur.execute(
                    query,
                    (
                        filename,
                        content_type,
                        size_bytes,
                        len(chunks),
                        chunk_size,
                        chunk_overlap,
                        content_hash,
                    ),
                )
                record = await cur.fetchone()
                assert record is not None
                await cur.executemany(INSERT_CHUNK, chunk_rows(record.id, chunks))
        except UniqueViolation as exc:
            raise DuplicateDocumentError("This file has already been uploaded.") from exc
        return record

    async def find_by_hash(self, content_hash: str) -> DocumentRecord | None:
        async with self._pool.connection() as conn:
            cur = conn.cursor(row_factory=class_row(DocumentRecord))
            await cur.execute(
                f"SELECT {_COLUMNS} FROM documents WHERE content_hash = %s", (content_hash,)
            )
            return await cur.fetchone()

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
