"""FastAPI dependency providers that wire repositories into services."""

from typing import Annotated

from fastapi import Depends, Request
from ollama import AsyncClient
from psycopg_pool import AsyncConnectionPool

from local_rag_system.config import Settings, get_settings
from local_rag_system.repositories.chunk_repository import ChunkRepository
from local_rag_system.repositories.conversation_repository import ConversationRepository
from local_rag_system.repositories.document_repository import DocumentRepository
from local_rag_system.repositories.ollama_repository import OllamaRepository
from local_rag_system.repositories.web_search_repository import WebSearchRepository
from local_rag_system.services.conversation_service import ConversationService
from local_rag_system.services.embedding_service import EmbeddingService
from local_rag_system.services.ingestion_service import IngestionService
from local_rag_system.services.model_service import ModelService
from local_rag_system.services.rag_service import RagService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _pool(request: Request) -> AsyncConnectionPool:
    pool: AsyncConnectionPool = request.app.state.pool
    return pool


def _ollama_client(request: Request) -> AsyncClient:
    client: AsyncClient = request.app.state.ollama_client
    return client


def get_ollama_repository(
    client: Annotated[AsyncClient, Depends(_ollama_client)],
) -> OllamaRepository:
    return OllamaRepository(client)


OllamaRepoDep = Annotated[OllamaRepository, Depends(get_ollama_repository)]


def get_embedding_service(ollama: OllamaRepoDep, settings: SettingsDep) -> EmbeddingService:
    return EmbeddingService(ollama, settings)


def get_model_service(ollama: OllamaRepoDep, settings: SettingsDep) -> ModelService:
    return ModelService(ollama, settings)


def get_ingestion_service(
    pool: Annotated[AsyncConnectionPool, Depends(_pool)],
    embeddings: Annotated[EmbeddingService, Depends(get_embedding_service)],
    settings: SettingsDep,
) -> IngestionService:
    return IngestionService(
        DocumentRepository(pool),
        ChunkRepository(pool),
        embeddings,
        settings.max_upload_bytes,
    )


def get_rag_service(
    pool: Annotated[AsyncConnectionPool, Depends(_pool)],
    ollama: OllamaRepoDep,
    settings: SettingsDep,
    embeddings: Annotated[EmbeddingService, Depends(get_embedding_service)],
) -> RagService:
    return RagService(
        ChunkRepository(pool),
        ConversationRepository(pool),
        ollama,
        embeddings,
        WebSearchRepository(),
        settings.effective_min_score,
    )


def get_conversation_service(
    pool: Annotated[AsyncConnectionPool, Depends(_pool)],
) -> ConversationService:
    return ConversationService(ConversationRepository(pool))


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]
ModelServiceDep = Annotated[ModelService, Depends(get_model_service)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
RagServiceDep = Annotated[RagService, Depends(get_rag_service)]
