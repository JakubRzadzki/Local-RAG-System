"""Orchestration of the retrieval-augmented generation pipeline."""

import logging
from collections.abc import AsyncIterator

from local_rag_system.exceptions import RagError
from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.ollama_repository import OllamaRepository
from local_rag_system.schemas.chat import (
    ChatEvent,
    ChatRequest,
    DoneEvent,
    ErrorEvent,
    SourceOut,
    SourcesEvent,
    TokenEvent,
)
from local_rag_system.services.embedding_service import EmbeddingService
from local_rag_system.services.prompt_builder import build_messages

logger = logging.getLogger(__name__)


class RagService:
    """retrieve -> build prompt -> stream the answer."""

    def __init__(
        self,
        chunks: ChunkRepository,
        ollama: OllamaRepository,
        embeddings: EmbeddingService,
    ) -> None:
        self._chunks = chunks
        self._ollama = ollama
        self._embeddings = embeddings

    async def stream_answer(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        """Yield a sources event, then tokens, then a done event.

        Failures are reported in-band as an :class:`ErrorEvent` because the HTTP
        status has already been sent once streaming begins.
        """
        try:
            capabilities = await self._ollama.capabilities(request.model)

            query = request.messages[-1].content
            query_vector = await self._embeddings.embed_query(query)
            retrieved = await self._chunks.search(
                query_vector, request.options.top_k, request.options.document_ids
            )
            yield SourcesEvent(
                sources=[
                    SourceOut(
                        index=number,
                        document_id=chunk.document_id,
                        filename=chunk.filename,
                        chunk_index=chunk.chunk_index,
                        page=chunk.page,
                        score=round(chunk.score, 4),
                        content=chunk.content,
                    )
                    for number, chunk in enumerate(retrieved, start=1)
                ]
            )

            # Thinking models stall before the first token; disable it where supported.
            think = False if "thinking" in capabilities else None
            messages = build_messages(request.messages, retrieved)
            async for token in self._ollama.stream_chat(
                request.model, messages, request.options.temperature, think
            ):
                yield TokenEvent(content=token)
            yield DoneEvent()
        except RagError as exc:
            yield ErrorEvent(message=_describe(exc))
        except Exception:
            logger.exception("Unexpected error while answering")
            yield ErrorEvent(message="Unexpected error while generating the answer.")


def _describe(exc: RagError) -> str:
    return f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
