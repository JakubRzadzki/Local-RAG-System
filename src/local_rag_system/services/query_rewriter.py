"""Turn short follow-up questions into standalone search queries."""

import logging
from collections.abc import Sequence

from local_rag_system.exceptions import RagError
from local_rag_system.repositories.ollama_repository import OllamaRepository
from local_rag_system.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

# Longer questions are normally self-contained, so they skip the extra model call.
MAX_WORDS_TO_REWRITE = 12
HISTORY_MESSAGES = 6
MAX_MESSAGE_CHARS = 400
MAX_QUERY_CHARS = 300

REWRITE_PROMPT = (
    "Rewrite the user's last message as one standalone search query, using the earlier "
    "conversation to resolve references such as 'it', 'that one' or 'the second'. Keep the "
    "language of the message. Reply with the query only: no quotes, no explanation."
)


def needs_rewrite(history: Sequence[ChatMessage]) -> bool:
    """A follow-up is a short message that comes after earlier turns."""
    return len(history) > 1 and len(history[-1].content.split()) < MAX_WORDS_TO_REWRITE


def _transcript(history: Sequence[ChatMessage]) -> str:
    lines = [f"{m.role}: {m.content[:MAX_MESSAGE_CHARS]}" for m in history[-HISTORY_MESSAGES:]]
    return "\n".join(lines)


class QueryRewriter:
    """Makes retrieval work for follow-ups like "and the second one?"."""

    def __init__(self, ollama: OllamaRepository) -> None:
        self._ollama = ollama

    async def rewrite(self, model: str, history: Sequence[ChatMessage], think: bool | None) -> str:
        """Return a standalone query, or the last message unchanged if that is not possible."""
        question = history[-1].content
        if not needs_rewrite(history):
            return question
        try:
            raw = await self._ollama.chat_once(
                model,
                [
                    {"role": "system", "content": REWRITE_PROMPT},
                    {"role": "user", "content": _transcript(history)},
                ],
                think,
                max_tokens=80,
            )
        except RagError:
            logger.warning("Query rewriting failed; using the original question", exc_info=True)
            return question
        rewritten = " ".join(raw.split()).strip("\"'")[:MAX_QUERY_CHARS]
        if not rewritten:
            return question
        logger.info("Rewrote follow-up %r as %r", question, rewritten)
        return rewritten
