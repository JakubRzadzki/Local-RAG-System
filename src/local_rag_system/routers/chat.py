"""``/api/chat`` streaming endpoint."""

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from local_rag_system.dependencies import RagServiceDep
from local_rag_system.schemas.chat import ChatRequest, encode_event

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_class=StreamingResponse)
async def chat(request: ChatRequest, service: RagServiceDep) -> StreamingResponse:
    """Answer a question from the indexed documents.

    Streams newline-delimited JSON events: one ``sources`` event, many ``token``
    events and a final ``done`` (or ``error``) event.
    """

    async def body() -> AsyncIterator[str]:
        async for event in service.stream_answer(request):
            yield encode_event(event)

    return StreamingResponse(
        body(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
