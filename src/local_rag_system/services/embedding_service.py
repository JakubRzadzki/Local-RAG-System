"""Embedding of documents and queries with the configured Ollama model."""

from collections.abc import Sequence

from local_rag_system.config import Settings
from local_rag_system.repositories.ollama_repository import OllamaRepository


class EmbeddingService:
    """Applies task prefixes and batches requests to the embedding model."""

    def __init__(self, ollama: OllamaRepository, settings: Settings) -> None:
        self._ollama = ollama
        self._settings = settings

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        prefix = self._settings.embedding_document_prefix
        batch_size = self._settings.embedding_batch_size
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = [prefix + text for text in texts[start : start + batch_size]]
            vectors.extend(await self._ollama.embed(self._settings.embedding_model, batch))
        return vectors

    async def embed_query(self, query: str) -> list[float]:
        prefixed = self._settings.embedding_query_prefix + query
        (vector,) = await self._ollama.embed(self._settings.embedding_model, [prefixed])
        return vector
