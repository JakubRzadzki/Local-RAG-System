"""IngestionService with fake repositories: size limit, duplicates, order of operations."""

from datetime import UTC, datetime

import pytest

from local_rag_system.exceptions import DuplicateDocumentError, FileTooLargeError
from local_rag_system.repositories.records import DocumentRecord, NewChunk
from local_rag_system.services.ingestion_service import IngestionService


class FakeDocuments:
    def __init__(self, existing: DocumentRecord | None = None) -> None:
        self.existing = existing
        self.created: list[tuple[str, str, list[NewChunk]]] = []

    async def find_by_hash(self, content_hash: str) -> DocumentRecord | None:
        return self.existing

    async def create_with_chunks(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        chunk_size: int,
        chunk_overlap: int,
        content_hash: str,
        chunks: list[NewChunk],
    ) -> DocumentRecord:
        self.created.append((filename, content_hash, chunks))
        return _record(filename)


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls = 0

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[0.0] for _ in texts]


def _record(filename: str) -> DocumentRecord:
    return DocumentRecord(1, filename, "text/plain", 1, 1, 800, 100, datetime.now(UTC))


def _service(
    documents: FakeDocuments, embeddings: FakeEmbeddings, limit: int = 1000
) -> IngestionService:
    return IngestionService(documents, None, embeddings, limit)  # type: ignore[arg-type]


async def test_file_over_the_limit_is_rejected_before_any_work() -> None:
    embeddings = FakeEmbeddings()
    service = _service(FakeDocuments(), embeddings, limit=10)

    with pytest.raises(FileTooLargeError):
        await service.ingest("a.txt", "text/plain", b"x" * 11, 800, 100)

    assert embeddings.calls == 0


async def test_duplicate_is_rejected_before_embedding() -> None:
    embeddings = FakeEmbeddings()
    service = _service(FakeDocuments(existing=_record("first.txt")), embeddings)

    with pytest.raises(DuplicateDocumentError, match="first.txt"):
        await service.ingest("copy.txt", "text/plain", b"hello world", 800, 100)

    assert embeddings.calls == 0


async def test_new_file_is_embedded_and_stored_in_one_call() -> None:
    documents = FakeDocuments()
    service = _service(documents, FakeEmbeddings())

    await service.ingest("a.txt", "text/plain", b"hello world", 800, 100)

    ((filename, content_hash, chunks),) = documents.created
    assert filename == "a.txt"
    assert len(content_hash) == 64
    assert [c.content for c in chunks] == ["hello world"]
