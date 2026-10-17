"""Orchestration of the retrieval-augmented generation pipeline."""

import asyncio
import logging
from collections.abc import AsyncIterator

from local_rag_system.exceptions import ConversationNotFoundError, RagError
from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.conversation_repository import ConversationRepository
from local_rag_system.repositories.ollama_repository import OllamaRepository
from local_rag_system.schemas.chat import (
    ChatEvent,
    ChatRequest,
    ConversationEvent,
    DoneEvent,
    ErrorEvent,
    SourceOut,
    SourcesEvent,
    TokenEvent,
)
from local_rag_system.services.conversation_service import make_title
from local_rag_system.services.embedding_service import EmbeddingService
from local_rag_system.services.prompt_builder import build_messages

logger = logging.getLogger(__name__)


class RagService:
    """retrieve -> build prompt -> stream the answer, persisting the conversation."""

    def __init__(
        self,
        chunks: ChunkRepository,
        conversations: ConversationRepository,
        ollama: OllamaRepository,
        embeddings: EmbeddingService,
    ) -> None:
        self._chunks = chunks
        self._conversations = conversations
        self._ollama = ollama
        self._embeddings = embeddings

    async def stream_answer(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        """Yield conversation, sources, token and done events.

        Failures are reported in-band as an :class:`ErrorEvent` because the HTTP
        status has already been sent once streaming begins. A partially streamed
        answer (e.g. the user pressed stop) is still saved to the conversation.
        """
        answer: list[str] = []
        sources: list[SourceOut] = []
        conversation_id: int | None = None
        try:
            capabilities = await self._ollama.capabilities(request.model)

            query = request.messages[-1].content
            conversation_id, title = await self._open_conversation(request, query)
            yield ConversationEvent(id=conversation_id, title=title)
            await self._conversations.add_message(conversation_id, "user", query)

            query_vector = await self._embeddings.embed_query(query)
            retrieved = await self._chunks.search(
                query_vector, request.options.top_k, request.options.document_ids
            )
            sources = [
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
            yield SourcesEvent(sources=sources)

            # Thinking models stall before the first token; disable it where supported.
            think = False if "thinking" in capabilities else None
            messages = build_messages(request.messages, retrieved)
            async for token in self._ollama.stream_chat(
                request.model, messages, request.options.temperature, think
            ):
                answer.append(token)
                yield TokenEvent(content=token)
            yield DoneEvent()
        except RagError as exc:
            yield ErrorEvent(message=_describe(exc))
        except Exception:
            logger.exception("Unexpected error while answering")
            yield ErrorEvent(message="Unexpected error while generating the answer.")
        finally:
            if conversation_id is not None and answer:
                await asyncio.shield(self._save_answer(conversation_id, "".join(answer), sources))

    async def _open_conversation(self, request: ChatRequest, query: str) -> tuple[int, str]:
        if request.conversation_id is None:
            created = await self._conversations.create(make_title(query), request.model)
            return created.id, created.title
        existing = await self._conversations.get(request.conversation_id)
        if existing is None:
            raise ConversationNotFoundError(f"Conversation {request.conversation_id} not found.")
        return existing.id, existing.title

    async def _save_answer(
        self, conversation_id: int, content: str, sources: list[SourceOut]
    ) -> None:
        try:
            await self._conversations.add_message(
                conversation_id,
                "assistant",
                content,
                [source.model_dump() for source in sources],
            )
        except Exception:
            logger.exception("Could not save the assistant message")


def _describe(exc: RagError) -> str:
    return f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
