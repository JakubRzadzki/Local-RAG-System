import pytest
from psycopg_pool import AsyncConnectionPool

from local_rag_system.exceptions import DuplicateDocumentError
from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.document_repository import DocumentRepository
from local_rag_system.repositories.records import NewChunk

DIM = 768


def new_chunk(i: int, embedding: list[float] | None = None) -> NewChunk:
    return NewChunk(i, f"chunk {i}", None, embedding or [1.0] + [0.0] * (DIM - 1))


async def test_document_and_chunks_are_stored_together(pool: AsyncConnectionPool) -> None:
    documents = DocumentRepository(pool)

    document = await documents.create_with_chunks(
        "a.txt", "text/plain", 10, 800, 100, "hash-a", [new_chunk(0), new_chunk(1)]
    )

    assert document.chunk_count == 2
    stored = await ChunkRepository(pool).list_by_document(document.id)
    assert [c.chunk_index for c in stored] == [0, 1]


async def test_same_content_hash_is_rejected_as_duplicate(pool: AsyncConnectionPool) -> None:
    documents = DocumentRepository(pool)
    await documents.create_with_chunks("a.txt", "text/plain", 1, 800, 100, "same", [])

    with pytest.raises(DuplicateDocumentError):
        await documents.create_with_chunks("copy.txt", "text/plain", 1, 800, 100, "same", [])

    assert len(await documents.list_all()) == 1


async def test_failed_chunk_insert_rolls_back_the_document(pool: AsyncConnectionPool) -> None:
    documents = DocumentRepository(pool)
    wrong_dimension = new_chunk(0, embedding=[1.0, 0.0])  # column is VECTOR(768)

    with pytest.raises(Exception, match="dimensions"):
        await documents.create_with_chunks(
            "a.txt", "text/plain", 1, 800, 100, "hash", [wrong_dimension]
        )

    assert await documents.list_all() == []
    assert await documents.find_by_hash("hash") is None
