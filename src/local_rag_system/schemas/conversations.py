"""Conversation DTOs."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from local_rag_system.schemas.chat import SourceOut


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    model: str
    created_at: datetime
    updated_at: datetime


class StoredMessageOut(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceOut]
    created_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[StoredMessageOut]


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=120)
