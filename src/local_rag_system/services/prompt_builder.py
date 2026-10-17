"""Prompt assembly for grounded question answering."""

from collections.abc import Sequence

from local_rag_system.repositories.records import RetrievedChunk
from local_rag_system.schemas.chat import ChatMessage

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using the provided context "
    "excerpts from the user's documents.\n"
    "Rules:\n"
    "- Base your answer on the context. If it does not contain the answer, say so "
    "plainly instead of guessing.\n"
    "- Cite the excerpts you used with their numbers in square brackets, e.g. [1] or "
    "[2][3].\n"
    "- Answer in the same language as the user's question.\n"
    "- Be concise and use Markdown where it helps readability."
)

NO_CONTEXT_NOTE = (
    "No documents have been indexed yet, so there is no context available. "
    "Tell the user to upload documents if their question depends on them."
)


def format_context(chunks: Sequence[RetrievedChunk]) -> str:
    """Render retrieved chunks as numbered, attributable excerpts."""
    if not chunks:
        return NO_CONTEXT_NOTE
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        location = f"{chunk.filename}, chunk {chunk.chunk_index}"
        if chunk.page is not None:
            location += f", page {chunk.page}"
        blocks.append(f"[{number}] ({location})\n{chunk.content}")
    return "\n\n".join(blocks)


def build_messages(
    history: Sequence[ChatMessage], chunks: Sequence[RetrievedChunk]
) -> list[dict[str, str]]:
    """Build the chat payload: system prompt with context, then the conversation."""
    system = f"{SYSTEM_PROMPT}\n\nContext:\n{format_context(chunks)}"
    return [
        {"role": "system", "content": system},
        *({"role": m.role, "content": m.content} for m in history),
    ]
