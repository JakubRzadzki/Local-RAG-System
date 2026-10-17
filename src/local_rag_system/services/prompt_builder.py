"""Prompt assembly for grounded question answering."""

from collections.abc import Sequence

from local_rag_system.repositories.records import RetrievedChunk, WebResult
from local_rag_system.schemas.chat import ChatMessage
from local_rag_system.services.app_guide import APP_GUIDE

SYSTEM_PROMPT = (
    "You are a helpful assistant inside a local RAG application. You answer questions "
    "using the context excerpts from the user's documents and, when enabled, web search "
    "results. You can also explain how this application works.\n"
    "Rules:\n"
    "- For questions about the user's documents, base your answer on the document "
    "excerpts and cite the ones you used with their numbers in square brackets, e.g. [1] "
    "or [2][3]. If they do not contain the answer, say so plainly instead of guessing.\n"
    "- For questions about this application (features, how to use it, how it works), "
    "answer from the application guide below. Do not cite excerpts for those.\n"
    "- When web search results are provided, use them for current or external facts "
    "(news, weather, prices, recent events) and cite them by number like the document "
    "excerpts. If the results are not enough, say what is missing.\n"
    "- For greetings, small talk and general-knowledge questions that are not about the "
    "documents (definitions, how things work, simple facts, coding help), answer directly "
    "from your own knowledge, without citations. Do not refuse just because the documents "
    "do not cover the topic; you may mention briefly that the answer is not from the "
    "documents, but do not apologize.\n"
    "- Only say you cannot help when the request needs live data you do not have. Keep "
    "that to one short sentence, then offer what you can do instead.\n"
    "- Answer in the same language as the user's question.\n"
    "- Be concise and use Markdown where it helps readability."
)

NO_CONTEXT_NOTE = (
    "No document excerpts are available (no documents are indexed or none matched). "
    "If the question depends on documents, tell the user to upload some."
)

WEB_DISABLED_NOTE = (
    "Web search is switched off. If the user needs live or current information, tell "
    "them to enable the Web toggle next to the message box."
)

WEB_FAILED_NOTE = "Web search was requested but failed, so no web results are available."

WEB_NO_RESULTS_NOTE = "Web search returned no results."


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


def format_web_results(results: Sequence[WebResult], first_number: int) -> str:
    """Render web results numbered after the document excerpts."""
    blocks = [
        f"[{number}] ({result.title} - {result.url})\n{result.snippet}"
        for number, result in enumerate(results, start=first_number)
    ]
    return "\n\n".join(blocks)


def build_messages(
    history: Sequence[ChatMessage],
    chunks: Sequence[RetrievedChunk],
    web_results: Sequence[WebResult] | None = None,
    web_failed: bool = False,
) -> list[dict[str, str]]:
    """Build the chat payload: system prompt, guide and context, then the conversation.

    ``web_results`` is ``None`` when web search is off, a list (possibly empty) when on.
    """
    parts = [SYSTEM_PROMPT, APP_GUIDE, f"Document excerpts:\n{format_context(chunks)}"]
    if web_failed:
        parts.append(WEB_FAILED_NOTE)
    elif web_results is None:
        parts.append(WEB_DISABLED_NOTE)
    elif web_results:
        parts.append(f"Web search results:\n{format_web_results(web_results, len(chunks) + 1)}")
    else:
        parts.append(WEB_NO_RESULTS_NOTE)
    return [
        {"role": "system", "content": "\n\n".join(parts)},
        *({"role": m.role, "content": m.content} for m in history),
    ]
