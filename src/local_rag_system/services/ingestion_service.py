"""Document ingestion: extract, chunk, embed and store."""

from local_rag_system.exceptions import DocumentNotFoundError, FileTooLargeError
from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.document_repository import DocumentRepository
from local_rag_system.repositories.records import DocumentRecord, NewChunk
from local_rag_system.services.chunking_service import chunk_text
from local_rag_system.services.embedding_service import EmbeddingService
from local_rag_system.services.text_extraction_service import extract_sections


class IngestionService:
    """Turns an uploaded file into searchable chunks."""

    def __init__(
        self,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        embeddings: EmbeddingService,
        max_upload_bytes: int,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._embeddings = embeddings
        self._max_upload_bytes = max_upload_bytes

    async def ingest(
        self,
        filename: str,
        content_type: str,
        data: bytes,
        chunk_size: int,
        chunk_overlap: int,
    ) -> DocumentRecord:
        if len(data) > self._max_upload_bytes:
            raise FileTooLargeError(
                f"File exceeds the {self._max_upload_bytes // (1024 * 1024)} MB limit."
            )

        sections = await extract_sections(filename, data)
        pieces: list[tuple[str, int | None]] = [
            (chunk, section.page)
            for section in sections
            for chunk in chunk_text(section.text, chunk_size, chunk_overlap)
        ]

        # Embed before touching the database so a failure leaves nothing behind.
        vectors = await self._embeddings.embed_documents([text for text, _ in pieces])
        new_chunks = [
            NewChunk(chunk_index=i, content=text, page=page, embedding=vector)
            for i, ((text, page), vector) in enumerate(zip(pieces, vectors, strict=True))
        ]

        document = await self._documents.create(
            filename, content_type, len(data), chunk_size, chunk_overlap
        )
        try:
            await self._chunks.add_many(document.id, new_chunks)
            await self._documents.set_chunk_count(document.id, len(new_chunks))
        except Exception:
            await self._documents.delete(document.id)
            raise
        return await self._require(document.id)

    async def list_documents(self) -> list[DocumentRecord]:
        return await self._documents.list_all()

    async def delete_document(self, document_id: int) -> None:
        if not await self._documents.delete(document_id):
            raise DocumentNotFoundError(f"Document {document_id} not found.")

    async def _require(self, document_id: int) -> DocumentRecord:
        document = await self._documents.get(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document {document_id} not found.")
        return document
