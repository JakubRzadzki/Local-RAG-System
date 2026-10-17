import pytest

from local_rag_system.exceptions import InvalidChunkingError
from local_rag_system.services.chunking_service import chunk_text

TEXT = (
    "First paragraph about dogs. Dogs love walks and playing.\n\n"
    "Second paragraph about cats. Cats sleep for most of the day.\n\n"
    "Third paragraph about fish. Fish swim in water and do not need walks."
)


def test_short_text_is_a_single_chunk() -> None:
    assert len(chunk_text(TEXT, size=1000, overlap=20)) == 1


def test_chunks_respect_size_and_overlap_between_paragraphs() -> None:
    chunks = chunk_text(TEXT, size=100, overlap=20)
    assert len(chunks) >= 3
    assert all(len(c) <= 100 + 20 + 2 for c in chunks)


def test_long_paragraph_is_split_by_characters() -> None:
    chunks = chunk_text("word " * 100, size=100, overlap=10)
    assert len(chunks) > 3
    assert all(len(c) <= 100 for c in chunks)


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("  \n\n  ") == []


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (100, 100), (100, -1)])
def test_invalid_parameters_are_rejected(size: int, overlap: int) -> None:
    with pytest.raises(InvalidChunkingError):
        chunk_text("text", size=size, overlap=overlap)
