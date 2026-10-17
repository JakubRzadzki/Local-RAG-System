"""Document DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    """A document that has been ingested into the vector store."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    created_at: datetime
