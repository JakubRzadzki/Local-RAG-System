import pytest
from psycopg_pool import AsyncConnectionPool

from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.document_repository import DocumentRepository
from local_rag_system.repositories.records import NewChunk

DIM = 768


def vec(index: int) -> list[float]:
    """Unit vector with a single 1.0 at ``index`` (cosine similarity is 1.0 or 0.0)."""
    v = [0.0] * DIM
    v[index] = 1.0
    return v


def chunk(i: int, content: str, embedding: list[float]) -> NewChunk:
    return NewChunk(chunk_index=i, content=content, page=None, embedding=embedding)


async def make_document(pool: AsyncConnectionPool, name: str = "a.txt") -> int:
    document = await DocumentRepository(pool).create_with_chunks(
        name, "text/plain", 1, 800, 100, content_hash=name, chunks=[]
    )
    return document.id


async def test_nearest_chunk_comes_first_with_expected_scores(pool: AsyncConnectionPool) -> None:
    repo = ChunkRepository(pool)
    doc = await make_document(pool)
    await repo.add_many(doc, [chunk(0, "match", vec(0)), chunk(1, "other", vec(1))])

    results = await repo.search(vec(0), top_k=2)

    assert [r.content for r in results] == ["match", "other"]
    # Identical vectors: cosine distance 0 -> score 1. Orthogonal: distance 1 -> score 0.
    assert results[0].score == pytest.approx(1.0)
    assert results[1].score == pytest.approx(0.0)


async def test_top_k_limits_results(pool: AsyncConnectionPool) -> None:
    repo = ChunkRepository(pool)
    doc = await make_document(pool)
    await repo.add_many(doc, [chunk(i, f"c{i}", vec(i)) for i in range(5)])

    assert len(await repo.search(vec(0), top_k=3)) == 3


async def test_results_carry_document_metadata(pool: AsyncConnectionPool) -> None:
    repo = ChunkRepository(pool)
    doc = await make_document(pool, "notes.md")
    await repo.add_many(doc, [NewChunk(7, "text", 3, vec(0))])

    (result,) = await repo.search(vec(0), top_k=1)

    assert (result.document_id, result.filename) == (doc, "notes.md")
    assert (result.chunk_index, result.page) == (7, 3)


async def test_document_filter_returns_only_selected_documents(pool: AsyncConnectionPool) -> None:
    repo = ChunkRepository(pool)
    first = await make_document(pool, "first.txt")
    second = await make_document(pool, "second.txt")
    await repo.add_many(first, [chunk(0, "in first", vec(0))])
    await repo.add_many(second, [chunk(0, "in second", vec(0))])

    results = await repo.search(vec(0), top_k=5, document_ids=[second])

    assert [r.document_id for r in results] == [second]


async def test_filter_still_returns_top_k_when_hnsw_candidates_are_all_filtered_out(
    pool: AsyncConnectionPool,
) -> None:
    # Without the document_id btree index the planner must use HNSW and filter afterwards.
    # HNSW only yields ~ef_search (40) candidates, all of which belong to "big", so a naive
    # query returns nothing for "small". Iterative scans make the index keep searching.
    async with pool.connection() as conn:
        await conn.execute("DROP INDEX IF EXISTS chunks_document_idx")
    repo = ChunkRepository(pool)
    big = await make_document(pool, "big.txt")
    small = await make_document(pool, "small.txt")
    await repo.add_many(big, [chunk(i, f"big {i}", vec(0)) for i in range(5000)])
    await repo.add_many(small, [chunk(i, f"small {i}", vec(1)) for i in range(3)])

    results = await repo.search(vec(0), top_k=3, document_ids=[small])

    assert len(results) == 3
    assert {r.document_id for r in results} == {small}


async def test_empty_document_ids_searches_all_documents(pool: AsyncConnectionPool) -> None:
    # The UI sends no ids when nothing is ticked, which means "search everything".
    repo = ChunkRepository(pool)
    first = await make_document(pool, "first.txt")
    second = await make_document(pool, "second.txt")
    await repo.add_many(first, [chunk(0, "a", vec(0))])
    await repo.add_many(second, [chunk(0, "b", vec(0))])

    results = await repo.search(vec(0), top_k=5, document_ids=[])

    assert {r.document_id for r in results} == {first, second}


async def test_chunks_are_removed_with_their_document(pool: AsyncConnectionPool) -> None:
    repo = ChunkRepository(pool)
    documents = DocumentRepository(pool)
    doc = await make_document(pool)
    await repo.add_many(doc, [chunk(0, "x", vec(0))])

    assert await documents.delete(doc) is True

    assert await repo.list_by_document(doc) == []
    assert await repo.search(vec(0), top_k=5) == []
