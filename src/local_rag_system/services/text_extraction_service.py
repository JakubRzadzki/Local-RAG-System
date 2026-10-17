"""Extract plain text from uploaded TXT / MD / PDF files."""

import asyncio
import io
from dataclasses import dataclass
from pathlib import PurePath

from pypdf import PdfReader

from local_rag_system.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)

SUPPORTED_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".pdf"})


@dataclass(frozen=True, slots=True)
class Section:
    """A run of text and, for PDFs, the page it came from."""

    text: str
    page: int | None = None


def _decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1250", errors="replace")


def _read_pdf(data: bytes) -> list[Section]:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise CorruptDocumentError("The PDF is password-protected.")
        sections = (
            Section(text=(page.extract_text() or "").strip(), page=number)
            for number, page in enumerate(reader.pages, start=1)
        )
        return [section for section in sections if section.text]
    except CorruptDocumentError:
        raise
    except Exception as exc:  # pypdf raises many unrelated types for damaged files
        raise CorruptDocumentError("The PDF is damaged or could not be read.") from exc


async def extract_sections(filename: str, data: bytes) -> list[Section]:
    """Return the non-empty text sections of an uploaded file.

    Raises:
        UnsupportedFileTypeError: for extensions other than TXT/MD/PDF.
        EmptyDocumentError: when the file contains no extractable text.
    """
    extension = PurePath(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or filename}'. Use TXT, MD or PDF."
        )

    if extension == ".pdf":
        # pypdf is synchronous and CPU-bound; keep it off the event loop.
        sections = await asyncio.to_thread(_read_pdf, data)
    else:
        text = _decode_text(data).strip()
        sections = [Section(text=text)] if text else []

    if not sections:
        raise EmptyDocumentError(f"No extractable text found in '{filename}'.")
    return sections
