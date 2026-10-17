from pathlib import Path

import pytest

from local_rag_system.exceptions import EmptyDocumentError, UnsupportedFileTypeError
from local_rag_system.repositories.records import RetrievedChunk
from local_rag_system.schemas.chat import ChatMessage
from local_rag_system.services.prompt_builder import build_messages, format_context
from local_rag_system.services.text_extraction_service import extract_sections

SAMPLE_DOCS = Path(__file__).resolve().parent.parent / "sample_docs"


def _chunk(page: int | None) -> RetrievedChunk:
    return RetrievedChunk(1, 1, "a.pdf", 3, page, "hello", 0.9)


async def test_extracts_plain_text() -> None:
    sections = await extract_sections("notes.md", "# Hi\n\nżółć".encode())
    assert [s.text for s in sections] == ["# Hi\n\nżółć"]
    assert sections[0].page is None


async def test_extracts_pdf_pages() -> None:
    data = (SAMPLE_DOCS / "python-tooling-cheatsheet.pdf").read_bytes()
    sections = await extract_sections("cheatsheet.pdf", data)
    assert [s.page for s in sections] == [1, 2, 3]
    assert "uv" in sections[0].text


async def test_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        await extract_sections("data.exe", b"x")


async def test_rejects_blank_file() -> None:
    with pytest.raises(EmptyDocumentError):
        await extract_sections("empty.txt", b"  \n")


def test_context_is_numbered_with_location() -> None:
    context = format_context([_chunk(page=2)])
    assert context.startswith("[1] (a.pdf, chunk 3, page 2)")


def test_messages_start_with_system_prompt_and_keep_history() -> None:
    history = [ChatMessage(role="user", content="q")]
    messages = build_messages(history, [_chunk(page=None)])
    assert messages[0]["role"] == "system"
    assert "hello" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "q"}
