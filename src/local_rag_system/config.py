"""Application settings, overridable through ``RAG_*`` environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/rag"
    ollama_host: str = "http://localhost:11434"

    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    embedding_batch_size: int = 32
    # nomic-embed-text was trained with task prefixes; other models can set "".
    embedding_document_prefix: str = "search_document: "
    embedding_query_prefix: str = "search_query: "

    default_chunk_size: int = 800
    default_chunk_overlap: int = 100
    max_upload_bytes: int = 20 * 1024 * 1024

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
