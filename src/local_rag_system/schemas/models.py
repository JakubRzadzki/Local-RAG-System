"""Ollama model DTOs."""

from pydantic import BaseModel, ConfigDict


class ModelOut(BaseModel):
    """A locally installed Ollama model."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    size_bytes: int
    family: str
    parameter_size: str
    quantization: str
    capabilities: list[str]
    supports_chat: bool


class ModelsResponse(BaseModel):
    """Installed models plus the embedding model used for retrieval."""

    models: list[ModelOut]
    embedding_model: str
    embedding_model_installed: bool
