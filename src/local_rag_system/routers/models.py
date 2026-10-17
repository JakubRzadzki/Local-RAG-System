"""``/api/models`` endpoints."""

from fastapi import APIRouter

from local_rag_system.dependencies import ModelServiceDep, SettingsDep
from local_rag_system.schemas.models import ModelOut, ModelsResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelsResponse)
async def list_models(service: ModelServiceDep, settings: SettingsDep) -> ModelsResponse:
    """List locally installed Ollama models."""
    models, embedding_installed = await service.list_models()
    return ModelsResponse(
        models=[
            ModelOut(
                name=m.name,
                size_bytes=m.size_bytes,
                family=m.family,
                parameter_size=m.parameter_size,
                quantization=m.quantization,
                capabilities=list(m.capabilities),
                supports_chat=service.supports_chat(m),
            )
            for m in models
        ],
        embedding_model=settings.embedding_model,
        embedding_model_installed=embedding_installed,
    )
