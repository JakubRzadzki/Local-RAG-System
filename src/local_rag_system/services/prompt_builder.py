"""Prompt assembly for grounded question answering."""

from collections.abc import Sequence

from local_rag_system.repositories.records import RetrievedChunk
from local_rag_system.schemas.chat import ChatMessage
from local_rag_system.services.app_guide import APP_GUIDE

SYSTEM_PROMPT = (
    "You are a helpful assistant inside a local RAG application. You answer questions "
    "using the context excerpts from the user's documents, and you can also explain how "
    "this application works.\n"
    "Rules:\n"
    "- For questions about the user's documents, base your answer on the context and cite "
    "the excerpts you used with their numbers in square brackets, e.g. [1] or [2][3]. If "
    "the context does not contain the answer, say so plainly instead of guessing.\n"
    "- For questions about this application (features, how to use it, how it works), "
    "answer from the application guide below. Do not cite excerpts for those.\n"
    "- For greetings and general questions unrelated to the documents, answer normally "
    "and briefly, without citations.\n"
    "- Answer in the same language as the user's question.\n"
    "- Be concise and use Markdown where it helps readability."
)

NO_CONTEXT_NOTE = (
    "No documents have been indexed yet, so there is no context available. "
    "If the question depends on documents, tell the user to upload some."
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
    """Build the chat payload: system prompt, app guide and context, then the conversation."""
    system = f"{SYSTEM_PROMPT}\n\n{APP_GUIDE}\n\nContext:\n{format_context(chunks)}"
    return [
        {"role": "system", "content": system},
        *({"role": m.role, "content": m.content} for m in history),
    ]
