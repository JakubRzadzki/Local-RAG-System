"""Paragraph-aware text chunking with overlap."""

import re

from local_rag_system.exceptions import InvalidChunkingError

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def normalize_newlines(text: str) -> str:
    """Convert Windows (``\\r\\n``) and old Mac (``\\r``) line endings to ``\\n``."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _cut_point(text: str, start: int, end: int) -> int:
    """Return where to cut ``text[start:end]`` so that a word is not split.

    Prefers the last whitespace in the second half of the window; falls back to ``end``.
    """
    if end >= len(text) or text[end].isspace():
        return end
    lower = start + (end - start) // 2
    for index in range(end - 1, lower, -1):
        if text[index].isspace():
            return index
    return end


def _split_long(text: str, size: int, overlap: int) -> list[str]:
    """Split a paragraph longer than ``size`` into pieces of at most ``size`` characters.

    Pieces end at word boundaries where possible and start ``overlap`` characters
    before the previous end (snapped forward to a word start).
    """
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = _cut_point(text, start, min(start + size, len(text)))
        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
        if end >= len(text):
            break
        next_start = end - overlap
        if next_start > 0 and not text[next_start - 1].isspace():
            following = next((i for i in range(next_start, end) if text[i].isspace()), None)
            if following is not None:
                next_start = following + 1
        start = next_start if next_start > start else end
    return parts


def _tail(text: str, overlap: int) -> str:
    """Last ~``overlap`` characters of ``text``, trimmed to start at a word boundary."""
    if overlap <= 0:
        return ""
    tail = text[-overlap:]
    if len(text) > overlap and " " in tail:
        tail = tail.split(" ", 1)[1]
    return tail


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split ``text`` into chunks of at most ``size`` characters.

    Paragraphs (separated by blank lines) are kept together where possible. Consecutive
    chunks share up to ``overlap`` characters so context is not lost at boundaries; the
    overlap is shortened when needed so a chunk never exceeds ``size``.

    Raises:
        InvalidChunkingError: if ``size`` is not positive or ``overlap`` is not
            within ``[0, size)``.
    """
    if size <= 0 or not 0 <= overlap < size:
        raise InvalidChunkingError("chunk_size must be > 0 and 0 <= overlap < chunk_size")

    paragraphs = [p.strip() for p in _PARAGRAPH_BREAK.split(normalize_newlines(text)) if p.strip()]

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
            room = min(overlap, size - len(para) - 2)
            carried = _tail(current, room)
            current = f"{carried}\n\n{para}" if carried else para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)
    return chunks
