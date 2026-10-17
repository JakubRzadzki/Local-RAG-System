"""Conversation history management."""

from local_rag_system.exceptions import ConversationNotFoundError
from local_rag_system.repositories.conversation_repository import ConversationRepository
from local_rag_system.repositories.records import ConversationRecord, MessageRecord

TITLE_MAX_LENGTH = 60


def make_title(first_message: str) -> str:
    """Derive a short single-line title from the first user message."""
    flat = " ".join(first_message.split())
    return flat if len(flat) <= TITLE_MAX_LENGTH else flat[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


class ConversationService:
    """Lists, renames and deletes saved conversations."""

    def __init__(self, conversations: ConversationRepository) -> None:
        self._conversations = conversations

    async def list_conversations(self) -> list[ConversationRecord]:
        return await self._conversations.list_all()

    async def get_with_messages(
        self, conversation_id: int
    ) -> tuple[ConversationRecord, list[MessageRecord]]:
        conversation = await self._require(conversation_id)
        return conversation, await self._conversations.list_messages(conversation_id)

    async def rename(self, conversation_id: int, title: str) -> ConversationRecord:
        renamed = await self._conversations.rename(conversation_id, title.strip())
        if renamed is None:
            raise ConversationNotFoundError(f"Conversation {conversation_id} not found.")
        return renamed

    async def delete(self, conversation_id: int) -> None:
        if not await self._conversations.delete(conversation_id):
            raise ConversationNotFoundError(f"Conversation {conversation_id} not found.")

    async def _require(self, conversation_id: int) -> ConversationRecord:
        conversation = await self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation {conversation_id} not found.")
        return conversation
