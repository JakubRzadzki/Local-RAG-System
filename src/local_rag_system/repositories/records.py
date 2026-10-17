"""Plain data records returned by repositories."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    id: int
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewChunk:
    chunk_index: int
    content: str
    page: int | None
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    page: int | None
    content: str
    score: float


@dataclass(frozen=True, slots=True)
class OllamaModelRecord:
    name: str
    size_bytes: int
    family: str
    parameter_size: str
    quantization: str
    capabilities: tuple[str, ...]
