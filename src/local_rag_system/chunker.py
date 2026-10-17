def _split_long(text: str, size: int, overlap: int) -> list[str]:
    """Split by characters; only used for paragraphs longer than size."""
    parts = []
    start = 0
    while start < len(text):
        end = start + size
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return parts


def _tail(text: str, overlap: int) -> str:
    """Last ~overlap characters of the text, trimmed to start at a word boundary."""
    tail = text[-overlap:]
    if len(text) > overlap and " " in tail:
        tail = tail.split(" ", 1)[1]
    return tail


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
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
            current = f"{_tail(current, overlap)}\n\n{para}"
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)
    return chunks
