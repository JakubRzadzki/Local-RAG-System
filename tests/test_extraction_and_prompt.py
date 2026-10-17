from pathlib import Path

import pytest

from local_rag_system.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from local_rag_system.repositories.records import RetrievedChunk, WebResult
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


def test_web_results_are_numbered_after_document_excerpts() -> None:
    web = [WebResult(title="Weather", url="https://w.example", snippet="Sunny, 21C")]
    messages = build_messages([ChatMessage(role="user", content="q")], [_chunk(page=None)], web)
    system = messages[0]["content"]
    assert "[2] (Weather - https://w.example)" in system
    assert "Sunny, 21C" in system


def test_disabled_web_search_points_user_to_the_toggle() -> None:
    system = build_messages([ChatMessage(role="user", content="q")], [], None)[0]["content"]
    assert "Web toggle" in system


def test_failed_web_search_is_reported_to_the_model() -> None:
    system = build_messages([ChatMessage(role="user", content="q")], [], [], web_failed=True)[0][
        "content"
    ]
    assert "failed" in system


async def test_damaged_pdf_is_a_domain_error() -> None:
    with pytest.raises(CorruptDocumentError):
        await extract_sections("broken.pdf", b"%PDF-1.4 this is not a real pdf")


async def test_truncated_pdf_is_a_domain_error() -> None:
    data = (SAMPLE_DOCS / "python-tooling-cheatsheet.pdf").read_bytes()
    with pytest.raises(CorruptDocumentError):
        await extract_sections("cut.pdf", data[:200])
