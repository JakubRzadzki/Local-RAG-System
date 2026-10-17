"""Chat request DTOs and the streamed event protocol (NDJSON)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatOptions(BaseModel):
    """Generation and retrieval parameters chosen in the UI."""

    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_k: int = Field(default=4, ge=1, le=20)
    document_ids: list[int] | None = Field(
        default=None, description="Restrict retrieval to these documents."
    )


class ChatRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage] = Field(min_length=1)
    options: ChatOptions = Field(default_factory=ChatOptions)
    conversation_id: int | None = Field(
        default=None, description="Continue this conversation; omit to start a new one."
    )

    @field_validator("messages")
    @classmethod
    def last_message_is_from_user(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages[-1].role != "user":
            raise ValueError("the last message must come from the user")
        return messages


class SourceOut(BaseModel):
    """A retrieved chunk that was supplied to the model as context."""

    index: int = Field(description="1-based citation number used in the answer, e.g. [1].")
    document_id: int
    filename: str
    chunk_index: int
    page: int | None
    score: float
    content: str


class ConversationEvent(BaseModel):
    type: Literal["conversation"] = "conversation"
    id: int
    title: str


class SourcesEvent(BaseModel):
    type: Literal["sources"] = "sources"
    sources: list[SourceOut]


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    content: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


ChatEvent = ConversationEvent | SourcesEvent | TokenEvent | DoneEvent | ErrorEvent


def encode_event(event: ChatEvent) -> str:
    """Serialize an event as one NDJSON line."""
    return event.model_dump_json() + "\n"
