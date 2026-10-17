"""Paragraph-aware text chunking with overlap."""

from local_rag_system.exceptions import InvalidChunkingError


def _split_long(text: str, size: int, overlap: int) -> list[str]:
    """Split by characters; only used for paragraphs longer than ``size``."""
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return parts


def _tail(text: str, overlap: int) -> str:
    """Last ~``overlap`` characters of ``text``, trimmed to start at a word boundary."""
    tail = text[-overlap:] if overlap else ""
    if len(text) > overlap and " " in tail:
        tail = tail.split(" ", 1)[1]
    return tail


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split ``text`` into chunks of at most ~``size`` characters.

    Paragraphs are kept together where possible; consecutive chunks share up to
    ``overlap`` characters so context is not lost at chunk boundaries.

    Raises:
        InvalidChunkingError: if ``size`` is not positive or ``overlap`` is not
            within ``[0, size)``.
    """
    if size <= 0 or not 0 <= overlap < size:
        raise InvalidChunkingError("chunk_size must be > 0 and 0 <= overlap < chunk_size")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long(para, size, overlap))
            continue

        if current and len(current) + len(para) + 2 > size:
            chunks.append(current)
            carried = _tail(current, overlap)
            current = f"{carried}\n\n{para}" if carried else para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)
    return chunks
