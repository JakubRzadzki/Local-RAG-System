import re

import pytest

from local_rag_system.exceptions import InvalidChunkingError
from local_rag_system.services.chunking_service import chunk_text

TEXT = (
    "First paragraph about dogs. Dogs love walks and playing.\n\n"
    "Second paragraph about cats. Cats sleep for most of the day.\n\n"
    "Third paragraph about fish. Fish swim in water and do not need walks."
)

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
) * 6


def _words(text: str) -> set[str]:
    return set(re.findall(r"\S+", text))


def test_short_text_is_a_single_chunk() -> None:
    assert len(chunk_text(TEXT, size=1000, overlap=20)) == 1


@pytest.mark.parametrize(("size", "overlap"), [(100, 20), (200, 50), (800, 100), (60, 10)])
def test_no_chunk_exceeds_size(size: int, overlap: int) -> None:
    for text in (TEXT, LOREM, LOREM.replace(" ", "\n")):
        assert all(len(c) <= size for c in chunk_text(text, size=size, overlap=overlap))


def test_paragraphs_become_separate_chunks_when_they_do_not_fit() -> None:
    chunks = chunk_text(TEXT, size=100, overlap=20)
    assert len(chunks) >= 3


def test_long_paragraph_is_split_on_word_boundaries() -> None:
    vocabulary = _words(LOREM)
    chunks = chunk_text(LOREM, size=120, overlap=30)
    assert len(chunks) > 3
    for chunk in chunks:
        assert _words(chunk) <= vocabulary, f"word split in the middle: {chunk!r}"


def test_consecutive_long_chunks_overlap() -> None:
    chunks = chunk_text(LOREM, size=120, overlap=30)
    for previous, following in zip(chunks, chunks[1:], strict=False):
        assert _words(previous) & _words(following)


def test_windows_line_endings_chunk_like_unix_ones() -> None:
    unix = chunk_text(TEXT, size=100, overlap=20)
    windows = chunk_text(TEXT.replace("\n", "\r\n"), size=100, overlap=20)
    assert windows == unix


def test_single_newlines_as_produced_by_pdfs_still_split_cleanly() -> None:
    pdf_like = LOREM.replace(". ", ".\n")
    vocabulary = _words(pdf_like)
    chunks = chunk_text(pdf_like, size=150, overlap=30)
    assert all(_words(c) <= vocabulary for c in chunks)


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("  \n\n  ") == []


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (100, 100), (100, -1)])
def test_invalid_parameters_are_rejected(size: int, overlap: int) -> None:
    with pytest.raises(InvalidChunkingError):
        chunk_text("text", size=size, overlap=overlap)
