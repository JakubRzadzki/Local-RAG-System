"""Discovery of locally installed Ollama models."""

from local_rag_system.config import Settings
from local_rag_system.repositories.ollama_repository import OllamaRepository
from local_rag_system.repositories.records import OllamaModelRecord


class ModelService:
    """Lists models and separates chat-capable ones from embedding-only ones."""

    def __init__(self, ollama: OllamaRepository, settings: Settings) -> None:
        self._ollama = ollama
        self._settings = settings

    async def list_models(self) -> tuple[list[OllamaModelRecord], bool]:
        """Return all installed models and whether the embedding model is present."""
        models = await self._ollama.list_models()
        wanted = self._settings.embedding_model
        installed = any(m.name == wanted or m.name.split(":")[0] == wanted for m in models)
        return models, installed

    @staticmethod
    def supports_chat(model: OllamaModelRecord) -> bool:
        return "completion" in model.capabilities
