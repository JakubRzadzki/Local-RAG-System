"""Application settings, overridable through ``RAG_*`` environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Measured on the sample documents: relevant top hits scored 0.74-0.84, unrelated <= 0.57.
CALIBRATED_MIN_SCORES: dict[str, float] = {"nomic-embed-text": 0.6}


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5432/rag"
    ollama_host: str = "http://localhost:11434"

    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    embedding_batch_size: int = 32
    # nomic-embed-text was trained with task prefixes; other models can set "".
    embedding_document_prefix: str = "search_document: "
    embedding_query_prefix: str = "search_query: "

    # Minimum cosine similarity for a chunk to be used. Leave unset to use the value
    # calibrated for the embedding model (see CALIBRATED_MIN_SCORES); similarity scales
    # differ between models, so a number tuned for one can cut off everything for another.
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)

    default_chunk_size: int = 800
    default_chunk_overlap: int = 100
    max_upload_bytes: int = 20 * 1024 * 1024

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @property
    def min_score_is_calibrated(self) -> bool:
        """Whether a threshold is configured or known for the embedding model."""
        return self.min_score is not None or self._model_family() in CALIBRATED_MIN_SCORES

    @property
    def effective_min_score(self) -> float:
        """The threshold to apply: explicit, calibrated for the model, or 0 (no filtering)."""
        if self.min_score is not None:
            return self.min_score
        return CALIBRATED_MIN_SCORES.get(self._model_family(), 0.0)

    def _model_family(self) -> str:
        return self.embedding_model.split(":")[0]


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
