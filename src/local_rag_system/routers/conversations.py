"""``/api/conversations`` endpoints."""

from fastapi import APIRouter, Response, status

from local_rag_system.dependencies import ConversationServiceDep
from local_rag_system.schemas.chat import SourceOut
from local_rag_system.schemas.conversations import (
    ConversationDetailOut,
    ConversationOut,
    ConversationRename,
    StoredMessageOut,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def list_conversations(service: ConversationServiceDep) -> list[ConversationOut]:
    """List saved conversations, most recently active first."""
    return [ConversationOut.model_validate(c) for c in await service.list_conversations()]


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: int, service: ConversationServiceDep
) -> ConversationDetailOut:
    """Return a conversation with all of its messages and their sources."""
    conversation, messages = await service.get_with_messages(conversation_id)
    return ConversationDetailOut(
        **ConversationOut.model_validate(conversation).model_dump(),
        messages=[
            StoredMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=[SourceOut.model_validate(s) for s in m.sources],
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: int, body: ConversationRename, service: ConversationServiceDep
) -> ConversationOut:
    """Rename a conversation."""
    return ConversationOut.model_validate(await service.rename(conversation_id, body.title))


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int, service: ConversationServiceDep) -> Response:
    """Delete a conversation and its messages."""
    await service.delete(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
